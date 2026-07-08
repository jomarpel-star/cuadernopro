#!/usr/bin/env python3
from pathlib import Path
import sqlite3
import sys
import traceback


APP_ROOT = Path(__file__).resolve().parents[1]
DB_SCHEMA = APP_ROOT / "runtime" / "v7" / "prueba_schema_v7_13.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.schema_v7 import (  # noqa: E402
    SCHEMA_VERSION,
    asegurar_ampliaciones_v7_17,
    crear_base_v7,
    crear_indices_v7,
    validar_esquema_v7,
)


COLUMNAS_V7_13 = {
    "explotacion": {
        "registro_autonomico",
        "tipo_explotacion",
        "orientacion_productiva",
        "fecha_alta",
        "agricultor_activo",
        "joven_agricultor",
    },
    "maquinaria": {
        "numero_serie",
        "fecha_compra",
        "horas_uso",
    },
    "equipos_aplicacion": {
        "matricula",
        "numero_roma",
        "fecha_adquisicion",
        "capacidad_litros",
    },
    "cultivos": {
        "marco_plantacion",
        "numero_arboles",
    },
}


TABLAS_V7_12 = {
    "explotacion": """
        CREATE TABLE explotacion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_explotacion TEXT,
            titular TEXT,
            nif TEXT,
            direccion TEXT,
            municipio TEXT,
            provincia TEXT,
            codigo_postal TEXT,
            telefono TEXT,
            email TEXT,
            identificador_oficial TEXT,
            tipo_identificador_oficial TEXT,
            responsable TEXT,
            asesor TEXT,
            numero_asesor TEXT,
            observaciones TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """,
    "maquinaria": """
        CREATE TABLE maquinaria(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            marca TEXT,
            modelo TEXT,
            matricula TEXT,
            numero_roma TEXT,
            descripcion TEXT,
            observaciones TEXT,
            activa INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    """,
    "equipos_aplicacion": """
        CREATE TABLE equipos_aplicacion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            marca TEXT,
            modelo TEXT,
            tipo TEXT,
            numero_serie TEXT,
            fecha_revision TEXT,
            fecha_proxima_revision TEXT,
            observaciones TEXT,
            activo INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    """,
    "cultivos": """
        CREATE TABLE cultivos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campana_id INTEGER,
            nombre TEXT NOT NULL,
            variedad TEXT,
            codigo_siex TEXT,
            superficie REAL,
            ano_plantacion INTEGER,
            activo INTEGER DEFAULT 1,
            observaciones TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """,
}


