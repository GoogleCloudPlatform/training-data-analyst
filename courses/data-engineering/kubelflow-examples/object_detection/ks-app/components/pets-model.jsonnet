local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["pets-model"];

local k = import "k.libsonnet";

// ksonnet appears to require name be a parameter of the prototype which is why we handle it differently.
local name = params.name;

// updatedParams includes the namespace from env by default.
// We can override namespace in params if needed
local updatedParams = env + params;

local tfServingBase = import "kubeflow/tf-serving/tf-serving.libsonnet";
local tfServing = tfServingBase {
  // Override parameters with user supplied parameters.
  params+: updatedParams {
    name: name,
  },
};

std.prune(k.core.v1.list.new(tfServing.components))
