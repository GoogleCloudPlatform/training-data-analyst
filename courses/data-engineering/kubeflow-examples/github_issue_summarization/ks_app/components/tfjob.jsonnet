local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["tfjob"];

local k = import "k.libsonnet";

local name = params.name;
local namespace = env.namespace;

local tfjob = {
  apiVersion: "kubeflow.org/v1",
  kind: "TFJob",
  metadata: {
    name: name,
    namespace: namespace,
  },
  spec: {
    tTLSecondsAfterFinished: 60 * 60 * 24 * 7,
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
                    name: "gcp-credentials",
                    mountPath: "/secret/gcp-credentials",
                    readOnly: true,
                  },
                ],
                command: [
                  "python",
                  "train.py",
                  "--num_epochs=" + std.toString(params.num_epochs),
                  "--sample_size=" + std.toString(params.sample_size),
                  "--input_data=" + params.input_data,
                  "--output_model=" + params.output_model,
                ],
                workingDir: "/issues",
                env: [
                  {
                    name: "GOOGLE_APPLICATION_CREDENTIALS",
                    value: "/secret/gcp-credentials/" + params.gcpSecretFile,
                  },
                ],
              },
            ],
            volumes: [
              {
                name: "gcp-credentials",
                secret: {
                  secretName: params.gcpSecretName,
                },
              },
            ],
            restartPolicy: "OnFailure",
          },  // spec
        },  // template
      },  // master
    },  // tfReplicaSpecs
  },  // spec
};

k.core.v1.list.new([
  tfjob,
])

