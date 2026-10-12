from library.process import Pipeline

from . import steps


def build_pipeline(source: str, target: str) -> Pipeline:
    """
    Builds the ETL pipeline: reads the raw parquet, deduplicates it and writes it as Delta.
    """
    return Pipeline(
        [
            steps.ReadParquet(source=source),
            steps.DistinctSelect(),
            steps.UniqueID(),
            steps.WriteDelta(target=target),
        ]
    )
