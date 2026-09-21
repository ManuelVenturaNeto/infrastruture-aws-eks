from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from ...config.dag import Step


class FilterStocks(Step):
    def run(self, df: DataFrame) -> DataFrame:
        """
        Keeps only standard-lot cash-market stocks and selects the columns used downstream.
        """
        return df.filter(
            (F.col("market_type") == "010")
            & (F.col("bdi_code") == "02")
            & (~F.col("specification").contains("DRN"))
        ).select(
            "trade_date",
            "year",
            "ticker",
            "company_name",
            "specification",
            "isin_code",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "total_trades",
            "total_quantity",
            "total_volume",
            "quote_factor",
        )
