import functools
import logging
import urllib.error
import zipfile
from pathlib import Path

import pyarrow.csv

from . import http, parquet
from .constants import NOT_FOUND

URL = "https://dadosabertos.ans.gov.br/FTP/PDA"
PARSE_OPTIONS = pyarrow.csv.ParseOptions(delimiter=";")
READ_OPTIONS = pyarrow.csv.ReadOptions(block_size=64 << 20)

STATES = (
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
)

logger = logging.getLogger(__name__)


def fetch(url: str, destination: Path) -> bool:
    """
    Downloads one ANS zip and converts its csv into parquet, skipping files already converted or missing upstream.
    """
    if destination.exists():
        return True
    archive = destination.with_suffix(".zip")
    try:
        http.download(url, archive)
        with zipfile.ZipFile(archive) as bundle:
            rows = parquet.csv_to_parquet(
                functools.partial(bundle.open, bundle.namelist()[0]),
                destination,
                PARSE_OPTIONS,
                READ_OPTIONS,
            )
    except urllib.error.HTTPError as error:
        if error.code != NOT_FOUND:
            raise
        logger.warning("%s: not found", url)
        return False
    finally:
        archive.unlink(missing_ok=True)
    logger.info("%s: %d rows", destination.name, rows)
    return True


def fetch_all(sources: list[tuple[str, Path]]) -> int:
    """
    Fetches every (url, destination) pair from ANS and returns how many were converted.
    """
    converted = 0
    for index, (url, destination) in enumerate(sources, start=1):
        logger.info("%d/%d %s", index, len(sources), url)
        converted += fetch(url, destination)
    return converted
