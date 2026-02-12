#****************************************************************************
# (C) Cloudera, Inc. 2020-2023
#  All rights reserved.
#
#  Applicable Open Source License: GNU Affero General Public License v3.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
#
# #  Author(s): Paul de Fusco
#***************************************************************************/

#!pip install "cdepy>=0.1.17"

from cdepy import cdeconnection
from cdepy import cdejob
from cdepy import cdemanager
from cdepy import cderesource
from cdepy import utils

DEV_JOBS_API_URL = "https://h84gnslb.cde-mbk2gj8x.pdf-3425.a465-9q4k.cloudera.site/dex/api/v1"
PRD_JOBS_API_URL = "https://rncv8wqr.cde-mbk2gj8x.pdf-3425.a465-9q4k.cloudera.site/dex/api/v1"
hol_username = "user001"

WORKLOAD_USER = "pauldefusco" #Your CDP Workload Username
WORKLOAD_PASSWORD = "<>" #Your CDP Workload Password

VC_URLS = [DEV_JOBS_API_URL, PRD_JOBS_API_URL]

for VC_URL in VC_URLS:

  myCdeConnection = cdeconnection.CdeConnection(VC_URL, WORKLOAD_USER, WORKLOAD_PASSWORD)
  myCdeConnection.setToken()

  myCdeClusterManager = cdemanager.CdeClusterManager(myCdeConnection)
  jobsList = myCdeClusterManager.listJobs()

  import json
  jobsListDict = json.loads(jobsList)

  import pandas as pd
  import numpy as np

  jobsDf = pd.DataFrame(jobsListDict['jobs'])

  userJobsDf = jobsDf[jobsDf['name'].str.contains(hol_username)]

  userAirflowJobsDf = userJobsDf[userJobsDf['type'] == 'airflow']
  userSparkJobsDf = userJobsDf[userJobsDf['type'] == 'spark']

  if len(userAirflowJobsDf['name'])>0:
    for airflowJobName in userAirflowJobsDf['name']:
      myCdeClusterManager.deleteJob(airflowJobName)

  if len(userSparkJobsDf['name'])>0:
    for sparkJobName in userSparkJobsDf['name']:
      myCdeClusterManager.deleteJob(sparkJobName)
