import os

from pyspark.sql import SparkSession

from .constants import BASE, DELTA, GPU, LOCAL
from .interfaces import Profile


def build_spark(
    app_name: str,
    gpu: bool = False,
    conf: dict[str, str] | None = None,
) -> SparkSession:
    """Builds the Spark session shared by the pipeline jobs.

    Args:
        app_name: Name shown in the Spark UI and History Server.
        gpu: Enables the RAPIDS accelerator.
        cores: Cores used in local mode.

    Returns:
        The active Spark session.
    """
    selected = [BASE, DELTA]

    if gpu:
        selected.append(GPU)

    if "KUBERNETES_SERVICE_HOST" not in os.environ:
        selected.append(LOCAL)
        packages = [p for profile in selected for p in profile.packages]

        if packages:
            selected.append(Profile(conf={"spark.jars.packages": ",".join(packages)}))

    builder = SparkSession.builder.appName(app_name)

    for profile in selected:
        for key, value in profile.conf.items():
            builder = builder.config(key, value)

    for key, value in (conf or {}).items():
        builder = builder.config(key, value)

    return builder.getOrCreate()
