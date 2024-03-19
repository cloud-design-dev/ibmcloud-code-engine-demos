#!/usr/bin/env python3

import os
import json
import logging
import ibm_boto3
from datetime import datetime
from ibm_botocore.client import Config, ClientError

def main(params):
    cos_instance_crn = os.environ.get('CLOUD_OBJECT_STORAGE_RESOURCE_INSTANCE_ID')
    if not cos_instance_crn:
        raise ValueError("CLOUD_OBJECT_STORAGE_RESOURCE_INSTANCE_ID environment variable not found. Make sure an Object storage instance is bound to this Code Engine project.")

    cos_api_key = os.environ.get('CLOUD_OBJECT_STORAGE_APIKEY')
    if not cos_api_key:
        raise ValueError("CLOUD_OBJECT_STORAGE_APIKEY environment variable not found. Make sure an Object storage instance is bound to this Code Engine project.")

    cos_endpoint = params.get('cos_endpoint')
    if not cos_endpoint:
        raise ValueError("cos_endpoint parameter not found. Make sure to pass the cos_endpoint parameter in the request.")

    cos_bucket = params.get('cos_bucket')
    if not cos_bucket:
        raise ValueError("cos_bucket parameter not found. Make sure to pass the cos_bucket parameter in the request.")

    # Check if 'CE_JOB' environment variable exists and is not empty, if so, use private endpoint
    if os.environ.get('CE_JOB', ''):
        cos_endpoint = f"https://s3.direct.{cos_endpoint}.cloud-object-storage.appdomain.cloud"
    else:
        cos_endpoint = f"https://s3.{cos_endpoint}.cloud-object-storage.appdomain.cloud"

    try:
        cos = ibm_boto3.client("s3",
            ibm_api_key_id=cos_api_key,
            ibm_service_instance_id=cos_instance_crn,
            config=Config(signature_version="oauth"),
            ibm_auth_endpoint="https://iam.cloud.ibm.com/identity/token",
            endpoint_url=cos_endpoint
        )
        
        current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M")
        item_name = f"{current_datetime}-env.json"
        env_vars = {}
        for key, value in os.environ.items():
            env_vars[key] = value
        
        json_string = json.dumps(env_vars, indent=4)
        cos.put_object(Body=json_string, Bucket=cos_bucket, Key=item_name)
        print("Item: {0} created!".format(item_name))

        return {
            "headers": {
                "Content-Type": "application/json",
            },
            "statusCode": 200,
            "body": json.dumps(json_string)
        }
    except ClientError as be:
        return {
            "headers": {
                "Content-Type": "application/json",
            },
            "statusCode": be.response['Error']['Code'],
            "body": json.dumps({"error": "Client Error", "details": str(be)})
        }
    except Exception as e:
        return {
            "headers": {
                "Content-Type": "application/json",
            },
            "statusCode": 500,
            "body": json.dumps({"error": "Server Error", "details": str(e)})
        }

