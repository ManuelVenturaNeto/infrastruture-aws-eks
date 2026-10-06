import logging
import re
import shutil
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pyarrow as pa
import pyarrow.csv
import pyarrow.parquet as pq

ANS = "https://dadosabertos.ans.gov.br/FTP/PDA"
TISS = f"{ANS}/TISS"
BENEFICIARIES = f"{ANS}/informacoes_consolidadas_de_beneficiarios-024"
CMS = "https://data.cms.gov/sites/default/files"
HEADERS = {"User-Agent": "Mozilla/5.0"}
ATTEMPTS = 3
NOT_FOUND = 404

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

TISS_SCOPES = (
    ("AMBULATORIAL", "AMB", "outpatient", range(2024, 2026)),
    ("HOSPITALAR", "HOSP", "hospital", range(2015, 2026)),
)
TISS_TABLES = {"CONS": "events", "DET": "items"}

BENEFICIARIES_FIRST = (2021, 5)
BENEFICIARIES_LAST = (2026, 8)

PARTD_QUARTERS = (
    "2025-01/1fc9b722-db45-4925-96c0-1bde30a2ae0f/SPUF_2024_20250131_2023q4.zip",
    "2025-04/09f4af93-d0b0-477c-99dc-c9a253d791c7/SPUF_2024_20250331_2024Q1.zip",
    "2025-04/bfb248f9-ef09-4e80-9ba5-4ff6e39fa037/SPUF_2024_20250331_2024Q2.zip",
    "2025-05/e015bae0-4b23-455d-8243-65aef830ab3c/SPUF_2024_20250430_2024Q3.zip",
    "2025-01/e78ce888-f571-4d86-baf0-7a1f9efffff4/SPUF_2025_20250109.zip",
    "2025-04/f868af60-dc78-4e9f-982c-31f53c1ad6a6/SPUF_2025_20250410.zip",
    "2025-07/f96da400-b96c-4a14-9a01-730f8a3e294f/SPUF_2025_20250703.zip",
    "2025-10/6b0620f5-9259-4f1f-929c-70feb8857887/SPUF_2025_20251009.zip",
    "2026-01/5942aa7e-a0c4-4e65-bd56-32608c33649f/SPUF_2026_20260107.zip",
    "2026-04/65e8dafd-c42b-4c2a-93c2-551bbc80bef9/SPUF_2026_20260408.zip",
    "2026-07/64c8d9e1-f350-45e5-88d8-5a2acce2b2d4/SPUF_2026_20260701.zip",
)
PARTD_SKIPPED = "sample"
PARTD_TABLE = re.compile(r"(.+?)\s+(?:file\s+)?PPUF")
PARTD_PART = re.compile(r"part (\d+)")

ANS_PARSE = pyarrow.csv.ParseOptions(delimiter=";")
PARTD_PARSE = pyarrow.csv.ParseOptions(delimiter="|", quote_char=False)
PARTD_READ = pyarrow.csv.ReadOptions(encoding="latin-1", block_size=64 << 20)
ANS_READ = pyarrow.csv.ReadOptions(block_size=64 << 20)

logger = logging.getLogger(__name__)


def download(url: str, destination: Path) -> None:
    """
    Downloads a file, retrying a few times before giving up; a missing file raises at once.
    """
    for attempt in range(1, ATTEMPTS + 1):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with (
                urllib.request.urlopen(request, timeout=300) as response,
                destination.open("wb") as file,
            ):
                shutil.copyfileobj(response, file)
            return
        except urllib.error.HTTPError as error:
            if error.code == NOT_FOUND or attempt == ATTEMPTS:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == ATTEMPTS:
                raise
        time.sleep(attempt)


