from pathlib import Path

from data_generator.utils import Options, files

OLIST = "https://huggingface.co/api/datasets/miminmoons/olist-ecommerce-for-delivery-and-review-prediction/parquet/default/train"
URLS = [f"{OLIST}/0.parquet"]


def ingest(output_dir: Path, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], output_dir)
