from library.process import Step
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .windows import array_median, by_ticker


class VolumeIndicators(Step):
    def run(self, df: DataFrame) -> DataFrame:
        """
        Computes log volume, 20-session median and MAD baselines, volume ratio, volume z-score and OBV.
        """
        last_20 = by_ticker().rowsBetween(-19, 0)

        df = df.withColumn("log_volume", F.log1p("total_volume"))
        df = df.withColumn(
            "volume_window", F.collect_list("total_volume").over(last_20)
        )
        df = df.withColumn("volume_median_20", array_median("volume_window"))
        df = df.withColumn(
            "volume_ratio", F.try_divide("total_volume", "volume_median_20")
        )
        df = df.withColumn(
            "volume_mad_20",
            array_median(
                F.transform(
                    "volume_window", lambda x: F.abs(x - F.col("volume_median_20"))
                )
            ),
        )
        df = df.withColumn(
            "volume_zscore_20",
            F.when(
                F.col("volume_mad_20") > 0,
                0.6745
                * (F.col("total_volume") - F.col("volume_median_20"))
                / F.col("volume_mad_20"),
            ),
        )
        df = df.withColumn(
            "obv",
            F.sum(
                F.when(F.col("log_return") > 0, F.col("total_quantity"))
                .when(F.col("log_return") < 0, -F.col("total_quantity"))
                .otherwise(0)
            ).over(by_ticker()),
        )
        return df.drop("volume_window")
