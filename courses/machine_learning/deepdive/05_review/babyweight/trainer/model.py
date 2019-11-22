import shutil

import numpy as np
import tensorflow as tf

tf.logging.set_verbosity(tf.logging.INFO)

BUCKET = None  # set from task.py
PATTERN = "of"

CSV_COLUMNS = [
    "weight_pounds",
    "is_male",
    "mother_age",
    "plurality",
    "gestation_weeks",
]
LABEL_COLUMN = "weight_pounds"
DEFAULTS = [[0.0], ["null"], [0.0], ["null"], [0.0]]

TRAIN_STEPS = 10000
EVAL_STEPS = None
BATCH_SIZE = 512
NEMBEDS = 3
NNSIZE = [64, 16, 4]


def read_dataset(filename_pattern, mode, batch_size):

    def _input_fn():

        def decode_csv(value_column):
            columns = tf.decode_csv(
                records=value_column,
                record_defaults=DEFAULTS
            )
            features = dict(zip(CSV_COLUMNS, columns))
            label = features.pop(LABEL_COLUMN)
            return features, label

        file_path = "gs://{}/babyweight/preproc/{}*{}*".format(
            BUCKET, filename_pattern, PATTERN)
        file_list = tf.gfile.Glob(filename=file_path)

        dataset = (
            tf.data.TextLineDataset(filenames=file_list).map(
                map_func=decode_csv)
        )

        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None  # indefinitely
            dataset = dataset.shuffle(buffer_size=10*batch_size)
        else:
            num_epochs = 1
        dataset = dataset.repeat(count=num_epochs).batch(batch_size=batch_size)

        return dataset

    return _input_fn


def get_wide_deep():

    fc_is_male = tf.feature_column.categorical_column_with_vocabulary_list(
        key="is_male",
        vocabulary_list=["True", "False", "Unknown"]
    )

    fc_plurality = tf.feature_column.categorical_column_with_vocabulary_list(
        key="plurality",
        vocabulary_list=[
            "Single(1)",
            "Twins(2)",
            "Triplets(3)",
            "Quadruplets(4)",
            "Quintuplets(5)",
            "Multiple(2+)"
        ]
    )

    fc_mother_age = tf.feature_column.numeric_column("mother_age")

    fc_gestation_weeks = tf.feature_column.numeric_column("gestation_weeks")


    fc_age_buckets = tf.feature_column.bucketized_column(
        source_column=fc_mother_age, 
        boundaries=np.arange(start=15, stop=45, step=1).tolist()
    )

    fc_gestation_buckets = tf.feature_column.bucketized_column(
        source_column=fc_gestation_weeks,
        boundaries=np.arange(start=17, stop=47, step=1).tolist())

    wide = [
        fc_is_male,
        fc_plurality,
        fc_age_buckets,
        fc_gestation_buckets
    ]

    # Feature cross all the wide columns and embed into a lower dimension
    crossed = tf.feature_column.crossed_column(
        keys=wide, hash_bucket_size=20000
    )
    fc_embed = tf.feature_column.embedding_column(
        categorical_column=crossed,
        dimension=3
    )

    # Continuous columns are deep, have a complex relationship with the output
    deep = [
        fc_mother_age,
        fc_gestation_weeks,
        fc_embed
    ]

    return wide, deep


def serving_input_fn():
    feature_placeholders = {
        "is_male": tf.placeholder(dtype=tf.string, shape=[None]),
        "mother_age": tf.placeholder(dtype=tf.float32, shape=[None]),
        "plurality": tf.placeholder(dtype=tf.string, shape=[None]),
        "gestation_weeks": tf.placeholder(dtype=tf.float32, shape=[None])
    }

    features = {
        key: tf.expand_dims(input=tensor, axis=-1)
        for key, tensor in feature_placeholders.items()
    }

    return tf.estimator.export.ServingInputReceiver(
        features=features, 
        receiver_tensors=feature_placeholders
    )


def my_rmse(labels, predictions):
    pred_values = predictions["predictions"]
    return {
        "rmse": tf.metrics.root_mean_squared_error(
            labels=labels,
            predictions=pred_values
        )
    }


def train_and_evaluate(output_dir):
    wide, deep = get_wide_deep()
    EVAL_INTERVAL = 300  # seconds

    run_config = tf.estimator.RunConfig(
        save_checkpoints_secs=EVAL_INTERVAL,
        keep_checkpoint_max=3)

    estimator = tf.estimator.DNNLinearCombinedRegressor(
        model_dir=output_dir,
        linear_feature_columns=wide,
        dnn_feature_columns=deep,
        dnn_hidden_units=NNSIZE,
        config=run_config)

    estimator = tf.contrib.estimator.add_metrics(estimator, my_rmse)

    train_spec = tf.estimator.TrainSpec(
        input_fn=read_dataset(
            "train", tf.estimator.ModeKeys.TRAIN, BATCH_SIZE),
        max_steps=TRAIN_STEPS)

    exporter = tf.estimator.LatestExporter(
        name="exporter",
        serving_input_receiver_fn=serving_input_fn,
        exports_to_keep=None)

    eval_spec = tf.estimator.EvalSpec(
        input_fn=read_dataset(
            "eval", tf.estimator.ModeKeys.EVAL, 2**15),
        steps=EVAL_STEPS,
        start_delay_secs=60,  # start evaluating after N seconds
        throttle_secs=EVAL_INTERVAL,  # evaluate every N seconds
        exporters=exporter)

    tf.estimator.train_and_evaluate(
        estimator=estimator,
        train_spec=train_spec,
        eval_spec=eval_spec
    )
