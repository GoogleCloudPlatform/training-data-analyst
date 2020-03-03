// A K8s job to run datagen using T2T.
local k = import "k.libsonnet";
local t2tJob = import "t2t-job.libsonnet";

local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["t2t-code-search-datagen"];

local jobSpec = {
  apiVersion: "batch/v1",
  kind: "Job",
  metadata: {
    name: params.name,
    namespace: env.namespace,
    labels: {
      app: params.name,
    },
  },
  spec: {
    replicas: 1,
    template: {
      metadata: {
        labels: {
          app: params.name,
        },
      },
      spec: {
      	restartPolicy: "OnFailure",
        containers: [
          {
            name: "t2t-datagen",
            image: params.image,
            command:  [
		      "/usr/local/sbin/t2t-entrypoint",
		      "t2t-datagen",
		      "--problem=" + params.problem,
		      "--data_dir=" + params.dataDir,
			],
            env: [
              {
                name: "GOOGLE_APPLICATION_CREDENTIALS",
                value: "/secret/gcp-credentials/user-gcp-sa.json",
              },
            ],
            workingDir: "/src",            
            volumeMounts: [
              {
                mountPath: "/secret/gcp-credentials",
                name: "gcp-credentials",
              },
            ],  //volumeMounts
          },
        ],  // containers
        volumes: [
          {
            name: "gcp-credentials",
            secret: {
              secretName: "user-gcp-sa",
            },
          },
        ],
      },  // spec
    },
  },
};

std.prune(k.core.v1.list.new([jobSpec]))
