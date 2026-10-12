from pathlib import Path

from data_generator.utils import Options, files

MOVIES_AMAZON = "https://huggingface.co/api/datasets/rohan2810/amazon-movies-meta-reviews-merged/parquet/default/train"
PARTS = 33
URLS = [f"{MOVIES_AMAZON}/{part}.parquet" for part in range(PARTS)]


def ingest(output_dir: Path, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], output_dir)
