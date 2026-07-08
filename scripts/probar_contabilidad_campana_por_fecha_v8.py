#!/usr/bin/env python3
from pathlib import Path
import sqlite3
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
DB_PRUEBA = APP_ROOT / "runtime" / "v8" / "prueba_contabilidad_campana_fecha_v8.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.fechas import detectar_campana_por_fecha  # noqa: E402
from core.schema_v7 import crear_base_v7  # noqa: E402
from modules.contabilidad import (  # noqa: E402
    _actualizar_movimiento_compatible,
    _insertar_movimiento_compatible,
    _leer_resumen_contabilidad,
    _resolver_campana_movimiento_por_fecha,
)
from modules.informes import cargar_datos_informes  # noqa: E402


def _assert_igual(actual, esperado, campo):

    if actual != esperado:

        raise AssertionError(
            f"{campo}: esperado {esperado!r}, obtenido {actual!r}"
        )


def _assert_float(actual, esperado, campo):

    if abs(float(actual or 0) - float(esperado)) > 0.0001:

        raise AssertionError(
            f"{campo}: esperado {esperado!r}, obtenido {actual!r}"
        )


def _fila(conn, tabla, registro_id):

    fila = conn.execute(
        f'SELECT * FROM "{tabla}" WHERE id=?',
        (int(registro_id),),
    ).fetchone()

    if fila is None:

        raise AssertionError(f"No existe {tabla}.id={registro_id}")

    return dict(fila)


def _crear_base():

    crear_base_v7(DB_PRUEBA, sobrescribir=True)
    conn = sqlite3.connect(DB_PRUEBA)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _insertar_campanas(conn):

    campana_2024 = conn.execute(
        """
        INSERT INTO campanas
        (nombre,fecha_inicio,fecha_fin,activa,estado)
        VALUES (?,?,?,?,?)
        """,
        ("2024/2025", "2024-10-01", "2025-09-30", 0, "abierta"),
    ).lastrowid
    campana_2025 = conn.execute(
        """
        INSERT INTO campanas
        (nombre,fecha_inicio,fecha_fin,activa,estado)
        VALUES (?,?,?,?,?)
        """,
        ("2025/2026", "2025-10-01", "2026-09-30", 1, "abierta"),
    ).lastrowid
    conn.commit()
    return int(campana_2024), int(campana_2025)


def _insertar_movimiento_por_fecha(
    conn,
    campana_activa_id,
    fecha,
    tipo,
    concepto,
    total,
):

    resolucion = _resolver_campana_movimiento_por_fecha(
        fecha,
        campana_activa_id,
        conn=conn,
    )
    campana_id = resolucion["campana_id"]

    if campana_id is None:

        raise AssertionError("La resolucion de campaña no devolvio campana_id")

    movimiento_id = _insertar_movimiento_compatible(
        conn,
        {
            "campana_id": campana_id,
            "fecha": fecha,
            "tipo": tipo,
            "categoria": "Prueba",
            "concepto": concepto,
            "numero_factura": "",
            "base_imponible": total,
            "iva_importe": 0.0,
            "retencion": 0.0,
            "total": total,
            "pagado": True,
            "fecha_pago": fecha,
            "observaciones": "",
        },
    )
    return movimiento_id, resolucion


def _ids_informe(conn, campana_id):

    datos = cargar_datos_informes(conn, campana_id)
    movimientos = datos["movimientos"]

    if movimientos.empty:

        return set()

    return set(movimientos["id"].astype(int).tolist())


