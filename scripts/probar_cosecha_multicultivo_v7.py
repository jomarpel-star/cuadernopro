#!/usr/bin/env python3
from pathlib import Path
import os
import sqlite3
import sys
import traceback

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
DB_MULTICULTIVO = APP_ROOT / "runtime" / "v7" / "prueba_cosecha_multicultivo_v7.db"
EXPORTS_DIR = APP_ROOT / "runtime" / "v7" / "exports_cosecha_multicultivo"
DOCS_DIR = APP_ROOT / "runtime" / "v7" / "documentos_cosecha_multicultivo"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_MULTICULTIVO)

from core.db import crear_tablas  # noqa: E402
from modules.cosecha import (  # noqa: E402
    _insertar_cosecha_compatible,
    _leer_cosechas_guardadas,
    _preparar_cosechas_presentacion,
)
from modules.informes import cargar_datos_informes  # noqa: E402
import modules.revision_siex as revision_siex  # noqa: E402
import services.cuadernopro_pdf as cuadernopro_pdf  # noqa: E402
import services.exportacion_siex as exportacion_siex  # noqa: E402


def _conectar():

    conn = sqlite3.connect(DB_MULTICULTIVO)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _leer(sql, params=None):

    with _conectar() as conn:

        return pd.read_sql_query(sql, conn, params=params or ())


def _limpiar_base():

    DB_MULTICULTIVO.parent.mkdir(parents=True, exist_ok=True)

    for ruta in (
        DB_MULTICULTIVO,
        DB_MULTICULTIVO.with_name(f"{DB_MULTICULTIVO.name}-wal"),
        DB_MULTICULTIVO.with_name(f"{DB_MULTICULTIVO.name}-shm"),
    ):

        if ruta.exists():

            ruta.unlink()

    crear_tablas(DB_MULTICULTIVO)


def _insertar_datos_base(conn):

    ahora = "2026-07-03T00:00:00"
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
            "Campana multicultivo",
            ahora,
            ahora,
        ),
    ).lastrowid
    cliente_id = conn.execute(
        """
        INSERT INTO clientes
        (nombre, nif, telefono, email, direccion, poblacion, provincia,
         codigo_postal, observaciones, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Cooperativa Multicultivo",
            "B30000000",
            "600000000",
            "coop@example.com",
            "Camino de prueba",
            "Jumilla",
            "Murcia",
            "30520",
            "Cliente de cosecha multicultivo",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
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
            "Finca Multicultivo",
            "Titular Multicultivo",
            "00000000T",
            "Camino agricola 1",
            "Jumilla",
            "Murcia",
            "30520",
            "600000001",
            "titular@example.com",
            "REGEPA-MULTI-001",
            "REGEPA",
            "REG-MULTI-001",
            "Agricola",
            "Almendro",
            "2026-01-01",
            1,
            0,
            "Titular Multicultivo",
            "Asesor Multicultivo",
            "ASE-001",
            "Explotacion de prueba",
            ahora,
            ahora,
        ),
    )

    parcelas = []

    for indice, superficie in enumerate([1.1, 1.2, 1.3, 1.4], start=1):

        parcela_id = conn.execute(
            """
            INSERT INTO parcelas
            (nombre, provincia_sigpac, municipio_sigpac, agregado_sigpac,
             zona_sigpac, poligono, parcela, recinto, superficie_sigpac,
             uso_sigpac, activa, observaciones, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                f"Parcela almendro {indice}",
                30,
                22,
                0,
                0,
                str(10 + indice),
                str(100 + indice),
                str(indice),
                superficie,
                "FS",
                1,
                "Parcela de prueba multicultivo",
                ahora,
                ahora,
            ),
        ).lastrowid
        parcelas.append((parcela_id, superficie))

    cultivos = []

    datos_cultivos = [
        (2010, 2.3, "7x7", 469),
        (2018, 1.3, "6x5", 433),
        (2022, 1.4, "6x5", 467),
    ]

    for ano, superficie, marco_plantacion, numero_arboles in datos_cultivos:

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
                "Almendro",
                "Comuna",
                f"ALM-{ano}",
                superficie,
                ano,
                marco_plantacion,
                numero_arboles,
                1,
                f"Almendro plantacion {ano}",
                ahora,
                ahora,
            ),
        ).lastrowid
        cultivos.append(cultivo_id)

    relaciones = [
        (cultivos[0], parcelas[0]),
        (cultivos[0], parcelas[1]),
        (cultivos[1], parcelas[2]),
        (cultivos[2], parcelas[3]),
    ]

    for cultivo_id, (parcela_id, superficie) in relaciones:

        conn.execute(
            """
            INSERT INTO cultivo_parcelas
            (cultivo_id, parcela_id, superficie, created_at, updated_at)
            VALUES (?,?,?,?,?)
            """,
            (cultivo_id, parcela_id, superficie, ahora, ahora),
        )

    detalles = [
        {
            "cultivo_id": cultivo_id,
            "parcela_id": parcela_id,
            "superficie": superficie,
        }
        for cultivo_id, (parcela_id, superficie) in relaciones
    ]
    cosecha_id = _insertar_cosecha_compatible(
        conn,
        {
            "campana_id": campana_id,
            "cultivo_id": cultivos[0],
            "fecha": "2026-09-15",
            "cantidad": 5200.0,
            "unidad": "kg",
            "destino": "Cooperativa",
            "cliente_id": cliente_id,
            "observaciones": "Cosecha multicultivo por plantacion",
        },
        parcelas_ids=[parcela_id for parcela_id, _ in parcelas],
        detalles_cultivos=detalles,
    )
    conn.commit()
    return {
        "campana_id": int(campana_id),
        "cliente_id": int(cliente_id),
        "cosecha_id": int(cosecha_id),
        "cultivos": [int(valor) for valor in cultivos],
        "parcelas": [int(valor[0]) for valor in parcelas],
        "superficie_total": 5.0,
    }


