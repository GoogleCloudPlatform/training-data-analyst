#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh

TEST_DATA=$PROJECT_DIR/tests/data
TEST_BUCKET=gs://$BUCKET/taxifare-test
DATA_PATH=$TEST_BUCKET/data
TRAIN_PATH=$DATA_PATH/taxi-train*
EVAL_PATH=$DATA_PATH/taxi-valid*
MODEL_PATH=$TEST_BUCKET/model

gsutil ls $TEST_BUCKET && gsutil -m rm -r $TEST_BUCKET 
gsutil -m cp $TEST_DATA/* $DATA_PATH

$SCRIPTS_DIR/run.sh \
--eval_data_path $EVAL_PATH \
--output_dir $MODEL_PATH \
--train_data_path $TRAIN_PATH \
--batch_size 5 \
--num_examples_to_train_on 100 \
--num_evals 1 \
--nbuckets 10 \
--nnsize 32 8

gsutil -m rm -r $TEST_BUCKET
