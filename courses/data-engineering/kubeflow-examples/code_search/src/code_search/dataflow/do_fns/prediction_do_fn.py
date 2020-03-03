# pylint: skip-file

"""A cherry-pick of PredictionDoFn from Kubeflow Batch Predict.

TODO: This file should be retired once kubeflow/batch-predict#10 is resolved.
"""

import datetime
import json
import logging
import threading
import traceback


import apache_beam as beam
from apache_beam.options.value_provider import ValueProvider
from apache_beam.utils.windowed_value import WindowedValue

from kubeflow_batch_predict import prediction as mlprediction
from kubeflow_batch_predict.dataflow import _aggregators as aggregators


from kubeflow_batch_predict.dataflow import _error_filter as error_filter
from tensorflow.python.saved_model import tag_constants

DEFAULT_BATCH_SIZE = 1000  # 1K instances per batch when evaluating models.
LOG_SIZE_LIMIT = 1000  # 1K bytes for the input field in log entries.
LOG_NAME = "worker"
_METRICS_NAMESPACE = "cloud_ml_batch_predict"


class PredictionDoFn(beam.DoFn):
  """A DoFn class loading the model to create session and performing prediction.

  The input PCollection consists of a list of strings from the input files.

  The DoFn first loads model from a given path where meta graph data and
  checkpoint data are exported to. Then if the there is only one string input
  tensor or the model needs to preprocess the input, it directly passes the
  data to prediction. Otherwise, it tries to load the data into JSON.

  Then it batches the inputs of each instance into one feed_dict. After that, it
  runs session and predicts the interesting values for all the instances.
  Finally it emits the prediction result for each individual instance.
  """

  class _ModelState(object):
    """Atomic representation of the in-memory state of the model."""

    def __init__(self,
                 model_dir,
                 tags,
                 framework=mlprediction.TENSORFLOW_FRAMEWORK_NAME):
      self.model_dir = model_dir
      client = mlprediction.create_client(framework, model_dir, tags)
      self.model = mlprediction.create_model(client, model_dir, framework)

  _thread_local = threading.local()

  def __init__(self,
               aggregator_dict=None,
               user_project_id="",
               user_job_id="",
               tags=tag_constants.SERVING,
               signature_name="",
               skip_preprocessing=False,
               target="",
               config=None,
               instances_key='instances',
               predictions_key='predictions',
               framework=mlprediction.TENSORFLOW_FRAMEWORK_NAME):
    """Constructor of Prediction beam.DoFn class.

    Args:
      aggregator_dict: A dict of aggregators containing maps from counter name
                       to the aggregator.
      user_project_id: A string. The project to which the logs will be sent.
      user_job_id:     A string. The job to which the logs will be sent.
      tags: A comma-separated string that contains a list of tags for serving
            graph.
      signature_name: A string to map into the signature map to get the serving
                     signature.
      skip_preprocessing: bool whether to skip preprocessing even when
                          the metadata.yaml/metadata.json file exists.
      target: The execution engine to connect to. See target in tf.Session(). In
              most cases, users should not set the target.
      config: A ConfigProto proto with configuration options. See config in
              tf.Session()
      framework: The framework used to train this model. Available frameworks:
               "TENSORFLOW", "SCIKIT_LEARN", and "XGBOOST".

    Side Inputs:
      model_dir: The directory containing the model to load and the
                 checkpoint files to restore the session.
    """
    self._target = target
    self._user_project_id = user_project_id
    self._user_job_id = user_job_id
    self._tags = tags
    self._signature_name = signature_name
    self._skip_preprocessing = skip_preprocessing
    self._config = config
    self._aggregator_dict = aggregator_dict
    self._model_state = None
    self._instances_key = instances_key
    self._predictions_key = predictions_key


    self._tag_list = []
    self._framework = framework
    # Metrics.
    self._model_load_seconds_distribution = beam.metrics.Metrics.distribution(
        _METRICS_NAMESPACE, "model_load_seconds")
    self._batch_process_ms_distribution = beam.metrics.Metrics.distribution(
        _METRICS_NAMESPACE, "batch_process_milliseconds")

  def start_bundle(self):
    if isinstance(self._signature_name, ValueProvider):
      self._signature_name = self._signature_name.get()

    if isinstance(self._tags, ValueProvider):
      self._tags = self._tags.get()

    self._tag_list = self._tags.split(",")

  def process(self, element, model_dir):
    try:
      if isinstance(model_dir, ValueProvider):
        model_dir = model_dir.get()
      framework = self._framework.get() if isinstance(self._framework, ValueProvider) else self._framework
      if self._model_state is None:
        if (getattr(self._thread_local, "model_state", None) is None or
            self._thread_local.model_state.model_dir != model_dir):
          start = datetime.datetime.now()
          self._thread_local.model_state = self._ModelState(
              model_dir, self._tag_list, framework)
          self._model_load_seconds_distribution.update(
              int((datetime.datetime.now() - start).total_seconds()))
        self._model_state = self._thread_local.model_state
      else:
        assert self._model_state.model_dir == model_dir

      # Measure the processing time.
      start = datetime.datetime.now()
      # Try to load it.
      if framework == mlprediction.TENSORFLOW_FRAMEWORK_NAME:
        # Even though predict() checks the signature in TensorFlowModel,
        # we need to duplicate this check here to determine the single string
        # input case.
        self._signature_name, signature = self._model_state.model.get_signature(
            self._signature_name)
        if self._model_state.model.is_single_string_input(signature):
          loaded_data = element
        else:
          loaded_data = [json.loads(d) for d in element]
      else:
        loaded_data = [json.loads(d) for d in element]
      loaded_data = mlprediction.decode_base64(loaded_data)
      instances = loaded_data[self._instances_key]

      # Actual prediction occurs.
      kwargs = {}
      if self._signature_name:
        kwargs = {"signature_name": self._signature_name}
      inputs, predictions = self._model_state.model.predict(instances, **kwargs)

      predictions = list(predictions)

      if self._aggregator_dict:
        self._aggregator_dict[aggregators.AggregatorName.ML_PREDICTIONS].inc(
            len(predictions))

      # For successful processing, record the time.
      td = datetime.datetime.now() - start
      time_delta_in_ms = int(
          td.microseconds / 10**3  + (td.seconds + td.days * 24 * 3600) * 10**3)
      self._batch_process_ms_distribution.update(time_delta_in_ms)

      loaded_data[self._predictions_key] = predictions
      yield loaded_data

    except mlprediction.PredictionError as e:
      logging.error("Got a known exception: [%s]\n%s", str(e),
                    traceback.format_exc())
      clean_error_detail = error_filter.filter_tensorflow_error(e.error_detail)


      # Track in the counter.
      if self._aggregator_dict:
        counter_name = aggregators.AggregatorName.ML_FAILED_PREDICTIONS
        self._aggregator_dict[counter_name].inc(len(element))

      # reraise failure to load model as permanent exception to end dataflow job
      if e.error_code == mlprediction.PredictionError.FAILED_TO_LOAD_MODEL:
        raise beam.utils.retry.PermanentException(clean_error_detail)
      try:
        yield beam.pvalue.TaggedOutput("errors", (clean_error_detail,
                                                  element))
      except AttributeError:
        yield beam.pvalue.SideOutputValue("errors", (clean_error_detail,
                                                     element))

    except Exception as e:  # pylint: disable=broad-except
      logging.error("Got an unknown exception: [%s].", traceback.format_exc())


      # Track in the counter.
      if self._aggregator_dict:
        counter_name = aggregators.AggregatorName.ML_FAILED_PREDICTIONS
        self._aggregator_dict[counter_name].inc(len(element))

      try:
        yield beam.pvalue.TaggedOutput("errors", (str(e), element))
      except AttributeError:
        yield beam.pvalue.SideOutputValue("errors", (str(e), element))
