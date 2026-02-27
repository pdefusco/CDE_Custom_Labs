import sys
from pyspark.sql import SparkSession
import configparser

spark = SparkSession\
    .builder\
    .appName("PythonSQL")\
    .getOrCreate()

print("JOB ARGUMENTS")
print(sys.argv)
print(sys.argv[0])
print(sys.argv[1])
print(sys.argv[2])
print(sys.argv[3])

dbname = sys.argv[1]
tablename = sys.argv[2]

config = configparser.ConfigParser()
config.read('/app/mount/{}'.format(sys.argv[3]))
property_3=config.get("general","property_3")
property_4=config.get("general","property_4")

def myFunction(dbname, tablename, property_1, property_2):
    print("DBNAME\n")
    print(dbname)
    print("TABLNAME\n")
    print(tablename)
    print("PROPERTY1\n")
    print(property_1)
    print("PROPERTY2\n")
    print(property_2)
    print("COMPLETE!\n")

# A list of Rows. Infer schema from the first row, create a DataFrame and print the schema

myFunction(dbname, tablename, property_3, property_4)
