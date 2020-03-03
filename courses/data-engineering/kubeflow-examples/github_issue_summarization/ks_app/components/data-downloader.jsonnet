// Run a job to download the data to a persistent volume.
//
local env = std.extVar("__ksonnet/environments");
local overrideParams = std.extVar("__ksonnet/params").components["data-pvc"];
local k = import "k.libsonnet";


local script = importstr "download_data.sh";

local scriptConfigMap = {
  apiVersion: "v1",
  kind: "ConfigMap",
  metadata: {
    name: "downloader",
    namespace: env.namespace,
  },

  data: {
    "download_data.sh": script,
  },
};

local params = {
  // Default location for the data. Should be a directory on the PVC.
  dataPath: "/data",
  dataUrl: "https://storage.googleapis.com/kubeflow-examples/github-issue-summarization-data/github-issues.zip",
  pvcName: "data-pvc",
} + overrideParams;

local downLoader = {
  apiVersion: "batch/v1",
  kind: "Job",
  metadata: {
    name: "download-data",
    namespace: env.namespace,
  },
  spec: {
    backoffLimit: 4,
    template: {
      spec: {
        containers: [
          {
            command: [
              "/bin/ash",
              "/scripts/download_data.sh",
              params.dataUrl,
              params.dataPath,
            ],
            image: "busybox",
            name: "downloader",
            volumeMounts: [
              {
                name: "script",
                mountPath: "/scripts",
              },
              {
                name: "data",
                mountPath: "/data",
              },
            ],
          },
        ],
        restartPolicy: "Never",
        volumes: [
          {
            name: "script",
            configMap: {
              name: "downloader",
            },
          },
          {
            name: "data",
            persistentVolumeClaim: {
              claimName: params.pvcName,
            },
          },
        ],
      },
    },
  },
};

std.prune(k.core.v1.list.new([downLoader, scriptConfigMap]))
