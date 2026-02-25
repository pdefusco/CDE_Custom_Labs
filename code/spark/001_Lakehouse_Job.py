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

#****************************************************************************
#  Rewritten to use Spark External Tables instead of Iceberg
#****************************************************************************

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.types import *
import sys
from utils import *

spark = SparkSession \
    .builder \
    .appName("BANK TRANSACTIONS BRONZE LAYER - EXTERNAL TABLES") \
    .enableHiveSupport() \
    .getOrCreate()

username = sys.argv[1]
storageLocation = sys.argv[2]

print("Username:", username)
print("Storage Location:", storageLocation)

db_name = f"HOL_DB_{username}"
base_path = f"{storageLocation}/external/{username}"

# ---------------------------------------------------
# DROP & CREATE DATABASE
# ---------------------------------------------------

spark.sql(f"DROP DATABASE IF EXISTS {db_name} CASCADE")
spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_name}")

# ---------------------------------------------------
# CREATE CUSTOMER (PII) EXTERNAL TABLE
# ---------------------------------------------------

pii_path = f"{storageLocation}/pii/{username}/pii"

piiDf = spark.read.options(header='True', delimiter=',') \
    .csv(pii_path)

# Cast latitude/longitude
piiDf = piiDf \
    .withColumn("address_latitude", F.col("address_latitude").cast("float")) \
    .withColumn("address_longitude", F.col("address_longitude").cast("float"))

cust_table_path = f"{base_path}/cust_table"

piiDf.write \
    .mode("overwrite") \
    .format("parquet") \
    .option("path", cust_table_path) \
    .saveAsTable(f"{db_name}.CUST_TABLE_{username}")

# ---------------------------------------------------
# CREATE REFINED CUSTOMER EXTERNAL TABLE
# ---------------------------------------------------

spark.sql(f"DROP TABLE IF EXISTS {db_name}.CUST_TABLE_REFINED_{username}")

spark.sql(f"""
CREATE TABLE {db_name}.CUST_TABLE_REFINED_{username}
USING PARQUET
LOCATION '{base_path}/cust_table_refined'
AS
SELECT
    NAME,
    EMAIL,
    BANK_COUNTRY,
    ACCOUNT_NO,
    CREDIT_CARD_NUMBER,
    CAST(ADDRESS_LATITUDE AS DOUBLE) AS ADDRESS_LATITUDE,
    CAST(ADDRESS_LONGITUDE AS DOUBLE) AS ADDRESS_LONGITUDE
FROM {db_name}.CUST_TABLE_{username}
""")

# Validate refined table
spark.sql(f"SELECT * FROM {db_name}.CUST_TABLE_REFINED_{username}").show()

# ---------------------------------------------------
# CREATE HISTORICAL TRANSACTIONS EXTERNAL TABLE
# ---------------------------------------------------

hist_trx_path = f"{storageLocation}/trans/{username}/rawtransactions"

transactionsDf = spark.read.json(hist_trx_path)
transactionsDf.printSchema()

# Flatten nested structures
transactionsDf = transactionsDf.select(flatten_struct(transactionsDf.schema))

# Cast numeric columns
cols = ["transaction_amount", "latitude", "longitude"]
transactionsDf = castMultipleColumns(transactionsDf, cols)

transactionsDf = transactionsDf.withColumn(
    "event_ts",
    F.col("event_ts").cast("timestamp")
)

hist_table_path = f"{base_path}/hist_trx"

transactionsDf.write \
    .mode("overwrite") \
    .format("parquet") \
    .option("path", hist_table_path) \
    .saveAsTable(f"{db_name}.HIST_TRX_{username}")

print("COUNT OF HIST_TRX TABLE")
spark.sql(f"SELECT COUNT(*) FROM {db_name}.HIST_TRX_{username}").show()

# ---------------------------------------------------
# SIMULATED "BRANCH" USING STAGING TABLE
# ---------------------------------------------------

# Load new transaction batch
trx_batch_path = f"{storageLocation}/trans/{username}/trx_batch_2"

trxBatchDf = spark.read.json(trx_batch_path)
trxBatchDf.printSchema()

cols = ["transaction_amount", "latitude", "longitude"]
trxBatchDf = castMultipleColumns(trxBatchDf, cols)

trxBatchDf = trxBatchDf.withColumn(
    "event_ts",
    F.col("event_ts").cast("timestamp")
)

# Write to staging external table
staging_path = f"{base_path}/hist_trx_staging"

trxBatchDf.write \
    .mode("overwrite") \
    .format("parquet") \
    .option("path", staging_path) \
    .saveAsTable(f"{db_name}.HIST_TRX_STAGING_{username}")

# Append staging data into main historical table
spark.sql(f"""
INSERT INTO {db_name}.HIST_TRX_{username}
SELECT * FROM {db_name}.HIST_TRX_STAGING_{username}
""")

print("COUNT AFTER APPEND")
spark.sql(f"SELECT COUNT(*) FROM {db_name}.HIST_TRX_{username}").show()
