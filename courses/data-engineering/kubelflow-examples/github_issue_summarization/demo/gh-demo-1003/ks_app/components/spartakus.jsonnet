local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components.spartakus;

local spartakus = import "kubeflow/core/spartakus.libsonnet";
local instance = spartakus.new(env, params);
instance.list(instance.all)
