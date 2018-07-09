# This DAG is configured to print the date and sleep for 5 seconds.
# However, it is configured to fail (see the expect_failure bash_command)
# and send an e-mail to your specified email on task failure.

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

YESTERDAY = datetime.combine(
    datetime.today() - timedelta(days=1), datetime.min.time())

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': YESTERDAY,
    'email': [ Variable.get('email') ],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 0,
}

with DAG('hello_world_email_bonus', default_args=default_args) as dag:
  t1 = BashOperator(task_id='print_date', bash_command='date', dag=dag)
  t2 = BashOperator(task_id='expect_failure', bash_command='exit 1', dag=dag)
  t1 >> t2
