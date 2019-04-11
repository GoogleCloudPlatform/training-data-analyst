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

tf.logging.set_verbosity(tf.logging.INFO)

LIST_OF_LABELS = 'daisy,dandelion,roses,sunflowers,tulips'.split(',')
HEIGHT = 299
WIDTH = 299
NUM_CHANNELS = 3
NCLASSES = 5

# Build Keras Model Using Keras Sequential API
def linear_model(input_tensor, hparams):
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_tensor = input_tensor, name = "image"))
    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(units = NCLASSES, activation = None))
    return model

def dnn_model(input_tensor, hparams):
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_tensor = input_tensor, name = "image"))
    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(units = 300, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = 100, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = 30, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = NCLASSES, activation = None))
    return model

def dnn_dropout_model(input_tensor, hparams):
    dprob = hparams.get("dprob", 0.1)
    
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_tensor = input_tensor, name = "image"))
    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(units = 300, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = 100, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = 30, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dropout(rate = dprob))
    model.add(tf.keras.layers.Dense(units = NCLASSES, activation = None))
    return model

def cnn_model(input_tensor, hparams):
    ksize1 = hparams.get("ksize1", 5)
    ksize2 = hparams.get("ksize2", 5)
    nfil1 = hparams.get("nfil1", 10)
    nfil2 = hparams.get("nfil2", 20)
    dprob = hparams.get("dprob", 0.25)
    
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_tensor = input_tensor, name = "image")) # shape = (?, 28, 28, 1)
    model.add(tf.keras.layers.Conv2D(filters = nfil1, kernel_size = ksize1, padding = "same", activation = tf.nn.relu)) # shape = (?, 28, 28, nfil1)
    model.add(tf.keras.layers.MaxPooling2D(pool_size = 2, strides = 2)) # shape = (?, 14, 14, nfil1)
    model.add(tf.keras.layers.Conv2D(filters = nfil2, kernel_size = ksize2, padding = "same", activation = tf.nn.relu)) # shape = (?, 14, 14, nfil2)
    model.add(tf.keras.layers.MaxPooling2D(pool_size = 2, strides = 2)) # shape = (?, 7, 7, nfil2)
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
        
    model.add(tf.keras.layers.Dense(units = NCLASSES, activation = None))
    return model

def read_and_preprocess_with_augment(image_bytes, label = None):
    return read_and_preprocess(image_bytes, label, augment = True)
    
def read_and_preprocess(image_bytes, label = None, augment = False):
    # Decode the image, end up with pixel values that are in the -1, 1 range
    image = tf.image.decode_jpeg(contents = image_bytes, channels = NUM_CHANNELS)
    image = tf.image.convert_image_dtype(image = image, dtype = tf.float32) # 0-1
    image = tf.expand_dims(input = image, axis = 0) # resize_bilinear needs batches
    
    if augment:
        image = tf.image.resize_bilinear(images = image, size = [HEIGHT + 10, WIDTH + 10], align_corners = False)
        image = tf.squeeze(input = image, axis = 0) # remove batch dimension
        image = tf.random_crop(value = image, size = [HEIGHT, WIDTH, NUM_CHANNELS])
        image = tf.image.random_flip_left_right(image = image)
        image = tf.image.random_brightness(image = image, max_delta = 63.0 / 255.0)
        image = tf.image.random_contrast(image = image, lower = 0.2, upper = 1.8)
    else:
        image = tf.image.resize_bilinear(images = image, size = [HEIGHT, WIDTH], align_corners = False)
        image = tf.squeeze(input = image, axis = 0) # remove batch dimension
        
    # Pixel values are in range [0,1], convert to [-1,1]
    image = tf.subtract(x = image, y = 0.5)
    image = tf.multiply(x = image, y = 2.0)
    return {'image': image}, label

def serving_input_fn():
    # Note: only handles one image at a time 
    feature_placeholders = {'image_bytes': tf.placeholder(dtype = tf.string, shape = [])}
    image, _ = read_and_preprocess(
        tf.squeeze(input = feature_placeholders['image_bytes']))
    image['image'] = tf.expand_dims(input = image['image'], axis = 0)
    return tf.estimator.export.ServingInputReceiver(features = image, receiver_tensors = feature_placeholders)

def make_input_fn(csv_of_filenames, batch_size, mode, augment = False):
    def _input_fn():
        def decode_csv(csv_row):
            filename, label = tf.decode_csv(records = csv_row, record_defaults = [[''],['']])
            image_bytes = tf.read_file(filename = filename)
            return image_bytes, label
        
        # Create tf.data.dataset from filename
        dataset = tf.data.TextLineDataset(filenames = csv_of_filenames).map(map_func = decode_csv)     
        
        if augment: 
            dataset = dataset.map(map_func = read_and_preprocess_with_augment)
        else:
            dataset = dataset.map(map_func = read_and_preprocess)

        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None # indefinitely
            dataset = dataset.shuffle(buffer_size = 10 * batch_size)
        else:
            num_epochs = 1 # end-of-input after this
 
        dataset = dataset.repeat(count = num_epochs).batch(batch_size = batch_size)
        return dataset.make_one_shot_iterator().get_next()
    return _input_fn

