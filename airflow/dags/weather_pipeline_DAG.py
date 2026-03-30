from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig
from cosmos.constants import ExecutionMode, TestBehavior
from cosmos.profiles import DatabricksTokenProfileMapping




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
    profile_config = ProfileConfig(
    profile_name="dbt_weather",
    target_name="dev",
    profiles_yml_filepath="/opt/airflow/dbt_weather/profiles.yml",
)

    dbt_task_group = DbtTaskGroup(
        group_id="dbt_weather_models",
        project_config=ProjectConfig(
            dbt_project_path="/opt/airflow/dbt_weather",
        ),
        profile_config=profile_config,
        execution_config=ExecutionConfig(
            execution_mode=ExecutionMode.LOCAL,
            dbt_executable_path="/home/airflow/.local/bin/dbt",
        ),
        operator_args={
            "install_deps": True,
        },
        #test_behavior=TestBehavior.AFTER_ALL,
    )

    

    ingest_task >> dbt_task_group




        