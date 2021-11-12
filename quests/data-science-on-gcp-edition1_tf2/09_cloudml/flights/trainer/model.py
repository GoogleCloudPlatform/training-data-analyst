import logging
import os
import time
import hypertune
import tensorflow as tf
import numpy as np

CSV_COLUMNS  = ('ontime,dep_delay,taxiout,distance,avg_dep_delay,avg_arr_delay' + \
                ',carrier,dep_lat,dep_lon,arr_lat,arr_lon,origin,dest').split(',')
LABEL_COLUMN = 'ontime'
DEFAULTS     = [[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],\
                ['na'],[0.0],[0.0],[0.0],[0.0],['na'],['na']]

BUCKET = None
OUTPUT_DIR = None
NBUCKETS = None
NUM_EXAMPLES = None
TRAIN_BATCH_SIZE = None
TRAIN_DATA_PATTERN = None
EVAL_DATA_PATTERN = None
DNN_HIDDEN_UNITS = [64, 32]

def setup(args):
    global BUCKET, OUTPUT_DIR, NBUCKETS, NUM_EXAMPLES
    global TRAIN_BATCH_SIZE, TRAIN_DATA_PATTERN, EVAL_DATA_PATTERN
    global DNN_HIDDEN_UNITS
    
    BUCKET = args['bucket']
    OUTPUT_DIR = args['output_dir']
    NBUCKETS = int(args['nbuckets'])
    NUM_EXAMPLES = int(args['num_examples'])
    TRAIN_BATCH_SIZE = int(args['train_batch_size'])
    DNN_HIDDEN_UNITS = args['dnn_hidden_units'].split(',')

    # set up training and evaluation data patterns
    DATA_BUCKET = "gs://{}/flights/chapter8/output/".format(BUCKET)
    TRAIN_DATA_PATTERN = DATA_BUCKET + "train*"
    EVAL_DATA_PATTERN = DATA_BUCKET + "test*"
    logging.info('Training based on data in {}'.format(TRAIN_DATA_PATTERN))
    
def features_and_labels(features):
  label = features.pop('ontime') # this is what we will train for
  return features, label

def read_dataset(pattern, batch_size, mode=tf.estimator.ModeKeys.TRAIN, truncate=None):
  dataset = tf.data.experimental.make_csv_dataset(pattern, batch_size, CSV_COLUMNS, DEFAULTS)
  dataset = dataset.map(features_and_labels)
  if mode == tf.estimator.ModeKeys.TRAIN:
    dataset = dataset.repeat()
    dataset = dataset.shuffle(batch_size*10)
  dataset = dataset.prefetch(1)
  if truncate is not None:
    dataset = dataset.take(truncate)
  return dataset

def read_lines():
    if TRAIN_BATCH_SIZE > 5:
        print('This is meant for trying out the input pipeline. Please set train_batch_size to be < 5')
        return
    
    logging.info("Checking input pipeline batch_size={}".format(TRAIN_BATCH_SIZE))
    one_item = read_dataset(TRAIN_DATA_PATTERN, TRAIN_BATCH_SIZE, truncate=1)
    print(list(one_item)) # should print one batch of items
    
def find_average_label():
    logging.info("Finding average label in num_examples={}".format(NUM_EXAMPLES))
    features_and_labels = read_dataset(TRAIN_DATA_PATTERN, 1, truncate=NUM_EXAMPLES)
    labels = features_and_labels.map(lambda x, y : y)
    count, sum = labels.reduce((0.0,0.0), lambda state, y: (state[0]+1.0, state[1]+y))
    print(sum/count) # average of the whole lot


def get_inputs_and_features(with_engineered_features):
    real = {
        colname : tf.feature_column.numeric_column(colname) 
          for colname in 
            ('dep_delay,taxiout,distance,avg_dep_delay,avg_arr_delay' +
             ',dep_lat,dep_lon,arr_lat,arr_lon').split(',')
    }
    sparse = {
      'carrier': tf.feature_column.categorical_column_with_vocabulary_list(
          'carrier',
          vocabulary_list='AS,VX,F9,UA,US,WN,HA,EV,MQ,DL,OO,B6,NK,AA'.split(',')),
      'origin' : tf.feature_column.categorical_column_with_hash_bucket(
          'origin', hash_bucket_size=1000), # FIXME
      'dest'   : tf.feature_column.categorical_column_with_hash_bucket(
          'dest', hash_bucket_size=1000) # FIXME
    }
    
    inputs = {
        colname : tf.keras.layers.Input(
            name=colname, shape=(), dtype='float32') 
          for colname in real.keys()
    }
    inputs.update({
        colname : tf.keras.layers.Input(
            name=colname, shape=(), dtype='string') 
          for colname in sparse.keys()
    })
    
    if with_engineered_features:
        logging.info("Adding engineered features to the model input")
        latbuckets = np.linspace(20.0, 50.0, NBUCKETS).tolist()  # USA
        lonbuckets = np.linspace(-120.0, -70.0, NBUCKETS).tolist() # USA
        disc = {}
        disc.update({
           'd_{}'.format(key) : tf.feature_column.bucketized_column(real[key], latbuckets) 
              for key in ['dep_lat', 'arr_lat']
        })
        disc.update({
           'd_{}'.format(key) : tf.feature_column.bucketized_column(real[key], lonbuckets) 
              for key in ['dep_lon', 'arr_lon']
        })

        # cross columns that make sense in combination
        sparse['dep_loc'] = tf.feature_column.crossed_column([disc['d_dep_lat'], disc['d_dep_lon']], NBUCKETS*NBUCKETS)
        sparse['arr_loc'] = tf.feature_column.crossed_column([disc['d_arr_lat'], disc['d_arr_lon']], NBUCKETS*NBUCKETS)
        sparse['dep_arr'] = tf.feature_column.crossed_column([sparse['dep_loc'], sparse['arr_loc']], NBUCKETS ** 4)
        #sparse['ori_dest'] = tf.feature_column.crossed_column(['origin', 'dest'], hash_bucket_size=1000)

        # embed all the sparse columns
        embed = {
           'embed_{}'.format(colname) : tf.feature_column.embedding_column(col, 10)
              for colname, col in sparse.items()
        }
        real.update(embed)
    #else:
    #    sparse = {}
    
    return inputs, real, sparse

