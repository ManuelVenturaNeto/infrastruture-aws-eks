from pathlib import Path

from .interfaces import Storage


class LocalStorage(Storage):
    def exists(self, path: Path) -> bool:
        return path.exists()

    def save(self, path: Path) -> None:
        return None

    def size(self) -> int:
        files = (self.root / self.name).rglob("*.parquet")
        return sum(file.stat().st_size for file in files)
