from library.process import Step
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .windows import by_ticker


class SlowStochastic(Step):
    def run(self, df: DataFrame) -> DataFrame:
        """
        Computes the slow stochastic (14, 3, 3): fast_k, slow_k and slow_d.
        """
        last_14 = by_ticker().rowsBetween(-13, 0)
        last_03 = by_ticker().rowsBetween(-2, 0)

        fast_k = 100 * F.try_divide(
            F.col("close_price") - F.min("low_price").over(last_14),
            F.max("high_price").over(last_14) - F.min("low_price").over(last_14),
        )

        df = df.withColumn("fast_k", fast_k)
        df = df.withColumn("slow_k", F.avg("fast_k").over(last_03))
        return df.withColumn("slow_d", F.avg("slow_k").over(last_03))
