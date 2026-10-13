import logging
from collections.abc import Callable
from pathlib import Path

from ..network import http
from ..storage import Storage

SUFFIXES = (".tsv.gz", ".parquet", ".pq")

logger = logging.getLogger(__name__)


def parquet_name(url: str) -> str:
    name = Path(url).name
    for suffix in SUFFIXES:
        name = name.removesuffix(suffix)
    return f"{name}.parquet"


def unique_names(urls: list[str]) -> list[str]:
    """
    Names each url's parquet file, prefixing the parent folder when two urls share a file name.
    """
    names = [parquet_name(url) for url in urls]
    if len(set(names)) == len(names):
        return names
    return [f"{Path(url).parent.name}_{name}" for url, name in zip(urls, names)]


def fetch_all(
    urls: list[str],
    storage: Storage,
    fetch: Callable[[str, Path], None] = http.download,
) -> int:
    for index, (url, name) in enumerate(zip(urls, unique_names(urls)), start=1):
        path = storage.directory / name
        if storage.exists(path):
            continue
        logger.info("%d/%d %s", index, len(urls), url)
        fetch(url, path)
        storage.save(path)
    return len(urls)
