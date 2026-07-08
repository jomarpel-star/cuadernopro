#!/usr/bin/env python3
from pathlib import Path
import os
import sqlite3
import sys
import tempfile
import traceback

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
DB_ARBOL = APP_ROOT / "runtime" / "v7" / "prueba_cultivos_arboles_v7.db"
EXPORTS_DIR = APP_ROOT / "runtime" / "v7" / "exports_cultivos_arboles"
DOCS_DIR = APP_ROOT / "runtime" / "v7" / "documentos_cultivos_arboles"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_ARBOL)

from core.db import crear_tablas  # noqa: E402
from modules.cultivos import (  # noqa: E402
    calcular_numero_arboles,
    parsear_marco_plantacion,
)
from modules.informes import cargar_datos_informes  # noqa: E402
import modules.revision_siex as revision_siex  # noqa: E402
import services.cuadernopro_pdf as cuadernopro_pdf  # noqa: E402
import services.exportacion_siex as exportacion_siex  # noqa: E402


def _conectar():

    conn = sqlite3.connect(DB_ARBOL)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _leer(sql, params=None):

    with _conectar() as conn:

        return pd.read_sql_query(sql, conn, params=params or ())


def _limpiar_base():

    DB_ARBOL.parent.mkdir(parents=True, exist_ok=True)

    for ruta in (
        DB_ARBOL,
        DB_ARBOL.with_name(f"{DB_ARBOL.name}-wal"),
        DB_ARBOL.with_name(f"{DB_ARBOL.name}-shm"),
    ):

        if ruta.exists():

            ruta.unlink()

    crear_tablas(DB_ARBOL)


