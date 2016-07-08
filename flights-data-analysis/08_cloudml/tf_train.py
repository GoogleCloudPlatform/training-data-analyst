#!/usr/bin/env python

import tensorflow as tf
import pandas as pd
import numpy as np
import subprocess
import os

LOCAL_TRAIN_DIR = os.environ['HOME'] + '/data/flights/'
BUCKET = 'cloud-training-demos'
GS_TRAIN_DIR = '/flights/chapter07/'
GS_MODEL_OUTPUT = 'gs://' + BUCKET + GS_TRAIN_DIR + 'trained_model.tf'
BATCH_SIZE = 10000
NUM_THREADS = 16
NUM_EPOCHS = 100

def download_trainfiles(prefix='flights'):
  if not os.path.exists(LOCAL_TRAIN_DIR):
     os.makedirs(LOCAL_TRAIN_DIR)

  ls = ['gsutil', 'ls', 'gs://' + BUCKET + GS_TRAIN_DIR + prefix + '-*.csv']
  infiles = subprocess.check_output(ls).split()
  localfiles = []
  for gsfile in infiles:
      fname = os.path.basename(gsfile)
      localfile = os.path.join(LOCAL_TRAIN_DIR, fname)
      localfiles.append(localfile)
      if os.path.exists(localfile):
         print 'Reusing {0}'.format(localfile)
      else:
         cp = ['gsutil', 'cp', gsfile, localfile]
         subprocess.check_call(cp)
 
  # find out how many patterns there in total (mine have no headers) 
  wcout = subprocess.check_output(['wc', '-l'] + localfiles)
  npatterns = int(wcout.split()[-2])
  print "{2}-*.csv dataset has {0} patterns in {1} files".format(npatterns, len(infiles), prefix)
  return npatterns

# build the graph to read the training data
def get_training_data(prefix='flights'):
  # set up queue
  infiles = tf.train.match_filenames_once(LOCAL_TRAIN_DIR + prefix + '-*.csv') 
  filename_queue = tf.train.string_input_producer(infiles, num_epochs=None)
  # read one example
  reader = tf.TextLineReader(skip_header_lines=0)
  _, line = reader.read(filename_queue)
  record_defaults=[[1.0],[1.0],[1.0],[1.0],[1.0],[1.0]]
  label, depdelay, taxiout, distance, avgdep, avgarr = tf.decode_csv(line, record_defaults=record_defaults)
  features = tf.pack([depdelay,taxiout,distance,avgdep,avgarr])
  labels   = tf.pack([label])

  # batch it
  f, l = tf.train.batch([features, labels], batch_size=BATCH_SIZE, num_threads=NUM_THREADS)
  return f, l

# build the neural network graph
def get_nn():
  npredictors = 5
  nhidden = [50, 10]
  noutputs = 1

  # number of nodes in each layer
  numnodes = [npredictors]
  numnodes.extend(nhidden)
  numnodes.extend([noutputs])
  print "Creating nn with {0} nodes in each layer".format(numnodes)

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
  return model, saver, feature_ph, target_ph, keep_prob_ph

############ 'main' starts here ##############
if __name__ == '__main__':
  npatterns = download_trainfiles()
  numbatches = (NUM_EPOCHS * npatterns)/BATCH_SIZE
  modelfile = '/tmp/trained_model'
  with tf.Session() as sess:
    # create the computation graph
    features, labels = get_training_data()
    model, saver, feature_ph, target_ph, keep_prob_ph = get_nn()
    cost = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(model, target_ph))
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
        result = sess.run(training_step, feed_dict = {feature_ph: features_feed, target_ph: labels_feed, keep_prob_ph: 0.5})
        nbatch = nbatch + 1
        if nbatch%10 == 0:
           # warn: this make training_step skip this data
           print "batchno={0}/{1} ({2}=epoch) cost={3}".format(nbatch, numbatches, npatterns/BATCH_SIZE, sess.run(cost, feed_dict = {feature_ph: features_feed, target_ph: labels_feed, keep_prob_ph: 1.0}))
  
    except tf.errors.OutOfRangeError as e:
      print "Ran out of inputs (?!)"
    finally:
      coord.request_stop()
    coord.join(threads)
    filename = saver.save(sess, modelfile, global_step=numbatches)
    print 'Model written to {0}'.format(filename)
    subprocess.check_call(['gsutil', 'cp', filename, GS_MODEL_OUTPUT])
    print 'Model also saved in {0}'.format(GS_MODEL_OUTPUT)
