from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

sys.path.append('/opt/airflow/ingest')

#from weather_fetcher import fetch_open_meteo_current
#from storage_jsonl import append_jsonl, utc_now_iso
#from config import ZUGLO_LAT, ZUGLO_LON, LOCATION_NAME
from main import run


def run_ingest():
    run()

default_args = {
    "owner": "weather",
    "retries":1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="weather_pipeline",
    default_args=default_args,
    description="A Zugló időjárás gyűjtő pipeline.",
    schedule_interval="2 * * * *",  # minden órában 2. percében
    catchup=False,
    tags=["weather", "zuglo"],
    start_date=datetime(2024, 2, 15, 0, 0, 0),
) as dag:
    
    ingest_task = PythonOperator(
        task_id="ingest_weather_zuglo", # 
        python_callable=run_ingest,

    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt/dbt_weather && dbt run --profiles-dir ."
        
    )

    ingest_task >> dbt_run




        