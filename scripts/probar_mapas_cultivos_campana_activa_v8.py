#!/usr/bin/env python3
from pathlib import Path
import os
import sqlite3
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = APP_ROOT / "runtime" / "tests"
DB_PRUEBA = RUNTIME_DIR / "prueba_mapas_cultivos_campana_activa_v8.db"

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_PRUEBA)

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.campanas import activar_campana, desactivar_campanas  # noqa: E402
from core.db import crear_tablas  # noqa: E402
from modules.mapas import (  # noqa: E402
    _formatear_arboles_tooltip,
    _leer_cultivos_mapa,
    construir_tooltip_parcela_mapa,
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


def _insertar_datos():

    ahora = "2026-07-08T00:00:00"

    with sqlite3.connect(DB_PRUEBA) as conn:

        conn.execute("PRAGMA foreign_keys=ON")
        campana_anterior_id = conn.execute(
            """
            INSERT INTO campanas
            (nombre, fecha_inicio, fecha_fin, activa, estado,
             observaciones, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                "2024/2025",
                "2024-10-01",
                "2025-09-30",
                0,
                "cerrada",
                "Campana anterior",
                ahora,
                ahora,
            ),
        ).lastrowid
        campana_actual_id = conn.execute(
            """
            INSERT INTO campanas
            (nombre, fecha_inicio, fecha_fin, activa, estado,
             observaciones, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                "2025/2026",
                "2025-10-01",
                "2026-09-30",
                1,
                "abierta",
                "Campana actual",
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
                "PLACAS SOLARES - 1",
                30,
                22,
                0,
                0,
                "41",
                "129",
                "1",
                17.2139,
                "TA",
                1,
                "Parcela prueba mapas",
                ahora,
                ahora,
            ),
        ).lastrowid
        cultivo_anterior_id = conn.execute(
            """
            INSERT INTO cultivos
            (campana_id, nombre, variedad, codigo_siex, superficie,
             ano_plantacion, marco_plantacion, numero_arboles, activo,
             created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                campana_anterior_id,
                "ALMENDRO",
                "GUARA",
                "104",
                17.2139,
                2018,
                "7X7",
                3513,
                1,
                ahora,
                ahora,
            ),
        ).lastrowid
        cultivo_actual_id = conn.execute(
            """
            INSERT INTO cultivos
            (campana_id, nombre, variedad, codigo_siex, superficie,
             ano_plantacion, marco_plantacion, numero_arboles, activo,
             created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                campana_actual_id,
                "ALMENDRO",
                "GUARA",
                "104",
                17.2139,
                2018,
                "7X7",
                9524,
                1,
                ahora,
                ahora,
            ),
        ).lastrowid

        for cultivo_id in [cultivo_anterior_id, cultivo_actual_id]:

            conn.execute(
                """
                INSERT INTO cultivo_parcelas
                (cultivo_id, parcela_id, superficie, created_at, updated_at)
                VALUES (?,?,?,?,?)
                """,
                (cultivo_id, parcela_id, 17.2139, ahora, ahora),
            )

        conn.commit()

    return {
        "campana_anterior_id": campana_anterior_id,
        "campana_actual_id": campana_actual_id,
        "parcela_id": parcela_id,
    }


def _cultivos_parcela():

    datos = _leer_cultivos_mapa()
    return datos.to_dict("records")


def _tooltip(cultivos):

    parcela = {
        "nombre": "PLACAS SOLARES - 1",
        "poligono": "41",
        "parcela": "129",
        "recinto": "1",
        "superficie_sigpac": 17.2139,
    }
    return construir_tooltip_parcela_mapa(parcela, cultivos)


def _assert_tooltip(cultivos, esperado, prohibido):

    tooltip = _tooltip(cultivos)

    if esperado not in tooltip:

        raise AssertionError(f"No aparece {esperado!r} en tooltip: {tooltip!r}")

    for valor in prohibido:

        if valor in tooltip:

            raise AssertionError(f"Aparece {valor!r} en tooltip: {tooltip!r}")

    if "max-width:360px" not in tooltip or "font-size:12px" not in tooltip:

        raise AssertionError(f"Tooltip no usa estilo compacto: {tooltip!r}")

    if "17,21 ha" not in tooltip:

        raise AssertionError(f"Tooltip no formatea superficie: {tooltip!r}")


def _assert_formateo_arboles():

    casos_validos = {
        9524: "9.524 árboles",
        9524.0: "9.524 árboles",
        "9524": "9.524 árboles",
        "9524.0": "9.524 árboles",
        "9.524": "9.524 árboles",
        "3.513": "3.513 árboles",
        "259": "259 árboles",
    }

    for valor, esperado in casos_validos.items():

        obtenido = _formatear_arboles_tooltip(valor)

        if obtenido != esperado:

            raise AssertionError(
                f"Formato de arboles inesperado para {valor!r}: "
                f"{obtenido!r}; esperado {esperado!r}"
            )

    for valor in [None, "", "nan", "None", "null", 0, "0"]:

        obtenido = _formatear_arboles_tooltip(valor)

        if obtenido:

            raise AssertionError(
                f"Valor de arboles invalido no debe mostrarse: "
                f"{valor!r} -> {obtenido!r}"
            )


def main():

    _limpiar_db()
    _assert_formateo_arboles()
    ctx = _insertar_datos()

    cultivos = _cultivos_parcela()

    if len(cultivos) != 1:

        raise AssertionError(f"Se esperaba 1 cultivo activo: {cultivos!r}")

    if int(cultivos[0]["arboles"]) != 9524:

        raise AssertionError(f"No se recupera cultivo activo: {cultivos!r}")

    _assert_tooltip(
        cultivos,
        "9.524 árboles",
        ["3513", "3.513", "· 9 árboles"],
    )

    with sqlite3.connect(DB_PRUEBA) as conn:

        activar_campana(conn, ctx["campana_anterior_id"])

    cultivos = _cultivos_parcela()

    if len(cultivos) != 1:

        raise AssertionError(f"Se esperaba 1 cultivo anterior: {cultivos!r}")

    if int(cultivos[0]["arboles"]) != 3513:

        raise AssertionError(f"No se recupera cultivo anterior: {cultivos!r}")

    _assert_tooltip(
        cultivos,
        "3.513 árboles",
        ["9524", "9.524", "· 3 árboles"],
    )

    with sqlite3.connect(DB_PRUEBA) as conn:

        desactivar_campanas(conn)

    cultivos = _cultivos_parcela()

    if cultivos:

        raise AssertionError(
            "Sin campana activa no deben mezclarse cultivos historicos: "
            f"{cultivos!r}"
        )

    tooltip = _tooltip(cultivos)

    if "Sin cultivo en campa" not in tooltip:

        raise AssertionError(f"Tooltip sin campana inesperado: {tooltip!r}")

    print("Mapas cultivos campana activa v8.4.6: OK")
    print(f"Base: {DB_PRUEBA}")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
