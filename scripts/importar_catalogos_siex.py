#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))

from services.catalogos_siex_importer import (
    diagnosticar_catalogos_siex,
    importar_catalogos_siex_desde_zip,
)


def main():

    parser = argparse.ArgumentParser(
        description="Importa catálogos SIEX desde un ZIP oficial en Excel."
    )
    parser.add_argument(
        "ruta_zip",
        help="Ruta al ZIP de catálogos SIEX.",
    )
    parser.add_argument(
        "--db",
        dest="ruta_db",
        help=(
            "Ruta de la base SQLite destino. Si se omite, se usa "
            "CUADERNOPRO_DB_PATH. No se usa cuadernopro.db por defecto."
        ),
    )
    args = parser.parse_args()
    ruta_zip = Path(args.ruta_zip).expanduser()
    ruta_db = args.ruta_db or os.getenv("CUADERNOPRO_DB_PATH")

    if not ruta_zip.exists():

        print(f"No existe el archivo: {ruta_zip}", file=sys.stderr)
        return 1

    if not ruta_db:

        print(
            "Indica la base destino con --db o CUADERNOPRO_DB_PATH. "
            "No se importa sobre cuadernopro.db por defecto.",
            file=sys.stderr,
        )
        return 1

    resumen = importar_catalogos_siex_desde_zip(ruta_zip, ruta_db=ruta_db)
    diagnostico = diagnosticar_catalogos_siex(ruta_db=ruta_db)

    print(f"ZIP: {resumen['ruta_zip']}")
    print(f"Base: {ruta_db}")
    print("Catálogos importados:")

    for catalogo in resumen["catalogos"]:

        print(
            "- {codigo}: {items} items ({archivo})".format(
                codigo=catalogo["codigo_catalogo"],
                items=catalogo["items"],
                archivo=catalogo["archivo_origen"],
            )
        )

    print(f"Total catálogos: {resumen['total_catalogos']}")
    print(f"Total items: {resumen['total_items']}")
    print(f"Archivos ignorados: {len(resumen['ignorados'])}")
    print(f"Duración: {resumen['duracion_segundos']} s")

    if resumen["ignorados"]:

        print("Ignorados:")

        for ignorado in resumen["ignorados"]:

            print(f"- {ignorado['archivo']}: {ignorado['motivo']}")

    if resumen["errores"]:

        print("Errores:")

        for error in resumen["errores"]:

            print(f"- {error['archivo']}: {error['error']}")

        return 2

    print(f"Diagnóstico: {diagnostico['estado']}")

    for error in diagnostico["errores"]:

        print(f"- ERROR: {error}")

    for aviso in diagnostico["advertencias"]:

        print(f"- Aviso: {aviso}")

    if not resumen["catalogos"]:

        print("No se importó ningún catálogo.", file=sys.stderr)
        return 2

    if not diagnostico["ok"]:

        return 2

    print("Importación completada sin errores bloqueantes.")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
