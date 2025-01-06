# Используем базовый образ Ubuntu
FROM ubuntu:20.04

# Устанавливаем root пользователя
USER root

# Устанавливаем необходимые зависимости
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы в контейнер
COPY . .

# Устанавливаем Python-зависимости
RUN pip3 install -r requirements.txt

# Команда для запуска приложения
CMD ["python3", "ds_bot.py"]
