// This component is specific to the code search demo effort.
// This component trains a model using the tiny hparams.
// Uses synchronous training.
local k = import "k.libsonnet";
local t2tJob = import "t2t-job.libsonnet";

local env = std.extVar("__ksonnet/environments");

// Note we are reusing the parameters for t2t-code-search-trainer and then explicitly overriding them.
local params = std.extVar("__ksonnet/params").components["t2t-code-search-trainer"] {
  name: "demo-trainer-11-07-dist-sync-gpu",
  outputDir: "gs://code-search-demo/models/20181107-dist-sync-gpu",
  train_steps: 200000,
  eval_steps: 100,
  hparams_set: "transformer_base",
  numWorkerGpu: 1,
  numChief: 1,
  numWorker: 8,
};
std.prune(k.core.v1.list.new([t2tJob.parts(params, env).jobDistSync]))
