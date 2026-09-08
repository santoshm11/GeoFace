# syntax=docker/dockerfile:1.3   # Enable BuildKit features

FROM python:3.10-slim

# System dependencies (for dlib, face_recognition, ngrok)
RUN apt-get update && apt-get install -y \
    build-essential cmake libopenblas-dev liblapack-dev \
    libjpeg-dev libpng-dev libtiff-dev \
    curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Install ngrok v3
RUN curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
    | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
    && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
    | tee /etc/apt/sources.list.d/ngrok.list \
    && apt-get update && apt-get install -y ngrok

WORKDIR /app

COPY requirements.txt .

# Upgrade pip and use cached downloads
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 --retries=10 -r requirements.txt

COPY . .

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 9000

CMD ["/start.sh"]
