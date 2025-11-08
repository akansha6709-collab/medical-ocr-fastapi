# Dockerfile (place in Backend/)
FROM python:3.11-slim

# system deps needed for pdf2image, tesseract and headless OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      poppler-utils \
      tesseract-ocr \
      libgl1 && \
    rm -rf /var/lib/apt/lists/*

# set workdir
WORKDIR /app

# copy only what we need first (speed up rebuilds)
COPY requirements.txt /app/requirements.txt

# install python deps
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# copy app code
COPY . /app

# Environment defaults
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV POPPLER_PATH=/usr/bin

# expose port
EXPOSE 8000

# start uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
