local env = std.extVar("__ksonnet/environments");
local overrideParams = std.extVar("__ksonnet/params").components["tfjob-pvc"];

local k = import "k.libsonnet";

local namespace = env.namespace;

local defaultParams = {
  image: "gcr.io/kubeflow-dev/tf-job-issue-summarization:v20180425-e79f888",
  input_data: "/data/github_issues.csv",

  output_model: "/data/model.h5",
  sample_size: "2000000",
  claim_name: "data-pvc",
};

local params = defaultParams + overrideParams;
local name = params.name;

local tfjob = {
  apiVersion: "kubeflow.org/v1beta1",
  kind: "TFJob",
  metadata: {
    name: name,
    namespace: namespace,
  },
  spec: {
    tfReplicaSpecs: {
      Master: {
        replicas: 1,
        template: {
          spec: {
            containers: [
              {
                image: params.image,
                name: "tensorflow",
                volumeMounts: [
                  {
                    name: "data",
                    mountPath: "/data",
                  },
                ],
                command: [
                  "python",
                  "/workdir/train.py",
                  "--sample_size=" + std.toString(params.sample_size),
                  "--input_data=" + params.input_data,
                  "--output_model=" + params.output_model,
                ],
              },
            ],
            volumes: [
              {
                name: "data",
                persistentVolumeClaim: {
                  claimName: params.claim_name,
                },
              },
            ],
            restartPolicy: "OnFailure",
          },
        },  // template
      },
    },
  },
};

k.core.v1.list.new([
  tfjob,
])
