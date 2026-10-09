from pathlib import Path

import pendulum
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import (
    SparkKubernetesOperator,
)
from airflow.sdk import DAG

with DAG(
    dag_id="shopping_amazon_etl",
    start_date=pendulum.datetime(2026, 10, 1, tz="America/Sao_Paulo"),
    schedule=None,
    catchup=False,
    template_searchpath=[str(Path(__file__).parent)],
):
    SparkKubernetesOperator(
        task_id="etl",
        namespace="spark-jobs",
        application_file="sparkapplication.yaml",
    )
