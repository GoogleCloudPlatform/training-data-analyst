local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["t2tgpu"];

local k = import "k.libsonnet";

local name = params.name;
local namespace = env.namespace;

local updatedParams = {
  cloud: "gke",
  sync: "0",

  dataDir: "gs://kubeflow-demo-base/featurization/yelp-data",
  usrDir: "./yelp_sentiment",
  problem: "yelp_sentiment",

  model: "transformer_encoder",
  hparams: "transformer_yelp_sentiment",
  hparamsSet: "transformer_yelp_sentiment",

  outputGCSPath: "gs://kubeflow-demo-base/kubeflow-demo-base-demo/GPU/training/yelp-model",

  gpuImage: "gcr.io/kubeflow-demo-base/kubeflow-yelp-demo-gpu:latest",
  cpuImage: "gcr.io/kubeflow-demo-base/kubeflow-yelp-demo-cpu:latest",

  trainSteps: 1000,
  evalSteps: 10,

  psGpu: 0,
  workerGpu: 1,

  workers: 3,
  masters: 1,
  ps: 1,

  jobName: "t2tgpu",
} + params;

local baseCommand = [
  "bash",
  "/home/jovyan/yelp_sentiment/worker_launcher.sh",
  "--train_steps=" + updatedParams.trainSteps,
  "--hparams_set=" + updatedParams.hparams,
  "--model=" + updatedParams.model,
  "--problem=" + updatedParams.problem,
  "--t2t_usr_dir=" + updatedParams.usrDir,
  "--data_dir=" + updatedParams.dataDir,
  "--output_dir=" + updatedParams.outputGCSPath,
];

local psCommand = baseCommand + [
  "--schedule=run_std_server",
];

local totalWorkerReplicas = updatedParams.workers + updatedParams.masters;

local workerBaseCommand = baseCommand + [
  "--schedule=train",
  "--sync=" + updatedParams.sync,
  "--ps_gpu=" + updatedParams.psGpu,
  "--worker_gpu=" + updatedParams.workerGpu,
  "--worker_replicas=" + totalWorkerReplicas,
  "--ps_replicas=" + updatedParams.ps,
  "--eval_steps=" + updatedParams.evalSteps,
];

local workerCommand = workerBaseCommand + [
  "--worker_job=/job:worker",
];

local masterCommand = workerBaseCommand + [
  "--worker_job=/job:master",
];

local gpuResources = {
  limits: {
    "nvidia.com/gpu": updatedParams.workerGpu,
  },
};

local cloud = std.toString(updatedParams.cloud);

local baseEnv = [
  {
    name: "PYTHONPATH",
    value: "/home/jovyan",
  },
];

local nonGkeEnv = baseEnv + [
  {
    name: "GOOGLE_APPLICATION_CREDENTIALS",
    value: "/secret/gcp-credentials/key.json"
  },
];

local nonGkeVolumes = [
  {
    name: "gcp-credentials",
    secret: {
      secretName: "gcp-credentials",
    },
  },
];

local nonGkeImagePullSecrets = [
  {
    name: "gcp-registry-credentials",
  },
];

local nonGkeVolumeMounts = [
  {
    mountPath: "/secret/gcp-credentials",
    name: "gcp-credentials",
  },
];

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
              spec: {
                containers: [
                  {
                    command: masterCommand,
                    env: if cloud != "gke" then nonGkeEnv else baseEnv,
                    image: if updatedParams.workerGpu > 0 then updatedParams.gpuImage else updatedParams.cpuImage,
                    name: "tensorflow",
                    [if updatedParams.workerGpu > 0 then "resources"]: gpuResources,
                    [if cloud != "gke" then "volumeMounts"]: nonGkeVolumeMounts,
                  },
                ],
                [if cloud != "gke" then "imagePullSecrets"]: nonGkeImagePullSecrets,
                restartPolicy: "OnFailure",
                [if cloud != "gke" then "volumes"]: nonGkeVolumes,
              },
            },
      }, // Master

      Worker: {
        replicas: updatedParams.workers,
        template: {
              spec: {
                containers: [
                  {
                    command: workerCommand,
                    env: if cloud != "gke" then nonGkeEnv else baseEnv,
                    image: if updatedParams.workerGpu > 0 then updatedParams.gpuImage else updatedParams.cpuImage,
                    name: "tensorflow",
                    [if updatedParams.workerGpu > 0 then "resources"]: gpuResources,
                    [if cloud != "gke" then "volumeMounts"]: nonGkeVolumeMounts,
                  },
                ],
                [if cloud != "gke" then "imagePullSecrets"]: nonGkeImagePullSecrets,
                restartPolicy: "OnFailure",
                [if cloud != "gke" then "volumes"]: nonGkeVolumes,
              },
            },
      }, // Worker
      Ps: {
        replicas: updatedParams.ps,
        template: {
              spec: {
                containers: [
                  {
                    command: psCommand,
                    env: if cloud != "gke" then nonGkeEnv else baseEnv,
                    image: updatedParams.cpuImage,
                    name: "tensorflow",
                    [if cloud != "gke" then "volumeMounts"]: nonGkeVolumeMounts,
                  },
                ],
                [if cloud != "gke" then "imagePullSecrets"]: nonGkeImagePullSecrets,
                restartPolicy: "OnFailure",
                [if cloud != "gke" then "volumes"]: nonGkeVolumes,
              },
            }, 
    }, // Ps    
  }, // tfReplicaSpecs
 }, // Spec
}; // tfJob

k.core.v1.list.new([
  tfjob,
])



