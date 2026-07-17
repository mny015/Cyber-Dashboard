# syntax=docker/dockerfile:1.7

# Self-contained coursework/demo image: Ubuntu, MySQL, Python, and Cyber Dashboard.
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG CYBER_DASHBOARD_REPOSITORY=https://github.com/mny015/Cyber-Dashboard.git
ARG CYBER_DASHBOARD_REF=main

ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        mysql-server \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN git clone \
        --depth 1 \
        --branch "${CYBER_DASHBOARD_REF}" \
        "${CYBER_DASHBOARD_REPOSITORY}" \
        /opt/cyber-dashboard \
    && rm -rf /opt/cyber-dashboard/.git \
    && python3 -m venv "${VIRTUAL_ENV}" \
    && "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir --upgrade pip \
    && "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir \
        -r /opt/cyber-dashboard/requirements.txt \
        gunicorn==23.0.0

RUN useradd \
        --system \
        --create-home \
        --home-dir /home/cyberdashboard \
        --shell /usr/sbin/nologin \
        cyberdashboard \
    && mkdir -p \
        /opt/cyber-dashboard/instance \
        /run/mysqld \
        /var/lib/mysql \
    && chown -R cyberdashboard:cyberdashboard /opt/cyber-dashboard/instance \
    && chown -R mysql:mysql /run/mysqld /var/lib/mysql

COPY docker/all-in-one-entrypoint.sh /usr/local/bin/cyber-dashboard-entrypoint
RUN sed -i 's/\r$//' /usr/local/bin/cyber-dashboard-entrypoint \
    && chmod 0755 /usr/local/bin/cyber-dashboard-entrypoint

WORKDIR /opt/cyber-dashboard

# These defaults are intentionally local-demo credentials. Override them when
# sharing an image beyond a trusted coursework verification environment.
ENV APP_ENV=development \
    SECRET_KEY=docker-demo-secret-key-change-before-sharing-2026 \
    DB_HOST=127.0.0.1 \
    DB_PORT=3306 \
    DB_USER=cyber_dashboard_user \
    DB_PASSWORD=cyber_dashboard_demo \
    DB_NAME=cyber_dashboard \
    DB_CHARSET=utf8mb4 \
    DB_POOL_SIZE=5 \
    DB_POOL_TIMEOUT=5 \
    MFA_ENCRYPTION_KEY=MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA= \
    REAUTHENTICATION_MAX_AGE=600 \
    TRUSTED_PROXY_HOPS=0 \
    PROFILE_IMAGE_MAX_BYTES=2097152 \
    SESSION_COOKIE_SECURE=false \
    RATELIMIT_STORAGE_URI=memory:// \
    LOG_FILE=instance/cyber_dashboard.log \
    LOAD_DEMO_DATA=true \
    DEMO_DATA_PASSWORD=CyberDemo2026! \
    GUNICORN_WORKERS=2 \
    GUNICORN_THREADS=4

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=5s --start-period=60s --retries=5 \
    CMD curl --fail --silent --show-error http://127.0.0.1:8080/api/ping || exit 1

ENTRYPOINT ["/usr/local/bin/cyber-dashboard-entrypoint"]
