#!/usr/bin/env python

from pyspark.sql.types import StringType, FloatType, StructType, StructField

# create spark session to imitate the PySpark shell
from pyspark.sql import SparkSession
spark = SparkSession \
    .builder \
    .appName("Bayes classification using Spark") \
    .getOrCreate()

# schema
header = 'FL_DATE,UNIQUE_CARRIER,AIRLINE_ID,CARRIER,FL_NUM,ORIGIN_AIRPORT_ID,ORIGIN_AIRPORT_SEQ_ID,ORIGIN_CITY_MARKET_ID,ORIGIN,DEST_AIRPORT_ID,DEST_AIRPORT_SEQ_ID,DEST_CITY_MARKET_ID,DEST,CRS_DEP_TIME,DEP_TIME,DEP_DELAY,TAXI_OUT,WHEELS_OFF,WHEELS_ON,TAXI_IN,CRS_ARR_TIME,ARR_TIME,ARR_DELAY,CANCELLED,CANCELLATION_CODE,DIVERTED,DISTANCE,DEP_AIRPORT_LAT,DEP_AIRPORT_LON,DEP_AIRPORT_TZOFFSET,ARR_AIRPORT_LAT,ARR_AIRPORT_LON,ARR_AIRPORT_TZOFFSET,EVENT,NOTIFY_TIME'

# all the types are string, except for 3 columns ...
def get_structfield(colname):
   if colname in ['ARR_DELAY', 'DEP_DELAY', 'DISTANCE']:
      return StructField(colname, FloatType(), True)
   else:
      return StructField(colname, StringType(), True)

schema = StructType([get_structfield(colname) for colname in header.split(',')])

# load CSV file
flights = spark.read\
            .schema(schema)\
            .csv('gs://cloud-training-demos-ml/flights/tzcorr/all_flights-00000*')

# filter to retain only training days
traindays = spark.read\
            .option('header', True)\
            .csv('gs://cloud-training-demos-ml/flights/trainday.csv')
traindays = traindays.filter(traindays['is_train_day'] == 'True')
# traindays.count()

#flights.count()
flights = flights.join(traindays, flights.FL_DATE == traindays.FL_DATE)
#flights.count()

# this view can now be queried ...
flights.createOrReplaceTempView('flights')

distthresh = flights.approxQuantile('DISTANCE', [0.2, 0.4, 0.6, 0.8], 0.05)
