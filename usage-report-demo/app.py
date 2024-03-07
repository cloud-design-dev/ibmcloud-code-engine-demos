#!/usr/bin/env python3
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
import json
import click
import logging
from ibm_platform_services import IamIdentityV1, UsageReportsV4
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import pandas as pd
import pytz
from rich.console import Console
from rich.table import Table
from ibm_cloud_sdk_core import ApiException

ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")

def setup_logging(default_path='logging.json', default_level=logging.info, env_key='LOG_CFG'):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

def iam_client():  
  authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
  iamIdentityService = IamIdentityV1(authenticator=authenticator)
  return iamIdentityService

def usage_client():  
  authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
  usageReportService = UsageReportsV4(authenticator=authenticator)
  return usageReportService

def get_account_id():
    try:
        client = iam_client()
        api_key = client.get_api_keys_details(
          iam_api_key=ibmcloud_api_key
        ).get_result()
    except ApiException as e:
        logging.error("API exception {}.".format(str(e)))
        quit(1)
    account_id = api_key["account_id"]
    return account_id


@click.group()
def cli():
    """Group to hold our commands"""
    pass


@cli.command()
def get_current_credit_balance():
    accountId = get_account_id()
    client = usage_client()
    usageMonth = datetime.now().strftime("%Y-%m")
    try:
        credits = client.get_account_summary(
            account_id=accountId,
            billingmonth=usageMonth
        ).get_result()
        accountCreditBalance = []
        for offer in credits['offers']:
            startingCreditBalance = offer['credits']['balance']
            accountCreditBalance.append(startingCreditBalance)
    except ApiException as e:
        if e.code == 424:
            logging.warning("API exception {}.".format(str(e)))
            quit(1)
        else:
            logging.error("API exception {}.".format(str(e)))
            quit(1)
    creditBalance = sum(accountCreditBalance)
    print(f"Credit Balance: {creditBalance}")
    return creditBalance

@cli.command()
def get_current_month_usage():
    accountId = get_account_id()
    client = usage_client()
    data = []
    usageMonth = datetime.now().strftime("%Y-%m")

    try:
        usage = client.get_account_usage(
            account_id=accountId,
            billingmonth=usageMonth,
            names=True
        ).get_result()

        # print(usage)
        for resource in usage['resources']:
            name = resource['resource_name']
            cost = resource['plans'][0]['cost']
            type = resource['resource_id']
            rounded_cost = round(cost, 4)
            print(f"Resource Name: {name}, Cost: {rounded_cost}, Resource Type: {type}")
            # print(name)
            

        # for resource in usage['resources']:
        #     rs_data = resource
        # # for resource in usage['resources']:
        # #     rs_data = resource
        # # data.append(rs_data)
    except ApiException as e:
        if e.code == 424:
            logging.warning("API exception {}.".format(str(e)))
            quit(1)
        else:
            logging.error("API exception {}.".format(str(e)))
            quit(1)

    # data.append(usage)
    # print(type(data))
    # print(json.dumps(data, indent=2))
    return data

# @click.command()
# @click.option('--all', is_flag=True, help='List all resource usage including those with zero cost')
# def get_usage(all):


#     try:
#         accountId = getAccountId(ibmcloud_api_key)
#         usageData = getCurrentMonthAccountUsage(accountId)
#         creditsData = getCurrentAccountCredits(accountId)

#         for credit in creditsData:
#             credit_balance = str(round(credit[0]['balance'], 0), 4)
#             print(f"Credit Balance: {credit_balance}")
#         resources = usageData[0]['resources']
#         # print(json.dumps(resources, indent=2))
#         console = Console()
#         table = Table(show_header=True, header_style="bold magenta")

#     # Add columns
#         table.add_column("Resource Name", style="dim", width=35)
#         # table.add_column("Resource ID")
#         table.add_column("Plan Name")
#         table.add_column("Billable Metrics")
#         # table.add_column("Billable Units")
#         table.add_column("Cost", justify="right")
#         for resource in resources:
#             resource_name = resource['resource_name']
#             resource_id = resource['resource_id']
#             for plan in resource['plans']:
#             # Check if plan_id starts with "classic_infrastructure" and skip it if true
#                 # if plan['plan_id'].startswith("classic_infrastructure"):
#                 #     continue

#                 plan_name = plan['plan_name']
#                 cost = round(plan.get('cost', 0), 4)

            
#                 metric_list = [f"{usage['metric_name']}" for usage in plan['usage']]
#                 metric_units = ", ".join(metric_list)
#                 unit_list = [f"{usage['unit_name']}" for usage in plan['usage']]
#                 unit_name = ", ".join(unit_list)
#                 if all or cost > 0:
#                     table.add_row(resource_name, plan_name, metric_units, str(cost))

#         console.print(table)
#     except ApiException as e:
#         logging.error("API exception {}.".format(str(e)))
#         quit(1)

if __name__ == '__main__':
    cli()