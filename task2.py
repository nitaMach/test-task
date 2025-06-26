import argparse
import os
import shutil
import json
import datetime
import subprocess
import logging
from typing import List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def clone_repository(repo_url: str, temp_dir: str) -> bool:
    """Клонирование репозитория во временную директорию"""
    logger.info(f"Начало клонирования репозитория из {repo_url}")
    try:
        subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)
        logger.info("Репозиторий успешно клонирован")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при клонировании репозитория: {e}")
        return False


def clean_directory(root_dir: str, keep_path: str) -> bool:
    """Удаление всех директорий, кроме указанной в keep_path"""
    logger.info(f"Очистка директорий, сохранение только {keep_path}")
    try:
        keep_path = os.path.normpath(keep_path)
        full_keep_path = os.path.join(root_dir, keep_path)

        # Проверка, что путь существует
        if not os.path.exists(full_keep_path):
            logger.error(f"Указанный путь {keep_path} не существует в репозитории")
            return False

        # Собираем все элементы в корне репозитория
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)

            # Пропускаем .git и наш целевой путь
            if item == '.git' or item_path == full_keep_path or item_path == os.path.dirname(full_keep_path):
                continue

            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                logger.info(f"Удалена директория: {item}")

        logger.info("Очистка директорий завершена")
        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке директорий: {e}")
        return False


def create_version_file(source_dir: str, version: str) -> bool:
    """Создание файла version.json в указанной директории"""
    logger.info(f"Создание version.json в {source_dir}")
    try:
        # Получаем список файлов с нужными расширениями
        allowed_extensions = ('.py', '.js', '.sh')
        files = [
            f for f in os.listdir(source_dir)
            if os.path.isfile(os.path.join(source_dir, f)) and f.endswith(allowed_extensions)
        ]

        version_data = {
            "name": "hello world",
            "version": version,
            "files": files
        }

        version_file_path = os.path.join(source_dir, 'version.json')
        with open(version_file_path, 'w') as f:
            json.dump(version_data, f, indent=2)

        logger.info(f"Файл version.json успешно создан: {version_data}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании version.json: {e}")
        return False


def create_archive(source_dir: str) -> str:
    """Создание архива с исходным кодом"""
    try:
        # Получаем имя последней директории в пути
        last_dir = os.path.basename(os.path.normpath(source_dir))

        # Формируем имя архива
        today = datetime.datetime.now().strftime("%Y%m%d")
        archive_name = f"{last_dir}{today}"

        # Создаем архив
        parent_dir = os.path.dirname(source_dir)
        archive_path = os.path.join(parent_dir, archive_name)

        logger.info(f"Создание архива {archive_name} из {source_dir}")
        result_archive_path = shutil.make_archive(
            archive_path,
            'zip',
            source_dir
        )

        logger.info(f"Архив успешно создан: {result_archive_path}")
        return result_archive_path
    except Exception as e:
        logger.error(f"Ошибка при создании архива: {e}")
        return ""


def main():
    parser = argparse.ArgumentParser(description='Универсальный сборочный скрипт')
    parser.add_argument('repository_url', help='URL Git-репозитория')
    parser.add_argument('source_path', help='Относительный путь к исходному коду')
    parser.add_argument('version', help='Версия продукта')

    args = parser.parse_args()

    # Создаем временную директорию
    temp_dir = 'temp_repo'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    # 1. Клонируем репозиторий
    if not clone_repository(args.repository_url, temp_dir):
        return

    # 2. Очищаем директории
    if not clean_directory(temp_dir, args.source_path):
        shutil.rmtree(temp_dir)
        return

    # 3. Создаем version.json
    source_dir = os.path.join(temp_dir, args.source_path)
    if not create_version_file(source_dir, args.version):
        shutil.rmtree(temp_dir)
        return

    # 4. Создаем архив
    archive_path = create_archive(source_dir)
    if not archive_path:
        shutil.rmtree(temp_dir)
        return

    # Перемещаем архив в текущую директорию
    final_archive = os.path.basename(archive_path)
    shutil.move(archive_path, final_archive)

    # Очищаем временные файлы
    shutil.rmtree(temp_dir)

    logger.info(f"Сборка успешно завершена! Создан архив: {final_archive}")


if __name__ == '__main__':
    main()