# Wrapper function to build selected Keras model type
def image_classifier(input_tensor, hparams):
    model_functions = {
        'linear': linear_model,
        'dnn': dnn_model,
        'dnn_dropout': dnn_dropout_model,
        'cnn': cnn_model}
    
    # Get function pointer for selected model type
    model_function = model_functions[hparams['model']]
    
    # Build selected Keras model
    model = model_function(input_tensor, hparams)
    
    return model

def model_fn(features, labels, mode, params):
    """
    The ML architecture is built in Keras and its output tensor is
    used for building the prediction heads
    """
    
    # Select the Keras model
    model = image_classifier(features["image"], params)
    
    # Extract the output tensor of the Keras model
    logits = model._graph.get_tensor_by_name(name = model.output.name)

    probabilities = tf.nn.softmax(logits = logits)
    class_int = tf.cast(x = tf.argmax(input = logits, axis = 1), dtype = tf.uint8)
    class_str = tf.gather(params = LIST_OF_LABELS, indices = tf.cast(x = class_int, dtype = tf.int32))
  
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        # Convert string label to int
        labels_table = tf.contrib.lookup.index_table_from_tensor(mapping = tf.constant(value = LIST_OF_LABELS, dtype = tf.string))
        labels = labels_table.lookup(keys = labels)

        loss = tf.reduce_mean(input_tensor = tf.nn.softmax_cross_entropy_with_logits_v2(logits = logits, labels = tf.one_hot(indices = labels, depth = NCLASSES)))
        
        if mode == tf.estimator.ModeKeys.TRAIN:
            # This is needed for batch normalization, but has no effect otherwise
            update_ops = tf.get_collection(key = tf.GraphKeys.UPDATE_OPS)
            with tf.control_dependencies(control_inputs = update_ops):
                train_op = tf.contrib.layers.optimize_loss(
                    loss = loss, 
                    global_step = tf.train.get_global_step(),
                    learning_rate = params['learning_rate'],
                    optimizer = "Adam")
            eval_metric_ops = None
        else:
            train_op = None
            eval_metric_ops =  {'accuracy': tf.metrics.accuracy(labels = labels, predictions = class_int)}
    else:
        loss = None
        train_op = None
        eval_metric_ops = None
 
    return tf.estimator.EstimatorSpec(
        mode = mode,
        predictions = {"probabilities": probabilities, 
                       "classid": class_int, 
                       "class": class_str},
        loss = loss,
        train_op = train_op,
        eval_metric_ops = eval_metric_ops,
        export_outputs = {"classes": tf.estimator.export.PredictOutput(
            {"probabilities": probabilities, 
             "classid": class_int, 
             "class": class_str})}
    )


# Create train_and_evaluate function
def train_and_evaluate(output_dir, hparams):
    tf.summary.FileWriterCache.clear() # ensure filewriter cache is clear for TensorBoard events file
    EVAL_INTERVAL = 60
        
    # Convert Keras model to an Estimator
    estimator = tf.estimator.Estimator(
        model_fn = model_fn,
        params = hparams,
        config= tf.estimator.RunConfig(save_checkpoints_secs = EVAL_INTERVAL),
        model_dir = output_dir)

    # Set estimator's train_spec to use train_input_fn and train for so many steps
    train_spec = tf.estimator.TrainSpec(
        input_fn = make_input_fn(
            hparams['train_data_path'],
            hparams['batch_size'],
            mode = tf.estimator.ModeKeys.TRAIN,
            augment = hparams['augment']),
        max_steps = hparams["train_steps"])

    # Create exporter that uses serving_input_fn to create saved_model for serving
    exporter = tf.estimator.LatestExporter(
        name = "exporter", 
        serving_input_receiver_fn = serving_input_fn)

    # Set estimator's eval_spec to use eval_input_fn and export saved_model
    eval_spec = tf.estimator.EvalSpec(
        input_fn = make_input_fn(
            hparams['eval_data_path'],
            hparams['batch_size'],
            mode = tf.estimator.ModeKeys.EVAL),
        steps = None,
        exporters = exporter,
        start_delay_secs = EVAL_INTERVAL,
        throttle_secs = EVAL_INTERVAL)

    # Run train_and_evaluate loop
    tf.estimator.train_and_evaluate(
        estimator = estimator, 
        train_spec = train_spec, 
        eval_spec = eval_spec)