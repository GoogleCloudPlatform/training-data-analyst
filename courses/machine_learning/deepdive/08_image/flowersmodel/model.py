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

tf.logging.set_verbosity(v = tf.logging.INFO)

LIST_OF_LABELS = "daisy,dandelion,roses,sunflowers,tulips".split(',')
HEIGHT = 299
WIDTH = 299
NUM_CHANNELS = 3
NCLASSES = 5

def linear_model(img, mode, hparams):
    X = tf.reshape(tensor = img, shape = [-1,HEIGHT * WIDTH]) #flatten
    ylogits = tf.layers.dense(input = X, units = NCLASSES, activation = None)
    return ylogits, NCLASSES

def dnn_model(img, mode, hparams):
    X = tf.reshape(tensor = img, shape = [-1, HEIGHT * WIDTH]) #flatten
    h1 = tf.layers.dense(input = X, units = 300, activation = tf.nn.relu)
    h2 = tf.layers.dense(input = h1, units = 100, activation = tf.nn.relu)
    h3 = tf.layers.dense(input = h2, units = 30, activation = tf.nn.relu)
    ylogits = tf.layers.dense(input = h3, units = NCLASSES, activation = None)
    return ylogits, NCLASSES

def dnn_dropout_model(img, mode, hparams):
    dprob = hparams.get("dprob", 0.1)

    X = tf.reshape(tensor = img, shape = [-1, HEIGHT * WIDTH]) #flatten
    h1 = tf.layers.dense(input = X, units = 300, activation = tf.nn.relu)
    h2 = tf.layers.dense(input = h1, units = 100, activation = tf.nn.relu)
    h3 = tf.layers.dense(input = h2, units = 30, activation = tf.nn.relu)
    h3d = tf.layers.dropout(inputs = h3, rate = dprob, training = (mode == tf.estimator.ModeKeys.TRAIN)) #only dropout when training
    ylogits = tf.layers.dense(input = h3d, units = NCLASSES, activation = None)
    return ylogits, NCLASSES

def cnn_model(img, mode, hparams):
    ksize1 = hparams.get("ksize1", 5)
    ksize2 = hparams.get("ksize2", 5)
    nfil1 = hparams.get("nfil1", 10)
    nfil2 = hparams.get("nfil2", 20)
    dprob = hparams.get("dprob", 0.25)

    c1 = tf.layers.conv2d(inputs = img, filters = nfil1,
                          kernel_size = ksize1, strides = 1,
                          padding = "same", activation = tf.nn.relu) # shape = (batch_size, HEIGHT, WIDTH, nfil1)
    
    p1 = tf.layers.max_pooling2d(inputs = c1, pool_size = 2, strides = 2) # shape = (batch_size, HEIGHT // 2, WIDTH // 2, nfil1)
    
    c2 = tf.layers.conv2d(inputs = p1, filters = nfil2,
                          kernel_size = ksize2, strides = 1, 
                          padding = "same", activation = tf.nn.relu) # shape = (batch_size, HEIGHT // 2, WIDTH // 2, nfil2)
    
    p2 = tf.layers.max_pooling2d(inputs = c2, pool_size = 2, strides = 2) # shape = (batch_size, HEIGHT // 4, WIDTH // 4, nfil2)

    outlen = p2.shape[1] * p2.shape[2] * p2.shape[3] # HEIGHT // 4 * WIDTH // 4 * nfil2
    p2flat = tf.reshape(tensor = p2, shape = [-1, outlen]) # shape = (batch_size, HEIGHT // 4 * WIDTH // 4 * nfil2)

    # Apply batch normalization
    if hparams["batch_norm"]:
        h3 = tf.layers.dense(inputs = p2flat, units = 300, activation = None)
        h3 = tf.layers.batch_normalization(inputs = h3, training = (mode == tf.estimator.ModeKeys.TRAIN)) # only batchnorm when training
        h3 = tf.nn.relu(features = h3)
    else:  
        h3 = tf.layers.dense(inputs = p2flat, units = 300, activation = tf.nn.relu)
  
    # Apply dropout
    h3d = tf.layers.dropout(inputs = h3, rate = dprob, training = (mode == tf.estimator.ModeKeys.TRAIN))

    ylogits = tf.layers.dense(inputs = h3d, units = NCLASSES, activation = None)
  
    # Apply batch normalization once more
    if hparams["batch_norm"]:
        ylogits = tf.layers.batch_normalization(inputs = ylogits, training = (mode == tf.estimator.ModeKeys.TRAIN))

    return ylogits, NCLASSES

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
    return {"image": image}, label

def serving_input_fn():
    # Note: only handles one image at a time 
    feature_placeholders = {"image_bytes": tf.placeholder(dtype = tf.string, shape = [])}
    image, _ = read_and_preprocess(tf.squeeze(input = feature_placeholders["image_bytes"]))
    image["image"] = tf.expand_dims(image["image"], axis = 0)
    return tf.estimator.export.ServingInputReceiver(features = image, receiver_tensors = feature_placeholders)

def make_input_fn(csv_of_filenames, batch_size, mode, augment = False):
    def _input_fn():
        def decode_csv(csv_row):
            filename, label = tf.decode_csv(records = csv_row, record_defaults = [[""],[""]])
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
    
def image_classifier(features, labels, mode, params):
    model_functions = {
        "linear": linear_model,
        "dnn": dnn_model,
        "dnn_dropout": dnn_dropout_model,
        "cnn": cnn_model}
    model_function = model_functions[params["model"]] 
    ylogits, nclasses = model_function(features["image"], mode, params)

    probabilities = tf.nn.softmax(logits = ylogits)
    class_int = tf.cast(x = tf.argmax(input = ylogits, axis = 1), dtype = tf.uint8)
    class_str = tf.gather(params = LIST_OF_LABELS, indices = tf.cast(x = class_int, dtype = tf.int32))
  
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        # Convert string label to int
        labels_table = tf.contrib.lookup.index_table_from_tensor(mapping = tf.constant(value = LIST_OF_LABELS, dtype = tf.string))
        labels = labels_table.lookup(keys = labels)

        loss = tf.reduce_mean(input_tensor = tf.nn.softmax_cross_entropy_with_logits_v2(logits = ylogits, labels = tf.one_hot(indices = labels, depth = NCLASSES)))
        
        if mode == tf.estimator.ModeKeys.TRAIN:
            # This is needed for batch normalization, but has no effect otherwise
            update_ops = tf.get_collection(key = tf.GraphKeys.UPDATE_OPS)
            with tf.control_dependencies(control_inputs = update_ops):
                train_op = tf.contrib.layers.optimize_loss(
                    loss = loss, 
                    global_step = tf.train.get_global_step(),
                    learning_rate = params["learning_rate"],
                    optimizer = "Adam")
            eval_metric_ops = None
        else:
            train_op = None
            eval_metric_ops =  {"accuracy": tf.metrics.accuracy(labels = labels, predictions = class_int)}
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

def train_and_evaluate(output_dir, hparams):
    tf.summary.FileWriterCache.clear() # ensure filewriter cache is clear for TensorBoard events file
    
    EVAL_INTERVAL = 300 # every 5 minutes
    
    # Instantiate base estimator class for custom model function
    estimator = tf.estimator.Estimator(
        model_fn = image_classifier,
        params = hparams,
        config = tf.estimator.RunConfig(
            save_checkpoints_secs = EVAL_INTERVAL),
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