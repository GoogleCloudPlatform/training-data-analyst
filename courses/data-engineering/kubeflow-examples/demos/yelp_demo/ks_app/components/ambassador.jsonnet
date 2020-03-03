local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components.ambassador;

local ambassador = import "kubeflow/core/ambassador.libsonnet";
local instance = ambassador.new(env, params);
instance.list(instance.all)
