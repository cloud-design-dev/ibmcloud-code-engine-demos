#!/usr/bin/env python3

import os
import json
import click
import logging
from ibm_platform_services import IamIdentityV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import pandas as pd
import pytz

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

def ibm_client():  
  authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
  iamIdentityService = IamIdentityV1(authenticator=authenticator)
  return iamIdentityService

def getAccountId():
    try:
        client = ibm_client()
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
@click.option('--auth_count', default=0, help='Filter service IDs by the number of authentications.')
def list_service_id_auth(auth_count):
    client = ibm_client()
    account_id = getAccountId()
    serviceIds = client.list_service_ids(
        account_id=account_id,
        sort="modified_at",
        pagesize=100
    ).get_result().get("serviceids")

    print(f"Listing Service IDs with {auth_count} authentications:\n-----")

    for serviceId in serviceIds:
        svcid = client.get_service_id(
            id=serviceId['id'],
            include_activity=True,
            include_history=True
        ).get_result()

        authentications = svcid['activity'].get('authn_count', 0)
        if authentications == auth_count:
            print(f"ID: {serviceId['id']}")

@cli.command()
def show_filtered_service_ids():
    client = ibm_client()
    account_id = getAccountId()
    serviceIds = client.list_service_ids(
        account_id=account_id,
        sort="modified_at",
        pagesize=100
    ).get_result().get("serviceids")

    filtered_serviceIds = []

    for serviceId in serviceIds:
        svcid = client.get_service_id(
            id=serviceId['id'],
            include_activity=True,
            include_history=True
        ).get_result()

        modified_date_str = svcid['modified_at']
        modified_date = parse(modified_date_str).replace(tzinfo=pytz.UTC)
        modified_date_date_only = modified_date.date()
        current_date = datetime.now()
        svc_id_scan_date = current_date - timedelta(days=3)
        svc_id_scan_date_date_only = svc_id_scan_date.date()
        authentications = svcid['activity']['authn_count']

        if authentications == 0 and modified_date_date_only < svc_id_scan_date_date_only:
            filtered_serviceIds.append(serviceId)

    print(f"Filtered Service IDs: {filtered_serviceIds}")



@cli.command()
def list_all_service_ids():
    client = ibm_client()
    account_id = getAccountId()
    serviceIds = client.list_service_ids(
        account_id=account_id,
        sort="modified_at",
        pagesize=100
    ).get_result().get("serviceids")

    print("Listing Service IDs on the account:\n-----")

    for serviceId in serviceIds:
      print(f"Name: {serviceId['name']}\tID: {serviceId['id']}\n")

@cli.command()
@click.option('--service-id', '-s', help='ID of the service ID to delete', required=True)
def get_service_id(service_id):
  client = ibm_client()
  serviceId = client.get_service_id(
    id=service_id,
    include_activity=True,
    include_history=True
  ).get_result()

  print(serviceId)

@cli.command()
def filter_and_export_service_ids():
    client = ibm_client()
    account_id = getAccountId()
    serviceIds = client.list_service_ids(
        account_id=account_id,
        sort="modified_at",
        pagesize=100
    ).get_result().get("serviceids")

    filtered_serviceIds = []
    six_months_ago = datetime.now() - relativedelta(months=6)

    for serviceId in serviceIds:
        svcid = client.get_service_id(
            id=serviceId['id'],
            include_activity=True,
            include_history=True
        ).get_result()

        modified_date_str = svcid['modified_at']
        modified_date = parse(modified_date_str).replace(tzinfo=pytz.UTC)
        six_months_ago = datetime.now(pytz.UTC) - relativedelta(months=6)
        authentications = svcid['activity']['authn_count']

        if authentications == 0 and modified_date < six_months_ago:
            filtered_serviceIds.append(serviceId)

    print(f"Filtered Service IDs: {filtered_serviceIds}")

    # Optionally, export to Excel
    df = pd.DataFrame(filtered_serviceIds)
    df.to_excel('filtered_service_ids.xlsx', index=False)

    print("Filtered service IDs have been written to 'filtered_service_ids.xlsx'")

## TODO: Create some dummy service ids on personal account and use that to test removing un-used service ids
@cli.command()
def delete_unused_service_ids():
  client = ibm_client()

  account_id = getAccountId()
  serviceIds = client.list_service_ids(
        account_id=account_id,
        sort="modified_at",
        pagesize=100
  ).get_result().get("serviceids")

  for id in serviceIds:
    service_id = id['id']
    svcid = client.get_service_id(
      id=service_id,
      include_activity=True,
      include_history=True
    ).get_result()

    authentications = svcid['activity']['authn_count']
    if authentications == 0:
      print(f"Deleting service ID: {service_id}")
      client.delete_service_id(
        id=service_id
      )
    else:
      print(f"Service ID {service_id} has {authentications} authentications and will not be deleted.")

if __name__ == '__main__':
    cli()
