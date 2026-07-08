#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/scripts/installer/common.sh"

echo "Actualizacion de CuadernoPro"
echo "============================"

comprobar_docker
detectar_comando_compose
cargar_env
crear_runtime

if [ -f runtime/cuadernopro.db ]; then
    DESTINO="runtime/backups/antes_update_$(date +%F_%H%M%S).db"
    cp -p runtime/cuadernopro.db "$DESTINO"
    echo "Backup previo creado: $DESTINO"
else
    echo "No existe runtime/cuadernopro.db. Se continua sin backup previo."
fi

"${COMPOSE_CMD[@]}" up -d --build --remove-orphans
"${COMPOSE_CMD[@]}" ps

mostrar_url
