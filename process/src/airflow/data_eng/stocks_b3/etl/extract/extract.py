from library.process import Pipeline

from .utils.read_delta import ReadDelta
from .utils.read_parquet import ReadParquet
from .utils.write_delta import WriteDelta


def build_pipeline(source: str, target: str) -> Pipeline:

    return Pipeline(
        [
            ReadParquet(source),
            WriteDelta(target),
            ReadDelta(target),
        ]
    )