def _conectar():

    conn = sqlite3.connect(DB_SCHEMA)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _columnas(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _user_version(conn):

    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _assert(condicion, mensaje):

    if not condicion:

        raise AssertionError(mensaje)


def _comprobar_columnas(conn):

    for tabla, columnas in COLUMNAS_V7_13.items():

        reales = _columnas(conn, tabla)
        faltan = sorted(columnas - reales)
        _assert(
            not faltan,
            f"Faltan columnas v7.13 en {tabla}: {', '.join(faltan)}",
        )


def _comprobar_sin_duplicados(conn):

    for tabla, columnas in COLUMNAS_V7_13.items():

        reales = [
            fila[1]
            for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
        ]

        for columna in columnas:

            _assert(
                reales.count(columna) == 1,
                f"Columna duplicada {tabla}.{columna}",
            )


def _recrear_tabla_v712(conn, tabla):

    reales = [
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    ]
    tabla_old = f"{tabla}_v712_old"
    conn.execute(f'ALTER TABLE "{tabla}" RENAME TO "{tabla_old}"')
    conn.execute(TABLAS_V7_12[tabla])
    comunes = [
        columna
        for columna in reales
        if columna in _columnas(conn, tabla)
    ]

    if comunes:

        lista = ",".join(f'"{columna}"' for columna in comunes)
        conn.execute(
            f'INSERT INTO "{tabla}" ({lista}) '
            f'SELECT {lista} FROM "{tabla_old}"'
        )

    conn.execute(f'DROP TABLE "{tabla_old}"')


def _simular_base_v712(conn):

    conn.execute("PRAGMA foreign_keys=OFF")

    for tabla in ("explotacion", "maquinaria", "equipos_aplicacion", "cultivos"):

        _recrear_tabla_v712(conn, tabla)

    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    conn.execute("PRAGMA foreign_keys=ON")
    crear_indices_v7(conn)


def _insertar_y_leer_campos():

    with _conectar() as conn:

        conn.execute("DELETE FROM equipos_aplicacion")
        conn.execute("DELETE FROM maquinaria")
        conn.execute("DELETE FROM explotacion")
        conn.execute(
            """
            INSERT INTO explotacion
            (nombre_explotacion,titular,nif,municipio,provincia,
             identificador_oficial,registro_autonomico,tipo_explotacion,
             orientacion_productiva,fecha_alta,agricultor_activo,
             joven_agricultor,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "Finca v7.13",
                "Titular v7.13",
                "00000000V",
                "Jumilla",
                "Murcia",
                "REGEPA-V713",
                "REG-AUT-V713",
                "Agraria",
                "Frutos secos",
                "2026-01-01",
                1,
                0,
                "2026-07-02T00:00:00",
                "2026-07-02T00:00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO maquinaria
            (tipo,marca,modelo,matricula,numero_roma,numero_serie,
             fecha_compra,horas_uso,descripcion,observaciones,activa,
             created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "Tractor",
                "Marca",
                "Modelo",
                "MU-713-A",
                "ROMA-V713",
                "SER-MAQ-V713",
                "2025-03-15",
                123.5,
                "Tractor v7.13",
                "Maquinaria ampliada",
                1,
                "2026-07-02T00:00:00",
                "2026-07-02T00:00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO equipos_aplicacion
            (nombre,marca,modelo,tipo,matricula,numero_roma,numero_serie,
             fecha_adquisicion,capacidad_litros,fecha_revision,
             fecha_proxima_revision,observaciones,activo,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "Equipo v7.13",
                "Marca equipo",
                "Modelo equipo",
                "Pulverizador",
                "MU-713-E",
                "ROMA-EQ-V713",
                "SER-EQ-V713",
                "2025-04-01",
                800.0,
                "2026-02-01",
                "2027-02-01",
                "Equipo ampliado",
                1,
                "2026-07-02T00:00:00",
                "2026-07-02T00:00:00",
            ),
        )
        conn.commit()

        explotacion = dict(
            conn.execute("SELECT * FROM explotacion LIMIT 1").fetchone()
        )
        maquinaria = dict(
            conn.execute("SELECT * FROM maquinaria LIMIT 1").fetchone()
        )
        equipo = dict(
            conn.execute("SELECT * FROM equipos_aplicacion LIMIT 1").fetchone()
        )

    _assert(
        explotacion["registro_autonomico"] == "REG-AUT-V713",
        "registro_autonomico no persiste",
    )
    _assert(
        explotacion["tipo_explotacion"] == "Agraria",
        "tipo_explotacion no persiste",
    )
    _assert(
        explotacion["orientacion_productiva"] == "Frutos secos",
        "orientacion_productiva no persiste",
    )
    _assert(explotacion["fecha_alta"] == "2026-01-01", "fecha_alta no persiste")
    _assert(int(explotacion["agricultor_activo"]) == 1, "agricultor_activo")
    _assert(int(explotacion["joven_agricultor"]) == 0, "joven_agricultor")
    _assert(maquinaria["numero_serie"] == "SER-MAQ-V713", "numero_serie maq")
    _assert(maquinaria["fecha_compra"] == "2025-03-15", "fecha_compra")
    _assert(float(maquinaria["horas_uso"]) == 123.5, "horas_uso")
    _assert(equipo["matricula"] == "MU-713-E", "matricula equipo")
    _assert(equipo["numero_roma"] == "ROMA-EQ-V713", "numero_roma equipo")
    _assert(equipo["fecha_adquisicion"] == "2025-04-01", "fecha_adquisicion")
    _assert(float(equipo["capacidad_litros"]) == 800.0, "capacidad_litros")


def main():

    print("Prueba esquema v7.13")
    print("====================")
    print(f"Base usada: {DB_SCHEMA}")

    try:

        DB_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
        if DB_SCHEMA.exists():

            DB_SCHEMA.unlink()

        resultado = crear_base_v7(DB_SCHEMA)
        print("Base nueva v7.13: OK")

        with _conectar() as conn:

            _assert(_user_version(conn) == SCHEMA_VERSION, "user_version")
            _comprobar_columnas(conn)
            _comprobar_sin_duplicados(conn)
            validacion = validar_esquema_v7(conn)
            _assert(validacion["ok"], "; ".join(validacion["errors"]))

        print("Columnas nuevas en base limpia: OK")

        with _conectar() as conn:

            _simular_base_v712(conn)
            conn.commit()
            _assert(
                "registro_autonomico" not in _columnas(conn, "explotacion"),
                "la simulacion v7.12 conserva registro_autonomico",
            )
            asegurar_ampliaciones_v7_17(conn)
            asegurar_ampliaciones_v7_17(conn)
            crear_indices_v7(conn)
            conn.commit()
            _comprobar_columnas(conn)
            _comprobar_sin_duplicados(conn)
            validacion = validar_esquema_v7(conn)
            _assert(validacion["ok"], "; ".join(validacion["errors"]))

        print("Ampliacion idempotente sobre v7 existente: OK")

        _insertar_y_leer_campos()
        print("Insercion y lectura de campos v7.13: OK")
        print(f"PRAGMA user_version: {resultado['user_version']}")
        print("Resultado: OK")
        return 0

    except Exception:

        print("Resultado: FALLO")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":

    raise SystemExit(main())
