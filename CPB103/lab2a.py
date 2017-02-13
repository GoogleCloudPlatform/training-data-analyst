#!/usr/bin/env python

from pyspark import SparkContext
sc = SparkContext("local")

rdd = sc.parallelize(range(1000), 10)
print rdd.mean()

file = sc.textFile("gs://cpb103-public-files/lab2a-input.txt")
dataLines = file.map(lambda s: s.split(",")).map(lambda x : (x[0], [x[1]]))
print dataLines.take(100)

databyKey = dataLines.reduceByKey(lambda a, b: a + b)
print databyKey.take(100)
