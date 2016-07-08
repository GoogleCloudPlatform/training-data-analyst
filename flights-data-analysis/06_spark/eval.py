from pyspark.mllib.classification import LogisticRegressionModel
from pyspark.mllib.regression import LabeledPoint
from pyspark import SparkContext

sc = SparkContext('local', 'logistic')

# read in list of testing days
testdays = sc.textFile('gs://cloud-training-demos/flights/trainday.csv') \
              .filter(lambda line: 'False' in line) \
              .map(lambda line: line.split(',')) \
              .map(lambda fields: fields[0])
testdays = set(testdays.collect()) # for fast searching

# read the data, filtering it to keep only testdays and non-cancels
# the header is organically removed because FL_DATE is not a testday
allfields = sc.textFile('gs://cloud-training-demos/flights/2015*.csv') \
           .map(lambda line : line.split(',')) \
           .filter(lambda fields: fields[0] in testdays and \
                                  fields[22] != '')

# these are the fields we used in the regression
# format is LabeledPoint(label, [x1, x2, ...]) 
flights = allfields.map(lambda fields: LabeledPoint(\
              float(float(fields[22]) < 15), #ontime \
              [ \
                  float(fields[15]), # DEP_DELAY \
                  float(fields[16]), # TAXI_OUT \
                  float(fields[26]), # DISTANCE \
              ]))

# read the saved model
lrmodel = LogisticRegressionModel.load(sc,\
             'gs://cloud-training-demos/flights/sparkoutput/model')
print lrmodel.weights,lrmodel.intercept

# how good is the fit?
lrmodel.setThreshold(0.7) # cancel if prob-of-ontime < 0.7
labelpred = flights.map(lambda p: (p.label, lrmodel.predict(p.features)))
def eval(labelpred):
    cancel = labelpred.filter(lambda (label, pred): pred == 1)
    nocancel = labelpred.filter(lambda (label, pred): pred == 0)
    corr_cancel = cancel.filter(lambda (label, pred): label == pred).count()
    corr_nocancel = nocancel.filter(lambda (label, pred): label == pred).count()
    return {'total_cancel': cancel.count(), \
            'correct_cancel': float(corr_cancel)/cancel.count(), \
            'total_noncancel': nocancel.count(), \
            'correct_noncancel': float(corr_nocancel)/nocancel.count() \
           }

print eval(labelpred)

