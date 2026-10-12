from pathlib import Path

from data_generator.utils import Options, files

URLS = ["https://data.openml.org/datasets/0004/42175/dataset_42175.pq"]


def ingest(output_dir: Path, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], output_dir)
