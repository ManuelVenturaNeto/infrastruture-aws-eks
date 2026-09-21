from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from ...config.dag import Step
from .windows import by_ticker


class MovingAverage(Step):
    def run(self, df: DataFrame) -> DataFrame:
        """
        Computes the 90-session moving average of the close price and the relative distance of the price to it.
        """
        last_90 = by_ticker().rowsBetween(-89, 0)

        df = df.withColumn("sma_90", F.avg("close_price").over(last_90))
        return df.withColumn(
            "sma_90_distance", F.try_divide("close_price", "sma_90") - 1
        )
