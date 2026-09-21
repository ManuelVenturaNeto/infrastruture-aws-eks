from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from ...config.dag import Step


class ReadDelta(Step):
    def __init__(self, spark: SparkSession, target: Path) -> None:
        """
        Stores the Spark session and the Delta table directory.
        """
        self.spark = spark
        self.target = target

    def run(self, df: DataFrame | None = None) -> DataFrame:
        """
        Reads the optimized Delta table, replacing the raw DataFrame received.
        """
        return self.spark.read.format("delta").load(str(self.target))
