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

from modules.contabilidad import (  # noqa: E402
    _columnas_tabla_conn,
    _insertar_movimiento_compatible,
    _leer_movimientos_contabilidad,
    _resolver_tercero_movimiento,
)


LEGACY_MOVIMIENTOS_PROHIBIDAS = {
    "tercero",
    "nif_tercero",
    "cultivo",
}


def _conectar_v7():

    if not DB_V7.exists():

        raise FileNotFoundError(
            "No existe la base v7 de prueba. Ejecuta primero "
            "`./venv/bin/python scripts/crear_base_v7.py "
            "runtime/v7/cuadernopro_v7_limpia.db`."
        )

    conn = sqlite3.connect(DB_V7)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _validar_columnas_limpias(conn):

    columnas = _columnas_tabla_conn(conn, "movimientos_economicos")
    faltan = {
        "campana_id",
        "cultivo_id",
        "cliente_id",
        "proveedor_id",
        "fecha",
        "tipo",
        "categoria",
        "concepto",
        "numero_factura",
        "base_imponible",
        "iva",
        "retencion",
        "total",
        "pendiente",
        "fecha_pago",
        "observaciones",
    } - columnas
    legacy = LEGACY_MOVIMIENTOS_PROHIBIDAS & columnas

    if faltan:

        raise AssertionError(
            "Faltan columnas limpias en movimientos_economicos: "
            + ", ".join(sorted(faltan))
        )

    if legacy:

        raise AssertionError(
            "Columnas legacy detectadas en movimientos_economicos v7: "
            + ", ".join(sorted(legacy))
        )

    if not _columnas_tabla_conn(conn, "movimientos_economicos_lineas_iva"):

        raise AssertionError("No existe movimientos_economicos_lineas_iva")

    if not _columnas_tabla_conn(conn, "movimientos_economicos_documentos"):

        raise AssertionError("No existe movimientos_economicos_documentos")


def _insertar_datos_minimos(conn):

    marca = datetime.now().strftime("%Y%m%d%H%M%S%f")
    campana_id = conn.execute(
        """
        INSERT INTO campanas
        (nombre, fecha_inicio, fecha_fin, activa, estado)
        VALUES (?,?,?,?,?)
        """,
        (
            f"Prueba v7.4 {marca}",
            "2026-01-01",
            "2026-12-31",
            1,
            "abierta",
        ),
    ).lastrowid
    cultivo_id = conn.execute(
        """
        INSERT INTO cultivos
        (campana_id, nombre, variedad, codigo_siex, superficie, activo)
        VALUES (?,?,?,?,?,?)
        """,
        (campana_id, "ALMENDRO", "Guara", "104", 4.5, 1),
    ).lastrowid
    cliente_id = conn.execute(
        """
        INSERT INTO clientes
        (nombre, nif, activo)
        VALUES (?,?,?)
        """,
        (f"Cliente prueba v7.4 {marca}", f"CLI{marca[-8:]}", 1),
    ).lastrowid
    proveedor_id = conn.execute(
        """
        INSERT INTO proveedores
        (nombre, nif, actividad, activo)
        VALUES (?,?,?,?)
        """,
        (
            f"Proveedor prueba v7.4 {marca}",
            f"PRO{marca[-8:]}",
            "Suministros",
            1,
        ),
    ).lastrowid

    return campana_id, cultivo_id, cliente_id, proveedor_id


def _insertar_linea_iva(conn, movimiento_id, descripcion, base, tipo_iva):

    cuota = round(float(base) * float(tipo_iva) / 100, 2)
    total = round(float(base) + cuota, 2)
    ahora = datetime.now().isoformat()
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
            cuota,
            total,
            ahora,
            ahora,
        ),
    )


