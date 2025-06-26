import requests
import datetime
import time
from typing import Dict, Tuple, Optional


class TimeSyncClient:
    """Клиент для получения и анализа данных о времени из Yandex Time API."""

    def __init__(self):
        """Инициализация клиента с настройками подключения."""
        self.api_url = "https://yandex.com/time/sync.json?geo=213"  # URL API времени
        self.timeout = 5  # Таймаут подключения в секундах

    def fetch_time_data(self) -> Dict:
        """
        Получение данных о времени от API.

        Возвращает:
            Dict: Словарь с данными о времени и временной зоне

        Исключения:
            Exception: При ошибках сети или неверном ответе API
        """
        try:
            response = requests.get(self.api_url, timeout=self.timeout)
            response.raise_for_status()  # Проверка кода ответа
            return response.json()  # Парсинг JSON
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка запроса к API: {str(e)}")

    def process_time_response(self, raw_data: Dict) -> Tuple[str, str, int]:
        """
        Обработка сырых данных от API.

        Аргументы:
            raw_data: Сырой ответ API в виде словаря

        Возвращает:
            tuple: (форматированное время, временная зона, timestamp)

        Исключения:
            ValueError: При неверном формате данных
        """
        if not raw_data or 'time' not in raw_data or 'clocks' not in raw_data:
            raise ValueError("Некорректный формат ответа API")

        timestamp = raw_data['time'] / 1000  # Конвертация из мс в секунды
        list_keys = list(raw_data['clocks'].keys())  # Получение списка идентификаторов для текущей временной зоны
        timezone = raw_data['clocks'][list_keys[0]]['name']  # Название временной зоны

        # Форматирование времени в читаемый вид
        dt = datetime.datetime.fromtimestamp(timestamp)
        readable_time = dt.strftime("%Y-%m-%d %H:%M:%S")

        return readable_time, timezone, raw_data['time']

    def measure_time_delta(self, local_before: float, server_time: int) -> float:
        """
        Расчет разницы между локальным и серверным временем.

        Аргументы:
            local_before: Локальное время до запроса (в секундах)
            server_time: Время сервера (в миллисекундах)

        Возвращает:
            float: Разница во времени в миллисекундах
        """
        server_time_sec = server_time / 1000  # Конвертация в секунды
        delta_ms = (server_time_sec - local_before) * 1000  # Расчет дельты
        return delta_ms

    def run_measurement_series(self, count: int = 5) -> float:
        """
        Выполнение серии измерений времени.

        Аргументы:
            count: Количество измерений (по умолчанию 5)

        Возвращает:
            float: Средняя задержка по всем измерениям

        Исключения:
            Exception: Если все измерения завершились ошибкой
        """
        deltas = []  # Список для хранения результатов

        for i in range(count):
            try:
                # 1. Фиксация локального времени перед запросом
                local_before = time.time()

                # 2. Получение данных от API
                raw_data = self.fetch_time_data()

                # 3. Обработка ответа
                readable_time, timezone, server_time = self.process_time_response(raw_data)

                # 4. Расчет временной дельты
                delta = self.measure_time_delta(local_before, server_time)
                deltas.append(delta)

                # Вывод результатов только для первого успешного измерения
                if i == 0:
                    print("\n[Сырой ответ API]")
                    print(raw_data)

                    print("\n[Обработанные данные]")
                    print(f"Время: {readable_time}")
                    print(f"Временная зона: {timezone}")

                    print("\n[Текущее измерение]")
                    print(f"Задержка: {delta:.2f} мс")

                # Небольшая пауза между измерениями
                if i < count - 1:
                    time.sleep(0.5)

            except Exception as e:
                print(f"Измерение {i + 1} не удалось: {str(e)}")
                continue

        if not deltas:
            raise Exception("Все измерения завершились ошибкой")

        # Расчет и вывод средней задержки
        average_delta = sum(deltas) / len(deltas)
        print(f"\n[Результаты серии ({len(deltas)} успешных измерений)]")
        print(f"Средняя задержка: {average_delta:.2f} мс")

        return average_delta


def main():
    """Основная функция выполнения программы."""
    print("=== Time Sync Client ===")
    print("Запуск измерения времени...\n")

    client = TimeSyncClient()

    try:
        # Запуск серии из 5 измерений
        client.run_measurement_series(5)
    except Exception as e:
        print(f"\nКритическая ошибка: {str(e)}")
    finally:
        print("\nЗавершение работы программы.")


if __name__ == "__main__":
    main()
