from data_generator.utils import Options, Storage
from data_generator.utils.sources import files

AMAZON_META = (
    "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main"
)
AMAZON_META_SHARDS = {
    "All_Beauty": 1,
    "Arts_Crafts_and_Sewing": 4,
    "Cell_Phones_and_Accessories": 7,
    "Electronics": 10,
    "Gift_Cards": 1,
    "Handmade_Products": 1,
    "Industrial_and_Scientific": 2,
    "Musical_Instruments": 2,
    "Toys_and_Games": 5,
}
URLS = [
    f"{AMAZON_META}/raw_meta_{category}/full-{shard:05d}-of-{shards:05d}.parquet"
    for category, shards in AMAZON_META_SHARDS.items()
    for shard in range(shards)
]


def ingest(storage: Storage, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], storage)
