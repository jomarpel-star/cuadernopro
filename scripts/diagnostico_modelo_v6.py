#!/usr/bin/env python3
import os
from pathlib import Path
import sqlite3


APP_ROOT = Path(__file__).resolve().parents[1]


def _resolver_directorio(nombre_variable, valor_por_defecto):

    ruta = Path(os.getenv(nombre_variable, valor_por_defecto)).expanduser()

    if not ruta.is_absolute():

        ruta = APP_ROOT / ruta

    return ruta.resolve()


def _resolver_ruta_datos(nombre_variable, valor_por_defecto):

    data_dir = _resolver_directorio("CUADERNOPRO_DATA_DIR", str(APP_ROOT))
    ruta = Path(os.getenv(nombre_variable, valor_por_defecto)).expanduser()

    if not ruta.is_absolute():

        ruta = data_dir / ruta

    return ruta.resolve()


def _conectar_solo_lectura(ruta_db):

    uri = f"file:{ruta_db}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _tabla_existe(conn, tabla):

    fila = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (tabla,),
    ).fetchone()
    return fila is not None


def _columnas(conn, tabla):

    if not _tabla_existe(conn, tabla):

        return set()

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _estado_columna(conn, tabla, columna):

    return "OK" if columna in _columnas(conn, tabla) else "FALTA"


def _contar(conn, tabla, where=None):

    if not _tabla_existe(conn, tabla):

        return None

    sql = f'SELECT COUNT(*) FROM "{tabla}"'

    if where:

        sql += f" WHERE {where}"

    return int(conn.execute(sql).fetchone()[0])


def _contar_vacios(conn, tabla, columna):

    if columna not in _columnas(conn, tabla):

        return None

    return _contar(
        conn,
        tabla,
        f'"{columna}" IS NULL OR TRIM(CAST("{columna}" AS TEXT))=""',
    )


def _contar_no_vacios(conn, tabla, columna):

    total = _contar(conn, tabla)
    vacios = _contar_vacios(conn, tabla, columna)

    if total is None or vacios is None:

        return None

    return total - vacios


def _contar_cultivos_con_parcelas(conn):

    if not _tabla_existe(conn, "cultivo_parcelas"):

        return None

    return int(
        conn.execute(
            """
            SELECT COUNT(DISTINCT cultivo_id)
            FROM cultivo_parcelas
            WHERE cultivo_id IS NOT NULL
            """
        ).fetchone()[0]
    )


def _contar_texto_sin_id(conn, tabla, columna_texto, columna_id):

    columnas = _columnas(conn, tabla)

    if columna_texto not in columnas or columna_id not in columnas:

        return None

    return _contar(
        conn,
        tabla,
        f'("{columna_id}" IS NULL OR TRIM(CAST("{columna_id}" AS TEXT))="") '
        f'AND "{columna_texto}" IS NOT NULL '
        f'AND TRIM(CAST("{columna_texto}" AS TEXT))!=""',
    )


def _formatear_contador(valor):

    return "N/D" if valor is None else str(valor)


