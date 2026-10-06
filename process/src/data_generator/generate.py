import argparse
import logging
import urllib.request
from pathlib import Path

import generate_insurance
import generate_stocks
import pyarrow as pa
import pyarrow.csv
import pyarrow.parquet as pq

OPENML = "https://data.openml.org/datasets/0004"
OLIST = "https://huggingface.co/api/datasets/miminmoons/olist-ecommerce-for-delivery-and-review-prediction/parquet/default/train"
FANNIE = "https://huggingface.co/api/datasets/yeigen/fannie-mae-loan-performance/parquet/default/train"
HOTELS = (
    "https://huggingface.co/api/datasets/gemuchu/hotel_bookings/parquet/default/train"
)
MOVIES_IMDB = "https://datasets.imdbws.com"
MOVIES_AMAZON = "https://huggingface.co/api/datasets/rohan2810/amazon-movies-meta-reviews-merged/parquet/default/train"
AMAZON_REVIEWS = "https://huggingface.co/api/datasets/gmongaras/Amazon-Reviews-2023/parquet/default/train"
AMAZON_META = (
    "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main"
)

AMAZON_REVIEWS_FILES = 26
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

IMDB_TABLES = (
    "title.basics",
    "title.akas",
    "title.crew",
    "title.episode",
    "title.principals",
    "title.ratings",
    "name.basics",
)

DATASETS = {
    "credit": [f"{OPENML}/46929/dataset_46929.pq"],
    "insurance": [f"{OPENML}/42742/dataset_42742.pq"],
    "cards": [f"{OPENML}/42175/dataset_42175.pq"],
    "shopping": [f"{OLIST}/0.parquet"],
    "real_estate": [f"{FANNIE}/{part}.parquet" for part in range(6765)],
    "hotels": [f"{HOTELS}/0.parquet"],
    "movies_imdb": [f"{MOVIES_IMDB}/{table}.tsv.gz" for table in IMDB_TABLES],
    "movies_amazon": [f"{MOVIES_AMAZON}/{part}.parquet" for part in range(33)],
    "shopping_amazon_reviews": [
        f"{AMAZON_REVIEWS}/{part}.parquet" for part in range(AMAZON_REVIEWS_FILES)
    ],
    "shopping_amazon_meta": [
        f"{AMAZON_META}/raw_meta_{category}/full-{shard:05d}-of-{shards:05d}.parquet"
        for category, shards in AMAZON_META_SHARDS.items()
        for shard in range(shards)
    ],
}

STOCKS_B3 = "stocks_b3"
INSURANCE = {
    "insurance_health_claims": generate_insurance.generate_health_claims,
    "insurance_health_beneficiaries": generate_insurance.generate_health_beneficiaries,
    "insurance_medicare_partd": generate_insurance.generate_medicare_partd,
}

SUFFIXES = (".tsv.gz", ".parquet", ".pq")
PARSE_OPTIONS = pyarrow.csv.ParseOptions(delimiter="\t", quote_char=False)
NULL_MARKER = "\\N"

logger = logging.getLogger(__name__)


def parquet_name(url: str) -> str:
    name = Path(url).name
    for suffix in SUFFIXES:
        name = name.removesuffix(suffix)
    return f"{name}.parquet"


def open_tsv(archive: Path, convert_options: pyarrow.csv.ConvertOptions | None = None):
    stream = pa.input_stream(archive, compression="gzip")
    return pyarrow.csv.open_csv(
        stream, parse_options=PARSE_OPTIONS, convert_options=convert_options
    )


def convert(archive: Path, destination: Path) -> None:
    column_names = open_tsv(archive).schema.names
    convert_options = pyarrow.csv.ConvertOptions(
        column_types={name: pa.string() for name in column_names},
        null_values=[NULL_MARKER],
    )
    reader = open_tsv(archive, convert_options)
    writer = pq.ParquetWriter(destination, reader.schema, compression="zstd")
    rows = 0
    for batch in reader:
        writer.write_batch(batch)
        rows += batch.num_rows
    writer.close()
    logger.info("%s: %d rows, %d columns", destination.name, rows, len(column_names))


def fetch(url: str, destination: Path) -> None:
    if not url.endswith(".tsv.gz"):
        urllib.request.urlretrieve(url, destination)
        return
    archive = destination.with_name(f"{destination.stem}.tsv.gz")
    urllib.request.urlretrieve(url, archive)
    convert(archive, destination)
    archive.unlink()


def unique_names(urls: list[str]) -> list[str]:
    """
    Names each url's parquet file, prefixing the parent folder when two urls share a file name.
    """
    names = [parquet_name(url) for url in urls]
    if len(set(names)) == len(names):
        return names
    return [f"{Path(url).parent.name}_{name}" for url, name in zip(urls, names)]


def fetch_all(urls: list[str], output_dir: Path) -> int:
    for index, (url, name) in enumerate(zip(urls, unique_names(urls)), start=1):
        logger.info("%d/%d %s", index, len(urls), url)
        fetch(url, output_dir / name)
    return len(urls)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=(*DATASETS, STOCKS_B3, *INSURANCE))
    parser.add_argument("--out", default="process/src/datasets")
    parser.add_argument("--files", type=int, default=400)
    parser.add_argument("--start_year", type=int)
    parser.add_argument("--end_year", type=int)
    args = parser.parse_args()

    output_dir = Path(args.out) / args.name / args.name
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.name == STOCKS_B3:
        files = generate_stocks.generate(output_dir, args.start_year, args.end_year)
        generate_stocks.generate_events(output_dir.with_name(f"{args.name}_events"))
    elif args.name in INSURANCE:
        files = INSURANCE[args.name](output_dir)
    else:
        files = fetch_all(DATASETS[args.name][: args.files], output_dir)

    total_bytes = sum(f.stat().st_size for f in output_dir.rglob("*.parquet"))
    logger.info("done: %d files, %.2f GB", files, total_bytes / (1 << 30))


if __name__ == "__main__":
    main()
