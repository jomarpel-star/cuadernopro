#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/scripts/installer/common.sh"

echo "Instalador de CuadernoPro"
echo "========================="

comprobar_docker
detectar_comando_compose
cargar_env
crear_runtime

PUERTO="$(obtener_puerto)"

if puerto_en_uso "$PUERTO"; then
    echo "AVISO: El puerto $PUERTO parece estar en uso. Edita .env y cambia CUADERNOPRO_PORT."
else
    ESTADO_PUERTO=$?
    if [ "$ESTADO_PUERTO" -eq 2 ]; then
        echo "AVISO: No se pudo comprobar si el puerto $PUERTO esta en uso."
    fi
fi

"${COMPOSE_CMD[@]}" up -d --build

echo
echo "CuadernoPro instalado correctamente."
mostrar_url
