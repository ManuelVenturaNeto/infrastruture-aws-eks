import logging
import shutil
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv
import pyarrow.parquet as pq

COTAHIST = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP"
FIRST_YEAR = 1986
HEADERS = {"User-Agent": "Mozilla/5.0"}

TEXT, INT, PRICE, DATE = "text", "int", "price", "date"
QUOTE_RECORD = "01"
PRICE_SCALE = 100.0

LAYOUT = (
    ("trade_date", 3, 10, DATE),
    ("bdi_code", 11, 12, TEXT),
    ("ticker", 13, 24, TEXT),
    ("market_type", 25, 27, TEXT),
    ("company_name", 28, 39, TEXT),
    ("specification", 40, 49, TEXT),
    ("forward_term", 50, 52, TEXT),
    ("currency", 53, 56, TEXT),
    ("open_price", 57, 69, PRICE),
    ("high_price", 70, 82, PRICE),
    ("low_price", 83, 95, PRICE),
    ("average_price", 96, 108, PRICE),
    ("close_price", 109, 121, PRICE),
    ("best_bid_price", 122, 134, PRICE),
    ("best_ask_price", 135, 147, PRICE),
    ("total_trades", 148, 152, INT),
    ("total_quantity", 153, 170, INT),
    ("total_volume", 171, 188, PRICE),
    ("strike_price", 189, 201, PRICE),
    ("correction_indicator", 202, 202, TEXT),
    ("expiration_date", 203, 210, DATE),
    ("quote_factor", 211, 217, INT),
    ("strike_points", 218, 230, INT),
    ("isin_code", 231, 242, TEXT),
    ("distribution_number", 243, 245, INT),
)

READ_OPTIONS = pyarrow.csv.ReadOptions(
    column_names=["line"], encoding="latin-1", block_size=64 << 20
)
PARSE_OPTIONS = pyarrow.csv.ParseOptions(delimiter="\x01", quote_char=False)
CONVERT_OPTIONS = pyarrow.csv.ConvertOptions(column_types={"line": pa.string()})

logger = logging.getLogger(__name__)


def last_year() -> int:
    return datetime.now(tz=UTC).year


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
            stream,
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


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request) as response, destination.open("wb") as file:
        shutil.copyfileobj(response, file)


def fetch(year: int, output_dir: Path) -> None:
    archive = output_dir / f"cotahist_{year}.zip"
    destination = output_dir / f"cotahist_{year}.parquet"
    try:
        download(COTAHIST.format(year=year), archive)
        rows = convert(archive, destination)
    finally:
        archive.unlink(missing_ok=True)
    logger.info("%s: %d rows", destination.name, rows)


def generate(output_dir: Path, start_year: int | None, end_year: int | None) -> int:
    start = start_year or FIRST_YEAR
    end = end_year or last_year()
    if start > end:
        raise ValueError(f"start_year {start} is after end_year {end}")
    years = range(start, end + 1)
    for index, year in enumerate(years, start=1):
        logger.info("%d/%d %s", index, len(years), COTAHIST.format(year=year))
        fetch(year, output_dir)
    return len(years)
