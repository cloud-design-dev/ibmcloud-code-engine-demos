# Python function for IBM Cloud Code Engine
--------

Simple function that takes `cos_endpoint` and `cos_bucket` as params and writes the environments variables to a JSON file in `cos_bucket`

## Create function

```shell
ibmcloud ce fn create --name FUNCTION_NAME --runtime python-3.11 --build-source . 
```

If everything works as expected you should get a URL once the build and push have completed. The URL is constructed in the form of `FUNCTION_NAME.CE_SUBDOMAIN.REGION.codeengine.appdomain.cloud`. **note**: if you set the function visibility to `private`, the FUNCTION_URL will be https://FUNCTION_NAME.CE_SUBDOMAIN.private.REGION.codeengine.appdomain.cloud


Set this as the environment variable "FUNCTION_URL"

```
export FUNCTION_URL="https://FUNCTION_NAME.CE_SUBDOMAIN.REGION.codeengine.appdomain.cloud"
```


## Test function

```
curl -X POST -H "Content-Type: application/json" -d '{"cos_bucket":"YOUR_COS_BUCKET", "cos_endpoint":"COS_ENDPOINT"}' "${FUNCTION_URL}"

```
