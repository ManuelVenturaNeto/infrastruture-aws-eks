import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from .interfaces import Storage

MISSING = "404"


class S3Storage(Storage):
    """Uploads each saved file to the same relative key and deletes it locally.

    The disk only holds the file in progress, and files already in the bucket
    are reported as existing, so a rerun resumes where the last one stopped.
    """

    def __init__(self, name: str, bucket: str, prefix: str) -> None:
        super().__init__(name, Path(tempfile.mkdtemp()))
        self.bucket = bucket
        self.prefix = prefix
        self.client = boto3.client("s3")

    def key(self, path: Path) -> str:
        relative = path.relative_to(self.root).as_posix()
        return f"{self.prefix}/{relative}" if self.prefix else relative

    def exists(self, path: Path) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self.key(path))
        except ClientError as error:
            if error.response["Error"]["Code"] == MISSING:
                return False
            raise
        return True

    def save(self, path: Path) -> None:
        self.client.upload_file(str(path), self.bucket, self.key(path))
        path.unlink()

    def size(self) -> int:
        prefix = f"{self.key(self.root / self.name)}/"
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)
        return sum(item["Size"] for page in pages for item in page.get("Contents", []))
