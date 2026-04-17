
import os
import numpy as np
import face_recognition

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from .models import Image, Wedding,FaceEncoding
from django.http import JsonResponse

from .services.face_encode import encode_faces

from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Wedding


from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Image


@api_view(['POST'])
def create_wedding(request):
    name = request.data.get('name')
    date = request.data.get('date')
    location = request.data.get('location')

    if not name:
        return Response({"error": "Name required"}, status=400)

    
    user = request.user if request.user.is_authenticated else User.objects.first()

    wedding = Wedding.objects.create(
        name=name,
        date=date,
        location=location,
        created_by=user
    )

    return Response({
        "wedding_id": wedding.id,
        "name": wedding.name
    })
# @api_view(['POST'])
# def create_wedding(request):
#     name = request.data.get('name')

#     if not name:
#         return Response({"error": "Wedding name is required"}, status=400)

#     wedding = Wedding.objects.create(name=name)

#     return Response({
#         "message": "Wedding created successfully",
#         "wedding_id": wedding.id,
#         "name": wedding.name
#     })



@api_view(['POST'])
def upload_images(request):
    wedding_id = request.data.get('wedding_id')
    images = request.FILES.getlist('images')

    # Validate wedding
    try:
        wedding = Wedding.objects.get(id=wedding_id)
    except Wedding.DoesNotExist:
        return Response({"error": "Invalid wedding ID"}, status=404)

    saved_images = []
    total_faces_saved = 0

    for image in images:
        # Step 1: Save image (ONLY ONCE)
        image_obj = Image.objects.create(
            wedding=wedding,
            image=image
        )

        #  Step 2: Extract ALL face encodings
        encodings = encode_faces(image_obj.image.path)

        #  If no face found → delete image ()
        if not encodings:
            image_obj.delete()
            continue

        #  Step 3: Save each face separately
        for enc in encodings:
            FaceEncoding.objects.create(
                image=image_obj,
                encoding=enc.tobytes()
            )
            total_faces_saved += 1

        saved_images.append(image_obj.id)

    return Response({
        "message": "Upload completed",
        "images_uploaded": len(saved_images),
        "faces_detected": total_faces_saved
    })
    
    
    
# Scan Face and Match

@api_view(['POST'])
def scan_face(request):
    image = request.FILES.get('image')
    wedding_id = request.data.get('wedding_id')

    #  Validate input
    if not image:
        return Response({"error": "Image is required"}, status=400)

    try:
        wedding = Wedding.objects.get(id=wedding_id)
    except Wedding.DoesNotExist:
        return Response({"error": "Invalid wedding ID"}, status=404)

    #  Save temp image
    temp_path = os.path.join(settings.MEDIA_ROOT, 'temp.jpg')

    with open(temp_path, 'wb+') as f:
        for chunk in image.chunks():
            f.write(chunk)

    # Encode guest face
    guest_image = face_recognition.load_image_file(temp_path)
    guest_encodings = face_recognition.face_encodings(guest_image)

    if not guest_encodings:
        return Response({"error": "No face found"}, status=400)

    guest_encoding = guest_encodings[0]

    #  Get ALL encodings for this wedding
    face_encodings = FaceEncoding.objects.filter(
        image__wedding=wedding
    ).select_related('image')

    matched_images = set()  # avoid duplicates

    for face in face_encodings:
        known_encoding = np.frombuffer(face.encoding, dtype=np.float64)

        result = face_recognition.compare_faces(
            [known_encoding],
            guest_encoding,
            tolerance=0.5
        )

        if result[0]:
            matched_images.add(face.image.image.url)

    return Response({
        "matched_images": list(matched_images)
    })
@api_view(['GET'])
def list_weddings(request):
    weddings = Wedding.objects.all().order_by('-id')

    data = []
    for w in weddings:
        data.append({
            "id": str(w.id),
            "title": w.name,
            "date": w.date.isoformat() if w.date else None,
            "location": w.location if w.location else "No location",
            "createdBy": {
                "name": w.created_by.username if w.created_by else "Unknown"
            },
            "photoCount": 0
        })

    return Response(data)


@api_view(['DELETE'])
def delete_wedding(request, id):
    try:
        wedding = Wedding.objects.get(id=id)
        wedding.delete()
        return Response({"success": True})
    except Wedding.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    


def get_images_by_event(request, event_id):
    images = Image.objects.filter(wedding_id=event_id)

    data = []
    for img in images:
        data.append({
            "id": img.id,
            "image": request.build_absolute_uri(img.image.url)  # FIX
        })

    return JsonResponse(data, safe=False)