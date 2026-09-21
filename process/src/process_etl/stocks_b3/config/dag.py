from abc import ABC, abstractmethod

from pyspark.sql import DataFrame


class Step(ABC):
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
        return df
