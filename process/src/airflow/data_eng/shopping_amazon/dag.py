import pendulum
from airflow.sdk import DAG
from library.kubernetes import Cpu, Gpu, spark_job

from data_eng.shopping_amazon import etl

with DAG(
    dag_id="shopping_amazon_reviews",
    start_date=pendulum.datetime(2026, 10, 1, tz="America/Sao_Paulo"),
    schedule=None,
    catchup=False,
) as dag:
    spark_job(
        dag,
        task_id="spark_process",
        job=etl,
        sources={"source": "shopping_amazon_reviews"},
        targets={"target": "shopping_amazon_reviews_delta"},
        cpu=Cpu.LARGE,
        gpu=Gpu.LARGE,
    )
