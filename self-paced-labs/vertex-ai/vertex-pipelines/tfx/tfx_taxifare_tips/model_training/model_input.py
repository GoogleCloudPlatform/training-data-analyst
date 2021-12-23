"""Functions for reading data as tf.data.Dataset into TFX pipeline."""

from typing import List

import tensorflow as tf
from tfx import v1 as tfx
from tfx_bsl.public import tfxio
from tensorflow_metadata.proto.v0 import schema_pb2

from tfx_taxifare_tips.model_training import features


def get_dataset(
    file_pattern: List[str],
    data_accessor: tfx.components.DataAccessor,
    schema: schema_pb2.Schema,
    batch_size: int = 200,
) -> tf.data.Dataset:
    """Generates features and label for training.
    Args:
      file_pattern: List of paths or patterns of input tfrecord files.
      data_accessor: DataAccessor for converting input to RecordBatch.
      schema: schema of the input data.
      batch_size: representing the number of consecutive elements of returned
        dataset to combine in a single batch.
    Returns:
      A dataset that contains (features, indices) tuple where features is a
        dictionary of Tensors, and indices is a single Tensor of label indices.
    """
    dataset = data_accessor.tf_dataset_factory(
        file_pattern,
        tfxio.TensorFlowDatasetOptions(
            batch_size=batch_size, label_key=features.TARGET_FEATURE_NAME
        ),
        schema=schema,
    ).repeat()

    return dataset
