#!/usr/bin/env python3
from pathlib import Path
import sqlite3
import sys

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = APP_ROOT / "runtime" / "tests"
DB_PRUEBA = RUNTIME_DIR / "prueba_campanas_activacion_v8.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.campanas import (  # noqa: E402
    activar_campana,
    desactivar_campanas,
    obtener_campana_activa,
    validar_unica_campana_activa,
)
from core.db import crear_tablas  # noqa: E402
from modules.campanas import (  # noqa: E402
    _etiqueta_campana,
    _formatear_fechas_campanas_para_ui,
)


def _limpiar_db():

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    for ruta in (
        DB_PRUEBA,
        DB_PRUEBA.with_name(f"{DB_PRUEBA.name}-wal"),
        DB_PRUEBA.with_name(f"{DB_PRUEBA.name}-shm"),
    ):

        if ruta.exists():

            ruta.unlink()

    crear_tablas(DB_PRUEBA)


def _insertar_campanas(conn):

    datos = [
        ("2023/2024", "2023-10-01", "2024-09-30"),
        ("2024/2025", "2024-10-01", "2025-09-30"),
        ("2025/2026", "2025-10-01", "2026-09-30"),
    ]
    ids = []

    for nombre, inicio, fin in datos:

        ids.append(
            conn.execute(
                """
                INSERT INTO campanas
                (nombre, fecha_inicio, fecha_fin, activa, estado)
                VALUES (?,?,?,?,?)
                """,
                (nombre, inicio, fin, 0, "abierta"),
            ).lastrowid
        )

    conn.commit()
    return ids


def _estado_activa(conn):

    return {
        int(fila[0]): int(fila[1])
        for fila in conn.execute(
            """
            SELECT id,activa
            FROM campanas
            ORDER BY id
            """
        )
    }


def _assert_unica_activa(conn, esperado_id):

    estado = _estado_activa(conn)

    if not validar_unica_campana_activa(conn):

        raise AssertionError(f"Hay mas de una campana activa: {estado!r}")

    activas = [
        campana_id
        for campana_id, activa in estado.items()
        if activa == 1
    ]

    if esperado_id is None:

        if activas:

            raise AssertionError(f"No se esperaban activas: {estado!r}")

    elif activas != [esperado_id]:

        raise AssertionError(
            f"Activa esperada {esperado_id}; estado real {estado!r}"
        )

    activa = obtener_campana_activa(conn)

    if esperado_id is None and activa is not None:

        raise AssertionError(f"obtener_campana_activa inesperada: {activa!r}")

    if esperado_id is not None and int(activa["id"]) != int(esperado_id):

        raise AssertionError(f"Campana activa inesperada: {activa!r}")


def _assert_total_campanas(conn, esperado):

    total = conn.execute("SELECT COUNT(*) FROM campanas").fetchone()[0]

    if int(total) != int(esperado):

        raise AssertionError(f"Campanas esperadas {esperado}; hay {total}")


def _validar_formato_fechas_ui():

    campana = {
        "nombre": "2025/2026",
        "fecha_inicio": "2025-10-01",
        "fecha_fin": "2026-09-30",
    }
    etiqueta = _etiqueta_campana(campana)
    esperada = "2025/2026 (01/10/2025 - 30/09/2026)"

    if etiqueta != esperada:

        raise AssertionError(f"Etiqueta inesperada: {etiqueta!r}")

    prohibidos = ["2025-10-01", "2026-09-30", "00:00:00", "Timestamp"]

    for texto in prohibidos:

        if texto in etiqueta:

            raise AssertionError(f"Etiqueta contiene valor tecnico {texto!r}")

    datos = pd.DataFrame([
        {
            "nombre": "2024/2025",
            "fecha_inicio": pd.Timestamp("2024-10-01 00:00:00"),
            "fecha_fin": pd.Timestamp("2025-09-30 00:00:00"),
            "activa": 0,
        }
    ])
    visual = _formatear_fechas_campanas_para_ui(datos)

    if visual.loc[0, "fecha_inicio"] != "01/10/2024":

        raise AssertionError(
            f"Fecha inicio visual inesperada: {visual.loc[0, 'fecha_inicio']!r}"
        )

    if visual.loc[0, "fecha_fin"] != "30/09/2025":

        raise AssertionError(
            f"Fecha fin visual inesperada: {visual.loc[0, 'fecha_fin']!r}"
        )

    texto_visual = " ".join(
        str(valor)
        for valor in visual.loc[0, ["fecha_inicio", "fecha_fin"]].tolist()
    )

    for texto in ["2024-10-01", "2025-09-30", "00:00:00", "NaT", "nan"]:

        if texto in texto_visual:

            raise AssertionError(f"Tabla visual contiene valor tecnico {texto!r}")


def main():

    _limpiar_db()
    _validar_formato_fechas_ui()

    with sqlite3.connect(DB_PRUEBA) as conn:

        conn.execute("PRAGMA foreign_keys=ON")
        campana_a, campana_b, campana_c = _insertar_campanas(conn)

        activar_campana(conn, campana_a)
        _assert_unica_activa(conn, campana_a)

        activar_campana(conn, campana_b)
        _assert_unica_activa(conn, campana_b)

        estado_antes_error = _estado_activa(conn)

        try:

            activar_campana(conn, 999999)

        except ValueError:

            pass

        else:

            raise AssertionError("Activar campana inexistente no fallo")

        estado_despues_error = _estado_activa(conn)

        if estado_despues_error != estado_antes_error:

            raise AssertionError(
                "La activacion fallida dejo la base inconsistente: "
                f"{estado_despues_error!r}"
            )

        _assert_unica_activa(conn, campana_b)

        desactivar_campanas(conn)
        _assert_unica_activa(conn, None)
        _assert_total_campanas(conn, 3)

        if campana_c not in _estado_activa(conn):

            raise AssertionError("La campana C ha desaparecido")

    print("Campanas activacion v8.4.5: OK")
    print(f"Base: {DB_PRUEBA}")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
