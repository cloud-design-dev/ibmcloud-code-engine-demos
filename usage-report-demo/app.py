#!/usr/bin/env python3
# Author: Ryan Tiffany
# Copyright (c) 2024
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import json
import click
import logging
from ibm_platform_services import IamIdentityV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import pandas as pd
import pytz
from rich.console import Console
from rich.table import Table
from ibm_cloud_sdk_core import ApiException

ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")
