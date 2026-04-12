import io
import logging

import numpy as np
import face_recognition

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Image, Wedding, FaceEncoding
from .services.face_encode import encode_faces
from .services.uploadthing import upload_to_uploadthing

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/create-wedding/
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
def create_wedding(request):
    """Create a new wedding/event session."""
    name = request.data.get('name', '').strip()

    if not name:
        return Response({"error": "Wedding name is required"}, status=400)

    wedding = Wedding.objects.create(name=name)
    logger.info("Wedding created: id=%s name=%s", wedding.id, wedding.name)

    return Response({
        "wedding_id": wedding.id,
        "name": wedding.name,
    }, status=201)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/upload-images/
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
def upload_images(request):
    """
    Upload wedding photos.

    Expects:
        - wedding_id (form field)
        - images     (one or more file fields)

    Flow for each image:
        1. Read bytes in memory
        2. Upload to UploadThing → get CDN URL + file key
        3. Encode all faces in the image (in memory)
        4. Skip images with no faces
        5. Save Image record (URL) + FaceEncoding rows to Supabase
    """
    wedding_id = request.data.get('wedding_id')
    files = request.FILES.getlist('images')

    if not wedding_id:
        return Response({"error": "wedding_id is required"}, status=400)
    if not files:
        return Response({"error": "At least one image is required"}, status=400)

    try:
        wedding = Wedding.objects.get(id=wedding_id)
    except Wedding.DoesNotExist:
        return Response({"error": "Invalid wedding ID"}, status=404)

    saved_images = []
    total_faces = 0
    errors = []

    for file in files:
        filename = file.name
        try:
            image_bytes = file.read()

            # ── 1. Detect faces before uploading ──────────────────────────────
            encodings = encode_faces(image_bytes)
            if not encodings:
                logger.info("No faces in %s — skipping upload", filename)
                errors.append({"file": filename, "reason": "No face detected"})
                continue

            # ── 2. Upload to UploadThing ───────────────────────────────────────
            ut_result = upload_to_uploadthing(image_bytes, filename)
            image_url = ut_result["url"]
            image_key = ut_result["key"]

            # ── 3. Persist image record to Supabase ────────────────────────────
            image_obj = Image.objects.create(
                wedding=wedding,
                image_url=image_url,
                uploadthing_key=image_key,
            )

            # ── 4. Persist face encodings to Supabase ──────────────────────────
            face_encoding_objs = [
                FaceEncoding(image=image_obj, encoding=enc.tobytes())
                for enc in encodings
            ]
            FaceEncoding.objects.bulk_create(face_encoding_objs)

            saved_images.append({
                "image_id": image_obj.id,
                "url": image_url,
                "faces_detected": len(encodings),
            })
            total_faces += len(encodings)
            logger.info("Saved image %s with %d face(s)", image_obj.id, len(encodings))

        except Exception as exc:
            logger.exception("Failed to process file %s", filename)
            errors.append({"file": filename, "reason": str(exc)})

    return Response({
        "images_uploaded": len(saved_images),
        "total_faces_detected": total_faces,
        "images": saved_images,
        "errors": errors,
    }, status=200)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/scan-face/
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
def scan_face(request):
    """
    Match a guest selfie against all known face encodings for a wedding.

    Expects:
        - image      (file field — guest's selfie)
        - wedding_id (form field)

    Returns:
        matched_images: list of UploadThing CDN URLs where the guest appears
    """
    file = request.FILES.get('image')
    wedding_id = request.data.get('wedding_id')

    if not file:
        return Response({"error": "image is required"}, status=400)
    if not wedding_id:
        return Response({"error": "wedding_id is required"}, status=400)

    try:
        wedding = Wedding.objects.get(id=wedding_id)
    except Wedding.DoesNotExist:
        return Response({"error": "Invalid wedding ID"}, status=404)

    # ── Encode the guest's face (in memory — no temp file) ────────────────────
    guest_bytes = file.read()
    guest_encodings = encode_faces(guest_bytes)

    if not guest_encodings:
        return Response({"error": "No face detected in the provided image"}, status=400)

    guest_encoding = guest_encodings[0]  # Use the first (most prominent) face

    # ── Load all known face encodings for this wedding from Supabase ──────────
    face_records = (
        FaceEncoding.objects
        .filter(image__wedding=wedding)
        .select_related('image')
    )

    matched_urls = set()  # use a set to avoid duplicate URLs

    for record in face_records:
        known_encoding = np.frombuffer(bytes(record.encoding), dtype=np.float64)
        match = face_recognition.compare_faces(
            [known_encoding],
            guest_encoding,
            tolerance=0.5,
        )
        if match[0]:
            matched_urls.add(record.image.image_url)

    logger.info(
        "Scan for wedding %s: %d matched image(s)",
        wedding_id,
        len(matched_urls),
    )

    return Response({
        "matched_images": list(matched_urls),
        "total_matches": len(matched_urls),
    })