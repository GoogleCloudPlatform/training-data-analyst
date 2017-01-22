from pyspark.mllib.classification import LogisticRegressionWithLBFGS
from pyspark.mllib.regression import LabeledPoint
from pyspark.sql import SparkSession
from pyspark import SparkContext

sc = SparkContext('local', 'logistic')
spark = SparkSession \
    .builder \
    .appName("Logistic regression w/ Spark ML") \
    .getOrCreate()

BUCKET='cloud-training-demos-ml'

# read dataset
traindays = spark.read \
    .option("header", "true") \
    .csv('gs://cloud-training-demos-ml/flights/trainday.csv')
traindays.createOrReplaceTempView('traindays')

from pyspark.sql.types import StringType, FloatType, StructType, StructField

header = 'FL_DATE,UNIQUE_CARRIER,AIRLINE_ID,CARRIER,FL_NUM,ORIGIN_AIRPORT_ID,ORIGIN_AIRPORT_SEQ_ID,ORIGIN_CITY_MARKET_ID,ORIGIN,DEST_AIRPORT_ID,DEST_AIRPORT_SEQ_ID,DEST_CITY_MARKET_ID,DEST,CRS_DEP_TIME,DEP_TIME,DEP_DELAY,TAXI_OUT,WHEELS_OFF,WHEELS_ON,TAXI_IN,CRS_ARR_TIME,ARR_TIME,ARR_DELAY,CANCELLED,CANCELLATION_CODE,DIVERTED,DISTANCE,DEP_AIRPORT_LAT,DEP_AIRPORT_LON,DEP_AIRPORT_TZOFFSET,ARR_AIRPORT_LAT,ARR_AIRPORT_LON,ARR_AIRPORT_TZOFFSET,EVENT,NOTIFY_TIME'

def get_structfield(colname):
   if colname in ['ARR_DELAY', 'DEP_DELAY', 'DISTANCE', 'TAXI_OUT']:
      return StructField(colname, FloatType(), True)
   else:
      return StructField(colname, StringType(), True)

schema = StructType([get_structfield(colname) for colname in header.split(',')])


#inputs = 'gs://cloud-training-demos-ml/flights/tzcorr/all_flights-00000-*' # 1/30th
inputs = 'gs://cloud-training-demos-ml/flights/tzcorr/all_flights-*'  # FULL
flights = spark.read\
            .schema(schema)\
            .csv(inputs)
flights.createOrReplaceTempView('flights')

# separate training and validation data
from pyspark.sql.functions import rand

traindays = traindays.withColumn("holdout", rand() > 0.8)  # 80% of data is for training
traindays.createOrReplaceTempView('traindays')



# logistic regression
trainquery = """
SELECT
  *
FROM flights f
JOIN traindays t
ON f.FL_DATE == t.FL_DATE
WHERE
  t.is_train_day == 'True' AND
  t.holdout == False AND
  f.dep_delay IS NOT NULL AND 
  f.arr_delay IS NOT NULL
"""
traindata = spark.sql(trainquery)

def to_example(fields):
  return LabeledPoint(\
              float(fields['ARR_DELAY'] < 15), #ontime \
              [ \
                  fields['DEP_DELAY'], # DEP_DELAY \
                  fields['TAXI_OUT'], # TAXI_OUT \
                  fields['DISTANCE'], # DISTANCE \
              ])

examples = traindata.rdd.map(to_example)
lrmodel = LogisticRegressionWithLBFGS.train(examples, intercept=True)
lrmodel.setThreshold(0.7)

# save model
MODEL_FILE='gs://' + BUCKET + '/flights/sparkmloutput/model'
lrmodel.save(sc, MODEL_FILE)


# evaluate model on the heldout data
evalquery = trainquery.replace("t.holdout == False","t.holdout == True")
evaldata = spark.sql(evalquery)
examples = evaldata.rdd.map(to_example)
labelpred = examples.map(lambda p: (p.label, lrmodel.predict(p.features)))
def eval(labelpred):
    cancel = labelpred.filter(lambda (label, pred): pred == 0)
    nocancel = labelpred.filter(lambda (label, pred): pred == 1)
    corr_cancel = cancel.filter(lambda (label, pred): label == pred).count()
    corr_nocancel = nocancel.filter(lambda (label, pred): label == pred).count()
    return {'total_cancel': cancel.count(), \
            'correct_cancel': float(corr_cancel)/cancel.count(), \
            'total_noncancel': nocancel.count(), \
            'correct_noncancel': float(corr_nocancel)/nocancel.count() \
           }
print eval(labelpred)

