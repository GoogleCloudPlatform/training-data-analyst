local k = import "k.libsonnet";

local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["search-index-server"];
local oldparams = {
  name: "test",
  lookupFile: null,
  indexFile: null,
  servingUrl: "http://t2t-code-search.kubeflow:8500/v1/models/t2t-code-search:predict",
  // 1 replica is convenient for debugging but we should bump after debugging.
  replicas: 1,
  image: "gcr.io/kubeflow-examples/code-search-ui:v20181122-dc0e646-dirty-043a63",
  problem: "someproble",
  dataDir: "datadir",
};

local deploymentSpec = {
  apiVersion: "extensions/v1beta1",
  kind: "Deployment",
  metadata: {
    name: params.name,
    namespace: env.namespace,
    labels: {
      app: params.name,
    },
  },
  spec: {
    replicas: params.replicas,
    selector: {
      matchLabels: {
        app: params.name,
      },
    },
    template: {
      metadata: {
        labels: {
          app: params.name,
        },
      },
      spec: {
        containers: [
          {
            name: params.name,
            image: params.image,
            command: [
              "python",
              "-m",
              "code_search.nmslib.cli.start_search_server",
              "--problem=" + params.problem,
              "--data_dir=" + params.dataDir,
              "--lookup_file=" + params.lookupFile,
              "--index_file=" + params.indexFile,
              "--serving_url=" + params.servingUrl,
            ],
            ports: [
              {
                containerPort: 8008,
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
  },  // spec
};

local service = {
  apiVersion: "v1",
  kind: "Service",
  metadata: {
    labels: {
      app: params.name,
    },
    name: params.name,
    namespace: env.namespace,
    annotations: {
      "getambassador.io/config":
        std.join("\n", [
          "---",
          "apiVersion: ambassador/v0",
          "kind: Mapping",
          "name: http-mapping-" + params.name,
          "prefix: /code-search/",
          "rewrite: /",
          "method: GET",
          "service: " + params.name + "." + env.namespace + ":8008",
        ]),
    },
  },
  spec: {
    type: "ClusterIP",
    selector: {
      app: params.name,
    },
    ports: [
      {
        name: "nmslib-serve-http",
        port: 8008,
        targetPort: 8008,
      },
    ],
  },
};

std.prune(k.core.v1.list.new([deploymentSpec, service]))
