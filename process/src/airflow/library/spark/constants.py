from .interfaces import Profile

BASE = Profile(
    conf={
        "spark.sql.parquet.compression.codec": "zstd",
        "spark.sql.session.timeZone": "UTC",
    }
)

LOCAL = Profile(conf={"spark.master": "local[4]", "spark.driver.memory": "6g"})

DELTA = Profile(
    conf={
        "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
        "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        "spark.databricks.delta.optimizeWrite.enabled": "true",
        "spark.databricks.delta.autoCompact.enabled": "true",
        "spark.databricks.delta.optimize.maxFileSize": "268435456",
    },
    packages=("io.delta:delta-spark_4.2_2.13:4.4.0",),
)

GPU = Profile(
    conf={
        "spark.plugins": "com.nvidia.spark.SQLPlugin",
        "spark.rapids.sql.enabled": "true",
        "spark.rapids.sql.concurrentGpuTasks": "1",
        "spark.rapids.memory.gpu.allocFraction": "0.8",
        "spark.rapids.sql.explain": "NOT_ON_GPU",
    },
    packages=("com.nvidia:rapids-4-spark_2.13:26.08.1",),
)
