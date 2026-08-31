#!/usr/bin/env python3
"""Restore a Himma object-store backup into an explicit test/restore bucket."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import boto3
from botocore.exceptions import ClientError

def safe_path(root: Path, key: str) -> Path:
    pure = PurePosixPath(key)
    if pure.is_absolute() or ".." in pure.parts:
        raise RuntimeError("Unsafe object key in backup manifest")
    return root.joinpath(*pure.parts)

def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("backup_dir", type=Path)
    args = parser.parse_args()
    bucket = os.environ["RESTORE_S3_BUCKET_NAME"]
    client = boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="us-east-1",
    )
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)
    payload = json.loads((args.backup_dir / "manifest.json").read_text(encoding="utf-8"))
    objects = payload.get("objects") or []
    for item in objects:
        key = str(item["key"])
        source = safe_path(args.backup_dir / "objects", key)
        expected = str(item["sha256"])
        if digest(source) != expected:
            raise RuntimeError(f"Backup checksum mismatch: {key}")
        client.upload_file(
            str(source), bucket, key,
            ExtraArgs={"ContentType": str(item.get("content_type") or "application/octet-stream")},
        )
        restored = client.get_object(Bucket=bucket, Key=key)["Body"].read()
        if hashlib.sha256(restored).hexdigest() != expected:
            raise RuntimeError(f"Restored object checksum mismatch: {key}")
    print(f"Object-store restore verified for {len(objects)} object(s).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
