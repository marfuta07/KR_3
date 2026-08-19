import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DBManager:
    """Класс для аналитики данных в БД"""

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.cursor = None

    def connect(self):
        """Установка соединения с БД"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logger.info("✅ DBManager подключен к БД")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            raise

    def disconnect(self):
        """Закрытие соединения"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("🔌 DBManager отключен")

    def get_countries_and_aeroplanes_count(self) -> List[Dict[str, Any]]:
        """
        Получает список всех стран и количество самолетов в их воздушных пространствах
        """
        try:
            self.cursor.execute("""
                SELECT 
                    c.name as country_name,
                    c.country_code,
                    COUNT(a.id) as aeroplanes_count
                FROM countries c
                LEFT JOIN aeroplanes a ON c.id = a.country_id
                GROUP BY c.id, c.name, c.country_code
                ORDER BY aeroplanes_count DESC
            """)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных: {e}")
            raise

    def get_all_aeroplanes(self) -> List[Dict[str, Any]]:
        """
        Получает список всех воздушных судов (только в воздухе)
        """
        try:
            self.cursor.execute("""
                SELECT 
                    a.icao24,
                    a.callsign,
                    c.name as country_name,
                    a.origin_country,
                    a.latitude,
                    a.longitude,
                    a.velocity,
                    a.baro_altitude,
                    a.on_ground,
                    a.created_at
                FROM aeroplanes a
                LEFT JOIN countries c ON a.country_id = c.id
                WHERE a.on_ground = FALSE
                ORDER BY a.velocity DESC NULLS LAST
            """)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных: {e}")
            raise

    def get_avg_speed(self) -> float:
        """
        Получает среднюю скорость по самолетам (только в воздухе)
        """
        try:
            self.cursor.execute("""
                SELECT AVG(velocity) as avg_speed
                FROM aeroplanes
                WHERE velocity IS NOT NULL 
                  AND on_ground = FALSE
                  AND velocity > 0
            """)
            result = self.cursor.fetchone()
            avg = result['avg_speed'] if result and result['avg_speed'] else 0.0
            logger.info(f"📊 Средняя скорость: {avg:.2f} м/с")
            return avg
        except Exception as e:
            logger.error(f"❌ Ошибка получения средней скорости: {e}")
            raise

    def get_aeroplanes_with_higher_speed(self) -> List[Dict[str, Any]]:
        """
        Получает список всех самолетов, у которых скорость выше средней
        """
        try:
            avg_speed = self.get_avg_speed()
            self.cursor.execute("""
                SELECT 
                    a.icao24,
                    a.callsign,
                    c.name as country_name,
                    a.velocity,
                    a.latitude,
                    a.longitude,
                    a.baro_altitude
                FROM aeroplanes a
                LEFT JOIN countries c ON a.country_id = c.id
                WHERE a.velocity > %s
                  AND a.on_ground = FALSE
                  AND a.velocity IS NOT NULL
                ORDER BY a.velocity DESC
            """, (avg_speed,))
            result = self.cursor.fetchall()
            logger.info(f"✈️ Найдено {len(result)} самолетов со скоростью выше средней")
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных: {e}")
            raise

    def get_aeroplanes_with_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Получает список всех самолетов, в позывном которых содержатся переданные символы
        """
        try:
            self.cursor.execute("""
                SELECT 
                    a.icao24,
                    a.callsign,
                    c.name as country_name,
                    a.origin_country,
                    a.velocity,
                    a.latitude,
                    a.longitude,
                    a.baro_altitude,
                    a.on_ground
                FROM aeroplanes a
                LEFT JOIN countries c ON a.country_id = c.id
                WHERE a.callsign ILIKE %s
                ORDER BY a.callsign
            """, (f'%{keyword}%',))
            result = self.cursor.fetchall()
            logger.info(f"🔍 Найдено {len(result)} самолетов с ключевым словом '{keyword}'")
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных: {e}")
            raise