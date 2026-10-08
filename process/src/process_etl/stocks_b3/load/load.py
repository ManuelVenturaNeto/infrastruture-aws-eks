from pathlib import Path

from library.process import Dag

from .utils.write_features import WriteFeatures


def build_dag(features: Path) -> Dag:

    return Dag([WriteFeatures(features)])
