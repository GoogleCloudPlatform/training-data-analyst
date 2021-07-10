import numpy as np
import os
import tensorflow as tf
import datetime

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.INFO)


def create_dataset(file_pattern, batch_size, mode):
    """Creates tf.data Dataset Object to feed into model.

    Args:
        file_pattern: str, file patterns to TFRecord data.
        batch_size: int, batch size for training.
        mode: tf.estimator.ModeKeys (TRAIN/EVAL).

    Returns:
        tf.data Dataset object.
    """

    def _parse(serialized_example):
        """Parse serialized example and return feature_dict and label.

        Args:
            serialized_example: tf.example to parse.

        Returns:
            Parsed features dictionary and label.
        """

        feature_map = {
            'dayofweek': tf.io.FixedLenFeature([], tf.int64),
            'dropofflat': tf.io.FixedLenFeature([], tf.float32),
            'dropofflon': tf.io.FixedLenFeature([], tf.float32),
            'fare_amount': tf.io.FixedLenFeature([], tf.float32),
            'hourofday': tf.io.FixedLenFeature([], tf.int64),
            'passengers': tf.io.FixedLenFeature([], tf.float32),
            'pickuplat': tf.io.FixedLenFeature([], tf.float32),
            'pickuplon': tf.io.FixedLenFeature([], tf.float32)
        }

        # Parse the serialized data into a dictionary.
        parsed_example = tf.io.parse_single_example(
            serialized=serialized_example,
            features=feature_map)

        features = add_engineered(parsed_example)
        label = features.pop("fare_amount")

        return features, label

    # Create a TensorFlow Dataset-object which has functionality
    # for reading and shuffling data from TFRecords files.
    files = tf.io.gfile.glob(file_pattern)
    dataset = tf.data.TFRecordDataset(
        filenames=files, compression_type="GZIP")

    # Parse the serialized data in the TFRecords files..
    dataset = dataset.map(_parse)

    if mode == tf.estimator.ModeKeys.TRAIN:
        # Repeat the dataset the given number of times.
        dataset = dataset.repeat().shuffle(
            buffer_size=10*batch_size)

    # Get a batch of data with the given size.
    dataset = dataset.batch(batch_size)

    # Get the next batch of images and labels.
    return dataset


def add_engineered(features):
    """Add engineered features to features dict.

    Args:
        features: dict, dictionary of input features.

    Returns:
        features: dict, dictionary with engineered features added.
    """
    features["londiff"] = features["dropofflon"] - features["pickuplon"]
    features["latdiff"] = features["dropofflat"] - features["pickuplat"]
    features["euclidean"] = tf.math.sqrt(
        features["londiff"]**2 + features["latdiff"]**2)
    return features


def serving_input_fn():
    """Creates serving input receiver for EvalSpec.

    Returns:
        tf.estimator.export.ServingInputReceiver object containing
            placeholders and features.
    """
    inputs = {
        "dayofweek": tf.compat.v1.placeholder(
            dtype=tf.dtypes.int64, shape=[None], name="dayofweek"),
        "hourofday": tf.compat.v1.placeholder(
            dtype=tf.dtypes.int64, shape=[None], name="hourofday"),
        "pickuplon": tf.compat.v1.placeholder(
            dtype=tf.dtypes.float32, shape=[None], name="pickuplon"),
        "pickuplat": tf.compat.v1.placeholder(
            dtype=tf.dtypes.float32, shape=[None], name="pickuplat"),
        "dropofflon": tf.compat.v1.placeholder(
            dtype=tf.dtypes.float32, shape=[None], name="dropofflon"),
        "dropofflat": tf.compat.v1.placeholder(
            dtype=tf.dtypes.float32, shape=[None], name="dropofflat"),
        "passengers": tf.compat.v1.placeholder(
            dtype=tf.dtypes.float32, shape=[None], name="passengers")
    }

    features = add_engineered(inputs)

    return tf.estimator.export.ServingInputReceiver(
        features=features, receiver_tensors=inputs)


def train_and_evaluate(args):
    """Build tf.estimator.DNNRegressor and call train_and_evaluate loop.

    Args:
        args: dict, dictionary of command line arguments from task.py.
    """
    feat_cols = [
        tf.feature_column.numeric_column('dayofweek'),
        tf.feature_column.numeric_column('hourofday'),
        tf.feature_column.numeric_column('pickuplat'),
        tf.feature_column.numeric_column('pickuplon'),
        tf.feature_column.numeric_column('dropofflat'),
        tf.feature_column.numeric_column('dropofflon'),
        tf.feature_column.numeric_column('passengers'),
        tf.feature_column.numeric_column('euclidean'),
        tf.feature_column.numeric_column('latdiff'),
        tf.feature_column.numeric_column('londiff')
    ]

    estimator = tf.estimator.DNNRegressor(
        feature_columns=feat_cols,
        hidden_units=args['hidden_units'].split(' '),
        model_dir=args['output_dir']
    )

    train_spec = tf.estimator.TrainSpec(
        input_fn=lambda: create_dataset(
            file_pattern=args['train_data_path'],
            batch_size=args['train_batch_size'],
            mode=tf.estimator.ModeKeys.TRAIN),
        max_steps=300
    )

    exporter = exporter = tf.estimator.LatestExporter(
        name="exporter",
        serving_input_receiver_fn=serving_input_fn)

    eval_spec = tf.estimator.EvalSpec(
        input_fn=lambda: create_dataset(
            file_pattern=args['eval_data_path'],
            batch_size=args['eval_batch_size'],
            mode=tf.estimator.ModeKeys.EVAL),
        exporters=exporter,
        steps=50
    )

    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)

