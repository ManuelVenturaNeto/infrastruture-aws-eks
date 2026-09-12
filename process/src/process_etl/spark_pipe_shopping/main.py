import argparse

from pyspark.sql import DataFrame, SparkSession

DEFAULT_INPUT = "file:///opt/spark/datasets/shopping"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--rows", type=int, default=20)
    return parser.parse_args()


def read(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.parquet(path)


def report(frame: DataFrame, rows: int) -> None:
    frame.printSchema()
    frame.show(rows, truncate=False)
    print(f"rows={frame.count()} columns={len(frame.columns)}")


def main() -> None:
    args = parse_args()

    spark = SparkSession.builder.appName("shopping-etl").getOrCreate()
    try:
        report(read(spark, args.input), args.rows)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
