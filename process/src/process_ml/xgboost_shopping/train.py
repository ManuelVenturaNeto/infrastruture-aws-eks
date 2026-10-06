import argparse

from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import DataFrame, SparkSession
from xgboost.spark import SparkXGBRegressor

DEFAULT_INPUT = "file:///opt/spark/datasets/shopping"
LABEL = "delivery_delay_hours"
FEATURES = [
    "price",
    "freight_value",
    "product_description_lenght",
    "product_photos_qty",
    "time_to_ship_hours",
    "purchase_count",
    "avg_review_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--rounds", type=int, default=100)
    return parser.parse_args()


def prepare(spark: SparkSession, path: str) -> DataFrame:
    frame = spark.read.parquet(path).select(LABEL, *FEATURES).dropna()
    assembler = VectorAssembler(inputCols=FEATURES, outputCol="features")
    return assembler.transform(frame).select("features", LABEL)


def train(frame: DataFrame, device: str, workers: int, rounds: int):
    regressor = SparkXGBRegressor(
        features_col="features",
        label_col=LABEL,
        device=device,
        num_workers=workers,
        n_estimators=rounds,
        max_depth=6,
    )
    return regressor.fit(frame)


def main() -> None:
    args = parse_args()

    spark = SparkSession.builder.appName("shopping-xgboost").getOrCreate()
    try:
        data = prepare(spark, args.input)
        train_set, test_set = data.randomSplit([0.8, 0.2], seed=42)
        print(
            f"device={args.device} workers={args.workers} train={train_set.count()} test={test_set.count()}"
        )

        model = train(train_set, args.device, args.workers, args.rounds)

        evaluator = RegressionEvaluator(
            labelCol=LABEL, predictionCol="prediction", metricName="rmse"
        )
        rmse = evaluator.evaluate(model.transform(test_set))
        print(f"rmse={rmse:.4f}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
