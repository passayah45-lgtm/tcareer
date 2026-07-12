import logging
import mimetypes
import uuid
from typing import BinaryIO

from django.conf import settings

logger = logging.getLogger(__name__)


def get_s3_client():
    import boto3

    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def upload_to_s3(
    file_obj: BinaryIO,
    key: str,
    content_type: str = "application/octet-stream",
    bucket: str | None = None,
) -> str:
    """
    Upload a file-like object to S3 and return the public URL.
    Used for certificates and email attachments only.
    For user uploads (videos, resumes), use presigned URLs instead.
    """
    bucket = bucket or settings.AWS_S3_BUCKET_NAME
    client = get_s3_client()

    try:
        client.upload_fileobj(
            file_obj,
            bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
    except Exception as exc:
        logger.error("S3 upload failed for key %s: %s", key, exc)
        raise

    if settings.AWS_S3_CUSTOM_DOMAIN:
        return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{key}"

    return f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def generate_presigned_upload_url(
    file_name: str,
    folder: str,
    content_type: str | None = None,
    expiry_seconds: int = 3600,
    bucket: str | None = None,
) -> dict:
    """
    Generate a presigned URL for direct browser-to-S3 upload.
    The browser uploads directly - the Django server never receives the file bytes.
    Returns both the upload URL and the final file URL.
    """
    bucket = bucket or settings.AWS_S3_BUCKET_NAME
    client = get_s3_client()

    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    unique_key = f"{folder}/{uuid.uuid4().hex}.{ext}"

    if not content_type:
        content_type, _ = mimetypes.guess_type(file_name)
        content_type = content_type or "application/octet-stream"

    try:
        upload_url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": unique_key,
                "ContentType": content_type,
            },
            ExpiresIn=expiry_seconds,
        )
    except Exception as exc:
        logger.error("Failed to generate presigned URL: %s", exc)
        raise

    if settings.AWS_S3_CUSTOM_DOMAIN:
        final_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{unique_key}"
    else:
        final_url = f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_key}"

    return {
        "upload_url": upload_url,
        "file_url": final_url,
        "key": unique_key,
        "content_type": content_type,
        "expires_in": expiry_seconds,
    }


def generate_presigned_download_url(key: str, expiry_seconds: int = 3600, bucket: str | None = None) -> str:
    """
    Generate a presigned download URL for private S3 objects.
    Use this for paid course videos and user-specific files.
    """
    bucket = bucket or settings.AWS_S3_BUCKET_NAME
    client = get_s3_client()

    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiry_seconds,
        )
    except Exception as exc:
        logger.error("Failed to generate presigned download URL for %s: %s", key, exc)
        raise


def generate_private_download_url(file_field=None, fallback_url: str = "", expiry_seconds: int = 3600) -> str:
    """
    Return a private-download URL for local storage or S3-backed storage.
    Authorization must happen before this helper is called.
    """
    if fallback_url:
        return fallback_url
    if not file_field:
        return ""

    key = getattr(file_field, "name", "")
    if not key:
        return ""

    has_s3_config = bool(
        getattr(settings, "AWS_S3_BUCKET_NAME", "")
        and getattr(settings, "AWS_ACCESS_KEY_ID", "")
        and getattr(settings, "AWS_SECRET_ACCESS_KEY", "")
    )
    if has_s3_config:
        try:
            return generate_presigned_download_url(key, expiry_seconds=expiry_seconds)
        except Exception:
            logger.exception("Falling back to storage URL for private download key %s", key)

    try:
        return file_field.url
    except Exception:
        logger.exception("Could not resolve local private download URL for %s", key)
        return ""
