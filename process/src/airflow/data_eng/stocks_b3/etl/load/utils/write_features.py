from library.process import Step
from pyspark.sql import DataFrame


class WriteFeatures(Step):
    def __init__(self, features: str) -> None:

        self.features = features

    def run(self, df: DataFrame) -> DataFrame:

        (
            df.write.format("delta")
            .partitionBy("year")
            .mode("overwrite")
            .save(self.features)
        )
        return df
