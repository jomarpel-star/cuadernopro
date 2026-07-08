#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import sqlite3
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
DB_V7 = APP_ROOT / "runtime" / "v7" / "cuadernopro_v7_limpia.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from modules.fertilizacion import (  # noqa: E402
    _columnas_tabla_conn as _columnas_fertilizacion,
    _insertar_fertilizacion_compatible,
    _leer_fertilizaciones_guardadas,
    _preparar_fertilizaciones_presentacion,
)
from modules.practicas_culturales import (  # noqa: E402
    _columnas_tabla_conn as _columnas_practicas,
    _insertar_practica_compatible,
    _leer_practicas_guardadas,
    _preparar_practicas_presentacion,
)


LEGACY_PROHIBIDAS = {
    "fertilizaciones": {"cultivo"},
    "practicas_culturales": {"cultivo"},
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


def _validar_tabla_limpia(conn, tabla, requeridas):

    columnas = _columnas_fertilizacion(conn, tabla)
    faltan = set(requeridas) - columnas
    legacy = LEGACY_PROHIBIDAS.get(tabla, set()) & columnas

    if faltan:

        raise AssertionError(
            f"Faltan columnas limpias en {tabla}: "
            + ", ".join(sorted(faltan))
        )

    if legacy:

        raise AssertionError(
            f"Columnas legacy detectadas en {tabla}: "
            + ", ".join(sorted(legacy))
        )


def _insertar_datos_minimos(conn):

    marca = datetime.now().strftime("%Y%m%d%H%M%S")
    campana_id = conn.execute(
        """
        INSERT INTO campanas
        (nombre, fecha_inicio, fecha_fin, activa, estado)
        VALUES (?,?,?,?,?)
        """,
        (
            f"Prueba v7.3 {marca}",
            "2026-01-01",
            "2026-12-31",
            1,
            "abierta",
        ),
    ).lastrowid
    parcela_id = conn.execute(
        """
        INSERT INTO parcelas
        (nombre, provincia_sigpac, municipio_sigpac, poligono, parcela,
         recinto, superficie_sigpac, activa)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            f"Parcela prueba v7.3 {marca}",
            41,
            91,
            "2",
            "34",
            "5",
            3.25,
            1,
        ),
    ).lastrowid
    cultivo_id = conn.execute(
        """
        INSERT INTO cultivos
        (campana_id, nombre, variedad, codigo_siex, superficie, activo)
        VALUES (?,?,?,?,?,?)
        """,
        (campana_id, "ALMENDRO", "Guara", "104", 3.25, 1),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO cultivo_parcelas
        (cultivo_id, parcela_id, superficie)
        VALUES (?,?,?)
        """,
        (cultivo_id, parcela_id, 3.25),
    )
    proveedor_id = conn.execute(
        """
        INSERT INTO proveedores
        (nombre, nif, actividad, activo)
        VALUES (?,?,?,?)
        """,
        (
            f"Proveedor prueba v7.3 {marca}",
            f"PROV{marca[-8:]}",
            "Servicios agricolas",
            1,
        ),
    ).lastrowid
    maquinaria_id = conn.execute(
        """
        INSERT INTO maquinaria
        (tipo, marca, modelo, descripcion, activa)
        VALUES (?,?,?,?,?)
        """,
        (
            "Tractor",
            "Marca prueba",
            "Modelo v7.3",
            f"Maquinaria prueba v7.3 {marca}",
            1,
        ),
    ).lastrowid

    return campana_id, parcela_id, cultivo_id, proveedor_id, maquinaria_id


def _validar_fertilizacion(fila):

    errores = []

    if "ALMENDRO" not in str(fila["cultivo_mostrado"]).upper():

        errores.append("fertilizacion sin cultivo resuelto")

    if "Parcela prueba v7.3" not in str(fila["parcelas"]):

        errores.append("fertilizacion sin parcelas resueltas")

    if float(fila["cantidad"]) != 500.0:

        errores.append("cantidad de fertilizacion incorrecta")

    if str(fila["unidad"]) != "kg":

        errores.append("unidad de fertilizacion incorrecta")

    if errores:

        raise AssertionError("; ".join(errores))


def _validar_practica(fila):

    errores = []

    if "ALMENDRO" not in str(fila["cultivo_mostrado"]).upper():

        errores.append("practica sin cultivo resuelto")

    if "Parcela prueba v7.3" not in str(fila["parcelas"]):

        errores.append("practica sin parcelas resueltas")

    if "Maquinaria prueba v7.3" not in str(fila["maquinaria"]):

        errores.append("practica sin maquinaria resuelta")

    if "Proveedor prueba v7.3" not in str(fila["prestador"]):

        errores.append("practica sin proveedor resuelto")

    if float(fila["superficie"]) != 3.25:

        errores.append("superficie de practica incorrecta")

    if errores:

        raise AssertionError("; ".join(errores))


def main():

    try:

        with _conectar_v7() as conn:

            _validar_tabla_limpia(
                conn,
                "fertilizaciones",
                {
                    "campana_id",
                    "cultivo_id",
                    "fecha",
                    "producto",
                    "cantidad",
                    "unidad",
                    "superficie",
                },
            )
            _validar_tabla_limpia(
                conn,
                "practicas_culturales",
                {
                    "campana_id",
                    "cultivo_id",
                    "fecha",
                    "labor",
                    "superficie",
                    "maquinaria_id",
                    "proveedor_id",
                },
            )

            if not _columnas_practicas(conn, "fertilizacion_parcelas"):

                raise AssertionError("No existe fertilizacion_parcelas")

            if not _columnas_practicas(conn, "practicas_culturales_parcelas"):

                raise AssertionError("No existe practicas_culturales_parcelas")

            (
                campana_id,
                parcela_id,
                cultivo_id,
                proveedor_id,
                maquinaria_id,
            ) = _insertar_datos_minimos(conn)
            fertilizacion_id = _insertar_fertilizacion_compatible(
                conn,
                {
                    "campana_id": campana_id,
                    "cultivo_id": cultivo_id,
                    "fecha": "2026-07-01",
                    "producto": "Compost prueba v7.3",
                    "tipo_fertilizante": "Orgánico",
                    "cantidad": 500.0,
                    "unidad": "kg",
                    "unidad_normalizada": "kg",
                    "superficie": 3.25,
                    "codigo_actuacion_siex": "FERT-V73",
                    "observaciones": "Prueba fertilizacion v7.3",
                    "cultivo": "NO_DEBE_GUARDARSE",
                },
                [parcela_id],
            )
            practica_id = _insertar_practica_compatible(
                conn,
                {
                    "campana_id": campana_id,
                    "cultivo_id": cultivo_id,
                    "fecha": "2026-07-02",
                    "labor": "Desbroce",
                    "codigo_actuacion_siex": "PRAC-V73",
                    "superficie": 3.25,
                    "maquinaria_id": maquinaria_id,
                    "proveedor_id": proveedor_id,
                    "observaciones": "Prueba practica v7.3",
                    "cultivo": "NO_DEBE_GUARDARSE",
                },
                [parcela_id],
            )
            conn.commit()
            fertilizaciones = _preparar_fertilizaciones_presentacion(
                _leer_fertilizaciones_guardadas(
                    conn=conn,
                    fertilizacion_id=fertilizacion_id,
                )
            )
            practicas = _preparar_practicas_presentacion(
                _leer_practicas_guardadas(conn=conn, practica_id=practica_id)
            )

            if fertilizaciones.empty:

                raise AssertionError("No se pudo leer la fertilizacion insertada")

            if practicas.empty:

                raise AssertionError("No se pudo leer la practica insertada")

            _validar_fertilizacion(fertilizaciones.iloc[0])
            _validar_practica(practicas.iloc[0])

    except Exception as exc:

        print(f"Resultado: ERROR - {exc}", file=sys.stderr)
        return 1

    print("Prueba fertilizacion/practicas v7")
    print("==================================")
    print(f"Base: {DB_V7}")
    print(f"Fertilizacion insertada: {fertilizacion_id}")
    print(f"Practica insertada: {practica_id}")
    print("Columnas legacy usadas: ninguna")
    print("Lectura campana/cultivo/parcelas/maquinaria/proveedor: OK")
    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
