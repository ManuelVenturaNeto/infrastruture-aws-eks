from library.process import Pipeline

from .utils.write_features import WriteFeatures


def build_pipeline(features: str) -> Pipeline:

    return Pipeline([WriteFeatures(features)])
