local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components.argo;

local argo = import "kubeflow/argo/argo.libsonnet";
local instance = argo.new(env, params);
instance.list(instance.all)
