local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["issue-summarization-model"];
local k = import "k.libsonnet";
local serve = import "kubeflow/seldon/serve-simple.libsonnet";

local name = params.name;
local image = params.image;
local namespace = env.namespace;
local replicas = params.replicas;
local endpoint = params.endpoint;

local modelVar = 
	if std.objectHas(params, "modelFile") then
	  {
	    name: "MODEL_FILE",
	    value: params.modelFile,
	  }
	else
	  {};

local titleVar = 
	if std.objectHas(params, "titleFile") then
	  {
	    name: "TITLE_PP_FILE",
	    value: params.titleFile,
	  }
	else
	  {};


local bodyVar = 
	if std.objectHas(params, "bodyFile") then
	  {
	    name: "BODY_PP_FILE",
	    value: params.bodyFile,
	  }
	else
	  {};

local containerEnv = [modelVar, titleVar, bodyVar];

# We don't use our ksonnet component because we want to override environment 
# variables and its just cleaner to copy paste the component.
# TODO(https://github.com/kubeflow/kubeflow/issues/403) We should rewrite
# our components to better support this.
local serve = {
      apiVersion: "machinelearning.seldon.io/v1alpha1",
      kind: "SeldonDeployment",
      metadata: {
        labels: {
          app: "seldon",
        },
        name: params.name,
        namespace: env.namespace,
      },
      spec: {
        annotations: {
          deployment_version: "v1",
          project_name: params.name,
        },
        name: name,
        predictors: [
          {
            annotations: {
              predictor_version: "v1",
            },
            componentSpec: {
              spec: {
                containers: [
                  {
                    image: params.image,
                    imagePullPolicy: "Always",
                    name: params.name,
                    env: std.prune(containerEnv),
                  },
                ],
                terminationGracePeriodSeconds: 1,
              },
            },
            graph: {
              children: [

              ],
              endpoint: {
                type: endpoint,
              },
              name: name,
              type: "MODEL",
            },
            name: name,
            replicas: replicas,
          },
        ],
      },
    };


k.core.v1.list.new(serve)
