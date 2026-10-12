from library.process import Step
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


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
