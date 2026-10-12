import argparse
import logging

from data_eng.stocks_b3.etl.config.paths import EVENTS, FEATURES, SOURCE, TARGET
from data_eng.stocks_b3.etl.extract import extract
from data_eng.stocks_b3.etl.load import load
from data_eng.stocks_b3.etl.transform import transform
from library.spark import build_spark


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=SOURCE)
    parser.add_argument("--target", default=TARGET)
    parser.add_argument("--events", default=EVENTS)
    parser.add_argument("--features", default=FEATURES)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    args = parse_args()

    spark = build_spark()
    try:
        df = extract.build_pipeline(args.source, args.target).run()
        df = transform.build_pipeline(args.events).run(df)
        load.build_pipeline(args.features).run(df)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
