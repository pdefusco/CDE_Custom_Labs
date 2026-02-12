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
from utils import *
from datetime import datetime
import sys, random, os, json, random, configparser

## CDE PROPERTIES

def parseProperties():
    """
    Method to parse total number of HOL participants argument
    """
    try:
        print("PARSING JOB ARGUMENTS...")
        maxParticipants = sys.argv[1]
        storageLocation = sys.argv[2]
        demo = sys.argv[3]
    except Exception as e:
        print("READING JOB ARG UNSUCCESSFUL")
        print('\n')
        print(f'caught {type(e)}: e')
        print(e)

    return maxParticipants, storageLocation, demo


def createSparkSession():
    """
    Method to create an Iceberg Spark Session
    """

    try:
        spark = SparkSession \
            .builder \
            .appName("DEMO LOAD") \
            .getOrCreate()
    except Exception as e:
        print("LAUNCHING SPARK SESSION UNSUCCESSFUL")
        print('\n')
        print(f'caught {type(e)}: e')
        print(e)

    return spark


def createTransactionData(spark, demo):
    """
    Method to create a bank Transactions dataframe using the dbldatagen and Faker frameworks
    """

    if demo == "manufacturing":

        try:
            print("CREATING CAR SALES DF...\n")
            dg = CarSalesDataGen(spark)
            transactionsDf = dg.salesDataGen()
        except Exception as e:
            print("CREATING TRANSACTION DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    elif demo == "bank":

        try:
            print("CREATING bank TRANSACTIONS DF...\n")
            dg = BankDataGen(spark)
            transactionsDf = dg.transactionsDataGen()
        except Exception as e:
            print("CREATING TRANSACTION DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    else:
        print("Wrong demo name was used. Please use either 'bank' or 'manufacturing'.")

    return transactionsDf


def createTransactionBatch(spark, demo):
    """
    Method to create a bank Transactions dataframe using the dbldatagen and Faker frameworks
    """

    if demo == "manufacturing":

        try:
            print("CREATING CAR SALES DF...\n")
            dg = CarSalesDataGen(spark)
            transactionsBatchDf = dg.salesBatchDataGen()
        except Exception as e:
            print("CREATING TRANSACTION DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    elif demo == "bank":

        try:
            print("CREATING bank TRANSACTIONS 1 DF BATCH...\n")
            dg = BankDataGen(spark)
            transactionsBatchDf = dg.transactionsBatchDataGen()
        except Exception as e:
            print("CREATING TRANSACTION DATA 1 UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    else:
        print("Wrong demo name was used. Please use either 'bank' or 'manufacturing'.")

    return transactionsBatchDf


def createSecondTransactionBatch(spark, demo):
    """
    Method to create a bank Transactions dataframe using the dbldatagen and Faker frameworks
    """

    if demo == "manufacturing":

        try:
            print("CREATING CAR SALES DF...\n")
            dg = CarSalesDataGen(spark)
            secondTransactionsBatchDf = dg.secondSalesBatchDataGen()
        except Exception as e:
            print("CREATING CAR DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    elif demo == "bank":

        try:
            print("CREATING bank TRANSACTIONS 2 BATCH DF...\n")
            dg = BankDataGen(spark)
            secondTransactionsBatchDf = dg.secondTransactionsBatchDataGen()
        except Exception as e:
            print("CREATING TRANSACTION DATA 2 UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    else:
        print("Wrong demo name was used. Please use either 'bank' or 'manufacturing'.")

    return secondTransactionsBatchDf


def createPiiData(spark, demo):
    """
    Method to create a bank Pii dataframe using the dbldatagen and Faker frameworks
    """

    if demo == "manufacturing":

        try:
            print("CREATING CAR SALES PII DF...\n")
            dg = CarSalesDataGen(spark)
            piiDf = dg.piiDataGen()
        except Exception as e:
            print("CREATING CAR SALES PII DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    elif demo == "bank":

        try:
            print("CREATING bank PII DF...\n")
            dg = BankDataGen(spark)
            piiDf = dg.piiDataGen()
        except Exception as e:
            print("CREATING bank PII DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    else:
        print("Wrong demo name was used. Please use either 'bank' or 'manufacturing'.")

    return piiDf


def saveTransactionData(transactionsDf, storageLocation, username, demo):
    """
    Method to save bank transactions to Cloud Storage in Json format
    """

    print("SAVING bank TRANSACTIONS TO JSON IN CLOUD STORAGE...\n")


    if demo == "manufacturing":

        try:
            transactionsDf. \
                write. \
                format("json"). \
                mode("overwrite"). \
                save("{0}/carsales/{1}/rawcarsales".format(storageLocation, username))
        except Exception as e:
            print("SAVING SYNTHETIC CAR SALES DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    elif demo == "bank":

        try:
            transactionsDf. \
                write. \
                format("json"). \
                mode("overwrite"). \
                save("{0}/trans/{1}/rawtransactions".format(storageLocation, username))
        except Exception as e:
            print("SAVING SYNTHETIC TRANSACTION DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    else:
        print("Wrong demo name was used. Please use either 'bank' or 'manufacturing'.")


def saveTransactionBatch(transactionsBatchDf, storageLocation, username, demo):
    """
    Method to save bank transactions to Cloud Storage in Json format
    """

    print("SAVING TRANSACTIONS BATCH 1 TO JSON IN CLOUD STORAGE...\n")

    if demo == "bank":

        try:
            transactionsBatchDf. \
                write. \
                format("json"). \
                mode("overwrite"). \
                save("{0}/trans/{1}/trx_batch_1".format(storageLocation, username))
        except Exception as e:
            print("SAVING TRANSACTION BATCH 1 UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    elif demo == "manufacturing":

        try:
            transactionsBatchDf. \
                write. \
                format("json"). \
                mode("overwrite"). \
                save("{0}/carsales/{1}/sales_batch_1".format(storageLocation, username))
        except Exception as e:
            print("SAVING TRANSACTION BATCH 1 UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    else:
        print("Wrong demo name was used. Please use either 'bank' or 'manufacturing'.")


def saveSecondTransactionBatch(secondTransactionsBatchDf, storageLocation, username, demo):
    """
    Method to save bank transactions to Cloud Storage in Json format
    """

    if demo == "bank":

        print("SAVING TRANSACTIONS BATCH 2 TO JSON IN CLOUD STORAGE...\n")

        try:
            secondTransactionsBatchDf. \
                write. \
                format("json"). \
                mode("overwrite"). \
                save("{0}/trans/{1}/trx_batch_2".format(storageLocation, username))
        except Exception as e:
            print("SAVING TRANSACTION BATCH 2 UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    elif demo == "manufacturing":

        print("SAVING CAR SALES BATCH 2 TO JSON IN CLOUD STORAGE...\n")

        try:
            secondTransactionsBatchDf. \
                write. \
                format("json"). \
                mode("overwrite"). \
                save("{0}/carsales/{1}/sales_batch_2".format(storageLocation, username))
        except Exception as e:
            print("SAVING CAR SALES BATCH 2 UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    else:
        print("Wrong demo name was used. Please use either 'bank' or 'manufacturing'.")


def savePiiData(piiDf, storageLocation, username, demo):
    """
    Method to save bank transactions to Cloud Storage in csv format
    """

    if demo == "bank":

        print("SAVING PII DF TO CSV IN CLOUD STORAGE...\n")

        try:
            piiDf \
                .write. \
                mode('overwrite') \
                .options(header='True', delimiter=',') \
                .csv("{0}/pii/{1}/pii".format(storageLocation, username))
        except Exception as e:
            print("SAVING SYNTHETIC PII DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    elif demo == "manufacturing":

        print("SAVING PII DF TO CSV IN CLOUD STORAGE...\n")

        try:
            piiDf \
                .write. \
                mode('overwrite') \
                .options(header='True', delimiter=',') \
                .csv("{0}/pii/{1}/pii".format(storageLocation, username))
        except Exception as e:
            print("SAVING SYNTHETIC PII DATA UNSUCCESSFUL")
            print('\n')
            print(f'caught {type(e)}: e')
            print(e)

    else:
        print("Wrong demo name was used. Please use either 'bank' or 'manufacturing'.")


def main():

    maxParticipants, storageLocation, demo = parseProperties()

    print("\nMax Participants: ", maxParticipants)
    print("\nStorage Location: ", storageLocation)
    print("\nDemo: ", demo)

    spark = createSparkSession()

    if demo == "manufacturing":

        for i in range(int(maxParticipants)):
            if i+1 < 10:
                username = "user00" + str(i+1)
            elif i+1 > 9 and i+1 < 99:
                username = "user0" + str(i+1)
            elif i+1 > 99:
                username = "user" + str(i+1)

            print("PROCESSING USER {}...\n".format(username))

            carSalesDf = createTransactionData(spark, demo)
            saveTransactionData(carSalesDf, storageLocation, username, demo)

            piiDf = createPiiData(spark, demo)
            savePiiData(piiDf, storageLocation, username, demo)

            transactionsBatchDf = createTransactionBatch(spark, demo)
            saveTransactionBatch(transactionsBatchDf, storageLocation, username, demo)

            secondTransactionsBatchDf = createSecondTransactionBatch(spark, demo)
            saveSecondTransactionBatch(secondTransactionsBatchDf, storageLocation, username, demo)

    elif demo == "bank":

        for i in range(int(maxParticipants)):
            if i+1 < 10:
                username = "user00" + str(i+1)
            elif i+1 > 9 and i+1 < 99:
                username = "user0" + str(i+1)
            elif i+1 > 99:
                username = "user" + str(i+1)

            print("PROCESSING USER {}...\n".format(username))

            bankTransactionsDf = createTransactionData(spark, demo)
            saveTransactionData(bankTransactionsDf, storageLocation, username, demo)

            piiDf = createPiiData(spark, demo)
            savePiiData(piiDf, storageLocation, username, demo)

            transactionsBatchDf = createTransactionBatch(spark, demo)
            saveTransactionBatch(transactionsBatchDf, storageLocation, username, demo)

            secondTransactionsBatchDf = createSecondTransactionBatch(spark, demo)
            saveSecondTransactionBatch(secondTransactionsBatchDf, storageLocation, username, demo)

    else:
        print("Wrong demo name was used. Please use either 'bank' or 'manufacturing'.")

if __name__ == "__main__":
    main()
