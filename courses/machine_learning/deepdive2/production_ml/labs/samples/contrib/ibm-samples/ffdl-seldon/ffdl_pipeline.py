import kfp
from kfp import components
from kfp import dsl
import ai_pipeline_params as params

# generate default secret name
secret_name = 'kfp-creds'

configuration_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/eb830cd73ca148e5a1a6485a9374c2dc068314bc/components/ibm-components/commons/config/component.yaml')
train_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/eb830cd73ca148e5a1a6485a9374c2dc068314bc/components/ibm-components/ffdl/train/component.yaml')
serve_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/eb830cd73ca148e5a1a6485a9374c2dc068314bc/components/ibm-components/ffdl/serve/component.yaml')
    
# create pipeline
@dsl.pipeline(
  name='FfDL pipeline',
  description='A pipeline for machine learning workflow using Fabric for Deep Learning and Seldon.'
)

def ffdlPipeline(
    GITHUB_TOKEN='',
    CONFIG_FILE_URL='https://raw.githubusercontent.com/user/repository/branch/creds.ini',
    model_def_file_path='gender-classification.zip',
    manifest_file_path='manifest.yml',
    model_deployment_name='gender-classifier',
    model_class_name='ThreeLayerCNN',
    model_class_file='gender_classification.py'
):
    """A pipeline for end to end machine learning workflow."""
    
    create_secrets = configuration_op(
                   token = GITHUB_TOKEN,
                   url = CONFIG_FILE_URL,
                   name = secret_name
    )

    train = train_op(
                   model_def_file_path,
                   manifest_file_path
    ).apply(params.use_ai_pipeline_params(secret_name))

    serve = serve_op(
                   train.output, 
                   model_deployment_name, 
                   model_class_name, 
                   model_class_file
    ).apply(params.use_ai_pipeline_params(secret_name))


if __name__ == '__main__':
    import kfp.compiler as compiler
    compiler.Compiler().compile(ffdlPipeline, __file__ + '.tar.gz')
