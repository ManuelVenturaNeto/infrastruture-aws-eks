from data_generator.utils import Options, Storage
from data_generator.utils.sources import files

FANNIE = "https://huggingface.co/api/datasets/yeigen/fannie-mae-loan-performance/parquet/default/train"
PARTS = 6765
URLS = [f"{FANNIE}/{part}.parquet" for part in range(PARTS)]


def ingest(storage: Storage, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], storage)
