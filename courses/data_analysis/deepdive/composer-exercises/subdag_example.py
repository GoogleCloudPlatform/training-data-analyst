"""DAG with repeating download-decrypt-wordcount structure.

This DAG downloads encrypted Shakespeare manuscripts, decrypts them, and
counts the words, but it does so by cloning the tasks!
"""

from airflow import DAG
from airflow.contrib.operators.gcs_download_operator import GoogleCloudStorageDownloadOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator

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

with DAG('subdag_example_before', default_args=default_args, catchup=False) as dag:
  start = DummyOperator(task_id='start')
  download_romeo = GoogleCloudStorageDownloadOperator(task_id='download_romeo',
                                                      bucket='smenyc2018-subdag-data',
                                                      object='romeo.enc',
                                                      filename='/home/airflow/gcs/data/romeo.enc')
  download_othello = GoogleCloudStorageDownloadOperator(task_id='download_othello',
                                                      bucket='smenyc2018-subdag-data',
                                                      object='othello.enc',
                                                      filename='/home/airflow/gcs/data/othello.enc')
  download_hamlet = GoogleCloudStorageDownloadOperator(task_id='download_hamlet',
                                                      bucket='smenyc2018-subdag-data',
                                                      object='hamlet.enc',
                                                      filename='/home/airflow/gcs/data/hamlet.enc')

  decrypt_romeo = BashOperator(task_id='decrypt_romeo',
                               bash_command='openssl enc -in /home/airflow/gcs/data/romeo.enc -out /home/airflow/gcs/data/romeo.txt -d -aes-128-cbc -k "hello-nyc"')
  decrypt_othello = BashOperator(task_id='decrypt_othello',
                                 bash_command='openssl enc -in /home/airflow/gcs/data/othello.enc -out /home/airflow/gcs/data/othello.txt -d -aes-128-cbc -k "hello-nyc"')
  decrypt_hamlet = BashOperator(task_id='decrypt_hamlet',
                                bash_command='openssl enc -in /home/airflow/gcs/data/hamlet.enc -out /home/airflow/gcs/data/hamlet.txt -d -aes-128-cbc -k "hello-nyc"')

  wordcount_romeo = BashOperator(task_id='wordcount_romeo',
                                 bash_command='wc -w /home/airflow/gcs/data/romeo.txt | tee /home/airflow/gcs/data/romeo_wordcount.txt')
  wordcount_othello = BashOperator(task_id='wordcount_othello',
                                 bash_command='wc -w /home/airflow/gcs/data/othello.txt | tee  /home/airflow/gcs/data/othello_wordcount.txt')
  wordcount_hamlet = BashOperator(task_id='wordcount_hamlet',
                                 bash_command='wc -w /home/airflow/gcs/data/hamlet.txt | tee /home/airflow/gcs/data/hamlet_wordcount.txt')

  start >> download_romeo >> decrypt_romeo >> wordcount_romeo
  start >> download_othello >> decrypt_othello >> wordcount_othello
  start >> download_hamlet >> decrypt_hamlet >> wordcount_hamlet
