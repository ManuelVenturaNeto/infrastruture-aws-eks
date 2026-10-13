from collections.abc import Iterator
from pathlib import Path

from data_generator.utils import Options, Storage
from data_generator.utils.sources import ans

BENEFICIARIES = f"{ans.URL}/informacoes_consolidadas_de_beneficiarios-024"
BENEFICIARIES_FIRST = (2021, 5)
BENEFICIARIES_LAST = (2026, 8)


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
        for state in ans.STATES:
            name = f"pda-024-icb-{state}-{year}_{month:02d}"
            url = f"{BENEFICIARIES}/{year}{month:02d}/{name}.zip"
            yield url, output_dir / f"{name}.parquet"


def ingest(storage: Storage, options: Options) -> int:
    """
    Downloads the ANS consolidated beneficiaries, one parquet file per state and month.
    """
    return ans.fetch_all(list(beneficiaries_sources(storage.directory)), storage)
