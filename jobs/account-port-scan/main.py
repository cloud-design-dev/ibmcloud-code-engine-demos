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
import sys
import os
import socket
import logging
import SoftLayer
import ibm_vpc
from ibm_cloud_sdk_core import ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")

ibmcloud_classic_username = os.environ.get('IBMCLOUD_CLASSIC_USERNAME')
if not ibmcloud_classic_username:
    raise ValueError("IBMCLOUD_CLASSIC_USERNAME environment variable not found")

ibmcloud_classic_api_key = os.environ.get('IBMCLOUD_CLASSIC_API_KEY')
if not ibmcloud_classic_api_key:
    raise ValueError("IBMCLOUD_CLASSIC_API_KEY environment variable not found")

authenticator = IAMAuthenticator(
    apikey=ibmcloud_api_key
)

def softlayer_client():
    client = SoftLayer.create_client_from_env(
        username=ibmcloud_classic_username, 
        api_key=ibmcloud_classic_api_key
        )
    return client

def get_regions():
    service = ibm_vpc.VpcV1(authenticator=authenticator)
    service.set_service_url(f'https://us-south.iaas.cloud.ibm.com/v1')
    try:
        response = service.list_regions().get_result()
        regions = response['regions']
        region_names = [region['name'] for region in regions]
        return region_names
    except ApiException as e:
        logging.error("Unable to retrieve regions: {0}".format(e))
        sys.exit()

def get_floating_ips():
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
    classic_host_ips = []
    client = softlayer_client()
    vms = client['Account'].getVirtualGuests()
    filtered_vms = [s for s in vms if s.get('primaryIpAddress')]

    for vm in filtered_vms:
        classic_host_ips.append(vm['primaryIpAddress'])
    return classic_host_ips

def get_classic_infrastructure_hardware():
    classic_host_ips = []
    client = softlayer_client()
    bare_metals = client['Account'].getHardware()
    filtered_bms = [s for s in bare_metals if s.get('primaryIpAddress')]

    for bare_metal in filtered_bms:
        classic_host_ips.append(bare_metal['primaryIpAddress'])
    return classic_host_ips


def scan_top_ports(target):
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
    print("Starting scan of floating IPs...")
    targets = get_floating_ips()
    for target in targets:
        open_ports = scan_top_ports(target)
        if open_ports: 
            logging.info(f"Open ports on {target}: {open_ports}")
    logging.info("VPC Floating IP Scan complete.")

    print("Starting scan on classic infrastructure virtual guests...")
    targets = get_classic_infrastructure_instances()
    for target in targets:
        open_ports = scan_top_ports(target)
        if open_ports: 
            logging.info(f"Open ports on {target}: {open_ports}")
    print("Classic Virtual Guests Scan complete.")

    print("Starting scan on classic infrastructure bare metals...")
    targets = get_classic_infrastructure_hardware()
    for target in targets:
        open_ports = scan_top_ports(target)
        if open_ports: 
            logging.info(f"Open ports on {target}: {open_ports}")
    print("Classic Bare Metals Scan complete.")

if __name__ == "__main__":
    main()
