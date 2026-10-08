from pathlib import Path

from delta.tables import DeltaTable
from library.process import Step
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


class WriteDelta(Step):
    def __init__(self, target: Path) -> None:
        """
        Stores the Delta table target directory.
        """
        self.target = target

    def run(self, df: DataFrame) -> DataFrame:
        """
        Writes the DataFrame as Delta partitioned by year, skipping the write if the table already exists.
        """
        if not DeltaTable.isDeltaTable(self.spark, str(self.target)):
            (
                df.withColumn("year", F.year("trade_date"))
                .write.format("delta")
                .partitionBy("year")
                .mode("overwrite")
                .save(str(self.target))
            )
        return df
