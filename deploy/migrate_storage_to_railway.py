#!/usr/bin/env python3
"""Audit/copy Himma objects from the legacy S3-compatible store to Railway Bucket.

Source is never modified.  Audit mode lists only aggregate counts/bytes.  Migrate
mode streams every source object to the target when missing or size-mismatched,
then verifies key presence and byte size.

Environment:
  S3_ENDPOINT / S3_ACCESS_KEY / S3_SECRET_KEY / S3_BUCKET_NAME  legacy source
  TARGET_S3_ENDPOINT / TARGET_S3_ACCESS_KEY / TARGET_S3_SECRET_KEY /
  TARGET_S3_BUCKET_NAME                                        Railway target
  STORAGE_MIGRATION_MODE                                       audit|migrate
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict

import boto3
from botocore.config import Config

MODE = os.getenv("STORAGE_MIGRATION_MODE", "audit").strip().lower()
if MODE not in {"audit", "migrate"}:
    raise SystemExit("STORAGE_MIGRATION_MODE must be 'audit' or 'migrate'")


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required")
    return value


SOURCE_ENDPOINT = required("S3_ENDPOINT")
SOURCE_ACCESS = required("S3_ACCESS_KEY")
SOURCE_SECRET = required("S3_SECRET_KEY")
SOURCE_BUCKET = required("S3_BUCKET_NAME")
TARGET_ENDPOINT = required("TARGET_S3_ENDPOINT")
TARGET_ACCESS = required("TARGET_S3_ACCESS_KEY")
TARGET_SECRET = required("TARGET_S3_SECRET_KEY")
TARGET_BUCKET = required("TARGET_S3_BUCKET_NAME")


@dataclass(frozen=True)
class Obj:
    size: int
    etag: str


def client(endpoint: str, access: str, secret: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name="us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": "auto"}),
    )


def inventory(s3, bucket: str) -> Dict[str, Obj]:
    result: Dict[str, Obj] = {}
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for item in page.get("Contents", []):
            result[item["Key"]] = Obj(
                size=int(item.get("Size", 0)),
                etag=str(item.get("ETag", "")).strip('"'),
            )
    return result


def print_summary(label: str, items: Dict[str, Obj]) -> None:
    print(f"{label}_OBJECTS={len(items)}")
    print(f"{label}_BYTES={sum(x.size for x in items.values())}")


def main() -> None:
    source = client(SOURCE_ENDPOINT, SOURCE_ACCESS, SOURCE_SECRET)
    target = client(TARGET_ENDPOINT, TARGET_ACCESS, TARGET_SECRET)

    source_items = inventory(source, SOURCE_BUCKET)
    target_items = inventory(target, TARGET_BUCKET)
    print_summary("SOURCE_STORAGE", source_items)
    print_summary("TARGET_STORAGE", target_items)

    if MODE == "audit":
        print("STORAGE_AUDIT_OK")
        return

    copied = 0
    skipped = 0
    for key, src in source_items.items():
        existing = target_items.get(key)
        if existing and existing.size == src.size:
            skipped += 1
            continue

        head = source.head_object(Bucket=SOURCE_BUCKET, Key=key)
        body = source.get_object(Bucket=SOURCE_BUCKET, Key=key)["Body"]
        extra = {}
        content_type = head.get("ContentType")
        if content_type:
            extra["ContentType"] = content_type
        cache_control = head.get("CacheControl")
        if cache_control:
            extra["CacheControl"] = cache_control
        metadata = head.get("Metadata")
        if metadata:
            extra["Metadata"] = metadata

        target.upload_fileobj(body, TARGET_BUCKET, key, ExtraArgs=extra or None)
        copied += 1
        print(f"COPIED_OBJECT bytes={src.size}")

    final_target = inventory(target, TARGET_BUCKET)
    missing = []
    mismatched = []
    for key, src in source_items.items():
        dst = final_target.get(key)
        if dst is None:
            missing.append(key)
        elif dst.size != src.size:
            mismatched.append((key, src.size, dst.size))

    if missing or mismatched:
        raise RuntimeError(
            f"Storage verification failed: missing={len(missing)}, size_mismatch={len(mismatched)}"
        )

    print(f"STORAGE_COPIED={copied}")
    print(f"STORAGE_SKIPPED={skipped}")
    print_summary("FINAL_TARGET_STORAGE", final_target)
    print("STORAGE_MIGRATION_COMPLETE")


if __name__ == "__main__":
    main()
