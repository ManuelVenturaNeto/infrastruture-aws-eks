from pathlib import Path

from pyspark.sql import SparkSession

from ..config.dag import Dag
from .utils.read_delta import ReadDelta
from .utils.read_parquet import ReadParquet
from .utils.write_delta import WriteDelta


def build_dag(spark: SparkSession, source: Path, target: Path) -> Dag:
    """
    Builds the extract DAG: reads the raw parquet, writes it as Delta and reads the Delta table back.
    """
    return Dag(
        [
            ReadParquet(spark, source),
            WriteDelta(spark, target),
            ReadDelta(spark, target),
        ]
    )
