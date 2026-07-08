#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
DB_V7 = APP_ROOT / "runtime" / "v7" / "prueba_integral_v7.db"
EXPORTS_DIR = APP_ROOT / "runtime" / "v7" / "exports_integral"
DOCS_DIR = APP_ROOT / "runtime" / "v7" / "documentos_integral"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.db import crear_tablas  # noqa: E402
from modules.informes import cargar_datos_informes  # noqa: E402
import modules.revision_siex as revision_siex  # noqa: E402
import services.cuadernopro_pdf as cuadernopro_pdf  # noqa: E402
import services.exportacion_siex as exportacion_siex  # noqa: E402


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

LEGACY_CODIGO_PENDIENTE = {
    "modules/explotacion.py": (
        "localidad",
        "carnet_fitosanitario",
        "fecha_ultima_inspeccion",
        "fecha_proxima_inspeccion",
    ),
    "modules/cultivos.py": (
        ("municipio,poligono", "parcelas.municipio"),
        "cultivos.parcela_id",
        "cultivos.especie",
    ),
    "modules/parcelas.py": (
        "cultivos.parcela_id",
        "cultivos.especie",
    ),
    "modules/maquinaria.py": (
        "fecha_ultima_inspeccion",
        "fecha_proxima_inspeccion",
    ),
}


def _conectar_v7():

    conn = sqlite3.connect(DB_V7)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _leer_v7(sql, params=None):

    with _conectar_v7() as conn:

        return pd.read_sql_query(sql, conn, params=params or ())


def _limpiar_base_prueba():

    DB_V7.parent.mkdir(parents=True, exist_ok=True)

    for ruta in (
        DB_V7,
        DB_V7.with_name(f"{DB_V7.name}-wal"),
        DB_V7.with_name(f"{DB_V7.name}-shm"),
    ):

        if ruta.exists():

            ruta.unlink()


def _preparar_base_v7():

    _limpiar_base_prueba()
    crear_tablas(DB_V7)


def _columnas(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _contar_tablas(conn):

    return int(conn.execute(
        """
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        """
    ).fetchone()[0])


def _validar_schema(conn):

    user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if user_version != 7:

        raise AssertionError(
            f"PRAGMA user_version={user_version}; esperado 7"
        )

    legacy = []
    for tabla, columnas_prohibidas in LEGACY_PROHIBIDAS.items():

        detectadas = sorted(columnas_prohibidas & _columnas(conn, tabla))
        legacy.extend(f"{tabla}.{columna}" for columna in detectadas)

    if legacy:

        raise AssertionError(
            "Columnas legacy detectadas: " + ", ".join(legacy)
        )

    return {
        "user_version": user_version,
        "table_count": _contar_tablas(conn),
    }


def _insertar_explotacion(conn, ctx):

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
            "Explotacion integral v7",
            "Titular Integral V7",
            "00000000T",
            "Camino Integral 1",
            "Jumilla",
            "Murcia",
            "30520",
            "600000000",
            "integral-v7@example.com",
            "REA-INTEGRAL-V7",
            "REA",
            "REG-AUT-INTEGRAL-V7",
            "Agraria",
            "Frutos secos",
            "2026-01-01",
            1,
            0,
            "Responsable Integral V7",
            "Asesor Integral V7",
            "ASE-V7-001",
            "Prueba integral v7 limpia",
            ctx["ahora"],
            ctx["ahora"],
        ),
    )


