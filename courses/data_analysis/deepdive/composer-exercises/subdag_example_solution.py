"""Solution for subdag_example.py.

Uses a factory function to return a DAG that can be used as the subdag argument
to SubDagOperator. Notice that:
1) the SubDAG's dag_id is formatted as parent_dag_id.subdag_task_id
2) the start_date and schedule_interval of the SubDAG are copied from the parent
   DAG.
"""
from airflow import DAG
from airflow.contrib.operators.gcs_download_operator import GoogleCloudStorageDownloadOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.subdag_operator import SubDagOperator

from datetime import datetime, timedelta


YESTERDAY = datetime.combine(
    datetime.today() - timedelta(days=1), datetime.min.time())


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': YESTERDAY,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def shakespeare_subdag(parent_dag, subdag_task_id, play_name):
  with DAG('{}.{}'.format(parent_dag.dag_id, subdag_task_id),
           schedule_interval=parent_dag.schedule_interval,
           start_date=parent_dag.start_date,
           default_args=parent_dag.default_args) as subdag:
    download = GoogleCloudStorageDownloadOperator(task_id='download',
                                                  bucket='smenyc2018-subdag-data',
                                                  object='{}.enc'.format(play_name),
                                                  filename='/home/airflow/gcs/data/{}.enc'.format(play_name))
    decrypt = BashOperator(task_id='decrypt',
                           bash_command='openssl enc -in /home/airflow/gcs/data/{play_name}.enc '
                           '-out /home/airflow/gcs/data/{play_name}.txt -d -aes-128-cbc -k "hello-nyc"'.format(play_name=play_name))
    wordcount = BashOperator(task_id='wordcount',
                             bash_command='wc -w /home/airflow/gcs/data/{play_name}.txt | tee /home/airflow/gcs/data/{play_name}_wordcount.txt'.format(play_name=play_name))
    download >> decrypt >> wordcount
  return subdag


with DAG('subdag_example_solution', default_args=default_args, catchup=False) as dag:
  start = DummyOperator(task_id='start')
  start >> SubDagOperator(task_id='process_romeo', subdag=shakespeare_subdag(dag, 'process_romeo', 'romeo'))
  start >> SubDagOperator(task_id='process_othello', subdag=shakespeare_subdag(dag, 'process_othello', 'othello'))
  start >> SubDagOperator(task_id='process_hamlet', subdag=shakespeare_subdag(dag, 'process_hamlet', 'hamlet'))
  start >> SubDagOperator(task_id='process_macbeth', subdag=shakespeare_subdag(dag, 'process_macbeth', 'macbeth'))
