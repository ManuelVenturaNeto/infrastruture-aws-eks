from abc import ABC, abstractmethod

from pyspark.sql import DataFrame, SparkSession


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
        for step in self.steps:
            df = step.run(df)

            if not isinstance(df, DataFrame):
                raise TypeError(
                    f"{type(step).__name__}.run() returned {type(df).__name__}, expected DataFrame"
                )

        return df
