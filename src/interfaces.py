"""
Модуль с абстрактными классами (интерфейсами) для проекта.

Определяет контракты, которые должны реализовывать все классы
для работы с данными и их хранения.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class DataStorage(ABC):
    """
    Абстрактный класс для хранилищ данных.

    Определяет методы, которые должны реализовывать все классы,
    отвечающие за хранение данных (БД, файлы, кэш и т.д.).
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Установка соединения с хранилищем.

        Raises:
            Exception: При ошибке подключения
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Закрытие соединения с хранилищем."""
        pass

    @abstractmethod
    def save_country(self, country_data: Dict[str, Any]) -> int:
        """
        Сохранение данных о стране.

        Args:
            country_data: Данные о стране (название, код, координаты)

        Returns:
            int: ID сохраненной страны

        Raises:
            Exception: При ошибке сохранения
        """
        pass

    @abstractmethod
    def save_aeroplane(self, aeroplane_data: Dict[str, Any]) -> None:
        """
        Сохранение данных о самолете.

        Args:
            aeroplane_data: Данные о самолете

        Raises:
            Exception: При ошибке сохранения
        """
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """Очистка всех данных в хранилище."""
        pass

    @abstractmethod
    def get_countries(self) -> List[Dict[str, Any]]:
        """
        Получение всех стран.

        Returns:
            List[Dict[str, Any]]: Список стран
        """
        pass

    @abstractmethod
    def get_aeroplanes(self, country_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получение самолетов (опционально по стране).

        Args:
            country_id: ID страны для фильтрации

        Returns:
            List[Dict[str, Any]]: Список самолетов
        """
        pass


class DataSource(ABC):
    """
    Абстрактный класс для источников данных.

    Определяет методы для получения данных из внешних источников
    (API, файлы, веб-скрапинг и т.д.).
    """

    @abstractmethod
    def get_country_coordinates(self, country_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение координат страны.

        Args:
            country_name: Название страны

        Returns:
            Optional[Dict[str, Any]]: Координаты или None
        """
        pass

    @abstractmethod
    def get_aeroplanes_in_area(self, lat_min: float, lat_max: float,
                               lon_min: float, lon_max: float) -> List[Dict[str, Any]]:
        """
        Получение самолетов в заданной области.

        Args:
            lat_min: Минимальная широта
            lat_max: Максимальная широта
            lon_min: Минимальная долгота
            lon_max: Максимальная долгота

        Returns:
            List[Dict[str, Any]]: Список самолетов в области
        """
        pass


class DataAnalyzer(ABC):
    """
    Абстрактный класс для анализа данных.

    Определяет методы для получения статистики и аналитики.
    """

    @abstractmethod
    def get_countries_and_aeroplanes_count(self) -> List[Dict[str, Any]]:
        """
        Получение стран и количества самолетов.

        Returns:
            List[Dict[str, Any]]: Статистика по странам
        """
        pass

    @abstractmethod
    def get_all_aeroplanes(self) -> List[Dict[str, Any]]:
        """
        Получение всех самолетов.

        Returns:
            List[Dict[str, Any]]: Список самолетов
        """
        pass

    @abstractmethod
    def get_avg_speed(self) -> float:
        """
        Получение средней скорости.

        Returns:
            float: Средняя скорость
        """
        pass

    @abstractmethod
    def get_aeroplanes_with_higher_speed(self) -> List[Dict[str, Any]]:
        """
        Получение самолетов со скоростью выше средней.

        Returns:
            List[Dict[str, Any]]: Список быстрых самолетов
        """
        pass

    @abstractmethod
    def get_aeroplanes_with_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Поиск самолетов по ключевому слову в позывном.

        Args:
            keyword: Ключевое слово для поиска

        Returns:
            List[Dict[str, Any]]: Найденные самолеты
        """
        pass