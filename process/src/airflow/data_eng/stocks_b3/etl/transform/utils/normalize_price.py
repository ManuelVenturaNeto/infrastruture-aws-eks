from library.process import Step
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


class NormalizePrice(Step):
    def run(self, df: DataFrame) -> DataFrame:
        """
        Divides the four prices by the quote factor and creates the intraday change day_trade.
        """
        df = df.withColumns(
            {
                name: F.try_divide(name, "quote_factor")
                for name in ("open_price", "high_price", "low_price", "close_price")
            }
        ).drop("quote_factor")
        return df.withColumn("day_trade", F.col("close_price") - F.col("open_price"))
