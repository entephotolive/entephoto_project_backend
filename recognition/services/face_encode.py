import io
import face_recognition
import numpy as np


def encode_faces(image_bytes: bytes) -> list:
    """
    Detect and encode all faces in the given image bytes.

    Args:
        image_bytes: Raw image bytes (from request.FILES or any source)

    Returns:
        List of numpy arrays (128-dim face encodings). Empty list if no faces found.
    """
    image = face_recognition.load_image_file(io.BytesIO(image_bytes))
    face_locations = face_recognition.face_locations(image)
    encodings = face_recognition.face_encodings(image, face_locations)
    return encodings