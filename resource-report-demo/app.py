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
from ibm_platform_services import IamIdentityV1, ResourceControllerV2, ResourceManagerV2
from ibm_platform_services.resource_controller_v2 import ResourceInstancesPager, ResourceBindingsPager, ResourceKeysPager
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import pandas as pd
from icecream import ic
import pytz


ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")

authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)

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
    iamIdentityService = IamIdentityV1(authenticator=authenticator)
    return iamIdentityService

def resource_controller_client():  
    resourceControllerService = ResourceControllerV2(authenticator=authenticator)
    return resourceControllerService

def resource_manager_client():  
    resourceManagerService = ResourceManagerV2(authenticator=authenticator)
    return resourceManagerService



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


def get_resource_group_id(group_name):
    account_id = get_account_id()
    client = resource_manager_client()
    resource_group_list = client.list_resource_groups(
        account_id=account_id
    ).get_result()
    for rg in resource_group_list:
        if rg["name"] == group_name:
            return rg["id"]
    return None


@click.group()
def cli():
    """Group to hold our commands"""
    pass

@cli.command()
def get_account_resources():
    client = resource_controller_client()
    all_results = []
    pager = ResourceInstancesPager(
        client=client
    )
    while pager.has_next():
        next_page = pager.get_next()
        assert next_page is not None
        all_results.extend(next_page)

    results = ic(all_results)
    return results


@cli.command()
def get_service_bindings():

    client = resource_controller_client()
    all_results = []
    pager = ResourceBindingsPager(
        client=client
    )
    while pager.has_next():
        next_page = pager.get_next()
        assert next_page is not None
        all_results.extend(next_page)

    results = ic(all_results)
    return results


@cli.command()
def get_resource_service_keys():
    client = resource_controller_client()
    all_results = []
    pager = ResourceKeysPager(
        client=client
    )
    while pager.has_next():
        next_page = pager.get_next()
        assert next_page is not None
        all_results.extend(next_page)

    results = ic(all_results)
    return results

## need to add try statements here with explicit error handling
@cli.command()
def get_resource_groups():
    account_id = get_account_id()
    client = resource_manager_client()
    resource_group_list = client.list_resource_groups(
        account_id=account_id
    ).get_result()

    # ic(resource_group_list)
    return resource_group_list


@cli.command()
def get_resources_by_group():
    account_id = get_account_id()
    rc_client = resource_controller_client()
    rm_client = resource_manager_client()
    resource_group_list = rm_client.list_resource_groups(
        account_id=account_id
    ).get_result()
    
    all_results = []
    for group in resource_group_list["resources"]:
        resource_group_id = group["id"]
        resource_list = rc_client.list_resource_instances(
            resource_group_id=resource_group_id
        ).get_result()
        
        all_results.extend(resource_list)
        ic(resource_list)

    return all_results

if __name__ == '__main__':
    cli()