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

# Import libraries and modules
import tensorflow as tf

# Set logging verbosity to INFO for richer output
tf.logging.set_verbosity(tf.logging.INFO)

# The number of video classes
NUM_CLASSES = 4716

# Create an input function to read our training and validation data
# Then provide the results to the Estimator API
def read_dataset_video(file_pattern, mode, batch_size):
    def _input_fn():
        print("\nread_dataset_video: _input_fn: file_pattern = {}".format(file_pattern))
        print("read_dataset_video: _input_fn: mode = {}".format(mode))
        print("read_dataset_video: _input_fn: batch_size = {}".format(batch_size))

        # This function will decode frame examples from the frame level TF Records
        def decode_example(serialized_examples):
            # Create feature map
            feature_map = {
                'video_id': tf.FixedLenFeature(shape = [], dtype = tf.string),
                'labels': tf.VarLenFeature(dtype = tf.int64),
                'mean_rgb': tf.FixedLenFeature(shape = [1024], dtype = tf.float32),
                'mean_audio': tf.FixedLenFeature(shape = [128], dtype = tf.float32)
            }

            # Parse TF Records into our features
            features = tf.parse_single_example(serialized = serialized_examples, features = feature_map)
            print("\nread_dataset_video: _input_fn: decode_example: features = {}".format(features)) # shape = video_id = (), mean_rgb = (1024,), mean_audio = (128,), labels = SparseTensor object

            # Extract and format labels
            sparse_labels = features.pop("labels") # SparseTensor object
            print("read_dataset_video: _input_fn: decode_example: sparse_labels = {}\n".format(sparse_labels))
            labels = tf.cast(x = tf.sparse_to_dense(sparse_indices = sparse_labels.values, output_shape = (NUM_CLASSES,), sparse_values = 1, validate_indices = False), dtype = tf.float32)
            print("read_dataset_video: _input_fn: decode_example: labels = {}\n".format(labels)) # shape = (NUM_CLASSES,)

            return features, labels

        # Create list of files from file pattern
        file_list = tf.gfile.Glob(filename = file_pattern)
        #print("read_dataset_video: _input_fn: file_list = {}".format(file_list))

        # Create dataset from file list
        dataset = tf.data.TFRecordDataset(filenames = file_list)
        print("read_dataset_video: _input_fn: dataset.TFRecordDataset = {}".format(dataset))

        # Decode TF Record dataset examples
        dataset = dataset.map(map_func = lambda x: decode_example(serialized_examples = x))
        print("read_dataset_video: _input_fn: dataset.map = {}".format(dataset))

        # Determine amount of times to repeat file and if we should shuffle based on if we are training or evaluating
        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None # read files forever

            # Shuffle the dataset within a buffer
            dataset = dataset.shuffle(buffer_size = batch_size * 10, seed = None)
            print("read_dataset_video: _input_fn: dataset.shuffle = {}".format(dataset))
        else:
            num_epochs = 1 # read files only once

        # Repeat files num_epoch times
        dataset = dataset.repeat(count = num_epochs)
        print("read_dataset_video: _input_fn: dataset.repeat = {}".format(dataset))

        # Group the data into batches
        dataset = dataset.batch(batch_size = batch_size)
        print("read_dataset_video: _input_fn: dataset.batch = {}".format(dataset))

        # Create a iterator and then pull the next batch of features and labels from the example queue
        batch_features, batch_labels = dataset.make_one_shot_iterator().get_next()
        print("read_dataset_video: _input_fn: batch_features = {}".format(batch_features))
        print("read_dataset_video: _input_fn: batch_labels = {}\n".format(batch_labels))

        return batch_features, batch_labels
    return _input_fn

