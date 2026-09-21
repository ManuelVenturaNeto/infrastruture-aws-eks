from pathlib import Path

from ..config.dag import Dag
from .utils.write_features import WriteFeatures


def build_dag(features: Path) -> Dag:
    """
    Builds the load DAG: writes the features table.
    """
    return Dag([WriteFeatures(features)])
