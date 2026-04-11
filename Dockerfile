FROM python:3.10

# Install system dependencies (keep minimal)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# Upgrade pip
RUN pip install --upgrade pip


RUN pip install dlib-bin==20.0.1

RUN pip install --prefer-binary -r requirements.txt

CMD ["gunicorn", "face_se.wsgi:application", "--bind", "0.0.0.0:8000"]