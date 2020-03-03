local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["cloud-endpoints"];

local cloudEndpoints = import "kubeflow/core/cloud-endpoints.libsonnet";
local instance = cloudEndpoints.new(env, params);
instance.list(instance.all)
