import tensorflow as tf


# Dense autoencoder model functions
def dense_encoder(X, params):
  """Dense model encoder subgraph that produces latent matrix.

  Given data matrix tensor X and dictionary of parameters, process through dense
  model encoder subgraph and return encoder latent vector for each example in
  batch.

  Args:
    X: tf.float64 matrix tensor of input data.
    params: Dictionary of parameters.

  Returns:
    tf.float64 matrix tensor encoder latent vector for each example in batch.
  """
  # Create the input layer to our DNN
  network = X

  # Add hidden layers with the given number of units/neurons per layer
  for units in params["enc_dnn_hidden_units"]:
    network = tf.layers.dense(
        inputs=network,
        units=units,
        activation=tf.nn.relu)

  latent_matrix = tf.layers.dense(
      inputs=network,
      units=params["latent_vector_size"],
      activation=tf.nn.relu)

  return latent_matrix


def dense_decoder(latent_matrix, orig_dims, params):
  """Dense model decoder subgraph that produces output matrix.

  Given encoder latent matrix tensor, the original dimensions of the input, and
  dictionary of parameters, process through dense model decoder subgraph and
  return decoder output matrix.

  Args:
    latent_matrix: tf.float64 matrix tensor of encoder latent matrix.
    orig_dims: Original dimensions of input data.
    params: Dictionary of parameters.

  Returns:
    tf.float64 matrix tensor decoder output vector for each example in batch.
  """
  # Create the input layer to our DNN
  network = latent_matrix

  # Add hidden layers with the given number of units/neurons per layer
  for units in params["dec_dnn_hidden_units"][::-1]:
    network = tf.layers.dense(
        inputs=network,
        units=units,
        activation=tf.nn.relu)

  output_matrix = tf.layers.dense(
      inputs=network,
      units=orig_dims,
      activation=tf.nn.relu)

  return output_matrix


def dense_autoencoder(X, orig_dims, params):
  """Dense model autoencoder using dense encoder and decoder networks.

  Given data matrix tensor X, the original dimensions of the input, and
  dictionary of parameters, process through dense model encoder and decoder
  subgraphs and return reconstructed inputs as output.

  Args:
    X: tf.float64 matrix tensor of input data.
    orig_dims: Original dimensions of input data.
    params: Dictionary of parameters.

  Returns:
    tf.float64 matrix tensor decoder output vector for each example in batch
    that is the reconstructed inputs.
  """
  latent_matrix = dense_encoder(X, params)
  output_matrix = dense_decoder(latent_matrix, orig_dims, params)

  return output_matrix


def dense_autoencoder_model(
    X, mode, params, cur_batch_size, dummy_var):
  """Dense autoencoder to reconstruct inputs and minimize reconstruction error.

  Given data matrix tensor X, the current Estimator mode, the dictionary of
  parameters, and the current batch size, process through dense model encoder
  and decoder subgraphs and return reconstructed inputs as output.

  Args:
    X: tf.float64 matrix tensor of input data.
    mode: Estimator ModeKeys. Can take values of TRAIN, EVAL, and PREDICT.
    params: Dictionary of parameters.
    cur_batch_size: Current batch size, could be partially filled.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: Reconstruction loss.
    train_op: Train operation so that Estimator can correctly add to dependency
      graph.
    X_time: 2D tensor representation of time major input data.
    X_time_recon: 2D tensor representation of time major input data.
    X_feat: 2D tensor representation of feature major input data.
    X_feat_recon: 2D tensor representation of feature major input data.
  """
  # Reshape into 2-D tensors
  # Time based
  # shape = (cur_batch_size * seq_len, num_feat)
  X_time = tf.reshape(
      tensor=X,
      shape=[cur_batch_size * params["seq_len"], params["num_feat"]])

  # shape = (cur_batch_size * seq_len, num_feat)
  X_time_recon = dense_autoencoder(X_time, params["num_feat"], params)

  # Features based
  # shape = (cur_batch_size, num_feat, seq_len)
  X_transposed = tf.transpose(a=X, perm=[0, 2, 1])

  # shape = (cur_batch_size * num_feat, seq_len)
  X_feat = tf.reshape(
      tensor=X_transposed,
      shape=[cur_batch_size * params["num_feat"], params["seq_len"]])

  # shape = (cur_batch_size * num_feat, seq_len)
  X_feat_recon = dense_autoencoder(X_feat, params["seq_len"], params)

  if (mode == tf.estimator.ModeKeys.TRAIN and
      params["training_mode"] == "reconstruction"):
    X_time_recon_3d = tf.reshape(
        tensor=X_time_recon,
        shape=[cur_batch_size, params["seq_len"], params["num_feat"]])
    X_feat_recon_3d = tf.transpose(
        a=tf.reshape(
            tensor=X_feat_recon,
            shape=[cur_batch_size, params["num_feat"], params["seq_len"]]),
        perm=[0, 2, 1])

    X_time_recon_3d_weighted = X_time_recon_3d * params["time_loss_weight"]
    X_feat_recon_3d_weighted = X_feat_recon_3d * params["feat_loss_weight"]

    predictions = (X_time_recon_3d_weighted + X_feat_recon_3d_weighted) \
      / (params["time_loss_weight"] + params["feat_loss_weight"])

    loss = tf.losses.mean_squared_error(labels=X, predictions=predictions)

    train_op = tf.contrib.layers.optimize_loss(
        loss=loss,
        global_step=tf.train.get_global_step(),
        learning_rate=params["learning_rate"],
        optimizer="Adam")

    return loss, train_op, None, None, None, None
  else:
    return None, None, X_time, X_time_recon, X_feat, X_feat_recon
