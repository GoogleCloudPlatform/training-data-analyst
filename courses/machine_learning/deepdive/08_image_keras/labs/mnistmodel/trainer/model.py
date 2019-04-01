#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
tf.logging.set_verbosity(tf.logging.INFO)

HEIGHT=28
WIDTH=28
NCLASSES=10

# Build Keras Model Using Keras Sequential API
def linear_model(hparams):
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_shape = [HEIGHT, WIDTH, 1], name = "image"))
    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(units = NCLASSES, activation = tf.nn.softmax, name = "probabilities"))
    return model

def dnn_model(hparams):
    # TODO: Implement DNN model with three hidden layers
    pass

def dnn_dropout_model(hparams):
    dprob = hparams.get("dprob", 0.1)
    
    # TODO: Implement DNN model and apply dropout to the last hidden layer
    pass

def cnn_model(hparams):
    ksize1 = hparams.get("ksize1", 5)
    ksize2 = hparams.get("ksize2", 5)
    nfil1 = hparams.get("nfil1", 10)
    nfil2 = hparams.get("nfil2", 20)
    dprob = hparams.get("dprob", 0.25)
    
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_shape = [HEIGHT, WIDTH, 1], name = "image")) # shape = (?, 28, 28, 1)
    model.add(tf.keras.layers.Conv2D(filters = nfil1, kernel_size = ksize1, padding = "same", activation = tf.nn.relu)) # shape = (?, 28, 28, nfil1)
    model.add(tf.keras.layers.MaxPooling2D(pool_size = 2, strides = 2)) # shape = (?, 14, 14, nfil1)
    model.add(# TODO: Apply a second convolution with nfil2 filters) # shape = (?, 14, 14, nfil2)
    model.add(# TODO: Apply a pooling layer with pool_size = 2 and strides = 2) # shape = (?, 7, 7, nfil2)
    model.add(tf.keras.layers.Flatten())

    # Apply batch normalization
    if hparams["batch_norm"]:
        model.add(tf.keras.layers.Dense(units = 300, activation = tf.nn.relu))
        model.add(tf.keras.layers.BatchNormalization())
        model.add(tf.keras.layers.Activation(activation = tf.nn.relu))
    else:  
        model.add(tf.keras.layers.Dense(units = 300, activation = tf.nn.relu))
  
    # Apply dropout
    model.add(tf.keras.layers.Dropout(rate = dprob))

    model.add(tf.keras.layers.Dense(units = NCLASSES, activation = None))
  
    # Apply batch normalization once more
    if hparams["batch_norm"]:
        model.add(tf.keras.layers.BatchNormalization())
        
    model.add(tf.keras.layers.Dense(units = NCLASSES, activation = tf.nn.softmax, name = "probabilities"))
    pass

# Create serving input function for inference
def serving_input_fn():
    # Input will be rank 3
    feature_placeholders = {
        "image": tf.placeholder(dtype = tf.float32, shape = [None, HEIGHT, WIDTH])}
    # But model function requires rank 4
    features = {
        "image": tf.expand_dims(input = feature_placeholders["image"], axis = -1)} 
    return tf.estimator.export.ServingInputReceiver(features = features, receiver_tensors = feature_placeholders)

# Wrapper function to build selected Keras model type
def image_classifier(hparams):
    model_functions = {
        'linear': linear_model,
        'dnn': dnn_model,
        'dnn_dropout': dnn_dropout_model,
        'cnn': cnn_model}
    
    # Get function pointer for selected model type
    model_function = model_functions[hparams['model']]
    
    # Build selected Keras model
    model = model_function(hparams)
    
    return model

# Create train_and_evaluate function
def train_and_evaluate(output_dir, hparams):
    tf.summary.FileWriterCache.clear() # ensure filewriter cache is clear for TensorBoard events file
    EVAL_INTERVAL = 60

    # Get mnist data
    mnist = tf.keras.datasets.mnist

    (x_train, y_train), (x_test, y_test) = mnist.load_data()

    # Scale our features between 0 and 1
    x_train, x_test = x_train / 255.0, x_test / 255.0
    
    # Reshape images to add a dimension for channels (1 in this case)
    x_train = x_train.reshape([-1, HEIGHT, WIDTH, 1])
    x_test = x_test.reshape([-1, HEIGHT, WIDTH, 1])

    # Convert labels to categorical one-hot encoding
    y_train = tf.keras.utils.to_categorical(y = y_train, num_classes = NCLASSES)
    y_test = tf.keras.utils.to_categorical(y = y_test, num_classes = NCLASSES)

    # Create training input function
    train_input_fn = tf.estimator.inputs.numpy_input_fn(
        x = {"image": x_train},
        y = y_train,
        batch_size = 100,
        num_epochs = None,
        shuffle = True,
        queue_capacity = 5000
      )

    # Create evaluation input function
    eval_input_fn = tf.estimator.inputs.numpy_input_fn(
        x = {"image": x_test},
        y = y_test,
        batch_size = 100,
        num_epochs = 1,
        shuffle = False,
        queue_capacity = 5000
      )
    
    # Build Keras model
    model = image_classifier(hparams)
        
    # Compile Keras model with optimizer, loss function, and eval metrics
    model.compile(
        optimizer = "adam",
        loss = "categorical_crossentropy",
        metrics = ["accuracy"])
        
    # Convert Keras model to an Estimator
    estimator = tf.keras.estimator.model_to_estimator(
        keras_model = model, 
        model_dir = output_dir, 
        config = tf.estimator.RunConfig(save_checkpoints_secs = EVAL_INTERVAL))

    # Set estimator's train_spec to use train_input_fn and train for so many steps
    train_spec = tf.estimator.TrainSpec(
        input_fn = train_input_fn,
        max_steps = hparams["train_steps"])

    # Create exporter that uses serving_input_fn to create saved_model for serving
    exporter = tf.estimator.LatestExporter(
        name = "exporter", 
        serving_input_receiver_fn = serving_input_fn)

    # Set estimator's eval_spec to use eval_input_fn and export saved_model
    eval_spec = tf.estimator.EvalSpec(
        input_fn = eval_input_fn,
        steps = None,
        exporters = exporter,
        throttle_secs = EVAL_INTERVAL)

    # Run train_and_evaluate loop
    tf.estimator.train_and_evaluate(
        estimator = estimator, 
        train_spec = train_spec, 
        eval_spec = eval_spec)