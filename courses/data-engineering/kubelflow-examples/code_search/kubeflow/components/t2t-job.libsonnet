local baseParams = std.extVar("__ksonnet/params").components["t2t-job"];

{
  getTrainerCmd(params):: {
    local trainer = [
      // t2t-entrypoint is a wrapper that parses TF_CONFIG
      "/usr/local/sbin/t2t-entrypoint",
      "t2t-trainer",
      "--problem=" + params.problem,
      "--model=" + params.model,
      "--hparams_set=" + params.hparams_set,
      "--data_dir=" + params.dataDir,
      "--output_dir=" + params.outputDir,
      "--train_steps=" + std.toString(params.train_steps),
      "--eval_steps=" + std.toString(params.eval_steps),
      "--t2t_usr_dir=/app/code_search/t2t",
    ],

    worker: trainer,

    worker_dist: trainer + [
      "--schedule=train",
      "--ps_gpu=" + std.toString(params.numPsGpu),
      "--worker_gpu=" + std.toString(params.numWorkerGpu),
      "--worker_replicas=" + std.toString(params.numWorker),
      "--ps_replicas=" + std.toString(params.numPs),
      "--eval_steps=" + std.toString(params.eval_steps),
      "--worker_job=/job:worker",
      // set address of ps
      "--ps_job=/job:ps",
    ],

    ps: trainer + [
      "--schedule=run_std_server",
      "--ps_job=/job:ps",
    ],
  },

  tfJobReplica(number, command, image, numGpus=0, imagePullSecrets=[], env=[], volumes=[], volumeMounts=[])::
    local containerSpec = {
      image: image,
      name: "tensorflow",
      command: command,
      resources: {
        limits: {
          [if numGpus > 0 then "nvidia.com/gpu"]: numGpus,
        },
      },
      [if std.length(env) > 0 then "env"]: env,
      [if std.length(volumeMounts) > 0 then "volumeMounts"]: volumeMounts,
    };
    {
      replicas: number,
      template: {
        spec: {
          containers: [containerSpec],
          [if std.length(imagePullSecrets) > 0 then "imagePullSecrets"]: imagePullSecrets,
          [if std.length(volumes) > 0 then "volumes"]: volumes,
          // restartPolicy: "OnFailure",
        },
      },
    },

  parts(newParams, env):: {
    local params = baseParams + newParams,

    local psImage = if params.numPsGpu > 0 then params.imageGpu else params.image,
    local workerImage = if params.numWorkerGpu > 0 then params.imageGpu else params.image,
    local workerEnv = [
      {
        name: "GOOGLE_APPLICATION_CREDENTIALS",
        value: "/secret/gcp-credentials/user-gcp-sa.json",
      },
    ],
    local workerVolumes = [
      {
        name: "gcp-credentials",
        secret: {
          secretName: "user-gcp-sa",
        },
      },
    ],
    local workerVolumeMounts = [
      {
        mountPath: "/secret/gcp-credentials",
        name: "gcp-credentials",
      },
    ],

    local cmd = $.getTrainerCmd(params),
    local workerCmd = if params.jobType == "exporter" then $.getExporterCmd(params)
    else
      if params.numWorker == 0 then
        cmd.worker
      else
        cmd.worker_dist,

    // Run a distributed job in synchronous mode.
    // https://github.com/tensorflow/tensor2tensor/blob/master/docs/distributed_training.md
    jobDistSync:: {
      local tfPort = 2222,
      local chiefCommand = [
        "t2t-trainer",
        "--problem=" + params.problem,
        "--model=" + params.model,
        "--hparams_set=" + params.hparams_set,
        "--data_dir=" + params.dataDir,
        "--output_dir=" + params.outputDir,
        "--train_steps=" + std.toString(params.train_steps),
        "--eval_steps=" + std.toString(params.eval_steps),
        "--t2t_usr_dir=/app/code_search/t2t",

        // Chief runs training
        "--schedule=train",

        // See T2T distributed training docs
        // https://github.com/tensorflow/tensor2tensor/blob/
        // In synchronous training the ps are actually used
        // as the
        "--sync",
        "--ps_replicas=" + std.toString(params.numWorker),
        "--ps_gpu=" + std.toString(params.numWorkerGpu),
        "--worker_gpu=0",
        "--worker_replicas=1",

        // We need to know the port configured by TF in order to
        // set the master flag. It would be be better to do this
        // in an entrypoint script and get the value from TF_CONFIG
        // so we don't have to manually configure the port to match what TFJob
        // uses.
        "--master=grpc://chief:" + std.toString(tfPort),
        "--worker_job=/job:chief",
      ],

      // In synchronous mode workers just run standard servers.
      local workerSyncCmd = [
        // Need to give fluentd time to collect logs in case of failures
        "/usr/local/sbin/run_and_wait.sh",
        "t2t-trainer",
        "--schedule=run_std_server",
        // "--hp_std_server_protocol=grpc",

        // If we don't set hparams std_server_protocol isn't set.
        "--model=" + params.model,
        "--hparams_set=" + params.hparams_set,
      ],

      local stdServerContainer(numGpu) = {
        image: params.imageGpu,
        name: "tensorflow-server",
        command: ["python", "-m", "code_search.t2t.start_std_server"],
        [if numGpu > 0 then "resources"]: {
          limits: {
            "nvidia.com/gpu": 1,
          },
        },
      },

      apiVersion: "kubeflow.org/v1alpha2",
      kind: "TFJob",
      metadata: {
        name: params.name,
        namespace: env.namespace,
      },
      spec: {
        tfReplicaSpecs: {
          // In synchronous mode we need a chief/master
          Chief: $.tfJobReplica(1,
                                chiefCommand,
                                params.image,
                                numGpus=0,
                                env=workerEnv,
                                volumes=workerVolumes,
                                volumeMounts=workerVolumeMounts) +
                 // There is a bug in Tensor2Tensor 1.10 and it doesn't start a std server
                 // https://github.com/tensorflow/tensor2tensor/issues/926
                 // To work around this we run a standard server as a side car.
                 {
                   template+: {
                     spec+: {
                       containers+: [stdServerContainer(params.numWorkerGpu)],
                     },
                   },
                 },
          // See comment above; with synchronous training ps are used as workers.
          [if params.numWorker > 0 then "Ps"]: $.tfJobReplica(params.numWorker,
                                                              // Run our code to start std servers.
                                                              // This is a work around for
                                                              // https://github.com/kubeflow/examples/issues/208#issuecomment-436720653
                                                              ["python", "-m", "code_search.t2t.start_std_server"],
                                                              workerImage,
                                                              numGpus=params.numWorkerGpu,
                                                              env=workerEnv,
                                                              volumes=workerVolumes,
                                                              volumeMounts=workerVolumeMounts),
        },  // tfReplicaSpes
      },  // spec
    },  // jobDistSync

    // This spec is used for single node training or async training.
    // TODO(https://github.com/kubeflow/examples/issues/208#issuecomment-436720653):
    // Distributed async training is not working with T2T 1.10.
    // It looks like the issue is that there is a bug in the code and TF standard
    // servers aren't being started. We can potentially work around that
    // by launching the stdsevers in a side car.
    job:: {
      apiVersion: "kubeflow.org/v1alpha2",
      kind: "TFJob",
      metadata: {
        name: params.name,
        namespace: env.namespace,
      },
      spec: {
        tfReplicaSpecs: {
          [if params.numPs > 0 then "PS"]: $.tfJobReplica(
            params.numPs,
            // As a work around to
            // https://github.com/kubeflow/examples/issues/208#issuecomment-436720653
            // we run our own code for starting a standard server rather than relying
            // on T2T.
            ["python", "-m", "code_search.t2t.start_std_server"],
            psImage,
            numGpus=params.numPsGpu,
            env=workerEnv,
            volumes=workerVolumes,
            volumeMounts=workerVolumeMounts
          ),
          [if params.numChief > 0 then "Chief"]: $.tfJobReplica(
            params.numChief,
            workerCmd,
            workerImage,
            numGpus=params.numWorkerGpu,
            env=workerEnv,
            volumes=workerVolumes,
            volumeMounts=workerVolumeMounts
          ),
          [if params.numWorker > 0 then "Worker"]: $.tfJobReplica(
            params.numWorker,
            workerCmd,
            workerImage,
            numGpus=params.numWorkerGpu,
            env=workerEnv,
            volumes=workerVolumes,
            volumeMounts=workerVolumeMounts
          ),
        },
      },
    },
  },
}
