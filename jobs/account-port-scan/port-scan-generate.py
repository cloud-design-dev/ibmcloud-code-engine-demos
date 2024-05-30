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

# TODO: Add COS python module
# TODO: Generate JSON file of open ports
# TODO: Write JSON file to COS bucket

__author__ = 'ryantiffany'
import sys
import os
import socket
import logging
import SoftLayer
import ibm_vpc
from ibm_cloud_sdk_core import ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

"""
Pull IBM Cloud API key from environment. If not set, raise an error. 
"""
ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")

"""
Create an IAM authenticator object for use with the VPC API.
"""
authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)


def setup_logging(default_path='logging.json', default_level=logging.info, env_key='LOG_CFG'):
    """
    Set up logging configuration and use logging.json to format logs
    """
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


def sl_iam_client():
    """
    Create a SoftLayer client object using the IBM Cloud API key
    This function is used to authenticate to the SoftLayer API
    and interact with Classic resources.
    """
    client = SoftLayer.create_client_from_env(
        username="apikey",
        api_key=ibmcloud_api_key
    )
    return client


def get_regions():
    """
    Retrieve a list of IBM Cloud VPC regions
    """
    service = ibm_vpc.VpcV1(authenticator=authenticator)
    service.set_service_url('https://us-south.iaas.cloud.ibm.com/v1')
    try:
        response = service.list_regions().get_result()
        regions = response['regions']
        region_names = [region['name'] for region in regions]
        return region_names
    except ApiException as e:
        logging.error("Unable to retrieve regions: %s", e)
        sys.exit()


def get_floating_ips():
    """
    Retrieve a list of IBM Cloud VPC floating IPs across all regions
    """
    floating_ips = []
    regions = get_regions()
    for region in regions:
        service = ibm_vpc.VpcV1(authenticator=authenticator)
        service.set_service_url(f'https://{region}.iaas.cloud.ibm.com/v1')
        response = service.list_floating_ips().get_result()
        for fip in response['floating_ips']:
            ip_address = fip['address']
            floating_ips.append(ip_address)
    return floating_ips


def get_classic_infrastructure_instances():
    """
    Retrieve of public IPs associated with classic
    infrastructure virtual guests
    """
    classic_host_ips = []
    client = sl_iam_client()
    vms = client['Account'].getVirtualGuests()
    filtered_vms = [s for s in vms if s.get('primaryIpAddress')]

    for vm in filtered_vms:
        classic_host_ips.append(vm['primaryIpAddress'])
    return classic_host_ips


def get_classic_infrastructure_hardware():
    """
    Retrieve of public IPs associated with classic
    bare metal servers and network gateways
    """
    classic_host_ips = []
    client = sl_iam_client()
    bare_metals = client['Account'].getHardware()
    filtered_bms = [s for s in bare_metals if s.get('primaryIpAddress')]

    for bare_metal in filtered_bms:
        classic_host_ips.append(bare_metal['primaryIpAddress'])
    return classic_host_ips


def scan_top_ports(target):
    """
    Scan the top ports on a target IP address
    """
    open_ports = []
    top_ports = [21, 22, 25, 23, 3389]
    for port in top_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((target, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except KeyboardInterrupt:
            sys.exit()
        except socket.error:
            pass
    return open_ports


def main():
    """
    Main function to scan IBM Cloud VPC and classic infrastructure
    """
    print("Starting scan of floating IPs...")
    targets = get_floating_ips()
    for target in targets:
        open_ports = scan_top_ports(target)
        if open_ports: 
            print(f"Open ports on {target}: {open_ports}")
    print("VPC Floating IP Scan complete.")

    print("Starting scan on classic infrastructure virtual guests...")
    targets = get_classic_infrastructure_instances()
    for target in targets:
        open_ports = scan_top_ports(target)
        if open_ports:
            print(f"Open ports on {target}: {open_ports}")
    print("Classic Virtual Guests Scan complete.")

    print("Starting scan on classic infrastructure bare metals...")
    targets = get_classic_infrastructure_hardware()
    for target in targets:
        open_ports = scan_top_ports(target)
        if open_ports:
            print(f"Open ports on {target}: {open_ports}")
    print("Classic Bare Metals Scan complete.")


if __name__ == "__main__":
    main()
