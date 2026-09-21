from pathlib import Path

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from ...config.dag import Step


class WriteDelta(Step):
    def __init__(self, spark: SparkSession, target: Path) -> None:
        """
        Stores the Spark session and the Delta table target directory.
        """
        self.spark = spark
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
