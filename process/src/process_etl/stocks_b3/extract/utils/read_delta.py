from pathlib import Path

from library.process import Step
from pyspark.sql import DataFrame


class ReadDelta(Step):
    def __init__(self, target: Path) -> None:
        """
        Stores the Delta table directory.
        """
        self.target = target

    def run(self, df: DataFrame | None = None) -> DataFrame:
        """
        Reads the optimized Delta table, replacing the raw DataFrame received.
        """
        return self.spark.read.format("delta").load(str(self.target))
