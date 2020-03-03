local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["issue-summarization-ui"];
local k = import "k.libsonnet";
local deployment = k.apps.v1beta1.deployment;
local container = k.apps.v1beta1.deployment.mixin.spec.template.spec.containersType;
local containerPort = container.portsType;
local service = k.core.v1.service;
local servicePort = k.core.v1.service.mixin.spec.portsType;

local targetPort = params.containerPort;
local labels = { app: params.name };

local appService = {
  apiVersion: "v1",
  kind: "Service",
  metadata: {
    name: "issue-summarization-ui",
    namespace: env.namespace,
    annotations: {
      "getambassador.io/config": "---\napiVersion: ambassador/v0\nkind:  Mapping\nname:  issue_summarization_ui\nprefix: /issue-summarization/\nrewrite: /\nservice: issue-summarization-ui:80\n",
    },
  },
  spec: {
    ports: [
      {
        port: 80,
        targetPort: 80,
      },
    ],
    selector: {
      app: "issue-summarization-ui",
    },
    type: params.type,
  },
};

local appDeployment = {
  apiVersion: "apps/v1beta1",
  kind: "Deployment",
  metadata: {
    name: "issue-summarization-ui",
    namespace: env.namespace,
  },
  spec: {
    replicas: 1,
    template: {
      metadata: {
        labels: {
          app: "issue-summarization-ui",
        },
      },
      spec: {
        containers: [
          {
            image: "gcr.io/kubeflow-examples/issue-summarization-ui:v20181004-v0.2-10-g997f5bd-dirty-c1abe8",
            command: [
              "python",
              "app.py",
              "--model_url=http://issue-summarization." + env.namespace + ".svc.cluster.local:8000/api/v0.1/predictions",
            ],
            env: [
              {
                name: "GITHUB_TOKEN",
                valueFrom: {
                  secretKeyRef: {
                    name: "github-token",
                    key: "github-token",
                  },
                },
              },
            ],
            name: "issue-summarization-ui",
            ports: [
              {
                containerPort: 80,
              },
            ],
          },
        ],
        volumes: [
          {
            name: "github-token",
            secret: {
              secretName: "github-token",
            },
          },
        ],  // volumes
      },
    },
  },
};

// Ingress to expose the demo at gh-demo.kubeflow.org
local uiIngress = {
  apiVersion: "extensions/v1beta1",
  kind: "Ingress",
  metadata: {
    name: params.name,
    namespace: env.namespace,
    annotations: {
      "kubernetes.io/ingress.global-static-ip-name": "gh-demo-kubeflow-org",
    },
  },
  spec: {
    backend: {
      serviceName: params.name,
      servicePort: targetPort,
    },
  },
};  // uiIngress

k.core.v1.list.new([appService, appDeployment, uiIngress])
