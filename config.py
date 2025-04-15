import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла (если он существует)
load_dotenv()

# Telegram Bot токен
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7678148639:AAERgt-8Y3n1ViVzFUNCqGaQj2ppXnqT7XU")

# TMDB API ключи
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "e790234d11642d449a1f37fad4ef3a56")
TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN", "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlNzkwMjM0ZDExNjQyZDQ0OWExZjM3ZmFkNGVmM2E1NiIsIm5iZiI6MTc0NDcxOTY3OC4yNiwic3ViIjoiNjdmZTRmM2U2MWIxYzRiYjMyOTk2ZTRlIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.KPbd1cZ_-GofALVYD-AOoj3-2w3ndm2ja3SPiDqpuZE")

# База данных SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///movie_tracker.db")

# Настройки уведомлений
NOTIFICATION_INTERVAL = int(os.getenv("NOTIFICATION_INTERVAL", "24"))  # в часах

# URL hdrezka (для справки, парсить будем через TMDB)
HDREZKA_URL = "https://hdrezka.ag/"