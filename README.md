# Wedding Face Recognition System

## Features
- Upload wedding images
- Auto face detection (dlib)
- Face encoding & matching
- Live scan API
- Django + DRF backend
- Celery background processing

## Tech Stack
- Django
- Django REST Framework
- face_recognition (dlib)
- Celery + Redis

## Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver# ente-photo.python
