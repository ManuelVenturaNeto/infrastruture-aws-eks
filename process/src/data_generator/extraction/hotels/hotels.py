from pathlib import Path

from data_generator.utils import Options, files

HOTELS = (
    "https://huggingface.co/api/datasets/gemuchu/hotel_bookings/parquet/default/train"
)
URLS = [f"{HOTELS}/0.parquet"]


def ingest(output_dir: Path, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], output_dir)
