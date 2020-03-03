local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["cert-manager"];

local certManager = import "kubeflow/core/cert-manager.libsonnet";
local instance = certManager.new(env, params);
instance.list(instance.all)