def _imprimir_estado(conn):

    print("Diagnostico modelo v6")
    print("=====================")
    print()
    print("Columnas preparadas:")
    print(f"- cultivos.campana_id: {_estado_columna(conn, 'cultivos', 'campana_id')}")
    print(f"- cultivos.codigo_siex: {_estado_columna(conn, 'cultivos', 'codigo_siex')}")
    print(f"- cultivos.superficie: {_estado_columna(conn, 'cultivos', 'superficie')}")
    print(
        "- cultivo_parcelas: "
        f"{'OK' if _tabla_existe(conn, 'cultivo_parcelas') else 'FALTA'}"
    )
    print(
        "- fertilizaciones.cultivo_id: "
        f"{_estado_columna(conn, 'fertilizaciones', 'cultivo_id')}"
    )
    print(
        "- practicas_culturales.cultivo_id: "
        f"{_estado_columna(conn, 'practicas_culturales', 'cultivo_id')}"
    )
    print(f"- cosecha.cultivo_id: {_estado_columna(conn, 'cosecha', 'cultivo_id')}")
    print()
    total_cultivos = _contar(conn, "cultivos")
    cultivos_con_parcelas = _contar_cultivos_con_parcelas(conn)
    cultivos_sin_parcelas = (
        None
        if total_cultivos is None or cultivos_con_parcelas is None
        else total_cultivos - cultivos_con_parcelas
    )
    print("Estado de cultivos:")
    print(f"- total cultivos: {_formatear_contador(total_cultivos)}")
    print(
        "- cultivos con campana_id: "
        f"{_formatear_contador(_contar_no_vacios(conn, 'cultivos', 'campana_id'))}"
    )
    print(
        "- cultivos con codigo_siex: "
        f"{_formatear_contador(_contar_no_vacios(conn, 'cultivos', 'codigo_siex'))}"
    )
    print(
        "- cultivos con superficie: "
        f"{_formatear_contador(_contar_no_vacios(conn, 'cultivos', 'superficie'))}"
    )
    print(
        "- cultivos con parcelas en cultivo_parcelas: "
        f"{_formatear_contador(cultivos_con_parcelas)}"
    )
    print(
        "- cultivos sin parcelas asociadas en cultivo_parcelas: "
        f"{_formatear_contador(cultivos_sin_parcelas)}"
    )
    print()
    print("Estado de fertilización:")
    print(
        "- total fertilizaciones: "
        f"{_formatear_contador(_contar(conn, 'fertilizaciones'))}"
    )
    print(
        "- fertilizaciones con cultivo_id: "
        f"{_formatear_contador(_contar_no_vacios(conn, 'fertilizaciones', 'cultivo_id'))}"
    )
    print(
        "- fertilizaciones sin cultivo_id: "
        f"{_formatear_contador(_contar_vacios(conn, 'fertilizaciones', 'cultivo_id'))}"
    )
    print(
        "- fertilizaciones con cultivo textual: "
        f"{_formatear_contador(_contar_no_vacios(conn, 'fertilizaciones', 'cultivo'))}"
    )
    print(
        "- fertilizaciones con cultivo textual pero sin cultivo_id: "
        f"{_formatear_contador(_contar_texto_sin_id(conn, 'fertilizaciones', 'cultivo', 'cultivo_id'))}"
    )
    print()
    print("Estado de prácticas culturales:")
    print(
        "- total prácticas culturales: "
        f"{_formatear_contador(_contar(conn, 'practicas_culturales'))}"
    )
    print(
        "- prácticas culturales con cultivo_id: "
        f"{_formatear_contador(_contar_no_vacios(conn, 'practicas_culturales', 'cultivo_id'))}"
    )
    print(
        "- prácticas culturales sin cultivo_id: "
        f"{_formatear_contador(_contar_vacios(conn, 'practicas_culturales', 'cultivo_id'))}"
    )
    print(
        "- prácticas culturales con cultivo textual: "
        f"{_formatear_contador(_contar_no_vacios(conn, 'practicas_culturales', 'cultivo'))}"
    )
    print(
        "- prácticas culturales con cultivo textual pero sin cultivo_id: "
        f"{_formatear_contador(_contar_texto_sin_id(conn, 'practicas_culturales', 'cultivo', 'cultivo_id'))}"
    )
    print()
    print("Estado de cosecha:")
    print(
        "- total cosechas: "
        f"{_formatear_contador(_contar(conn, 'cosecha'))}"
    )
    print(
        "- cosechas con cultivo_id: "
        f"{_formatear_contador(_contar_no_vacios(conn, 'cosecha', 'cultivo_id'))}"
    )
    print(
        "- cosechas sin cultivo_id: "
        f"{_formatear_contador(_contar_vacios(conn, 'cosecha', 'cultivo_id'))}"
    )
    print(
        "- cosechas con cultivo textual: "
        f"{_formatear_contador(_contar_no_vacios(conn, 'cosecha', 'cultivo'))}"
    )
    print(
        "- cosechas con cultivo textual pero sin cultivo_id: "
        f"{_formatear_contador(_contar_texto_sin_id(conn, 'cosecha', 'cultivo', 'cultivo_id'))}"
    )
    print()
    print("Registros pendientes de normalizar:")
    print(
        "- fertilizaciones con cultivo_id vacio: "
        f"{_formatear_contador(_contar_vacios(conn, 'fertilizaciones', 'cultivo_id'))}"
    )
    print(
        "- practicas_culturales con cultivo_id vacio: "
        f"{_formatear_contador(_contar_vacios(conn, 'practicas_culturales', 'cultivo_id'))}"
    )
    print(
        "- cosecha con cultivo_id vacio: "
        f"{_formatear_contador(_contar_vacios(conn, 'cosecha', 'cultivo_id'))}"
    )
    print(
        "- cultivos sin campana_id: "
        f"{_formatear_contador(_contar_vacios(conn, 'cultivos', 'campana_id'))}"
    )
    print(
        "- cultivos sin codigo_siex: "
        f"{_formatear_contador(_contar_vacios(conn, 'cultivos', 'codigo_siex'))}"
    )
    print(
        "- cultivos sin superficie: "
        f"{_formatear_contador(_contar_vacios(conn, 'cultivos', 'superficie'))}"
    )
    print()
    print("Totales de referencia:")

    for tabla in [
        "cultivos",
        "cultivo_parcelas",
        "fertilizaciones",
        "practicas_culturales",
        "cosecha",
    ]:

        print(f"- {tabla}: {_formatear_contador(_contar(conn, tabla))}")


def main():

    ruta_db = _resolver_ruta_datos("CUADERNOPRO_DB_PATH", "cuadernopro.db")
    print(f"Base de datos: {ruta_db}")

    if not ruta_db.exists():

        print("No existe la base de datos configurada.")
        return 1

    conn = _conectar_solo_lectura(ruta_db)

    try:

        _imprimir_estado(conn)

    finally:

        conn.close()

    return 0


if __name__ == "__main__":

    raise SystemExit(main())
