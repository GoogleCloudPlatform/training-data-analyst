import tensorflow as tf

from .calculate_error_distribution_statistics import non_singleton_batch_cov_variable_updating
from .calculate_error_distribution_statistics import singleton_batch_cov_variable_updating


# PCA model functions
def create_pca_vars(var_name, size):
  """Creates PCA variables.

  Given variable name and size, create and return PCA variables for count,
  mean, covariance, eigenvalues, eignvectors, and k principal components.

  Args:
    var_name: String denoting which set of variables to create. Values are
      "time" and "feat".
    size: The size of the variable, either sequence length or number of
      features.

  Returns:
    PCA variables for count, mean, covariance, eigenvalues,
    eigenvectors, and k principal components.
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

    k_pc_var = tf.get_variable(
        name="pca_{}_k_principal_components_var".format(var_name),
        dtype=tf.int64,
        initializer=tf.ones(shape=[], dtype=tf.int64),
        trainable=False)

  return count_var, mean_var, cov_var, eigval_var, eigvec_var, k_pc_var


def create_both_pca_vars(seq_len, num_feat):
  """Creates both time & feature major PCA variables.

  Given dimensions of inputs, create and return PCA variables for count,
  mean, covariance, eigenvalues, eigenvectors, and k principal components
  for both time and feature major representations.

  Args:
    seq_len: Number of timesteps in sequence.
    num_feat: Number of features.

  Returns:
    PCA variables for count, mean, covariance, eigenvalues,
    eigenvectors, and k principal components for both time and feature
    major representations.
  """
  # Time based
  (pca_time_count_var,
   pca_time_mean_var,
   pca_time_cov_var,
   pca_time_eigval_var,
   pca_time_eigvec_var,
   pca_time_k_pc_var) = create_pca_vars(
       var_name="time", size=num_feat)

  # Features based
  (pca_feat_count_var,
   pca_feat_mean_var,
   pca_feat_cov_var,
   pca_feat_eigval_var,
   pca_feat_eigvec_var,
   pca_feat_k_pc_var) = create_pca_vars(
       var_name="feat", size=seq_len)

  return (pca_time_count_var,
          pca_time_mean_var,
          pca_time_cov_var,
          pca_time_eigval_var,
          pca_time_eigvec_var,
          pca_time_k_pc_var,
          pca_feat_count_var,
          pca_feat_mean_var,
          pca_feat_cov_var,
          pca_feat_eigval_var,
          pca_feat_eigvec_var,
          pca_feat_k_pc_var)


def pca_reconstruction_k_pc(X_cen, pca_eigvec_var, k_pc):
  """PCA reconstruction with k principal components.

  Given centered data matrix tensor X, variables for the column means
  and eigenvectors, and the number of principal components, returns
  the reconstruction of X centered.

  Args:
    X_cen: tf.float64 matrix tensor of centered input data.
    pca_eigvec_var: tf.float64 matrix variable storing eigenvectors.
    k_pc: Number of principal components to keep.

  Returns:
    X_cen_recon: 2D input data tensor reconstructed.
  """
  # time_shape = (num_feat, num_feat)
  # feat_shape = (seq_len, seq_len)
  projection_matrix = tf.matmul(
      a=pca_eigvec_var[:, -k_pc:],
      b=pca_eigvec_var[:, -k_pc:],
      transpose_b=True)

  # time_shape = (cur_batch_size * seq_len, num_feat)
  # feat_shape = (cur_batch_size * num_feat, seq_len)
  X_cen_recon = tf.matmul(
      a=X_cen,
      b=projection_matrix)

  return X_cen_recon


def pca_reconstruction_k_pc_mse(X_cen, pca_eigvec_var, k_pc):
  """PCA reconstruction with k principal components.

  Given centered data matrix tensor X, variables for the column means
  and eigenvectors, and the number of principal components, returns
  reconstruction MSE.

  Args:
    X_cen: tf.float64 matrix tensor of centered input data.
    pca_eigvec_var: tf.float64 matrix variable storing eigenvectors.
    k_pc: Number of principal components to keep.

  Returns:
    mse: Reconstruction mean squared error.
  """
  # time_shape = (cur_batch_size * seq_len, num_feat)
  # feat_shape = (cur_batch_size * num_feat, seq_len)
  X_cen_recon = pca_reconstruction_k_pc(
      X_cen, pca_eigvec_var, k_pc)

  # time_shape = (cur_batch_size * seq_len, num_feat)
  # feat_shape = (cur_batch_size * num_feat, seq_len)
  error = X_cen - X_cen_recon

  # shape = ()
  mse = tf.reduce_mean(
      input_tensor=tf.reduce_sum(
          input_tensor=tf.square(x=error), axis=-1))

  return mse


def find_best_k_principal_components(X_recon_mse, pca_k_pc_var):
  """Find best k principal components from reconstruction MSE.

  Given reconstruction MSE, return number of principal components
  with lowest MSE in varible.

  Args:
    X_recon_mse: tf.float64 vector tensor of reconstruction mean
      squared error.
    pca_k_pc_var: tf.int64 scalar variable to hold best number of
      principal components.

  Returns:
    pca_k_pc_var: Updated scalar variable now with best number of
      principal components.
  """
  best_pca_k_pc = tf.argmin(input=X_recon_mse) + 1

  with tf.control_dependencies(
      control_inputs=[tf.assign(ref=pca_k_pc_var,
                                value=best_pca_k_pc)]):

    return tf.identity(input=pca_k_pc_var)


def set_k_principal_components(user_k_pc, pca_k_pc_var):
  """Set k principal components from user-defined value.

  Given user-defined number of principal components, return
  variable set to this value.

  Args:
    user_k_pc: User-defined python integer for number of principal
      components.
    pca_k_pc_var: tf.int64 scalar variable to hold chosen number of
      principal components.

  Returns:
    pca_k_pc_var: Updated scalar variable now with chosen number of
      principal components.
  """
  with tf.control_dependencies(
      control_inputs=[tf.assign(ref=pca_k_pc_var,
                                value=user_k_pc)]):

    return tf.identity(input=pca_k_pc_var)


def pca_model(X, mode, params, cur_batch_size, dummy_var):
  """PCA to reconstruct inputs and minimize reconstruction error.

  Given data matrix tensor X, the current Estimator mode, the dictionary of
  parameters, current batch size, and the number of features, process through
  PCA model subgraph and return reconstructed inputs as output.

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

  # Features based
  # shape = (cur_batch_size, num_feat, seq_len)
  X_transposed = tf.transpose(a=X, perm=[0, 2, 1])

  # shape = (cur_batch_size * num_feat, seq_len)
  X_feat = tf.reshape(
      tensor=X_transposed,
      shape=[cur_batch_size * params["num_feat"], params["seq_len"]])

  ##############################################################################

  # Variables for calculating error distribution statistics
  (pca_time_count_var,
   pca_time_mean_var,
   pca_time_cov_var,
   pca_time_eigval_var,
   pca_time_eigvec_var,
   pca_time_k_pc_var,
   pca_feat_count_var,
   pca_feat_mean_var,
   pca_feat_cov_var,
   pca_feat_eigval_var,
   pca_feat_eigvec_var,
   pca_feat_k_pc_var) = create_both_pca_vars(
      params["seq_len"], params["num_feat"])

  # 3. Loss function, training/eval ops
  if (mode == tf.estimator.ModeKeys.TRAIN and
      params["training_mode"] == "reconstruction"):
    if not params["autotune_principal_components"]:
      with tf.variable_scope(name_or_scope="pca_vars", reuse=tf.AUTO_REUSE):
        # Check if batch is a singleton, very important for covariance math

        # Time based
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

        if params["k_principal_components_time"] is not None:
          pca_time_k_pc = set_k_principal_components(
              params["k_principal_components_time"], pca_time_k_pc_var)
        else:
          pca_time_k_pc = tf.zeros(shape=(), dtype=tf.float64)

        # Features based
        # shape = ()
        singleton_features_condition = tf.equal(
            x=cur_batch_size * params["num_feat"], y=1)

        pca_feat_cov_var, pca_feat_mean_var, pca_feat_count_var = tf.cond(
            pred=singleton_features_condition,
            true_fn=lambda: singleton_batch_cov_variable_updating(
                params["num_feat"],
                X_feat,
                pca_feat_count_var, pca_feat_mean_var,
                pca_feat_cov_var),
            false_fn=lambda: non_singleton_batch_cov_variable_updating(
                cur_batch_size,
                params["num_feat"],
                X_feat,
                pca_feat_count_var,
                pca_feat_mean_var,
                pca_feat_cov_var))

        # shape = (seq_len,) & (seq_len, seq_len)
        pca_feat_eigval_tensor, pca_feat_eigvec_tensor = tf.linalg.eigh(
            tensor=pca_feat_cov_var)

        if params["k_principal_components_feat"] is not None:
          pca_feat_k_pc = set_k_principal_components(
              params["k_principal_components_feat"], pca_feat_k_pc_var)
        else:
          pca_feat_k_pc = tf.zeros(shape=(), dtype=tf.float64)

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
                                          value=pca_feat_eigvec_tensor),
                                pca_time_k_pc,
                                pca_feat_k_pc]):


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
      if params["k_principal_components_time"] is None:
        # shape = (cur_batch_size * seq_len, num_feat)
        X_time_cen = X_time - pca_time_mean_var

        # shape = (num_feat - 1,)
        X_time_recon_mse = tf.map_fn(
            fn=lambda x: pca_reconstruction_k_pc_mse(
                X_time_cen, pca_time_eigvec_var, x),
            elems=tf.range(start=1,
                           limit=params["num_feat"],
                           dtype=tf.int64),
            dtype=tf.float64)

        pca_time_k_pc = find_best_k_principal_components(
            X_time_recon_mse, pca_time_k_pc_var)
      else:
        pca_time_k_pc = set_k_principal_components(
            params["k_principal_components_time"], pca_time_k_pc_var)

      if params["k_principal_components_feat"] is None:
        # Features based
        # shape = (cur_batch_size * num_feat, seq_len)
        X_feat_cen = X_feat - pca_feat_mean_var

        # shape = (seq_len - 1,)
        X_feat_recon_mse = tf.map_fn(
            fn=lambda x: pca_reconstruction_k_pc_mse(
                X_feat_cen, pca_feat_eigvec_var, x),
            elems=tf.range(start=1,
                           limit=params["seq_len"],
                           dtype=tf.int64),
            dtype=tf.float64)

        pca_feat_k_pc = find_best_k_principal_components(
            X_feat_recon_mse, pca_feat_k_pc_var)
      else:
        pca_feat_k_pc = set_k_principal_components(
            params["k_principal_components_feat"], pca_feat_k_pc_var)

      with tf.control_dependencies(
          control_inputs=[pca_time_k_pc, pca_feat_k_pc]):
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
    X_time_cen = X_time - pca_time_mean_var

    # shape = (cur_batch_size * seq_len, num_feat)
    if params["k_principal_components_time"] is None:
      X_time_recon = pca_reconstruction_k_pc(
          X_time_cen,
          pca_time_eigvec_var,
          pca_time_k_pc_var)
    else:
      X_time_recon = pca_reconstruction_k_pc(
          X_time_cen,
          pca_time_eigvec_var,
          params["k_principal_components_time"])

    # Features based
    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat_cen = X_feat - pca_feat_mean_var

    # shape = (cur_batch_size * num_feat, seq_len)
    if params["k_principal_components_feat"] is None:
      X_feat_recon = pca_reconstruction_k_pc(
          X_feat_cen,
          pca_feat_eigvec_var,
          pca_feat_k_pc_var)
    else:
      X_feat_recon = pca_reconstruction_k_pc(
          X_feat_cen,
          pca_feat_eigvec_var,
          params["k_principal_components_feat"])

    return None, None, X_time_cen, X_time_recon, X_feat_cen, X_feat_recon
