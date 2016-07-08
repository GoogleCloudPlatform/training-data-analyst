#!/usr/bin/env python

import tensorflow as tf
import pandas as pd
import numpy as np
import subprocess
import os

import tf_train as train

train.BATCH_SIZE = 100  # keep this small, to limit unprocessed lines due to roundoff
PROB_THRESH = 0.7 # ontime > 0.7 for us to not cancel meeting

############ 'main' starts here ##############
if __name__ == '__main__':
  # get the patterns we need to evaluate on
  npatterns = train.download_trainfiles(prefix='testflights')
  numbatches = npatterns/train.BATCH_SIZE  # slightly fewer ...
  if (numbatches*train.BATCH_SIZE != npatterns):
    print "WARNING: {0} patterns ignored due to roundoff".format(npatterns%train.BATCH_SIZE)
 
  
  with tf.Session() as sess:
    # create the computation graph
    model, saver, feature_ph, target_ph, keep_prob_ph = train.get_nn()

    # tf_train.py wrote this out; use it to get graph populated
    localfilename = '/tmp/trained_model.tf'
    subprocess.check_call(['gsutil', 'cp', train.GS_MODEL_OUTPUT, localfilename])
    saver.restore(sess, localfilename)

    # evaluation graph
    features, labels = train.get_training_data(prefix='testflights')
    pred_bool = tf.greater(model, PROB_THRESH*tf.identity(model)) # threshold output of model
    truth_bool = tf.greater(target_ph, 0.5*tf.identity(target_ph))
    cost = tf.reduce_sum(tf.to_int32(tf.logical_xor(pred_bool, truth_bool))) # number wrong
 
    tf.initialize_all_variables().run()
    tf.get_default_graph().finalize()  #prevent changing graph

    # start the evaluation
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(coord=coord)

    totalcost = 0.0
    try: 
      nbatch = 0
      while nbatch < numbatches:
        features_feed, labels_feed = sess.run([features, labels])
        batchcost = cost.eval(feed_dict = {feature_ph: features_feed, target_ph: labels_feed, keep_prob_ph: 1.0})
        totalcost = totalcost + batchcost
        nbatch = nbatch + 1
        if nbatch%100 == 0:
           print 'ErrorRate = {0} ({1} incorrect predictions in {2}th batch / {3})'.format(totalcost/(nbatch*train.BATCH_SIZE), batchcost, nbatch, numbatches)
    except tf.errors.OutOfRangeError as e:
      print "Ran out of inputs (?!)"
    finally:
      coord.request_stop()
    coord.join(threads)

    print 'ErrorRate over complete dataset = {0}'.format(totalcost/(numbatches*train.BATCH_SIZE))
