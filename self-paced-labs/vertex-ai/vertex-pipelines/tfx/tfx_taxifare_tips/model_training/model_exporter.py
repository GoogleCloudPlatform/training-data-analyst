"""Functions for exporting the model for serving."""

import logging

import tensorflow as tf
import tensorflow_transform as tft
import tensorflow_data_validation as tfdv
from tensorflow_transform.tf_metadata import schema_utils

from tfx_taxifare_tips.model_training import features


def _get_serve_tf_examples_fn(classifier, tft_output, raw_feature_spec):
    """Returns a function that parses a serialized tf.Example and applies TFT."""

    classifier.tft_layer = tft_output.transform_features_layer()

    @tf.function
    def serve_tf_examples_fn(serialized_tf_examples):
        """Returns the output to be used in the serving signature."""
        for key in list(raw_feature_spec.keys()):
            if key not in features.FEATURE_NAMES:
                raw_feature_spec.pop(key)

        parsed_features = tf.io.parse_example(serialized_tf_examples, raw_feature_spec)

        transformed_features = classifier.tft_layer(parsed_features)
        logits = classifier(transformed_features)
        probabilities = tf.keras.activations.sigmoid(logits)
        return {"probabilities": probabilities}

    return serve_tf_examples_fn


def _get_serve_features_fn(classifier, tft_output):
    """Returns a function that accept a dictionary of features and applies TFT."""

    classifier.tft_layer = tft_output.transform_features_layer()

    @tf.function
    def serve_features_fn(raw_features):
        """Returns the output to be used in the serving signature."""

        transformed_features = classifier.tft_layer(raw_features)
        logits = classifier(transformed_features)
        neg_probabilities = tf.keras.activations.sigmoid(logits)
        pos_probabilities = 1 - neg_probabilities
        probabilities = tf.concat([neg_probabilities, pos_probabilities], -1)
        batch_size = tf.shape(probabilities)[0]
        classes = tf.repeat([features.TARGET_LABELS], [batch_size], axis=0)
        return {"classes": classes, "scores": probabilities}

    return serve_features_fn


def export_serving_model(
    classifier, serving_model_dir, raw_schema_location, tft_output_dir
):

    raw_schema = tfdv.load_schema_text(raw_schema_location)
    raw_feature_spec = schema_utils.schema_as_feature_spec(raw_schema).feature_spec

    tft_output = tft.TFTransformOutput(tft_output_dir)

    features_input_signature = {
        feature_name: tf.TensorSpec(
            shape=(None, 1), dtype=spec.dtype, name=feature_name
        )
        for feature_name, spec in raw_feature_spec.items()
        if feature_name in features.FEATURE_NAMES
    }

    signatures = {
        "serving_default": _get_serve_features_fn(
            classifier, tft_output
        ).get_concrete_function(features_input_signature),
        "serving_tf_example": _get_serve_tf_examples_fn(
            classifier, tft_output, raw_feature_spec
        ).get_concrete_function(
            tf.TensorSpec(shape=[None], dtype=tf.string, name="examples")
        ),
    }

    logging.info("Model export started...")
    classifier.save(serving_model_dir, signatures=signatures)
    logging.info("Model export completed.")
