import functools
import logging
from pathlib import Path

import pyarrow as pa
import pyarrow.csv

from data_generator.utils import Options, files, http, parquet

MOVIES_IMDB = "https://datasets.imdbws.com"
IMDB_TABLES = (
    "title.basics",
    "title.akas",
    "title.crew",
    "title.episode",
    "title.principals",
    "title.ratings",
    "name.basics",
)
URLS = [f"{MOVIES_IMDB}/{table}.tsv.gz" for table in IMDB_TABLES]

PARSE_OPTIONS = pyarrow.csv.ParseOptions(delimiter="\t", quote_char=False)
NULL_MARKER = "\\N"

logger = logging.getLogger(__name__)


def fetch(url: str, destination: Path) -> None:
    archive = destination.with_name(f"{destination.stem}.tsv.gz")
    try:
        http.download(url, archive)
        rows = parquet.csv_to_parquet(
            functools.partial(pa.input_stream, archive, compression="gzip"),
            destination,
            PARSE_OPTIONS,
            null_values=[NULL_MARKER],
        )
    finally:
        archive.unlink(missing_ok=True)
    logger.info("%s: %d rows", destination.name, rows)


def ingest(output_dir: Path, options: Options) -> int:
    return files.fetch_all(URLS[: options.files], output_dir, fetch)
