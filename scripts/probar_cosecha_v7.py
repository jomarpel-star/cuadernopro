#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import sqlite3
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
DB_V7 = APP_ROOT / "runtime" / "v7" / "cuadernopro_v7_limpia.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from modules.cosecha import (  # noqa: E402
    _columnas_tabla_conn,
    _insertar_cosecha_compatible,
    _leer_cosechas_guardadas,
    _preparar_cosechas_presentacion,
)


LEGACY_COSECHA_PROHIBIDAS = {
    "cultivo",
    "cliente",
    "nif_cliente",
    "kg",
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


def _insertar_datos_minimos(conn):

    marca = datetime.now().strftime("%Y%m%d%H%M%S")

    campana_id = conn.execute(
        """
        INSERT INTO campanas
        (nombre, fecha_inicio, fecha_fin, activa, estado)
        VALUES (?,?,?,?,?)
        """,
        (
            f"Prueba v7.2 {marca}",
            "2026-01-01",
            "2026-12-31",
            1,
            "abierta",
        ),
    ).lastrowid
    cliente_id = conn.execute(
        """
        INSERT INTO clientes
        (nombre, nif, activo)
        VALUES (?,?,?)
        """,
        (f"Cliente prueba v7.2 {marca}", f"NIF{marca[-8:]}", 1),
    ).lastrowid
    parcela_id = conn.execute(
        """
        INSERT INTO parcelas
        (nombre, provincia_sigpac, municipio_sigpac, poligono, parcela,
         recinto, superficie_sigpac, activa)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            f"Parcela prueba v7.2 {marca}",
            41,
            91,
            "1",
            "23",
            "4",
            2.75,
            1,
        ),
    ).lastrowid
    cultivo_id = conn.execute(
        """
        INSERT INTO cultivos
        (campana_id, nombre, variedad, codigo_siex, superficie, activo)
        VALUES (?,?,?,?,?,?)
        """,
        (campana_id, "ALMENDRO", "Guara", "104", 2.75, 1),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO cultivo_parcelas
        (cultivo_id, parcela_id, superficie)
        VALUES (?,?,?)
        """,
        (cultivo_id, parcela_id, 2.75),
    )

    return campana_id, cliente_id, parcela_id, cultivo_id


def _validar_columnas_limpias(conn):

    columnas = _columnas_tabla_conn(conn, "cosecha")
    faltan = {
        "campana_id",
        "cultivo_id",
        "fecha",
        "cantidad",
        "unidad",
        "destino",
        "cliente_id",
        "observaciones",
    } - columnas
    legacy = LEGACY_COSECHA_PROHIBIDAS & columnas

    if faltan:

        raise AssertionError(
            "Faltan columnas limpias en cosecha: "
            + ", ".join(sorted(faltan))
        )

    if legacy:

        raise AssertionError(
            "Columnas legacy detectadas en cosecha v7: "
            + ", ".join(sorted(legacy))
        )


def _validar_lectura(fila):

    errores = []

    if int(fila["campana_id"]) <= 0:

        errores.append("campana_id no valido")

    if int(fila["cultivo_id"]) <= 0:

        errores.append("cultivo_id no valido")

    if int(fila["cliente_id"]) <= 0:

        errores.append("cliente_id no valido")

    if "ALMENDRO" not in str(fila["cultivo_mostrado"]).upper():

        errores.append("cultivo no resuelto desde cultivos")

    if "Cliente prueba v7.2" not in str(fila["cliente"]):

        errores.append("cliente no resuelto desde clientes")

    if float(fila["cantidad"]) != 1250.0:

        errores.append("cantidad no leida correctamente")

    if str(fila["unidad"]) != "kg":

        errores.append("unidad no leida correctamente")

    if errores:

        raise AssertionError("; ".join(errores))


def main():

    try:

        with _conectar_v7() as conn:

            _validar_columnas_limpias(conn)
            campana_id, cliente_id, parcela_id, cultivo_id = (
                _insertar_datos_minimos(conn)
            )
            cosecha_id = _insertar_cosecha_compatible(
                conn,
                {
                    "campana_id": campana_id,
                    "cultivo_id": cultivo_id,
                    "fecha": "2026-07-01",
                    "cantidad": 1250.0,
                    "unidad": "kg",
                    "destino": "Cooperativa prueba v7.2",
                    "cliente_id": cliente_id,
                    "observaciones": "Prueba automatica v7.2",
                    "cultivo": "NO_DEBE_GUARDARSE",
                    "cliente": "NO_DEBE_GUARDARSE",
                    "nif_cliente": "NO_DEBE_GUARDARSE",
                    "kg": 1250.0,
                },
                [parcela_id],
            )
            conn.commit()
            cosechas = _preparar_cosechas_presentacion(
                _leer_cosechas_guardadas(conn=conn, cosecha_id=cosecha_id)
            )

            if cosechas.empty:

                raise AssertionError("No se pudo leer la cosecha insertada")

            fila = cosechas.iloc[0]
            _validar_lectura(fila)

    except Exception as exc:

        print(f"Resultado: ERROR - {exc}", file=sys.stderr)
        return 1

    print("Prueba cosecha v7")
    print("=================")
    print(f"Base: {DB_V7}")
    print(f"Cosecha insertada: {cosecha_id}")
    print("Columnas legacy usadas: ninguna")
    print("Lectura campaña/cultivo/cliente: OK")
    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