def _insertar_documento_simulado(conn, movimiento_id):

    ahora = datetime.now().isoformat()
    conn.execute(
        """
        INSERT INTO movimientos_economicos_documentos
        (movimiento_id, tipo_documento, nombre_original, nombre_guardado,
         ruta_relativa, extension, mime_type, size_bytes, sha256, orden,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            movimiento_id,
            "factura",
            "factura_prueba_v7_4.pdf",
            f"factura_prueba_v7_4_{movimiento_id}.pdf",
            f"facturas/prueba_v7_4_{movimiento_id}.pdf",
            "pdf",
            "application/pdf",
            0,
            "",
            1,
            ahora,
            ahora,
        ),
    )


def _resolver_movimientos(movimientos):

    if movimientos.empty:

        return movimientos

    return pd.concat(
        [
            movimientos,
            movimientos.apply(_resolver_tercero_movimiento, axis=1),
        ],
        axis=1,
    )


def _validar_movimiento(fila, tipo, tercero_esperado):

    errores = []

    if str(fila["tipo"]) != tipo:

        errores.append(f"tipo incorrecto para {tipo}")

    if "ALMENDRO" not in str(fila["cultivo"]).upper():

        errores.append(f"cultivo no resuelto para {tipo}")

    if tercero_esperado not in str(fila["tercero_resuelto"]):

        errores.append(f"tercero no resuelto para {tipo}")

    if int(fila["facturas_count"]) != 1:

        errores.append(f"factura simulada no resuelta para {tipo}")

    if float(fila["iva_importe"]) <= 0:

        errores.append(f"iva no leido para {tipo}")

    if errores:

        raise AssertionError("; ".join(errores))


def main():

    try:

        with _conectar_v7() as conn:

            _validar_columnas_limpias(conn)
            campana_id, cultivo_id, cliente_id, proveedor_id = (
                _insertar_datos_minimos(conn)
            )
            ingreso_id = _insertar_movimiento_compatible(
                conn,
                {
                    "campana_id": campana_id,
                    "cultivo_id": cultivo_id,
                    "fecha": "2026-07-01",
                    "tipo": "Ingreso",
                    "categoria": "Venta de cosecha",
                    "concepto": "Ingreso prueba v7.4",
                    "numero_factura": "FV-74-1",
                    "cliente_id": cliente_id,
                    "proveedor_id": proveedor_id,
                    "base_imponible": 1000.0,
                    "iva_porcentaje": 10.0,
                    "iva_importe": 100.0,
                    "retencion": 0.0,
                    "total": 1100.0,
                    "pagado": False,
                    "pendiente": 1,
                    "fecha_pago": "",
                    "tercero": "NO_DEBE_GUARDARSE",
                    "nif_tercero": "NO_DEBE_GUARDARSE",
                    "cultivo": "NO_DEBE_GUARDARSE",
                    "observaciones": "Prueba ingreso v7.4",
                },
            )
            gasto_id = _insertar_movimiento_compatible(
                conn,
                {
                    "campana_id": campana_id,
                    "cultivo_id": cultivo_id,
                    "fecha": "2026-07-02",
                    "tipo": "Gasto",
                    "categoria": "Fertilizantes",
                    "concepto": "Gasto prueba v7.4",
                    "numero_factura": "FR-74-1",
                    "cliente_id": cliente_id,
                    "proveedor_id": proveedor_id,
                    "base_imponible": 500.0,
                    "iva_porcentaje": 21.0,
                    "iva_importe": 105.0,
                    "retencion": 0.0,
                    "total": 605.0,
                    "pagado": True,
                    "pendiente": 0,
                    "fecha_pago": "2026-07-03",
                    "tercero": "NO_DEBE_GUARDARSE",
                    "nif_tercero": "NO_DEBE_GUARDARSE",
                    "cultivo": "NO_DEBE_GUARDARSE",
                    "observaciones": "Prueba gasto v7.4",
                },
            )

            _insertar_linea_iva(conn, ingreso_id, "Venta", 1000.0, 10.0)
            _insertar_linea_iva(conn, gasto_id, "Compra", 500.0, 21.0)
            _insertar_documento_simulado(conn, ingreso_id)
            _insertar_documento_simulado(conn, gasto_id)
            conn.commit()

            ingreso = _resolver_movimientos(
                _leer_movimientos_contabilidad(conn=conn, movimiento_id=ingreso_id)
            )
            gasto = _resolver_movimientos(
                _leer_movimientos_contabilidad(conn=conn, movimiento_id=gasto_id)
            )

            if ingreso.empty:

                raise AssertionError("No se pudo leer el ingreso insertado")

            if gasto.empty:

                raise AssertionError("No se pudo leer el gasto insertado")

            _validar_movimiento(
                ingreso.iloc[0],
                "Ingreso",
                "Cliente prueba v7.4",
            )
            _validar_movimiento(
                gasto.iloc[0],
                "Gasto",
                "Proveedor prueba v7.4",
            )

            lineas_iva = conn.execute(
                """
                SELECT COUNT(*)
                FROM movimientos_economicos_lineas_iva
                WHERE movimiento_id IN (?,?)
                """,
                (ingreso_id, gasto_id),
            ).fetchone()[0]

            if int(lineas_iva) != 2:

                raise AssertionError("No se insertaron las lineas de IVA")

    except Exception as exc:

        print(f"Resultado: ERROR - {exc}", file=sys.stderr)
        return 1

    print("Prueba contabilidad v7")
    print("======================")
    print(f"Base: {DB_V7}")
    print(f"Ingreso insertado: {ingreso_id}")
    print(f"Gasto insertado: {gasto_id}")
    print("Columnas legacy usadas: ninguna")
    print("Lectura cliente/proveedor/cultivo/IVA/facturas: OK")
    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
