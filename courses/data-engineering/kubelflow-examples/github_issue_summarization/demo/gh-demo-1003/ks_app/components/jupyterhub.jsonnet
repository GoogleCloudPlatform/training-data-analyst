local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components.jupyterhub;

local jupyterhub = import "kubeflow/core/jupyterhub.libsonnet";
local instance = jupyterhub.new(env, params);
instance.list(instance.all)
