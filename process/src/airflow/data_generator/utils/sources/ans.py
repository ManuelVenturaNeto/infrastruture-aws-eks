import functools
import logging
import urllib.error
import zipfile
from pathlib import Path

import pyarrow.csv

from ..formats import parquet
from ..network import http
from ..network.constants import NOT_FOUND
from ..storage import Storage

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


def fetch(url: str, path: Path, storage: Storage) -> bool:
    """
    Downloads one ANS zip and converts its csv into parquet, skipping files already converted or missing upstream.
    """
    if storage.exists(path):
        return True
    archive = path.with_suffix(".zip")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        http.download(url, archive)
        with zipfile.ZipFile(archive) as bundle:
            rows = parquet.csv_to_parquet(
                functools.partial(bundle.open, bundle.namelist()[0]),
                path,
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
    logger.info("%s: %d rows", path.name, rows)
    storage.save(path)
    return True


def fetch_all(sources: list[tuple[str, Path]], storage: Storage) -> int:
    """
    Fetches every (url, path) pair from ANS and returns how many were converted.
    """
    converted = 0
    for index, (url, path) in enumerate(sources, start=1):
        logger.info("%d/%d %s", index, len(sources), url)
        converted += fetch(url, path, storage)
    return converted
