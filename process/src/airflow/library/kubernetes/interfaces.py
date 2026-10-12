from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class Profile:
    manifest: dict = field(default_factory=dict)


class Instances(Enum):
    SINGLE = (1, 1)
    SMALL = (2, 4)
    MEDIUM = (4, 8)
    LARGE = (8, 16)
    XLARGE = (16, 32)

    def __init__(self, minimum: int, maximum: int) -> None:
        self.minimum = minimum
        self.maximum = maximum


class Cpu(Enum):
    SMALL = (1, 2)
    MEDIUM = (2, 4)
    LARGE = (4, 8)
    XLARGE = (8, 16)

    def __init__(self, cores: int, memory: int) -> None:
        self.cores = cores
        self.memory = memory


class Gpu(Enum):
    NONE = 0
    SMALL = 4
    MEDIUM = 8
    LARGE = 16
    XLARGE = 32

    @property
    def memory(self) -> int:
        return self.value
