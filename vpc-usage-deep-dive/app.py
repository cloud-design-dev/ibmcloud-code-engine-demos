#!/usr/bin/env python3
import os
import logging
from datetime import datetime, tzinfo, timezone
import pandas as pd
import numpy as np
import ibm_boto3
from ibm_platform_services import IamIdentityV1, UsageReportsV4, GlobalSearchV2
from ibm_cloud_sdk_core import ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_platform_services.resource_controller_v2 import *
from ibm_botocore.client import Config, ClientError
from ibm_vpc import VpcV1
from urllib import parse

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


def vpc_client():
    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    vpcService = VpcV1(authenticator=authenticator)
    return vpcService


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


def get_vpc_regions():
    try:
        client = vpc_client()
        regions = client.list_regions().get_result()
    except ApiException as e:
        logging.error("API exception {}.".format(str(e)))
        quit(1)
    return regions


def get_vpc_instances():
    client = vpc_client()

    regions = get_vpc_regions().get("regions")

    items = []
    image_items = []

    for region in regions:
        endpoint = region["endpoint"] + "/v1"
        client.set_service_url(endpoint)
        # print(f"Endpoint: {endpoint}")
        instances = client.list_instances()
        while True:
            try:
                result = instances.get_result()
            except ApiException as e:
                logging.error("List VPC virtual server instances with status code {}:{}".format(str(e.code), e.message))
                quit(1)

            items = items + result["instances"]
            if "next" not in result:
                break
            else:
                next = dict(parse.parse_qsl(parse.urlsplit(result["next"]["href"]).query))
                instances = endpoint.list_instances(start=next["start"])

        instances = client.list_bare_metal_servers()
        while True:
            try:
                result = instances.get_result()
            except ApiException as e:
                logging.error("List BM server instances with status code {}:{}".format(str(e.code), e.message))
                quit(1)

            items = items + result["bare_metal_servers"]
            if "next" not in result:
                break
            else:
                next = dict(parse.parse_qsl(parse.urlsplit(result["next"]["href"]).query))
                instances = endpoint.list_bare_metal_servers(start=next["start"])

    instance_cache = {}
    for resource in items:
        crn = resource["crn"]
        instance_cache[crn] = resource

    print(f"Instance Cache: {instance_cache}")
    return instance_cache


try:
    account_id = get_account_id()
    print(f"Account ID: {account_id}")
    vpc_instances = get_vpc_instances()
    print(f"VPC Instances: {vpc_instances}")

except ApiException as e:
    logging.error("API exception {}.".format(str(e)))
    quit(1)
