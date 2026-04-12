"""
UploadThing service — server-side file upload via REST API.

Docs: https://docs.uploadthing.com/api-reference/server
"""

import io
import os
import uuid
import mimetypes
import requests
from django.conf import settings

UPLOADTHING_API = "https://api.uploadthing.com/v6"


def upload_to_uploadthing(file_bytes: bytes, filename: str) -> dict:
    """
    Upload raw bytes to UploadThing and return the file metadata.

    Args:
        file_bytes: Raw image bytes from request.FILES
        filename:   Original filename (used for MIME detection)

    Returns:
        dict with keys: url (CDN URL), key (file key)

    Raises:
        RuntimeError: if UploadThing returns a non-200 response
    """
    secret_key = settings.UPLOADTHING_SECRET_KEY
    if not secret_key:
        raise RuntimeError("UPLOADTHING_SECRET_KEY is not configured")

    content_type, _ = mimetypes.guess_type(filename)
    content_type = content_type or "image/jpeg"

    # ── Direct Server-Side Upload to UploadThing ─────────────────────────────
    # For backend uploads, UploadThing V6 allows sending the file directly 
    # as multipart/form-data rather than handling a 2-step presigned URL.
    response = requests.post(
        f"{UPLOADTHING_API}/uploadFiles",
        headers={
            "X-Uploadthing-Api-Key": secret_key,
            "X-Uploadthing-Version": "6.8.0",
        },
        files={
            "files": (filename or f"{uuid.uuid4()}.jpg", file_bytes, content_type)
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"UploadThing upload failed [{response.status_code}]: "
            f"{response.text}"
        )

    data = response.json()

    # Extract metadata safely
    file_info = None
    if isinstance(data, list) and len(data) > 0:
        file_info = data[0]
    elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
        file_info = data["data"][0]

    if file_info and (file_info.get("url") or file_info.get("fileUrl")):
        final_url = file_info.get("url") or file_info.get("fileUrl")
        file_key = file_info.get("key")
        return {"url": final_url, "key": file_key}

    raise RuntimeError(f"Unexpected UploadThing response format: {data}")
