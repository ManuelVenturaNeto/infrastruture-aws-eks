import argparse
import logging
import urllib.request
from pathlib import Path

import pyarrow as pa
import pyarrow.csv
import pyarrow.parquet as pq

OPENML = "https://data.openml.org/datasets/0004"
OLIST = "https://huggingface.co/api/datasets/miminmoons/olist-ecommerce-for-delivery-and-review-prediction/parquet/default/train"
FANNIE = "https://huggingface.co/api/datasets/yeigen/fannie-mae-loan-performance/parquet/default/train"
HOTEIS = "https://huggingface.co/api/datasets/gemuchu/hotel_bookings/parquet/default/train"
FILMES_IMDB = "https://datasets.imdbws.com"
FILMES_AMAZON = "https://huggingface.co/api/datasets/rohan2810/amazon-movies-meta-reviews-merged/parquet/default/train"

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
    "credito": [f"{OPENML}/46929/dataset_46929.pq"],
    "seguros": [f"{OPENML}/42742/dataset_42742.pq"],
    "cartao": [f"{OPENML}/42175/dataset_42175.pq"],
    "shopping": [f"{OLIST}/0.parquet"],
    "imoveis": [f"{FANNIE}/{part}.parquet" for part in range(6765)],
    "hoteis": [f"{HOTEIS}/0.parquet"],
    "filmes_imdb": [f"{FILMES_IMDB}/{table}.tsv.gz" for table in IMDB_TABLES],
    "filmes_amazon": [f"{FILMES_AMAZON}/{part}.parquet" for part in range(33)],
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
    return pyarrow.csv.open_csv(stream, parse_options=PARSE_OPTIONS, convert_options=convert_options)


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


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=DATASETS)
    parser.add_argument("--out", default="src/datasets")
    parser.add_argument("--files", type=int, default=400)
    args = parser.parse_args()

    urls = DATASETS[args.name][: args.files]
    output_dir = Path(args.out) / args.name
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(urls, start=1):
        logger.info("%d/%d %s", index, len(urls), url)
        fetch(url, output_dir / parquet_name(url))

    total_bytes = sum(f.stat().st_size for f in output_dir.glob("*.parquet"))
    logger.info("done: %d files, %.2f GB", len(urls), total_bytes / (1 << 30))


if __name__ == "__main__":
    main()
