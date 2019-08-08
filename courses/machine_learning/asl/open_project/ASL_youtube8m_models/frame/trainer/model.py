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

import tensorflow as tf

# Set logging to be level of INFO
tf.logging.set_verbosity(tf.logging.INFO)

# The number of video classes
NUM_CLASSES = 4716
# The number of frames to extract per video
MAX_FRAMES = 20

# Create an input function to read our training and validation data
# Then provide the results to the Estimator API
def read_dataset_frame(file_pattern, mode, batch_size):
    def _input_fn():
        print("\nread_dataset_frame: _input_fn: file_pattern = {}".format(file_pattern))
        print("read_dataset_frame: _input_fn: mode = {}".format(mode))
        print("read_dataset_frame: _input_fn: batch_size = {}".format(batch_size))
        
        # This function dequantizes our tensors to bring them back to full floating point precision
        def dequantize(feat_vector, max_quantized_value = 2, min_quantized_value = -2):
            assert max_quantized_value > min_quantized_value # ensure the max value is larger than the min value
            quantized_range = max_quantized_value - min_quantized_value # find the range between max and min
            scalar = quantized_range / 255.0 # create a scale factor where 0 is the min and 1 is the max
            bias = (quantized_range / 512.0) + min_quantized_value # create bias term to shift our scaled feature vector
            return feat_vector * scalar + bias # return the scaled and shifted feature vector

        # This function resizes our frames axis so that we only get a subset of frames
        def resize_axis(tensor, axis, new_size, fill_value = 0):
            tensor = tf.convert_to_tensor(value = tensor) # ensure tensor is a tensor
            shape = tf.unstack(value = tf.shape(input = tensor)) # create a list where each element is a 1-D tensor the size of each dimension in tensor

            pad_shape = shape[:] # create a copy of the shape list of 1-D tensors
            pad_shape[axis] = tf.maximum(x = 0, y = new_size - shape[axis]) # change the size of the axis dimension to the maximum of 0 and the new size of our padded shape

            shape[axis] = tf.minimum(x = shape[axis], y = new_size) # change the size of the axis dimension to the minimum of our original shape and the new size of our padded shape
            shape = tf.stack(values = shape) # stack the list of tensor sizes back into a larger tensor

            resized = tf.concat(values = [
                tf.slice(input_ = tensor, begin = tf.zeros_like(tensor = shape), size = shape), # slice the tensor starting at the 0th index in each dimension and going as far as our adjusted shape in each dimension
                tf.fill(dims = tf.stack(values = pad_shape), value = tf.cast(x = fill_value, dtype = tensor.dtype)) # fill the rest of the tensor with the fill value
            ], axis = axis) # concatenate our sliced tensor with our fill value tensor together

            new_shape = tensor.get_shape().as_list() # get the static shape of the tensor and output it to a list
            new_shape[axis] = new_size # change the static shape's axis to our new size
            resized.set_shape(shape = new_shape) # set the static shape of our resized tensor to our new shape
            return resized # return the resized tensor

        # Read files from file_pattern which provided by args
        input_file_names = tf.matching_files(pattern = file_pattern)

        # Determine amount of times to repeat file and if we should shuffle the file queue based on if we are training or evaluating
        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None # forever
            shuffle = True
        else:
            num_epochs = 1 # until EOF
            shuffle = False

        # Create filename queue from our input file names
        filename_queue = tf.train.string_input_producer(string_tensor = input_file_names, num_epochs = num_epochs, shuffle = shuffle)

        # Create a TF Record reader to read in our TF Record files
        reader = tf.TFRecordReader()

        # Use our TF Record reader to read from the filename queue
        queue, serialized_examples = reader.read(queue = filename_queue)
        
        # Create context and sequence feature map
        context_features = {
            "video_id": tf.FixedLenFeature(shape = [], dtype = tf.string),
            "labels": tf.VarLenFeature(dtype = tf.int64)
        }
        sequence_features = {
            "rgb": tf.FixedLenSequenceFeature(shape = [], dtype = tf.string),
            "audio": tf.FixedLenSequenceFeature(shape = [], dtype = tf.string)
        }

        # Parse TF Records into our features
        contexts, features = tf.parse_single_sequence_example(
            serialized = serialized_examples, 
            context_features = context_features,
            sequence_features = sequence_features)
        print("read_dataset_frame: _input_fn: contexts = {}".format(contexts)) # shape = video_id = (), labels = SparseTensor object
        print("read_dataset_frame: _input_fn: features = {}".format(features)) # shape = rgb = (frames_per_video,), audio = (frames_per_video,)

        # Create features
        # Pass video_id to features
        features['video_id'] = contexts['video_id'] # shape = video_id = (), rgb = (frames_per_video,), audio = (frames_per_video,)
        print("read_dataset_frame: _input_fn: features = {}".format(features))

        # Fix rgb data
        decoded_rgb = tf.reshape(tensor = tf.cast(x = tf.decode_raw(bytes = features["rgb"], out_type = tf.uint8), dtype = tf.float32), shape = [-1, 1024]) # shape = (frames_per_video, 1024)
        print("read_dataset_frame: _input_fn: decoded_rgb = {}".format(decoded_rgb))
        rgb_matrix = resize_axis(tensor = dequantize(decoded_rgb), axis = 0, new_size = MAX_FRAMES) # shape = (MAX_FRAMES, 1024)
        print("read_dataset_frame: _input_fn: rgb_matrix = {}".format(rgb_matrix))
        features['rgb'] = rgb_matrix
        print("read_dataset_frame: _input_fn: features = {}".format(features)) # shape = video_id = (), rgb = (MAX_FRAMES, 1024), audio = (frames_per_video,)

        # Fix audio data
        decoded_audio = tf.reshape(tensor = tf.cast(x = tf.decode_raw(bytes = features["audio"], out_type = tf.uint8), dtype = tf.float32), shape = [-1, 128]) # shape = (frames_per_video, 128)
        print("read_dataset_frame: _input_fn: decoded_audio = {}".format(decoded_audio))
        audio_matrix = resize_axis(tensor = dequantize(decoded_audio), axis = 0, new_size = MAX_FRAMES) # shape = (MAX_FRAMES, 128)
        print("read_dataset_frame: _input_fn: audio_matrix = {}".format(audio_matrix))
        features['audio'] = audio_matrix
        print("read_dataset_frame: _input_fn: features = {}".format(features)) # shape = video_id = (), rgb = (MAX_FRAMES, 1024), audio = (MAX_FRAMES, 128)

        # Add labels to features dictionary and change to correct format from sparse to dense and to floats
        features['labels'] = tf.cast(x = tf.sparse_to_dense(sparse_indices = contexts['labels'].values, output_shape = (NUM_CLASSES,), sparse_values = 1, validate_indices = False), dtype = tf.float32)
        print("read_dataset_frame: _input_fn: features = {}".format(features)) # shape = video_id = (), rgb = (MAX_FRAMES, 1024), audio = (MAX_FRAMES, 128), labels = (NUM_CLASSES,)

        # Shuffle and batch features
        batch_features = tf.train.shuffle_batch(
            tensors = features, 
            batch_size = batch_size, 
            capacity = batch_size * 10, 
            min_after_dequeue = batch_size,
            num_threads = 1,
            enqueue_many = False,
            allow_smaller_final_batch = True)
        print("read_dataset_frame: _input_fn: batch_features = {}".format(batch_features)) # shape = video_id = (batch_size,), rgb = (batch_size, MAX_FRAMES, 1024), audio = (batch_size, MAX_FRAMES, 128), labels = (batch_size, NUM_CLASSES)

        # Pop off labels from feature dictionary
        batch_labels = batch_features.pop('labels')
        print("read_dataset_frame: _input_fn: batch_labels = {}\n".format(batch_labels)) # shape = (batch_size, NUM_CLASSES)

        return batch_features, batch_labels
    return _input_fn

