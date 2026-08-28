"""
Модуль конфигурации проекта.

Содержит настройки подключения к БД и список стран для мониторинга.
"""

import os
from dotenv import load_dotenv
from pathlib import Path
import urllib.parse

# Загружаем .env файл
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Файл .env загружен из {env_file}")
else:
    print(f"❌ Файл .env не найден в {env_file}")

# Получаем параметры из .env
DB_NAME = os.getenv('DB_NAME', 'aviation_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '').strip()
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

# Конфигурация БД
DB_CONFIG = {
    'dbname': DB_NAME,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'host': DB_HOST,
    'port': DB_PORT,
    'client_encoding': 'UTF8'
}

# DSN строка
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
DB_DSN = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?client_encoding=utf8"

# Список стран для мониторинга (не менее 10)
COUNTRIES = [
    'Russia',
    'United States',
    'Germany',
    'France',
    'China',
    'United Kingdom',
    'Japan',
    'Canada',
    'Australia',
    'India',
    'Brazil',
    'Italy',
    'Spain',
    'South Korea',
    'Mexico'
]

print("Параметры БД:")
print(f"  DB_NAME: {DB_NAME}")
print(f"  DB_USER: {DB_USER}")
print(f"  DB_PASSWORD: {'*' * len(DB_PASSWORD)}")
print(f"  DB_HOST: {DB_HOST}")
print(f"  DB_PORT: {DB_PORT}")
print(f"  Количество стран: {len(COUNTRIES)}")