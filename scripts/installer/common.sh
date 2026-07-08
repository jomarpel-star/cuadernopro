#!/usr/bin/env bash

COMPOSE_CMD=()

detectar_comando_compose() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(docker compose)
        return 0
    fi

    if command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(docker-compose)
        return 0
    fi

    echo "ERROR: No se encontro Docker Compose." >&2
    echo "Instala Docker Compose o revisa que 'docker compose' funcione." >&2
    exit 1
}

comprobar_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "ERROR: Docker no esta instalado o no esta en PATH." >&2
        exit 1
    fi

    if ! docker info >/dev/null 2>&1; then
        echo "ERROR: Docker esta instalado, pero no responde." >&2
        echo "Revisa que el servicio Docker este iniciado y que tu usuario tenga permisos." >&2
        exit 1
    fi
}

cargar_env() {
    if [ ! -f .env ]; then
        if [ ! -f .env.example ]; then
            echo "ERROR: No existe .env ni .env.example." >&2
            exit 1
        fi

        cp .env.example .env
        echo "Se ha creado .env desde .env.example. Puedes editar el puerto antes de continuar."
    fi
}

crear_runtime() {
    mkdir -p runtime runtime/backups runtime/exports runtime/documentos
}

obtener_puerto() {
    local puerto="8503"
    local linea=""

    if [ -f .env ]; then
        linea="$(grep -E '^[[:space:]]*CUADERNOPRO_PORT[[:space:]]*=' .env | tail -n 1 || true)"
        if [ -n "$linea" ]; then
            puerto="${linea#*=}"
            puerto="${puerto%%#*}"
            puerto="$(printf '%s' "$puerto" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
            puerto="${puerto%\"}"
            puerto="${puerto#\"}"
            puerto="${puerto%\'}"
            puerto="${puerto#\'}"
        fi
    fi

    if [ -z "$puerto" ]; then
        puerto="8503"
    fi

    printf '%s\n' "$puerto"
}

puerto_en_uso() {
    local puerto="$1"

    if command -v ss >/dev/null 2>&1; then
        ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(:|\\.)${puerto}$"
        return $?
    fi

    if command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$puerto" -sTCP:LISTEN -Pn >/dev/null 2>&1
        return $?
    fi

    if command -v netstat >/dev/null 2>&1; then
        netstat -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(:|\\.)${puerto}$"
        return $?
    fi

    return 2
}

mostrar_url() {
    local puerto
    local ip

    puerto="$(obtener_puerto)"
    ip="IP_DEL_SERVIDOR"

    if command -v hostname >/dev/null 2>&1; then
        ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
        if [ -z "$ip" ]; then
            ip="IP_DEL_SERVIDOR"
        fi
    fi

    echo "Accede desde: http://${ip}:${puerto}"
    echo "Acceso local: http://localhost:${puerto}"
}
