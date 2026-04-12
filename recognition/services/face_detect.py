
import face_recognition

def detect_faces(image_path):
    """
    Detect face locations in an image
    Returns list of face coordinates
    """
    image = face_recognition.load_image_file(image_path)

    # returns [(top, right, bottom, left), ...]
    face_locations = face_recognition.face_locations(image)

    return face_locations