# Example Pipeline to update code search UI configuration
# To compile, use Kubeflow Pipelines V0.1.3 SDK or above.

import uuid
from kubernetes import client as k8s_client
import kfp.dsl as dsl
import kfp.gcp as gcp


# disable max arg lint check
# pylint: disable=R0913

def dataflow_function_embedding_op(
        cluster_name: str,
        function_embeddings_bq_table: str,
        function_embeddings_dir: str,
        namespace: str,
        num_workers: int,
        project: 'GcpProject',
        saved_model_dir: 'GcsUri',
        worker_machine_type: str,
        workflow_id: str,
        working_dir: str,):
  return dsl.ContainerOp(
    name='dataflow_function_embedding',
    image='gcr.io/kubeflow-examples/code-search/ks:v20181210-d7487dd-dirty-eb371e',
    command=['/usr/local/src/submit_code_embeddings_job.sh'],
    arguments=[
      "--cluster=%s" % cluster_name,
      "--dataDir=%s" % 'gs://code-search-demo/20181104/data',
      "--functionEmbeddingsDir=%s" % function_embeddings_dir,
      "--functionEmbeddingsBQTable=%s" % function_embeddings_bq_table,
      "--modelDir=%s" % saved_model_dir,
      "--namespace=%s" % namespace,
      "--numWorkers=%s" % num_workers,
      "--project=%s" % project,
      "--workerMachineType=%s" % worker_machine_type,
      "--workflowId=%s" % workflow_id,
      "--workingDir=%s" % working_dir,
    ]
  ).apply(gcp.use_gcp_secret('user-gcp-sa'))



def search_index_creator_op(
        cluster_name: str,
        function_embeddings_dir: str,
        index_file: str,
        lookup_file: str,
        namespace: str,
        workflow_id: str):
  return dsl.ContainerOp(
    # use component name as step name
    name='search_index_creator',
    image='gcr.io/kubeflow-examples/code-search/ks:v20181210-d7487dd-dirty-eb371e',
    command=['/usr/local/src/launch_search_index_creator_job.sh'],
    arguments=[
      '--cluster=%s' % cluster_name,
      '--functionEmbeddingsDir=%s' % function_embeddings_dir,
      '--indexFile=%s' % index_file,
      '--lookupFile=%s' % lookup_file,
      '--namespace=%s' % namespace,
      '--workflowId=%s' % workflow_id,
    ]
  )


def update_index_op(
        app_dir: str,
        base_branch: str,
        base_git_repo: str,
        bot_email: str,
        fork_git_repo: str,
        index_file: str,
        lookup_file: str,
        workflow_id: str):
  return (
    dsl.ContainerOp(
      name='update_index',
      image='gcr.io/kubeflow-examples/code-search/ks:v20181210-d7487dd-dirty-eb371e',
      command=['/usr/local/src/update_index.sh'],
      arguments=[
        '--appDir=%s' % app_dir,
        '--baseBranch=%s' % base_branch,
        '--baseGitRepo=%s' % base_git_repo,
        '--botEmail=%s' % bot_email,
        '--forkGitRepo=%s' % fork_git_repo,
        '--indexFile=%s' % index_file,
        '--lookupFile=%s' % lookup_file,
        '--workflowId=%s' % workflow_id,
      ],
    )
    .add_volume(
      k8s_client.V1Volume(
        name='github-access-token',
        secret=k8s_client.V1SecretVolumeSource(
          secret_name='github-access-token'
        )
      )
    )
    .add_env_variable(
      k8s_client.V1EnvVar(
        name='GITHUB_TOKEN',
        value_from=k8s_client.V1EnvVarSource(
          secret_key_ref=k8s_client.V1SecretKeySelector(
            name='github-access-token',
            key='token',
          )
        )
      )
    )
  )


# The pipeline definition
@dsl.pipeline(
  name='github_code_index_update',
  description='Example of pipeline to update github code index'
)
def github_code_index_update(
    project='code-search-demo',
    cluster_name='cs-demo-1103',
    namespace='kubeflow',
    working_dir='gs://code-search-demo/pipeline',
    saved_model_dir='gs://code-search-demo/models/20181107-dist-sync-gpu/export/1541712907/',
    target_dataset='code_search',
    worker_machine_type='n1-highcpu-32',
    num_workers=5,
    base_git_repo='kubeflow/examples',
    base_branch='master',
    app_dir='code_search/ks-web-app',
    fork_git_repo='IronPan/examples',
    bot_email='kf.sample.bot@gmail.com',
    # Can't use workflow name as bq_suffix since BQ table doesn't accept '-' and
    # workflow name is assigned at runtime. Pipeline might need to support
    # replacing characters in workflow name.
    # For recurrent pipeline, pass in '[[Index]]' instead, for unique naming.
    bq_suffix=uuid.uuid4().hex[:6].upper()):
  workflow_name = '{{workflow.name}}'
  working_dir = '%s/%s' % (working_dir, workflow_name)
  lookup_file = '%s/code-embeddings-index/embedding-to-info.csv' % working_dir
  index_file = '%s/code-embeddings-index/embeddings.index'% working_dir
  function_embeddings_dir = '%s/%s' % (working_dir, "code_embeddings")
  function_embeddings_bq_table = \
    '%s:%s.function_embeddings_%s' % (project, target_dataset, bq_suffix)

  function_embedding = dataflow_function_embedding_op(
    cluster_name,
    function_embeddings_bq_table,
    function_embeddings_dir,
    namespace,
    num_workers,
    project,
    saved_model_dir,
    worker_machine_type,
    workflow_name,
    working_dir)

  search_index_creator = search_index_creator_op(
    cluster_name,
    function_embeddings_dir,
    index_file,
    lookup_file,
    namespace,
    workflow_name)
  search_index_creator.after(function_embedding)

  update_index_op(
    app_dir,
    base_branch,
    base_git_repo,
    bot_email,
    fork_git_repo,
    index_file,
    lookup_file,
    workflow_name).after(search_index_creator)


if __name__ == '__main__':
  import kfp.compiler as compiler

  compiler.Compiler().compile(github_code_index_update, __file__ + '.tar.gz')
