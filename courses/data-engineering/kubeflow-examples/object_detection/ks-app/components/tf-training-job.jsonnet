local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["tf-training-job"];

local k = import "k.libsonnet";

local tfJobCpu = {
  apiVersion: params.tfjobApiVersion,
  kind: "TFJob",
  metadata: {
    name: params.name,
    namespace: env.namespace,
  },
  spec: {
    tfReplicaSpecs: {
      Worker: {
        replicas: params.numWorkers,
        template: {
          spec: {
            containers: [
              {
                workingDir: "/models",
                command: [
                  "python",
                  "research/object_detection/legacy/train.py",
                ],
                args:[
                  "--alsologtostderr",
                  "--pipeline_config_path=" + params.pipelineConfigPath,
                  "--train_dir=" + params.trainDir,
                ],
                image: params.image,
                imagePullPolicy: "Always",
                name: "tensorflow",
                [if params.numGpu > 0 then "resources"] : {
                  limits:{
                    "nvidia.com/gpu": params.numGpu,
                  },
                },
                volumeMounts: [{
                  mountPath: params.mountPath,
                  name: "pets-data",
                },],
              },
            ],
            volumes: [{
                name: "pets-data",
                persistentVolumeClaim: {
                  claimName: params.pvc,
                },
            },],
            restartPolicy: "OnFailure",
          },
        },
      },
      Master: {
        replicas: 1,
        template: {
          spec: {
            containers: [
              {
                workingDir: "/models",
                command: [
                  "python",
                  "research/object_detection/legacy/train.py",
                ],
                args:[
                  "--alsologtostderr",
                  "--pipeline_config_path=" + params.pipelineConfigPath,
                  "--train_dir=" + params.trainDir,
                ],
                image: params.image,
                imagePullPolicy: "Always",
                name: "tensorflow",
                [if params.numGpu > 0 then "resources"] : {
                  limits:{
                    "nvidia.com/gpu": params.numGpu,
                  },
                },
                volumeMounts: [{
                  mountPath: params.mountPath,
                  name: "pets-data",
                },],
              },
            ],
            volumes: [{
                name: "pets-data",
                persistentVolumeClaim: {
                  claimName: params.pvc,
                },
            },],
            restartPolicy: "OnFailure",
          },
        },
      },
      Ps: {
        replicas: params.numPs,
        template: {
          spec: {
            containers: [
              {
                workingDir: "/models",
                command: [
                  "python",
                  "research/object_detection/legacy/train.py",
                ],
                args:[
                  "--alsologtostderr",
                  "--pipeline_config_path=" + params.pipelineConfigPath,
                  "--train_dir=" + params.trainDir,
                ],
                image: params.image,
                imagePullPolicy: "Always",
                name: "tensorflow",
                [if params.numGpu > 0 then "resources"] : {
                  limits:{
                    "nvidia.com/gpu": params.numGpu,
                  },
                },
                volumeMounts: [{
                  mountPath: params.mountPath,
                  name: "pets-data",
                },],
              },
            ],
            volumes: [{
                name: "pets-data",
                persistentVolumeClaim: {
                  claimName: params.pvc,
                },
            },],
            restartPolicy: "OnFailure",
          },
        },
        tfReplicaType: "PS",
      },
    },
  },
};

k.core.v1.list.new([
  tfJobCpu,
])
