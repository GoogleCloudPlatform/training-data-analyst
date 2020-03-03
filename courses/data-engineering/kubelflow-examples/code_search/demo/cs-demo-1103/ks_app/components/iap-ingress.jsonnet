local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["iap-ingress"];

local iap = import "kubeflow/core/iap.libsonnet";
local instance = iap.new(env, params);
instance.list(instance.all)
