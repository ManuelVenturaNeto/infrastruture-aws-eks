from library.process import Step
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .windows import by_ticker


class TrendFlags(Step):
    def run(self, df: DataFrame) -> DataFrame:
        """
        Flags 1/0 whether the close rose against N weeks (2 to 24) and N months (2 to 6) ago.
        """
        df = df.withColumns(
            {
                f"last_{n}_weeks_up": (
                    F.col("close_price") > F.lag("close_price", 5 * n).over(by_ticker())
                ).cast("int")
                for n in range(2, 26, 2)
            }
        )
        return df.withColumns(
            {
                f"last_{n}_months_up": (
                    F.col("close_price")
                    > F.lag("close_price", 21 * n).over(by_ticker())
                ).cast("int")
                for n in range(2, 8, 2)
            }
        )
