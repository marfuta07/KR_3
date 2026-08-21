"""
Модуль для работы с внешними API.

Содержит класс APIClient, реализующий интерфейс DataSource.
"""

import requests
import time
import logging
from typing import List, Dict, Any, Optional
from src.interfaces import DataSource

logger = logging.getLogger(__name__)


class APIClient(DataSource):
    """
    Реализация DataSource для OpenSky Network и Nominatim API.

    Отвечает за получение координат стран и данных о самолетах.
    """

    def __init__(self):
        """Инициализация HTTP сессии."""
        self.session = requests.Session()

    def get_country_coordinates(self, country_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение координат страны через Nominatim API.

        Args:
            country_name: Название страны

        Returns:
            Optional[Dict[str, Any]]: Словарь с координатами или None
        """
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': country_name,
                'format': 'json',
                'limit': 1
            }
            headers = {'User-Agent': 'AviationDataCollector/1.0'}

            logger.info(f"🌍 Запрос координат для {country_name}...")
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data:
                result = {
                    'name': country_name,
                    'country_code': data[0].get('address', {}).get('country_code', '').upper(),
                    'latitude': float(data[0]['lat']),
                    'longitude': float(data[0]['lon'])
                }
                logger.info(f"✅ Получены координаты {country_name}: "
                            f"{result['latitude']:.2f}, {result['longitude']:.2f}")
                return result

            logger.warning(f"⚠️ Координаты для {country_name} не найдены")
            return None

        except requests.exceptions.Timeout:
            logger.error(f"⏰ Таймаут при запросе координат {country_name}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения координат {country_name}: {e}")
            return None

    def get_aeroplanes_by_bounding_box(self, lat_min: float, lat_max: float,
                                       lon_min: float, lon_max: float) -> List[Dict[str, Any]]:
        """
        Получение самолетов по ограничивающему прямоугольнику через OpenSky API.

        Args:
            lat_min: Минимальная широта
            lat_max: Максимальная широта
            lon_min: Минимальная долгота
            lon_max: Максимальная долгота

        Returns:
            List[Dict[str, Any]]: Список самолетов
        """
        try:
            url = "https://opensky-network.org/api/states/all"
            params = {
                'lamin': lat_min,
                'lamax': lat_max,
                'lomin': lon_min,
                'lomax': lon_max
            }

            logger.info(f"✈️ Запрос данных для области: "
                        f"lat[{lat_min:.2f}..{lat_max:.2f}], "
                        f"lon[{lon_min:.2f}..{lon_max:.2f}]")

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            states = data.get('states')

            if states is None:
                logger.warning("⚠️ API вернул None")
                return []

            aeroplanes = []
            for state in states:
                if state and len(state) >= 17:
                    aeroplane = {
                        'icao24': state[0],
                        'callsign': state[1].strip() if state[1] else None,
                        'origin_country': state[2],
                        'time_position': state[3],
                        'last_contact': state[4],
                        'longitude': state[5],
                        'latitude': state[6],
                        'baro_altitude': state[7],
                        'on_ground': state[8],
                        'velocity': state[9],
                        'true_track': state[10],
                        'vertical_rate': state[11],
                        'sensors': str(state[12]) if state[12] is not None else None,
                        'geo_altitude': state[13],
                        'squawk': state[14],
                        'spi': state[15],
                        'position_source': state[16]
                    }
                    aeroplanes.append(aeroplane)

            logger.info(f"✅ Найдено {len(aeroplanes)} самолетов")
            return aeroplanes

        except requests.exceptions.Timeout:
            logger.error("⏰ Таймаут при запросе к OpenSky API")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка сети: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка получения самолетов: {e}")
            return []

    def get_aeroplanes_in_area(self, lat_min: float, lat_max: float,
                               lon_min: float, lon_max: float) -> List[Dict[str, Any]]:
        """
        Получение самолетов в заданной области (реализация интерфейса).

        Args:
            lat_min: Минимальная широта
            lat_max: Максимальная широта
            lon_min: Минимальная долгота
            lon_max: Максимальная долгота

        Returns:
            List[Dict[str, Any]]: Список самолетов
        """
        return self.get_aeroplanes_by_bounding_box(lat_min, lat_max, lon_min, lon_max)