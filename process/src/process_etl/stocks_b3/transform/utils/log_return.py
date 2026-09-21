from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from ...config.dag import Step
from .windows import by_ticker

PRICES = ("open_price", "high_price", "low_price", "close_price")


class LogReturn(Step):
    def run(self, df: DataFrame) -> DataFrame:
        """
        Creates the log1p columns for prices, a signed log for day_trade, and the daily log return per ticker.
        Prices are never negative, so log1p is safe there; day_trade is, so it takes signum(x) * log1p(|x|).
        """
        return (
            df.withColumns({f"log_{name}": F.log1p(name) for name in PRICES})
            .withColumn(
                "log_day_trade",
                F.signum("day_trade") * F.log1p(F.abs("day_trade")),
            )
            .withColumn(
                "log_return",
                F.log(
                    F.try_divide("close_price", F.lag("close_price").over(by_ticker()))
                ),
            )
        )
