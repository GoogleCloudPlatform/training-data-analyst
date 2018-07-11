from airflow import DAG
from airflow.operators.bash_operator import BashOperator
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

def atomic_subdag(parent_dag_name, subdag_task_id, default_args, num_shards):
  default_args = dict(default_args)
  default_args.update({'retries': 0})
  with DAG('{}.{}'.format(parent_dag_name, subdag_task_id),
           default_args=default_args) as subdag:
    for i in xrange(num_shards):
      BashOperator(task_id='write_shard{}'.format(i),
                   bash_command='echo {} >> /tmp/{}.output'.format(i, i))
  return subdag

with DAG('subdag_parent', default_args=default_args) as dag:
  t1 = BashOperator(task_id='prologue', bash_command='echo prologue')
  t2 = SubDagOperator(task_id='atomic_subdag',
                      retries=10,
                      retry_delay=timedelta(seconds=1),
                      subdag=atomic_subdag('subdag_parent',
                                           'atomic_subdag',
                                           default_args,
                                           10))
  t3 = BashOperator(task_id='epilogue', bash_command='echo epilogue')

t1 >> t2 >> t3
