from data_generator.utils import Options, Storage
from data_generator.utils.sources import files

MOVIES_AMAZON = "https://huggingface.co/api/datasets/rohan2810/amazon-movies-meta-reviews-merged/parquet/default/train"
PARTS = 33
URLS = [f"{MOVIES_AMAZON}/{part}.parquet" for part in range(PARTS)]


def ingest(storage: Storage, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], storage)
