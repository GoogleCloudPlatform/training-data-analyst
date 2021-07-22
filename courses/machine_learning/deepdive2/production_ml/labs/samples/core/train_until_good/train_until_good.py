#!/usr/bin/env python3
# Copyright 2020 The Kubeflow Pipleines authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This sample demonstrates continuous training using a train-eval-check recursive loop.
# The main pipeline trains the initial model and then gradually trains the model
# some more until the model evaluation metrics are good enough.

import kfp
from kfp import components


chicago_taxi_dataset_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/e3337b8bdcd63636934954e592d4b32c95b49129/components/datasets/Chicago%20Taxi/component.yaml')
xgboost_train_on_csv_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/567c04c51ff00a1ee525b3458425b17adbe3df61/components/XGBoost/Train/component.yaml')
xgboost_predict_on_csv_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/567c04c51ff00a1ee525b3458425b17adbe3df61/components/XGBoost/Predict/component.yaml')

pandas_transform_csv_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/6162d55998b176b50267d351241100bb0ee715bc/components/pandas/Transform_DataFrame/in_CSV_format/component.yaml')
drop_header_op = kfp.components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/02c9638287468c849632cf9f7885b51de4c66f86/components/tables/Remove_header/component.yaml')
calculate_regression_metrics_from_csv_op = kfp.components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/616542ac0f789914f4eb53438da713dd3004fba4/components/ml_metrics/Calculate_regression_metrics/from_CSV/component.yaml')


# This recursive sub-pipeline trains a model, evaluates it, calculates the metrics and checks them.
# If the model error is too high, then more training is performed until the model is good.
@kfp.dsl.graph_component
def train_until_low_error(starting_model, training_data, true_values):
    # Training
    model = xgboost_train_on_csv_op(
        training_data=training_data,
        starting_model=starting_model,
        label_column=0,
        objective='reg:squarederror',
        num_iterations=50,
    ).outputs['model']

    # Predicting
    predictions = xgboost_predict_on_csv_op(
        data=training_data,
        model=model,
        label_column=0,
    ).output

    # Calculating the regression metrics    
    metrics_task = calculate_regression_metrics_from_csv_op(
        true_values=true_values,
        predicted_values=predictions,
    )

    # Checking the metrics
    with kfp.dsl.Condition(metrics_task.outputs['mean_squared_error'] > 0.01):
        # Training some more
        train_until_low_error(
            starting_model=model,
            training_data=training_data,
            true_values=true_values,
        )


# The main pipleine trains the initial model and then gradually trains the model some more until the model evaluation metrics are good enough.
@kfp.dsl.pipeline()
def train_until_good_pipeline():
    # Preparing the training data
    training_data = chicago_taxi_dataset_op(
        where='trip_start_timestamp >= "2019-01-01" AND trip_start_timestamp < "2019-02-01"',
        select='tips,trip_seconds,trip_miles,pickup_community_area,dropoff_community_area,fare,tolls,extras,trip_total',
        limit=10000,
    ).output

    # Preparing the true values
    true_values_table = pandas_transform_csv_op(
        table=training_data,
        transform_code='df = df[["tips"]]',
    ).output
    
    true_values = drop_header_op(true_values_table).output

    # Initial model training
    first_model = xgboost_train_on_csv_op(
        training_data=training_data,
        label_column=0,
        objective='reg:squarederror',
        num_iterations=100,
    ).outputs['model']

    # Recursively training until the error becomes low
    train_until_low_error(
        starting_model=first_model,
        training_data=training_data,
        true_values=true_values,
    )


if __name__ == '__main__':
    kfp_endpoint=None
    kfp.Client(host=kfp_endpoint).create_run_from_pipeline_func(train_until_good_pipeline, arguments={})
