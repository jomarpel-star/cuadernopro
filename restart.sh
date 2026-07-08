#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/scripts/installer/common.sh"

comprobar_docker
detectar_comando_compose
cargar_env

"${COMPOSE_CMD[@]}" restart
"${COMPOSE_CMD[@]}" ps

mostrar_url
