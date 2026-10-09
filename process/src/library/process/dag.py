import logging
import time
from abc import ABC, abstractmethod

from pyspark.sql import DataFrame, SparkSession

logger = logging.getLogger(__name__)


class Step(ABC):
    @property
    def spark(self) -> SparkSession:
        """
        Returns the Spark session started by the job's entry point.
        """
        return SparkSession.getActiveSession()

    @abstractmethod
    def run(self, df: DataFrame) -> DataFrame:
        """
        Takes a DataFrame, applies this step's transformation and returns the result.
        """


class Dag:
    def __init__(self, steps: list[Step]) -> None:
        """
        Stores the ordered list of steps that make up the pipeline.
        """
        self.steps = steps

    def run(self, df: DataFrame | None = None) -> DataFrame:
        """
        Runs the steps in order, feeding each step's output into the next one.
        """
        app = SparkSession.getActiveSession().conf.get("spark.app.name")
        logger.info("job %s started", app)
        started = time.monotonic()

        try:
            for step in self.steps:
                name = type(step).__name__
                logger.info("step %s started", name)

                df = step.run(df)

                if not isinstance(df, DataFrame):
                    raise TypeError(
                        f"{name}.run() returned {type(df).__name__}, expected DataFrame"
                    )

                logger.info("step %s finished", name)

        except Exception:
            logger.exception(
                "job %s failed after %.1fs", app, time.monotonic() - started
            )
            raise

        logger.info("job %s finished in %.1fs", app, time.monotonic() - started)
        return df
