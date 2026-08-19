import sys
import os
from pathlib import Path

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Импорты
from src.config import DB_CONFIG, DB_DSN, COUNTRIES
from src.database import Database
from src.api_inf import APIClient
from src.db_manager import DBManager

import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК ПРОГРАММЫ СБОРА ДАННЫХ О САМОЛЕТАХ")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        # ШАГ 1: Подготовка БД
        logger.info("\n📌 ШАГ 1: Подготовка базы данных")

        # Пробуем подключиться через DSN строку (более надежно)
        logger.info("Используем DSN строку для подключения...")
        db = Database(DB_DSN)  # Используем DSN вместо словаря
        db.connect()
        db.create_tables_if_not_exists()
        db.clear_data()

        # ШАГ 2: Сбор данных из API
        logger.info("\n📌 ШАГ 2: Сбор данных из API")
        api_client = APIClient()

        # 2.1 Получаем координаты стран
        countries_data = {}
        for country in COUNTRIES:
            logger.info(f"\n📍 Обработка страны: {country}")
            country_info = api_client.get_country_coordinates(country)

            if country_info:
                country_id = db.insert_country(country_info)
                countries_data[country] = {
                    'id': country_id,
                    'info': country_info
                }
                logger.info(f"✅ Страна {country} сохранена с ID {country_id}")
            else:
                logger.warning(f"⚠️ Пропускаем страну {country} (координаты не найдены)")

            time.sleep(1)

        # 2.2 Получаем данные о самолетах
        total_aeroplanes = 0
        for country, data in countries_data.items():
            logger.info(f"\n✈️ Поиск самолетов в воздушном пространстве {country}")

            lat = data['info']['latitude']
            lon = data['info']['longitude']

            lat_min = lat - 5
            lat_max = lat + 5
            lon_min = lon - 5
            lon_max = lon + 5

            aeroplanes = api_client.get_aeroplanes_by_bounding_box(
                lat_min, lat_max, lon_min, lon_max
            )

            for aeroplane in aeroplanes:
                aeroplane['country_id'] = data['id']
                db.insert_aeroplane(aeroplane)

            total_aeroplanes += len(aeroplanes)
            logger.info(f"✅ Сохранено {len(aeroplanes)} самолетов для {country}")

            time.sleep(1)

        db.disconnect()

        # ШАГ 3: Аналитика
        logger.info("\n📌 ШАГ 3: Анализ данных через DBManager")
        db_manager = DBManager(DB_CONFIG)  # Для DBManager используем словарь
        db_manager.connect()

        # 3.1 Страны и количество самолетов
        logger.info("\n📊 СТРАНЫ И КОЛИЧЕСТВО САМОЛЕТОВ:")
        countries_stats = db_manager.get_countries_and_aeroplanes_count()
        for item in countries_stats:
            logger.info(f"  • {item['country_name']}: {item['aeroplanes_count']} самолетов")

        # 3.2 Все самолеты (первые 5)
        logger.info("\n📊 ВСЕ САМОЛЕТЫ (первые 5):")
        aeroplanes = db_manager.get_all_aeroplanes()
        for plane in aeroplanes[:5]:
            logger.info(f"  • {plane.get('callsign', 'N/A')} | "
                        f"Скорость: {plane.get('velocity', 'N/A')} м/с | "
                        f"{plane.get('country_name', 'N/A')}")

        # 3.3 Средняя скорость
        avg_speed = db_manager.get_avg_speed()
        logger.info(f"\n📊 СРЕДНЯЯ СКОРОСТЬ: {avg_speed:.2f} м/с")

        # 3.4 Самолеты со скоростью выше средней
        logger.info("\n📊 САМОЛЕТЫ СО СКОРОСТЬЮ ВЫШЕ СРЕДНЕЙ (первые 5):")
        fast_planes = db_manager.get_aeroplanes_with_higher_speed()
        for plane in fast_planes[:5]:
            logger.info(f"  • {plane.get('callsign', 'N/A')} | "
                        f"Скорость: {plane.get('velocity', 'N/A')} м/с")

        # 3.5 Поиск по ключевому слову
        keyword = "AFL"
        logger.info(f"\n📊 САМОЛЕТЫ С КЛЮЧЕВЫМ СЛОВОМ '{keyword}':")
        keyword_planes = db_manager.get_aeroplanes_with_keyword(keyword)
        for plane in keyword_planes[:5]:
            logger.info(f"  • {plane.get('callsign', 'N/A')} | "
                        f"Страна: {plane.get('country_name', 'N/A')} | "
                        f"Скорость: {plane.get('velocity', 'N/A')} м/с")

        db_manager.disconnect()

        elapsed_time = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info("✅ ПРОГРАММА УСПЕШНО ЗАВЕРШЕНА")
        logger.info(f"📊 ИТОГО СОБРАНО: {total_aeroplanes} самолетов")
        logger.info(f"⏱️ ВРЕМЯ ВЫПОЛНЕНИЯ: {elapsed_time:.2f} секунд")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()