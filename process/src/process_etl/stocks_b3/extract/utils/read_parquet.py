from pathlib import Path

from library.process import Step
from pyspark.sql import DataFrame


class ReadParquet(Step):
    def __init__(self, source: Path) -> None:
        """
        Stores the raw parquet directory.
        """
        self.source = source

    def run(self, df: DataFrame | None = None) -> DataFrame:
        """
        Reads every year of the raw parquet; ignores the input DataFrame since this is the first step.
        """
        return self.spark.read.parquet(str(self.source))
