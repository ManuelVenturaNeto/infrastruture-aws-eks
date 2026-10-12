import os

from pyspark.sql import SparkSession

from .constants import BASE, DELTA, GPU, LOCAL
from .interfaces import Profile
from .resources import log_resources


def build_spark(conf: dict[str, str] | None = None) -> SparkSession:
    """Builds the Spark session shared by the pipeline jobs.

    The name shown in the Spark UI and History Server comes from SPARK_APP_NAME,
    set by the DAG as <dag_id>_<task_id>; local runs fall back to "local".

    Args:
        conf: Extra Spark settings applied last.

    Returns:
        The active Spark session.
    """
    selected = [BASE, DELTA]

    if os.environ.get("SPARK_GPU") == "true":
        selected.append(GPU)

    if "KUBERNETES_SERVICE_HOST" not in os.environ:
        selected.append(LOCAL)
        packages = [p for profile in selected for p in profile.packages]

        if packages:
            selected.append(Profile(conf={"spark.jars.packages": ",".join(packages)}))

    builder = SparkSession.builder.appName(os.environ.get("SPARK_APP_NAME", "local"))

    for profile in selected:
        for key, value in profile.conf.items():
            builder = builder.config(key, value)

    for key, value in (conf or {}).items():
        builder = builder.config(key, value)

    session = builder.getOrCreate()
    log_resources(session)
    return session
