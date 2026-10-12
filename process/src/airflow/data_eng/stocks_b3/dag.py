import pendulum
from airflow.sdk import DAG
from library.kubernetes import spark_job

from data_eng.stocks_b3 import etl

with DAG(
    dag_id="stocks_b3",
    start_date=pendulum.datetime(2026, 10, 1, tz="America/Sao_Paulo"),
    schedule=None,
    catchup=False,
) as dag:
    spark_job(
        dag,
        task_id="spark_process",
        job=etl,
        sources={"source": "stocks_b3", "events": "stocks_b3_events"},
        targets={"target": "stocks_b3_delta", "features": "stocks_b3_features"},
    )
