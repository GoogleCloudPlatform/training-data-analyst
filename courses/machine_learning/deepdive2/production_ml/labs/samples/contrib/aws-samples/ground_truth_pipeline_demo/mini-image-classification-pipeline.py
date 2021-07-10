#!/usr/bin/env python3

import kfp
import json
import copy
from kfp import components
from kfp import dsl
from kfp.aws import use_aws_secret

sagemaker_workteam_op = components.load_component_from_file(
    "../../../../components/aws/sagemaker/workteam/component.yaml"
)
sagemaker_gt_op = components.load_component_from_file(
    "../../../../components/aws/sagemaker/ground_truth/component.yaml"
)
sagemaker_train_op = components.load_component_from_file(
    "../../../../components/aws/sagemaker/train/component.yaml"
)

channelObjList = []

channelObj = {
    "ChannelName": "",
    "DataSource": {
        "S3DataSource": {
            "S3Uri": "",
            "S3DataType": "AugmentedManifestFile",
            "S3DataDistributionType": "FullyReplicated",
            "AttributeNames": ["source-ref", "category"],
        }
    },
    "ContentType": "application/x-recordio",
    "CompressionType": "None",
    "RecordWrapperType": "RecordIO",
}


@dsl.pipeline(
    name="Ground Truth image classification test pipeline",
    description="SageMaker Ground Truth job test",
)
def ground_truth_test(
    region="us-west-2",
    team_name="ground-truth-demo-team",
    team_description="Team for mini image classification labeling job",
    user_pool="",
    user_groups="",
    client_id="",
    ground_truth_train_job_name="mini-image-classification-demo-train",
    ground_truth_validation_job_name="mini-image-classification-demo-validation",
    ground_truth_label_attribute_name="category",
    ground_truth_train_manifest_location="s3://your-bucket-name/mini-image-classification/ground-truth-demo/train.manifest",
    ground_truth_validation_manifest_location="s3://your-bucket-name/mini-image-classification/ground-truth-demo/validation.manifest",
    ground_truth_output_location="s3://your-bucket-name/mini-image-classification/ground-truth-demo/output",
    ground_truth_task_type="image classification",
    ground_truth_worker_type="private",
    ground_truth_label_category_config="s3://your-bucket-name/mini-image-classification/ground-truth-demo/class_labels.json",
    ground_truth_ui_template="s3://your-bucket-name/mini-image-classification/ground-truth-demo/instructions.template",
    ground_truth_title="Mini image classification",
    ground_truth_description="Test for Ground Truth KFP component",
    ground_truth_num_workers_per_object=1,
    ground_truth_time_limit=30,
    ground_truth_task_availibility=3600,
    ground_truth_max_concurrent_tasks=20,
    training_algorithm_name="image classification",
    training_input_mode="Pipe",
    training_hyperparameters={
        "num_classes": "2",
        "num_training_samples": "14",
        "mini_batch_size": "2",
    },
    training_output_location="s3://your-bucket-name/mini-image-classification/training-output",
    training_instance_type="ml.m5.2xlarge",
    training_instance_count=1,
    training_volume_size=50,
    training_max_run_time=3600,
    role_arn="",
):

    workteam = sagemaker_workteam_op(
        region=region,
        team_name=team_name,
        description=team_description,
        user_pool=user_pool,
        user_groups=user_groups,
        client_id=client_id,
    )

    ground_truth_train = sagemaker_gt_op(
        region=region,
        role=role_arn,
        job_name=ground_truth_train_job_name,
        label_attribute_name=ground_truth_label_attribute_name,
        manifest_location=ground_truth_train_manifest_location,
        output_location=ground_truth_output_location,
        task_type=ground_truth_task_type,
        worker_type=ground_truth_worker_type,
        workteam_arn=workteam.output,
        label_category_config=ground_truth_label_category_config,
        ui_template=ground_truth_ui_template,
        title=ground_truth_title,
        description=ground_truth_description,
        num_workers_per_object=ground_truth_num_workers_per_object,
        time_limit=ground_truth_time_limit,
        task_availibility=ground_truth_task_availibility,
        max_concurrent_tasks=ground_truth_max_concurrent_tasks,
    )

    ground_truth_validation = sagemaker_gt_op(
        region=region,
        role=role_arn,
        job_name=ground_truth_validation_job_name,
        label_attribute_name=ground_truth_label_attribute_name,
        manifest_location=ground_truth_validation_manifest_location,
        output_location=ground_truth_output_location,
        task_type=ground_truth_task_type,
        worker_type=ground_truth_worker_type,
        workteam_arn=workteam.output,
        label_category_config=ground_truth_label_category_config,
        ui_template=ground_truth_ui_template,
        title=ground_truth_title,
        description=ground_truth_description,
        num_workers_per_object=ground_truth_num_workers_per_object,
        time_limit=ground_truth_time_limit,
        task_availibility=ground_truth_task_availibility,
        max_concurrent_tasks=ground_truth_max_concurrent_tasks,
    )

    channelObj["ChannelName"] = "train"
    channelObj["DataSource"]["S3DataSource"]["S3Uri"] = str(
        ground_truth_train.outputs["output_manifest_location"]
    )
    channelObjList.append(copy.deepcopy(channelObj))
    channelObj["ChannelName"] = "validation"
    channelObj["DataSource"]["S3DataSource"]["S3Uri"] = str(
        ground_truth_validation.outputs["output_manifest_location"]
    )
    channelObjList.append(copy.deepcopy(channelObj))

    training = sagemaker_train_op(
        region=region,
        algorithm_name=training_algorithm_name,
        training_input_mode=training_input_mode,
        hyperparameters=training_hyperparameters,
        channels=json.dumps(channelObjList),
        instance_type=training_instance_type,
        instance_count=training_instance_count,
        volume_size=training_volume_size,
        max_run_time=training_max_run_time,
        model_artifact_path=training_output_location,
        role=role_arn,
    )


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(ground_truth_test, __file__ + ".zip")
