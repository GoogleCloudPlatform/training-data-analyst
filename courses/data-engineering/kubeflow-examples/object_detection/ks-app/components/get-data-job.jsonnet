local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["get-data-job"];

local k = import "k.libsonnet";

local getDataJob(namespace, name, pvc, url, mountPath) = {
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
              name: "get-data",
              image: "inutano/wget",
              imagePullPolicy: "IfNotPresent",
              command: ["wget",  url, "-P", mountPath, "--no-check-certificate"],
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
  getDataJob(env.namespace, params.name + "-dataset", params.pvc, params.urlData, params.mountPath),
  getDataJob(env.namespace, params.name + "-annotations", params.pvc, params.urlAnnotations, params.mountPath),
  getDataJob(env.namespace, params.name + "-model", params.pvc, params.urlModel, params.mountPath),
  getDataJob(env.namespace, params.name + "-config", params.pvc, params.urlPipelineConfig, params.mountPath)]))
