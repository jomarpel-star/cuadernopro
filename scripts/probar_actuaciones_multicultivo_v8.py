#!/usr/bin/env python3
from pathlib import Path
import os
import sqlite3
import sys
import traceback

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
DB_MULTICULTIVO = (
    APP_ROOT / "runtime" / "v8" / "prueba_actuaciones_multicultivo_v8.db"
)
EXPORTS_DIR = APP_ROOT / "runtime" / "v8" / "exports_actuaciones_multicultivo"
DOCS_DIR = APP_ROOT / "runtime" / "v8" / "documentos_actuaciones_multicultivo"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_MULTICULTIVO)

from core.db import crear_tablas  # noqa: E402
from modules.fertilizacion import (  # noqa: E402
    _actualizar_fertilizacion_compatible,
    _insertar_fertilizacion_compatible,
    _leer_fertilizaciones_guardadas,
    _preparar_fertilizaciones_presentacion,
)
from modules.informes import cargar_datos_informes  # noqa: E402
from modules.practicas_culturales import (  # noqa: E402
    _actualizar_practica_compatible,
    _insertar_practica_compatible,
    _leer_practicas_guardadas,
    _preparar_practicas_presentacion,
)
import modules.revision_siex as revision_siex  # noqa: E402
from modules.tratamientos import (  # noqa: E402
    _actualizar_tratamiento_compatible,
    _insertar_tratamiento_compatible,
    _leer_tratamientos_guardados,
)
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
            "Campana actuaciones multicultivo",
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
            "Finca actuaciones multicultivo",
            "Titular Multicultivo",
            "00000000T",
            "Camino agricola 1",
            "Jumilla",
            "Murcia",
            "30520",
            "600000001",
            "titular@example.com",
            "REGEPA-ACT-001",
            "REGEPA",
            "REG-ACT-001",
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
    producto_id = conn.execute(
        """
        INSERT INTO productos_fito
        (nombre, numero_registro, materia_activa, plazo_seguridad, activo,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            "Cobre multicultivo",
            "REG-ACT-001",
            "Oxicloruro de cobre",
            "14 dias",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    aplicador_id = conn.execute(
        """
        INSERT INTO personas
        (nombre, nif, rol, carnet_aplicador, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            "Aplicador Multicultivo",
            "00000001A",
            "Aplicador fitosanitario",
            "CARNET-ACT",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    equipo_id = conn.execute(
        """
        INSERT INTO equipos_aplicacion
        (nombre, marca, modelo, tipo, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            "Atomizador multicultivo",
            "ATASA",
            "Turbo 2000",
            "Atomizador",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    maquinaria_id = conn.execute(
        """
        INSERT INTO maquinaria
        (tipo, marca, modelo, descripcion, activa, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            "Tractor",
            "John Deere",
            "5100",
            "Tractor multicultivo",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    proveedor_id = conn.execute(
        """
        INSERT INTO proveedores
        (nombre, nif, actividad, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?)
        """,
        (
            "Servicios Multicultivo",
            "B30000000",
            "Servicios agricolas",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
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
                "Parcela de prueba",
                ahora,
                ahora,
            ),
        ).lastrowid
        parcelas.append((parcela_id, superficie))

    cultivos = []

    for ano, superficie, marco, arboles in [
        (2010, 2.3, "7x7", 469),
        (2018, 1.3, "6x5", 433),
        (2022, 1.4, "6x5", 467),
    ]:

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
                marco,
                arboles,
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
            "cultivo_id": int(cultivo_id),
            "parcela_id": int(parcela_id),
            "superficie": float(superficie),
        }
        for cultivo_id, (parcela_id, superficie) in relaciones
    ]
    tratamiento_id = _insertar_tratamiento_compatible(
        conn,
        {
            "campana_id": campana_id,
            "cultivo_id": cultivos[0],
            "fecha": "2026-03-10",
            "fecha_inicio": "2026-03-10",
            "fecha_fin": "2026-03-10",
            "producto_id": producto_id,
            "producto": "Cobre multicultivo",
            "plaga_motivo": "Cribado",
            "dosis": "2 kg/ha",
            "caldo": 800.0,
            "aplicador_id": aplicador_id,
            "equipo_aplicacion_id": equipo_id,
            "superficie_tratada": 5.0,
            "plazo_seguridad": "14 dias",
            "eficacia": "B",
            "observaciones": "Tratamiento multicultivo",
        },
        detalles_cultivos=detalles,
    )
    fertilizacion_id = _insertar_fertilizacion_compatible(
        conn,
        {
            "campana_id": campana_id,
            "cultivo_id": cultivos[0],
            "fecha": "2026-02-15",
            "producto": "Complejo NPK",
            "tipo_fertilizante": "Mineral",
            "cantidad": 1200.0,
            "unidad": "kg",
            "unidad_normalizada": "kg",
            "superficie": 5.0,
            "codigo_actuacion_siex": "FERT-MULTI",
            "observaciones": "Fertilizacion multicultivo",
        },
        detalles_cultivos=detalles,
    )
    practica_id = _insertar_practica_compatible(
        conn,
        {
            "campana_id": campana_id,
            "cultivo_id": cultivos[0],
            "fecha": "2026-01-20",
            "labor": "Poda",
            "codigo_actuacion_siex": "PODA-MULTI",
            "superficie": 5.0,
            "maquinaria_id": maquinaria_id,
            "proveedor_id": proveedor_id,
            "observaciones": "Practica multicultivo",
        },
        detalles_cultivos=detalles,
    )
    tratamiento_fallback_id = _insertar_tratamiento_compatible(
        conn,
        {
            "campana_id": campana_id,
            "cultivo_id": cultivos[0],
            "fecha": "2026-04-10",
            "fecha_inicio": "2026-04-10",
            "fecha_fin": "2026-04-10",
            "producto_id": producto_id,
            "plaga_motivo": "Fallback",
            "superficie_tratada": 1.1,
            "eficacia": "B",
        },
        [{"parcela_id": parcelas[0][0], "superficie": parcelas[0][1]}],
    )
    fertilizacion_fallback_id = _insertar_fertilizacion_compatible(
        conn,
        {
            "campana_id": campana_id,
            "cultivo_id": cultivos[0],
            "fecha": "2026-04-15",
            "producto": "Fallback fertilizante",
            "tipo_fertilizante": "Mineral",
            "cantidad": 100.0,
            "unidad": "kg",
            "superficie": 1.1,
        },
        [parcelas[0][0]],
    )
    practica_fallback_id = _insertar_practica_compatible(
        conn,
        {
            "campana_id": campana_id,
            "cultivo_id": cultivos[0],
            "fecha": "2026-04-20",
            "labor": "Fallback labor",
            "superficie": 1.1,
            "maquinaria_id": maquinaria_id,
            "proveedor_id": proveedor_id,
        },
        [parcelas[0][0]],
    )
    conn.commit()
    return {
        "campana_id": int(campana_id),
        "cultivos": [int(valor) for valor in cultivos],
        "parcelas": [int(valor[0]) for valor in parcelas],
        "tratamiento_id": int(tratamiento_id),
        "fertilizacion_id": int(fertilizacion_id),
        "practica_id": int(practica_id),
        "tratamiento_fallback_id": int(tratamiento_fallback_id),
        "fertilizacion_fallback_id": int(fertilizacion_fallback_id),
        "practica_fallback_id": int(practica_fallback_id),
        "superficie_total": 5.0,
        "detalle_count": len(detalles),
    }


def _assert_igual(actual, esperado, etiqueta):

    if actual != esperado:

        raise AssertionError(f"{etiqueta}: esperado {esperado!r}, obtenido {actual!r}")


def _assert_float(actual, esperado, etiqueta):

    if abs(float(actual or 0) - float(esperado)) > 0.0001:

        raise AssertionError(f"{etiqueta}: esperado {esperado}, obtenido {actual}")


def _validar_tablas_puente(ctx):

    pares = [
        (
            "tratamiento_cultivos",
            "tratamiento_id",
            ctx["tratamiento_id"],
            "tratamiento_parcelas",
        ),
        (
            "fertilizacion_cultivos",
            "fertilizacion_id",
            ctx["fertilizacion_id"],
            "fertilizacion_parcelas",
        ),
        (
            "practicas_culturales_cultivos",
            "practica_id",
            ctx["practica_id"],
            "practicas_culturales_parcelas",
        ),
    ]

    with _conectar() as conn:

        for tabla_detalle, campo, registro_id, tabla_parcelas in pares:

            detalle = pd.read_sql_query(
                f"""
                SELECT cultivo_id, parcela_id, superficie
                FROM {tabla_detalle}
                WHERE {campo}=?
                ORDER BY cultivo_id, parcela_id
                """,
                conn,
                params=(registro_id,),
            )
            compat = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM {tabla_parcelas}
                WHERE {campo}=?
                """,
                (registro_id,),
            ).fetchone()[0]
            _assert_igual(len(detalle), ctx["detalle_count"], tabla_detalle)
            _assert_igual(int(compat), len(ctx["parcelas"]), tabla_parcelas)
            _assert_igual(
                sorted(detalle["cultivo_id"].dropna().astype(int).unique()),
                sorted(ctx["cultivos"]),
                f"cultivos {tabla_detalle}",
            )
            _assert_float(
                pd.to_numeric(detalle["superficie"], errors="coerce").sum(),
                ctx["superficie_total"],
                f"superficie {tabla_detalle}",
            )

    return "tablas puente y compatibilidad OK"


def _validar_listados_e_informes(ctx):

    with _conectar() as conn:

        tratamientos = _leer_tratamientos_guardados(conn=conn)
        fertilizaciones = _preparar_fertilizaciones_presentacion(
            _leer_fertilizaciones_guardadas(conn=conn)
        )
        practicas = _preparar_practicas_presentacion(
            _leer_practicas_guardadas(conn=conn)
        )
        informes = cargar_datos_informes(conn, ctx["campana_id"])

    comprobaciones = [
        (tratamientos, ctx["tratamiento_id"], "Tratamiento"),
        (fertilizaciones, ctx["fertilizacion_id"], "Fertilizacion"),
        (practicas, ctx["practica_id"], "Practica"),
    ]

    for dataframe, registro_id, etiqueta in comprobaciones:

        fila = dataframe[dataframe["id"].astype(int) == int(registro_id)].iloc[0]
        contenido = " ".join(str(valor) for valor in fila.tolist())

        for esperado in ["Almendro", "Plant. 2018", "Parcela almendro 4"]:

            if esperado not in contenido:

                raise AssertionError(f"{etiqueta} sin {esperado}")

    for clave in ("tratamientos", "fertilizaciones", "practicas"):

        if informes[clave].empty:

            raise AssertionError(f"Informes sin {clave}")

    return "listados e informes OK"


def _validar_revision_siex(ctx):

    with _conectar() as conn:

        revision, registros = revision_siex._generar_revision(
            conn,
            ctx["campana_id"],
        )

    if registros <= 0:

        raise AssertionError("Revision SIEX no reviso registros")

    for area, registro_id in [
        ("Tratamientos", ctx["tratamiento_id"]),
        ("Fertilización", ctx["fertilizacion_id"]),
        ("Prácticas culturales", ctx["practica_id"]),
    ]:

        filas = revision[
            (revision["area"] == area)
            & (revision["registro_id"].astype(str) == str(registro_id))
        ]
        problemas = " ".join(filas["problema"].astype(str).tolist()).lower()

        if "sin cultivo" in problemas or "sin parcelas" in problemas:

            raise AssertionError(f"Revision SIEX no reconoce detalle en {area}")

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

        tratamientos = exportacion_siex.obtener_dataframe_tratamientos(
            conn,
            ctx["campana_id"],
        )
        fertilizaciones = exportacion_siex.obtener_dataframe_fertilizacion(
            conn,
            ctx["campana_id"],
        )
        practicas = exportacion_siex.obtener_dataframe_practicas(
            conn,
            ctx["campana_id"],
        )

    if len(contenido) <= 1024 or not nombre.endswith(".xlsx"):

        raise AssertionError("Excel SIEX vacio o nombre invalido")

    checks = [
        (tratamientos, "tratamiento_id", ctx["tratamiento_id"]),
        (fertilizaciones, "fertilizacion_id", ctx["fertilizacion_id"]),
        (practicas, "practica_id", ctx["practica_id"]),
    ]

    for dataframe, columna, registro_id in checks:

        filas = dataframe[dataframe[columna].astype(int) == int(registro_id)]
        _assert_igual(len(filas), ctx["detalle_count"], columna)

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


def _validar_edicion_y_borrado(ctx):

    with _conectar() as conn:

        conteos_antes = {
            "tratamiento": conn.execute(
                """
                SELECT COUNT(*) FROM tratamiento_cultivos
                WHERE tratamiento_id=?
                """,
                (ctx["tratamiento_id"],),
            ).fetchone()[0],
            "fertilizacion": conn.execute(
                """
                SELECT COUNT(*) FROM fertilizacion_cultivos
                WHERE fertilizacion_id=?
                """,
                (ctx["fertilizacion_id"],),
            ).fetchone()[0],
            "practica": conn.execute(
                """
                SELECT COUNT(*) FROM practicas_culturales_cultivos
                WHERE practica_id=?
                """,
                (ctx["practica_id"],),
            ).fetchone()[0],
        }
        _actualizar_tratamiento_compatible(
            conn,
            ctx["tratamiento_id"],
            {"observaciones": "Tratamiento editado sin tocar detalle"},
        )
        _actualizar_fertilizacion_compatible(
            conn,
            ctx["fertilizacion_id"],
            {"observaciones": "Fertilizacion editada sin tocar detalle"},
        )
        _actualizar_practica_compatible(
            conn,
            ctx["practica_id"],
            {"observaciones": "Practica editada sin tocar detalle"},
        )
        conn.commit()
        conteos_despues = {
            "tratamiento": conn.execute(
                """
                SELECT COUNT(*) FROM tratamiento_cultivos
                WHERE tratamiento_id=?
                """,
                (ctx["tratamiento_id"],),
            ).fetchone()[0],
            "fertilizacion": conn.execute(
                """
                SELECT COUNT(*) FROM fertilizacion_cultivos
                WHERE fertilizacion_id=?
                """,
                (ctx["fertilizacion_id"],),
            ).fetchone()[0],
            "practica": conn.execute(
                """
                SELECT COUNT(*) FROM practicas_culturales_cultivos
                WHERE practica_id=?
                """,
                (ctx["practica_id"],),
            ).fetchone()[0],
        }
        _assert_igual(conteos_despues, conteos_antes, "detalle tras edicion")
        conn.execute("DELETE FROM tratamientos WHERE id=?", (ctx["tratamiento_id"],))
        conn.execute(
            "DELETE FROM fertilizaciones WHERE id=?",
            (ctx["fertilizacion_id"],),
        )
        conn.execute(
            "DELETE FROM practicas_culturales WHERE id=?",
            (ctx["practica_id"],),
        )
        conn.commit()
        restantes = sum(
            conn.execute(sql, (registro_id,)).fetchone()[0]
            for sql, registro_id in [
                (
                    "SELECT COUNT(*) FROM tratamiento_cultivos WHERE tratamiento_id=?",
                    ctx["tratamiento_id"],
                ),
                (
                    "SELECT COUNT(*) FROM tratamiento_parcelas WHERE tratamiento_id=?",
                    ctx["tratamiento_id"],
                ),
                (
                    "SELECT COUNT(*) FROM fertilizacion_cultivos WHERE fertilizacion_id=?",
                    ctx["fertilizacion_id"],
                ),
                (
                    "SELECT COUNT(*) FROM fertilizacion_parcelas WHERE fertilizacion_id=?",
                    ctx["fertilizacion_id"],
                ),
                (
                    "SELECT COUNT(*) FROM practicas_culturales_cultivos WHERE practica_id=?",
                    ctx["practica_id"],
                ),
                (
                    """
                    SELECT COUNT(*) FROM practicas_culturales_parcelas
                    WHERE practica_id=?
                    """,
                    ctx["practica_id"],
                ),
            ]
        )
        _assert_igual(restantes, 0, "detalles tras borrado")

    return "edicion general y borrado OK"


def _validar_fallback(ctx):

    with _conectar() as conn:

        tratamientos = _leer_tratamientos_guardados(conn=conn)
        fertilizaciones = _preparar_fertilizaciones_presentacion(
            _leer_fertilizaciones_guardadas(conn=conn)
        )
        practicas = _preparar_practicas_presentacion(
            _leer_practicas_guardadas(conn=conn)
        )

    checks = [
        (tratamientos, ctx["tratamiento_fallback_id"], "Fallback"),
        (fertilizaciones, ctx["fertilizacion_fallback_id"], "Fallback"),
        (practicas, ctx["practica_fallback_id"], "Fallback"),
    ]

    for dataframe, registro_id, esperado in checks:

        fila = dataframe[dataframe["id"].astype(int) == int(registro_id)].iloc[0]
        contenido = " ".join(str(valor) for valor in fila.tolist())

        if esperado not in contenido or "Parcela almendro 1" not in contenido:

            raise AssertionError("Fallback antiguo no resuelto")

    return "fallback antiguo OK"


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

        print("Prueba actuaciones multicultivo v8.0.1")
        print("=======================================")
        print(f"Base usada: {DB_MULTICULTIVO}")
        print("Preparacion base: FALLO")
        print(traceback.format_exc())
        return 1

    pruebas = [
        ("Tablas puente", lambda: _validar_tablas_puente(ctx)),
        ("Listados e informes", lambda: _validar_listados_e_informes(ctx)),
        ("Revision SIEX", lambda: _validar_revision_siex(ctx)),
        ("Excel SIEX", lambda: _validar_excel_siex(ctx)),
        ("PDF oficial", lambda: _validar_pdf(ctx)),
        ("Fallback antiguo", lambda: _validar_fallback(ctx)),
        ("Edicion y borrado", lambda: _validar_edicion_y_borrado(ctx)),
    ]

    for nombre, funcion in pruebas:

        _registrar(resultados, nombre, funcion)

    print("Prueba actuaciones multicultivo v8.0.1")
    print("=======================================")
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

        return 1

    print("")
    print("Conclusion: actuaciones multicultivo v8.0.1 validadas")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
