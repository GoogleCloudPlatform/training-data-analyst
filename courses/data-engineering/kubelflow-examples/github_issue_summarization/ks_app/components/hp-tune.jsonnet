// Run an HP Tuning job using Katib
//
// Experimental:
// This is experimental code looking at adding hp tuning using Katib
// to the GitHub issue summarization example. It doesn't work yet.
local env = std.extVar("__ksonnet/environments");
local overrideParams = std.extVar("__ksonnet/params").components["hp-tune"];
local k = import "k.libsonnet";

local params = {
  // Image containing the Katib source code.
  tunerImage: "gcr.io/kubeflow-examples/gh-issue-hp-tuner:v20180629-b14b337-dirty-e6d4f9",
  name: "hp-tune",
  katibEndpoint: "vizier-core:6789",
} + overrideParams;

local tuner = {
  apiVersion: "batch/v1",
  kind: "Job",
  metadata: {
    name: params.name,
    namespace: env.namespace,
  },
  spec: {
    backoffLimit: 4,
    template: {
      spec: {
        containers: [
          {
            command: [
              "/opt/kubeflow/git-issue-summarize-demo",
              "--katib_endpoint=" + params.katibEndpoint,
            ],
            image: params.tunerImage,
            name: "tuner",            
          },
        ],
        restartPolicy: "Never",        
      },
    },
  },
};

std.prune(k.core.v1.list.new([tuner]))
