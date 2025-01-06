import discord
from discord.ext import commands
import asyncio
import yt_dlp as youtube_dl
import os
from dotenv import load_dotenv
import subprocess

try:
    result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print("FFmpeg доступен на сервере.")
    else:
        print("FFmpeg недоступен.")
except FileNotFoundError:
    print("FFmpeg не установлен.")


# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")


cookies_content = os.getenv("YOUTUBE_COOKIES")
if cookies_content:
    with open("youtube.txt", "w") as f:
        f.write(cookies_content)
    print("Файл cookies.txt создан успешно.")
else:
    print("Переменная YOUTUBE_COOKIES не найдена. Проверьте настройки Railway.")

# Настройки yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'cookiefile': 'youtube.txt',  # Используйте cookies файл
}


ffmpeg_options = {
    'options': '-vn',
}


ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Базовая настройка бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(
                url,
                download=not stream
            )
        )

        if 'entries' in data:  # Если это плейлист, берем первый трек
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)

        return cls(
            discord.FFmpegPCMAudio(filename, **ffmpeg_options),
            data=data
        )


# Очередь песен
song_queue = asyncio.Queue()
play_next_song = asyncio.Event()


async def music_player(ctx):
    while True:
        play_next_song.clear()
        current_song = await song_queue.get()

        def after_playing(_):
            bot.loop.call_soon_threadsafe(play_next_song.set)

        ctx.voice_client.play(current_song, after=after_playing)
        await ctx.send(f"Сейчас играет: {current_song.title}")
        await play_next_song.wait()


@bot.command(name='join')
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("Вы должны быть в голосовом канале, чтобы использовать эту команду.")

    channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)
    await channel.connect()


@bot.command(name='play')
async def play(ctx, *, url):
    if not ctx.voice_client:
        await ctx.invoke(join)

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            await song_queue.put(player)
            await ctx.send(f"Добавлено в очередь: {player.title}")
        except Exception as e:
            await ctx.send(f"Ошибка при добавлении трека: {str(e)}")

    if not ctx.voice_client.is_playing():
        bot.loop.create_task(music_player(ctx))


@bot.command(name='skip')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Трек пропущен.")


@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Воспроизведение приостановлено.")


@bot.command(name='resume')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Воспроизведение возобновлено.")


@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Воспроизведение остановлено, очередь очищена.")
        while not song_queue.empty():
            song_queue.get_nowait()


@bot.command(name='queue')
async def queue(ctx):
    if song_queue.empty():
        await ctx.send("Очередь пуста.")
    else:
        queue_list = []
        for idx, song in enumerate(song_queue._queue, start=1):
            queue_list.append(f"{idx}. {song.title}")
        await ctx.send("\n".join(queue_list))


@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Бот отключился от голосового канала.")


@bot.command(name='commands')
async def commands_list(ctx):
    help_message = """
    **Команды бота:**
    - `!join`: Подключить бота к голосовому каналу.
    - `!play <URL>`: Воспроизведение музыки из YouTube.
    - `!queue`: Показать текущую очередь песен.
    - `!skip`: Пропустить текущий трек.
    - `!pause`: Приостановить воспроизведение.
    - `!resume`: Возобновить воспроизведение.
    - `!stop`: Остановить воспроизведение и очистить очередь.
    - `!leave`: Отключить бота от голосового канала.
    """
    await ctx.send(help_message)


# Запуск бота
bot.run(TOKEN)
