#!/usr/bin/env python

import tensorflow as tf
import pandas as pd
import numpy as np
import subprocess
import os

############ 'main' starts here ##############
sess = tf.Session()
# copy-paste from train.get_nn()
# create the computation graph
npredictors = 5
nhidden = [50, 10]
noutputs = 1

# number of nodes in each layer
numnodes = [npredictors]
numnodes.extend(nhidden)
numnodes.extend([noutputs])
#print "Creating nn with {0} nodes in each layer".format(numnodes)

# input and output placeholders
feature_ph = tf.placeholder("float", [None, npredictors])
target_ph = tf.placeholder("float", [None, noutputs])
keep_prob_ph = tf.placeholder("float")

# weights and biases. weights for each input; bias for each output
weights = [tf.Variable(tf.truncated_normal([numnodes[i], numnodes[i+1]], stddev=0.01), name='weight_{0}'.format(i)) for i in xrange(0,len(numnodes)-1)]
biases = [tf.Variable(tf.ones([numnodes[i+1]]), name='bias_{0}'.format(i)) for i in xrange(0,len(numnodes)-1)]

# matrix multiplication at each layer
# activation function = tanh for input, relu for each hidden layer, sigmoid for output layer
model = tf.tanh(tf.matmul(feature_ph, weights[0]) + biases[0])
for layer in xrange(1, len(weights)-1):
  model = tf.nn.dropout(tf.nn.relu(tf.matmul(model, weights[layer]) + biases[layer]), keep_prob_ph)
model = tf.sigmoid(tf.matmul(model, weights[-1]) + biases[-1])

# for saving and restoring
allvars = []
allvars.extend(weights)
allvars.extend(biases)
saver = tf.train.Saver(allvars)

localfilename = 'trained_model.tf'
saver.restore(sess, localfilename)

# write weights and biases
for (weight, bias) in zip(weights, biases):
   w = sess.run(weight) # 2D matrix
   b = sess.run(bias)   # 1D vector
   for (w1, b1) in zip(w, b):
     for wt in w1:
       print wt
     print b1
