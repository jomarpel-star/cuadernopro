#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/scripts/installer/common.sh"

leer_env_valor() {
    local clave="$1"
    local linea=""
    local valor=""

    if [ -f .env ]; then
        linea="$(grep -E "^[[:space:]]*${clave}[[:space:]]*=" .env | tail -n 1 || true)"
    fi

    if [ -n "$linea" ]; then
        valor="${linea#*=}"
        valor="${valor%%#*}"
        valor="$(printf '%s' "$valor" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        valor="${valor%\"}"
        valor="${valor#\"}"
        valor="${valor%\'}"
        valor="${valor#\'}"
    fi

    printf '%s\n' "$valor"
}

actualizar_env() {
    local clave="$1"
    local valor="$2"
    local temporal

    temporal="$(mktemp)"
    awk -v clave="$clave" -v valor="$valor" '
        BEGIN { actualizado = 0 }
        $0 ~ "^" clave "=" {
            print clave "=" valor
            actualizado = 1
            next
        }
        { print }
        END {
            if (!actualizado) {
                print clave "=" valor
            }
        }
    ' .env > "$temporal"
    mv "$temporal" .env
}

if [ ! -f .env ]; then
    if [ ! -f .env.example ]; then
        echo "ERROR: No existe .env ni .env.example." >&2
        exit 1
    fi

    cp .env.example .env
    echo "Se ha creado .env desde .env.example."
    echo "Edita .env y configura CUADERNOPRO_DOMAIN y el hash de contrasena."
    echo "Puedes generar el hash con: ./proxy_hash_password.sh"
    exit 1
fi

dominio="$(leer_env_valor "CUADERNOPRO_DOMAIN")"
hash="$(leer_env_valor "CUADERNOPRO_PROXY_PASSWORD_HASH")"
bind_address="$(leer_env_valor "CUADERNOPRO_BIND_ADDRESS")"

if [ -z "$dominio" ] || [ "$dominio" = "cuadernopro.ejemplo.es" ]; then
    echo "ERROR: Configura CUADERNOPRO_DOMAIN en .env con un dominio real." >&2
    exit 1
fi

if [ -z "$hash" ]; then
    echo "ERROR: Configura CUADERNOPRO_PROXY_PASSWORD_HASH en .env." >&2
    echo "Generalo con: ./proxy_hash_password.sh" >&2
    exit 1
fi

if [ -z "$bind_address" ]; then
    actualizar_env "CUADERNOPRO_BIND_ADDRESS" "127.0.0.1"
    echo "Se ha configurado CUADERNOPRO_BIND_ADDRESS=127.0.0.1 en .env."
elif [ "$bind_address" != "127.0.0.1" ] && [ "$bind_address" != "localhost" ]; then
    echo "ERROR: Para usar el proxy, configura CUADERNOPRO_BIND_ADDRESS=127.0.0.1 en .env." >&2
    echo "Asi Streamlit no queda publicado directamente en interfaces externas." >&2
    exit 1
fi

comprobar_docker
detectar_comando_compose
crear_runtime
mkdir -p runtime/caddy/data runtime/caddy/config

"${COMPOSE_CMD[@]}" --profile proxy up -d --build

echo "Proxy de CuadernoPro iniciado."
echo "Accede desde: https://${dominio}"
