{
  parts(_env, _params):: {
    local params = _env + _params,

    local minio = import "kfp/pipeline/minio.libsonnet",
    local mysql = import "kfp/pipeline/mysql.libsonnet",
    local pipeline_apiserver = import "kfp/pipeline/pipeline-apiserver.libsonnet",
    local pipeline_scheduledworkflow = import "kfp/pipeline/pipeline-scheduledworkflow.libsonnet",
    local pipeline_persistenceagent = import "kfp/pipeline/pipeline-persistenceagent.libsonnet",
    local pipeline_ui = import "kfp/pipeline/pipeline-ui.libsonnet",

    local name = params.name,
    local namespace = params.namespace,
    local apiImage = params.apiImage,
    local scheduledWorkflowImage = params.scheduledWorkflowImage,
    local persistenceAgentImage = params.persistenceAgentImage,
    local uiImage = params.uiImage,
    all:: minio.parts(namespace).all +
          mysql.parts(namespace).all +
          pipeline_apiserver.all(namespace, apiImage) +
          pipeline_scheduledworkflow.all(namespace, scheduledWorkflowImage) +
          pipeline_persistenceagent.all(namespace, persistenceAgentImage) +
          pipeline_ui.all(namespace, uiImage),
  },
}
