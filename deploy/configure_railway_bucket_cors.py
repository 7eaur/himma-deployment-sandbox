#!/usr/bin/env python3
"""Apply and verify browser-safe CORS rules on the Railway audio bucket.

Uses the already-injected target bucket credentials and the API's CORS_ORIGINS
list. No credentials or object keys are printed.
"""

from __future__ import annotations

import os

import boto3
from botocore.config import Config


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required")
    return value


endpoint = required("TARGET_S3_ENDPOINT")
access = required("TARGET_S3_ACCESS_KEY")
secret = required("TARGET_S3_SECRET_KEY")
bucket = required("TARGET_S3_BUCKET_NAME")
raw_origins = required("CORS_ORIGINS")
origins = [item.strip() for item in raw_origins.split(",") if item.strip()]
if not origins:
    raise SystemExit("CORS_ORIGINS must contain at least one origin")

s3 = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=access,
    aws_secret_access_key=secret,
    region_name="us-east-1",
    config=Config(signature_version="s3v4", s3={"addressing_style": "auto"}),
)

cors = {
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "HEAD", "PUT", "POST"],
            "AllowedOrigins": origins,
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000,
        }
    ]
}

s3.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors)
verified = s3.get_bucket_cors(Bucket=bucket)
rules = verified.get("CORSRules", [])
if not rules:
    raise RuntimeError("Bucket CORS verification returned no rules")

actual = rules[0]
missing_origins = sorted(set(origins) - set(actual.get("AllowedOrigins", [])))
required_methods = {"GET", "HEAD", "PUT", "POST"}
missing_methods = sorted(required_methods - set(actual.get("AllowedMethods", [])))
if missing_origins or missing_methods:
    raise RuntimeError(
        f"Bucket CORS verification failed: missing_origins={len(missing_origins)}, "
        f"missing_methods={missing_methods}"
    )

print(f"BUCKET_CORS_ORIGINS={len(origins)}")
print("BUCKET_CORS_OK")
