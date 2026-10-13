import re

import pyarrow.csv

CMS = "https://data.cms.gov/sites/default/files"

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

PARTD_PARSE = pyarrow.csv.ParseOptions(delimiter="|", quote_char=False)
PARTD_READ = pyarrow.csv.ReadOptions(encoding="latin-1", block_size=64 << 20)
