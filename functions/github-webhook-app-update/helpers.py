import json
import hashlib
import hmac
import httpx

HEADERS = {"Content-Type": "text/plain;charset=utf-8"}


def verify_payload(params):
    """Verify X-Hub-Signature-256, commits, & head_commit.id exist."""
    if (
        "__ce_headers" not in params
        or "X-Hub-Signature-256" not in params["__ce_headers"]
    ):
        return {
            "headers": HEADERS,
            "body": "Missing params.headers.X-Hub-Signature-256",
        }

    if "workflow_run" not in params:
        return {
            "headers": HEADERS,
            "body": "Missing params.workflow_run",
        }

    return None

def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    for value in payload_body:
        value: str
        if value.startswith("__"):
            del value
    payload_body_bytes = json.dumps(payload_body).encode('utf-8')

    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body_bytes, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        return {
            "statusCode": 403,
            "headers": HEADERS,
            "body": "Request signatures didn't match!",
        }

    return None

def get_iam_token(ibmcloud_api_key):
    """Get IAM token from IBM Cloud using API key."""
    hdrs = { "Accept" : "application/json", "Content-Type" : "application/x-www-form-urlencoded" }
    iam_params = { "grant_type" : "urn:ibm:params:oauth:grant-type:apikey", "apikey" : ibmcloud_api_key }
    resp = httpx.post('https://iam.cloud.ibm.com/identity/token', data = iam_params, headers = hdrs)
    resp.raise_for_status() 
    return resp.json().get('access_token', None)

