from pathlib import Path

from pyspark.sql import DataFrame

from ...config.dag import Step


class WriteFeatures(Step):
    def __init__(self, features: Path) -> None:
        """
        Stores the features table target directory.
        """
        self.features = features

    def run(self, df: DataFrame) -> DataFrame:
        """
        Writes the features as Delta partitioned by year, overwriting the previous version.
        """
        (
            df.write.format("delta")
            .partitionBy("year")
            .mode("overwrite")
            .save(str(self.features))
        )
        return df
