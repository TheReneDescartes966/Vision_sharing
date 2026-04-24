FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libgstrtspserver-1.0-0 \
    python3-gi \
    python3-gst-1.0 \
    gir1.2-gst-rtsp-server-1.0 \
    ffmpeg \
    curl \
    wget \
    libavfilter-extra \
    libavdevice-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app/ ./app/

COPY app/assets/ /app/assets/

RUN mkdir -p /app/recordings /app/hls /app/logs /app/assets && \
    chmod 777 /app/recordings /app/hls /app/logs

EXPOSE 8000 8554

ENV VIDEO_SOURCE=test
ENV USE_GPU=false
ENV RECORDINGS_DIR=/app/recordings
ENV HLS_DIR=/app/hls

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]