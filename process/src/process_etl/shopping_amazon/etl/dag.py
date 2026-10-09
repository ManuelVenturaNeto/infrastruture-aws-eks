from library.process import Dag

from . import steps


def build_dag(source: str, target: str) -> Dag:
    """
    Builds the extract DAG: reads the raw parquet, writes it as Delta and reads the Delta table back.
    """
    return Dag(
        [
            steps.ReadParquet(source=source),
            steps.DistinctSelect(),
            steps.UniqueID(),
            steps.WriteDelta(target=target),
        ]
    )
