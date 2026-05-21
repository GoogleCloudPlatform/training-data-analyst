"""This is a sample code for Dataplex practice labs. This module is for reading metadata from gRPC metastore and manipulating it via py-Spark"""
import argparse
from pyspark.sql import SparkSession


def main(zone, tablename):
    spark = SparkSession.builder.enableHiveSupport().getOrCreate()

    #Database:
    print("Show all the databases from dataplex lake")
    spark.sql("SHOW DATABASES").show()

    #Tables
    print("Show all the table from dataplex zone")
    spark.sql(f"SHOW TABLES IN {zone}").show()

    #Query
    print("Show sample records from {}.{}".format(zone, tablename))
    sql_statment="SELECT * FROM {}.{} LIMIT 10".format(zone, tablename)
    spark.sql(sql_statment).show()
    print("Job Completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--zone", help="Zone for the dataplex")

    parser.add_argument("--tablename", help="Tablename for the dataplex")


    args = parser.parse_args()
    main(args.zone, args.tablename)
