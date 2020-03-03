local exporter = import "export-model.libsonnet";
local k = import "k.libsonnet";

local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["t2t-code-search-exporter"];

std.prune(k.core.v1.list.new([exporter.parts(params, env).job]))
