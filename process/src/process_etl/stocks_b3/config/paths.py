from pathlib import Path

DATASETS = next(
    path / "datasets"
    for path in Path(__file__).resolve().parents
    if (path / "datasets").is_dir()
)
SOURCE = DATASETS / "stocks_b3"
TARGET = DATASETS / "stocks_b3_delta"
FEATURES = DATASETS / "stocks_b3_features"
EVENTS = DATASETS / "stocks_b3_events"
