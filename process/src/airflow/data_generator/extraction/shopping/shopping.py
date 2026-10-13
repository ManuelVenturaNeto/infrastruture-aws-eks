from data_generator.utils import Options, Storage
from data_generator.utils.sources import files

OLIST = "https://huggingface.co/api/datasets/miminmoons/olist-ecommerce-for-delivery-and-review-prediction/parquet/default/train"
URLS = [f"{OLIST}/0.parquet"]


def ingest(storage: Storage, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], storage)
