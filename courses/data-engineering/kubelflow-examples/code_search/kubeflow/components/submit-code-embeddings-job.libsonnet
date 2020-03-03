{
  parts(params, env):: {
  	// Submit a Dataflow job to compute the code embeddings used a trained model.
  	job :: {
	  apiVersion: "batch/v1",
	  kind: "Job",
	  metadata: {
	    name: params.name + '-' + params.jobNameSuffix,
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
	              "python2",
	              "-m",
	              "code_search.dataflow.cli.create_function_embeddings",
	              "--runner=DataflowRunner",
	              "--project=" + params.project,
	              "--function_embeddings_table=" + params.functionEmbeddingsBQTable,
	              "--output_dir=" + params.functionEmbeddingsDir,
	              "--data_dir=" + params.dataDir,
	              "--problem=" + params.problem,
	              "--job_name=" + params.jobName + '-' + params.jobNameSuffix,
	              "--saved_model_dir=" + params.modelDir,
	              "--temp_location=" + params.workingDir + "/dataflow/temp",
	              "--staging_location=" + params.workingDir + "/dataflow/staging",
	              "--worker_machine_type=" + params.workerMachineType,
	              "--num_workers=" + params.numWorkers,
	              "--requirements_file=requirements.txt",
                  if (params.waitUntilFinish == "true") then
                      "--wait_until_finished"
                  else [],
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
	}, // job
  }, // parts
}