from delta import DeltaTable
from library.process import Step
from pyspark.sql import DataFrame


class WriteDelta(Step):
    def __init__(self, *, target: str) -> None:
        super().__init__()
        self.target = target

    def run(self, df: DataFrame) -> DataFrame:
        if not DeltaTable.isDeltaTable(self.spark, self.target):
            (
                df.write.format("delta")
                .partitionBy("year_month")
                .mode("overwrite")
                .save(self.target)
            )
        return df
