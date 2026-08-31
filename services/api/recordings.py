"""
recordings.py — Real MinIO-backed audio recording flow.

Flow:
  1. POST /recordings/init → returns a presigned PUT URL from MinIO
  2. Client uploads blob directly to MinIO via the presigned URL
  3. POST /recordings/complete → verifies object exists in MinIO, returns storage_key
  4. GET /recordings/stream/:key → returns presigned GET URL (short-lived)
"""

import uuid
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db.models import Student
from dependencies import get_current_student, get_current_researcher
import boto3
from botocore.exceptions import ClientError

router = APIRouter(prefix="/recordings", tags=["Recordings"])

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "himma-audio")
# Presigned URL validity in seconds (15 min for upload, 5 min for stream)
UPLOAD_URL_EXPIRY = 900
STREAM_URL_EXPIRY = 300

if not S3_ACCESS_KEY or not S3_SECRET_KEY:
    raise RuntimeError("S3_ACCESS_KEY and S3_SECRET_KEY are required")


def _get_s3():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name="us-east-1",
    )


class InitResponse(BaseModel):
    recording_id: str
    upload_url: str
    storage_key: str


class CompleteRequest(BaseModel):
    recording_id: str
    storage_key: str


class CompleteResponse(BaseModel):
    status: str
    storage_key: str
    file_size: int
    mime_type: str


class StreamResponse(BaseModel):
    url: str
    expires_in: int


@router.post("/init", response_model=InitResponse)
def init_recording(student: Student = Depends(get_current_student)):
    """
    Generate a storage_key and a presigned PUT URL for the client to upload
    an audio blob directly to MinIO. No data passes through the API server.
    """
    recording_id = str(uuid.uuid4())
    storage_key = f"audio/{student.id}/{recording_id}.webm"

    s3 = _get_s3()
    try:
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": storage_key,
                "ContentType": "audio/webm",
            },
            ExpiresIn=UPLOAD_URL_EXPIRY,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Storage unavailable: {e}")

    return {
        "recording_id": recording_id,
        "storage_key": storage_key,
        "upload_url": upload_url,
    }


@router.post("/complete", response_model=CompleteResponse)
def complete_recording(
    req: CompleteRequest,
    student: Student = Depends(get_current_student),
):
    """
    Verify the uploaded object actually exists in MinIO.
    Returns file metadata so the caller can store it with the attempt.
    """
    # Security: only allow keys belonging to this student
    expected_prefix = f"audio/{student.id}/"
    if not req.storage_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="Storage key does not belong to this student")

    s3 = _get_s3()
    try:
        head = s3.head_object(Bucket=S3_BUCKET_NAME, Key=req.storage_key)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            raise HTTPException(status_code=404, detail="Audio object not found in storage. Upload may have failed.")
        raise HTTPException(status_code=503, detail=f"Storage error: {e}")

    file_size = head["ContentLength"]
    mime_type = head.get("ContentType", "audio/webm")

    if file_size < 1000:  # < 1 KB is almost certainly empty/corrupt
        raise HTTPException(status_code=400, detail=f"Audio file too small ({file_size} bytes). Recording may be empty.")

    return {
        "status": "ok",
        "storage_key": req.storage_key,
        "file_size": file_size,
        "mime_type": mime_type,
    }


@router.get("/stream/{student_id}/{recording_id}", response_model=StreamResponse)
def stream_recording(
    student_id: int,
    recording_id: str,
    researcher=Depends(get_current_researcher),
):
    """
    Generate a short-lived presigned GET URL for the researcher to play back audio.
    Only researchers can access this endpoint.
    """
    storage_key = f"audio/{student_id}/{recording_id}.webm"

    s3 = _get_s3()
    try:
        # Verify object exists before issuing URL
        s3.head_object(Bucket=S3_BUCKET_NAME, Key=storage_key)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": storage_key},
            ExpiresIn=STREAM_URL_EXPIRY,
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            raise HTTPException(status_code=404, detail="Recording not found")
        raise HTTPException(status_code=503, detail=f"Storage error: {e}")

    return {"url": url, "expires_in": STREAM_URL_EXPIRY}


@router.get("/stream-by-key")
def stream_by_key(
    key: str,
    researcher=Depends(get_current_researcher),
):
    """
    Generate a presigned GET URL for a storage_key directly.
    Used by the audio-review page which stores the full storage_key.
    """
    if not key.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid recording key")

    s3 = _get_s3()
    try:
        s3.head_object(Bucket=S3_BUCKET_NAME, Key=key)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": key},
            ExpiresIn=STREAM_URL_EXPIRY,
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            raise HTTPException(status_code=404, detail="Recording not found")
        raise HTTPException(status_code=503, detail=str(e))

    return {"url": url, "expires_in": STREAM_URL_EXPIRY}
