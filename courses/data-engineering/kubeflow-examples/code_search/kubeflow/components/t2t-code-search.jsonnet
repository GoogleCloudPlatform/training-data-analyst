// NOTE: This is only a dummy to allow `ks param set`. DONOT use.
// TODO(jlew): We should get rid of this and use experiments.jsonnet and globals
// to define common parameters; see https://github.com/kubeflow/examples/issues/308.
local k = import "k.libsonnet";
local t2tJob = import "t2t-job.libsonnet";

local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["t2t-code-search"];

std.prune(k.core.v1.list.new([t2tJob.parts(params, env).job]))
