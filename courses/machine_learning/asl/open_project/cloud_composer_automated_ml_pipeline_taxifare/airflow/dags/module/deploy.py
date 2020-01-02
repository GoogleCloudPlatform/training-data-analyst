import datetime
import logging

from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.contrib.operators.mlengine_operator import MLEngineModelOperator, MLEngineVersionOperator


def deploy_tasks(model, dag, PROJECT_ID, MODEL_NAME, MODEL_VERSION, MODEL_LOCATION):
  # Constants
  OTHER_VERSION_NAME = "v_{0}".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")[0:12])

  # Create model on ML-Engine
  bash_ml_engine_models_list_op = BashOperator(
    task_id="bash_ml_engine_models_list_{}_task".format(model.replace(".","_")),
    xcom_push=True,
    bash_command="gcloud ml-engine models list --filter='name:{0}'".format(MODEL_NAME + model.replace(".","_")),
    dag=dag
  )

  def check_if_model_already_exists(templates_dict, **kwargs):
    cur_model = templates_dict["model"].replace(".","_")
    ml_engine_models_list = kwargs["ti"].xcom_pull(task_ids="bash_ml_engine_models_list_{}_task".format(cur_model))
    logging.info("check_if_model_already_exists: {}: ml_engine_models_list = \n{}".format(cur_model, ml_engine_models_list))
    create_model_task = "ml_engine_create_model_{}_task".format(cur_model)
    dont_create_model_task = "dont_create_model_dummy_branch_{}_task".format(cur_model)
    if len(ml_engine_models_list) == 0 or ml_engine_models_list == "Listed 0 items.":
      return create_model_task
    return dont_create_model_task

  check_if_model_already_exists_op = BranchPythonOperator(
    task_id="check_if_model_already_exists_{}_task".format(model.replace(".","_")),
    templates_dict={"model": model.replace(".","_")},
    python_callable=check_if_model_already_exists,
    provide_context=True,
    dag=dag
  )

  ml_engine_create_model_op = MLEngineModelOperator(
    task_id="ml_engine_create_model_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model={"name": MODEL_NAME + model.replace(".","_")}, 
    operation="create",
    dag=dag
  )

  create_model_dummy_op = DummyOperator(
    task_id="create_model_dummy_{}_task".format(model.replace(".","_")),
    trigger_rule="all_done",
    dag=dag
  )

  dont_create_model_dummy_branch_op = DummyOperator(
    task_id="dont_create_model_dummy_branch_{}_task".format(model.replace(".","_")),
    dag=dag
  )

  dont_create_model_dummy_op = DummyOperator(
    task_id="dont_create_model_dummy_{}_task".format(model.replace(".","_")),
    trigger_rule="all_done",
    dag=dag
  )

  # Create version of model on ML-Engine
  bash_ml_engine_versions_list_op = BashOperator(
    task_id="bash_ml_engine_versions_list_{}_task".format(model.replace(".","_")),
    xcom_push=True,
    bash_command="gcloud ml-engine versions list --model {0} --filter='name:{1}'".format(MODEL_NAME + model.replace(".","_"), MODEL_VERSION),
    dag=dag
  )

  def check_if_model_version_already_exists(templates_dict, **kwargs):
    cur_model = templates_dict["model"].replace(".","_")
    ml_engine_versions_list = kwargs["ti"].xcom_pull(task_ids="bash_ml_engine_versions_list_{}_task".format(cur_model))
    logging.info("check_if_model_version_already_exists: {}: ml_engine_versions_list = \n{}".format(cur_model, ml_engine_versions_list))
    create_version_task = "ml_engine_create_version_{}_task".format(cur_model)
    create_other_version_task = "ml_engine_create_other_version_{}_task".format(cur_model)
    if len(ml_engine_versions_list) == 0 or ml_engine_versions_list == "Listed 0 items.":
      return create_version_task
    return create_other_version_task

  check_if_model_version_already_exists_op = BranchPythonOperator(
    task_id="check_if_model_version_already_exists_{}_task".format(model.replace(".","_")), 
    templates_dict={"model": model.replace(".","_")},
    python_callable=check_if_model_version_already_exists,
    provide_context=True,
    dag=dag
  )

  ml_engine_create_version_op = MLEngineVersionOperator(
    task_id="ml_engine_create_version_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model_name=MODEL_NAME + model.replace(".","_"), 
    version_name=MODEL_VERSION, 
    version={
      "name": MODEL_VERSION,
      "deploymentUri": MODEL_LOCATION + model.replace(".","_"),
      "runtimeVersion": "1.13",
      "framework": "TENSORFLOW",
      "pythonVersion": "3.5",
    },
    operation="create",
    dag=dag
  )

  ml_engine_create_other_version_op = MLEngineVersionOperator(
    task_id="ml_engine_create_other_version_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model_name=MODEL_NAME + model.replace(".","_"), 
    version_name=OTHER_VERSION_NAME, 
    version={
      "name": OTHER_VERSION_NAME,
      "deploymentUri": MODEL_LOCATION + model.replace(".","_"),
      "runtimeVersion": "1.13",
      "framework": "TENSORFLOW",
      "pythonVersion": "3.5",
    },
    operation="create",
    dag=dag
  )

  ml_engine_set_default_version_op = MLEngineVersionOperator(
    task_id="ml_engine_set_default_version_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model_name=MODEL_NAME + model.replace(".","_"), 
    version_name=MODEL_VERSION, 
    version={"name": MODEL_VERSION}, 
    operation="set_default",
    dag=dag
  )

  ml_engine_set_default_other_version_op = MLEngineVersionOperator(
    task_id="ml_engine_set_default_other_version_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model_name=MODEL_NAME + model.replace(".","_"), 
    version_name=OTHER_VERSION_NAME, 
    version={"name": OTHER_VERSION_NAME}, 
    operation="set_default",
    dag=dag
  )
  
  # Build dependency graph, set_upstream dependencies for all tasks
  check_if_model_already_exists_op.set_upstream(bash_ml_engine_models_list_op)

  ml_engine_create_model_op.set_upstream(check_if_model_already_exists_op)
  create_model_dummy_op.set_upstream(ml_engine_create_model_op)
  dont_create_model_dummy_branch_op.set_upstream(check_if_model_already_exists_op)
  dont_create_model_dummy_op.set_upstream(dont_create_model_dummy_branch_op)

  bash_ml_engine_versions_list_op.set_upstream([dont_create_model_dummy_op, create_model_dummy_op])
  check_if_model_version_already_exists_op.set_upstream(bash_ml_engine_versions_list_op)

  ml_engine_set_default_version_op.set_upstream(ml_engine_create_version_op)
  ml_engine_set_default_other_version_op.set_upstream(ml_engine_create_other_version_op)
  
  return (bash_ml_engine_models_list_op,
          check_if_model_version_already_exists_op,
          ml_engine_create_version_op,
          ml_engine_create_other_version_op)
