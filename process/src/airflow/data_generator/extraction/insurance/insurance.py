from data_generator.utils import Options, Storage
from data_generator.utils.sources import files

URLS = ["https://data.openml.org/datasets/0004/42742/dataset_42742.pq"]


def ingest(storage: Storage, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], storage)
