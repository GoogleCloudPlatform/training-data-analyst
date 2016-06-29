#!/usr/bin/env python

import tensorflow as tf
import pandas as pd
import numpy as np
import subprocess
import os

LOCAL_TRAIN_DIR = os.environ['HOME'] + '/data/flights/'
BUCKET = 'cloud-training-demos'
GS_TRAIN_DIR = '/flights/chapter07/'
BATCH_SIZE = 10000
NUM_THREADS = 16
NUM_EPOCHS = 10

def download_trainfiles():
  if not os.path.exists(LOCAL_TRAIN_DIR):
     os.makedirs(LOCAL_TRAIN_DIR)

  ls = ['gsutil', 'ls', 'gs://' + BUCKET + GS_TRAIN_DIR + 'flights-*.csv']
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
  print "Training dataset has {0} patterns in {1} files".format(npatterns, len(infiles))
  return npatterns

# build the graph to read the training data
def get_training_data():
  # set up queue
  infiles = tf.train.match_filenames_once(LOCAL_TRAIN_DIR + 'flights-*.csv') 
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
if __name__ == '__main__':
  npatterns = download_trainfiles()
  numbatches = (NUM_EPOCHS * npatterns)/BATCH_SIZE
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
           print "batchno={0}/{1} ({2}=epoch) cost={3}".format(nbatch, numbatches, npatterns/BATCH_SIZE, sess.run(cost, feed_dict = {feature_data: features_feed, target_data: labels_feed}))
  
    except tf.errors.OutOfRangeError as e:
      print "Ran out of inputs (?!)"
    finally:
      coord.request_stop()
    coord.join(threads)
    filename = saver.save(sess, modelfile, global_step=numbatches)
    print 'Model written to {0}'.format(filename)
    gsfilename = 'gs://' + BUCKET + GS_TRAIN_DIR + 'trained_model.tf'
    subprocess.check_call(['gsutil', 'cp', filename, gsfilename])
    print 'Model also saved in {0}'.format(gsfilename)
