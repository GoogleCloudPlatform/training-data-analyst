local k = import "k.libsonnet";

local env = std.extVar("__ksonnet/environments");
local baseParams = std.extVar("__ksonnet/params").components["search-index-creator"];
local experiments = import "experiments.libsonnet";

local experimentName = baseParams.experiment;
local jobNameSuffix = baseParams.jobNameSuffix;
local params = baseParams + experiments[experimentName] + {
  name: experimentName + "-create-search-index-" + jobNameSuffix,
};

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
    backoffLimit: 0,
    template: {
      metadata: {
        labels: {
          app: params.name,
        },
      },
      spec: {
        // Don't restart because all the job should do is launch the Dataflow job.
        restartPolicy: "Never",
        containers: [
          {
            name: "dataflow",
            image: params.image,
            command: [
		          "python",
		          "-m",
		          "code_search.nmslib.cli.create_search_index",
		          "--data_dir=" + params.functionEmbeddingsDir,
		          "--lookup_file=" + params.lookupFile,
		          "--index_file=" + params.indexFile,
		        ],
            env: [
              {
                name: "GOOGLE_APPLICATION_CREDENTIALS",
                value: "/secret/gcp-credentials/user-gcp-sa.json",
              },
            ],
            // Creating the index requires a lot of memory.
            resources: {
            	requests: {
			        memory: "32Gi"
			 	},
			 	limits: {
			        memory: "100Gi"
			 	},
			},
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

std.prune(k.core.v1.list.new(jobSpec))
