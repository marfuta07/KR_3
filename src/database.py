import psycopg2
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Класс для управления БД: создание, очистка, загрузка данных"""

    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.cursor = None

    def connect(self):
        """Установка соединения с БД"""
        try:
            # Проверяем, что передано (словарь или строка DSN)
            if isinstance(self.db_config, dict):
                # Если словарь, пробуем подключиться через DSN строку
                logger.info("Подключение через DSN строку (из словаря)")

                # Собираем DSN вручную
                dsn = (
                    f"dbname={self.db_config.get('dbname', 'aviation_db')} "
                    f"user={self.db_config.get('user', 'postgres')} "
                    f"password={self.db_config.get('password', '')} "
                    f"host={self.db_config.get('host', 'localhost')} "
                    f"port={self.db_config.get('port', '5432')} "
                    f"client_encoding=utf8"
                )

                # Очищаем строку от лишних пробелов
                dsn = ' '.join(dsn.split())
                logger.info(
                    f"Подключение к: dbname={self.db_config.get('dbname')} user={self.db_config.get('user')} host={self.db_config.get('host')} port={self.db_config.get('port')}")

                self.connection = psycopg2.connect(dsn)

            elif isinstance(self.db_config, str):
                # Если уже строка DSN
                logger.info("Подключение через DSN строку")
                self.connection = psycopg2.connect(self.db_config)
            else:
                raise ValueError("db_config должен быть словарем или строкой DSN")

            self.cursor = self.connection.cursor()
            logger.info("✅ Подключение к БД установлено")

        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            logger.error(f"Тип db_config: {type(self.db_config)}")
            if isinstance(self.db_config, dict):
                safe_config = self.db_config.copy()
                safe_config['password'] = '***'
                logger.error(f"Параметры: {safe_config}")
            raise

    def disconnect(self):
        """Закрытие соединения"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("🔌 Соединение с БД закрыто")

    def create_tables_if_not_exists(self):
        """Создает таблицы, если они не существуют"""
        try:
            logger.info("📋 Проверка наличия таблиц...")

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
            logger.info("✅ Таблицы проверены/созданы успешно")

        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            raise

    def clear_data(self):
        """Очищает все данные из таблиц"""
        try:
            logger.info("🗑️ Очистка старых данных...")

            self.cursor.execute("SET CONSTRAINTS ALL DEFERRED")
            self.cursor.execute("TRUNCATE TABLE aeroplanes CASCADE")
            self.cursor.execute("TRUNCATE TABLE countries CASCADE")
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

            self.connection.commit()
            logger.info("✅ Старые данные удалены")

        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Ошибка очистки данных: {e}")
            raise

    def insert_country(self, country_data: Dict[str, Any]) -> int:
        """Вставка данных о стране"""
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
            logger.error(f"❌ Ошибка вставки страны {country_data.get('name')}: {e}")
            raise

    def insert_aeroplane(self, aeroplane_data: Dict[str, Any]):
        """Вставка данных о самолете"""
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
            logger.error(f"❌ Ошибка вставки самолета {aeroplane_data.get('icao24')}: {e}")
            raise
