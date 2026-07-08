#!/usr/bin/env python3
from pathlib import Path
import argparse
import sqlite3
import sys


APP_ROOT = Path(__file__).resolve().parents[1]

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.fechas import detectar_campana_por_fecha  # noqa: E402


def _resolver_ruta(ruta_db):

    ruta = Path(ruta_db).expanduser()

    if not ruta.is_absolute():

        ruta = APP_ROOT / ruta

    return ruta.resolve()


def _tabla_existe(conn, tabla):

    return conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (tabla,),
    ).fetchone() is not None


def _columnas(conn, tabla):

    if not _tabla_existe(conn, tabla):

        return set()

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _campanas_por_id(conn):

    if not _tabla_existe(conn, "campanas"):

        return {}

    return {
        int(fila[0]): {
            "id": int(fila[0]),
            "nombre": fila[1],
            "fecha_inicio": fila[2],
            "fecha_fin": fila[3],
        }
        for fila in conn.execute(
            """
            SELECT id,nombre,fecha_inicio,fecha_fin
            FROM campanas
            ORDER BY id
            """
        )
    }


def _leer_movimientos(conn):

    columnas = _columnas(conn, "movimientos_economicos")

    if not columnas:

        raise RuntimeError("No existe la tabla movimientos_economicos")

    faltantes = {"id", "fecha", "campana_id"} - columnas

    if faltantes:

        raise RuntimeError(
            "Faltan columnas en movimientos_economicos: "
            + ", ".join(sorted(faltantes))
        )

    expr_tipo = "tipo" if "tipo" in columnas else "''"
    expr_concepto = "concepto" if "concepto" in columnas else "''"

    return conn.execute(
        f"""
        SELECT id,fecha,campana_id,{expr_tipo} AS tipo,{expr_concepto} AS concepto
        FROM movimientos_economicos
        ORDER BY fecha,id
        """
    ).fetchall()


def diagnosticar(ruta_db):

    conn = sqlite3.connect(ruta_db)
    conn.execute("PRAGMA foreign_keys=ON")

    try:

        campanas = _campanas_por_id(conn)
        movimientos = _leer_movimientos(conn)
        diferencias = []
        sin_campana_por_fecha = []

        for movimiento in movimientos:

            movimiento_id = int(movimiento[0])
            fecha = movimiento[1]
            campana_guardada_id = (
                int(movimiento[2])
                if movimiento[2] is not None
                else None
            )
            campana_esperada = detectar_campana_por_fecha(fecha, conn=conn)

            if campana_esperada is None:

                sin_campana_por_fecha.append(movimiento)
                continue

            if campana_guardada_id != int(campana_esperada["id"]):

                diferencias.append(
                    {
                        "id": movimiento_id,
                        "fecha": fecha,
                        "tipo": movimiento[3],
                        "concepto": movimiento[4],
                        "guardada": campanas.get(campana_guardada_id),
                        "esperada": campana_esperada,
                    }
                )

        print("Diagnostico contabilidad/campañas v8")
        print("====================================")
        print(f"Base revisada: {ruta_db}")
        print(f"Movimientos revisados: {len(movimientos)}")
        print(f"Diferencias detectadas: {len(diferencias)}")
        print(f"Fechas sin campaña configurada: {len(sin_campana_por_fecha)}")

        if diferencias:

            print("")
            print("| ID | Fecha | Tipo | Concepto | Campaña guardada | Campaña esperada |")
            print("| ---: | --- | --- | --- | --- | --- |")

            for diferencia in diferencias:

                guardada = diferencia["guardada"] or {}
                esperada = diferencia["esperada"] or {}
                print(
                    "| "
                    f"{diferencia['id']} | "
                    f"{diferencia['fecha']} | "
                    f"{diferencia['tipo']} | "
                    f"{diferencia['concepto']} | "
                    f"{guardada.get('nombre', 'Sin campaña')} | "
                    f"{esperada.get('nombre', 'Sin campaña')} |"
                )

        if sin_campana_por_fecha:

            print("")
            print(
                "Hay movimientos cuya fecha no pertenece a ninguna campaña "
                "configurada. No se consideran diferencia si usan el fallback "
                "de campaña activa."
            )

        if diferencias:

            print("")
            print("Resultado: diferencias detectadas")
            return 1

        print("")
        print("Resultado: OK")
        return 0

    finally:

        conn.close()


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Detecta movimientos economicos cuya fecha pertenece a una "
            "campaña distinta de la guardada en campana_id."
        )
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Ruta de la base SQLite a revisar",
    )
    args = parser.parse_args()
    ruta_db = _resolver_ruta(args.db)

    if not ruta_db.exists():

        print(f"ERROR: no existe la base indicada: {ruta_db}", file=sys.stderr)
        return 2

    try:

        return diagnosticar(ruta_db)

    except Exception as exc:

        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":

    raise SystemExit(main())
