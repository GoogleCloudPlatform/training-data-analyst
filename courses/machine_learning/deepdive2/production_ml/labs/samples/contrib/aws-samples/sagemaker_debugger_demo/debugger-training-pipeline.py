#!/usr/bin/env python3

import kfp
import json
import os
import copy
from kfp import components
from kfp import dsl


cur_file_dir = os.path.dirname(__file__)
components_dir = os.path.join(cur_file_dir, "../../../../components/aws/sagemaker/")

sagemaker_train_op = components.load_component_from_file(
    components_dir + "/train/component.yaml"
)


def training_input(input_name, s3_uri, content_type):
    return {
        "ChannelName": input_name,
        "DataSource": {"S3DataSource": {"S3Uri": s3_uri, "S3DataType": "S3Prefix"}},
        "ContentType": content_type,
    }


def training_debug_hook(s3_uri, collection_dict):
    return {
        "S3OutputPath": s3_uri,
        "CollectionConfigurations": format_collection_config(collection_dict),
    }


def format_collection_config(collection_dict):
    output = []
    for key, val in collection_dict.items():
        output.append({"CollectionName": key, "CollectionParameters": val})
    return output


def training_debug_rules(rule_name, parameters):
    return {
        "RuleConfigurationName": rule_name,
        "RuleEvaluatorImage": "503895931360.dkr.ecr.us-east-1.amazonaws.com/sagemaker-debugger-rules:latest",
        "RuleParameters": parameters,
    }


collections = {
    "feature_importance": {"save_interval": "5"},
    "losses": {"save_interval": "10"},
    "average_shap": {"save_interval": "5"},
    "metrics": {"save_interval": "3"},
}


bad_hyperparameters = {
    "max_depth": "5",
    "eta": "0",
    "gamma": "4",
    "min_child_weight": "6",
    "silent": "0",
    "subsample": "0.7",
    "num_round": "50",
}


@dsl.pipeline(
    name="XGBoost Training Pipeline with bad hyperparameters",
    description="SageMaker training job test with debugger",
)
def training(role_arn="", bucket_name="my-bucket"):
    train_channels = [
        training_input(
            "train",
            f"s3://{bucket_name}/mnist_kmeans_example/input/valid_data.csv",
            "text/csv",
        )
    ]
    train_debug_rules = [
        training_debug_rules(
            "LossNotDecreasing",
            {"rule_to_invoke": "LossNotDecreasing", "tensor_regex": ".*"},
        ),
        training_debug_rules(
            "Overtraining",
            {
                "rule_to_invoke": "Overtraining",
                "patience_train": "10",
                "patience_validation": "20",
            },
        ),
    ]
    training = sagemaker_train_op(
        region="us-east-1",
        image="683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:0.90-2-cpu-py3",
        hyperparameters=bad_hyperparameters,
        channels=train_channels,
        instance_type="ml.m5.2xlarge",
        model_artifact_path=f"s3://{bucket_name}/mnist_kmeans_example/output/model",
        debug_hook_config=training_debug_hook(
            f"s3://{bucket_name}/mnist_kmeans_example/hook_config", collections
        ),
        debug_rule_config=train_debug_rules,
        role=role_arn,
    )


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(training, __file__ + ".zip")
