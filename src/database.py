"""
Модуль для работы с базой данных PostgreSQL.

Содержит класс Database, реализующий интерфейс DataStorage.
"""

import psycopg2
import logging
from typing import Dict, List, Any, Optional
from src.interfaces import DataStorage

logger = logging.getLogger(__name__)


class Database(DataStorage):
    """
    Реализация DataStorage для PostgreSQL.

    Отвечает за подключение, создание таблиц,
    очистку данных и вставку записей.
    """

    def __init__(self, db_config):
        """
        Инициализация объекта Database.

        Args:
            db_config: DSN строка или словарь с параметрами подключения
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None

    def connect(self) -> None:
        """Установка соединения с базой данных."""
        try:
            if isinstance(self.db_config, str):
                self.connection = psycopg2.connect(self.db_config)
            else:
                self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            logger.info("✅ Подключение к БД установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    def disconnect(self) -> None:
        """Закрытие соединения с базой данных."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("🔌 Соединение с БД закрыто")

    def create_tables(self) -> None:
        """Создание таблиц, если они не существуют."""
        try:
            logger.info("📋 Создание таблиц...")

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS countries (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    country_code VARCHAR(10),
                    latitude FLOAT,
                    longitude FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS aeroplanes (
                    id SERIAL PRIMARY KEY,
                    icao24 VARCHAR(20) NOT NULL,
                    callsign VARCHAR(50),
                    country_id INTEGER REFERENCES countries(id),
                    origin_country VARCHAR(255),
                    time_position INTEGER,
                    last_contact INTEGER,
                    longitude FLOAT,
                    latitude FLOAT,
                    baro_altitude FLOAT,
                    on_ground BOOLEAN,
                    velocity FLOAT,
                    true_track FLOAT,
                    vertical_rate FLOAT,
                    sensors VARCHAR(255),
                    geo_altitude FLOAT,
                    squawk VARCHAR(10),
                    spi BOOLEAN,
                    position_source INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Создаем индексы
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_aeroplanes_country_id 
                ON aeroplanes(country_id)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_aeroplanes_velocity 
                ON aeroplanes(velocity)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_aeroplanes_callsign 
                ON aeroplanes(callsign)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_aeroplanes_on_ground 
                ON aeroplanes(on_ground)
            """)

            self.connection.commit()
            logger.info("✅ Таблицы созданы/проверены")

        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            raise

    def clear_all(self) -> None:
        """Очистка всех данных в таблицах."""
        try:
            logger.info("🗑️ Очистка старых данных...")
            self.cursor.execute("TRUNCATE TABLE aeroplanes CASCADE")
            self.cursor.execute("TRUNCATE TABLE countries CASCADE")
            self.connection.commit()
            logger.info("✅ Данные очищены")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Ошибка очистки данных: {e}")
            raise

    def save_country(self, country_data: Dict[str, Any]) -> int:
        """
        Сохранение данных о стране.

        Args:
            country_data: Данные о стране

        Returns:
            int: ID сохраненной страны
        """
        try:
            self.cursor.execute("""
                INSERT INTO countries (name, country_code, latitude, longitude)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                country_data['name'],
                country_data.get('country_code'),
                country_data.get('latitude'),
                country_data.get('longitude')
            ))
            country_id = self.cursor.fetchone()[0]
            self.connection.commit()
            return country_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Ошибка сохранения страны: {e}")
            raise

    def save_aeroplane(self, aeroplane_data: Dict[str, Any]) -> None:
        """
        Сохранение данных о самолете.

        Args:
            aeroplane_data: Данные о самолете
        """
        try:
            self.cursor.execute("""
                INSERT INTO aeroplanes (
                    icao24, callsign, country_id, origin_country,
                    time_position, last_contact, longitude, latitude,
                    baro_altitude, on_ground, velocity, true_track,
                    vertical_rate, sensors, geo_altitude, squawk,
                    spi, position_source
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                          %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                aeroplane_data.get('icao24'),
                aeroplane_data.get('callsign'),
                aeroplane_data.get('country_id'),
                aeroplane_data.get('origin_country'),
                aeroplane_data.get('time_position'),
                aeroplane_data.get('last_contact'),
                aeroplane_data.get('longitude'),
                aeroplane_data.get('latitude'),
                aeroplane_data.get('baro_altitude'),
                aeroplane_data.get('on_ground'),
                aeroplane_data.get('velocity'),
                aeroplane_data.get('true_track'),
                aeroplane_data.get('vertical_rate'),
                aeroplane_data.get('sensors'),
                aeroplane_data.get('geo_altitude'),
                aeroplane_data.get('squawk'),
                aeroplane_data.get('spi'),
                aeroplane_data.get('position_source')
            ))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Ошибка сохранения самолета: {e}")
            raise

    def get_countries(self) -> List[Dict[str, Any]]:
        """
        Получение списка всех стран.

        Returns:
            List[Dict[str, Any]]: Список стран
        """
        try:
            self.cursor.execute("""
                SELECT id, name, country_code, latitude, longitude, created_at
                FROM countries
                ORDER BY name
            """)
            result = self.cursor.fetchall()
            columns = ['id', 'name', 'country_code', 'latitude', 'longitude', 'created_at']
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            logger.error(f"❌ Ошибка получения стран: {e}")
            raise

    def get_aeroplanes(self, country_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получение списка самолетов (опционально по стране).

        Args:
            country_id: ID страны для фильтрации

        Returns:
            List[Dict[str, Any]]: Список самолетов
        """
        try:
            if country_id:
                self.cursor.execute("""
                    SELECT 
                        id, icao24, callsign, country_id, origin_country,
                        time_position, last_contact, longitude, latitude,
                        baro_altitude, on_ground, velocity, true_track,
                        vertical_rate, sensors, geo_altitude, squawk,
                        spi, position_source, created_at
                    FROM aeroplanes
                    WHERE country_id = %s
                    ORDER BY created_at DESC
                """, (country_id,))
            else:
                self.cursor.execute("""
                    SELECT 
                        id, icao24, callsign, country_id, origin_country,
                        time_position, last_contact, longitude, latitude,
                        baro_altitude, on_ground, velocity, true_track,
                        vertical_rate, sensors, geo_altitude, squawk,
                        spi, position_source, created_at
                    FROM aeroplanes
                    ORDER BY created_at DESC
                    LIMIT 1000
                """)

            result = self.cursor.fetchall()
            columns = ['id', 'icao24', 'callsign', 'country_id', 'origin_country',
                       'time_position', 'last_contact', 'longitude', 'latitude',
                       'baro_altitude', 'on_ground', 'velocity', 'true_track',
                       'vertical_rate', 'sensors', 'geo_altitude', 'squawk',
                       'spi', 'position_source', 'created_at']
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            logger.error(f"❌ Ошибка получения самолетов: {e}")
            raise