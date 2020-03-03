local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components.pipeline;

local k = import "k.libsonnet";
local all = import "kubeflow/pipeline/all.libsonnet";

std.prune(k.core.v1.list.new(all.parts(env, params).all))
