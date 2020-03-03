local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["decompress-data-job"];

local k = import "k.libsonnet";

local decompressDataJob(namespace, name, pvc, pathToFile, mountPath) = {
      apiVersion: "batch/v1",
      kind: "Job",
      metadata: {
        name: name,
        namespace: namespace,
      },
      spec: {
        template: {
          spec: {
            containers: [{
              name: "decompress-data",
              image: "ubuntu:16.04",
              imagePullPolicy: "IfNotPresent",
              command: ["tar", "--no-same-owner", "-xzvf",  pathToFile, "-C", mountPath],
              volumeMounts: [{
                  mountPath: mountPath,
                  name: "pets-data",
              },],
              },],
            volumes: [{
                name: "pets-data",
                persistentVolumeClaim: {
                  claimName: pvc,
                },
            },],
            restartPolicy: "Never",
          },
        },
        backoffLimit: 4,
      },
    };

std.prune(k.core.v1.list.new([
decompressDataJob(env.namespace, params.name + "-dataset", params.pvc, params.pathToDataset, params.mountPath),
decompressDataJob(env.namespace, params.name + "-annotations", params.pvc, params.pathToAnnotations, params.mountPath),
decompressDataJob(env.namespace, params.name + "-model", params.pvc, params.pathToModel, params.mountPath)]))