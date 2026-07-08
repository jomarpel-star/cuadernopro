#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/scripts/installer/common.sh"

comprobar_docker
detectar_comando_compose
cargar_env
crear_runtime

"${COMPOSE_CMD[@]}" up -d

echo "CuadernoPro iniciado."
mostrar_url
