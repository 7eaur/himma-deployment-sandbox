import os
import hashlib
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile
import uuid

MAX_AUDIO_BYTES = 10 * 1024 * 1024

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "himma-audio")

if not S3_ACCESS_KEY or not S3_SECRET_KEY:
    raise RuntimeError("S3_ACCESS_KEY and S3_SECRET_KEY are required")

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)

def init_storage():
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
    except ClientError:
        s3_client.create_bucket(Bucket=S3_BUCKET_NAME)

def upload_audio(
    file: UploadFile,
    owner_id: int,
    operation_id: str,
) -> tuple[str, int, str]:
    """Store audio under a deterministic key and return key, size, digest."""
    payload = file.file.read(MAX_AUDIO_BYTES + 1)
    file_size = len(payload)
    if file_size <= 0 or file_size > MAX_AUDIO_BYTES:
        raise ValueError("Audio file size is outside the allowed range")

    digest = hashlib.sha256(payload).hexdigest()
    extension = ".webm" if "webm" in (file.content_type or "") else ".audio"
    object_id = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"himma-audio:{owner_id}:{operation_id}",
    )
    key = f"audio/{owner_id}/{object_id}{extension}"

    try:
        existing = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=key)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code not in {"404", "NoSuchKey", "NotFound"}:
            raise RuntimeError("Audio storage is unavailable") from exc
    except BotoCoreError as exc:
        raise RuntimeError("Audio storage is unavailable") from exc
    else:
        existing_digest = existing.get("Metadata", {}).get("sha256")
        if (
            existing.get("ContentLength") == file_size
            and existing.get("ContentType") == file.content_type
            and existing_digest == digest
        ):
            return key, file_size, digest
        raise ValueError("Idempotency-Key was reused with different audio")

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=payload,
            ContentType=file.content_type,
            Metadata={"sha256": digest},
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError("Audio storage is unavailable") from exc
    return key, file_size, digest


def verify_audio(
    storage_key: str,
    expected_size: int,
    expected_mime: str | None = None,
    *,
    expected_content_type: str | None = None,
) -> None:
    """Verify client-submitted audio metadata against the private object store.

    ``expected_mime`` is kept for existing callers; ``expected_content_type`` is
    an explicit keyword alias for newer runtime code.
    """
    content_type = expected_content_type or expected_mime
    if not content_type:
        raise ValueError("Expected audio MIME type is required")

    try:
        response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=storage_key)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            raise ValueError("Audio object does not exist") from exc
        raise RuntimeError("Audio storage is unavailable") from exc
    except BotoCoreError as exc:
        raise RuntimeError("Audio storage is unavailable") from exc

    if response["ContentLength"] != expected_size:
        raise ValueError("Audio file size does not match the stored object")
    if response.get("ContentType") != content_type:
        raise ValueError("Audio MIME type does not match the stored object")
