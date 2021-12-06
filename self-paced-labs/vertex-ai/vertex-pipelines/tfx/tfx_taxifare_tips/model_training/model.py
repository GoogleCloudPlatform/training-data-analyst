"""TensorFlow model training code."""
from typing import Dict
import tensorflow as tf
import tensorflow_transform as tft
from tfx_taxifare_tips.model_training import features


def _create_model_input_layers():
    """
    Args:
    Returns:
      inputs (dict[str] = tf.keras.layers):
    """
    input_layers = {}
    for feature_name in features.FEATURE_NAMES:
        name = features.transformed_name(feature_name)
        if feature_name in features.NUMERICAL_FEATURE_NAMES:
            input_layers[name] = tf.keras.layers.Input(
                name=name, shape=[], dtype=tf.float32
            )
        elif feature_name in features.categorical_feature_names():
            input_layers[name] = tf.keras.layers.Input(
                name=name, shape=[], dtype=tf.int64
            )
        else:
            pass

    return input_layers


def _create_model_preprocessing_layers(input_layers, tft_output: tft.TFTransformOutput):
    """
    Args:
    Returns:
    """
    preprocessing_layers = []
    for key in input_layers:
        feature_name = features.original_name(key)
        if feature_name in features.EMBEDDING_CATEGORICAL_FEATURES:
            vocab_size = tft_output.vocabulary_size_by_name(feature_name)
            embedding_size = features.EMBEDDING_CATEGORICAL_FEATURES[feature_name]
            embedding_output = tf.keras.layers.Embedding(
                input_dim=vocab_size + 1,
                output_dim=embedding_size,
                name=f"{key}_embedding",
            )(input_layers[key])
            preprocessing_layers.append(embedding_output)
        elif feature_name in features.ONEHOT_CATEGORICAL_FEATURE_NAMES:
            vocab_size = tft_output.vocabulary_size_by_name(feature_name)
            onehot_layer = tf.keras.layers.CategoryEncoding(
                max_tokens=vocab_size,
                output_mode="binary",
                name=f"{key}_onehot",
            )(input_layers[key])
            preprocessing_layers.append(onehot_layer)
        elif feature_name in features.NUMERICAL_FEATURE_NAMES:
            numeric_layer = tf.expand_dims(input_layers[key], -1)
            preprocessing_layers.append(numeric_layer)
        else:
            pass

    return preprocessing_layers


def build_binary_classifier(hyperparameters: Dict, tft_output: tft.TFTransformOutput):
    """
    Args:
      hyperparameters:
      tft_output: A TFTransformOutput.
    Returns:
      model:
    """
    input_layers = _create_model_input_layers()

    preprocessing_layers = _create_model_preprocessing_layers(
        input_layers=input_layers, tft_output=tft_output
    )

    joined = tf.keras.layers.Concatenate(name="combines_inputs")(preprocessing_layers)

    feedforward_output = tf.keras.Sequential(
        [
            tf.keras.layers.Dense(units, activation="relu")
            for units in hyperparameters["hidden_units"]
        ],
        name="feedforward_network",
    )(joined)

    logits = tf.keras.layers.Dense(units=1, name="logits")(feedforward_output)

    model = tf.keras.Model(inputs=input_layers, outputs=[logits])

    return model
