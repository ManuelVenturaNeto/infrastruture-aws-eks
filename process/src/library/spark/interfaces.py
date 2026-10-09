from dataclasses import dataclass, field


@dataclass(frozen=True)
class Profile:
    conf: dict[str, str] = field(default_factory=dict)
    packages: tuple[str, ...] = ()
