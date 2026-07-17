FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    build-essential \
    libSDL2-dev \
    libSDL2-image-dev \
    libSDL2-mixer-dev \
    libSDL2-ttf-dev \
    libfreetype6-dev \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libxi6 \
    libxcursor1 \
    libxinerama1 \
    libgl1 \
    libglu1-mesa \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV SDL_AUDIODRIVER=dummy

CMD ["python", "gui.py"]FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    build-essential \
    libSDL2-dev \
    libSDL2-image-dev \
    libSDL2-mixer-dev \
    libSDL2-ttf-dev \
    libfreetype6-dev \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libxi6 \
    libxcursor1 \
    libxinerama1 \
    libgl1 \
    libglu1-mesa \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV SDL_AUDIODRIVER=dummy

CMD ["python", "gui.py"]