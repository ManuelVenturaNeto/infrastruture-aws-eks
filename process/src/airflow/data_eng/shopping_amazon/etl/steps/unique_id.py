from library.process import Step
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


class UniqueID(Step):
    def run(self, df: DataFrame) -> DataFrame:
        window = Window.partitionBy("id").orderBy("rating", "full_text")
        return (
            df.withColumn("row_number", F.row_number().over(window))
            .filter(F.col("row_number") == 1)
            .drop("row_number")
        )
