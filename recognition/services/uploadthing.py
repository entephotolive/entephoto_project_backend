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

    # ── Step 1: Request a presigned upload URL ─────────────────────────────────
    presign_response = requests.post(
        f"{UPLOADTHING_API}/uploadFiles",
        headers={
            "X-Uploadthing-Api-Key": secret_key,
            "Content-Type": "application/json",
            "X-Uploadthing-Version": "6.8.0",
        },
        json={
            "files": [
                {
                    "name": filename or f"{uuid.uuid4()}.jpg",
                    "size": len(file_bytes),
                    "type": content_type,
                }
            ],
        },
        timeout=30,
    )

    if presign_response.status_code != 200:
        raise RuntimeError(
            f"UploadThing presign failed [{presign_response.status_code}]: "
            f"{presign_response.text}"
        )

    presign_data = presign_response.json()

    # UploadThing returns a list of file upload configs
    file_config = presign_data.get("data", [{}])[0]
    upload_url = file_config.get("url")
    fields = file_config.get("fields", {})
    file_key = file_config.get("key")
    final_url = file_config.get("fileUrl") or file_config.get("ufsUrl")

    if not upload_url:
        raise RuntimeError(f"UploadThing returned no upload URL: {presign_data}")

    # ── Step 2: PUT/POST the file bytes to the presigned URL ───────────────────
    if fields:
        # S3-style multipart POST
        upload_response = requests.post(
            upload_url,
            data=fields,
            files={"file": (filename, io.BytesIO(file_bytes), content_type)},
            timeout=60,
        )
    else:
        # Direct PUT
        upload_response = requests.put(
            upload_url,
            data=file_bytes,
            headers={"Content-Type": content_type},
            timeout=60,
        )

    if upload_response.status_code not in (200, 204):
        raise RuntimeError(
            f"UploadThing S3 upload failed [{upload_response.status_code}]: "
            f"{upload_response.text}"
        )

    # ── Step 3: Poll for the final file URL if not returned in presign ─────────
    if not final_url and file_key:
        poll_response = requests.get(
            f"{UPLOADTHING_API}/pollUpload/{file_key}",
            headers={"X-Uploadthing-Api-Key": secret_key},
            timeout=15,
        )
        if poll_response.status_code == 200:
            poll_data = poll_response.json()
            final_url = (
                poll_data.get("fileData", {}).get("fileUrl")
                or poll_data.get("url")
            )

    if not final_url:
        final_url = f"https://utfs.io/f/{file_key}"

    return {"url": final_url, "key": file_key}
