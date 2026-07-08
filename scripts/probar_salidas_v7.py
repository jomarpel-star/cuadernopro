#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
DB_V7 = APP_ROOT / "runtime" / "v7" / "cuadernopro_v7_limpia.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.schema_v7 import crear_base_v7  # noqa: E402
from modules.informes import cargar_datos_informes  # noqa: E402
import services.cuadernopro_pdf as cuadernopro_pdf  # noqa: E402
import services.exportacion_siex as exportacion_siex  # noqa: E402


LEGACY_PROHIBIDAS = {
    "cosecha": {"cultivo", "cliente", "nif_cliente", "kg"},
    "fertilizaciones": {"cultivo"},
    "practicas_culturales": {"cultivo"},
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


def _conectar_v7():

    conn = sqlite3.connect(DB_V7)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _leer_v7(sql, params=None):

    with _conectar_v7() as conn:

        return pd.read_sql_query(sql, conn, params=params or ())


def _validar_sin_legacy(conn):

    errores = []

    for tabla, columnas_prohibidas in LEGACY_PROHIBIDAS.items():

        columnas = {
            fila[1]
            for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
        }
        detectadas = columnas_prohibidas & columnas

        if detectadas:

            errores.append(f"{tabla}: {', '.join(sorted(detectadas))}")

    if errores:

        raise AssertionError(
            "Columnas legacy detectadas en base v7: "
            + "; ".join(errores)
        )


def _insertar_datos(conn):

    ahora = datetime.now().isoformat()
    marca = datetime.now().strftime("%Y%m%d%H%M%S%f")
    conn.execute(
        """
        INSERT INTO explotacion
        (nombre_explotacion, titular, nif, direccion, municipio, provincia,
         codigo_postal, telefono, email, identificador_oficial,
         tipo_identificador_oficial, responsable, asesor, numero_asesor,
         observaciones, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            f"Explotacion prueba v7.6 {marca}",
            "Titular prueba",
            "00000000T",
            "Camino de prueba",
            "Municipio prueba",
            "Provincia prueba",
            "00000",
            "600000000",
            "prueba@example.com",
            f"REA{marca[-6:]}",
            "REA",
            "Responsable prueba",
            "Asesor prueba",
            "ASE-001",
            "Prueba aislada de salidas v7",
            ahora,
            ahora,
        ),
    )
    campana_id = conn.execute(
        """
        INSERT INTO campanas
        (nombre, fecha_inicio, fecha_fin, activa, estado, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            f"Prueba v7.6 {marca}",
            "2026-01-01",
            "2026-12-31",
            1,
            "abierta",
            ahora,
            ahora,
        ),
    ).lastrowid
    parcela_id = conn.execute(
        """
        INSERT INTO parcelas
        (nombre, provincia_sigpac, municipio_sigpac, poligono, parcela,
         recinto, superficie_sigpac, uso_sigpac, activa, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            f"Parcela prueba v7.6 {marca}",
            41,
            91,
            "7",
            "45",
            "2",
            4.5,
            "TA",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    cultivo_id = conn.execute(
        """
        INSERT INTO cultivos
        (campana_id, nombre, variedad, codigo_siex, superficie,
         ano_plantacion, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            "ALMENDRO",
            "Guara",
            "104",
            4.5,
            2018,
            1,
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
        (cultivo_id, parcela_id, 4.5, ahora, ahora),
    )
    cliente_id = conn.execute(
        """
        INSERT INTO clientes
        (nombre, nif, telefono, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?)
        """,
        (f"Cliente prueba v7.6 {marca}", "B00000001", "600000001", 1, ahora, ahora),
    ).lastrowid
    proveedor_id = conn.execute(
        """
        INSERT INTO proveedores
        (nombre, nif, actividad, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?)
        """,
        (
            f"Proveedor prueba v7.6 {marca}",
            "B00000002",
            "Servicios agrarios",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    producto_id = conn.execute(
        """
        INSERT INTO productos_fito
        (nombre, numero_registro, materia_activa, titular, uso_autorizado,
         plazo_seguridad, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            f"Producto fito prueba v7.6 {marca}",
            f"REG{marca[-8:]}",
            "Materia activa prueba",
            "Titular prueba",
            "Uso prueba",
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
            f"Aplicador prueba v7.6 {marca}",
            "00000001A",
            "Aplicador fitosanitario",
            "CARNET-001",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    maquinaria_id = conn.execute(
        """
        INSERT INTO maquinaria
        (tipo, marca, modelo, matricula, numero_roma, descripcion, activa,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            "Tractor",
            "Marca",
            "Modelo",
            "0000AAA",
            "ROMA-001",
            "Tractor prueba",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    equipo_id = conn.execute(
        """
        INSERT INTO equipos_aplicacion
        (nombre, marca, modelo, tipo, numero_serie, fecha_revision,
         fecha_proxima_revision, activo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "ATASA TURBO 2000",
            "ATASA",
            "Turbo 2000",
            "Equipo aplicacion",
            "SER-001",
            "2026-02-01",
            "2027-02-01",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    tratamiento_id = conn.execute(
        """
        INSERT INTO tratamientos
        (campana_id, cultivo_id, fecha_inicio, fecha_fin, producto_id,
         aplicador_id, equipo_aplicacion_id, plaga_motivo, dosis, caldo,
         superficie_tratada, plazo_seguridad, eficacia, observaciones,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            cultivo_id,
            "2026-03-10",
            "2026-03-10",
            producto_id,
            aplicador_id,
            equipo_id,
            "Repilo",
            "2 l/ha",
            400,
            4.5,
            "14 dias",
            "B",
            "Tratamiento prueba v7.6",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO tratamiento_parcelas
        (tratamiento_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (tratamiento_id, parcela_id, 4.5, ahora, ahora),
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
            tratamiento_id,
            "receta",
            "receta_prueba_v7_6.pdf",
            "receta_prueba_v7_6.pdf",
            "recetas/prueba_v7_6.pdf",
            "pdf",
            "application/pdf",
            0,
            "",
            1,
            ahora,
            ahora,
        ),
    )
    fertilizacion_id = conn.execute(
        """
        INSERT INTO fertilizaciones
        (campana_id, cultivo_id, fecha, producto, tipo_fertilizante, cantidad,
         unidad, unidad_normalizada, superficie, codigo_actuacion_siex,
         observaciones, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            cultivo_id,
            "2026-04-01",
            "Abono prueba",
            "Mineral",
            250,
            "kg",
            "kg",
            4.5,
            "FERT-001",
            "Fertilizacion prueba v7.6",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO fertilizacion_parcelas
        (fertilizacion_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (fertilizacion_id, parcela_id, 4.5, ahora, ahora),
    )
    practica_id = conn.execute(
        """
        INSERT INTO practicas_culturales
        (campana_id, cultivo_id, fecha, labor, codigo_actuacion_siex,
         superficie, maquinaria_id, proveedor_id, observaciones, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            cultivo_id,
            "2026-05-01",
            "Poda",
            "LAB-001",
            4.5,
            maquinaria_id,
            proveedor_id,
            "Practica prueba v7.6",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO practicas_culturales_parcelas
        (practica_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (practica_id, parcela_id, 4.5, ahora, ahora),
    )
    cosecha_id = conn.execute(
        """
        INSERT INTO cosecha
        (campana_id, cultivo_id, fecha, cantidad, unidad, destino, cliente_id,
         observaciones, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            cultivo_id,
            "2026-09-01",
            1200,
            "kg",
            "Cooperativa",
            cliente_id,
            "Cosecha prueba v7.6",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO cosecha_parcelas
        (cosecha_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (cosecha_id, parcela_id, 4.5, ahora, ahora),
    )
    ingreso_id = conn.execute(
        """
        INSERT INTO movimientos_economicos
        (campana_id, cultivo_id, fecha, tipo, categoria, concepto,
         numero_factura, cliente_id, proveedor_id, base_imponible, iva,
         retencion, total, pendiente, fecha_pago, observaciones, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            cultivo_id,
            "2026-10-01",
            "Ingreso",
            "Venta",
            "Venta almendra",
            "FV-001",
            cliente_id,
            None,
            1000,
            210,
            0,
            1210,
            0,
            "2026-10-15",
            "Ingreso prueba v7.6",
            ahora,
            ahora,
        ),
    ).lastrowid
    gasto_id = conn.execute(
        """
        INSERT INTO movimientos_economicos
        (campana_id, cultivo_id, fecha, tipo, categoria, concepto,
         numero_factura, cliente_id, proveedor_id, base_imponible, iva,
         retencion, total, pendiente, fecha_pago, observaciones, created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            cultivo_id,
            "2026-04-15",
            "Gasto",
            "Insumos",
            "Compra fertilizante",
            "FC-001",
            None,
            proveedor_id,
            300,
            63,
            0,
            363,
            1,
            "",
            "Gasto prueba v7.6",
            ahora,
            ahora,
        ),
    ).lastrowid

    for movimiento_id, descripcion, base, tipo_iva in [
        (ingreso_id, "Venta almendra", 1000, 21),
        (gasto_id, "Compra fertilizante", 300, 21),
    ]:

        conn.execute(
            """
            INSERT INTO movimientos_economicos_lineas_iva
            (movimiento_id, descripcion, base_imponible, tipo_iva, cuota_iva,
             total_linea, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                movimiento_id,
                descripcion,
                base,
                tipo_iva,
                round(base * tipo_iva / 100, 2),
                round(base + (base * tipo_iva / 100), 2),
                ahora,
                ahora,
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
            ingreso_id,
            "factura",
            "factura_prueba_v7_6.pdf",
            "factura_prueba_v7_6.pdf",
            "facturas/prueba_v7_6.pdf",
            "pdf",
            "application/pdf",
            0,
            "",
            1,
            ahora,
            ahora,
        ),
    )
    conn.commit()
    return campana_id


def _validar_informes(conn, campana_id):

    datos = cargar_datos_informes(conn, campana_id)

    esperados = {
        "movimientos": "Venta almendra",
        "tratamientos": "Repilo",
        "fertilizaciones": "Abono prueba",
        "practicas": "Poda",
        "cosechas": "Cooperativa",
    }

    for clave, texto in esperados.items():

        dataframe = datos[clave]

        if dataframe.empty:

            raise AssertionError(f"Informes sin datos en {clave}")

        contenido = " ".join(str(valor) for valor in dataframe.stack().tolist())

        if texto not in contenido:

            raise AssertionError(f"Informes no resuelven {clave}: {texto}")

    return datos


def _validar_excel(campana_id):

    original_conectar = exportacion_siex.conectar
    exportacion_siex.conectar = _conectar_v7

    try:

        contenido, nombre = exportacion_siex.generar_excel_asistido_siex(
            campana_id=campana_id,
        )

    finally:

        exportacion_siex.conectar = original_conectar

    if not contenido or len(contenido) < 1024:

        raise AssertionError("Excel SIEX v7 vacio o demasiado pequeno")

    if not nombre.endswith(".xlsx"):

        raise AssertionError("Nombre de Excel SIEX invalido")

    with _conectar_v7() as conn:

        hojas = {
            "Tratamientos": exportacion_siex.obtener_dataframe_tratamientos(
                conn,
                campana_id,
            ),
            "Fertilizacion": exportacion_siex.obtener_dataframe_fertilizacion(
                conn,
                campana_id,
            ),
            "Practicas": exportacion_siex.obtener_dataframe_practicas(
                conn,
                campana_id,
            ),
            "Cosecha": exportacion_siex.obtener_dataframe_cosecha(
                conn,
                campana_id,
            ),
        }

    for nombre_hoja, dataframe in hojas.items():

        if dataframe.empty:

            raise AssertionError(f"Excel SIEX sin datos en {nombre_hoja}")

    return nombre, len(contenido)


def _validar_pdf(campana_id):

    original_conectar = cuadernopro_pdf.conectar
    original_leer = cuadernopro_pdf.leer
    original_exports = cuadernopro_pdf.EXPORTS_DIR
    original_docs = cuadernopro_pdf.DOCS_DIR
    cuadernopro_pdf.conectar = _conectar_v7
    cuadernopro_pdf.leer = _leer_v7
    cuadernopro_pdf.EXPORTS_DIR = APP_ROOT / "runtime" / "v7" / "exports"
    cuadernopro_pdf.DOCS_DIR = APP_ROOT / "runtime" / "v7" / "documentos"

    try:

        ruta_pdf = Path(cuadernopro_pdf.generar_cuadernopro_pdf(campana_id))

    finally:

        cuadernopro_pdf.conectar = original_conectar
        cuadernopro_pdf.leer = original_leer
        cuadernopro_pdf.EXPORTS_DIR = original_exports
        cuadernopro_pdf.DOCS_DIR = original_docs

    if not ruta_pdf.exists() or ruta_pdf.stat().st_size <= 0:

        raise AssertionError("PDF oficial v7 no se ha generado correctamente")

    return ruta_pdf


def main():

    crear_base_v7(DB_V7, sobrescribir=True)

    with _conectar_v7() as conn:

        _validar_sin_legacy(conn)
        campana_id = _insertar_datos(conn)
        _validar_sin_legacy(conn)
        datos_informes = _validar_informes(conn, campana_id)

    excel_nombre, excel_bytes = _validar_excel(campana_id)
    ruta_pdf = _validar_pdf(campana_id)

    print("Prueba salidas v7")
    print("=================")
    print(f"Base v7: {DB_V7}")
    print(f"Campana prueba: {campana_id}")
    print(
        "Informes: OK "
        f"({', '.join(clave for clave in datos_informes if clave != 'avisos')})"
    )
    print(f"Excel SIEX: OK ({excel_nombre}, {excel_bytes} bytes)")
    print(f"PDF oficial: OK ({ruta_pdf})")
    print("Legacy detectado: ninguno")
    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
