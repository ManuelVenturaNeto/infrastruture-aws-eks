import json
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

from .constants import ATTEMPTS, HEADERS, NOT_FOUND, TIMEOUT


def download(url: str, destination: Path) -> None:
    """
    Downloads a file, retrying a few times before giving up; a missing file raises at once.
    """
    for attempt in range(1, ATTEMPTS + 1):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with (
                urllib.request.urlopen(request, timeout=TIMEOUT) as response,
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


def fetch_json(url: str) -> dict | list:
    """
    Downloads a JSON document, retrying a few times before giving up.
    """
    for attempt in range(1, ATTEMPTS + 1):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt == ATTEMPTS:
                raise
            time.sleep(attempt)
