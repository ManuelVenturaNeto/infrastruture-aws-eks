from library.spark import build_spark

from . import dag

SOURCE = "process/src/datasets/shopping_amazon_reviews/shopping_amazon_reviews"
TARGET = "process/src/datasets/shopping_amazon_reviews/shopping_amazon_reviews_delta"


def main() -> None:
    session = build_spark("shopping_amazon", gpu=True)
    try:
        dag.build_dag(source=SOURCE, target=TARGET).run()
    finally:
        session.stop()


if __name__ == "__main__":
    main()
