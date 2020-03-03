import json
import logging
import os
import sys

import numpy as np
import dill as dpickle
import pandas as pd
import tensorflow as tf
# TODO(https://github.com/kubeflow/examples/issues/280)
# TODO(https://github.com/kubeflow/examples/issues/196)
# We'd like to switch to importing keras from TensorFlow in order to support
# TF.Estimator but using tensorflow.keras we can't train a model either using
# Keras' fit function or using TF.Estimator.
import keras
from keras.callbacks import CSVLogger, ModelCheckpoint

from ktext.preprocess import processor
from sklearn.model_selection import train_test_split
from seq2seq_utils import load_decoder_inputs, load_encoder_inputs, load_text_processor, Seq2Seq_Inference # # pylint: disable=line-too-long

class Trainer(object): #pylint: disable=too-many-instance-attributes
  def __init__(self, output_dir):
    """Construct the trainer.

    Args:
      output_dir: Directory where outputs should be written.
    """
    if not output_dir:
      raise ValueError("output dir can't be None.")

    self.output_dir = output_dir

    # Pull out the information needed for TF.Estimator.
    self.tf_config = os.environ.get('TF_CONFIG', '{}')
    self.tf_config_json = json.loads(self.tf_config)

    self.cluster = self.tf_config_json.get('cluster')
    self.job_name = self.tf_config_json.get('task', {}).get('type')
    self.task_index = self.tf_config_json.get('task', {}).get('index')

    # Files storing the preprocessors
    self.body_pp_file = os.path.join(self.output_dir, 'body_pp.dpkl')
    self.title_pp_file = os.path.join(self.output_dir, 'title_pp.dpkl')

    # Files to store the processed data
    self.preprocessed_titles = os.path.join(self.output_dir,
                                            'train_title_vecs.npy')
    self.preprocessed_bodies = os.path.join(self.output_dir,
                                            'train_body_vecs.npy')

    self.history = None
    self.decoder_input_data = None
    self.seq2seq_Model = None
    self.decoder_target_data = None
    self.test_df = None
    self.encoder_input_data = None
    self.title_pp = None
    self.body_pp = None

  def preprocess(self, data_file, num_samples=None):
    """Preprocess the input.

    Trains preprocessors and splits the data into train and test sets.

    Args:
      data_file: The datafile to process
      num_samples: Number of samples to use. Set to None to use
        entire dataset.
    """
    # We preprocess the data if we are the master or chief.
    # Or if we aren't running distributed.
    if self.job_name and self.job_name.lower() not in ["master", "chief"]:
      return

    # TODO(jlewi): The test data isn't being used for anything. How can
    # we configure evaluation?
    if num_samples:
      sampled = pd.read_csv(data_file).sample(n=num_samples)
      traindf, self.test_df = train_test_split(sampled, test_size=.10)
    else:
      traindf, self.test_df = train_test_split(pd.read_csv(data_file), test_size=.10)

    # Print stats about the shape of the data.
    logging.info('Train: %d rows %d columns', traindf.shape[0], traindf.shape[1])

    train_body_raw = traindf.body.tolist()
    train_title_raw = traindf.issue_title.tolist()

    # Clean, tokenize, and apply padding / truncating such that each document
    # length = 70. Also, retain only the top 8,000 words in the vocabulary and set
    # the remaining words to 1 which will become common index for rare words.
    self.body_pp = processor(keep_n=8000, padding_maxlen=70)
    train_body_vecs = self.body_pp.fit_transform(train_body_raw)

    logging.info('Example original body: %s', train_body_raw[0])
    logging.info('Example body after pre-processing: %s', train_body_vecs[0])

    self.title_pp = processor(append_indicators=True, keep_n=4500,
                              padding_maxlen=12, padding='post')

    # process the title data
    train_title_vecs = self.title_pp.fit_transform(train_title_raw)

    logging.info('Example original title: %s', train_title_raw[0])
    logging.info('Example title after pre-processing: %s', train_title_vecs[0])

    # Save the preprocessor
    with open(self.body_pp_file, 'wb') as f:
      dpickle.dump(self.body_pp, f)

    with open(self.title_pp_file, 'wb') as f:
      dpickle.dump(self.title_pp, f)

    # Save the processed data
    np.save(self.preprocessed_titles, train_title_vecs)
    np.save(self.preprocessed_bodies, train_body_vecs)

  def build_model(self, learning_rate):
    """Build a keras model."""
    logging.info("starting")

    if self.job_name and self.job_name.lower() in ["ps"]:
      logging.info("ps doesn't build model")
      return

    self.encoder_input_data, doc_length = load_encoder_inputs(
      self.preprocessed_bodies)
    self.decoder_input_data, self.decoder_target_data = load_decoder_inputs(
      self.preprocessed_titles)

    num_encoder_tokens, self.body_pp = load_text_processor(
      self.body_pp_file)
    num_decoder_tokens, self.title_pp = load_text_processor(
      self.title_pp_file)

    #arbitrarly set latent dimension for embedding and hidden units
    latent_dim = 300

    ##### Define Model Architecture ######

    ########################
    #### Encoder Model ####
    encoder_inputs = keras.layers.Input(shape=(doc_length,), name='Encoder-Input')

    # Word embeding for encoder (ex: Issue Body)
    x = keras.layers.Embedding(
      num_encoder_tokens, latent_dim, name='Body-Word-Embedding', mask_zero=False)(encoder_inputs)
    x = keras.layers.BatchNormalization(name='Encoder-Batchnorm-1')(x)

    # We do not need the `encoder_output` just the hidden state.
    _, state_h = keras.layers.GRU(latent_dim, return_state=True, name='Encoder-Last-GRU')(x)

    # Encapsulate the encoder as a separate entity so we can just
    #  encode without decoding if we want to.

    encoder_model = keras.Model(inputs=encoder_inputs, outputs=state_h, name='Encoder-Model')
    seq2seq_encoder_out = encoder_model(encoder_inputs)

    ########################
    #### Decoder Model ####
    decoder_inputs = keras.layers.Input(shape=(None,), name='Decoder-Input')  # for teacher forcing

    # Word Embedding For Decoder (ex: Issue Titles)
    dec_emb = keras.layers.Embedding(
      num_decoder_tokens,
                latent_dim, name='Decoder-Word-Embedding',
                mask_zero=False)(decoder_inputs)
    dec_bn = keras.layers.BatchNormalization(name='Decoder-Batchnorm-1')(dec_emb)

    # TODO(https://github.com/kubeflow/examples/issues/196):
    # With TF.Estimtor we hit https://github.com/keras-team/keras/issues/9761
    # and the model won't train.
    decoder_gru = keras.layers.GRU(
      latent_dim, return_state=True, return_sequences=True, name='Decoder-GRU')

    decoder_gru_output, _ = decoder_gru(dec_bn, initial_state=[seq2seq_encoder_out])
    x = keras.layers.BatchNormalization(name='Decoder-Batchnorm-2')(decoder_gru_output)

    # Dense layer for prediction
    decoder_dense = keras.layers.Dense(
      num_decoder_tokens, activation='softmax', name='Final-Output-Dense')
    decoder_outputs = decoder_dense(x)

    ########################
    #### Seq2Seq Model ####

    self.seq2seq_Model = keras.Model([encoder_inputs, decoder_inputs], decoder_outputs)

    self.seq2seq_Model.compile(
      optimizer=keras.optimizers.Nadam(lr=learning_rate),
      loss='sparse_categorical_crossentropy',)
      #  TODO(jlewi): Computing accuracy causes a dimension mismatch.
      # tensorflow.python.framework.errors_impl.InvalidArgumentError: Incompatible shapes: [869] vs. [79,11] # pylint: disable=line-too-long
      # [[{{node metrics/acc/Equal}} = Equal[T=DT_FLOAT, _device="/job:localhost/replica:0/task:0/device:CPU:0"](metrics/acc/Reshape, metrics/acc/Cast)]]  # pylint: disable=line-too-long
      # metrics=['accuracy'])

    self.seq2seq_Model.summary()

  def train_keras(self,
                  output_model_h5,
                  base_name='tutorial_seq2seq', batch_size=1200, epochs=7):
    """Train using Keras.

    This is an alternative to using the TF.Estimator API.

    TODO(jlewi): The reason we added support for using Keras
    was to debug whether we were hitting issue:
    https://github.com/keras-team/keras/issues/9761 only with TF.Estimator.
    """
    logging.info("Using base name: %s", base_name)
    csv_logger = CSVLogger('{:}.log'.format(base_name))
    model_checkpoint = ModelCheckpoint(
      '{:}.epoch{{epoch:02d}}-val{{val_loss:.5f}}.hdf5'.format(
        base_name), save_best_only=True)

    self.history = self.seq2seq_Model.fit(
      [self.encoder_input_data, self.decoder_input_data],
      np.expand_dims(self.decoder_target_data, -1),
      batch_size=batch_size,
              epochs=epochs,
              validation_split=0.12, callbacks=[csv_logger, model_checkpoint])

    #############
    # Save model.
    #############
    self.seq2seq_Model.save(output_model_h5)

  def evaluate_keras(self):
    """Generates predictions on holdout set and calculates BLEU Score."""
    seq2seq_inf = Seq2Seq_Inference(encoder_preprocessor=self.body_pp,
                                    decoder_preprocessor=self.title_pp,
                                    seq2seq_model=self.seq2seq_Model)

    bleu_score = seq2seq_inf.evaluate_model(holdout_bodies=self.test_df.body.tolist(),
                                            holdout_titles=self.test_df.issue_title.tolist(),
                                            max_len_title=12)
    logging.info("Bleu score: %s", bleu_score)
    return bleu_score

  def train_estimator(self):
    """Train the model using the TF.Estimator API."""
    if self.job_name:
      cluster_spec = tf.train.ClusterSpec(self.cluster)
    if self.job_name == "ps":
      server = tf.train.Server(cluster_spec, job_name=self.job_name,
                               task_index=self.task_index)

      server.join()
      sys.exit(0)

    cfg = tf.estimator.RunConfig(session_config=tf.ConfigProto(log_device_placement=False))

    estimator = keras.estimator.model_to_estimator(
      keras_model=self.seq2seq_Model, model_dir=self.output_dir,
                  config=cfg)

    expanded = np.expand_dims(self.decoder_target_data, -1)
    input_fn = tf.estimator.inputs.numpy_input_fn(
      x={'Encoder-Input': self.encoder_input_data,
                    'Decoder-Input': self.decoder_input_data},
                 y=expanded,
                 shuffle=False)

    train_spec = tf.estimator.TrainSpec(input_fn=input_fn,
                                        max_steps=self.args.max_steps)
    eval_spec = tf.estimator.EvalSpec(input_fn=input_fn, throttle_secs=10,
                                      steps=self.args.eval_steps)

    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)
