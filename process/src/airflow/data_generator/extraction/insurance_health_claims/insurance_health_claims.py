from collections.abc import Iterator
from pathlib import Path

from data_generator.utils import Options, Storage
from data_generator.utils.sources import ans

TISS = f"{ans.URL}/TISS"
TISS_SCOPES = (
    ("AMBULATORIAL", "AMB", "outpatient", range(2024, 2026)),
    ("HOSPITALAR", "HOSP", "hospital", range(2015, 2026)),
)
TISS_TABLES = {"CONS": "events", "DET": "items"}


def tiss_sources(output_dir: Path) -> Iterator[tuple[str, Path]]:
    """
    Lists the monthly TISS files per state, routing each one to its table folder.
    """
    for folder, prefix, scope, years in TISS_SCOPES:
        for year in years:
            for state in ans.STATES:
                for month in range(1, 13):
                    for kind, table in TISS_TABLES.items():
                        name = f"{state}_{year}{month:02d}_{prefix}_{kind}"
                        url = f"{TISS}/{folder}/{year}/{state}/{name}.zip"
                        yield url, output_dir / f"{scope}_{table}" / f"{name}.parquet"


def ingest(storage: Storage, options: Options) -> int:
    """
    Downloads the ANS TISS outpatient and hospital events and items into one folder per table.
    """
    return ans.fetch_all(list(tiss_sources(storage.directory)), storage)
