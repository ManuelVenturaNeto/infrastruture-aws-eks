from pathlib import Path

from library.process import Step
from pyspark.sql import DataFrame


class WriteFeatures(Step):
    def __init__(self, features: Path) -> None:

        self.features = features

    def run(self, df: DataFrame) -> DataFrame:

        (
            df.write.format("delta")
            .partitionBy("year")
            .mode("overwrite")
            .save(str(self.features))
        )
        return df
