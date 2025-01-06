FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libffi-dev \
    libnacl-dev \
    && pip install --no-cache-dir discord.py yt-dlp python-dotenv pynacl

WORKDIR /app
COPY . /app

CMD ["python", "ds_bot.py"]