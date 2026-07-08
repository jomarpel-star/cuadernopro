#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/scripts/installer/common.sh"

crear_runtime

if [ ! -f runtime/cuadernopro.db ]; then
    echo "No existe runtime/cuadernopro.db. No se ha creado backup."
    exit 0
fi

DESTINO="runtime/backups/manual_$(date +%F_%H%M%S).db"
cp -p runtime/cuadernopro.db "$DESTINO"

echo "Backup manual creado: $DESTINO"