# Create our model function to be used in our custom estimator
def video_level_model(features, labels, mode, params):
    print("\nvideo_level_model: features = {}".format(features))
    print("video_level_model: labels = {}".format(labels))
    print("video_level_model: mode = {}".format(mode))
    
    # 0. Configure network
    # Get dynamic batch size
    current_batch_size = tf.shape(features['mean_rgb'])[0]
    print("video_level_model: current_batch_size = {}".format(current_batch_size))

    # Stack all of the features into a 3-D tensor
    combined_features = tf.concat(values = [features['mean_rgb'], features['mean_audio']], axis = 1) # shape = (current_batch_size, 1024 + 128)
    print("video_level_model: combined_features = {}".format(combined_features))
    
    # 1. Create the DNN structure now
    # Create the input layer to our frame DNN
    network = combined_features # shape = (current_batch_size, 1024 + 128)
    print("video_level_model: network = combined_features = {}".format(network))
    
    # Add hidden layers with the given number of units/neurons per layer
    for units in params['hidden_units']:
        network = tf.layers.dense(inputs = network, units = units, activation = tf.nn.relu) # shape = (current_batch_size, units)
        print("video_level_model: network = {}, units = {}".format(network, units))
        
    # Connect the final hidden layer to a dense layer with no activation to get the logits
    logits = tf.layers.dense(inputs = network, units = NUM_CLASSES, activation = None) # shape = (current_batch_size, NUM_CLASSES)
    print("video_level_model: logits = {}".format(logits))
    
    # Select the top k logits in descending order
    top_k_logits = tf.nn.top_k(input = logits, k = params['top_k'], sorted = True) # shape = (current_batch_size, top_k)
    print("video_level_model: top_k_logits = {}".format(top_k_logits))

    # Since this is a multi-class, multi-label problem we will apply a sigmoid, not a softmax, to each logit to get its own probability
    probabilities = tf.sigmoid(logits) # shape = (current_batch_size, NUM_CLASSES)
    print("video_level_model: probabilities = {}".format(probabilities))
    
    # Select the top k probabilities in descending order
    top_k_probabilities = tf.sigmoid(top_k_logits.values) # shape = (current_batch_size, top_k)
    print("video_level_model: top_k_probabilities = {}".format(top_k_probabilities))
    
    # Select the top k classes in descending order of likelihood
    top_k_classes = top_k_logits.indices # shape = (current_batch_size, top_k)
    print("video_level_model: top_k_classes = {}".format(top_k_classes))
    
    # The 0/1 predictions based on a threshold, in this case the threshold is if the probability it greater than random chance
    predictions = tf.where(
        condition = probabilities > 1.0 / NUM_CLASSES, # shape = (current_batch_size, NUM_CLASSES)
        x = tf.ones_like(tensor = probabilities), 
        y = tf.zeros_like(tensor = probabilities))
    print("video_level_model: predictions = {}".format(predictions))

    top_k_predictions = tf.where(
        condition = top_k_probabilities > 1.0 / NUM_CLASSES, # shape = (current_batch_size, top_k)
        x = tf.ones_like(tensor = top_k_probabilities), 
        y = tf.zeros_like(tensor = top_k_probabilities))
    print("video_level_model: top_k_predictions = {}\n".format(top_k_predictions))

    # 2. Loss function, training/eval ops 
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        # Since this is a multi-class, multi-label problem, we will use sigmoid activation and cross entropy loss
        loss = tf.losses.sigmoid_cross_entropy(multi_class_labels = labels, logits = logits)
    
        train_op = tf.contrib.layers.optimize_loss(
            loss = loss,
            global_step = tf.train.get_global_step(),
            learning_rate = 0.01,
            optimizer = "Adam")
        eval_metric_ops = {
            "accuracy": tf.metrics.mean_per_class_accuracy(labels = labels, predictions = predictions, num_classes = NUM_CLASSES)
        }
    else:
        loss = None
        train_op = None
        eval_metric_ops = None
  
    # 3. Create predictions
    predictions_dict = {"logits": top_k_logits.values, 
                        "probabilities": top_k_probabilities, 
                        "predictions": top_k_predictions,
                        "classes": top_k_classes}

    # 4. Create export outputs
    export_outputs = {"predict_export_outputs": tf.estimator.export.PredictOutput(outputs = predictions_dict)}

    # 5. Return EstimatorSpec
    return tf.estimator.EstimatorSpec(
        mode = mode,
        predictions = predictions_dict,
        loss = loss,
        train_op = train_op,
        eval_metric_ops = eval_metric_ops,
        export_outputs = export_outputs)

