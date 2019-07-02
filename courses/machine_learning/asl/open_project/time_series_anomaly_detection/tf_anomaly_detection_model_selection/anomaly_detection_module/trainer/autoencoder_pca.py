import tensorflow as tf


# PCA model functions
def create_pca_vars(var_name, size):
  """Creates PCA variables.

  Given variable name and size, create and return PCA variables for count,
  mean, covariance, eigenvalues, and eignvectors.

  Args:
    var_name: String denoting which set of variables to create. Values are
      "time" and "feat".
    size: The size of the variable, either sequence length or number of
      features.

  Returns:
    PCA variables for count, mean, covariance, eigenvalues, and
    eigenvectors.
  """
  with tf.variable_scope(
      name_or_scope="pca_vars", reuse=tf.AUTO_REUSE):
    count_var = tf.get_variable(
        name="pca_{}_count_var".format(var_name),
        dtype=tf.int64,
        initializer=tf.zeros(shape=[], dtype=tf.int64),
        trainable=False)

    mean_var = tf.get_variable(
        name="pca_{}_mean_var".format(var_name),
        dtype=tf.float64,
        initializer=tf.zeros(shape=[size], dtype=tf.float64),
        trainable=False)

    cov_var = tf.get_variable(
        name="pca_{}_cov_var".format(var_name),
        dtype=tf.float64,
        initializer=tf.zeros(shape=[size, size], dtype=tf.float64),
        trainable=False)

    eigval_var = tf.get_variable(
        name="pca_{}_eigval_var".format(var_name),
        dtype=tf.float64,
        initializer=tf.zeros(shape=[size], dtype=tf.float64),
        trainable=False)

    eigvec_var = tf.get_variable(
        name="pca_{}_eigvec_var".format(var_name),
        dtype=tf.float64,
        initializer=tf.zeros(shape=[size, size], dtype=tf.float64),
        trainable=False)

  return count_var, mean_var, cov_var, eigval_var, eigvec_var


def create_both_pca_vars(seq_len, num_feat):
  """Creates both time & feature major PCA variables.

  Given dimensions of inputs, create and return PCA variables for count,
  mean, covariance, eigenvalues, and eigenvectors for both time and
  feature major representations.

  Args:
    seq_len: Number of timesteps in sequence.
    num_feat: Number of features.

  Returns:
    PCA variables for count, mean, covariance, eigenvalues, and
    eigenvectors for both time and feature major representations.
  """
  # Time based
  (pca_time_count_var,
   pca_time_mean_var,
   pca_time_cov_var,
   pca_time_eigval_var,
   pca_time_eigvec_var) = create_pca_vars(
       var_name="time", size=num_feat)

  # Features based
  (pca_feat_count_var,
   pca_feat_mean_var,
   pca_feat_cov_var,
   pca_feat_eigval_var,
   pca_feat_eigvec_var) = create_pca_vars(
       var_name="feat", size=seq_len)

  return (pca_time_count_var,
          pca_time_mean_var,
          pca_time_cov_var,
          pca_time_eigval_var,
          pca_time_eigvec_var,
          pca_feat_count_var,
          pca_feat_mean_var,
          pca_feat_cov_var,
          pca_feat_eigval_var,
          pca_feat_eigvec_var)

