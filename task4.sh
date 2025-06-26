#!/bin/bash
set -euo pipefail

# Конфигурация
OLD_BASE="/opt/misc"
NEW_BASE="/srv/data"
UNIT_PREFIX="foobar-"
LOG_FILE="/var/log/foobar_migration.log"

# Инициализация лог-файла
exec > >(tee -a "$LOG_FILE") 2>&1
echo "=== Начало миграции $(date) ==="

# Функция для вывода сообщений с отметкой времени
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Функция проверки существования юнита
unit_exists() {
    systemctl list-units --all --no-legend "$1" | grep -q "$1"
}

# Функция остановки сервиса
stop_service() {
    local unit_name="$1"
    log "Остановка сервиса $unit_name"
    if systemctl is-active --quiet "$unit_name"; then
        systemctl stop "$unit_name" || {
            log "Ошибка: не удалось остановить $unit_name"
            return 1
        }
        log "Сервис $unit_name успешно остановлен"
    else
        log "Сервис $unit_name уже остановлен"
    fi
}

# Функция переноса файлов
move_files() {
    local service_name="$1"
    local old_dir="$OLD_BASE/$service_name"
    local new_dir="$NEW_BASE/$service_name"

    log "Перенос файлов из $old_dir в $new_dir"

    # Проверка существования исходной директории
    if [ ! -d "$old_dir" ]; then
        log "Ошибка: исходная директория $old_dir не существует"
        return 1
    fi

    # Создание целевой директории
    mkdir -p "$new_dir" || {
        log "Ошибка: не удалось создать директорию $new_dir"
        return 1
    }

    # Копирование файлов с сохранением атрибутов
    cp -a "$old_dir/." "$new_dir/" || {
        log "Ошибка: не удалось скопировать файлы из $old_dir в $new_dir"
        return 1
    }

    # Проверка целостности копирования
    local diff_result
    diff_result=$(diff -qr "$old_dir" "$new_dir" 2>&1)
    if [ -n "$diff_result" ]; then
        log "Ошибка: различия между исходной и целевой директориями"
        log "Подробности: $diff_result"
        return 1
    fi

    log "Файлы успешно перенесены в $new_dir"
}

# Функция изменения юнита
modify_unit() {
    local unit_name="$1"
    local service_name="${unit_name#$UNIT_PREFIX}"
    local new_dir="$NEW_BASE/$service_name"
    local unit_file="/etc/systemd/system/$unit_name.service"

    log "Модификация юнита $unit_name"

    # Проверка существования файла юнита
    if [ ! -f "$unit_file" ]; then
        log "Ошибка: файл юнита $unit_file не найден"
        return 1
    fi

    # Создание резервной копии
    cp "$unit_file" "$unit_file.bak" || {
        log "Ошибка: не удалось создать резервную копию $unit_file"
        return 1
    }

    # Обновление WorkingDirectory
    sed -i "s|^WorkingDirectory=$OLD_BASE/$service_name|WorkingDirectory=$new_dir|" "$unit_file" || {
        log "Ошибка: не удалось обновить WorkingDirectory"
        return 1
    }

    # Обновление ExecStart
    sed -i "s|^ExecStart=$OLD_BASE/$service_name|ExecStart=$new_dir|" "$unit_file" || {
        log "Ошибка: не удалось обновить ExecStart"
        return 1
    }

    # Перезагрузка systemd
    systemctl daemon-reload || {
        log "Ошибка: не удалось перезагрузить конфигурацию systemd"
        return 1
    }

    log "Юнит $unit_name успешно модифицирован"
}

# Функция запуска сервиса
start_service() {
    local unit_name="$1"
    log "Запуск сервиса $unit_name"
    systemctl start "$unit_name" || {
        log "Ошибка: не удалось запустить $unit_name"
        return 1
    }
    log "Сервис $unit_name успешно запущен"
}

# Основная функция обработки юнита
process_unit() {
    local unit_name="$1"
    local service_name="${unit_name#$UNIT_PREFIX}"

    log "Начало обработки юнита $unit_name"

    # Проверка существования юнита
    if ! unit_exists "$unit_name"; then
        log "Ошибка: юнит $unit_name не существует"
        return 1
    fi

    # Выполнение шагов миграции
    stop_service "$unit_name" || return 1
    move_files "$service_name" || return 1
    modify_unit "$unit_name" || return 1
    start_service "$unit_name" || return 1

    log "Юнит $unit_name успешно обработан"
}

# Основная функция
main() {
    log "Поиск юнитов с префиксом $UNIT_PREFIX"

    # Получение списка юнитов
    mapfile -t units < <(systemctl list-units --all --no-legend "${UNIT_PREFIX}*" | awk '{print $1}')

    if [ ${#units[@]} -eq 0 ]; then
        log "Не найдено юнитов с префиксом $UNIT_PREFIX"
        return 0
    fi

    log "Найдены юниты: ${units[*]}"

    # Обработка каждого юнита
    for unit in "${units[@]}"; do
        if [[ "$unit" == *@.* ]]; then
            log "Пропуск шаблонного юнита $unit"
            continue
        fi

        process_unit "$unit" || {
            log "Ошибка при обработке юнита $unit. Прерывание миграции."
            return 1
        }
    done

    log "Миграция успешно завершена"
}

# Запуск основной функции
if main; then
    log "=== Успешное завершение миграции ==="
    exit 0
else
    log "=== Миграция завершена с ошибками ==="
    exit 1
fi
