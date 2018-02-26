local params = std.extVar("__ksonnet/params").components["kubeflow-core"];
local k = import 'k.libsonnet';
local all = import "kubeflow/core/all.libsonnet";

std.prune(k.core.v1.list.new(all.parts(params).all))