# Create our model function to be used in our custom estimator
def frame_level_model(features, labels, mode, params):
    print("\nframe_level_model: features = {}".format(features)) # features['rgb'].shape = (batch_size, MAX_FRAMES, 1024), features['audio'].shape = (batch_size, MAX_FRAMES, 128)
    print("frame_level_model: labels = {}".format(labels))
    print("frame_level_model: mode = {}".format(mode))

    # 0. Configure network
    # Get dynamic batch size
    current_batch_size = tf.shape(features['rgb'])[0]
    print("frame_level_model: current_batch_size = {}".format(current_batch_size))

    # Stack all of the features into a 3-D tensor
    combined_features = tf.concat(values = [features['rgb'], features['audio']], axis = 2) # shape = (current_batch_size, MAX_FRAMES, 1024 + 128)
    print("frame_level_model: combined_features = {}".format(combined_features))

    # Reshape the combined features into a 2-D tensor that we will pass through our DNN
    reshaped_combined_features = tf.reshape(tensor = combined_features, shape = [current_batch_size * MAX_FRAMES, 1024 + 128]) # shape = (current_batch_size * MAX_FRAMES, 1024 + 128)
    print("frame_level_model: reshaped_combined_features = {}".format(reshaped_combined_features))

    # 1. Create the DNN structure now
    # Create the input layer to our frame DNN
    network = reshaped_combined_features # shape = (current_batch_size * MAX_FRAMES, 1024 + 128)
    print("frame_level_model: network = reshaped_combined_features = {}".format(network))

    # Add hidden layers with the given number of units/neurons per layer
    for units in params['hidden_units']:
        network = tf.layers.dense(inputs = network, units = units, activation = tf.nn.relu) # shape = (current_batch_size * MAX_FRAMES, units)
        print("frame_level_model: network = {}, units = {}".format(network, units))

    # Connect the final hidden layer to a dense layer with no activation to get the logits
    logits = tf.layers.dense(inputs = network, units = NUM_CLASSES, activation = None) # shape = (current_batch_size * MAX_FRAMES, NUM_CLASSES)
    print("frame_level_model: logits = {}".format(logits))

    # Since this is a multi-class, multi-label problem we will apply a sigmoid, not a softmax, to each logit to get its own probability
    probabilities = tf.sigmoid(logits) # shape = (current_batch_size * MAX_FRAMES, NUM_CLASSES)
    print("frame_level_model: probabilities = {}".format(probabilities))

    # Reshape the probabilities back into a 3-D tensor so that we have a frames axis
    reshaped_probabilities = tf.reshape(tensor = probabilities, shape = [current_batch_size, MAX_FRAMES, NUM_CLASSES]) # shape = (current_batch_size, MAX_FRAMES, NUM_CLASSES)
    print("frame_level_model: reshaped_probabilities = {}".format(reshaped_probabilities))

    # Find the average probability over all frames for each label for each example in the batch
    average_probabilities_over_frames = tf.reduce_mean(input_tensor = reshaped_probabilities, axis = 1) # shape = (current_batch_size, NUM_CLASSES)
    print("frame_level_model: average_probabilities_over_frames = {}".format(average_probabilities_over_frames))

    # Select the top k probabilities in descending order
    top_k_probabilities = tf.nn.top_k(input = average_probabilities_over_frames, k = params['top_k'], sorted = True) # shape = (current_batch_size, top_k)
    print("frame_level_model: top_k_probabilities = {}".format(top_k_probabilities))

    # Find the logits from the average probabilities by using the inverse logit 
    inverse_probabilities_logits = tf.log(average_probabilities_over_frames + 0.00000001) - tf.log(1.0 - average_probabilities_over_frames + 0.00000001) # shape = (current_batch_size, NUM_CLASSES)
    print("frame_level_model: inverse_probabilities_logits = {}".format(inverse_probabilities_logits))

    # Select the top k logits using the indices of the top k probabilities in descending order
    top_k_logits = tf.map_fn(fn = lambda x: tf.gather(params = inverse_probabilities_logits[x], indices = top_k_probabilities.indices[x]), 
                             elems = tf.range(start = 0, limit = current_batch_size), 
                             dtype = tf.float32) # shape = (current_batch_size, 1, top_k)
    print("frame_level_model: top_k_logits = {}".format(top_k_logits))

    # Select the top k classes in descending order of likelihood
    top_k_classes = top_k_probabilities.indices # shape = (current_batch_size, top_k)
    print("frame_level_model: top_k_classes = {}".format(top_k_classes))

    # The 0/1 predictions based on a threshold, in this case the threshold is if the probability it greater than random chance
    predictions = tf.where(
        condition = average_probabilities_over_frames > 1.0 / NUM_CLASSES, # shape = (current_batch_size, NUM_CLASSES)
        x = tf.ones_like(tensor = average_probabilities_over_frames), 
        y = tf.zeros_like(tensor = average_probabilities_over_frames))
    print("frame_level_model: predictions = {}".format(predictions))

    # The 0/1 top k predictions based on a threshold, in this case the threshold is if the probability it greater than random chance
    top_k_predictions = tf.where(
        condition = top_k_probabilities.values > 1.0 / NUM_CLASSES, # shape = (current_batch_size, top_k)
        x = tf.ones_like(tensor = top_k_probabilities.values), 
        y = tf.zeros_like(tensor = top_k_probabilities.values))
    print("frame_level_model: top_k_predictions = {}\n".format(top_k_predictions))

    # 2. Loss function, training/eval ops 
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        # Since this is a multi-class, multi-label problem, we will use sigmoid activation and cross entropy loss
        # We already have the probabilities we can use the cross entropy formula directly to calculate the loss
        loss = tf.reduce_mean(input_tensor = -tf.reduce_sum(input_tensor = labels * tf.log(x = average_probabilities_over_frames + 0.00000001), axis = 1))

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
    predictions_dict = {"logits": top_k_logits, 
                        "probabilities": top_k_probabilities.values, 
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
    def get_shape_and_set_modified_shape_3D(tensor, additional_dimension_sizes):
        # Get static shape for tensor and convert it to list
        shape = tensor.get_shape().as_list()
        # Set outer shape to additional_dimension_sizes[0] * additional_dimension_sizes[1] since we know that this is the correct size
        shape[1] = additional_dimension_sizes[0] * additional_dimension_sizes[0]
        # Set the shape of tensor to our modified shape
        tensor.set_shape(shape = shape) # shape = (batch_size, additional_dimension_sizes[0] * additional_dimension_sizes[1])
        print("serving_input_fn: get_shape_and_set_modified_shape_3D: tensor = {}, additional_dimension_sizes = {}".format(tensor, additional_dimension_sizes))
        # Finally reshape tensor into the shape it is supposed to be for the model function
        tensor = tf.reshape(tensor = tensor, shape = [-1, additional_dimension_sizes[0], additional_dimension_sizes[1]]) # shape = (batch_size, additional_dimension_sizes[0], additional_dimension_sizes[1])
        print("serving_input_fn: get_shape_and_set_modified_shape_3D: tensor = {}, additional_dimension_sizes = {}".format(tensor, additional_dimension_sizes))
        return tensor

    # Create placeholders to accept the data sent to the model at serving time
    feature_placeholders = { # all features come in as a batch of strings, shape = (batch_size,), this was so because of passing the arrays to online ml-engine prediction
        'video_id': tf.placeholder(dtype = tf.string, shape = [None]),
        'rgb': tf.placeholder(dtype = tf.string, shape = [None]),
        'audio': tf.placeholder(dtype = tf.string, shape = [None])
    }
    print("\nserving_input_fn: feature_placeholders = {}".format(feature_placeholders))

    # Create feature tensors
    features = {
        "video_id": feature_placeholders["video_id"],
        "rgb": fix_shape_and_type_for_serving(placeholder = feature_placeholders["rgb"]),
        "audio": fix_shape_and_type_for_serving(placeholder = feature_placeholders["audio"])
    }
    print("serving_input_fn: features = {}".format(features))

    # Fix dynamic shape ambiguity of feature tensors for our DNN
    features["rgb"] = get_shape_and_set_modified_shape_3D(tensor = features["rgb"], additional_dimension_sizes = [MAX_FRAMES, 1024])
    features["audio"] = get_shape_and_set_modified_shape_3D(tensor = features["audio"], additional_dimension_sizes = [MAX_FRAMES, 128])
    print("serving_input_fn: features = {}\n".format(features))

    return tf.estimator.export.ServingInputReceiver(features = features, receiver_tensors = feature_placeholders)

# Create custom estimator's train and evaluate function
def train_and_evaluate(args):
    # Create our custome estimator using our model function
    estimator = tf.estimator.Estimator(
        model_fn = frame_level_model, 
        model_dir = args['output_dir'],
        params = {'hidden_units': args['hidden_units'], 'top_k': args['top_k']})
    # Create train spec to read in our training data
    train_spec = tf.estimator.TrainSpec(
        input_fn = read_dataset_frame(
            file_pattern = args['train_file_pattern'], 
            mode = tf.estimator.ModeKeys.TRAIN, 
            batch_size = args['batch_size']),
        max_steps = args['train_steps'])
    # Create exporter to save out the complete model to disk
    exporter = tf.estimator.LatestExporter(name = 'exporter', serving_input_receiver_fn = serving_input_fn)
    # Create eval spec to read in our validation data and export our model
    eval_spec = tf.estimator.EvalSpec(
        input_fn = read_dataset_frame(
            file_pattern = args['eval_file_pattern'], 
            mode = tf.estimator.ModeKeys.EVAL, 
            batch_size = args['batch_size']),
        steps = None,
        exporters = exporter,
        start_delay_secs = args['start_delay_secs'],
        throttle_secs = args['throttle_secs'])
    # Create train and evaluate loop to train and evaluate our estimator
    tf.estimator.train_and_evaluate(estimator = estimator, train_spec = train_spec, eval_spec = eval_spec)