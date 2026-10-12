from pathlib import Path

from data_generator.utils import Options, files

AMAZON_REVIEWS = "https://huggingface.co/api/datasets/gmongaras/Amazon-Reviews-2023/parquet/default/train"
AMAZON_REVIEWS_FILES = 26
URLS = [f"{AMAZON_REVIEWS}/{part}.parquet" for part in range(AMAZON_REVIEWS_FILES)]


def ingest(output_dir: Path, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], output_dir)
