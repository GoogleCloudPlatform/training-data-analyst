#!/usr/bin/env python3


import kfp
from kfp import components
from kfp import dsl

sagemaker_hpo_op = components.load_component_from_file(
    "../../../../components/aws/sagemaker/hyperparameter_tuning/component.yaml"
)
sagemaker_process_op = components.load_component_from_file(
    "../../../../components/aws/sagemaker/process/component.yaml"
)
sagemaker_train_op = components.load_component_from_file(
    "../../../../components/aws/sagemaker/train/component.yaml"
)
sagemaker_model_op = components.load_component_from_file(
    "../../../../components/aws/sagemaker/model/component.yaml"
)
sagemaker_deploy_op = components.load_component_from_file(
    "../../../../components/aws/sagemaker/deploy/component.yaml"
)
sagemaker_batch_transform_op = components.load_component_from_file(
    "../../../../components/aws/sagemaker/batch_transform/component.yaml"
)


def processing_input(input_name, s3_uri, local_path):
    return {
        "InputName": input_name,
        "S3Input": {
            "S3Uri": s3_uri,
            "LocalPath": local_path,
            "S3DataType": "S3Prefix",
            "S3InputMode": "File",
        },
    }


def processing_output(output_name, s3_uri, local_path):
    return {
        "OutputName": output_name,
        "S3Output": {
            "S3Uri": s3_uri,
            "LocalPath": local_path,
            "S3UploadMode": "EndOfJob",
        },
    }


def training_input(input_name, s3_uri):
    return {
        "ChannelName": input_name,
        "DataSource": {"S3DataSource": {"S3Uri": s3_uri, "S3DataType": "S3Prefix"}},
    }


@dsl.pipeline(
    name="MNIST Classification pipeline",
    description="MNIST Classification using KMEANS in SageMaker",
)
def mnist_classification(role_arn="", bucket_name=""):
    # Common component inputs
    region = "us-east-1"
    instance_type = "ml.m5.2xlarge"
    train_image = "382416733822.dkr.ecr.us-east-1.amazonaws.com/kmeans:1"

    # Training input and output location based on bucket name
    hpo_channels = [
        training_input("train", f"s3://{bucket_name}/mnist_kmeans_example/train_data"),
        training_input("test", f"s3://{bucket_name}/mnist_kmeans_example/test_data"),
    ]
    train_channels = [
        training_input("train", f"s3://{bucket_name}/mnist_kmeans_example/train_data")
    ]
    train_output_location = f"s3://{bucket_name}/mnist_kmeans_example/output"

    process = sagemaker_process_op(
        role=role_arn,
        region=region,
        image="763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:1.5.0-cpu-py36-ubuntu16.04",
        instance_type=instance_type,
        container_entrypoint=[
            "python",
            "/opt/ml/processing/code/kmeans_preprocessing.py",
        ],
        input_config=[
            processing_input(
                "mnist_tar",
                "s3://sagemaker-sample-data-us-east-1/algorithms/kmeans/mnist/mnist.pkl.gz",
                "/opt/ml/processing/input",
            ),
            processing_input(
                "source_code",
                f"s3://{bucket_name}/mnist_kmeans_example/processing_code/kmeans_preprocessing.py",
                "/opt/ml/processing/code",
            ),
        ],
        output_config=[
            processing_output(
                "train_data",
                f"s3://{bucket_name}/mnist_kmeans_example/",
                "/opt/ml/processing/output_train/",
            ),
            processing_output(
                "test_data",
                f"s3://{bucket_name}/mnist_kmeans_example/",
                "/opt/ml/processing/output_test/",
            ),
            processing_output(
                "valid_data",
                f"s3://{bucket_name}/mnist_kmeans_example/input/",
                "/opt/ml/processing/output_valid/",
            ),
        ],
    )

    hpo = sagemaker_hpo_op(
        region=region,
        image=train_image,
        metric_name="test:msd",
        metric_type="Minimize",
        static_parameters={"k": "10", "feature_dim": "784"},
        integer_parameters=[
            {"Name": "mini_batch_size", "MinValue": "500", "MaxValue": "600"},
            {"Name": "extra_center_factor", "MinValue": "10", "MaxValue": "20"},
        ],
        categorical_parameters=[
            {"Name": "init_method", "Values": ["random", "kmeans++"]}
        ],
        channels=hpo_channels,
        output_location=train_output_location,
        instance_type=instance_type,
        max_num_jobs=3,
        max_parallel_jobs=2,
        role=role_arn,
    ).after(process)

    training = sagemaker_train_op(
        region=region,
        image=train_image,
        hyperparameters=hpo.outputs["best_hyperparameters"],
        channels=train_channels,
        instance_type=instance_type,
        model_artifact_path=train_output_location,
        role=role_arn,
    )

    create_model = sagemaker_model_op(
        region=region,
        model_name=training.outputs["job_name"],
        image=training.outputs["training_image"],
        model_artifact_url=training.outputs["model_artifact_url"],
        role=role_arn,
    )

    sagemaker_deploy_op(
        region=region, model_name_1=create_model.output,
    )

    sagemaker_batch_transform_op(
        region=region,
        model_name=create_model.output,
        instance_type=instance_type,
        batch_strategy="MultiRecord",
        input_location=f"s3://{bucket_name}/mnist_kmeans_example/input",
        content_type="text/csv",
        split_type="Line",
        output_location=f"s3://{bucket_name}/mnist_kmeans_example/output",
    )


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(mnist_classification, __file__ + ".zip")
