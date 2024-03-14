import os
import ibm_vpc
import json
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException

def main(params):
    ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
    if not ibmcloud_api_key:
        raise ValueError("IBMCLOUD_API_KEY environment variable not found")

    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    region = params.get("region")
    instance_name = params.get("instance_name")
    vpc_client = ibm_vpc.VpcV1(authenticator=authenticator)
    vpc_client.set_service_url(f'https://{region}.iaas.cloud.ibm.com/v1')
    try:
        instances = vpc_client.list_instances().get_result()
        instance_id = [instance['id'] for instance in instances['instances'] if instance['name'] == instance_name]
        stop_instance = vpc_client.create_instance_action(instance_id=instance_id[0], type='stop')
        result = stop_instance.get_result()
        return {
            "headers": {
                "Content-Type": "application/json",
            },
            "statusCode": 200,
            "body": json.dumps(result)
        }
    except ApiException as e:
        return {
            "headers": {
                "Content-Type": "application/json",
            },
            "statusCode": e.code,
            "body": json.dumps({"error": "Failed to retrieve VPCs", "details": str(e)})
        }

