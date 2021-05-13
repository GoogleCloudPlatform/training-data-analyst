import kfp.dsl as dsl
import kfp.components as components
import ai_pipeline_params as params

secret_name = 'aios-creds'

preprocess_spark_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/spark/data_preprocess_spark/component.yaml')
train_spark_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/spark/train_spark/component.yaml')
store_spark_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/spark/store_spark_model/component.yaml')
deploy_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/watson/deploy/component.yaml')
subscribe_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/watson/manage/subscribe/component.yaml')
fairness_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/watson/manage/monitor_fairness/component.yaml')
quality_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/watson/manage/monitor_quality/component.yaml')


@dsl.pipeline(
  name='Watson OpenScale Pipeline',
  description='A pipeline for end to end Spark machine learning workflow and model monitoring.'
)
def aiosPipeline(
    BUCKET_NAME='',
    TRAINING_DATA_LINK='https://raw.githubusercontent.com/emartensibm/german-credit/master/german_credit_data_biased_training.csv',
    POSTGRES_SCHEMA_NAME='data_mart_credit',
    LABEL_NAME='Risk',
    PROBLEM_TYPE='BINARY_CLASSIFICATION',
    THRESHOLD='0.7',
    AIOS_MANIFEST_PATH='aios.json',
    MODEL_FILE_PATH='model.py',
    SPARK_ENTRYPOINT='python model.py',
    MODEL_NAME='Spark German Risk Model - Final',
    DEPLOYMENT_NAME='Spark German Risk Deployment - Final'
):

    """A pipeline for Spark machine learning workflow with OpenScale."""

    data_preprocess_spark = preprocess_spark_op(
        bucket_name=BUCKET_NAME,
        data_url=TRAINING_DATA_LINK
        ).apply(params.use_ai_pipeline_params(secret_name))
    train_spark = train_spark_op(
        bucket_name=BUCKET_NAME,
        data_filename=data_preprocess_spark.output,
        model_filename=MODEL_FILE_PATH,
        spark_entrypoint=SPARK_ENTRYPOINT
        ).apply(params.use_ai_pipeline_params(secret_name))
    store_spark_model = store_spark_op(
        bucket_name=BUCKET_NAME,
        aios_manifest_path=AIOS_MANIFEST_PATH,
        problem_type=PROBLEM_TYPE,
        model_name=MODEL_NAME,
        deployment_name=DEPLOYMENT_NAME,
        model_filepath=train_spark.outputs['model_filepath'],
        train_data_filepath=train_spark.outputs['train_data_filepath']
        ).apply(params.use_ai_pipeline_params(secret_name))
    deploy = deploy_op(
        model_uid=store_spark_model.output,
        model_name=MODEL_NAME,
        deployment_name=DEPLOYMENT_NAME
        ).apply(params.use_ai_pipeline_params(secret_name))
    subscribe = subscribe_op(
        model_uid=deploy.outputs['model_uid'],
        model_name=MODEL_NAME,
        aios_schema=POSTGRES_SCHEMA_NAME,
        label_column=LABEL_NAME,
        aios_manifest_path=AIOS_MANIFEST_PATH,
        bucket_name=BUCKET_NAME,
        problem_type=PROBLEM_TYPE
        ).apply(params.use_ai_pipeline_params(secret_name))
    monitor_quality = quality_op(
        model_name=subscribe.output,
        quality_threshold=THRESHOLD
        ).apply(params.use_ai_pipeline_params(secret_name))
    monitor_fairness = fairness_op(
        model_name=subscribe.output,
        aios_manifest_path=AIOS_MANIFEST_PATH,
        cos_bucket_name=BUCKET_NAME,
        data_filename=data_preprocess_spark.output
        ).apply(params.use_ai_pipeline_params(secret_name))


if __name__ == '__main__':
    import kfp.compiler as compiler
    compiler.Compiler().compile(aiosPipeline, __file__ + '.tar.gz')
