local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["t2ttpu"];

local k = import "k.libsonnet";

local name = params.name;
local namespace = env.namespace;

local updatedParams = {
      cloud: "gke",

      dataDir: "gs://kubeflow-demo-base/featurization/yelp-data",
      usrDir: "./yelp_sentiment",
      problem: "yelp_sentiment",

      model: "transformer_encoder",
      hparams: "transformer_yelp_sentiment",
      hparamsSet: "transformer_yelp_sentiment",

      outputGCSPath: "gs://kubeflow-demo-base/training/yelp-model-TPU",

      cpuImage: "gcr.io/kubeflow-demo-base/kubeflow-yelp-demo-cpu:latest",
      gpuImage: "gcr.io/kubeflow-demo-base/kubeflow-yelp-demo-gpu:latest",

      trainSteps: 1000,
      evalSteps: 10,

      tpus: 8,

      jobName: "t2ttpu",

      tpuEndpoint: "$(KUBE_GOOGLE_CLOUD_TPU_ENDPOINTS)",
} + params;

local cloud = std.toString(updatedParams.cloud);

local tfjob = {
  apiVersion: "kubeflow.org/v1alpha2",
  kind: "TFJob",
  metadata: {
    name: updatedParams.jobName,
    namespace: namespace,
  },
  spec: {
    tfReplicaSpecs: {
      Master: {
        replicas: 1,
        template: {
          metadata: {
            annotations: {
              "tf-version.cloud-tpus.google.com": "1.9",
            },
          },
          spec: {
            containers: [
              {
                args: [
                  "--model=" + updatedParams.model,
                  "--hparams_set=" + updatedParams.hparamsSet,
                  "--problem=" + updatedParams.problem,
	          "--t2t_usr_dir=" + updatedParams.usrDir,
                  "--train_steps=" + updatedParams.trainSteps,
                  "--eval_steps=" + updatedParams.evalSteps,
                  "--data_dir=" + updatedParams.dataDir,
                  "--output_dir=" + updatedParams.outputGCSPath,
                  "--use_tpu",
                  "--master=" + updatedParams.tpuEndpoint,
                ],
                command: [
                  "t2t-trainer",
                ],
                image: updatedParams.cpuImage,
                name: "tensorflow",
                resources: {
                  "limits": {
                    "cloud-tpus.google.com/v2": updatedParams.tpus,
                  },
                  requests: {
                    memory: "1Gi",
                  },
                },
              },
            ],
            restartPolicy: "OnFailure",
          }, // spec
        }, // template
      }, // Master
    }, // tfReplicaSpecs
  }, // Spec
}; // tfJob

k.core.v1.list.new([
  tfjob,
])

