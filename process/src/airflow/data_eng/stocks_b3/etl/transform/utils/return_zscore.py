from library.process import Step
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .windows import array_median, by_ticker


class ReturnZScore(Step):
    def run(self, df: DataFrame) -> DataFrame:
        """
        Computes the modified z-score (median and MAD) of the return over the last 90 sessions.
        """
        last_90 = by_ticker().rowsBetween(-89, 0)

        df = df.withColumn("return_window", F.collect_list("log_return").over(last_90))
        df = df.withColumn("return_median", array_median("return_window"))
        df = df.withColumn(
            "return_mad",
            array_median(
                F.transform(
                    "return_window", lambda x: F.abs(x - F.col("return_median"))
                )
            ),
        )
        df = df.withColumn(
            "return_zscore",
            F.when(
                F.col("return_mad") > 0,
                0.6745
                * (F.col("log_return") - F.col("return_median"))
                / F.col("return_mad"),
            ),
        )
        return df.drop("return_window", "return_median", "return_mad")
