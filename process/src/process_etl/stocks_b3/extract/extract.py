from pathlib import Path

from library.process import Dag

from .utils.read_delta import ReadDelta
from .utils.read_parquet import ReadParquet
from .utils.write_delta import WriteDelta


def build_dag(source: Path, target: Path) -> Dag:

    return Dag(
        [
            ReadParquet(source),
            WriteDelta(target),
            ReadDelta(target),
        ]
    )
