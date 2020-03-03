// Launch tensorboard instances for multiple experiments
// running as part of the code search demo.
local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["demo-tensorboard"];

local k = import "k.libsonnet";

local namespace = env.namespace;

// A dictionary mapping names for instances to the logDir for those instances
local instances = {
  "demo-trainer-11-05-single-gpu": "gs://code-search-demo/models/20181105-single-gpu",
  "demo-trainer-11-07-dist-sync-gpu": "gs://code-search-demo/models/20181107-dist-sync-gpu",
};

local parts(name, logDir) = {
  service:: {
    apiVersion: "v1",
    kind: "Service",
    metadata: {
      name: name + "-tb",
      namespace: env.namespace,
      annotations: {
        "getambassador.io/config":
          std.join("\n", [
            "---",
            "apiVersion: ambassador/v0",
            "kind:  Mapping",
            "name: " + name + "_mapping",
            "prefix: /tensorboard/" + name + "/",
            "rewrite: /",
            "service: " + name + "-tb." + namespace,
          ]),
      },  //annotations
    },
    spec: {
      ports: [
        {
          name: "http",
          port: 80,
          targetPort: 80,
        },
      ],
      selector: {
        app: "tensorboard",
        "tb-job": name,
      },
    },
  },  // service

  deployment:: {
    apiVersion: "apps/v1beta1",
    kind: "Deployment",
    metadata: {
      name: name + "-tb",
      namespace: env.namespace,
    },
    spec: {
      replicas: 1,
      template: {
        metadata: {
          labels: {
            app: "tensorboard",
            "tb-job": name,
          },
          name: name,
          namespace: namespace,
        },
        spec: {
          containers: [
            {
              command: [
                "/usr/local/bin/tensorboard",
                "--logdir=" + logDir,
                "--port=80",
              ],
              image: params.image,
              name: "tensorboard",
              ports: [
                {
                  containerPort: 80,
                },
              ],
              env: [
                {
                  name: "GOOGLE_APPLICATION_CREDENTIALS",
                  value: "/secret/gcp-credentials/user-gcp-sa.json",
                },
              ],
              volumeMounts: [
                {
                  mountPath: "/secret/gcp-credentials",
                  name: "gcp-credentials",
                },
              ],
            },
          ],

          volumes: [
            {
              name: "gcp-credentials",
              secret: {
                secretName: "user-gcp-sa",
              },
            },
          ],
        },
      },
    },
  },  // deployment

  items: [self.service, self.deployment],
};  // parts

local tbObjects = std.flattenArrays(std.map(function(f) parts(f, instances[f]).items,
                                            std.objectFieldsAll(instances)));

std.prune(k.core.v1.list.new(tbObjects))