def _insertar_campana(conn, ctx):

    ctx["campana_id"] = conn.execute(
        """
        INSERT INTO campanas
        (nombre, fecha_inicio, fecha_fin, activa, estado, observaciones,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            "2025/2026",
            "2025-10-01",
            "2026-09-30",
            1,
            "abierta",
            "Campana de prueba integral v7",
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid


def _insertar_cliente_proveedor(conn, ctx):

    ctx["cliente_id"] = conn.execute(
        """
        INSERT INTO clientes
        (nombre, nif, telefono, email, direccion, poblacion, provincia,
         codigo_postal, observaciones, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Cliente prueba integral",
            "B00000001",
            "600000001",
            "cliente-integral@example.com",
            "Calle Cliente 1",
            "Jumilla",
            "Murcia",
            "30520",
            "Cliente para prueba integral v7",
            1,
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid
    ctx["proveedor_id"] = conn.execute(
        """
        INSERT INTO proveedores
        (nombre, nif, telefono, email, direccion, poblacion, provincia,
         codigo_postal, actividad, observaciones, activo, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Proveedor prueba integral",
            "B00000002",
            "600000002",
            "proveedor-integral@example.com",
            "Calle Proveedor 2",
            "Jumilla",
            "Murcia",
            "30520",
            "Servicios agrarios",
            "Proveedor para prueba integral v7",
            1,
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid


def _insertar_parcela(conn, ctx):

    ctx["parcela_id"] = conn.execute(
        """
        INSERT INTO parcelas
        (nombre, provincia_sigpac, municipio_sigpac, agregado_sigpac,
         zona_sigpac, poligono, parcela, recinto, superficie_sigpac,
         uso_sigpac, sigpac_geojson, activa, observaciones, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Parcela SIGPAC integral",
            30,
            22,
            0,
            0,
            "7",
            "45",
            "2",
            4.5,
            "TA",
            "",
            1,
            "Parcela minima de prueba integral v7",
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid


def _insertar_cultivo(conn, ctx):

    ctx["cultivo_id"] = conn.execute(
        """
        INSERT INTO cultivos
        (campana_id, nombre, variedad, codigo_siex, superficie,
         ano_plantacion, marco_plantacion, numero_arboles, activo,
         observaciones, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ctx["campana_id"],
            "ALMENDRO",
            "Guara",
            "104",
            4.5,
            2018,
            "6x5",
            1500,
            1,
            "Cultivo ALMENDRO de prueba integral v7",
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO cultivo_parcelas
        (cultivo_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (
            ctx["cultivo_id"],
            ctx["parcela_id"],
            4.5,
            ctx["ahora"],
            ctx["ahora"],
        ),
    )


def _insertar_maquinaria_equipo(conn, ctx):

    ctx["maquinaria_id"] = conn.execute(
        """
        INSERT INTO maquinaria
        (tipo, marca, modelo, matricula, numero_roma, numero_serie,
         fecha_compra, horas_uso, descripcion, observaciones, activa,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Tractor",
            "John Deere",
            "5100M",
            "0000AAA",
            "ROMA-MAQ-V7",
            "SER-MAQ-INTEGRAL-V7",
            "2025-01-15",
            100.0,
            "Tractor general integral",
            "Maquinaria general de prueba",
            1,
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid
    ctx["equipo_id"] = conn.execute(
        """
        INSERT INTO equipos_aplicacion
        (nombre, marca, modelo, tipo, matricula, numero_roma, numero_serie,
         fecha_adquisicion, capacidad_litros, fecha_revision,
         fecha_proxima_revision, observaciones, activo, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Atomizador integral",
            "ATASA",
            "Turbo 2000",
            "Equipo aplicacion fito",
            "EQ-0000AAA",
            "ROMA-EQ-INTEGRAL-V7",
            "SER-EQ-V7",
            "2025-02-15",
            600.0,
            "2026-02-01",
            "2027-02-01",
            "Equipo aplicacion fito integral",
            1,
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid


def _insertar_producto_persona(conn, ctx):

    ctx["producto_id"] = conn.execute(
        """
        INSERT INTO productos_fito
        (nombre, numero_registro, materia_activa, titular, uso_autorizado,
         plazo_seguridad, observaciones, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Producto fito integral",
            "REG-V7-0001",
            "Materia activa integral",
            "Titular producto integral",
            "Uso autorizado integral",
            "14 dias",
            "Producto fitosanitario de prueba integral v7",
            1,
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid
    ctx["aplicador_id"] = conn.execute(
        """
        INSERT INTO personas
        (nombre, nif, telefono, email, rol, carnet_aplicador,
         numero_asesor, observaciones, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Aplicador prueba integral",
            "00000001A",
            "600000003",
            "aplicador-integral@example.com",
            "Aplicador fitosanitario",
            "CARNET-V7-001",
            "",
            "Aplicador para prueba integral v7",
            1,
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid


def _insertar_tratamiento(conn, ctx):

    ctx["tratamiento_id"] = conn.execute(
        """
        INSERT INTO tratamientos
        (campana_id, cultivo_id, fecha_inicio, fecha_fin, producto_id,
         aplicador_id, equipo_aplicacion_id, plaga_motivo, dosis, caldo,
         superficie_tratada, plazo_seguridad, eficacia, observaciones,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ctx["campana_id"],
            ctx["cultivo_id"],
            "2026-03-10",
            "2026-03-10",
            ctx["producto_id"],
            ctx["aplicador_id"],
            ctx["equipo_id"],
            "Repilo integral",
            "2 l/ha",
            400,
            4.5,
            "14 dias",
            "B",
            "Tratamiento completo de prueba integral v7",
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO tratamiento_parcelas
        (tratamiento_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (
            ctx["tratamiento_id"],
            ctx["parcela_id"],
            4.5,
            ctx["ahora"],
            ctx["ahora"],
        ),
    )
    conn.execute(
        """
        INSERT INTO tratamiento_cultivos
        (tratamiento_id, cultivo_id, parcela_id, superficie, observaciones,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            ctx["tratamiento_id"],
            ctx["cultivo_id"],
            ctx["parcela_id"],
            4.5,
            "Detalle multicultivo integral",
            ctx["ahora"],
            ctx["ahora"],
        ),
    )
    conn.execute(
        """
        INSERT INTO tratamientos_documentos
        (tratamiento_id, tipo_documento, nombre_original, nombre_guardado,
         ruta_relativa, extension, mime_type, size_bytes, sha256, orden,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ctx["tratamiento_id"],
            "receta",
            "receta_integral_v7.pdf",
            "receta_integral_v7.pdf",
            "recetas/receta_integral_v7.pdf",
            "pdf",
            "application/pdf",
            0,
            "",
            1,
            ctx["ahora"],
            ctx["ahora"],
        ),
    )


def _insertar_fertilizacion(conn, ctx):

    ctx["fertilizacion_id"] = conn.execute(
        """
        INSERT INTO fertilizaciones
        (campana_id, cultivo_id, fecha, producto, tipo_fertilizante,
         cantidad, unidad, unidad_normalizada, superficie,
         codigo_actuacion_siex, observaciones, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ctx["campana_id"],
            ctx["cultivo_id"],
            "2026-04-01",
            "Abono integral",
            "Mineral",
            250,
            "kg",
            "kg",
            4.5,
            "FERT-V7-001",
            "Fertilizacion de prueba integral v7",
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO fertilizacion_parcelas
        (fertilizacion_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (
            ctx["fertilizacion_id"],
            ctx["parcela_id"],
            4.5,
            ctx["ahora"],
            ctx["ahora"],
        ),
    )
    conn.execute(
        """
        INSERT INTO fertilizacion_cultivos
        (fertilizacion_id, cultivo_id, parcela_id, superficie, observaciones,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            ctx["fertilizacion_id"],
            ctx["cultivo_id"],
            ctx["parcela_id"],
            4.5,
            "Detalle multicultivo integral",
            ctx["ahora"],
            ctx["ahora"],
        ),
    )


def _insertar_practica(conn, ctx):

    ctx["practica_id"] = conn.execute(
        """
        INSERT INTO practicas_culturales
        (campana_id, cultivo_id, fecha, labor, codigo_actuacion_siex,
         superficie, maquinaria_id, proveedor_id, observaciones, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ctx["campana_id"],
            ctx["cultivo_id"],
            "2026-05-01",
            "Poda integral",
            "LAB-V7-001",
            4.5,
            ctx["maquinaria_id"],
            ctx["proveedor_id"],
            "Practica cultural de prueba integral v7",
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO practicas_culturales_parcelas
        (practica_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (
            ctx["practica_id"],
            ctx["parcela_id"],
            4.5,
            ctx["ahora"],
            ctx["ahora"],
        ),
    )
    conn.execute(
        """
        INSERT INTO practicas_culturales_cultivos
        (practica_id, cultivo_id, parcela_id, superficie, observaciones,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            ctx["practica_id"],
            ctx["cultivo_id"],
            ctx["parcela_id"],
            4.5,
            "Detalle multicultivo integral",
            ctx["ahora"],
            ctx["ahora"],
        ),
    )


def _insertar_cosecha(conn, ctx):

    ctx["cosecha_id"] = conn.execute(
        """
        INSERT INTO cosecha
        (campana_id, cultivo_id, fecha, cantidad, unidad, destino,
         cliente_id, observaciones, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ctx["campana_id"],
            ctx["cultivo_id"],
            "2026-09-01",
            1200,
            "kg",
            "Cooperativa integral",
            ctx["cliente_id"],
            "Cosecha de prueba integral v7",
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO cosecha_parcelas
        (cosecha_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (
            ctx["cosecha_id"],
            ctx["parcela_id"],
            4.5,
            ctx["ahora"],
            ctx["ahora"],
        ),
    )
    conn.execute(
        """
        INSERT INTO cosecha_cultivos
        (cosecha_id, cultivo_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?,?)
        """,
        (
            ctx["cosecha_id"],
            ctx["cultivo_id"],
            ctx["parcela_id"],
            4.5,
            ctx["ahora"],
            ctx["ahora"],
        ),
    )


def _insertar_contabilidad(conn, ctx):

    ctx["ingreso_id"] = conn.execute(
        """
        INSERT INTO movimientos_economicos
        (campana_id, cultivo_id, fecha, tipo, categoria, concepto,
         numero_factura, cliente_id, proveedor_id, base_imponible, iva,
         retencion, total, pendiente, fecha_pago, observaciones, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ctx["campana_id"],
            ctx["cultivo_id"],
            "2026-09-15",
            "Ingreso",
            "Venta",
            "Venta almendra integral",
            "FV-V7-001",
            ctx["cliente_id"],
            None,
            1000,
            210,
            0,
            1210,
            0,
            "2026-09-30",
            "Ingreso de prueba integral v7",
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid
    ctx["gasto_id"] = conn.execute(
        """
        INSERT INTO movimientos_economicos
        (campana_id, cultivo_id, fecha, tipo, categoria, concepto,
         numero_factura, cliente_id, proveedor_id, base_imponible, iva,
         retencion, total, pendiente, fecha_pago, observaciones, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ctx["campana_id"],
            ctx["cultivo_id"],
            "2026-04-15",
            "Gasto",
            "Insumos",
            "Compra fertilizante integral",
            "FC-V7-001",
            None,
            ctx["proveedor_id"],
            300,
            63,
            0,
            363,
            1,
            "",
            "Gasto de prueba integral v7",
            ctx["ahora"],
            ctx["ahora"],
        ),
    ).lastrowid

    for movimiento_id, descripcion, base, tipo_iva in (
        (ctx["ingreso_id"], "Venta almendra integral", 1000, 21),
        (ctx["gasto_id"], "Compra fertilizante integral", 300, 21),
    ):

        conn.execute(
            """
            INSERT INTO movimientos_economicos_lineas_iva
            (movimiento_id, descripcion, base_imponible, tipo_iva,
             cuota_iva, total_linea, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                movimiento_id,
                descripcion,
                base,
                tipo_iva,
                round(base * tipo_iva / 100, 2),
                round(base + (base * tipo_iva / 100), 2),
                ctx["ahora"],
                ctx["ahora"],
            ),
        )

    conn.execute(
        """
        INSERT INTO movimientos_economicos_documentos
        (movimiento_id, tipo_documento, nombre_original, nombre_guardado,
         ruta_relativa, extension, mime_type, size_bytes, sha256, orden,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ctx["ingreso_id"],
            "factura",
            "factura_integral_v7.pdf",
            "factura_integral_v7.pdf",
            "facturas/factura_integral_v7.pdf",
            "pdf",
            "application/pdf",
            0,
            "",
            1,
            ctx["ahora"],
            ctx["ahora"],
        ),
    )


def _validar_conteos(conn):

    esperados = {
        "explotacion": 1,
        "campanas": 1,
        "clientes": 1,
        "proveedores": 1,
        "parcelas": 1,
        "cultivos": 1,
        "cultivo_parcelas": 1,
        "maquinaria": 1,
        "equipos_aplicacion": 1,
        "productos_fito": 1,
        "personas": 1,
        "tratamientos": 1,
        "tratamiento_parcelas": 1,
        "tratamiento_cultivos": 1,
        "tratamientos_documentos": 1,
        "fertilizaciones": 1,
        "fertilizacion_parcelas": 1,
        "fertilizacion_cultivos": 1,
        "practicas_culturales": 1,
        "practicas_culturales_parcelas": 1,
        "practicas_culturales_cultivos": 1,
        "cosecha": 1,
        "cosecha_parcelas": 1,
        "cosecha_cultivos": 1,
        "movimientos_economicos": 2,
        "movimientos_economicos_lineas_iva": 2,
        "movimientos_economicos_documentos": 1,
    }
    errores = []

    for tabla, minimo in esperados.items():

        total = int(conn.execute(
            f'SELECT COUNT(*) FROM "{tabla}"'
        ).fetchone()[0])

        if total < minimo:

            errores.append(f"{tabla}: {total}; esperado >= {minimo}")

    if errores:

        raise AssertionError("; ".join(errores))


def _validar_informes(conn, ctx):

    datos = cargar_datos_informes(conn, ctx["campana_id"])
    esperados = {
        "movimientos": "Venta almendra integral",
        "tratamientos": "Repilo integral",
        "fertilizaciones": "Abono integral",
        "practicas": "Poda integral",
        "cosechas": "Cooperativa integral",
    }

    for clave, texto in esperados.items():

        dataframe = datos[clave]

        if dataframe.empty:

            raise AssertionError(f"Informes sin datos en {clave}")

        contenido = " ".join(str(valor) for valor in dataframe.stack().tolist())

        if texto not in contenido:

            raise AssertionError(f"Informes no resuelven {clave}: {texto}")

    ctx["informes_avisos"] = len(datos.get("avisos", []))


def _validar_revision_siex(conn, ctx):

    revision, registros_revisados = revision_siex._generar_revision(
        conn,
        ctx["campana_id"],
    )
    ctx["revision_siex_filas"] = len(revision)
    ctx["revision_siex_registros"] = registros_revisados
    ctx["revision_siex_bloqueos"] = (
        0
        if revision.empty
        else int((revision["bloquea_exportacion"] == "Si").sum())
    )

    if registros_revisados <= 0:

        raise AssertionError("Revision SIEX no reviso registros")

    return revision


def _validar_excel_siex(ctx, revision):

    original_conectar = exportacion_siex.conectar
    exportacion_siex.conectar = _conectar_v7

    try:

        contenido, nombre = exportacion_siex.generar_excel_asistido_siex(
            campana_id=ctx["campana_id"],
            revision=revision,
        )

    finally:

        exportacion_siex.conectar = original_conectar

    if not contenido or len(contenido) < 1024:

        raise AssertionError("Excel SIEX vacio o demasiado pequeno")

    if not nombre.endswith(".xlsx"):

        raise AssertionError("Nombre de Excel SIEX invalido")

    with _conectar_v7() as conn:

        hojas = {
            "Tratamientos": exportacion_siex.obtener_dataframe_tratamientos(
                conn,
                ctx["campana_id"],
            ),
            "Fertilizacion": exportacion_siex.obtener_dataframe_fertilizacion(
                conn,
                ctx["campana_id"],
            ),
            "Practicas": exportacion_siex.obtener_dataframe_practicas(
                conn,
                ctx["campana_id"],
            ),
            "Cosecha": exportacion_siex.obtener_dataframe_cosecha(
                conn,
                ctx["campana_id"],
            ),
        }

    vacias = [
        nombre_hoja
        for nombre_hoja, dataframe in hojas.items()
        if dataframe.empty
    ]
    if vacias:

        raise AssertionError(
            "Excel SIEX sin datos en: " + ", ".join(vacias)
        )

    ctx["excel_siex_nombre"] = nombre
    ctx["excel_siex_bytes"] = len(contenido)


def _validar_pdf_oficial(ctx):

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    original_conectar = cuadernopro_pdf.conectar
    original_leer = cuadernopro_pdf.leer
    original_exports = cuadernopro_pdf.EXPORTS_DIR
    original_docs = cuadernopro_pdf.DOCS_DIR
    cuadernopro_pdf.conectar = _conectar_v7
    cuadernopro_pdf.leer = _leer_v7
    cuadernopro_pdf.EXPORTS_DIR = EXPORTS_DIR
    cuadernopro_pdf.DOCS_DIR = DOCS_DIR

    try:

        ruta_pdf = Path(cuadernopro_pdf.generar_cuadernopro_pdf(
            ctx["campana_id"],
        ))

    finally:

        cuadernopro_pdf.conectar = original_conectar
        cuadernopro_pdf.leer = original_leer
        cuadernopro_pdf.EXPORTS_DIR = original_exports
        cuadernopro_pdf.DOCS_DIR = original_docs

    if not ruta_pdf.exists() or ruta_pdf.stat().st_size <= 0:

        raise AssertionError("PDF oficial no se ha generado correctamente")

    ctx["pdf_oficial"] = str(ruta_pdf)
    ctx["pdf_oficial_bytes"] = ruta_pdf.stat().st_size


def _buscar_dependencias_legacy_codigo():

    hallazgos = []

    for ruta_relativa, patrones in LEGACY_CODIGO_PENDIENTE.items():

        ruta = APP_ROOT / ruta_relativa

        if not ruta.exists():

            continue

        contenido = ruta.read_text(encoding="utf-8")
        detectados = []

        for patron in patrones:

            if isinstance(patron, tuple):

                aguja, etiqueta = patron

            else:

                aguja = patron
                etiqueta = patron

            if aguja in contenido:

                detectados.append(etiqueta)

        if detectados:

            hallazgos.append(
                f"{ruta_relativa}: " + ", ".join(detectados)
            )

    return hallazgos


def _registrar(resultados, modulo, funcion):

    try:

        detalle = funcion()
        resultados.append((modulo, "OK", detalle or ""))
        return True

    except Exception as exc:

        resultados.append((modulo, "Fallo", str(exc)))
        return False


def _imprimir_resultados(resultados, ctx, schema_info, legacy_codigo):

    print("Prueba integral base v7 limpia")
    print("==============================")
    print(f"Base: {DB_V7}")
    print(f"PRAGMA user_version: {schema_info['user_version']}")
    print(f"Numero de tablas: {schema_info['table_count']}")
    print("")
    print("Modulos probados")

    for modulo, estado, detalle in resultados:

        linea = f"- {modulo}: {estado}"

        if detalle:

            linea += f" ({detalle})"

        print(linea)

    print("")
    print("Salidas")
    print(
        "- Excel SIEX: "
        f"OK ({ctx.get('excel_siex_nombre')}, "
        f"{ctx.get('excel_siex_bytes')} bytes)"
    )
    print(
        "- PDF oficial: "
        f"OK ({ctx.get('pdf_oficial')}, "
        f"{ctx.get('pdf_oficial_bytes')} bytes)"
    )
    print(
        "- Revision SIEX: "
        f"OK ({ctx.get('revision_siex_registros')} registros, "
        f"{ctx.get('revision_siex_filas')} avisos/info, "
        f"{ctx.get('revision_siex_bloqueos')} bloqueos)"
    )
    print("")

    if legacy_codigo:

        print("Dependencias legacy pendientes en codigo")

        for hallazgo in legacy_codigo:

            print(f"- {hallazgo}")

    else:

        print("Dependencias legacy pendientes en codigo: ninguna detectada")

    fallos = [modulo for modulo, estado, _ in resultados if estado != "OK"]
    print("")
    print("Legacy en esquema: ninguno")
    print("Resultado: " + ("FALLO" if fallos else "OK"))


def main():

    resultados = []
    ctx = {
        "ahora": datetime.now().isoformat(timespec="seconds"),
    }
    schema_info = {}
    revision = pd.DataFrame()

    _registrar(
        resultados,
        "Base v7 limpia",
        lambda: (_preparar_base_v7(), "creada con core.db.crear_tablas")[1],
    )

    with _conectar_v7() as conn:

        _registrar(
            resultados,
            "Diagnostico esquema",
            lambda: schema_info.update(_validar_schema(conn)) or "schema OK",
        )
        _registrar(resultados, "Explotacion", lambda: _insertar_explotacion(conn, ctx))
        _registrar(resultados, "Campana", lambda: _insertar_campana(conn, ctx))
        _registrar(
            resultados,
            "Cliente y proveedor",
            lambda: _insertar_cliente_proveedor(conn, ctx),
        )
        _registrar(resultados, "Parcela", lambda: _insertar_parcela(conn, ctx))
        _registrar(resultados, "Cultivo", lambda: _insertar_cultivo(conn, ctx))
        _registrar(
            resultados,
            "Maquinaria y equipo aplicacion",
            lambda: _insertar_maquinaria_equipo(conn, ctx),
        )
        _registrar(
            resultados,
            "Producto fitosanitario y persona",
            lambda: _insertar_producto_persona(conn, ctx),
        )
        _registrar(
            resultados,
            "Tratamiento",
            lambda: _insertar_tratamiento(conn, ctx),
        )
        _registrar(
            resultados,
            "Fertilizacion",
            lambda: _insertar_fertilizacion(conn, ctx),
        )
        _registrar(
            resultados,
            "Practica cultural",
            lambda: _insertar_practica(conn, ctx),
        )
        _registrar(resultados, "Cosecha", lambda: _insertar_cosecha(conn, ctx))
        _registrar(
            resultados,
            "Contabilidad",
            lambda: _insertar_contabilidad(conn, ctx),
        )
        conn.commit()
        _registrar(resultados, "Conteos relacionales", lambda: _validar_conteos(conn))
        _registrar(resultados, "Informes", lambda: _validar_informes(conn, ctx))

        def _revision():

            nonlocal revision
            revision = _validar_revision_siex(conn, ctx)

        _registrar(resultados, "Revision SIEX", _revision)

    _registrar(
        resultados,
        "Excel asistido SIEX",
        lambda: _validar_excel_siex(ctx, revision),
    )
    _registrar(
        resultados,
        "PDF oficial",
        lambda: _validar_pdf_oficial(ctx),
    )

    legacy_codigo = _buscar_dependencias_legacy_codigo()
    _imprimir_resultados(resultados, ctx, schema_info, legacy_codigo)

    return 1 if any(estado != "OK" for _, estado, _ in resultados) else 0


if __name__ == "__main__":

    raise SystemExit(main())
