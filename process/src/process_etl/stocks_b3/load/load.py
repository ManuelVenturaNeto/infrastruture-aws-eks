from pathlib import Path

from library.process import Dag

from .utils.write_features import WriteFeatures


def build_dag(features: Path) -> Dag:
    """
    Builds the load DAG: writes the features table.
    """
    return Dag([WriteFeatures(features)])
