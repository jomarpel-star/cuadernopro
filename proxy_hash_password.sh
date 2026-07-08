#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker no esta instalado o no esta en PATH." >&2
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker esta instalado, pero no responde." >&2
    echo "Revisa que el servicio Docker este iniciado y que tu usuario tenga permisos." >&2
    exit 1
fi

read -r -p "Usuario para acceso exterior [admin]: " usuario
usuario="${usuario:-admin}"

if [ -z "$usuario" ]; then
    echo "ERROR: El usuario no puede estar vacio." >&2
    exit 1
fi

if printf '%s' "$usuario" | grep -q '[[:space:]]'; then
    echo "ERROR: El usuario no debe contener espacios." >&2
    exit 1
fi

read -r -s -p "Contrasena: " password
printf '\n'
read -r -s -p "Repite la contrasena: " password_confirmacion
printf '\n'

if [ -z "$password" ]; then
    echo "ERROR: La contrasena no puede estar vacia." >&2
    exit 1
fi

if [ "$password" != "$password_confirmacion" ]; then
    echo "ERROR: Las contrasenas no coinciden." >&2
    exit 1
fi

hash="$(
    docker run --rm caddy:2 caddy hash-password --plaintext "$password"
)"

printf '\nHash generado:\n%s\n\n' "$hash"

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

if [ -f .env ]; then
    actualizar_env "CUADERNOPRO_PROXY_USER" "$usuario"
    actualizar_env "CUADERNOPRO_PROXY_PASSWORD_HASH" "$hash"
    echo ".env actualizado con CUADERNOPRO_PROXY_USER y CUADERNOPRO_PROXY_PASSWORD_HASH."
else
    echo "No existe .env. Copia .env.example a .env y anade estos valores:"
    echo "CUADERNOPRO_PROXY_USER=$usuario"
    echo "CUADERNOPRO_PROXY_PASSWORD_HASH=$hash"
fi
