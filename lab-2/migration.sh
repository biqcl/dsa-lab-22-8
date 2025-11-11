 #!/bin/bash

set -euo pipefail

# Параметры подключения к базе данных
DB_NAME="${DB_NAME:-database}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Путь к директории с миграциями 
MIGRATIONS_DIR="${MIGRATIONS_DIR:-.}"

# Функция для выполнения SQL-скрипта из файла
run_sql() {
    local file="$1"
    PGPASSWORD="postgres" /C/Program\ Files/PostgreSQL/17/bin/psql.exe -U "$DB_USER" -d "$DB_NAME" -f "$file" \
        -h "$DB_HOST" \
        -p "$DB_PORT" 
}

# Функция для выполнения SQL-команды, переданной в виде строки
run_sql_c() {
    local command="$1"
    PGPASSWORD="postgres" /C/Program\ Files/PostgreSQL/17/bin/psql.exe -U "$DB_USER" -d "$DB_NAME" -c "$command" \
        -h "$DB_HOST" \
        -p "$DB_PORT" 
}

# Основная логика скрипта 
echo "Создание таблицы migrations"
run_sql_c "
CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"

echo "Получение списка применённых миграций"
applied_migrations=$(
    PGPASSWORD="postgres" /C/Program\ Files/PostgreSQL/17/bin/psql.exe -U "$DB_USER" -d "$DB_NAME" \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -t \
        -c "SELECT migration_name FROM migrations;"
)

echo "Начинаем применение миграций из директории: $(realpath "$MIGRATIONS_DIR")"

for file in $(find "$MIGRATIONS_DIR" -maxdepth 1 -name "*.sql" | sort -V); do
    migration_name=$(basename "$file")
    echo "Проверяем миграцию: $migration_name"

    if echo "$applied_migrations" | grep -q "^$migration_name$"; then
        echo "Миграция '$migration_name' уже применена, пропускаем."
    else
        echo "Применяем новую миграцию: '$migration_name'"
        run_sql "$file"

        escaped_migration_name=$(echo "$migration_name" | sed "s/'/''/g")
        run_sql_c "INSERT INTO migrations (migration_name) VALUES ('$escaped_migration_name');"

        echo "Миграция '$migration_name' успешно применена и записана в журнал."
    fi
done

echo "Все миграции применены."
