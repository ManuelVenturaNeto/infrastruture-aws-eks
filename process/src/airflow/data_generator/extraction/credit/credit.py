from data_generator.utils import Options, Storage
from data_generator.utils.sources import files

URLS = ["https://data.openml.org/datasets/0004/46929/dataset_46929.pq"]


def ingest(storage: Storage, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], storage)
