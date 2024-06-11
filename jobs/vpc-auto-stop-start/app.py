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
import time
import logging
import ibm_vpc
from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
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

def vpc_client():
    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    try:
        vpc_service = VpcV1(authenticator=authenticator)
    except ApiException as e:
        logging.error("API exception {}.".format(str(e)))
        quit(1)
    return vpc_service

ignore_group = ['piku', 'jbmh-locate']

@click.group()
def cli():
    """Group to hold our commands"""
    pass


@cli.command()
def stop_vpc_instances():
    client = vpc_client()
    workloads_regions = client.list_regions().get_result()['regions']
    try:
        for region in workloads_regions:
            vpc_endpoint = region['name']
            client.set_service_url(f'https://{vpc_endpoint}.iaas.cloud.ibm.com/v1')
            list_instances = client.list_instances().get_result()['instances']
            for instance in list_instances:
                instance_id = instance['id']
                instance_name = instance['name']
                if instance_name not in ignore_group:
                    print(f"Stopping instance {instance_id}")
                    response = client.create_instance_action(instance_id=instance_id, type='stop').get_result()
                    logging.info(response)
    except ApiException as e:
        print("Failed to stop instances: %s\n" % e)


@cli.command()
def start_vpc_instances():
    client = vpc_client()
    workloads_regions = client.list_regions().get_result()['regions']
    try:
        for region in workloads_regions:
            vpc_endpoint = region['name']
            client.set_service_url(f'https://{vpc_endpoint}.iaas.cloud.ibm.com/v1')
            list_instances = client.list_instances().get_result()['instances']
            for instance in list_instances:
                instance_id = instance['id']
                instance_name = instance['name']
                if instance_name not in ignore_group:
                    print(f"Starting instance {instance_id}")
                    response = client.create_instance_action(instance_id=instance_id, type='start').get_result()
                    logging.info(response)

                    while True:
                        instance_status = client.get_instance(id=instance_id).get_result()['status']
                        if instance_status == 'running':
                            logging.info(f"Instance {instance_id} is now running")
                            break
                        else:
                            logging.info(f"Instance {instance_id} status: {instance_status}. Waiting...")
                            time.sleep(5) 
    except ApiException as e:
        print("Failed to start instances: %s\n" % e)

if __name__ == '__main__':
    cli()
