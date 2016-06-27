#!/usr/bin/env python

from apiclient import discovery
from oauth2client.client import GoogleCredentials
from gcloud import storage
import tensorflow as tf
import pandas as pd
import numpy as np
import os

#bucket = client.get_bucket('cloud-training-demos')
#infiles = bucket.list_blobs(prefix='/flights/chapter07/')


# build the graph to read the training data
def get_training_data():
  # set up queue
  infiles = ['/Users/vlakshmanan/data/flights/flights-00001-of-00012.csv', '/Users/vlakshmanan/data/flights/flights-00002-of-00012.csv']
  filename_queue = tf.train.string_input_producer(infiles, num_epochs=None)
  # read one example
  reader = tf.TextLineReader(skip_header_lines=0)
  _, line = reader.read(filename_queue)
  record_defaults=[[1.0],[1.0],[1.0],[1.0],[1.0],[1.0]]
  label, depdelay, taxiout, distance, avgdep, avgarr = tf.decode_csv(line, record_defaults=record_defaults)
  features = tf.pack([depdelay,taxiout,distance,avgdep,avgarr])
  labels   = tf.pack([label])

  # batch it
  f, l = tf.train.batch([features, labels], batch_size=10000, num_threads=3)
  return f, l

# build the neural network graph
def get_nn():
  npredictors = 5
  nhidden = 7
  noutputs = 1
  feature_data = tf.placeholder("float", [None, npredictors])
  target_data = tf.placeholder("float", [None, noutputs])
  weights1 = tf.Variable(tf.truncated_normal([npredictors, nhidden], stddev=0.01))
  weights2 = tf.Variable(tf.truncated_normal([nhidden, noutputs], stddev=0.01))
  biases1 = tf.Variable(tf.ones([nhidden]))
  biases2 = tf.Variable(tf.ones([noutputs]))
  model = tf.sigmoid(tf.matmul(tf.nn.relu(tf.matmul(feature_data, weights1) + biases1), weights2) + biases2)
  saver = tf.train.Saver({'weights1' : weights1, 'biases1' : biases1, 'weights2' : weights2, 'biases2' : biases2})
  return model, saver, feature_data, target_data

############ 'main' starts here ##############
numbatches = 300
modelfile = '/tmp/trained_model'
with tf.Session() as sess:
  # create the computation graph
  features, labels = get_training_data()
  model, saver, feature_data, target_data = get_nn()
  cost = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(model, target_data))
  optimizer = tf.train.AdamOptimizer(learning_rate=0.0001)
  training_step = optimizer.minimize(cost)
 
  tf.initialize_all_variables().run()

  tf.get_default_graph().finalize()  #prevent changing graph

  # start the training
  coord = tf.train.Coordinator()
  threads = tf.train.start_queue_runners(coord=coord)

  try: 
    nbatch = 0
    while nbatch < numbatches:
       features_feed, labels_feed = sess.run([features, labels])
       result = sess.run(training_step, feed_dict = {feature_data: features_feed, target_data: labels_feed})
       nbatch = nbatch + 1
       if nbatch%10 == 0:
           # Q: does this make training_step skip this data?
           print "batchno={0} cost={1}".format(nbatch, sess.run(cost, feed_dict = {feature_data: features_feed, target_data: labels_feed}))
  except tf.errors.OutOfRangeError as e:
     print "Ran out of inputs (?!)"
  finally:
     coord.request_stop()
  coord.join(threads)
  filename = saver.save(sess, modelfile, global_step=numbatches)
  print 'Model written to {0}'.format(filename)

