{
  parts(params, env):: [
    {
      apiVersion: "v1",
      kind: "Service",
      metadata: {
        name: "kubeflow-demo-ui",
        namespace: env.namespace,
        annotations: {
          "getambassador.io/config":
            std.join("\n", [
              "---",
              "apiVersion: ambassador/v0",
              "kind: Mapping",
              "name: kubeflow_demo_ui",
              "prefix: /kubeflow_demo/",
              "rewrite: /",
              "service: kubeflow-demo-ui:80",
            ]),
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
          app: "kubeflow-demo-ui",
        },
        type: "ClusterIP",
      },
    },
    {
      apiVersion: "apps/v1beta1",
      kind: "Deployment",
      metadata: {
        name: "kubeflow-demo-ui",
        namespace: env.namespace,
      },
      spec: {
        replicas: 1,
        template: {
          metadata: {
            labels: {
              app: "kubeflow-demo-ui",
            },
          },
          spec: {
            containers: [
              {
		args: [
		  "app.py",
		  "--model_url",
		  "http://serving:8000/model/serving:predict",
		  "--data_dir",
		  "gs://kubeflow-demo-base/featurization/yelp-data-1000000",
		],
		command: [
		  "python",
		],
                image: params.image,
                name: "kubeflow-demo-ui",
                ports: [
                  {
                    containerPort: 80,
                  },
                ],
	        "env": [
                  {
                    name: "GOOGLE_APPLICATION_CREDENTIALS",
                    value: "/secret/gcp-credentials/key.json"
                  },
                ],
                "volumeMounts": [
                  {
                    mountPath: "/secret/gcp-credentials",
                    name: "gcp-credentials",
                  },
                ],
              },
            ],
            "imagePullSecrets": [
              {
                name: "gcp-registry-credentials",
              },
            ],
            "volumes": [
              {
                name: "gcp-credentials",
                secret: {
                  secretName: "gcp-credentials",
                },
              },
            ],
          },
        },
      },
    },
  ],
}
