import functools
import logging
import shutil
import zipfile
from pathlib import Path

from data_generator.utils import Options, Storage
from data_generator.utils.formats import parquet
from data_generator.utils.network import http

from .constants import (
    CMS,
    PARTD_PARSE,
    PARTD_PART,
    PARTD_QUARTERS,
    PARTD_READ,
    PARTD_SKIPPED,
    PARTD_TABLE,
)

logger = logging.getLogger(__name__)


def partd_destination(output_dir: Path, quarter: str, member: str) -> Path | None:
    """
    Maps an inner file of a Part D quarter to its table folder, or None when it is not a table.
    """
    match = PARTD_TABLE.match(member)
    if member.startswith(PARTD_SKIPPED) or match is None:
        return None
    table = match.group(1).strip().replace(" ", "_")
    part = PARTD_PART.search(member)
    suffix = f"_part{part.group(1)}" if part else ""
    return output_dir / table / f"{quarter}{suffix}.parquet"


def convert_quarter(archive: Path, storage: Storage) -> int:
    """
    Converts every table of a Part D quarter: an outer zip holding one inner zip per file.
    """
    files = 0
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.namelist():
            path = partd_destination(storage.directory, archive.stem, member)
            if path is None or storage.exists(path):
                continue
            inner = storage.directory / "inner.zip"
            try:
                with bundle.open(member) as source, inner.open("wb") as target:
                    shutil.copyfileobj(source, target)
                with zipfile.ZipFile(inner) as table:
                    rows = parquet.csv_to_parquet(
                        functools.partial(table.open, table.namelist()[0]),
                        path,
                        PARTD_PARSE,
                        PARTD_READ,
                    )
            finally:
                inner.unlink(missing_ok=True)
            logger.info("%s/%s: %d rows", path.parent.name, path.name, rows)
            storage.save(path)
            files += 1
    return files


def ingest(storage: Storage, options: Options) -> int:
    """
    Downloads the CMS quarterly Part D formulary, pharmacy network and pricing files into one folder per table.
    """
    files = 0
    for index, path in enumerate(PARTD_QUARTERS, start=1):
        url = f"{CMS}/{path}"
        logger.info("%d/%d %s", index, len(PARTD_QUARTERS), url)
        archive = storage.directory / Path(path).name
        try:
            http.download(url, archive)
            files += convert_quarter(archive, storage)
        finally:
            archive.unlink(missing_ok=True)
    return files
