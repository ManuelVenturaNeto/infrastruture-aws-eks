from dataclasses import dataclass


@dataclass(frozen=True)
class Options:
    files: int
    start_year: int | None = None
    end_year: int | None = None
