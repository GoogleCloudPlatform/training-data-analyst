// Create a PVC to store the data.
// This PVC can be used if you don't have access to an object store
// but your cluster has a default storage class
local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["data-pvc"];
local k = import "k.libsonnet";

local pvc = {
  apiVersion: "v1",
  kind: "PersistentVolumeClaim",
  metadata: {
    name: "data-pvc",
    namespace: env.namespace,
  },
  spec: {
    accessModes: [
      "ReadWriteOnce",
    ],
    resources: {
      requests: {
        storage: "10Gi",
      },
    },
  },
};

std.prune(k.core.v1.list.new([pvc]))
