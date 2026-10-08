import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from library.spark import build_spark

from .config.paths import EVENTS, FEATURES, SOURCE, TARGET
from .extract import extract
from .load import load
from .transform import transform


def main() -> None:

    spark = build_spark("stocks_b3")
    try:
        df = extract.build_dag(SOURCE, TARGET).run()
        df = transform.build_dag(EVENTS).run(df)
        load.build_dag(FEATURES).run(df)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
