from data_generator.utils import Options, Storage
from data_generator.utils.sources import files

HOTELS = (
    "https://huggingface.co/api/datasets/gemuchu/hotel_bookings/parquet/default/train"
)
URLS = [f"{HOTELS}/0.parquet"]


def ingest(storage: Storage, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], storage)
