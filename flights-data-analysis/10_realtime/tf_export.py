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

saver_def = saver.as_saver_def()
print saver_def.filename_tensor_name
print saver_def.restore_op_name
saver.restore(sess, 'trained_model.tf')
tf.train.write_graph(sess.graph_def, '.', 'trained_model.proto', as_text=False)
tf.train.write_graph(sess.graph_def, '.', 'trained_model.txt', as_text=True)
