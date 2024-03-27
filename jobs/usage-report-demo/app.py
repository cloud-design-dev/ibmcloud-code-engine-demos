#!/usr/bin/env python3
"""Module providing functions to report IBM Cloud account credits and usage"""
# Author: Ryan Tiffany
# Copyright (c) 2024
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys
import json
import logging
from datetime import datetime
import click
from ibm_platform_services import IamIdentityV1, UsageReportsV4
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from rich.console import Console
from rich.table import Table


ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")


def setup_logging(default_path='logging.json', default_level=logging.info, env_key='LOG_CFG'):
    """
    Set up logging configuration.

    Args:
        default_path (str, optional): 
            Default path to the logging configuration file. Defaults to 'logging.json'.
        default_level (int, optional): 
            Default logging level. Defaults to logging.INFO.
        env_key (str, optional): 
            Environment variable key to override the default path. Defaults to 'LOG_CFG'.
    """

    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt', encoding='utf-8') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def iam_client():
    """
    Creates and returns an instance of the IAMIdentityV1 client.

    Returns:
        IamIdentityV1: An instance of the IAMIdentityV1 client.
    """

    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    iam_identity_service = IamIdentityV1(authenticator=authenticator)
    return iam_identity_service


def usage_client():
    """
    Creates and returns an instance of the UsageReportsV4 class.

    Returns:
        UsageReportsV4: An instance of the UsageReportsV4 class.
    """
    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    usage_report_service = UsageReportsV4(authenticator=authenticator)
    return usage_report_service


def get_account_id():
    """
    Retrieves the account ID associated with the API key.

    Returns:
        str: The account ID.
    """
    try:
        client = iam_client()
        api_key = client.get_api_keys_details(
          iam_api_key=ibmcloud_api_key
        ).get_result()
    except ApiException as e:
        logging.error("API exception %s.", str(e))
        sys.exit(0)
    account_id = api_key["account_id"]
    return account_id


@click.group()
def cli():
    """Group to hold our commands"""


@cli.command()
def get_current_credit_balance():
    """
    Retrieves the current credit balance for the account.

    Returns:
        float: The credit balance for the account.
    """

    account_id = get_account_id()
    client = usage_client()
    usage_month = datetime.now().strftime("%Y-%m")
    try:
        account_credits = client.get_account_summary(
            account_id=account_id,
            billingmonth=usage_month
        ).get_result()

        account_credit_balance = []
        for offer in account_credits['offers']:
            starting_credit_balance = offer['credits']['balance']
            account_credit_balance.append(starting_credit_balance)

        credit_balance = sum(account_credit_balance)
        print(f"Credit Balance: {credit_balance}")
        return credit_balance

    except ApiException as e:
        if e.code == 424:
            logging.warning("API exception %s.", str(e))
            sys.exit(0)
        else:
            logging.error("API exception %s.", str(e))
            sys.exit(0)


@cli.command()
def get_current_month_usage():
    """
    Retrieves the usage data for the current month and prints the resource name, cost, 
    and type for each resource. Also calculates and prints the total cost for the current month.

    Returns:
        list: The usage data for the current month.
    """

    account_id = get_account_id()
    client = usage_client()
    data = []
    usage_month = datetime.now().strftime("%Y-%m")

    try:
        usage = client.get_account_usage(
            account_id=account_id,
            billingmonth=usage_month,
            names=True
        ).get_result()

        total_cost = 0

        for resource in usage['resources']:
            name = resource['resource_name']
            for plan in resource['plans']:
                cost = plan['cost']
                resource_type = resource['resource_id']
                rounded_cost = round(cost, 4)
                total_cost += rounded_cost
                print(f"Resource Name: {name}, Cost: {rounded_cost},"
                    f"Resource Type: {resource_type}")

        print(f"\nTotal Cost: {round(total_cost, 4)}")

    except ApiException as e:
        if e.code == 424:
            logging.warning("API exception %s.", str(e))
            sys.exit(0)
        else:
            logging.error("API exception %s.", str(e))
            sys.exit(0)

    return data


@cli.command()
def pretty_print_usage():
    """
    Prints a formatted usage report for an account.

    This function retrieves the account usage for the current month and prints a formatted table
    displaying the resource name, plan name, billable metrics, and cost for each resource and plan.
    It also calculates and displays the total cost for all resources.

    Raises:
        ApiException: If there is an error while retrieving the account usage.

    Returns:
        None
    """

    account_id = get_account_id()
    client = usage_client()
    usage_month = datetime.now().strftime("%Y-%m")

    try:
        usage = client.get_account_usage(
            account_id=account_id,
            billingmonth=usage_month,
            names=True
        ).get_result()

        resources = usage['resources']
        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Resource Name", style="dim", width=35)
        table.add_column("Plan Name")
        table.add_column("Billable Metrics")
        table.add_column("ResourceID")
        table.add_column("Cost", justify="right")

        total_cost = 0

        for resource in resources:
            resource_name = resource['resource_name']
            resource_id = resource['resource_id']
            for plan in resource['plans']:
                plan_name = plan['plan_name']
                cost = round(plan.get('cost', 0), 4)
                total_cost += cost
                metric_list = [f"{usage['metric_name']}" for usage in plan['usage']]
                metric_units = ", ".join(metric_list)
                if cost > 0:
                    table.add_row(resource_name, plan_name, metric_units, resource_id, str(cost))
        console.print(table)


        total_row = Table(show_header=True, header_style="bold magenta")
        total_row.add_column("Total Cost:", style="bold", justify="right")
        total_row.add_column(str(round(total_cost, 4)), style="bold", justify="right")
        console.print(total_row)

    except ApiException as e:
        logging.error("API exception %s.", str(e))
        sys.exit(0)

if __name__ == '__main__':
    cli()
