from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession

RAPIDS_PACKAGE = "com.nvidia:rapids-4-spark_2.13:26.08.1"


def build_spark(app_name: str, gpu: bool = False) -> SparkSession:
    """
    Builds the local Spark session with Delta Lake enabled and optimized write settings.
    """
    builder = (
        SparkSession.builder.appName(app_name)
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
        .config("spark.sql.session.timeZone", "UTC")
    )
    if gpu:
        builder = (
            builder.config("spark.plugins", "com.nvidia.spark.SQLPlugin")
            .config("spark.rapids.sql.enabled", "true")
            .config("spark.rapids.sql.concurrentGpuTasks", "1")
            .config("spark.rapids.memory.gpu.allocFraction", "0.8")
            .config("spark.rapids.sql.explain", "NOT_ON_GPU")
        )
    extra_packages = [RAPIDS_PACKAGE] if gpu else []
    return configure_spark_with_delta_pip(
        builder, extra_packages=extra_packages
    ).getOrCreate()
