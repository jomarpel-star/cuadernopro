#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import sqlite3
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
DB_V7 = APP_ROOT / "runtime" / "v7" / "cuadernopro_v7_limpia.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from modules.tratamientos import (  # noqa: E402
    _columnas_tabla_conn,
    _insertar_tratamiento_compatible,
    _leer_tratamientos_guardados,
    _normalizar_eficacia,
)


LEGACY_TRATAMIENTOS_PROHIBIDAS = {
    "fecha",
    "cultivo",
    "producto",
    "aplicador",
    "equipo",
    "equipo_id",
    "maquinaria_id",
    "problema",
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

    columnas = _columnas_tabla_conn(conn, "tratamientos")
    faltan = {
        "campana_id",
        "cultivo_id",
        "fecha_inicio",
        "fecha_fin",
        "producto_id",
        "aplicador_id",
        "equipo_aplicacion_id",
        "plaga_motivo",
        "dosis",
        "caldo",
        "superficie_tratada",
        "plazo_seguridad",
        "eficacia",
        "observaciones",
    } - columnas
    legacy = LEGACY_TRATAMIENTOS_PROHIBIDAS & columnas

    if faltan:

        raise AssertionError(
            "Faltan columnas limpias en tratamientos: "
            + ", ".join(sorted(faltan))
        )

    if legacy:

        raise AssertionError(
            "Columnas legacy detectadas en tratamientos v7: "
            + ", ".join(sorted(legacy))
        )

    if not _columnas_tabla_conn(conn, "tratamiento_parcelas"):

        raise AssertionError("No existe tratamiento_parcelas")

    if not _columnas_tabla_conn(conn, "tratamientos_documentos"):

        raise AssertionError("No existe tratamientos_documentos")


def _insertar_datos_minimos(conn):

    marca = datetime.now().strftime("%Y%m%d%H%M%S%f")
    campana_id = conn.execute(
        """
        INSERT INTO campanas
        (nombre, fecha_inicio, fecha_fin, activa, estado)
        VALUES (?,?,?,?,?)
        """,
        (
            f"Prueba v7.5 {marca}",
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
            f"Parcela prueba v7.5 {marca}",
            41,
            91,
            "7",
            "45",
            "2",
            4.5,
            1,
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
    conn.execute(
        """
        INSERT INTO cultivo_parcelas
        (cultivo_id, parcela_id, superficie)
        VALUES (?,?,?)
        """,
        (cultivo_id, parcela_id, 4.5),
    )
    producto_id = conn.execute(
        """
        INSERT INTO productos_fito
        (nombre, numero_registro, materia_activa, plazo_seguridad, activo)
        VALUES (?,?,?,?,?)
        """,
        (
            f"Producto prueba v7.5 {marca}",
            f"REG{marca[-8:]}",
            "Materia activa prueba",
            "14 dias",
            1,
        ),
    ).lastrowid
    aplicador_id = conn.execute(
        """
        INSERT INTO personas
        (nombre, nif, rol, carnet_aplicador, activo)
        VALUES (?,?,?,?,?)
        """,
        (
            f"Aplicador prueba v7.5 {marca}",
            f"APL{marca[-8:]}",
            "Aplicador fitosanitario",
            f"CARNET{marca[-6:]}",
            1,
        ),
    ).lastrowid
    equipo_id = conn.execute(
        """
        INSERT INTO equipos_aplicacion
        (nombre, marca, modelo, tipo, numero_serie, activo)
        VALUES (?,?,?,?,?,?)
        """,
        (
            f"Equipo prueba v7.5 {marca}",
            "ATASA",
            "Turbo 2000",
            "Equipo aplicación",
            f"SER{marca[-8:]}",
            1,
        ),
    ).lastrowid

    return (
        campana_id,
        parcela_id,
        cultivo_id,
        producto_id,
        aplicador_id,
        equipo_id,
    )


def _insertar_documento_simulado(conn, tratamiento_id):

    ahora = datetime.now().isoformat()
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
            "receta_prueba_v7_5.pdf",
            f"receta_prueba_v7_5_{tratamiento_id}.pdf",
            f"recetas/prueba_v7_5_{tratamiento_id}.pdf",
            "pdf",
            "application/pdf",
            0,
            "",
            1,
            ahora,
            ahora,
        ),
    )


def _validar_lectura(fila):

    errores = []

    if "ALMENDRO" not in str(fila["cultivo"]).upper():

        errores.append("cultivo no resuelto desde cultivos")

    if "Producto prueba v7.5" not in str(fila["producto"]):

        errores.append("producto no resuelto desde productos_fito")

    if "REG" not in str(fila["registro_producto"]):

        errores.append("registro de producto no resuelto")

    if "Aplicador prueba v7.5" not in str(fila["aplicador"]):

        errores.append("aplicador no resuelto desde personas")

    if "Equipo prueba v7.5" not in str(fila["equipo"]):

        errores.append("equipo no resuelto desde equipos_aplicacion")

    if "Parcela prueba v7.5" not in str(fila["parcelas"]):

        errores.append("parcelas no resueltas desde tratamiento_parcelas")

    if str(fila["plaga"]) != "Repilo prueba v7.5":

        errores.append("plaga_motivo no leido correctamente")

    if float(fila["superficie_tratada"]) != 4.5:

        errores.append("superficie_tratada incorrecta")

    if _normalizar_eficacia(fila["eficacia"]) != "B":

        errores.append("eficacia incorrecta")

    if int(fila["recetas_count"]) != 1:

        errores.append("receta simulada no resuelta")

    if errores:

        raise AssertionError("; ".join(errores))


def main():

    try:

        with _conectar_v7() as conn:

            _validar_columnas_limpias(conn)
            (
                campana_id,
                parcela_id,
                cultivo_id,
                producto_id,
                aplicador_id,
                equipo_id,
            ) = _insertar_datos_minimos(conn)
            tratamiento_id = _insertar_tratamiento_compatible(
                conn,
                {
                    "campana_id": campana_id,
                    "cultivo_id": cultivo_id,
                    "fecha": "2026-07-01",
                    "fecha_inicio": "2026-07-01",
                    "fecha_fin": "2026-07-02",
                    "producto_id": producto_id,
                    "producto": "NO_DEBE_GUARDARSE",
                    "aplicador_id": aplicador_id,
                    "aplicador": "NO_DEBE_GUARDARSE",
                    "equipo_id": equipo_id,
                    "equipo_aplicacion_id": equipo_id,
                    "equipo": "NO_DEBE_GUARDARSE",
                    "maquinaria_id": equipo_id,
                    "plaga_motivo": "Repilo prueba v7.5",
                    "plaga": "NO_DEBE_GUARDARSE",
                    "problema": "NO_DEBE_GUARDARSE",
                    "dosis": "2 l/ha",
                    "caldo": 800.0,
                    "superficie_tratada": 4.5,
                    "plazo_seguridad": "14 dias",
                    "eficacia": "B",
                    "observaciones": "Prueba tratamiento v7.5",
                },
                [{"parcela_id": parcela_id, "superficie": 4.5}],
            )
            _insertar_documento_simulado(conn, tratamiento_id)
            conn.commit()
            tratamientos = _leer_tratamientos_guardados(
                conn=conn,
                tratamiento_id=tratamiento_id,
            )

            if tratamientos.empty:

                raise AssertionError("No se pudo leer el tratamiento insertado")

            _validar_lectura(tratamientos.iloc[0])

    except Exception as exc:

        print(f"Resultado: ERROR - {exc}", file=sys.stderr)
        return 1

    print("Prueba tratamientos v7")
    print("======================")
    print(f"Base: {DB_V7}")
    print(f"Tratamiento insertado: {tratamiento_id}")
    print("Columnas legacy usadas: ninguna")
    print("Lectura campana/cultivo/parcelas/producto/aplicador/equipo/receta: OK")
    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
