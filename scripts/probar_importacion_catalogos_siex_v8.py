#!/usr/bin/env python3
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import os
import sqlite3
import subprocess
import sys
import tempfile
import traceback

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
DB_CATALOGOS = APP_ROOT / "runtime" / "v8" / "prueba_catalogos_siex_v8.db"
ZIP_SINTETICO = APP_ROOT / "runtime" / "v8" / "catalogos_siex_sintetico.zip"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_CATALOGOS)

from core.db import crear_tablas  # noqa: E402
from services.catalogos_siex_importer import (  # noqa: E402
    diagnosticar_catalogos_siex,
    importar_catalogos_siex_desde_zip,
    resumen_catalogos_siex,
)


def _assert(condicion, mensaje):

    if not condicion:

        raise AssertionError(mensaje)


def _conectar():

    conn = sqlite3.connect(DB_CATALOGOS)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _limpiar_runtime():

    DB_CATALOGOS.parent.mkdir(parents=True, exist_ok=True)

    for ruta in (
        DB_CATALOGOS,
        DB_CATALOGOS.with_name(f"{DB_CATALOGOS.name}-wal"),
        DB_CATALOGOS.with_name(f"{DB_CATALOGOS.name}-shm"),
        ZIP_SINTETICO,
    ):

        if ruta.exists():

            ruta.unlink()


def _excel_bytes(dataframe):

    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

        dataframe.to_excel(writer, index=False)

    return buffer.getvalue()


def _crear_zip_sintetico():

    cultivo = pd.DataFrame(
        [
            {
                "Código SIEX": "101",
                "Cultivo": "Almendro",
                "Fecha de alta": "2024-01-01",
                "Fecha de baja": "",
            },
            {
                "Código SIEX": "102",
                "Cultivo": "Olivo",
                "Fecha de alta": "2024-01-01",
                "Fecha de baja": "",
            },
        ]
    )
    actividad = pd.DataFrame(
        [
            {
                "Código SIEX": "A01",
                "Actividad agraria": "Producción",
                "Fecha de baja": "",
            },
            {
                "Código SIEX": "A02",
                "Actividad agraria": "Mantenimiento",
                "Fecha de baja": "2025-12-31",
            },
        ]
    )

    with ZipFile(ZIP_SINTETICO, "w") as zip_file:

        zip_file.writestr("Cultivo.xlsx", _excel_bytes(cultivo))
        zip_file.writestr("Actividad agraria.xlsx", _excel_bytes(actividad))
        zip_file.writestr("README.txt", "Archivo ignorado en la prueba.")


def _contar(tabla):

    with _conectar() as conn:

        return int(conn.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0])


def _validar_importacion_idempotente():

    resumen_1 = importar_catalogos_siex_desde_zip(
        ZIP_SINTETICO,
        ruta_db=DB_CATALOGOS,
    )
    _assert(resumen_1["total_catalogos"] == 2, "primera importacion catalogos")
    _assert(resumen_1["total_items"] == 4, "primera importacion items")
    _assert(len(resumen_1["ignorados"]) == 1, "archivo ignorado esperado")
    _assert(not resumen_1["errores"], f"errores: {resumen_1['errores']}")

    catalogos_1 = _contar("siex_catalogos")
    items_1 = _contar("siex_catalogos_items")

    resumen_2 = importar_catalogos_siex_desde_zip(
        ZIP_SINTETICO,
        ruta_db=DB_CATALOGOS,
    )
    _assert(resumen_2["total_catalogos"] == 2, "segunda importacion catalogos")
    _assert(resumen_2["total_items"] == 4, "segunda importacion items")
    _assert(_contar("siex_catalogos") == catalogos_1, "duplica catalogos")
    _assert(_contar("siex_catalogos_items") == items_1, "duplica items")

    return "servicio importa dos veces sin duplicar"


def _validar_cli():

    resultado = subprocess.run(
        [
            sys.executable,
            "scripts/importar_catalogos_siex.py",
            str(ZIP_SINTETICO),
            "--db",
            str(DB_CATALOGOS),
        ],
        cwd=APP_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    if resultado.returncode != 0:

        raise AssertionError(resultado.stdout)

    _assert(_contar("siex_catalogos") == 2, "CLI duplica catalogos")
    _assert(_contar("siex_catalogos_items") == 4, "CLI duplica items")
    return "CLI importa con --db sin duplicar"


def _validar_resumen_diagnostico():

    resumen = resumen_catalogos_siex(ruta_db=DB_CATALOGOS)
    diagnostico = diagnosticar_catalogos_siex(ruta_db=DB_CATALOGOS)

    _assert(resumen["total_catalogos"] == 2, "resumen catalogos")
    _assert(resumen["total_items"] == 4, "resumen items")
    _assert(diagnostico["ok"], f"diagnostico no OK: {diagnostico}")
    _assert(
        "cultivo" in diagnostico["catalogos_presentes"],
        "falta catalogo cultivo",
    )
    return f"diagnostico {diagnostico['estado']}"


def _validar_render_modulo():

    from streamlit.testing.v1 import AppTest

    contenido = f"""
from pathlib import Path
import os
import sys

APP_ROOT = Path({str(APP_ROOT)!r})
DB_CATALOGOS = Path({str(DB_CATALOGOS)!r})
os.environ["CUADERNOPRO_DB_PATH"] = str(DB_CATALOGOS)

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import modules.catalogos_siex as modulo

modulo.render()
"""
    temporal = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".py",
        prefix="catalogos_siex_v8_",
        dir=DB_CATALOGOS.parent,
        delete=False,
    )

    try:

        with temporal:

            temporal.write(contenido)

        prueba = AppTest.from_file(Path(temporal.name), default_timeout=10)
        prueba.run(timeout=10)
        excepciones = list(prueba.exception)

        if excepciones:

            raise AssertionError("\n".join(str(error) for error in excepciones))

    finally:

        try:

            Path(temporal.name).unlink()

        except OSError:

            pass

    return "modulo Catálogos SIEX renderiza"


def _validar_revision_exportacion():

    import modules.revision_siex as revision_siex
    import services.exportacion_siex as exportacion_siex

    with _conectar() as conn:

        revision, registros = revision_siex._generar_revision(conn, None)

    contenido, nombre = exportacion_siex.generar_excel_asistido_siex(
        campana_id=None,
        revision=revision,
    )
    _assert(registros >= 0, "revision sin registros")
    _assert(len(contenido) > 0, "excel SIEX vacio")
    _assert(nombre.endswith(".xlsx"), "nombre Excel no xlsx")
    return "revision SIEX y Excel asistido no rompen"


def main():

    print("Prueba importacion catalogos SIEX v8")
    print("====================================")
    print(f"Base: {DB_CATALOGOS}")

    pruebas = [
        ("Preparar base limpia", lambda: (crear_tablas(DB_CATALOGOS), "OK")[1]),
        ("Crear ZIP sintetico", lambda: (_crear_zip_sintetico(), "OK")[1]),
        ("Importacion idempotente", _validar_importacion_idempotente),
        ("CLI", _validar_cli),
        ("Resumen y diagnostico", _validar_resumen_diagnostico),
        ("Render modulo", _validar_render_modulo),
        ("Revision/exportacion SIEX", _validar_revision_exportacion),
    ]

    try:

        _limpiar_runtime()

        for nombre, funcion in pruebas:

            resultado = funcion()
            print(f"- {nombre}: OK ({resultado})")

    except Exception:

        print("Resultado: FALLO")
        print(traceback.format_exc())
        return 1

    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
