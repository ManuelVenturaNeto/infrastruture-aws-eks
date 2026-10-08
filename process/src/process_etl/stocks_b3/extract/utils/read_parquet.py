from pathlib import Path

from library.process import Step
from pyspark.sql import DataFrame


class ReadParquet(Step):
    def __init__(self, source: Path) -> None:

        self.source = source

    def run(self, df: DataFrame | None = None) -> DataFrame:

        return self.spark.read.parquet(str(self.source))
