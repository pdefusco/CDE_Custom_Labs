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
#  ANALYTICS LAYER - READ EXTERNAL TABLES + TRANSFORM + PRINT TO STDOUT
#****************************************************************************

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import *
import sys
import math

spark = SparkSession \
    .builder \
    .appName("BANK TRANSACTIONS ANALYTICS LAYER") \
    .enableHiveSupport() \
    .getOrCreate()

username = sys.argv[1]
print("Username:", username)

db_name = f"HOL_DB_{username}"

# ---------------------------------------------------
# READ TABLES
# ---------------------------------------------------

custDf = spark.sql(f"SELECT * FROM {db_name}.CUST_TABLE_REFINED_{username}")
trxDf = spark.sql(f"SELECT * FROM {db_name}.HIST_TRX_{username}")

print("Customer Count:", custDf.count())
print("Transaction Count:", trxDf.count())

# ---------------------------------------------------
# SIMPLE TRANSFORMATIONS
# ---------------------------------------------------

# 1. Add time features
trxDf = trxDf \
    .withColumn("transaction_date", F.to_date("event_ts")) \
    .withColumn("transaction_hour", F.hour("event_ts")) \
    .withColumn("is_weekend",
                F.when(F.dayofweek("event_ts").isin([1,7]), 1).otherwise(0))

# 2. Bucket transaction amount
trxDf = trxDf.withColumn(
    "amount_bucket",
    F.when(F.col("transaction_amount") < 100, "LOW")
     .when(F.col("transaction_amount") < 1000, "MEDIUM")
     .otherwise("HIGH")
)

# ---------------------------------------------------
# JOIN CUSTOMERS WITH TRANSACTIONS
# ---------------------------------------------------

joinedDf = trxDf.join(
    custDf,
    trxDf.account_no == custDf.account_no,
    "left"
)

# ---------------------------------------------------
# ADVANCED TRANSFORMATIONS
# ---------------------------------------------------

# 1. Window: Running total per account
windowSpec = Window.partitionBy("account_no") \
                   .orderBy("event_ts") \
                   .rowsBetween(Window.unboundedPreceding, Window.currentRow)

joinedDf = joinedDf.withColumn(
    "running_total",
    F.sum("transaction_amount").over(windowSpec)
)

# 2. Detect unusually large transactions (z-score per account)

statsDf = joinedDf.groupBy("account_no").agg(
    F.avg("transaction_amount").alias("avg_amt"),
    F.stddev("transaction_amount").alias("std_amt")
)

joinedDf = joinedDf.join(statsDf, "account_no")

joinedDf = joinedDf.withColumn(
    "z_score",
    (F.col("transaction_amount") - F.col("avg_amt")) / F.col("std_amt")
)

joinedDf = joinedDf.withColumn(
    "is_anomaly",
    F.when(F.abs(F.col("z_score")) > 3, 1).otherwise(0)
)

# 3. Geospatial distance from registered customer address (Haversine)

def haversine(lat1, lon1, lat2, lon2):
    return 6371 * 2 * F.asin(
        F.sqrt(
            F.pow(F.sin((F.radians(lat2 - lat1)) / 2), 2) +
            F.cos(F.radians(lat1)) *
            F.cos(F.radians(lat2)) *
            F.pow(F.sin((F.radians(lon2 - lon1)) / 2), 2)
        )
    )

joinedDf = joinedDf.withColumn(
    "distance_from_home_km",
    haversine(
        F.col("address_latitude"),
        F.col("address_longitude"),
        F.col("latitude"),
        F.col("longitude")
    )
)

# Flag suspicious distance
joinedDf = joinedDf.withColumn(
    "far_from_home_flag",
    F.when(F.col("distance_from_home_km") > 500, 1).otherwise(0)
)

# 4. Daily aggregation per country

dailyCountryAgg = joinedDf.groupBy(
    "bank_country",
    "transaction_date"
).agg(
    F.count("*").alias("total_transactions"),
    F.sum("transaction_amount").alias("total_amount"),
    F.avg("transaction_amount").alias("avg_transaction")
)

# ---------------------------------------------------
# OUTPUT EVERYTHING TO STDOUT
# ---------------------------------------------------

print("\n===== SAMPLE ENRICHED TRANSACTIONS =====")
joinedDf.select(
    "account_no",
    "transaction_amount",
    "amount_bucket",
    "running_total",
    "z_score",
    "is_anomaly",
    "distance_from_home_km",
    "far_from_home_flag"
).show(50, truncate=False)

print("\n===== DAILY COUNTRY AGGREGATES =====")
dailyCountryAgg.show(50, truncate=False)

print("\n===== TOP 10 HIGH-RISK TRANSACTIONS =====")
joinedDf.orderBy(
    F.desc("is_anomaly"),
    F.desc("distance_from_home_km")
).select(
    "account_no",
    "transaction_amount",
    "z_score",
    "distance_from_home_km",
    "far_from_home_flag"
).show(10, truncate=False)

print("Analytics job completed successfully.")
