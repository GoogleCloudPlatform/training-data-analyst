// Submit a Dataflow job to compute the code embeddings used a trained model.
local k = import "k.libsonnet";

local experiments = import "experiments.libsonnet";
local lib = import "submit-code-embeddings-job.libsonnet";
local env = std.extVar("__ksonnet/environments");
local baseParams = std.extVar("__ksonnet/params").components["submit-code-embeddings-job"];
local experimentName = baseParams.experiment;
local params = baseParams + experiments[experimentName] + {
  name: experimentName + "-embed-code",
};


std.prune(k.core.v1.list.new([lib.parts(params,env).job]))
