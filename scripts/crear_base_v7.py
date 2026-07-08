#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import argparse
import shutil
import sys


APP_ROOT = Path(__file__).resolve().parents[1]

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.schema_v7 import crear_base_v7  # noqa: E402


def _resolver_ruta(ruta):

    ruta = Path(ruta).expanduser()

    if not ruta.is_absolute():

        ruta = APP_ROOT / ruta

    return ruta.resolve()


def _validar_ruta_segura(ruta):

    if ruta.name == "cuadernopro.db":

        raise ValueError(
            "Por seguridad no se permite crear v7 sobre cuadernopro.db"
        )


def _ruta_backup(ruta):

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidata = ruta.with_name(f"{ruta.name}.bak-{marca}")
    contador = 1

    while candidata.exists():

        candidata = ruta.with_name(f"{ruta.name}.bak-{marca}-{contador}")
        contador += 1

    return candidata


def _preparar_destino(ruta):

    ruta.parent.mkdir(parents=True, exist_ok=True)

    if not ruta.exists():

        return None

    backup = _ruta_backup(ruta)
    shutil.copy2(ruta, backup)
    ruta.unlink()
    return backup


def _imprimir_resumen(ruta, backup, resultado):

    print("Creacion base v7")
    print("================")
    print(f"Ruta creada: {ruta}")

    if backup:

        print(f"Backup previo: {backup}")

    print(f"Version esperada: {resultado['schema_version']}")
    print(f"PRAGMA user_version: {resultado['user_version']}")
    print(f"Numero de tablas: {resultado['table_count']}")
    print(
        "Tablas principales: "
        + ", ".join(resultado["principal_tables"])
    )

    if resultado["legacy_columns"]:

        print(
            "Columnas legacy detectadas: "
            + ", ".join(resultado["legacy_columns"])
        )

    else:

        print("Columnas legacy detectadas: ninguna")

    if resultado["ok"]:

        print("Resultado: OK")

    else:

        print("Resultado: ERROR")

        for error in resultado["errors"]:

            print(f"- {error}")


def main():

    parser = argparse.ArgumentParser(
        description="Crea una base SQLite limpia con esquema CuadernoPro v7."
    )
    parser.add_argument(
        "ruta_db",
        help="Ruta de la base v7 de prueba a crear",
    )
    args = parser.parse_args()
    ruta = _resolver_ruta(args.ruta_db)

    try:

        _validar_ruta_segura(ruta)
        backup = _preparar_destino(ruta)
        resultado = crear_base_v7(ruta)
        _imprimir_resumen(ruta, backup, resultado)

    except Exception as error:

        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0 if resultado["ok"] else 1


if __name__ == "__main__":

    raise SystemExit(main())
