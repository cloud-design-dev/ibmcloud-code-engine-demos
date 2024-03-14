#!/usr/bin/env python3
# Author: Ryan Tiffany
# Copyright (c) 2023
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

__author__ = 'ryantiffany'
import os
import ibm_vpc
import click
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_platform_services import ApiException

ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")

region = os.environ.get('IBMCLOUD_REGION')
if not region:
    raise ValueError("IBMCLOUD_REGION environment variable not found")

instance_name = os.environ.get('INSTANCE_NAME')
if not region:
    raise ValueError("INSTANCE_NAME environment variable not found")



def vpc_client():
    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    client = ibm_vpc.VpcV1(authenticator=authenticator)
    client.set_service_url(f'https://{region}.iaas.cloud.ibm.com/v1')
    return client


@click.group()
def cli():
    """Group to hold our commands"""
    pass


def filter_instances(instance_name: str):
    try:
        client = vpc_client()
        instances = client.list_instances().get_result()
        instance_id = [instance['id'] for instance in instances['instances'] if instance['name'] == instance_name]
        return instance_id[0]
    except ApiException as e:
        return e


@cli.command()
def stop_instance():
    client = vpc_client()
    instance_id = filter_instances(instance_name)
    stop_instance = client.create_instance_action(
        instance_id=instance_id,
        type='stop'
    )
    return stop_instance


@cli.command()
def start_instance():
    client = vpc_client()
    instance_id = filter_instances(instance_name)
    stop_instance = client.create_instance_action(
        instance_id=instance_id,
        type='start'
    )
    return stop_instance


if __name__ == '__main__':
    cli()
