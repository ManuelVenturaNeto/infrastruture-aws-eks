from library.process import Step
from pyspark.sql import DataFrame


class ReadParquet(Step):
    def __init__(self, *, source: str) -> None:
        super().__init__()
        self.source = source

    def run(self, df: DataFrame) -> DataFrame:
        return self.spark.read.parquet(self.source)
