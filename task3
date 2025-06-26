import json
import random
import argparse
from functools import total_ordering


@total_ordering
class Version:
    def __init__(self, version_str):
        self.version_parts = list(map(int, version_str.split('.')))

    def __eq__(self, other):
        return self.version_parts == other.version_parts

    def __lt__(self, other):
        return self.version_parts < other.version_parts

    def __str__(self):
        return '.'.join(map(str, self.version_parts))

    def __repr__(self):
        return f'Version("{str(self)}")'


def generate_version_from_template(template):
    """Генерирует 2 варианта версии на основе шаблона"""
    versions = []
    for _ in range(2):
        parts = []
        for part in template.split('.'):
            if part == '*':
                parts.append(str(random.randint(0, 9)))
            else:
                parts.append(part)
        versions.append('.'.join(parts))
    return versions


def load_config(config_path):
    """Загружает конфигурационный файл"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config


def main():
    parser = argparse.ArgumentParser(description='Генератор версий на основе шаблонов')
    parser.add_argument('version', help='Версия продукта для сравнения (формат X.Y.Z...)')
    parser.add_argument('config', help='Путь к конфигурационному файлу (JSON)')
    args = parser.parse_args()

    try:
        # Загрузка конфигурации
        config = load_config(args.config)

        # Генерация всех версий
        all_versions = []
        for template in config.values():
            generated = generate_version_from_template(template)
            all_versions.extend(generated)

        # Преобразование в объекты Version и сортировка
        version_objects = [Version(v) for v in all_versions]
        version_objects.sort()

        # Создание Version для входной версии
        input_version = Version(args.version)

        # Фильтрация версий старше входной
        older_versions = [v for v in version_objects if v < input_version]

        # Вывод результатов
        print("Все сгенерированные версии (отсортированные):")
        for v in version_objects:
            print(v)

        print("\nВерсии старше", args.version, ":")
        for v in older_versions:
            print(v)

    except json.JSONDecodeError:
        print("Ошибка: Неверный формат конфигурационного файла")
    except FileNotFoundError:
        print("Ошибка: Конфигурационный файл не найден")
    except ValueError as e:
        print(f"Ошибка: Некорректный формат версии - {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main()
