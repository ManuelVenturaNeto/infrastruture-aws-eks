import argparse
import logging

from library.spark import build_spark

from data_eng.shopping_amazon.etl import pipeline

SOURCE = "process/src/datasets/shopping_amazon_reviews/shopping_amazon_reviews"
TARGET = "process/src/datasets/shopping_amazon_reviews/shopping_amazon_reviews_delta"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=SOURCE)
    parser.add_argument("--target", default=TARGET)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    args = parse_args()
    session = build_spark()
    try:
        pipeline.build_pipeline(source=args.source, target=args.target).run()
    finally:
        session.stop()


if __name__ == "__main__":
    main()