# Create our serving input function to accept the data at serving and send it in the right format to our custom estimator
def serving_input_fn():
    # This function fixes the shape and type of our input strings
    def fix_shape_and_type_for_serving(placeholder):
        # String split each string in the batch and output the values from the resulting SparseTensors
        split_string = tf.map_fn(
            fn = lambda x: tf.string_split(source = [placeholder[x]], delimiter=',').values, 
            elems = tf.range(start = 0, limit = tf.shape(input = placeholder)[0]), 
            dtype = tf.string) # shape = (batch_size, input_sequence_length)
        print("serving_input_fn: fix_shape_and_type_for_serving: split_string = {}".format(split_string))

        # Convert each string in the split tensor to float
        feature_tensor = tf.string_to_number(string_tensor = split_string, out_type = tf.float32) # shape = (batch_size, input_sequence_length)
        print("serving_input_fn: fix_shape_and_type_for_serving: feature_tensor = {}".format(feature_tensor))
        return feature_tensor

    # This function fixes dynamic shape ambiguity of last dimension so that we will be able to use it in our DNN (since tf.layers.dense require the last dimension to be known)
    def get_shape_and_set_modified_shape_2D(tensor, additional_dimension_sizes):
        # Get static shape for tensor and convert it to list
        shape = tensor.get_shape().as_list()
        # Set outer shape to additional_dimension_sizes[0] since we know that this is the correct size
        shape[1] = additional_dimension_sizes[0]
        # Set the shape of tensor to our modified shape
        tensor.set_shape(shape = shape) # shape = (batch_size, additional_dimension_sizes[0])
        print("serving_input_fn: get_shape_and_set_modified_shape_2D: tensor = {}, additional_dimension_sizes = {}".format(tensor, additional_dimension_sizes))
        return tensor

    # Create placeholders to accept the data sent to the model at serving time
    feature_placeholders = { # all features come in as a batch of strings, shape = (batch_size,), this was so because of passing the arrays to online ml-engine prediction
        'video_id': tf.placeholder(dtype = tf.string, shape = [None]),
        'mean_rgb': tf.placeholder(dtype = tf.string, shape = [None]),
        'mean_audio': tf.placeholder(dtype = tf.string, shape = [None])
    }
    print("\nserving_input_fn: feature_placeholders = {}".format(feature_placeholders))

    # Create feature tensors
    features = {
        "video_id": feature_placeholders["video_id"],
        "mean_rgb": fix_shape_and_type_for_serving(placeholder = feature_placeholders["mean_rgb"]),
        "mean_audio": fix_shape_and_type_for_serving(placeholder = feature_placeholders["mean_audio"])
    }
    print("serving_input_fn: features = {}".format(features))

    # Fix dynamic shape ambiguity of feature tensors for our DNN
    features["mean_rgb"] = get_shape_and_set_modified_shape_2D(tensor = features["mean_rgb"], additional_dimension_sizes = [1024])
    features["mean_audio"] = get_shape_and_set_modified_shape_2D(tensor = features["mean_audio"], additional_dimension_sizes = [128])
    print("serving_input_fn: features = {}\n".format(features))

    return tf.estimator.export.ServingInputReceiver(features = features, receiver_tensors = feature_placeholders)

# Create custom estimator's train and evaluate function
def train_and_evaluate(args):
    # Create custom estimator's train and evaluate function
    estimator = tf.estimator.Estimator(
        model_fn = video_level_model, 
        model_dir = args['output_dir'],
        params = {'hidden_units': args['hidden_units'], 'top_k': args['top_k']})
    # Create train spec to read in our training data
    train_spec = tf.estimator.TrainSpec(
        input_fn = read_dataset_video(
            file_pattern = args['train_file_pattern'], 
            mode = tf.estimator.ModeKeys.TRAIN, 
            batch_size = args['batch_size']),
        max_steps = args['train_steps'])
    # Create exporter to save out the complete model to disk
    exporter = tf.estimator.LatestExporter(name = 'exporter', serving_input_receiver_fn = serving_input_fn)
    # Create eval spec to read in our validation data and export our model
    eval_spec = tf.estimator.EvalSpec(
        input_fn = read_dataset_video(
            file_pattern = args['eval_file_pattern'], 
            mode = tf.estimator.ModeKeys.EVAL, 
            batch_size = args['batch_size']),
        steps = None,
        exporters = exporter,
        start_delay_secs = args['start_delay_secs'],
        throttle_secs = args['throttle_secs'])
    # Create train and evaluate loop to train and evaluate our estimator
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)