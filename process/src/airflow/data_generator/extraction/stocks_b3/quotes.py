import io
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv
import pyarrow.parquet as pq

from data_generator.utils import Storage
from data_generator.utils.network import http

from .constants import (
    CONVERT_OPTIONS,
    COTAHIST,
    DELIMITER,
    FIRST_YEAR,
    INT,
    LAYOUT,
    PARSE_OPTIONS,
    PRICE,
    PRICE_SCALE,
    QUOTE_RECORD,
    READ_OPTIONS,
    TEXT,
)

logger = logging.getLogger(__name__)


class SanitizedStream(io.RawIOBase):
    def __init__(self, stream):
        self.stream = stream

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        data = self.stream.read(len(buffer)).replace(DELIMITER.encode(), b" ")
        buffer[: len(data)] = data
        return len(data)


def last_year() -> int:
    return datetime.now(tz=timezone.utc).year


def field(lines: pa.Array, start: int, end: int, kind: str) -> pa.Array:
    raw = pc.utf8_slice_codeunits(lines, start - 1, end)
    if kind == TEXT:
        return pc.utf8_trim_whitespace(raw)
    if kind == INT:
        return raw.cast(pa.int64())
    if kind == PRICE:
        return pc.divide(raw.cast(pa.int64()), PRICE_SCALE)
    return pc.strptime(raw, format="%Y%m%d", unit="s").cast(pa.date32())


def parse(lines: pa.Array) -> pa.RecordBatch:
    record_type = pc.utf8_slice_codeunits(lines, 0, 2)
    quotes = pc.filter(lines, pc.equal(record_type, QUOTE_RECORD))
    columns = {
        name: field(quotes, start, end, kind) for name, start, end, kind in LAYOUT
    }
    return pa.RecordBatch.from_pydict(columns)


def convert(archive: Path, destination: Path) -> int:
    rows = 0
    writer = None
    with (
        zipfile.ZipFile(archive) as bundle,
        bundle.open(bundle.namelist()[0]) as stream,
    ):
        reader = pyarrow.csv.open_csv(
            io.BufferedReader(SanitizedStream(stream)),
            read_options=READ_OPTIONS,
            parse_options=PARSE_OPTIONS,
            convert_options=CONVERT_OPTIONS,
        )
        for batch in reader:
            parsed = parse(batch.column(0))
            if writer is None:
                writer = pq.ParquetWriter(
                    destination, parsed.schema, compression="zstd"
                )
            writer.write_batch(parsed)
            rows += parsed.num_rows
    if writer is not None:
        writer.close()
    return rows


def fetch(year: int, storage: Storage) -> None:
    archive = storage.directory / f"cotahist_{year}.zip"
    path = storage.directory / f"cotahist_{year}.parquet"
    try:
        http.download(COTAHIST.format(year=year), archive)
        rows = convert(archive, path)
    finally:
        archive.unlink(missing_ok=True)
    logger.info("%s: %d rows", path.name, rows)
    storage.save(path)


def generate(storage: Storage, start_year: int | None, end_year: int | None) -> int:
    start = start_year or FIRST_YEAR
    end = end_year or last_year()
    if start > end:
        raise ValueError(f"start_year {start} is after end_year {end}")
    years = range(start, end + 1)
    for index, year in enumerate(years, start=1):
        logger.info("%d/%d %s", index, len(years), COTAHIST.format(year=year))
        fetch(year, storage)
    return len(years)