def convert(
    archive: zipfile.ZipFile,
    member: str,
    destination: Path,
    parse_options: pyarrow.csv.ParseOptions,
    read_options: pyarrow.csv.ReadOptions,
) -> int:
    """
    Converts one delimited text member of a zip archive into a zstd parquet file with every column as string.
    """
    with archive.open(member) as stream:
        column_names = pyarrow.csv.open_csv(
            stream, read_options=read_options, parse_options=parse_options
        ).schema.names
    convert_options = pyarrow.csv.ConvertOptions(
        column_types={name: pa.string() for name in column_names}
    )
    rows = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(member) as stream:
        reader = pyarrow.csv.open_csv(
            stream,
            read_options=read_options,
            parse_options=parse_options,
            convert_options=convert_options,
        )
        with pq.ParquetWriter(destination, reader.schema, compression="zstd") as writer:
            for batch in reader:
                writer.write_batch(batch)
                rows += batch.num_rows
    return rows


def fetch_ans(url: str, destination: Path) -> bool:
    """
    Downloads one ANS zip and converts its csv into parquet, skipping files already converted or missing upstream.
    """
    if destination.exists():
        return True
    archive = destination.with_suffix(".zip")
    try:
        download(url, archive)
        with zipfile.ZipFile(archive) as bundle:
            rows = convert(
                bundle, bundle.namelist()[0], destination, ANS_PARSE, ANS_READ
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
        converted += fetch_ans(url, destination)
    return converted


def tiss_sources(output_dir: Path) -> Iterator[tuple[str, Path]]:
    """
    Lists the monthly TISS files per state, routing each one to its table folder.
    """
    for folder, prefix, scope, years in TISS_SCOPES:
        for year in years:
            for state in STATES:
                for month in range(1, 13):
                    for kind, table in TISS_TABLES.items():
                        name = f"{state}_{year}{month:02d}_{prefix}_{kind}"
                        url = f"{TISS}/{folder}/{year}/{state}/{name}.zip"
                        yield url, output_dir / f"{scope}_{table}" / f"{name}.parquet"


def months(first: tuple[int, int], last: tuple[int, int]) -> Iterator[tuple[int, int]]:
    """
    Iterates over (year, month) pairs from first to last, both included.
    """
    year, month = first
    while (year, month) <= last:
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def beneficiaries_sources(output_dir: Path) -> Iterator[tuple[str, Path]]:
    """
    Lists the monthly consolidated beneficiaries files per state.
    """
    for year, month in months(BENEFICIARIES_FIRST, BENEFICIARIES_LAST):
        for state in STATES:
            name = f"pda-024-icb-{state}-{year}_{month:02d}"
            url = f"{BENEFICIARIES}/{year}{month:02d}/{name}.zip"
            yield url, output_dir / f"{name}.parquet"


def generate_health_claims(output_dir: Path) -> int:
    """
    Downloads the ANS TISS outpatient and hospital events and items into one folder per table.
    """
    return fetch_all(list(tiss_sources(output_dir)))


def generate_health_beneficiaries(output_dir: Path) -> int:
    """
    Downloads the ANS consolidated beneficiaries, one parquet file per state and month.
    """
    return fetch_all(list(beneficiaries_sources(output_dir)))


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


def convert_quarter(archive: Path, output_dir: Path) -> int:
    """
    Converts every table of a Part D quarter: an outer zip holding one inner zip per file.
    """
    files = 0
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.namelist():
            destination = partd_destination(output_dir, archive.stem, member)
            if destination is None or destination.exists():
                continue
            inner = output_dir / "inner.zip"
            try:
                with bundle.open(member) as source, inner.open("wb") as target:
                    shutil.copyfileobj(source, target)
                with zipfile.ZipFile(inner) as table:
                    rows = convert(
                        table, table.namelist()[0], destination, PARTD_PARSE, PARTD_READ
                    )
            finally:
                inner.unlink(missing_ok=True)
            logger.info(
                "%s/%s: %d rows", destination.parent.name, destination.name, rows
            )
            files += 1
    return files


def generate_medicare_partd(output_dir: Path) -> int:
    """
    Downloads the CMS quarterly Part D formulary, pharmacy network and pricing files into one folder per table.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    files = 0
    for index, path in enumerate(PARTD_QUARTERS, start=1):
        url = f"{CMS}/{path}"
        logger.info("%d/%d %s", index, len(PARTD_QUARTERS), url)
        archive = output_dir / Path(path).name
        try:
            download(url, archive)
            files += convert_quarter(archive, output_dir)
        finally:
            archive.unlink(missing_ok=True)
    return files
