FROM ubuntu:22.04

# Установить необходимые зависимости
RUN apt-get update && apt-get install -y ffmpeg python3 python3-pip
    python3 \
    python3-pip \
    ffmpeg \
    gcc \
    libffi-dev \
    libc6


# Установить зависимости Python
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt
COPY ./bin/ffmpeg /usr/local/bin/ffmpeg
RUN chmod +x /usr/local/bin/ffmpeg

# Запуск бота
CMD ["python3", "ds_bot.py"]
