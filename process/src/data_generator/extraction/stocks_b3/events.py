import base64
import json
import logging
import urllib.error
from datetime import UTC, date, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from data_generator.utils import http

from .constants import (
    COMPANIES,
    EVENTS_FILE,
    EVENTS_SCHEMA,
    LANGUAGE,
    NEVER_LISTED,
    PAGE_SIZE,
    SUPPLEMENT,
)

logger = logging.getLogger(__name__)


def encode(payload: dict) -> str:
    """
    Encodes a request payload the way the B3 listed-companies service expects: base64 of its JSON.
    """
    return base64.b64encode(json.dumps(payload).encode()).decode()


def list_companies() -> list[str]:
    """
    Lists the issuing-company codes of every company listed on B3, skipping BDRs and never-listed registrations.
    """
    payload = {"language": LANGUAGE, "pageNumber": 1, "pageSize": PAGE_SIZE}
    first = http.fetch_json(COMPANIES.format(payload=encode(payload)))
    companies = list(first["results"])
    for page in range(2, first["page"]["totalPages"] + 1):
        payload["pageNumber"] = page
        companies += http.fetch_json(COMPANIES.format(payload=encode(payload)))[
            "results"
        ]
    return [
        company["issuingCompany"]
        for company in companies
        if not company["typeBDR"] and company["dateListing"] != NEVER_LISTED
    ]


def parse_date(value: str) -> date | None:
    """
    Parses a dd/mm/yyyy string from the B3 service; empty strings become null.
    """
    if not value:
        return None
    return datetime.strptime(value, "%d/%m/%Y").replace(tzinfo=UTC).date()


def parse_factor(value: str) -> float:
    """
    Parses a Brazilian-formatted number from the B3 service: dots for thousands, comma for decimals.
    """
    return float(value.replace(".", "").replace(",", "."))


def fetch_events(company: str) -> list[dict]:
    """
    Fetches the stock events (splits, reverse splits and bonus issues) of one company.
    """
    payload = {"issuingCompany": company, "language": LANGUAGE}
    supplement = http.fetch_json(SUPPLEMENT.format(payload=encode(payload)))
    if isinstance(supplement, list):
        supplement = supplement[0] if supplement else {}
    return [
        {
            "issuing_company": company,
            "isin_code": event["isinCode"],
            "label": event["label"],
            "factor": parse_factor(event["factor"]),
            "last_date_prior": parse_date(event["lastDatePrior"]),
            "approved_on": parse_date(event["approvedOn"]),
        }
        for event in supplement.get("stockDividends") or []
    ]


def generate_events(output_dir: Path) -> int:
    """
    Downloads the stock events of every listed company into a single parquet file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    companies = list_companies()
    events = []
    for index, company in enumerate(companies, start=1):
        try:
            found = fetch_events(company)
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            KeyError,
        ) as error:
            logger.warning("%d/%d %s: %s", index, len(companies), company, error)
            continue
        events += found
        if found:
            logger.info(
                "%d/%d %s: %d events", index, len(companies), company, len(found)
            )
    table = pa.Table.from_pylist(events, schema=EVENTS_SCHEMA)
    pq.write_table(table, output_dir / EVENTS_FILE, compression="zstd")
    logger.info(
        "%s: %d events from %d companies", EVENTS_FILE, len(events), len(companies)
    )
    return len(events)
