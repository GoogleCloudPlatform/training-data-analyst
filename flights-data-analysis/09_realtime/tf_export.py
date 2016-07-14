#!/usr/bin/env python

import tensorflow as tf
import pandas as pd
import numpy as np
import subprocess
import os

import tf_train as train

############ 'main' starts here ##############
sess = tf.Session()
model, saver, feature_ph, target_ph, keep_prob_ph = train.get_nn()
localfilename = 'trained_model.tf'
saver.restore(sess, localfilename)
# parameters for C++: http://stackoverflow.com/questions/37508771/how-to-save-and-restore-a-tensorflow-graph-and-its-state-in-c
saver_def = saver.as_saver_def()
print saver_def.filename_tensor_name
print saver_def.restore_op_name
print saver_def.save_tensor_name
# write weights and biases
print model
