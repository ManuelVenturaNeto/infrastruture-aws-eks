import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stocks_b3.config.paths import EVENTS, FEATURES, SOURCE, TARGET
from stocks_b3.config.spark import build_spark
from stocks_b3.extract import extract
from stocks_b3.load import load
from stocks_b3.transform import transform


def main() -> None:
    """
    Starts Spark, runs extract, transform and load in sequence, and stops the session at the end.
    """
    spark = build_spark()
    try:
        df = extract.build_dag(spark, SOURCE, TARGET).run()
        df = transform.build_dag(spark, EVENTS).run(df)
        load.build_dag(FEATURES).run(df)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
