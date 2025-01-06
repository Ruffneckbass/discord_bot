import cloudconvert
import os
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import requests


# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")


# Проверка наличия ключей
if not TOKEN:
    raise ValueError("Токен Discord отсутствует. Убедитесь, что он задан в .env файле.")
if not CLOUDCONVERT_API_KEY:
    raise ValueError("Ключ CloudConvert API отсутствует. Убедитесь, что он задан в .env файле.")

# Инициализация CloudConvert API
cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY)

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True

# Настройка бота
bot = commands.Bot(command_prefix="!", intents=intents)


async def convert_video_to_audio(video_url, output_file):
    """Конвертация видео в аудио через CloudConvert API."""
    try:
        # Создаем задание на конвертацию
        job = cloudconvert.Job.create(payload={
            "tasks": {
                "import-url": {
                    "operation": "import/url",
                    "url": video_url,
                },
                "convert": {
                    "operation": "convert",
                    "input": "import-url",
                    "output_format": "mp3",
                },
                "export": {
                    "operation": "export/url",
                    "input": "convert",
                }
            }
        })

        # Получаем ссылку на скачивание результата
        export_task = next(
            task for task in job["data"]["tasks"] if task["name"] == "export"
        )
        file_url = export_task["result"]["files"][0]["url"]

        # Скачиваем аудио
        response = requests.get(file_url)
        response.raise_for_status()
        with open(output_file, "wb") as f:
            f.write(response.content)

        return output_file

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке файла: {e}")
        return None
    except cloudconvert.exceptions.ApiError as e:
        print(f"Ошибка CloudConvert API: {e}")
        return None
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return None


@bot.command(name="play")
async def play(ctx, url):
    """Добавление трека для воспроизведения."""
    if not ctx.voice_client:
        await ctx.invoke(join)

    output_file = "song.mp3"
    await ctx.send("Обрабатываем аудио, пожалуйста подождите...")

    audio_file = await convert_video_to_audio(url, output_file)
    if audio_file:
        ctx.voice_client.play(discord.FFmpegPCMAudio(audio_file), after=lambda e: print(f"Игра завершена: {e}"))
        await ctx.send(f"Играем трек: {audio_file}")
    else:
        await ctx.send("Ошибка при обработке аудио.")


@bot.command(name="join")
async def join(ctx):
    """Подключение к голосовому каналу."""
    if not ctx.author.voice:
        await ctx.send("Вы должны быть в голосовом канале!")
        return
    channel = ctx.author.voice.channel
    await channel.connect()


@bot.command(name="leave")
async def leave(ctx):
    """Отключение от голосового канала."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Бот отключен.")


# Запуск бота
bot.run(TOKEN)