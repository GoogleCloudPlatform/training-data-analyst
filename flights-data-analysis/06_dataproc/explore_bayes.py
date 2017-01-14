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

# this view can now be queried ...
flights.createOrReplaceTempView('flights')

# run SQL over registered view
results = spark.sql('SELECT COUNT(*) FROM flights WHERE DISTANCE < 300')
results.show()

# create hexbin distplot
#df = spark.sql('SELECT distance, dep_delay FROM flights WHERE RAND() < 0.001 AND dep_delay > -20 AND dep_delay < 30 AND distance < 2000')
#import seaborn as sns
#g = sns.jointplot(df['distance'], df['dep_delay'], kind="hex", size=10, joint_kws={'gridsize':20})

# quantization threshold for distance the hard way
results  = spark.sql("""
 SELECT 
   distance,
   COUNT(*) AS numflights
 FROM 
   (SELECT 
      CEILING(DISTANCE) AS distance,
      ARR_DELAY AS delay
    FROM flights)
 GROUP BY 
    distance
""")
results.show()
results.describe().show()

# the easy way
distthresh = flights.approxQuantile('DISTANCE', [0.2, 0.4, 0.6, 0.8], 0.05)
diststhresh

delaythresh = flights.approxQuantile('DEP_DELAY', [0.2, 0.4, 0.6, 0.8], 0.05)
delaythresh