def _columnas(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _assert(condicion, mensaje):

    if not condicion:

        raise AssertionError(mensaje)


def _assert_igual(actual, esperado, etiqueta):

    if actual != esperado:

        raise AssertionError(
            f"{etiqueta}: esperado {esperado!r}, obtenido {actual!r}"
        )


def _assert_float(actual, esperado, etiqueta):

    if abs(float(actual or 0) - float(esperado)) > 0.0001:

        raise AssertionError(
            f"{etiqueta}: esperado {esperado!r}, obtenido {actual!r}"
        )


def _insertar_base_minima(conn):

    ahora = "2026-07-03T00:00:00"
    conn.execute(
        """
        INSERT INTO explotacion
        (nombre_explotacion, titular, nif, direccion, municipio, provincia,
         codigo_postal, telefono, email, identificador_oficial,
         tipo_identificador_oficial, registro_autonomico, tipo_explotacion,
         orientacion_productiva, fecha_alta, agricultor_activo,
         joven_agricultor, responsable, asesor, numero_asesor,
         observaciones, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Finca arboles v7",
            "Titular arboles v7",
            "00000000A",
            "Camino Arboles 1",
            "Jumilla",
            "Murcia",
            "30520",
            "600000000",
            "arboles@example.com",
            "REGEPA-ARB-V7",
            "REGEPA",
            "REG-AUT-ARB-V7",
            "Agraria",
            "Frutos secos",
            "2026-01-01",
            1,
            0,
            "Responsable arboles",
            "Asesor arboles",
            "ASE-ARB-V7",
            "Explotacion base arboles",
            ahora,
            ahora,
        ),
    )
    campana_id = conn.execute(
        """
        INSERT INTO campanas
        (nombre, fecha_inicio, fecha_fin, activa, estado, observaciones,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            "2026",
            "2026-01-01",
            "2026-12-31",
            1,
            "abierta",
            "Campana arboles",
            ahora,
            ahora,
        ),
    ).lastrowid
    parcela_id = conn.execute(
        """
        INSERT INTO parcelas
        (nombre, provincia_sigpac, municipio_sigpac, agregado_sigpac,
         zona_sigpac, poligono, parcela, recinto, superficie_sigpac,
         uso_sigpac, activa, observaciones, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Parcela almendro arboles",
            30,
            22,
            0,
            0,
            "7",
            "45",
            "2",
            2.5,
            "FS",
            1,
            "Parcela para calculo de arboles",
            ahora,
            ahora,
        ),
    ).lastrowid
    numero_arboles = calcular_numero_arboles(2.5, "7x7")
    cultivo_id = conn.execute(
        """
        INSERT INTO cultivos
        (campana_id, nombre, variedad, codigo_siex, superficie,
         ano_plantacion, marco_plantacion, numero_arboles, activo,
         observaciones, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            "Almendro 2018",
            "Guara",
            "104",
            2.5,
            2018,
            "7x7",
            numero_arboles,
            1,
            "Cultivo con marco de plantacion",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO cultivo_parcelas
        (cultivo_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (cultivo_id, parcela_id, 2.5, ahora, ahora),
    )
    conn.commit()
    return {
        "campana_id": int(campana_id),
        "parcela_id": int(parcela_id),
        "cultivo_id": int(cultivo_id),
    }


def _validar_esquema():

    with _conectar() as conn:

        columnas = _columnas(conn, "cultivos")

    _assert(
        "marco_plantacion" in columnas,
        "No existe cultivos.marco_plantacion",
    )
    _assert(
        "numero_arboles" in columnas,
        "No existe cultivos.numero_arboles",
    )
    return "columnas marco_plantacion y numero_arboles presentes"


def _validar_parseo():

    validos = {
        "7x7": (7.0, 7.0),
        "7X7": (7.0, 7.0),
        "7 x 7": (7.0, 7.0),
        "7×7": (7.0, 7.0),
        "7*7": (7.0, 7.0),
        " 7x7 ": (7.0, 7.0),
        "6x5": (6.0, 5.0),
        "6 x 5": (6.0, 5.0),
        "6X5": (6.0, 5.0),
        "6*5": (6.0, 5.0),
        "6,5x5": (6.5, 5.0),
        "7.5x6": (7.5, 6.0),
    }

    for texto, esperado in validos.items():

        _assert_igual(parsear_marco_plantacion(texto), esperado, texto)

    invalidos = ["", "abc", "7", "7x", "x7", "7x0", "0x7", "-7x7"]

    for texto in invalidos:

        _assert_igual(parsear_marco_plantacion(texto), None, texto)

    return f"{len(validos)} marcos validos y {len(invalidos)} invalidos OK"


def _validar_calculo():

    casos = [
        (1, "5x5", 400),
        (1, "7x7", 204),
        (2.5, "7x7", 510),
        (3, "6x5", 1000),
    ]

    for superficie, marco, esperado in casos:

        _assert_igual(
            calcular_numero_arboles(superficie, marco),
            esperado,
            f"{superficie} ha {marco}",
        )

    _assert_igual(calcular_numero_arboles(None, "7x7"), None, "sin superficie")
    _assert_igual(calcular_numero_arboles(2.5, "abc"), None, "marco invalido")
    return "calculos 400, 204, 510 y 1000 OK"


def _validar_ruta_formulario():

    casos = {
        "7x7": 510,
        "6,5x5": 769,
        "7×7": 510,
    }

    for marco, esperado in casos.items():

        calculado = calcular_numero_arboles(2.5, marco)
        aviso_invalido = calculado is None and str(marco or "").strip() != ""
        _assert(
            not aviso_invalido,
            f"El formulario marcaria {marco!r} como marco invalido",
        )
        _assert_igual(calculado, esperado, f"calculo formulario {marco}")

    return "ruta de formulario acepta 7x7, 6,5x5 y 7x7 unicode"


def _texto_elemento(elemento):

    for atributo in ("value", "body", "message"):

        valor = getattr(elemento, atributo, None)

        if valor:

            return str(valor)

    return str(elemento)


def _crear_app_cultivos_temporal():

    contenido = f"""
from pathlib import Path
import os
import sys

APP_ROOT = Path({str(APP_ROOT)!r})
DB_ARBOL = Path({str(DB_ARBOL)!r})
os.environ["CUADERNOPRO_DB_PATH"] = str(DB_ARBOL)

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import modules.cultivos as modulo

modulo.render()
"""
    temporal = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".py",
        prefix="cultivos_arboles_app_",
        dir=DB_ARBOL.parent,
        delete=False,
    )

    with temporal:

        temporal.write(contenido)

    return Path(temporal.name)


def _widget_por_etiqueta(widgets, etiqueta):

    for widget in widgets:

        if getattr(widget, "label", "") == etiqueta:

            return widget

    raise AssertionError(f"No se encuentra widget {etiqueta!r}")


def _validar_app_test_formulario():

    from streamlit.testing.v1 import AppTest

    app_temporal = _crear_app_cultivos_temporal()
    casos = {
        "7x7": 510,
        "6x5": 833,
        "6,5x5": 769,
        "7×7": 510,
    }

    try:

        prueba = AppTest.from_file(app_temporal, default_timeout=10)
        prueba.run(timeout=10)
        _widget_por_etiqueta(
            prueba.radio,
            "Opciones de cultivos",
        ).set_value("➕ Nuevo cultivo")
        prueba.run(timeout=10)

        for marco, esperado in casos.items():

            _widget_por_etiqueta(
                prueba.number_input,
                "Superficie del cultivo (ha)",
            ).set_value(2.5)
            _widget_por_etiqueta(
                prueba.text_input,
                "Marco de plantación",
            ).set_value(marco)
            prueba.run(timeout=10)

            avisos = [
                _texto_elemento(aviso)
                for aviso in getattr(prueba, "warning", [])
            ]
            contenido_avisos = " ".join(avisos)
            _assert(
                "Marco de plantación no válido" not in contenido_avisos,
                f"AppTest muestra aviso invalido para {marco!r}",
            )
            infos = [
                _texto_elemento(info)
                for info in getattr(prueba, "info", [])
            ]
            contenido_infos = " ".join(infos)
            _assert(
                f"Árboles estimados: {esperado}" in contenido_infos,
                f"AppTest no muestra calculo {esperado} para {marco!r}",
            )

        return "AppTest Cultivos acepta 7x7, 6x5, 6,5x5 y 7x7 unicode"

    finally:

        try:

            app_temporal.unlink()

        except OSError:

            pass


def _validar_persistencia(ctx):

    with _conectar() as conn:

        fila = dict(
            conn.execute(
                """
                SELECT superficie, marco_plantacion, numero_arboles
                FROM cultivos
                WHERE id=?
                """,
                (ctx["cultivo_id"],),
            ).fetchone()
        )
        _assert_float(fila["superficie"], 2.5, "superficie inicial")
        _assert_igual(fila["marco_plantacion"], "7x7", "marco inicial")
        _assert_igual(int(fila["numero_arboles"]), 510, "arboles iniciales")

        recalculado = calcular_numero_arboles(2.5, "6x5")
        conn.execute(
            """
            UPDATE cultivos
            SET marco_plantacion=?, numero_arboles=?
            WHERE id=?
            """,
            ("6x5", recalculado, ctx["cultivo_id"]),
        )
        conn.commit()
        actualizada = dict(
            conn.execute(
                """
                SELECT marco_plantacion, numero_arboles
                FROM cultivos
                WHERE id=?
                """,
                (ctx["cultivo_id"],),
            ).fetchone()
        )

    _assert_igual(actualizada["marco_plantacion"], "6x5", "marco editado")
    _assert_igual(int(actualizada["numero_arboles"]), 833, "arboles editados")
    return "persistencia y recalculo 6x5 OK"


def _validar_informes(ctx):

    with _conectar() as conn:

        informes = cargar_datos_informes(conn, ctx["campana_id"])

    cultivos = informes.get("cultivos", pd.DataFrame())

    if cultivos.empty:

        raise AssertionError("Informes no devuelven cultivos")

    contenido = " ".join(str(valor) for valor in cultivos.stack().tolist())

    for texto in ["Almendro 2018", "6x5", "833"]:

        if texto not in contenido:

            raise AssertionError(f"Informes sin texto esperado: {texto}")

    return "informes muestran marco y numero de arboles"


def _validar_revision_siex(ctx):

    with _conectar() as conn:

        revision, registros = revision_siex._generar_revision(
            conn,
            ctx["campana_id"],
        )

    if registros <= 0:

        raise AssertionError("Revision SIEX no reviso registros")

    return f"revision SIEX OK ({registros} registros, {len(revision)} avisos)"


def _validar_excel_siex(ctx):

    original_conectar = exportacion_siex.conectar
    exportacion_siex.conectar = _conectar

    try:

        contenido, nombre = exportacion_siex.generar_excel_asistido_siex(
            campana_id=ctx["campana_id"],
        )

    finally:

        exportacion_siex.conectar = original_conectar

    with _conectar() as conn:

        cultivos_siex = exportacion_siex.obtener_dataframe_cultivos(
            conn,
            ctx["campana_id"],
        )

    if len(contenido) <= 1024 or not nombre.endswith(".xlsx"):

        raise AssertionError("Excel SIEX vacio o nombre invalido")

    _assert_igual(len(cultivos_siex), 1, "filas cultivos SIEX")
    _assert(
        "marco_plantacion" not in cultivos_siex.columns,
        "Excel SIEX no debe exponer marco_plantacion como campo oficial",
    )
    _assert(
        "numero_arboles" not in cultivos_siex.columns,
        "Excel SIEX no debe exponer numero_arboles como campo oficial",
    )
    return f"excel SIEX OK ({len(contenido)} bytes)"


def _validar_pdf(ctx):

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    original_conectar = cuadernopro_pdf.conectar
    original_leer = cuadernopro_pdf.leer
    original_exports = cuadernopro_pdf.EXPORTS_DIR
    original_docs = cuadernopro_pdf.DOCS_DIR
    cuadernopro_pdf.conectar = _conectar
    cuadernopro_pdf.leer = _leer
    cuadernopro_pdf.EXPORTS_DIR = EXPORTS_DIR
    cuadernopro_pdf.DOCS_DIR = DOCS_DIR

    try:

        ruta_pdf = Path(cuadernopro_pdf.generar_cuadernopro_pdf(ctx["campana_id"]))

    finally:

        cuadernopro_pdf.conectar = original_conectar
        cuadernopro_pdf.leer = original_leer
        cuadernopro_pdf.EXPORTS_DIR = original_exports
        cuadernopro_pdf.DOCS_DIR = original_docs

    if not ruta_pdf.exists() or ruta_pdf.stat().st_size <= 0:

        raise AssertionError("PDF oficial sin contenido")

    return f"PDF OK ({ruta_pdf.stat().st_size} bytes)"


def _registrar(resultados, nombre, funcion):

    try:

        resultados.append((nombre, "OK", funcion()))

    except Exception:

        resultados.append((nombre, "FALLO", traceback.format_exc()))


def main():

    resultados = []

    try:

        _limpiar_base()

        with _conectar() as conn:

            ctx = _insertar_base_minima(conn)

    except Exception:

        print("Prueba cultivos arboles v7")
        print("==========================")
        print(f"Base usada: {DB_ARBOL}")
        print("Preparacion base: FALLO")
        print(traceback.format_exc())
        return 1

    pruebas = [
        ("Esquema", _validar_esquema),
        ("Parseo marco", _validar_parseo),
        ("Calculo arboles", _validar_calculo),
        ("Ruta formulario", _validar_ruta_formulario),
        ("AppTest formulario", _validar_app_test_formulario),
        ("Persistencia", lambda: _validar_persistencia(ctx)),
        ("Informes", lambda: _validar_informes(ctx)),
        ("Revision SIEX", lambda: _validar_revision_siex(ctx)),
        ("Excel SIEX", lambda: _validar_excel_siex(ctx)),
        ("PDF oficial", lambda: _validar_pdf(ctx)),
    ]

    for nombre, funcion in pruebas:

        _registrar(resultados, nombre, funcion)

    print("Prueba cultivos arboles v7")
    print("==========================")
    print(f"Base usada: {DB_ARBOL}")
    print("")
    print("| Prueba | Resultado | Observaciones |")
    print("| --- | --- | --- |")

    for nombre, estado, detalle in resultados:

        primera_linea = detalle.strip().splitlines()[0] if detalle else ""
        print(f"| {nombre} | {estado} | {primera_linea} |")

    fallos = [fila for fila in resultados if fila[1] != "OK"]

    if fallos:

        print("")
        print("Errores")

        for nombre, _, detalle in fallos:

            print(f"## {nombre}")
            print(detalle)

        print("Resultado: FALLO")
        return 1

    print("")
    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
