"""This is a sample code for Dataplex practice labs. This module is for reading metadata from gRPC metastore and manipulating it via py-Spark"""
import argparse
from pyspark.sql import SparkSession


def main(zone, tablename, updated_table_name):
    spark = SparkSession.builder.enableHiveSupport().getOrCreate()

    #Database:
    spark.sql("SHOW DATABASES").show()

    spark.sql(f"SHOW TABLES IN {zone}").show()

    #Rename
    print(f"ALTER TABLE {zone}.{tablename} RENAME TO {zone}.{updated_table_name}")
    sql_statment="ALTER TABLE {}.{} RENAME TO {}.{}".format(zone, tablename,zone, updated_table_name)
    spark.sql(sql_statment).show()
    print("Table renamed")
    spark.sql(f"SHOW TABLES IN {zone}").show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--zone", help="Zone for the dataplex")

    parser.add_argument("--tablename", help="Tablename for the dataplex")

    parser.add_argument("--updated_table_name", help="Updated table for the dataplex")

    args = parser.parse_args()
    main(args.zone, args.tablename, args.updated_table_name)
