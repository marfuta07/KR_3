import logging
import time
from src.config import DB_CONFIG, COUNTRIES
from src.database import Database
from src.api_inf import APIClient
from src.db_manager import DBManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """
    Алгоритм работы программы при каждом запуске:
    1. Проверка наличия таблиц в БД (если нет - создаем)
    2. Очистка старых данных (TRUNCATE)
    3. Получение свежих данных из API
    4. Загрузка данных в БД
    5. Аналитика через DBManager
    """

    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК ПРОГРАММЫ СБОРА ДАННЫХ О САМОЛЕТАХ")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        # ===== ШАГ 1: Подготовка БД =====
        logger.info("\n📌 ШАГ 1: Подготовка базы данных")
        db = Database(DB_CONFIG)
        db.connect()

        # Проверяем и создаем таблицы если их нет
        db.create_tables_if_not_exists()

        # Очищаем старые данные (полная перезапись)
        db.clear_data()

        # ===== ШАГ 2: Сбор данных из API =====
        logger.info("\n📌 ШАГ 2: Сбор данных из API")
        api_client = APIClient()

        # 2.1 Получаем координаты стран
        countries_data = {}
        for country in COUNTRIES:
            logger.info(f"\n📍 Обработка страны: {country}")
            country_info = api_client.get_country_coordinates(country)

            if country_info:
                # Сохраняем страну в БД и получаем ее ID
                country_id = db.insert_country(country_info)
                countries_data[country] = {
                    'id': country_id,
                    'info': country_info
                }
                logger.info(f"✅ Страна {country} сохранена с ID {country_id}")
            else:
                logger.warning(f"⚠️ Пропускаем страну {country} (координаты не найдены)")

            time.sleep(1)  # Задержка для соблюдения лимитов API

        # 2.2 Получаем данные о самолетах для каждой страны
        total_aeroplanes = 0
        for country, data in countries_data.items():
            logger.info(f"\n✈️ Поиск самолетов в воздушном пространстве {country}")

            lat = data['info']['latitude']
            lon = data['info']['longitude']

            # Создаем область вокруг страны (±5 градусов)
            lat_min = lat - 5
            lat_max = lat + 5
            lon_min = lon - 5
            lon_max = lon + 5

            # Получаем самолеты
            aeroplanes = api_client.get_aeroplanes_by_bounding_box(
                lat_min, lat_max, lon_min, lon_max
            )

            # Сохраняем самолеты в БД
            for aeroplane in aeroplanes:
                aeroplane['country_id'] = data['id']
                db.insert_aeroplane(aeroplane)

            total_aeroplanes += len(aeroplanes)
            logger.info(f"✅ Сохранено {len(aeroplanes)} самолетов для {country}")

            time.sleep(1)  # Задержка для соблюдения лимитов API

        # Закрываем соединение с БД для записи
        db.disconnect()

        # ===== ШАГ 3: Аналитика данных =====
        logger.info("\n📌 ШАГ 3: Анализ данных через DBManager")
        db_manager = DBManager(DB_CONFIG)
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

        # 3.4 Самолеты со скоростью выше средней (первые 5)
        logger.info("\n📊 САМОЛЕТЫ СО СКОРОСТЬЮ ВЫШЕ СРЕДНЕЙ (первые 5):")
        fast_planes = db_manager.get_aeroplanes_with_higher_speed()
        for plane in fast_planes[:5]:
            logger.info(f"  • {plane.get('callsign', 'N/A')} | "
                        f"Скорость: {plane.get('velocity', 'N/A')} м/с")

        # 3.5 Поиск по ключевому слову
        keyword = "AFL"  # Аэрофлот
        logger.info(f"\n📊 САМОЛЕТЫ С КЛЮЧЕВЫМ СЛОВОМ '{keyword}':")
        keyword_planes = db_manager.get_aeroplanes_with_keyword(keyword)
        for plane in keyword_planes[:5]:
            logger.info(f"  • {plane.get('callsign', 'N/A')} | "
                        f"Страна: {plane.get('country_name', 'N/A')} | "
                        f"Скорость: {plane.get('velocity', 'N/A')} м/с")

        db_manager.disconnect()

        # ===== ИТОГИ =====
        elapsed_time = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info("✅ ПРОГРАММА УСПЕШНО ЗАВЕРШЕНА")
        logger.info(f"📊 ИТОГО СОБРАНО: {total_aeroplanes} самолетов")
        logger.info(f"⏱️ ВРЕМЯ ВЫПОЛНЕНИЯ: {elapsed_time:.2f} секунд")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        raise


if __name__ == "__main__":
    main()