# check certain library exsistence

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
  'owner': 'gabe',
  'retry': 0,
  'retry_delay': timedelta(minutes = 5) 
}

def get_lib():
  import json
  print(f"package with version {json.__version__}")

with DAG(
  default_args = default_args,
  dag_id = 'dag_python_dependency_v01',
  start_date = datetime(2021, 10, 16),
  schedule_interval = '@daily'
) as dag:
  
  get_lib = PythonOperator(
    task_id = 'get_lib',
    python_callable = get_lib
  )

  get_lib