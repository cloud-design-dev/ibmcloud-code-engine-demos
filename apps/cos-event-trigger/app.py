#!/usr/bin/env python3
from flask import Flask, request, jsonify
import json
import os
import httpx
from datetime import datetime

app = Flask(__name__)

# IBM Cloud Logging configuration
IBM_INSTANCE_ID = os.environ.get("IBM_INSTANCE_ID")
CE_REGION = os.environ.get("CE_REGION", "us-south")
IBM_APP_NAME = os.environ.get("CE_APP", "cos-event-trigger")
IBM_SUBSYSTEM_NAME = os.environ.get("CE_PROJECT_ID", "event-processor")
IBM_LOG_SEVERITY = os.environ.get("IBM_LOG_SEVERITY", "info")

def get_iam_token():
    ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
    if not ibmcloud_api_key:
        raise ValueError("IBMCLOUD_API_KEY environment variable not found")
    hdrs = { 'Accept': 'application/json', 'Content-Type' : 'application/x-www-form-urlencoded' }
    params = { 'grant_type' : 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': ibmcloud_api_key }
    resp = httpx.post('https://iam.cloud.ibm.com/identity/token', data = params, headers = hdrs)
    # raise exception if invalid status
    resp.raise_for_status()
    json_payload = resp.json()
    token = json_payload['access_token']
    return token

def send_to_ibm_logging(log_text, severity=None):
    """Send log to IBM Cloud Logging"""
    if not IBM_INSTANCE_ID:
        print("IBM Cloud Logging not configured. Set IBM_INSTANCE_ID and IBM_IAM_TOKEN environment variables.")
        return False
    
    url = f"https://{IBM_INSTANCE_ID}.ingress.{CE_REGION}.logs.cloud.ibm.com/logs/v1/singles"
    
    iam_token = get_iam_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": iam_token
    }
    
    payload = [{
        "applicationName": IBM_APP_NAME,
        "subsystemName": IBM_SUBSYSTEM_NAME,
        "severity": severity or IBM_LOG_SEVERITY,
        "text": log_text
    }]
    
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        if response.status_code >= 200 and response.status_code < 300:
            print(f"Successfully sent log to IBM Cloud Logging: {response.status_code}")
            return True
        else:
            print(f"Failed to send log to IBM Cloud Logging: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"Error sending log to IBM Cloud Logging: {str(e)}")
        return False

# Equivalent to EventStats in Go
class EventStats:
    def __init__(self):
        self.by_bucket = {}
        self.by_type = {}
        self.by_object = {}
    
    def to_dict(self):
        return {
            "by_bucket": self.by_bucket,
            "by_type": self.by_type,
            "by_object": self.by_object
        }

# Global stats object
stats = EventStats()

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify(stats.to_dict())

@app.route('/', methods=['POST'])
def handle_event():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = request.data.decode('utf-8')
    
    # Parse the event data
    event = json.loads(body)
    
    # Update stats
    bucket = event.get('bucket', 'unknown')
    operation = event.get('operation', 'unknown')
    key = event.get('key', 'unknown')
    
    stats.by_bucket[bucket] = stats.by_bucket.get(bucket, 0) + 1
    stats.by_type[operation] = stats.by_type.get(operation, 0) + 1
    stats.by_object[key] = stats.by_object.get(key, 0) + 1
    
    print(f"{current_time} - Received:")
    print(f"\nBody: {body}")
    
    # Send to IBM Cloud Logging
    log_message = f"COS Event: {operation} on {bucket}/{key} - {body}"
    send_to_ibm_logging(log_message)
    
    return "OK"

if __name__ == '__main__':
    print("Listening on port 8080")
    app.run(host='0.0.0.0', port=8080)