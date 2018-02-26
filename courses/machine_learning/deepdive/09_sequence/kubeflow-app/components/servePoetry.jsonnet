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

std.prune(k.core.v1.list.new([
  tfServing.parts.deployment.modelServer(name, namespace, modelPath, modelServerImage, httpProxyImage),
  tfServing.parts.deployment.modelService(name, namespace),
]))
