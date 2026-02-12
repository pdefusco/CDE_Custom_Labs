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

from os.path import exists
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.types import *
import sys

spark = SparkSession \
    .builder \
    .appName("BANK TRANSACTIONS SAMPLE APP") \
    .getOrCreate()

storageLocation = sys.argv[1] #"s3a://go01-demo/data"
username = sys.argv[2] #user001
#username = "user001"

### LOAD HISTORICAL TRANSACTIONS FILE FROM CLOUD STORAGE
transactionsDf = spark.read.json("{0}/trans/{1}/rawtransactions".format(storageLocation, username))
transactionsDf.printSchema()

spark.sql("""CREATE DATABASE
                IF NOT EXISTS
                SPARK_CATALOG.HOL_DB_{}""".format(username))

spark.sql("""DROP TABLE
            IF EXISTS spark_catalog.HOL_DB_{0}.TRANSACTIONS_{0}
            PURGE""".format(username))

transactionsDf.writeTo("SPARK_CATALOG.HOL_DB_{0}.TRANSACTIONS_{0}".format(username))\
                .using("iceberg")\
                .tableProperty("write.format.default", "parquet")\
                .createOrReplace()

trxBatchDf = spark.read.schema("""credit_card_number string,
                                    credit_card_provider string,
                                    event_ts timestamp,
                                    latitude double,
                                    longitude double,
                                    transaction_amount long,
                                    transaction_currency string,
                                    transaction_type string""")\
                        .json("{0}/trans/{1}/trx_batch_1".format(storageLocation, username))
trxBatchDf.createOrReplaceTempView("trx_batch")

# PRE-MERGE COUNTS BY TRANSACTION TYPE:
spark.sql("""SELECT TRANSACTION_TYPE,
                COUNT(*)
                FROM spark_catalog.HOL_DB_{0}.TRANSACTIONS_{0}
                GROUP BY TRANSACTION_TYPE""".format(username)).show()

# MERGE OPERATION
spark.sql("""MERGE INTO spark_catalog.HOL_DB_{0}.TRANSACTIONS_{0} t
                USING (SELECT * FROM trx_batch) s
                ON t.credit_card_number = s.credit_card_number
                WHEN MATCHED AND t.transaction_amount < 1000
                AND t.transaction_currency != "CHF"
                THEN UPDATE SET t.transaction_type = "invalid"
                WHEN NOT MATCHED THEN INSERT *""".format(username))

# POST-MERGE COUNT:
spark.sql("""SELECT TRANSACTION_TYPE,
                COUNT(*)
                FROM spark_catalog.HOL_DB_{0}.TRANSACTIONS_{0}
                GROUP BY TRANSACTION_TYPE""".format(username)).show()

# ICEBERG TABLE HISTORY (SHOWS EACH SNAPSHOT AND TIMESTAMP)
spark.sql("""SELECT *
            FROM spark_catalog.HOL_DB_{0}.TRANSACTIONS_{0}.history""".format(username)).show()

# ICEBERG TABLE SNAPSHOTS (USEFUL FOR INCREMENTAL QUERIES AND TIME TRAVEL)
spark.sql("""SELECT *
            FROM spark_catalog.HOL_DB_{0}.TRANSACTIONS_{0}.snapshots""".format(username)).show()

# APPEND SECOND DATA BATCH
trxBatchDf = spark.read.schema("""credit_card_number string, credit_card_provider string,
                                    event_ts timestamp, latitude double, longitude double, transaction_amount long,
                                    transaction_currency string, transaction_type string""")\
                    .json("{0}/trans/{1}/trx_batch_2".format(storageLocation, username))

trxBatchDf.writeTo("spark_catalog.HOL_DB_{0}.TRANSACTIONS_{0}".format(username))\
            .using("iceberg")\
            .append()

# STORE FIRST AND LAST SNAPSHOT ID'S FROM SNAPSHOTS TABLE
snapshots_df = spark.sql("""SELECT *
                            FROM spark_catalog.HOL_DB_{0}.TRANSACTIONS_{0}.snapshots;""".format(username))

last_snapshot = snapshots_df\
                    .select("snapshot_id")\
                    .tail(1)[0][0]

second_snapshot = snapshots_df\
                    .select("snapshot_id")\
                    .collect()[1][0]

incReadDf = spark.read\
    .format("iceberg")\
    .option("start-snapshot-id", second_snapshot)\
    .option("end-snapshot-id", last_snapshot)\
    .load("spark_catalog.HOL_DB_{0}.TRANSACTIONS_{0}".format(username))

print("Incremental Report:")
incReadDf.show()
