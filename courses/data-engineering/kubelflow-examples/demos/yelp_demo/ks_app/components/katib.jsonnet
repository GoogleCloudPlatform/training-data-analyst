local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components.katib;

local k = import "k.libsonnet";

local studyjobcontroller = import "kubeflow/katib/studyjobcontroller.libsonnet";
local suggestion = import "kubeflow/katib/suggestion.libsonnet";
local vizier = import "kubeflow/katib/vizier.libsonnet";

local namespace = env.namespace;

std.prune(
  k.core.v1.list.new(vizier.all(params, namespace))
  + k.core.v1.list.new(suggestion.all(params, namespace))
  + k.core.v1.list.new(studyjobcontroller.all(params, namespace))
)
