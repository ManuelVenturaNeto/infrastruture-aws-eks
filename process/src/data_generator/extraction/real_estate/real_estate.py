from pathlib import Path

from data_generator.utils import Options, files

FANNIE = "https://huggingface.co/api/datasets/yeigen/fannie-mae-loan-performance/parquet/default/train"
PARTS = 6765
URLS = [f"{FANNIE}/{part}.parquet" for part in range(PARTS)]


def ingest(output_dir: Path, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], output_dir)
