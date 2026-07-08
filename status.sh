#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/scripts/installer/common.sh"

comprobar_docker
detectar_comando_compose

"${COMPOSE_CMD[@]}" ps

echo
echo "Datos locales:"

if [ -f runtime/cuadernopro.db ]; then
    echo "Base de datos: runtime/cuadernopro.db"
    echo "Tamano: $(ls -lh runtime/cuadernopro.db | awk '{print $5}')"
else
    echo "Base de datos: no existe runtime/cuadernopro.db"
fi

echo
echo "Ultimos backups:"
if [ -d runtime/backups ]; then
    ls -lh runtime/backups | tail
else
    echo "No existe runtime/backups"
fi
