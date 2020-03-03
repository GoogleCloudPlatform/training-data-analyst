local k = import "k.libsonnet";
local t2tJob = import "t2t-job.libsonnet";

local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["t2t-code-search-trainer"];
std.prune(k.core.v1.list.new([t2tJob.parts(params, env).job]))
