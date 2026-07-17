#!/usr/bin/env bash
set -Eeuo pipefail

readonly MYSQL_SOCKET="/run/mysqld/mysqld.sock"
readonly MYSQL_PID_FILE="/run/mysqld/mysqld.pid"
MYSQL_PID=""
APP_PID=""

log() {
    printf '[cyber-dashboard] %s\n' "$*"
}

require_safe_identifier() {
    local name="$1"
    local value="$2"
    if [[ -z "${value}" || "${value}" =~ [^A-Za-z0-9_] ]]; then
        log "${name} must contain only letters, numbers, and underscores."
        exit 1
    fi
}

require_safe_password() {
    if [[ -z "${DB_PASSWORD}" || "${DB_PASSWORD}" =~ [^A-Za-z0-9_.-] ]]; then
        log "DB_PASSWORD may contain only letters, numbers, dots, dashes, and underscores."
        exit 1
    fi
}

stop_processes() {
    local exit_code=$?
    trap - EXIT TERM INT

    if [[ -n "${APP_PID}" ]] && kill -0 "${APP_PID}" 2>/dev/null; then
        log "Stopping Cyber Dashboard."
        kill -TERM "${APP_PID}" 2>/dev/null || true
        wait "${APP_PID}" 2>/dev/null || true
    fi

    if [[ -n "${MYSQL_PID}" ]] && kill -0 "${MYSQL_PID}" 2>/dev/null; then
        log "Stopping MySQL."
        mysqladmin \
            --protocol=socket \
            --socket="${MYSQL_SOCKET}" \
            --user=root \
            shutdown >/dev/null 2>&1 || kill -TERM "${MYSQL_PID}" 2>/dev/null || true
        wait "${MYSQL_PID}" 2>/dev/null || true
    fi

    exit "${exit_code}"
}

trap stop_processes EXIT TERM INT

require_safe_identifier "DB_NAME" "${DB_NAME}"
require_safe_identifier "DB_USER" "${DB_USER}"
require_safe_password

case "${LOAD_DEMO_DATA,,}" in
    true|false) ;;
    *)
        log "LOAD_DEMO_DATA must be true or false."
        exit 1
        ;;
esac

mkdir -p /run/mysqld /var/lib/mysql /opt/cyber-dashboard/instance
chown -R mysql:mysql /run/mysqld /var/lib/mysql
chown -R cyberdashboard:cyberdashboard /opt/cyber-dashboard/instance

if [[ ! -d /var/lib/mysql/mysql ]]; then
    log "Initializing the internal MySQL data directory."
    mysqld --initialize-insecure --user=mysql --datadir=/var/lib/mysql
fi

log "Starting internal MySQL on 127.0.0.1:${DB_PORT}."
mysqld \
    --user=mysql \
    --datadir=/var/lib/mysql \
    --socket="${MYSQL_SOCKET}" \
    --pid-file="${MYSQL_PID_FILE}" \
    --bind-address=127.0.0.1 \
    --port="${DB_PORT}" \
    --skip-name-resolve &
MYSQL_PID=$!

for _attempt in $(seq 1 60); do
    if mysqladmin \
        --protocol=socket \
        --socket="${MYSQL_SOCKET}" \
        --user=root \
        ping >/dev/null 2>&1; then
        break
    fi
    if ! kill -0 "${MYSQL_PID}" 2>/dev/null; then
        log "MySQL stopped before it became ready."
        exit 1
    fi
    sleep 1
done

if ! mysqladmin \
    --protocol=socket \
    --socket="${MYSQL_SOCKET}" \
    --user=root \
    ping >/dev/null 2>&1; then
    log "MySQL did not become ready within 60 seconds."
    exit 1
fi

log "Creating the application database and local database account."
mysql \
    --protocol=socket \
    --socket="${MYSQL_SOCKET}" \
    --user=root <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'127.0.0.1'
    IDENTIFIED BY '${DB_PASSWORD}';
ALTER USER '${DB_USER}'@'127.0.0.1'
    IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

log "Applying numbered SQL migrations."
python scripts/migrate.py

log "Seeding reference catalogs."
python scripts/seed.py

if [[ "${LOAD_DEMO_DATA,,}" == "true" ]]; then
    demo_user_count="$(
        MYSQL_PWD="${DB_PASSWORD}" mysql \
            --host="${DB_HOST}" \
            --port="${DB_PORT}" \
            --user="${DB_USER}" \
            --database="${DB_NAME}" \
            --batch \
            --skip-column-names \
            --execute="SELECT COUNT(*) FROM users WHERE email = 'admin.demo@demo.cyberdashboard.dev';"
    )"
    if [[ "${demo_user_count}" == "0" ]]; then
        log "Loading realistic linked demo records."
        python docs/inject_test_data.py \
            --confirm-db "${DB_NAME}" \
            --password "${DEMO_DATA_PASSWORD}"
    else
        log "Demo records already exist; keeping the tester's current data."
    fi
else
    log "Demo data loading is disabled."
fi

chown -R cyberdashboard:cyberdashboard /opt/cyber-dashboard/instance

log "Starting Cyber Dashboard at http://0.0.0.0:8080."
gunicorn \
    --bind 0.0.0.0:8080 \
    --workers "${GUNICORN_WORKERS}" \
    --threads "${GUNICORN_THREADS}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --user cyberdashboard \
    --group cyberdashboard \
    run:app &
APP_PID=$!

wait -n "${MYSQL_PID}" "${APP_PID}"
