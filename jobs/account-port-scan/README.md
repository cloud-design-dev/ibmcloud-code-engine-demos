# Scan Floating IPs and Classic IaaS

This python script will scan all the Floating IPs associated with your IBM Cloud account as well as the classic virtual and bare metal servers with public IPs. 

## Run locally

### Clone the repository

The first step is to clone the respository and change in to our port scan directory:

```shell
git clone https://github.com/cloud-design-dev/dts-ce-demo.git
cd dts-ce-demo/jobs/account-port-scan
```

### Set the classic username and cloud API keys

```shell
export IBMCLOUD_CLASSIC_USERNAME="YOUR_CLASSIC_IAAS_USER"
export IBMCLOUD_CLASSIC_API_KEY="YOUR_CLASSIC_IAAS_API_KEY"
export IBMCLOUD_API_KEY="YOUR_IBMCLOUD_API_KEY"
```

### Install python requirements

Install the required python SDKs to interact with the classic and vpc resources. 

```shell
pip install -r requirements 
```

### Run script

With the variables set and modules installed, you can run the script:

```
python app.py
```
