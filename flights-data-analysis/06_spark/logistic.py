from pyspark.mllib.linalg import Vectors
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.param import Param, Params
from pyspark import SparkContext

sc = SparkContext('local', 'logistic')

# read the data, removing the header line
infile = sc.textFile('gs://cloud-training-demos/flights/201501.csv')
header = infile.filter(lambda line: 'FL_DATE' in line)
header.collect()
data = infile.subtract(header)
flights = data.map(lambda line: line.split(',')) \
              .map(lambda fields: (fields[0], fields[1], fields[2]))
flights.top(2)


