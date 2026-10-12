from library.process import Step
from pyspark.sql import DataFrame


class ReadDelta(Step):
    def __init__(self, target: str) -> None:

        self.target = target

    def run(self, df: DataFrame | None = None) -> DataFrame:

        return self.spark.read.format("delta").load(self.target)
