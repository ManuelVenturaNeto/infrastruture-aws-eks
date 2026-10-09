from pathlib import Path

from delta import DeltaTable
from library.process import Step
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


class ReadParquet(Step):
    def __init__(self, *, source: Path) -> None:
        super().__init__()
        self.source = source

    def run(self, df: DataFrame) -> DataFrame:
        return self.spark.read.parquet(str(self.source))


class DistinctSelect(Step):
    def run(self, df: DataFrame) -> DataFrame:
        return df.distinct().select(
            F.concat_ws("_", F.col("user_id"), F.col("timestamp")).alias("id"),
            F.col("rating"),
            F.col("user_id"),
            F.timestamp_millis("timestamp").alias("timestamp"),
            F.date_format(F.timestamp_millis("timestamp"), "yyyy-MM").alias(
                "year_month"
            ),
            F.to_json(F.struct(F.col("title"), F.col("text"))).alias("full_text"),
            F.col("asin"),
            F.col("parent_asin"),
            F.when(F.col("helpful_vote") == 0, False)
            .otherwise(True)
            .alias("helpful_vote"),
            F.col("verified_purchase"),
        )


class UniqueID(Step):
    def run(self, df: DataFrame) -> DataFrame:
        window = Window.partitionBy("id").orderBy("rating", "full_text")
        return (
            df.withColumn("row_number", F.row_number().over(window))
            .filter(F.col("row_number") == 1)
            .drop("row_number")
        )


class WriteDelta(Step):
    def __init__(self, *, target: Path) -> None:
        super().__init__()
        self.target = target

    def run(self, df: DataFrame) -> DataFrame:
        if not DeltaTable.isDeltaTable(self.spark, str(self.target)):
            (
                df.write.format("delta")
                .partitionBy("year_month")
                .mode("overwrite")
                .save(str(self.target))
            )
        return df
