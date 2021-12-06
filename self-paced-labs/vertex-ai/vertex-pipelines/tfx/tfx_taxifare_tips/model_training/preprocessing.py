"""TensorFlow Transform preprocessing function."""

import tensorflow as tf
import tensorflow_transform as tft

from tfx_taxifare_tips.model_training import features


def preprocessing_fn(inputs):
    """tf.transform's callback function for preprocessing inputs.
    Args:
      inputs: map from feature keys to raw not-yet-transformed features.
    Returns:
      Map from string feature key to transformed feature operations.
    """

    outputs = {}

    for key in features.FEATURE_NAMES:
        if key in features.NUMERICAL_FEATURE_NAMES:
            outputs[features.transformed_name(key)] = tft.scale_to_z_score(inputs[key])

        elif key in features.categorical_feature_names():
            outputs[features.transformed_name(key)] = tft.compute_and_apply_vocabulary(
                inputs[key],
                num_oov_buckets=1,
                vocab_filename=key,
            )

    outputs[features.TARGET_FEATURE_NAME] = inputs[features.TARGET_FEATURE_NAME]

    for key in outputs:
        outputs[key] = tf.squeeze(outputs[key], -1)

    return outputs
