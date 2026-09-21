from pathlib import Path

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from ...config.dag import Step

PRICES = ("open_price", "high_price", "low_price", "close_price")
REVERSE_SPLIT = "GRUPAMENTO"
SHARE_EVENTS = ("DESDOBRAMENTO", "BONIFICACAO", REVERSE_SPLIT)
LISTED, INFERRED = "b3", "inferred"

SPLIT_RATIOS = (
    1.5,
    2.0,
    3.0,
    4.0,
    5.0,
    6.0,
    8.0,
    10.0,
    20.0,
    25.0,
    50.0,
    100.0,
    1000.0,
)
MULTIPLIERS = SPLIT_RATIOS + tuple(1 / ratio for ratio in SPLIT_RATIOS)
RATIO_TOLERANCE = 0.03
QUANTITY_SHARE = 0.5
MIN_TRADES = 10
MIN_PRICE = 1.0
MATCH_DAYS = 5


class AdjustCorporateActions(Step):
    def __init__(self, spark: SparkSession, events: Path) -> None:
        """
        Stores the Spark session and the directory of the B3 stock-events parquet.
        """
        self.spark = spark
        self.events = events

    def listed_events(self) -> DataFrame:
        """
        Reads the share-count events published by B3 and turns each factor into a quantity multiplier.
        Other labels (spin-offs, mergers, capital redemptions) carry capital percentages, not share ratios.
        """
        multiplier = F.when(F.col("label") == REVERSE_SPLIT, F.col("factor")).otherwise(
            1 + F.col("factor") / 100
        )
        return (
            self.spark.read.parquet(str(self.events))
            .filter(F.col("label").isin(*SHARE_EVENTS))
            .select(
                "isin_code",
                "last_date_prior",
                multiplier.alias("multiplier"),
                F.lit(LISTED).alias("source"),
            )
            .distinct()
        )

    def inferred_events(self, df: DataFrame) -> DataFrame:
        """
        Detects share-count events from the quotes themselves: a one-day price ratio matching a round
        split ratio while the traded quantity moves the opposite way, on two liquid sessions priced above
        the minimum tick range, where a one-cent move cannot mimic a round ratio.
        """
        by_isin = Window.partitionBy("isin_code").orderBy("trade_date")
        previous = df.select(
            "isin_code",
            "trade_date",
            "close_price",
            "total_quantity",
            "total_trades",
            F.lag("trade_date").over(by_isin).alias("last_date_prior"),
            F.lag("close_price").over(by_isin).alias("previous_close"),
            F.lag("total_quantity").over(by_isin).alias("previous_quantity"),
            F.lag("total_trades").over(by_isin).alias("previous_trades"),
        )

        raw_multiplier = F.try_divide("previous_close", "close_price")
        candidates = F.array(*[F.lit(value) for value in MULTIPLIERS])
        matches = F.filter(
            candidates,
            lambda value: F.abs(F.log(raw_multiplier / value)) <= RATIO_TOLERANCE,
        )
        multiplier = F.try_element_at(matches, F.lit(1))

        quantity_log = F.log(F.try_divide("total_quantity", "previous_quantity"))
        multiplier_log = F.log(multiplier)
        quantity_agrees = (F.signum(quantity_log) == F.signum(multiplier_log)) & (
            F.abs(quantity_log) >= QUANTITY_SHARE * F.abs(multiplier_log)
        )
        liquid = (
            (F.col("total_trades") >= MIN_TRADES)
            & (F.col("previous_trades") >= MIN_TRADES)
            & (F.col("close_price") >= MIN_PRICE)
            & (F.col("previous_close") >= MIN_PRICE)
        )

        return (
            previous.withColumn("multiplier", multiplier)
            .filter(F.col("multiplier").isNotNull() & quantity_agrees & liquid)
            .select(
                "isin_code",
                "last_date_prior",
                "multiplier",
                F.lit(INFERRED).alias("source"),
            )
        )

    def all_events(self, df: DataFrame) -> DataFrame:
        """
        Combines listed and inferred events, keeping an inferred one only where B3 has nothing nearby.
        """
        listed = self.listed_events()
        inferred = self.inferred_events(df)
        nearby = (F.col("inferred.isin_code") == F.col("listed.isin_code")) & (
            F.abs(F.datediff("inferred.last_date_prior", "listed.last_date_prior"))
            <= MATCH_DAYS
        )
        missing = inferred.alias("inferred").join(
            listed.alias("listed"), nearby, "left_anti"
        )
        return listed.unionByName(missing)

    def run(self, df: DataFrame) -> DataFrame:
        """
        Back-adjusts prices and quantity so every session is expressed in today's share unit.
        The adjustment of a session is the product of the multipliers of all events still ahead of it.
        The quotes are cached first: inferring events is a second pass over them, and without the cache
        Spark would scan the Delta table and shuffle it twice.
        """
        df = df.cache()
        events = (
            self.all_events(df)
            .groupBy("isin_code")
            .agg(
                F.collect_list(F.struct("last_date_prior", "multiplier")).alias(
                    "events"
                )
            )
        )
        df = df.join(F.broadcast(events), "isin_code", "left")

        pending = F.filter(
            "events", lambda event: event["last_date_prior"] >= F.col("trade_date")
        )
        adjustment = F.aggregate(
            pending, F.lit(1.0), lambda acc, event: acc * event["multiplier"]
        )

        df = df.withColumn("adjustment", F.coalesce(adjustment, F.lit(1.0)))
        df = df.withColumns(
            {name: F.col(name) / F.col("adjustment") for name in PRICES}
        )
        df = df.withColumn(
            "total_quantity",
            F.round(F.col("total_quantity") * F.col("adjustment")).cast("long"),
        )
        return df.drop("events")
