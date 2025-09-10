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

__author__ = 'ryantiffany'
import sys
import os
import socket
import json
import logging
import logging.config
import requests
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

cloud_logging_endpoint = os.environ.get('IBM_CLOUD_LOGGING_ENDPOINT')
if not cloud_logging_endpoint:
    raise ValueError("IBM_CLOUD_LOGGING_ENDPOINT environment variable not found")


"""
Create an IAM authenticator object for use with the VPC API.
"""
authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)


def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
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


def get_iam_token():
    """
    Get IAM token using the API key for authenticating with IBM Cloud Logging
    """
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": ibmcloud_api_key
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        logging.error("Error obtaining IAM token: %s", e)
        return None


def format_ports_json(vpc_results, vg_results, bm_results):
    """
    Format all results into a single JSON array in the specified format
    
    Args:
        vpc_results (dict): Dictionary with IP addresses as keys and lists of open ports as values for VPC
        vg_results (dict): Dictionary with IP addresses as keys and lists of open ports as values for Virtual Guests
        bm_results (dict): Dictionary with IP addresses as keys and lists of open ports as values for Bare Metal servers
    
    Returns:
        list: List of formatted entries in the specified format
    """
    all_ports_json = []
    
    # Process VPC floating IPs
    for ip, ports in vpc_results.items():
        for port in ports:
            all_ports_json.append({
                "server-ip": ip,
                "open-port": str(port),
                "environment": "VPC"
            })
    
    # Process Classic Virtual Guests
    for ip, ports in vg_results.items():
        for port in ports:
            all_ports_json.append({
                "server-ip": ip,
                "open-port": str(port),
                "environment": "Classic"
            })
    
    # Process Classic Bare Metal servers
    for ip, ports in bm_results.items():
        for port in ports:
            all_ports_json.append({
                "server-ip": ip,
                "open-port": str(port),
                "environment": "Classic"
            })
    
    return all_ports_json


def format_scan_results(target_type, results):
    """
    Format scan results to be sent to IBM Cloud Logging
    
    Args:
        target_type (str): Type of target (floating_ip, virtual_guest, bare_metal)
        results (dict): Dictionary with IP addresses as keys and lists of open ports as values
    
    Returns:
        list: List of formatted log entries
    """
    log_entries = []
    
    # Get computer name from environment variable or fall back to local system name
    computer_name = os.environ.get('CE_PROJECT_ID', socket.gethostname())
    
    for ip, ports in results.items():
        if ports:  # Only include IPs with open ports
            log_entry = {
                "applicationName": "account-port-scan",
                "subsystemName": f"{target_type}-scan",
                "computerName": computer_name,
                "text": {
                    "ip_address": ip,
                    "open_ports": ports,
                    "target_type": target_type,
                    "message": f"Open-Port-Detected: Open ports detected on {target_type} {ip}: {ports}"
                }
            }
            log_entries.append(log_entry)
    
    return log_entries


def send_to_ibm_cloud_logging(log_entries, all_ports_json):
    """
    Send log entries to IBM Cloud Logging
    
    Args:
        log_entries (list): List of formatted log entries
        all_ports_json (list): List of all open ports in the specified JSON format
    
    Returns:
        bool: True if logs were sent successfully, False otherwise
    """
    if not log_entries:
        logging.info("No open ports detected, no logs to send")
        return True
    
    # Get log endpoint from environment variable or use default from example
    log_endpoint = f"{cloud_logging_endpoint}/logs/v1/singles"
    
    token = get_iam_token()
    if not token:
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Add a summary log entry with the full JSON of all open ports
    computer_name = os.environ.get('CE_PROJECT_ID', socket.gethostname())
    summary_entry = {
        "applicationName": "account-port-scan",
        "subsystemName": "summary-scan",
        "computerName": computer_name,
        "text": {
            "message": "Open-Port-Detected: Summary of all open ports across all environments",
            "open_ports_summary": all_ports_json
        }
    }
    
    # Add the summary entry to the log entries
    log_entries.append(summary_entry)
    
    try:
        response = requests.post(log_endpoint, headers=headers, json=log_entries)
        response.raise_for_status()
        logging.info("Successfully sent %d log entries to IBM Cloud Logging", len(log_entries))
        return True
    except requests.exceptions.RequestException as e:
        logging.error("Error sending logs to IBM Cloud Logging: %s", e)
        return False


def main():
    """
    Main function to scan IBM Cloud VPC and classic infrastructure
    and send results to IBM Cloud Logging
    """
    # Set up logging
    setup_logging()
    
    # Results dictionary for each target type
    floating_ip_results = {}
    virtual_guest_results = {}
    bare_metal_results = {}
    
    print("Starting scan of floating IPs...")
    targets = get_floating_ips()
    for target in targets:
        open_ports = scan_top_ports(target)
        floating_ip_results[target] = open_ports
        if open_ports: 
            print(f"Open ports on {target}: {open_ports}")
    print("VPC Floating IP Scan complete.")

    print("Starting scan on classic infrastructure virtual guests...")
    targets = get_classic_infrastructure_instances()
    for target in targets:
        open_ports = scan_top_ports(target)
        virtual_guest_results[target] = open_ports
        if open_ports:
            print(f"Open ports on {target}: {open_ports}")
    print("Classic Virtual Guests Scan complete.")

    print("Starting scan on classic infrastructure bare metals...")
    targets = get_classic_infrastructure_hardware()
    for target in targets:
        open_ports = scan_top_ports(target)
        bare_metal_results[target] = open_ports
        if open_ports:
            print(f"Open ports on {target}: {open_ports}")
    print("Classic Bare Metals Scan complete.")
    
    # Create the consolidated JSON object for all open ports
    all_ports_json = format_ports_json(
        floating_ip_results, 
        virtual_guest_results, 
        bare_metal_results
    )
    
    # Format the individual log entries
    floating_ip_logs = format_scan_results("floating_ip", floating_ip_results)
    virtual_guest_logs = format_scan_results("virtual_guest", virtual_guest_results)
    bare_metal_logs = format_scan_results("bare_metal", bare_metal_results)
    
    # Combine all individual logs into a single list
    all_logs = floating_ip_logs + virtual_guest_logs + bare_metal_logs
    
    # Send logs to IBM Cloud Logging
    if all_logs or all_ports_json:
        print(f"Sending {len(all_logs)} log entries and a summary to IBM Cloud Logging...")
        success = send_to_ibm_cloud_logging(all_logs, all_ports_json)
        if success:
            print("Successfully sent logs to IBM Cloud Logging")
        else:
            print("Failed to send logs to IBM Cloud Logging")
    else:
        print("No open ports detected, no logs to send")


if __name__ == "__main__":
    main()