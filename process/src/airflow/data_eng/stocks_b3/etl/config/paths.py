from pathlib import Path

DATASETS = Path(__file__).resolve().parents[5] / "datasets" / "stocks_b3"
SOURCE = str(DATASETS / "stocks_b3")
TARGET = str(DATASETS / "stocks_b3_delta")
FEATURES = str(DATASETS / "stocks_b3_features")
EVENTS = str(DATASETS / "stocks_b3_events")
