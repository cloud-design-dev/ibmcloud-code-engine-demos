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
import sys
import time
import logging
import httpx
import click
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

ignore_group = ['hyperion', 'jbmh-locate']

def get_iam_token():
    try:
        hdrs = { 'Accept' : 'application/json', 'Content-Type' : 'application/x-www-form-urlencoded' }
        params = { 'grant_type' : 'urn:ibm:params:oauth:grant-type:apikey', 'apikey' : ibmcloud_api_key }
        resp = httpx.post('https://iam.cloud.ibm.com/identity/token', data = params, headers = hdrs)
        resp.raise_for_status()
        response_json = resp.json()
        iam_token  = response_json['access_token']
        return iam_token

    except httpx.HTTPError as e:
        logging.error("HTTP exception {}.".format(str(e)))
        sys.exit(1)

def send_log_to_ibm_cloud_logs(application_name, subsystem_name, computer_name, message):
    iam_token = get_iam_token()
    if not iam_token:
        raise ValueError("IAM_TOKEN environment variable not found")

    log_data = [{
        "applicationName": application_name,
        "subsystemName": subsystem_name,
        "computerName": computer_name,
        "text": {"message": message},
        "category": "cat-1",
        "className": "class-1",
        "methodName": "method-1",
        "threadId": "thread-1"
    }]

    logging_url = os.environ.get('LOGGING_URL')
    hdrs = { 'Content-Type' : 'application/json', "Authorization": f"{iam_token}" }
    resp = httpx.post(logging_url, data=json.dumps(log_data), headers = hdrs)
    resp.raise_for_status()
    print(resp.text)




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
                    print(f"Stopping instance {instance_name}")
                    response = client.create_instance_action(instance_id=instance_id, type='stop').get_result()
                    send_log_to_ibm_cloud_logs("ce-start-stop-script", "stop-action", f"{instance_name}", f"Stopping instance {instance_name}")
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
   
                print(f"Starting instance {instance_name}")
                send_log_to_ibm_cloud_logs("ce-start-stop-script", "start-action", f"{instance_name}", f"Starting instance {instance_name}")
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
