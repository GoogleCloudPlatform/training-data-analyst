import shutil, os, datetime
import numpy as np
import tensorflow as tf

BUCKET = None  # set from task.py
PATTERN = 'of' # gets all files

# Determine CSV, label, and key columns
CSV_COLUMNS = 'weight_pounds,is_male,mother_age,plurality,gestation_weeks,key'.split(',')
LABEL_COLUMN = 'weight_pounds'
KEY_COLUMN = 'key'

# Set default values for each CSV column
DEFAULTS = [[0.0], ['null'], [0.0], ['null'], [0.0], ['nokey']]

# Define some hyperparameters
TRAIN_EXAMPLES = 1000 * 1000
EVAL_STEPS = None
NUM_EVALS = 10
BATCH_SIZE = 512
NEMBEDS = 3
NNSIZE = [64, 16, 4]

# Create an input function reading a file using the Dataset API
def features_and_labels(row_data):
    for unwanted_col in ['key']:
        row_data.pop(unwanted_col)
    label = row_data.pop(LABEL_COLUMN)
    return row_data, label  # features, label

# load the training data
def load_dataset(pattern, batch_size=1, mode=tf.estimator.ModeKeys.EVAL):
  dataset = (tf.data.experimental.make_csv_dataset(pattern, batch_size, CSV_COLUMNS, DEFAULTS)
             .map(features_and_labels) # features, label
             )
  if mode == tf.estimator.ModeKeys.TRAIN:
        dataset = dataset.shuffle(1000).repeat()
  dataset = dataset.prefetch(1) # take advantage of multi-threading; 1=AUTOTUNE
  return dataset

## Build a Keras wide-and-deep model using its Functional API
def rmse(y_true, y_pred):
    return tf.sqrt(tf.reduce_mean(tf.square(y_pred - y_true))) 

# Helper function to handle categorical columns
def categorical_fc(name, values):
    orig = tf.feature_column.categorical_column_with_vocabulary_list(name, values)
    wrapped = tf.feature_column.indicator_column(orig)
    return orig, wrapped

def build_wd_model(dnn_hidden_units = [64, 32], nembeds = 3):
    # input layer
    deep_inputs = {
        colname : tf.keras.layers.Input(name=colname, shape=(), dtype='float32')
           for colname in ['mother_age', 'gestation_weeks']
    }
    wide_inputs = {
        colname : tf.keras.layers.Input(name=colname, shape=(), dtype='string')
           for colname in ['is_male', 'plurality']        
    }
    inputs = {**wide_inputs, **deep_inputs}
    
    # feature columns from inputs
    deep_fc = {
        colname : tf.feature_column.numeric_column(colname)
           for colname in ['mother_age', 'gestation_weeks']
    }
    wide_fc = {}
    is_male, wide_fc['is_male'] = categorical_fc('is_male', ['True', 'False', 'Unknown'])
    plurality, wide_fc['plurality'] = categorical_fc('plurality',
                      ['Single(1)', 'Twins(2)', 'Triplets(3)',
                       'Quadruplets(4)', 'Quintuplets(5)','Multiple(2+)'])
    
    # bucketize the float fields. This makes them wide
    age_buckets = tf.feature_column.bucketized_column(deep_fc['mother_age'],
                                                     boundaries=np.arange(15,45,1).tolist())
    wide_fc['age_buckets'] = tf.feature_column.indicator_column(age_buckets)
    gestation_buckets = tf.feature_column.bucketized_column(deep_fc['gestation_weeks'],
                                                     boundaries=np.arange(17,47,1).tolist())
    wide_fc['gestation_buckets'] = tf.feature_column.indicator_column(gestation_buckets)
    
    # cross all the wide columns. We have to do the crossing before we one-hot encode
    crossed = tf.feature_column.crossed_column(
        [is_male, plurality, age_buckets, gestation_buckets], hash_bucket_size=20000)
    deep_fc['crossed_embeds'] = tf.feature_column.embedding_column(crossed, nembeds)

    # the constructor for DenseFeatures takes a list of numeric columns
    # The Functional API in Keras requires that you specify: LayerConstructor()(inputs)
    wide_inputs = tf.keras.layers.DenseFeatures(wide_fc.values(), name='wide_inputs')(inputs)
    deep_inputs = tf.keras.layers.DenseFeatures(deep_fc.values(), name='deep_inputs')(inputs)
        
    # hidden layers for the deep side
    layers = [int(x) for x in dnn_hidden_units]
    deep = deep_inputs
    for layerno, numnodes in enumerate(layers):
        deep = tf.keras.layers.Dense(numnodes, activation='relu', name='dnn_{}'.format(layerno+1))(deep)        
    deep_out = deep
    
    # linear model for the wide side
    wide_out = tf.keras.layers.Dense(10, activation='relu', name='linear')(wide_inputs)
   
    # concatenate the two sides
    both = tf.keras.layers.concatenate([deep_out, wide_out], name='both')

    # final output is a linear activation because this is regression
    output = tf.keras.layers.Dense(1, activation='linear', name='weight')(both)
    model = tf.keras.models.Model(inputs, output)
    model.compile(optimizer='adam', loss='mse', metrics=[rmse, 'mse'])
    return model



# The main function
def train_and_evaluate(output_dir):
    model = build_wd_model(NNSIZE, NEMBEDS)
    print("Here is our Wide-and-Deep architecture so far:\n")
    print(model.summary())

    train_file_path = 'gs://{}/babyweight/preproc/{}*{}*'.format(BUCKET, 'train', PATTERN)
    eval_file_path = 'gs://{}/babyweight/preproc/{}*{}*'.format(BUCKET, 'eval', PATTERN)
    trainds = load_dataset('train*', BATCH_SIZE, tf.estimator.ModeKeys.TRAIN)
    evalds = load_dataset('eval*', 1000, tf.estimator.ModeKeys.EVAL)
    if EVAL_STEPS:
        evalds = evalds.take(EVAL_STEPS)
    steps_per_epoch = TRAIN_EXAMPLES // (BATCH_SIZE * NUM_EVALS)
    
    checkpoint_path = os.path.join(output_dir, 'checkpoints/babyweight')
    cp_callback = tf.keras.callbacks.ModelCheckpoint(checkpoint_path, save_weights_only=True, verbose=1)
    
    history = model.fit(trainds, 
                        validation_data=evalds,
                        epochs=NUM_EVALS, 
                        steps_per_epoch=steps_per_epoch,
                        verbose=2, # 0=silent, 1=progress bar, 2=one line per epoch
                        callbacks=[cp_callback])
    
    EXPORT_PATH = os.path.join(output_dir, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    tf.saved_model.save(model, EXPORT_PATH) # with default serving function
    print("Exported trained model to {}".format(EXPORT_PATH))
