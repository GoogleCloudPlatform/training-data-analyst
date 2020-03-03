local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["tf-job-operator"];

local tfJobOperator = import "kubeflow/core/tf-job-operator.libsonnet";
local instance = tfJobOperator.new(env, params);
instance.list(instance.all)
