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

infile = '/Users/vlakshmanan/data/flights/flights-00001-of-00012.csv'
# read into pandas
df = pd.read_csv(infile, header=None, names=['label','depdelay','taxiout','distance','avgdep','avgarr'])

# scale inputs
print df.describe()
df['depdelay'] = df['depdelay']/60
df['taxiout'] = df['taxiout']/30
df['distance'] = df['distance']/3000
df['avgdep'] = df['avgdep']/30
df['avgarr'] = df['avgarr']/30
print df.describe()

predictors = df.iloc[:,1:6]
targets = df.iloc[:,0]

trainsize = len(targets)
npredictors = len(predictors.columns)
noutputs = 1
nhidden = 5
numiter = 10000
modelfile = '/tmp/trained_model'
with tf.Session() as sess:
  feature_data = tf.placeholder("float", [None, npredictors])
  target_data = tf.placeholder("float", [None, noutputs])
  weights1 = tf.Variable(tf.truncated_normal([npredictors, nhidden], stddev=0.01))
  weights2 = tf.Variable(tf.truncated_normal([nhidden, noutputs], stddev=0.01))
  biases1 = tf.Variable(tf.ones([nhidden]))
  biases2 = tf.Variable(tf.ones([noutputs]))
  model = tf.sigmoid(tf.matmul(tf.nn.relu(tf.matmul(feature_data, weights1) + biases1), weights2) + biases2)
  cost = tf.nn.l2_loss(tf.nn.sigmoid_cross_entropy_with_logits(model, target_data))
  training_step = tf.train.AdamOptimizer(learning_rate=0.0001).minimize(cost)
  init = tf.initialize_all_variables()
  sess.run(init)

  saver = tf.train.Saver({'weights1' : weights1, 'biases1' : biases1, 'weights2' : weights2, 'biases2' : biases2})
  for iter in xrange(0, numiter):
    sess.run(training_step, feed_dict = {
        feature_data : predictors[:trainsize].values,
        target_data : targets[:trainsize].values.reshape(trainsize, noutputs)
      })
    
    if iter%1000 == 0:
      print '{0} error={1}'.format(iter, np.sqrt(cost.eval(feed_dict = {
          feature_data : predictors[:trainsize].values,
          target_data : targets[:trainsize].values.reshape(trainsize, noutputs)
      }) / trainsize))
    
  filename = saver.save(sess, modelfile, global_step=numiter)
  print 'Model written to {0}'.format(filename)