def wide_and_deep_classifier(inputs,
                             linear_feature_columns,
                             dnn_feature_columns,
                             dnn_hidden_units):
    deep = tf.keras.layers.DenseFeatures(
        dnn_feature_columns, name='deep_inputs')(inputs)
    layers = [int(x) for x in dnn_hidden_units]
    for layerno, numnodes in enumerate(layers):
        deep = tf.keras.layers.Dense(numnodes, activation='relu', name='dnn_{}'.format(layerno+1))(deep)        
    wide = tf.keras.layers.DenseFeatures(linear_feature_columns, name='wide_inputs')(inputs)
    both = tf.keras.layers.concatenate([deep, wide], name='both')
    output = tf.keras.layers.Dense(1, activation='sigmoid', name='pred')(both)
    model = tf.keras.Model(inputs, output)
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy', rmse])
    return model

def rmse(y_true, y_pred):
    return tf.sqrt(tf.reduce_mean(tf.square(y_pred - y_true))) 

def linear_classifier(inputs,
                      sparse,
                      real):
    both = tf.keras.layers.DenseFeatures(
        list(sparse) + list(real), name='features')(inputs)
    output = tf.keras.layers.Dense(
        1, activation='sigmoid', name='pred')(both)
    model = tf.keras.Model(inputs, output)
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy', rmse])
    return model

def train_and_evaluate(model_type = 'linear'):
    # create inputs and feature columns
    use_engineered_features = (model_type != 'linear')
    inputs, real, sparse = get_inputs_and_features(use_engineered_features)
    
    # one-hot encode the sparse columns
    sparse = {
        colname : tf.feature_column.indicator_column(col)
          for colname, col in sparse.items()
    }
    
    # create model
    model = None
    if model_type == 'linear':
        model = linear_classifier(inputs,
                                  sparse.values(),
                                  real.values())
    else:
        model = wide_and_deep_classifier(inputs, 
                                         sparse.values(),
                                         real.values(),
                                         DNN_HIDDEN_UNITS)
    
    # train and evaluate
    train_batch_size = TRAIN_BATCH_SIZE

    if NUM_EXAMPLES < 10000: # partial data
        print("Develop mode")
        eval_batch_size = 100
        steps_per_epoch = 3
        epochs = 2
        num_eval_examples = 5*eval_batch_size
    else:
        print("Full dataset mode")
        eval_batch_size = 10000
        steps_per_epoch = NUM_EXAMPLES // train_batch_size
        epochs = 10
        num_eval_examples = None

    train_dataset = read_dataset(TRAIN_DATA_PATTERN, train_batch_size)
    eval_dataset = read_dataset(EVAL_DATA_PATTERN, eval_batch_size,
                                tf.estimator.ModeKeys.EVAL,
                                num_eval_examples)

    checkpoint_path = os.path.join(OUTPUT_DIR,
                                   'checkpoints/flights.cpt')
    cp_callback = tf.keras.callbacks.ModelCheckpoint(
        checkpoint_path, save_weights_only=True, verbose=1)

    history = model.fit(train_dataset, 
                        validation_data=eval_dataset,
                        epochs=epochs, 
                        steps_per_epoch=steps_per_epoch,
                        validation_steps=10,
                        callbacks=[cp_callback])
    
    # export
    export_dir = os.path.join(OUTPUT_DIR,
                              'export/flights_{}'.format(
                                  time.strftime("%Y%m%d-%H%M%S")))
    print('Exporting to {}'.format(export_dir))
    tf.saved_model.save(model, export_dir)
    
    # write out final metric
    final_rmse = history.history['val_rmse'][-1]
    print("Final RMSE = {}".format(final_rmse))
    hpt = hypertune.HyperTune()
    hpt.report_hyperparameter_tuning_metric(
       hyperparameter_metric_tag='rmse',
       metric_value=final_rmse,
       global_step=1) 