def _assert_igual(actual, esperado, etiqueta):

    if actual != esperado:

        raise AssertionError(f"{etiqueta}: esperado {esperado!r}, obtenido {actual!r}")


def _assert_float(actual, esperado, etiqueta):

    if abs(float(actual or 0) - float(esperado)) > 0.0001:

        raise AssertionError(f"{etiqueta}: esperado {esperado}, obtenido {actual}")


def _validar_tabla_puente(ctx):

    with _conectar() as conn:

        filas = pd.read_sql_query(
            """
            SELECT cosecha_id, cultivo_id, parcela_id, superficie
            FROM cosecha_cultivos
            WHERE cosecha_id=?
            ORDER BY cultivo_id, parcela_id
            """,
            conn,
            params=(ctx["cosecha_id"],),
        )
        total = conn.execute(
            """
            SELECT COALESCE(SUM(superficie),0)
            FROM cosecha_cultivos
            WHERE cosecha_id=?
            """,
            (ctx["cosecha_id"],),
        ).fetchone()[0]

    _assert_igual(len(filas), 4, "detalle cosecha_cultivos")
    _assert_igual(
        sorted(filas["cultivo_id"].dropna().astype(int).unique().tolist()),
        sorted(ctx["cultivos"]),
        "cultivos en detalle",
    )
    _assert_igual(
        sorted(filas["parcela_id"].dropna().astype(int).tolist()),
        sorted(ctx["parcelas"]),
        "parcelas en detalle",
    )
    _assert_float(total, ctx["superficie_total"], "superficie detalle")
    return "tabla puente OK"


def _validar_listado_e_informes(ctx):

    with _conectar() as conn:

        cosechas = _preparar_cosechas_presentacion(
            _leer_cosechas_guardadas(conn=conn)
        )
        informes = cargar_datos_informes(conn, ctx["campana_id"])

    if cosechas.empty:

        raise AssertionError("Listado de cosecha vacio")

    cosecha = cosechas[cosechas["id"].astype(int) == ctx["cosecha_id"]].iloc[0]
    contenido = " ".join(str(valor) for valor in cosecha.tolist())

    for texto in ["Almendro", "Parcela almendro 1", "Parcela almendro 4"]:

        if texto not in contenido:

            raise AssertionError(f"Listado sin texto esperado: {texto}")

    _assert_float(
        cosecha["superficie_detalle"],
        ctx["superficie_total"],
        "superficie listado",
    )
    cosechas_informe = informes["cosechas"]

    if cosechas_informe.empty:

        raise AssertionError("Informes sin cosecha multicultivo")

    contenido_informe = " ".join(
        str(valor) for valor in cosechas_informe.stack().tolist()
    )

    if "Parcela almendro 4" not in contenido_informe:

        raise AssertionError("Informes no muestran parcelas de detalle")

    return "listado e informes OK"


def _validar_revision_siex(ctx):

    with _conectar() as conn:

        revision, registros = revision_siex._generar_revision(
            conn,
            ctx["campana_id"],
        )

    if registros <= 0:

        raise AssertionError("Revision SIEX no reviso registros")

    if not revision.empty:

        cosecha = revision[
            (revision["area"] == "Cosecha")
            & (revision["registro_id"].astype(str) == str(ctx["cosecha_id"]))
        ]
        problemas = " ".join(cosecha["problema"].astype(str).tolist())

        if "sin cultivo asociado" in problemas.lower():

            raise AssertionError("Revision SIEX no reconoce cosecha_cultivos")

    return f"revision SIEX OK ({registros} registros)"


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

        cosecha_siex = exportacion_siex.obtener_dataframe_cosecha(
            conn,
            ctx["campana_id"],
        )

    if len(contenido) <= 1024 or not nombre.endswith(".xlsx"):

        raise AssertionError("Excel SIEX vacio o nombre invalido")

    _assert_igual(len(cosecha_siex), 4, "filas cosecha SIEX")
    _assert_float(
        pd.to_numeric(cosecha_siex["superficie"], errors="coerce").sum(),
        ctx["superficie_total"],
        "superficie SIEX",
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

            ctx = _insertar_datos_base(conn)

    except Exception:

        print("Prueba cosecha multicultivo v7")
        print("==============================")
        print(f"Base usada: {DB_MULTICULTIVO}")
        print("Preparacion base: FALLO")
        print(traceback.format_exc())
        return 1

    pruebas = [
        ("Tabla puente", lambda: _validar_tabla_puente(ctx)),
        ("Listado e informes", lambda: _validar_listado_e_informes(ctx)),
        ("Revision SIEX", lambda: _validar_revision_siex(ctx)),
        ("Excel SIEX", lambda: _validar_excel_siex(ctx)),
        ("PDF oficial", lambda: _validar_pdf(ctx)),
    ]

    for nombre, funcion in pruebas:

        _registrar(resultados, nombre, funcion)

    print("Prueba cosecha multicultivo v7")
    print("==============================")
    print(f"Base usada: {DB_MULTICULTIVO}")
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

    print("")
    print("Resultado: " + ("FALLO" if fallos else "OK"))
    return 1 if fallos else 0


if __name__ == "__main__":

    raise SystemExit(main())
