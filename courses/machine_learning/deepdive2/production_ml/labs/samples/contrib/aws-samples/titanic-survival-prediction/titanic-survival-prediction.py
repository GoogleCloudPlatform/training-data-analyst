#!/usr/bin/env python3

import kfp
from kfp import components
from kfp import dsl
from kfp import gcp
from kfp.aws import use_aws_secret

emr_create_cluster_op = components.load_component_from_file(
    "../../../../components/aws/emr/create_cluster/component.yaml"
)
emr_submit_spark_job_op = components.load_component_from_file(
    "../../../../components/aws/emr/submit_spark_job/component.yaml"
)
emr_delete_cluster_op = components.load_component_from_file(
    "../../../../components/aws/emr/delete_cluster/component.yaml"
)


@dsl.pipeline(
    name="Titanic Suvival Prediction Pipeline",
    description="Predict survival on the Titanic",
)
def titanic_suvival_prediction(
    region="us-west-2",
    log_s3_uri="s3://kubeflow-pipeline-data/emr/titanic/logs",
    cluster_name="emr-cluster",
    job_name="spark-ml-trainner",
    input="s3://kubeflow-pipeline-data/emr/titanic/train.csv",
    output="s3://kubeflow-pipeline-data/emr/titanic/output",
    jar_path="s3://kubeflow-pipeline-data/emr/titanic/titanic-survivors-prediction_2.11-1.0.jar",
    main_class="com.amazonaws.emr.titanic.Titanic",
    instance_type="m4.xlarge",
    instance_count="3",
):

    create_cluster = emr_create_cluster_op(
        region=region,
        name=cluster_name,
        instance_type=instance_type,
        instance_count=instance_count,
        log_s3_uri=log_s3_uri,
    ).apply(use_aws_secret("aws-secret", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"))

    training_and_prediction = emr_submit_spark_job_op(
        region=region,
        jobflow_id=create_cluster.output,
        job_name=job_name,
        jar_path=jar_path,
        main_class=main_class,
        input=input,
        output=output,
    ).apply(use_aws_secret("aws-secret", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"))

    delete_cluster = emr_delete_cluster_op(
        region=region,
        jobflow_id=create_cluster.output,
        dependent=training_and_prediction.outputs["job_id"],
    ).apply(use_aws_secret("aws-secret", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"))


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(titanic_suvival_prediction, __file__ + ".zip")
