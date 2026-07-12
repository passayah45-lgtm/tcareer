from pathlib import Path

from django.conf import settings
from rest_framework import serializers


class UploadValidationService:
    DEFAULT_ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".mp4"}
    DEFAULT_ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/webp",
        "video/mp4",
    }

    @staticmethod
    def validate_metadata(
        *,
        file_name: str,
        content_type: str,
        file_size: int,
        allowed_extensions: set[str] | None = None,
        allowed_mime_types: set[str] | None = None,
        max_size_bytes: int | None = None,
    ) -> None:
        extension = Path(file_name).suffix.lower()
        allowed_extensions = allowed_extensions or UploadValidationService.DEFAULT_ALLOWED_EXTENSIONS
        allowed_mime_types = allowed_mime_types or UploadValidationService.DEFAULT_ALLOWED_MIME_TYPES
        max_size_bytes = max_size_bytes or getattr(settings, "MAX_UPLOAD_SIZE_BYTES", 25 * 1024 * 1024)

        if content_type not in allowed_mime_types:
            raise serializers.ValidationError({"content_type": "This file type is not accepted."})
        if extension not in allowed_extensions:
            raise serializers.ValidationError({"file_name": "Unsupported file extension."})
        if file_size < 0 or file_size > max_size_bytes:
            raise serializers.ValidationError({"file_size": "File size exceeds the allowed limit."})

    @staticmethod
    def validate_private_document(*, file_name: str, content_type: str, file_size: int) -> None:
        UploadValidationService.validate_metadata(
            file_name=file_name,
            content_type=content_type,
            file_size=file_size,
            allowed_extensions={".pdf", ".png", ".jpg", ".jpeg"},
            allowed_mime_types={"application/pdf", "image/png", "image/jpeg"},
            max_size_bytes=getattr(settings, "MAX_PRIVATE_DOCUMENT_SIZE_BYTES", 10 * 1024 * 1024),
        )
