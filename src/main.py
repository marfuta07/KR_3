import sys
from pathlib import Path

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Импорты
from src.config import DB_CONFIG, DB_DSN, COUNTRIES
from src.database import Database
from src.api_inf import APIClient
from src.db_manager import DBManager
from src.interfaces import DataStorage, DataSource, DataAnalyzer

import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main(storage: DataStorage, source: DataSource, analyzer: DataAnalyzer):
    """
    Главная функция программы.

    Args:
        storage: Хранилище данных (Database)
        source: Источник данных (APIClient)
        analyzer: Анализатор данных (DBManager)
    """
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК ПРОГРАММЫ СБОРА ДАННЫХ О САМОЛЕТАХ")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        # ШАГ 1: Подготовка БД
        logger.info("\n📌 ШАГ 1: Подготовка базы данных")
        storage.connect()
        storage.create_tables_if_not_exists()
        storage.clear_data()

        # ШАГ 2: Сбор данных из API
        logger.info("\n📌 ШАГ 2: Сбор данных из API")

        # 2.1 Получаем координаты стран
        countries_data = {}
        for country in COUNTRIES:
            logger.info(f"\n📍 Обработка страны: {country}")
            country_info = source.get_country_coordinates(country)

            if country_info:
                country_id = storage.save_country(country_info)
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

            # Увеличиваем область для больших стран
            if country in ['Russia', 'China']:
                lat_min = lat - 15
                lat_max = lat + 15
                lon_min = lon - 20
                lon_max = lon + 20
            else:
                lat_min = lat - 5
                lat_max = lat + 5
                lon_min = lon - 5
                lon_max = lon + 5

            aeroplanes = source.get_aeroplanes_in_area(
                lat_min, lat_max, lon_min, lon_max
            )

            for aeroplane in aeroplanes:
                aeroplane['country_id'] = data['id']
                storage.save_aeroplane(aeroplane)

            total_aeroplanes += len(aeroplanes)
            logger.info(f"✅ Сохранено {len(aeroplanes)} самолетов для {country}")

            time.sleep(1)

        storage.disconnect()

        # ШАГ 3: Аналитика
        logger.info("\n📌 ШАГ 3: Анализ данных через DBManager")
        analyzer.connect()

        # 3.1 Страны и количество самолетов
        logger.info("\n📊 СТРАНЫ И КОЛИЧЕСТВО САМОЛЕТОВ:")
        countries_stats = analyzer.get_countries_and_aeroplanes_count()
        for item in countries_stats:
            logger.info(f"  • {item['country_name']}: {item['aeroplanes_count']} самолетов")

        # 3.2 Все самолеты (первые 5)
        logger.info("\n📊 ВСЕ САМОЛЕТЫ (первые 5):")
        aeroplanes = analyzer.get_all_aeroplanes()
        for plane in aeroplanes[:5]:
            logger.info(f"  • {plane.get('callsign', 'N/A')} | "
                        f"Скорость: {plane.get('velocity', 'N/A')} м/с | "
                        f"{plane.get('country_name', 'N/A')}")

        # 3.3 Средняя скорость
        avg_speed = analyzer.get_avg_speed()
        logger.info(f"\n📊 СРЕДНЯЯ СКОРОСТЬ: {avg_speed:.2f} м/с")

        # 3.4 Самолеты со скоростью выше средней
        logger.info("\n📊 САМОЛЕТЫ СО СКОРОСТЬЮ ВЫШЕ СРЕДНЕЙ (первые 5):")
        fast_planes = analyzer.get_aeroplanes_with_higher_speed()
        for plane in fast_planes[:5]:
            logger.info(f"  • {plane.get('callsign', 'N/A')} | "
                        f"Скорость: {plane.get('velocity', 'N/A')} м/с")

        # 3.5 Поиск по ключевому слову
        keyword = "UAL"
        logger.info(f"\n📊 САМОЛЕТЫ С КЛЮЧЕВЫМ СЛОВОМ '{keyword}':")
        keyword_planes = analyzer.get_aeroplanes_with_keyword(keyword)
        for plane in keyword_planes[:5]:
            logger.info(f"  • {plane.get('callsign', 'N/A')} | "
                        f"Страна: {plane.get('country_name', 'N/A')} | "
                        f"Скорость: {plane.get('velocity', 'N/A')} м/с")

        analyzer.disconnect()

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
    # Создаем конкретные реализации (Dependency Injection)
    storage = Database(DB_DSN)  # Используем DSN для подключения
    source = APIClient()
    analyzer = DBManager(DB_CONFIG)

    # Запускаем с внедренными зависимостями
    main(storage, source, analyzer)