def pca_model(X, mode, params, cur_batch_size, num_feat, dummy_var):
  """PCA to reconstruct inputs and minimize reconstruction error.

  Given data matrix tensor X, the current Estimator mode, the dictionary of
  parameters, current batch size, and the number of features, process through
  PCA model subgraph and return reconstructed inputs as output.

  Args:
    X: tf.float64 matrix tensor of input data.
    mode: Estimator ModeKeys. Can take values of TRAIN, EVAL, and PREDICT.
    params: Dictionary of parameters.
    cur_batch_size: Current batch size, could be partially filled.
    num_feat: Number of features.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: Reconstruction loss.
    train_op: Train operation so that Estimator can correctly add to dependency
      graph.
    X_time: 2D tensor representation of time major input data.
    X_time_recon: 3D tensor representation of time major input data.
    X_feat: 2D tensor representation of feature major input data.
    X_feat_recon: 3D tensor representation of feature major input data.
  """
  # Reshape into 2-D tensors
  # Time based
  # shape = (cur_batch_size * seq_len, num_feat)
  X_time = tf.reshape(
      tensor=X,
      shape=[cur_batch_size * params["seq_len"], num_feat])

  # Features based
  # shape = (cur_batch_size, num_feat, seq_len)
  X_transposed = tf.transpose(a=X, perm=[0, 2, 1])

  # shape = (cur_batch_size * num_feat, seq_len)
  X_feat = tf.reshape(
      tensor=X_transposed,
      shape=[cur_batch_size * num_feat, params["seq_len"]])

  ##############################################################################

  # Variables for calculating error distribution statistics
  (pca_time_count_var,
   pca_time_mean_var,
   pca_time_cov_var,
   pca_time_eigval_var,
   pca_time_eigvec_var,
   pca_feat_count_var,
   pca_feat_mean_var,
   pca_feat_cov_var,
   pca_feat_eigval_var,
   pca_feat_eigvec_var) = create_both_pca_vars(params["seq_len"], num_feat)

  # 3. Loss function, training/eval ops
  if (mode == tf.estimator.ModeKeys.TRAIN and
      params["training_mode"] == "reconstruction"):
    with tf.variable_scope(name_or_scope="pca_vars", reuse=tf.AUTO_REUSE):
      # Check if batch is a singleton or not, very important for covariance math

      # Time based ########################################
      # shape = ()
      singleton_condition = tf.equal(
          x=cur_batch_size * params["seq_len"], y=1)

      pca_time_cov_var, pca_time_mean_var, pca_time_count_var = tf.cond(
          pred=singleton_condition,
          true_fn=lambda: singleton_batch_cov_variable_updating(
              params["seq_len"],
              X_time,
              pca_time_count_var,
              pca_time_mean_var,
              pca_time_cov_var),
          false_fn=lambda: non_singleton_batch_cov_variable_updating(
              cur_batch_size,
              params["seq_len"],
              X_time,
              pca_time_count_var,
              pca_time_mean_var,
              pca_time_cov_var))

      # shape = (num_feat,) & (num_feat, num_feat)
      pca_time_eigval_tensor, pca_time_eigvec_tensor = tf.linalg.eigh(
          tensor=pca_time_cov_var)

      # Features based ########################################
      # shape = ()
      singleton_features_condition = tf.equal(
          x=cur_batch_size * num_feat, y=1)

      pca_feat_cov_var, pca_feat_mean_var, pca_feat_count_var = tf.cond(
          pred=singleton_features_condition,
          true_fn=lambda: singleton_batch_cov_variable_updating(
              num_feat,
              X_feat,
              pca_feat_count_var, pca_feat_mean_var,
              pca_feat_cov_var),
          false_fn=lambda: non_singleton_batch_cov_variable_updating(
              cur_batch_size,
              num_feat,
              X_feat,
              pca_feat_count_var,
              pca_feat_mean_var,
              pca_feat_cov_var))

      # shape = (seq_len,) & (seq_len, seq_len)
      pca_feat_eigval_tensor, pca_feat_eigvec_tensor = tf.linalg.eigh(
          tensor=pca_feat_cov_var)

    # Lastly use control dependencies around loss to enforce the mahalanobis
    # variables to be assigned, the control order matters, hence the separate
    # contexts
    with tf.control_dependencies(
        control_inputs=[pca_time_cov_var, pca_feat_cov_var]):
      with tf.control_dependencies(
          control_inputs=[pca_time_mean_var, pca_feat_mean_var]):
        with tf.control_dependencies(
            control_inputs=[pca_time_count_var, pca_feat_count_var]):
          with tf.control_dependencies(
              control_inputs=[tf.assign(ref=pca_time_eigval_var,
                                        value=pca_time_eigval_tensor),
                              tf.assign(ref=pca_time_eigvec_var,
                                        value=pca_time_eigvec_tensor),
                              tf.assign(ref=pca_feat_eigval_var,
                                        value=pca_feat_eigval_tensor),
                              tf.assign(ref=pca_feat_eigvec_var,
                                        value=pca_feat_eigvec_tensor)]):
            loss = tf.reduce_sum(
                input_tensor=tf.zeros(
                    shape=(), dtype=tf.float64) * dummy_var)

            train_op = tf.contrib.layers.optimize_loss(
                loss=loss,
                global_step=tf.train.get_global_step(),
                learning_rate=params["learning_rate"],
                optimizer="SGD")

            return loss, train_op, None, None, None, None
  else:
    # Time based
    # shape = (cur_batch_size * seq_len, num_feat)
    X_time = X_time - pca_time_mean_var

    # shape = (cur_batch_size * seq_len, params["k_principal_components"])
    X_time_projected = tf.matmul(
        a=X_time,
        b=pca_time_eigvec_var[:, -params["k_principal_components"]:])

    # shape = (cur_batch_size * seq_len, num_feat)
    X_time_recon = tf.matmul(
        a=X_time_projected,
        b=pca_time_eigvec_var[:, -params["k_principal_components"]:],
        transpose_b=True)

    # Features based
    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat = X_feat - pca_feat_mean_var

    # shape = (cur_batch_size * num_feat, params["k_principal_components"])
    X_feat_projected = tf.matmul(
        a=X_feat,
        b=pca_feat_eigvec_var[:, -params["k_principal_components"]:])

    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat_recon = tf.matmul(
        a=X_feat_projected,
        b=pca_feat_eigvec_var[:, -params["k_principal_components"]:],
        transpose_b=True)

    return None, None, X_time, X_time_recon, X_feat, X_feat_recon
