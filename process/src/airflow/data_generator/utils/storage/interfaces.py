from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):
    """Where a dataset's files end up.

    Processes always write under root; save decides what happens next.
    """

    def __init__(self, name: str, root: Path) -> None:
        self.name = name
        self.root = root

    @property
    def directory(self) -> Path:
        return self.table(self.name)

    def table(self, table: str) -> Path:
        return self.root / self.name / table

    @abstractmethod
    def exists(self, path: Path) -> bool: ...

    @abstractmethod
    def save(self, path: Path) -> None: ...

    @abstractmethod
    def size(self) -> int: ...
