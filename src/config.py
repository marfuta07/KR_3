import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем .env файл
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Файл .env загружен из {env_file}")
else:
    print(f"❌ Файл .env не найден в {env_file}")

# Конфигурация БД
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'aviation_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'client_encoding': 'UTF8'
}

# Для отладки (не показывает пароль)
print("Параметры БД:")
print(f"  DB_NAME: {DB_CONFIG['dbname']}")
print(f"  DB_USER: {DB_CONFIG['user']}")
print(f"  DB_PASSWORD: {'*' * len(DB_CONFIG['password'])}")
print(f"  DB_HOST: {DB_CONFIG['host']}")
print(f"  DB_PORT: {DB_CONFIG['port']}")


COUNTRIES = [
    'Russia',
    'United States',
    'Germany',
    'France',
    'China'
]