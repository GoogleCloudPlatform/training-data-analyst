from airflow import DAG
from airflow.operators.bash_operator import BashOperator
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

with DAG('hello_world_solution', default_args=default_args) as dag:
  t1 = BashOperator(task_id='print_date', bash_command='date', dag=dag)
  t2 = BashOperator(task_id='sleep', bash_command='sleep 5', dag=dag)
  t1 >> t2

  # Airflow macro expansion.
  templated_command = """
    {% for i in range(5) %}
    echo "{{ ds }}"
    echo "{{ macros.ds_add(ds, 7)}}"
    echo "{{ params.my_param }}"
    {% endfor %}
  """

  # Solution:
  # gsutil cp count.txt gs://{your-composer-bucket}/dags
  with open('/home/airflow/gcs/dags/count.txt') as f:
    number_of_templated_tasks = int(f.read())
    for i in xrange(number_of_templated_tasks):
      tmp = BashOperator(
          task_id='templated-%s' % i,
          bash_command=templated_command,
          params={'my_param': 'composer-test'},
          dag=dag)
      t2 >> tmp
