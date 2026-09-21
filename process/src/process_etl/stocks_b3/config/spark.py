from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession


def build_spark() -> SparkSession:
    """
    Builds the local Spark session with Delta Lake enabled and optimized write settings.
    """
    return configure_spark_with_delta_pip(
        SparkSession.builder.appName("stocks_b3")
        .master("local[4]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.driver.memory", "6g")
        .config("spark.sql.parquet.compression.codec", "zstd")
        .config("spark.databricks.delta.optimizeWrite.enabled", "true")
        .config("spark.databricks.delta.autoCompact.enabled", "true")
        .config("spark.databricks.delta.optimize.maxFileSize", "268435456")
        .config("spark.ui.showConsoleProgress", "true")
    ).getOrCreate()
