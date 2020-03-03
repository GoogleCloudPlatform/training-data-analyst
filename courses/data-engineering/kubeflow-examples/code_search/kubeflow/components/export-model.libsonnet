{
  parts(params, env):: {
    job: {
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
                name: "exporter",
                image: params.image,
                command: [
                  "t2t-exporter",
                  "--problem=" + params.problem,
                  "--data_dir=" + params.dataDir,
                  // TODO(kubeflow/examples#331): t2t-exporter should have flags --export and --export_dir
                  // which allow us to control the location of the exported model.
                  "--output_dir=" + params.outputDir,
                  "--model=" + params.model,
                  "--hparams_set=" + params.hparams_set,
                  // Need to import the problems.
                  "--t2t_usr_dir=/src/code_search/t2t",
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
    },
  },  // parts
}
