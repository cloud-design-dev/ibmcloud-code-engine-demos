#!/usr/bin/env python3
from __future__ import annotations
from subprocess import run, PIPE, DEVNULL
import json
from datetime import datetime
from json import dump as json_dump
import click
from dotenv import load_dotenv
import os
from sys import stdout
import ibm_boto3
from ibm_botocore.client import Config, ClientError

load_dotenv()

cos_instance_crn = os.environ.get('CLOUD_OBJECT_STORAGE_RESOURCE_INSTANCE_ID')
if not cos_instance_crn:
    raise ValueError("CLOUD_OBJECT_STORAGE_RESOURCE_INSTANCE_ID environment variable not found. Make sure an Object storage instance is bound to this Code Engine project.")

cos_api_key = os.environ.get('CLOUD_OBJECT_STORAGE_APIKEY')
if not cos_api_key:
    raise ValueError("CLOUD_OBJECT_STORAGE_APIKEY environment variable not found. Make sure an Object storage instance is bound to this Code Engine project.")

cos_bucket = os.environ.get('CLOUD_OBJECT_STORAGE_BUCKET')
if not cos_bucket:
    raise ValueError("CLOUD_OBJECT_STORAGE_BUCKET environment variable not found. Make sure you set this in Code Engine.")

# Check if 'CE_JOB' environment variable exists and is not empty, if so, use private endpoint
if os.environ.get('CE_JOB', ''):
    cos_endpoint = "https://s3.direct.us-south.cloud-object-storage.appdomain.cloud"
else:
    cos_endpoint = "https://s3.us-south.cloud-object-storage.appdomain.cloud"

# Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
# this returns a json list, it may be possible to use the endpoint based on the location of the code engine project. For example, if the code engine project is in Dallas, the endpoint would be s3.us-south.cloud-object-storage.appdomain.cloud. The region is in the CE subdomain assigned to all project resources. 

# Create client 
cos = ibm_boto3.client("s3",
    ibm_api_key_id=cos_api_key,
    ibm_service_instance_id=cos_instance_crn,
    config=Config(signature_version="oauth"),
    ibm_auth_endpoint="https://iam.cloud.ibm.com/identity/token",
    endpoint_url=cos_endpoint
)

# Define the keys we're interested in
keys_of_interest = {
    "Server Port",
    "Complete requests",
    "Failed requests",
    "Total transferred",
    "Requests per second",
    "Transfer rate",
}

conversion_dict = {
    "Server Port": int,
    "Complete requests": int,
    "Failed requests": int,
    "Total transferred": lambda s: int(s.rstrip(" bytes")),
    "Requests per second": lambda s: float(s.rstrip(" [#/sec] (mean)")),
    "Transfer rate": lambda s: float(s.rstrip("[Kbytes/sec] received")),
}

@click.command()
@click.option('-n', default=300, help='Number of requests to perform', type=int, required=False)
@click.option('-c', default=10, help='Number of multiple requests to make at a time', type=int, required=False)
@click.argument('url', required=True, type=str)
def main(n, c, url):
    # Ensure the URL ends with a trailing slash as ab requires it
    if not url.endswith('/'):
        url += '/'
    
    ab_args = ["ab", f"-n{n}", f"-c{c}", url]
    ab_result = run(
        args=ab_args,
        check=True,
        text=True,
        stdout=PIPE,
        stderr=DEVNULL,
    )

    ab_dict = {}
    for line in ab_result.stdout.splitlines()[6:]:
        if ":" not in line:
            continue

        key, value = line.split(":")
        key = key.strip()
        value = value.strip()

        transformed_key = key.lower().replace(" ", "_")

        # Only process keys of interest
        if transformed_key in [k.lower().replace(" ", "_") for k in keys_of_interest]:
            conversion_func = conversion_dict.get(key)
            if conversion_func is not None:
                value = conversion_func(value)

            ab_dict[transformed_key] = value

    json_data_str = json.dumps(ab_dict)

    sanitized_url = url.replace("http://", "").replace("https://", "").rstrip("/").replace("/", "-").replace(":", "-")
    current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M")
    item_name = f"{sanitized_url}-{current_datetime}-benchmark_results.json"
    create_text_file(json_data_str, cos_bucket, item_name )
    

def create_text_file(file_text, bucket_name, item_name):
    print("Creating new item: {0}".format(item_name))
    try:
        cos.put_object(Body=file_text, Bucket=bucket_name, Key=item_name)
        print("Item: {0} created!".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to create text file: {0}".format(e))


if __name__ == "__main__":
    main()
