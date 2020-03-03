local experiments = import "experiments.libsonnet";
local exporter = import "export-model.libsonnet";
local k = import "k.libsonnet";
local env = std.extVar("__ksonnet/environments");

local params = std.extVar("__ksonnet/params").components["t2t-code-search-exporter"] +
               experiments["demo-trainer-11-07-dist-sync-gpu"] + {
  name: "demo-export-11-07-dist-sync-gpu",
};

std.prune(k.core.v1.list.new([exporter.parts(params, env).job]))
