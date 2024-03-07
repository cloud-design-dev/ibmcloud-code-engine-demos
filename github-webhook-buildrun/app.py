#!/usr/bin/env python3

import os
import json
import logging
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from ibm_code_engine_sdk.code_engine_v2 import CodeEngineV2

ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")

ce_api_url = os.environ.get('CE_API_BASE_URL') 
if not ce_api_url:
    raise ValueError("CE_API_BASE_URL environment variable not found. We are not running in Code Engine")

project_id = os.environ.get('CE_PROJECT_ID')
if not project_id:
    raise ValueError("CE_PROJECT_ID environment variable not found. We are not running in Code Engine")

output_image = os.environ.get('CE_OUTPUT_IMAGE')
output_secret = os.environ.get('CE_OUTPUT_SECRET')
GitHubSecret = os.environ.get("GIT_SECRET")


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


def code_engine_client():
    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    service = CodeEngineV2(authenticator=authenticator)
    service_url = ce_api_url + "/v2"
    service.set_service_url(service_url)
    return service


def create_build_run():
    client = code_engine_client()
    try:
        response = client.create_build_run(
            project_id=project_id,
            source_url=source_url,
            output_image=output_image,
            output_secret=output_secret
        ).get_result()
        return response
    except ApiException as e:
        logging.error("API exception {}.".format(str(e)))
        quit(1)


# if __name__ == '__main__':
#     cli()
