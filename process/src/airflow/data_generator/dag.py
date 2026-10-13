import importlib

import pendulum
from airflow.sdk import DAG, Param, task
from library.kubernetes import LAKE, spark_job

import data_generator
from data_generator import extraction
from data_generator.extraction import PROCESSES

ALL = "all"

with DAG(
    dag_id="data_generator",
    start_date=pendulum.datetime(2026, 10, 1, tz="America/Sao_Paulo"),
    schedule=None,
    catchup=False,
    default_args={"retries": 2},
    params={"dataset": Param(ALL, enum=[ALL, *PROCESSES])},
) as dag:

    @task.branch
    def select(**context) -> list[str]:
        dataset = context["params"]["dataset"]
        return PROCESSES if dataset == ALL else [dataset]

    selected = select()

    for name in PROCESSES:
        machine = importlib.import_module(f"{extraction.__name__}.{name}.machine")
        selected >> spark_job(
            dag,
            task_id=name,
            job=data_generator,
            arguments=[name, "--out", LAKE],
            driver=machine.CPU,
        )
