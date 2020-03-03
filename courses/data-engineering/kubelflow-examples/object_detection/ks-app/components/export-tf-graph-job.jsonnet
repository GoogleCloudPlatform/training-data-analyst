local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["export-tf-graph-job"];

local k = import "k.libsonnet";
local obj_detection = import "obj-detection.libsonnet";

local namespace = env.namespace;
local jobName = params.name;
local pvc = params.pvc;
local mountPath = params.mountPath;
local image = params.image;
local command = params.command;
local args = params.args;

local exportTfGraphJob = {
apiVersion: "batch/v1",
  kind: "Job",
  metadata: {
    name: params.name,
    namespace: env.namespace,
  },
  spec: {
    template: {
      spec: {
        containers: [{
          name: "export-graph",
          image: params.image,
          imagePullPolicy: "IfNotPresent",
          command: ['python', '/models/research/object_detection/export_inference_graph.py'],
          args: ['--input_type=' + params.inputType,
                 '--pipeline_config_path=' + params.pipelineConfigPath,
                 '--trained_checkpoint_prefix=' + params.trainedCheckpoint,
                 '--output_directory=' + params.outputDir],
          volumeMounts: [{
              mountPath: params.mountPath,
              name: "pets-data",
          },],
          },],
        volumes: [{
            name: "pets-data",
            persistentVolumeClaim: {
              claimName: params.pvc,
            },
        },],
        restartPolicy: "Never",
      },
    },
    backoffLimit: 4,
  },
};

std.prune(k.core.v1.list.new([exportTfGraphJob,]))