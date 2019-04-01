local params = std.extVar("__ksonnet/params").components.servePoetry;
// TODO(https://github.com/ksonnet/ksonnet/issues/222): We have to add namespace as an explicit parameter
// because ksonnet doesn't support inheriting it from the environment yet.

local k = import 'k.libsonnet';
local tfServing = import 'kubeflow/tf-serving/tf-serving.libsonnet';

local name = params.name;
local namespace = params.namespace;
local modelPath = params.model_path;
local modelServerImage = params.model_server_image;
local httpProxyImage = params.http_proxy_image;

// 
local service = tfServing.parts.deployment.modelService(name, namespace) + {
	"spec"+: {
		type: "NodePort",	

	},	
};

local ingress = {
      apiVersion: "extensions/v1beta1",
      kind: "Ingress",
      metadata: {
        name: "models-ingress",
        namespace: namespace,
        annotations: {
          "kubernetes.io/ingress.global-static-ip-name": params.ipName,
        },
      },
      spec: {
        rules: [
          {
            http: {
              paths: [
                {
                  backend: {
                    serviceName: "poetry",
    				servicePort: 8000
                  },
                  path: "/*",
                },
              ],
            },
          },
        ],
      },
    }; 

std.prune(k.core.v1.list.new([
  tfServing.parts.deployment.modelServer(name, namespace, modelPath, modelServerImage, httpProxyImage),
  service,
  ingress
]))
