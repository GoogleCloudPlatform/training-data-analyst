{
  parts(params, env): {
    local name = params.name,
    local namespace = env.namespace,

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
    },

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
                  "--logdir=" + params.logDir,
                  "--port=80",
                ],
                image: params.image,
                name: "tensorboard",
                ports: [
                  {
                    containerPort: 80,
                  },
                ],
                // "livenessProbe": {
                //    "httpGet": {
                //      "path": "/",
                //      "port": 80
                //    },
                //    "initialDelaySeconds": 15,
                //    "periodSeconds": 3
                //  }
                volumeMounts: [
                  {
                    name: "gcp-credentials",
                    mountPath: "/secret/gcp-credentials",
                    readOnly: true,
                  },
                  {
                    name: "shared-fs",
                    mountPath: params.mountPath,
                  },
                ],
              },
            ],
            volumes: [
              {
                name: "gcp-credentials",
                secret: {
                  secretName: params.gcpSecretName,
                },
              },
              {
                name: "shared-fs",
                persistentVolumeClaim: {
                  claimName: params.pvc,
                },
              },
            ],  //volumes
          },
        },
      },
    },
  },
}
