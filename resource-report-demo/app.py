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
def get_account_resources():
    """Get account resources"""
    account_id = get_account_id()
    try:
        client = usage_client()
        resources = client.get_resource_usage(
            account_id=account_id
        ).get_result()
    except ApiException as e:
        logging.error("API exception {}.".format(str(e)))
        quit(1)
    console = Console()
    table = Table(title="Resource Usage")
    table.add_column("Resource ID", style="cyan", no_wrap=True)
    table.add_column("Resource Name", style="magenta")
    table.add_column("Resource Type", style="green")
    table.add_column("Total Usage", style="red")
    table.add_column("Unit", style="yellow")
    for resource in resources["resources"]:
        table.add_row(
            resource["resource_id"],
            resource["resource_name"],
            resource["resource_type"],
            resource["usage"],
            resource["unit"]
        )
    console.print(table)


if __name__ == '__main__':
    cli()