import datetime

from airflow.contrib.operators.mlengine_operator import MLEngineTrainingOperator
from airflow.operators.bash_operator import BashOperator


def training_tasks(model, dag, PROJECT_ID, BUCKET, DATA_DIR, MODEL_NAME, MODEL_VERSION, MODEL_LOCATION):
  # Constants
  # The code package name comes from the model code in the module directory
  REGION = "us-east1"
  PACKAGE_URI = BUCKET + "/taxifare/code/taxifare-0.1.tar.gz"
  JOB_DIR = BUCKET + "/jobs"

  # ML Engine training job
  job_id = "taxifare_{}_{}".format(model.replace(".","_"), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
  train_files = DATA_DIR + "{}/train-*.csv".format(model.replace(".","_"))
  eval_files = DATA_DIR + "{}/eval-*.csv".format(model.replace(".","_"))
  output_dir = BUCKET + "/taxifare/trained_model/{}".format(model.replace(".","_"))
  job_dir = JOB_DIR + "/" + job_id
  training_args = [
    "--job-dir", job_dir,
    "--train_data_paths", train_files,
    "--eval_data_paths", eval_files,
    "--output_dir", output_dir,
    "--train_steps", str(500),
    "--train_batch_size", str(32),
    "--eval_steps", str(500),
    "--eval_batch_size", str(32),
    "--nbuckets", str(8),
    "--hidden_units", "128,32,4"
  ]

  # Reference: https://airflow.apache.org/integration.html#cloud-ml-engine
  ml_engine_training_op = MLEngineTrainingOperator(
    task_id="ml_engine_training_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID,
    job_id=job_id,
    package_uris=[PACKAGE_URI],
    training_python_module="trainer.task",
    training_args=training_args,
    region=REGION,
    scale_tier="BASIC",
    runtime_version="1.13", 
    python_version="3.5",
    dag=dag
  )

  bash_remove_old_saved_model_op = BashOperator(
    task_id="bash_remove_old_saved_model_{}_task".format(model.replace(".","_")),
    bash_command="if gsutil ls {0} 2> /dev/null; then gsutil -m rm -rf {0}/*; else true; fi".format(MODEL_LOCATION + model.replace(".","_")),
    dag=dag
  )

  bash_copy_new_saved_model_op = BashOperator(
    task_id="bash_copy_new_saved_model_{}_task".format(model.replace(".","_")),
    bash_command="gsutil -m rsync -d -r `gsutil ls {0}/export/exporter/ | tail -1` {1}".format(output_dir, MODEL_LOCATION + model.replace(".","_")),
    dag=dag
  )
  
  # Build dependency graph, set_upstream dependencies for all tasks
  bash_remove_old_saved_model_op.set_upstream(ml_engine_training_op)
  bash_copy_new_saved_model_op.set_upstream(bash_remove_old_saved_model_op)
  
  return (ml_engine_training_op,
          bash_copy_new_saved_model_op)
