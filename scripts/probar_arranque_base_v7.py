#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
DB_PRUEBA = APP_ROOT / "runtime" / "v7" / "prueba_arranque_v7.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.db import crear_tablas  # noqa: E402


LEGACY_PROHIBIDAS = {
    "cultivos": {"parcela_id"},
    "fertilizaciones": {"cultivo"},
    "practicas_culturales": {"cultivo"},
    "cosecha": {"cultivo", "cliente", "nif_cliente", "kg"},
    "movimientos_economicos": {"tercero", "nif_tercero", "cultivo"},
    "tratamientos": {
        "fecha",
        "cultivo",
        "producto",
        "aplicador",
        "equipo",
        "equipo_id",
        "maquinaria_id",
        "problema",
    },
}


def _backup_si_existe(ruta):

    if not ruta.exists():

        return None

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = ruta.with_name(f"{ruta.name}.bak-{marca}")
    contador = 1

    while backup.exists():

        backup = ruta.with_name(f"{ruta.name}.bak-{marca}-{contador}")
        contador += 1

    shutil.copy2(ruta, backup)
    ruta.unlink()
    return backup


def _conectar(ruta):

    conn = sqlite3.connect(ruta)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _columnas(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _validar_base_v7(ruta):

    with _conectar(ruta) as conn:

        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])

        if user_version != 7:

            raise AssertionError(
                f"PRAGMA user_version={user_version}; esperado 7"
            )

        legacy_detectadas = []

        for tabla, columnas_prohibidas in LEGACY_PROHIBIDAS.items():

            detectadas = sorted(columnas_prohibidas & _columnas(conn, tabla))

            if detectadas:

                legacy_detectadas.extend(
                    f"{tabla}.{columna}"
                    for columna in detectadas
                )

        if legacy_detectadas:

            raise AssertionError(
                "Columnas legacy detectadas: "
                + ", ".join(legacy_detectadas)
            )

    diagnostico = subprocess.run(
        [
            sys.executable,
            str(APP_ROOT / "scripts" / "diagnostico_schema_v7.py"),
            str(ruta),
        ],
        cwd=APP_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    if diagnostico.returncode != 0:

        print(diagnostico.stdout)
        print(diagnostico.stderr, file=sys.stderr)
        raise AssertionError(
            "El diagnostico v7 devolvio codigo "
            f"{diagnostico.returncode}"
        )

    return diagnostico.stdout


def main():

    DB_PRUEBA.parent.mkdir(parents=True, exist_ok=True)
    backup = _backup_si_existe(DB_PRUEBA)

    crear_tablas(DB_PRUEBA)
    diagnostico = _validar_base_v7(DB_PRUEBA)

    print("Prueba arranque base v7")
    print("=======================")
    print(f"Ruta prueba: {DB_PRUEBA}")

    if backup:

        print(f"Backup previo: {backup}")

    print("Inicializacion real: core.db.crear_tablas")
    print("PRAGMA user_version: 7")
    print("Columnas legacy detectadas: ninguna")
    print("Diagnostico schema v7: OK")
    print("Resumen diagnostico:")

    for linea in diagnostico.splitlines():

        if linea.startswith("Numero de tablas:") or linea.startswith("Resultado:"):

            print(f"- {linea}")

    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
