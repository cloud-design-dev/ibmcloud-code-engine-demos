"""main entry point to webhook function"""
import logging
import os
import json
import httpx
from helpers import verify_payload, verify_signature, get_iam_token

HEADERS = {"Content-Type": "text/plain;charset=utf-8"}

logger = logging.getLogger()


def main(params):
    ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
    if not ibmcloud_api_key:
        raise ValueError("IBMCLOUD_API_KEY environment variable not found")

    secret_token = os.environ.get("WEBHOOK_SECRET")
    if not secret_token:
        raise ValueError("WEBHOOK_SECRET environment variable not found")

    payload_body = params
    headers = payload_body["__ce_headers"]
    signature_header = headers.get("X-Hub-Signature-256", None)
    image_tag = payload_body.get('workflow_run', {}).get('head_sha', None)
    if not image_tag:
        return {
            "headers": {"Content-Type": "application/json"},
            "statusCode": 400,
            "body": "Missing image tag"
        }
    verify_payload(payload_body)
    verify_signature(payload_body, secret_token, signature_header)

    iam_token = get_iam_token(ibmcloud_api_key)
    if not iam_token:
        return {
            "headers": HEADERS,
            "statusCode": 500,
            "body": "Failed to get IAM token",
        }

    code_engine_app = os.environ.get('CE_APP')
    code_engine_region = os.environ.get('CE_REGION')
    project_id = os.environ.get('CE_PROJECT_ID')
    app_endpoint = f"https://api.{code_engine_region}.codeengine.cloud.ibm.com/v2/projects/{project_id}/apps/{code_engine_app}"

    try:

        app_get = httpx.get(app_endpoint, headers = { "Authorization" : iam_token })
        results = app_get.json()
        etag = results['entity_tag']
        short_tag = image_tag[:8]
        update_headers = { "Authorization" : iam_token, "Content-Type" : "application/merge-patch+json", "If-Match" : etag }
        app_patch_model = { "image_reference": "private.us.icr.io/rtiffany/dts-ce-py-app:" + short_tag }
        app_update = httpx.patch(app_endpoint, headers = update_headers, json = app_patch_model)
        app_update.raise_for_status()
        app_json_payload = app_update.json()
        latest_ready_revision = app_json_payload.get('latest_ready_revision', None)

        data = {
            "headers": {"Content-Type": "application/json"},
            "statusCode": 200,
            "latest_ready_revision": latest_ready_revision,
            "body": "App updated successfully"
        }
 
        return {
                "headers": {"Content-Type": "application/json"},
                "statusCode": 200,
                "body": json.dumps(data)
                }
    except httpx.HTTPError as e:
        # Define results here to avoid the error
        results = {"error": str(e)}
        return {
                "headers": {"Content-Type": "application/json"},
                "statusCode": 500,
                "body": json.dumps(results)
        }