def _validar_altas_y_balances(conn, campana_2024, campana_2025):

    movimiento_antiguo_id, resolucion_antiguo = _insertar_movimiento_por_fecha(
        conn,
        campana_2025,
        "2025-03-15",
        "Ingreso",
        "Ingreso campaña anterior",
        1000.0,
    )
    movimiento_actual_id, resolucion_actual = _insertar_movimiento_por_fecha(
        conn,
        campana_2025,
        "2026-02-10",
        "Gasto",
        "Gasto campaña activa",
        200.0,
    )
    movimiento_fuera_id, resolucion_fuera = _insertar_movimiento_por_fecha(
        conn,
        campana_2025,
        "2023-01-15",
        "Gasto",
        "Gasto fuera de campañas",
        50.0,
    )
    conn.commit()

    _assert_igual(
        detectar_campana_por_fecha("2025-03-15", conn=conn)["id"],
        campana_2024,
        "helper fecha 2025-03-15",
    )
    _assert_igual(
        detectar_campana_por_fecha("2026-02-10", conn=conn)["id"],
        campana_2025,
        "helper fecha 2026-02-10",
    )
    _assert_igual(
        detectar_campana_por_fecha("2023-01-15", conn=conn),
        None,
        "helper fecha fuera de campañas",
    )

    movimiento_antiguo = _fila(
        conn,
        "movimientos_economicos",
        movimiento_antiguo_id,
    )
    movimiento_actual = _fila(
        conn,
        "movimientos_economicos",
        movimiento_actual_id,
    )
    movimiento_fuera = _fila(
        conn,
        "movimientos_economicos",
        movimiento_fuera_id,
    )

    _assert_igual(
        movimiento_antiguo["campana_id"],
        campana_2024,
        "movimiento antiguo por fecha",
    )
    _assert_igual(
        movimiento_actual["campana_id"],
        campana_2025,
        "movimiento actual por fecha",
    )
    _assert_igual(
        movimiento_fuera["campana_id"],
        campana_2025,
        "fallback campaña activa",
    )
    _assert_igual(
        resolucion_fuera["estado"],
        "fallback_activa",
        "estado fallback fecha sin campaña",
    )
    _assert_igual(
        resolucion_fuera["mensaje"],
        (
            "La fecha no pertenece a ninguna campaña configurada. "
            "Se usará la campaña activa."
        ),
        "mensaje fallback fecha sin campaña",
    )
    _assert_igual(
        resolucion_antiguo["campana_id"],
        campana_2024,
        "resolucion alta antigua",
    )
    _assert_igual(
        resolucion_actual["campana_id"],
        campana_2025,
        "resolucion alta actual",
    )

    resumen_2024 = _leer_resumen_contabilidad(campana_2024, conn=conn)
    resumen_2025 = _leer_resumen_contabilidad(campana_2025, conn=conn)
    _assert_float(resumen_2024["ingresos"], 1000.0, "ingresos 2024/2025")
    _assert_float(resumen_2024["gastos"], 0.0, "gastos 2024/2025")
    _assert_float(resumen_2025["ingresos"], 0.0, "ingresos 2025/2026")
    _assert_float(resumen_2025["gastos"], 250.0, "gastos 2025/2026")

    _assert_igual(
        _ids_informe(conn, campana_2024),
        {movimiento_antiguo_id},
        "informe movimientos 2024/2025",
    )
    _assert_igual(
        _ids_informe(conn, campana_2025),
        {movimiento_actual_id, movimiento_fuera_id},
        "informe movimientos 2025/2026",
    )

    return movimiento_antiguo_id, movimiento_actual_id, movimiento_fuera_id


def _validar_edicion(conn, campana_2024, campana_2025, movimiento_antiguo_id):

    _actualizar_movimiento_compatible(
        conn,
        movimiento_antiguo_id,
        {
            "concepto": "Ingreso editado sin cambiar fecha",
            "base_imponible": 1100.0,
            "iva_importe": 0.0,
            "retencion": 0.0,
            "total": 1100.0,
        },
    )
    conn.commit()
    movimiento = _fila(conn, "movimientos_economicos", movimiento_antiguo_id)
    _assert_igual(
        movimiento["campana_id"],
        campana_2024,
        "edicion importe no cambia campaña",
    )

    nueva_fecha = "2026-03-20"
    resolucion = _resolver_campana_movimiento_por_fecha(
        nueva_fecha,
        campana_2025,
        conn=conn,
    )
    _actualizar_movimiento_compatible(
        conn,
        movimiento_antiguo_id,
        {
            "campana_id": resolucion["campana_id"],
            "fecha": nueva_fecha,
        },
    )
    conn.commit()
    movimiento = _fila(conn, "movimientos_economicos", movimiento_antiguo_id)
    _assert_igual(
        movimiento["campana_id"],
        campana_2025,
        "edicion fecha cambia campaña",
    )

    resumen_2024 = _leer_resumen_contabilidad(campana_2024, conn=conn)
    resumen_2025 = _leer_resumen_contabilidad(campana_2025, conn=conn)
    _assert_float(
        resumen_2024["ingresos"],
        0.0,
        "ingresos 2024/2025 tras editar fecha",
    )
    _assert_float(
        resumen_2025["ingresos"],
        1100.0,
        "ingresos 2025/2026 tras editar fecha",
    )

    ids_2024 = _ids_informe(conn, campana_2024)
    ids_2025 = _ids_informe(conn, campana_2025)
    _assert_igual(
        movimiento_antiguo_id in ids_2024,
        False,
        "informe 2024 sin movimiento reubicado",
    )
    _assert_igual(
        movimiento_antiguo_id in ids_2025,
        True,
        "informe 2025 con movimiento reubicado",
    )


def main():

    print("Prueba contabilidad campaña por fecha v8")
    print("========================================")
    print(f"Base de prueba: {DB_PRUEBA}")

    try:

        conn = _crear_base()

        try:

            campana_2024, campana_2025 = _insertar_campanas(conn)
            movimiento_antiguo_id, _, _ = _validar_altas_y_balances(
                conn,
                campana_2024,
                campana_2025,
            )
            _validar_edicion(
                conn,
                campana_2024,
                campana_2025,
                movimiento_antiguo_id,
            )

        finally:

            conn.close()

    except Exception as exc:

        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
