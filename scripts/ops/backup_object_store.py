#!/usr/bin/env python3
"""Create a private filesystem backup of the Himma S3/MinIO bucket.

Designed for the current small research deployment. The backup directory must
be stored on encrypted/private infrastructure outside the application host.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

import boto3


def _client():
    required = ("S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET_NAME")
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise RuntimeError(f"Missing required object-store configuration: {', '.join(missing)}")
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="us-east-1",
    )


def _safe_path(root: Path, key: str) -> Path:
    pure = PurePosixPath(key)
    if pure.is_absolute() or ".." in pure.parts:
        raise RuntimeError(f"Unsafe object key in bucket: {key!r}")
    return root.joinpath(*pure.parts)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    objects_dir = output_dir / "objects"
    objects_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    client = _client()
    bucket = os.environ["S3_BUCKET_NAME"]
    paginator = client.get_paginator("list_objects_v2")
    manifest: list[dict[str, object]] = []

    for page in paginator.paginate(Bucket=bucket):
        for row in page.get("Contents", []):
            key = str(row["Key"])
            destination = _safe_path(objects_dir, key)
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            client.download_file(bucket, key, str(destination))
            head = client.head_object(Bucket=bucket, Key=key)
            manifest.append(
                {
                    "key": key,
                    "size": destination.stat().st_size,
                    "sha256": _sha256(destination),
                    "content_type": head.get("ContentType") or "application/octet-stream",
                    "metadata": head.get("Metadata") or {},
                }
            )

    manifest.sort(key=lambda item: str(item["key"]))
    (output_dir / "manifest.json").write_text(
        json.dumps({"bucket": bucket, "objects": manifest}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Object-store backup created with {len(manifest)} object(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
