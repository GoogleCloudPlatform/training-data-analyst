#!/usr/bin/env python

from pyspark import SparkContext
sc = SparkContext("local")

file = sc.textFile("gs://BUCKET_NAME/unstructured/lab2-input.txt")
dataLines = file.map(lambda s: s.split(",")).map(lambda x : (x[0], [x[1]]))
print(dataLines.take(100))

databyKey = dataLines.reduceByKey(lambda a, b: a + b)
print(databyKey.take(100))

countByKey = databyKey.map(lambda k_v: (k_v[0], len(k_v[1])))
print(countByKey.take(100))
