from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from ...config.dag import Step


class ReadParquet(Step):
    def __init__(self, spark: SparkSession, source: Path) -> None:
        """
        Stores the Spark session and the raw parquet directory.
        """
        self.spark = spark
        self.source = source

    def run(self, df: DataFrame | None = None) -> DataFrame:
        """
        Reads every year of the raw parquet; ignores the input DataFrame since this is the first step.
        """
        return self.spark.read.parquet(str(self.source))
