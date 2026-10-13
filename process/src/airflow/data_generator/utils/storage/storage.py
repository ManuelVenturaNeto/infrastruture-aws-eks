from pathlib import Path

from .interfaces import Storage
from .local import LocalStorage
from .s3 import S3Storage

S3_SCHEMES = ("s3://", "s3a://")


def open_storage(name: str, out: str) -> Storage:
    for scheme in S3_SCHEMES:
        if out.startswith(scheme):
            bucket, _, prefix = out.removeprefix(scheme).partition("/")
            return S3Storage(name, bucket, prefix.strip("/"))
    return LocalStorage(name, Path(out))
