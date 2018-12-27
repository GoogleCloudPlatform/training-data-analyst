import tensorflow as tf
import shutil
print(tf.__version__)

#1. Train and Evaluate Input Functions
CSV_COLUMN_NAMES = ['fare_amount', 'pickuplon','pickuplat','dropofflon','dropofflat','passengers', 'key']
CSV_DEFAULTS = [[0.0], [-74.0], [40.0], [-74.0], [40.7], [1.0], ['nokey']]

def read_dataset(csv_path):
    def _parse_row(row):
        # Decode the CSV row into list of TF tensors
        fields = tf.decode_csv(row, record_defaults=CSV_DEFAULTS)

        # Pack the result into a dictionary
        features = dict(zip(CSV_COLUMN_NAMES, fields))
        features.pop('key') # discard, not a real feature
        
        # Separate the label from the features
        label = features.pop('fare_amount') # remove label from features and store

        return features, label
    
    # Create a dataset containing the text lines.
    dataset = tf.data.TextLineDataset(csv_path)

    # Parse each CSV row into correct (features,label) format for Estimator API
    dataset = dataset.map(_parse_row)
    
    return dataset

def train_input_fn(csv_path, batch_size=128):
    #1. Convert CSV into tf.data.Dataset  with (features,label) format
    dataset = read_dataset(csv_path)
      
    #2. Shuffle, repeat, and batch the examples.
    dataset = dataset.shuffle(1000).repeat().batch(batch_size)
   
    return dataset

def eval_input_fn(csv_path, batch_size=128):
    #1. Convert CSV into tf.data.Dataset  with (features,label) format
    dataset = read_dataset(csv_path)

    #2.Batch the examples.
    dataset = dataset.batch(batch_size)
   
    return dataset
  
#2. Feature Columns
FEATURE_NAMES = CSV_COLUMN_NAMES[1:len(CSV_COLUMN_NAMES) - 1] # all but first and last columns

feature_cols = [tf.feature_column.numeric_column(k) for k in FEATURE_NAMES]

#3. Serving Input Receiver Function
def serving_input_receiver_fn():
    receiver_tensors = {
        'pickuplon' : tf.placeholder(tf.float32, shape=[None]), # shape is vector to allow batch of requests
        'pickuplat' : tf.placeholder(tf.float32, shape=[None]),
        'dropofflat' : tf.placeholder(tf.float32, shape=[None]),
        'dropofflon' : tf.placeholder(tf.float32, shape=[None]),
        'passengers' : tf.placeholder(tf.float32, shape=[None]),
    }
    # Note:
    # You would transform data here from the reiever format to the format expected
    # by your model, although in this case no transformation is needed.
    
    features = receiver_tensors # 'features' is what is passed on to the model
    return tf.estimator.export.ServingInputReceiver(features, receiver_tensors)
  
#4. Train and Evaluate
def train_and_evaluate(params):
  OUTDIR = params['output_dir']

  model = tf.estimator.LinearRegressor(
      feature_columns=feature_cols,
      model_dir = OUTDIR,
      config = tf.estimator.RunConfig(
          tf_random_seed=1, # for reproducibility
          save_checkpoints_steps=max(10,params['train_steps']//10) # checkpoint every N steps
      ) 
  )

  train_spec=tf.estimator.TrainSpec(
                     input_fn = lambda:train_input_fn(params['train_data_path']),
                     max_steps = params['train_steps'])

  exporter = tf.estimator.FinalExporter('exporter', serving_input_receiver_fn) # export SavedModel once at the end of training
  # Note: alternatively use tf.estimator.BestExporter to export at every checkpoint that has lower loss than the previous checkpoint


  eval_spec=tf.estimator.EvalSpec(
                     input_fn=lambda:eval_input_fn(params['eval_data_path']),
                     steps = None,
                     start_delay_secs=1, # wait at least N seconds before first evaluation (default 120)
                     throttle_secs=1, # wait at least N seconds before each subsequent evaluation (default 600)
                     exporters = exporter) # export SavedModel once at the end of training

  # Note:
  # We set start_delay_secs and throttle_secs to 1 because we want to evaluate after every checkpoint.
  # As long as checkpoints are > 1 sec apart this ensures the throttling never kicks in.

  tf.logging.set_verbosity(tf.logging.INFO) # so loss is printed during training
  shutil.rmtree(OUTDIR, ignore_errors = True) # start fresh each time

  tf.estimator.train_and_evaluate(model, train_spec, eval_spec)