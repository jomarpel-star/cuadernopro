#!/usr/bin/env python3
from pathlib import Path
import argparse
import sqlite3
import sys


APP_ROOT = Path(__file__).resolve().parents[1]

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.schema_v7 import validar_esquema_v7  # noqa: E402


COSECHA_LIMPIA_REQUERIDA = (
    "campana_id",
    "cultivo_id",
    "fecha",
    "cantidad",
    "unidad",
    "destino",
    "cliente_id",
    "observaciones",
)

COSECHA_LEGACY_PROHIBIDA = (
    "cultivo",
    "cliente",
    "nif_cliente",
    "kg",
)

FERTILIZACION_LIMPIA_REQUERIDA = (
    "campana_id",
    "cultivo_id",
    "fecha",
    "producto",
    "cantidad",
    "unidad",
    "superficie",
)

FERTILIZACION_LEGACY_PROHIBIDA = (
    "cultivo",
)

PRACTICAS_LIMPIA_REQUERIDA = (
    "campana_id",
    "cultivo_id",
    "fecha",
    "labor",
    "superficie",
    "maquinaria_id",
    "proveedor_id",
)

PRACTICAS_LEGACY_PROHIBIDA = (
    "cultivo",
)

MOVIMIENTOS_LIMPIA_REQUERIDA = (
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
)

MOVIMIENTOS_LEGACY_PROHIBIDA = (
    "tercero",
    "nif_tercero",
    "cultivo",
)

TRATAMIENTOS_LIMPIA_REQUERIDA = (
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
)

TRATAMIENTOS_LEGACY_PROHIBIDA = (
    "fecha",
    "cultivo",
    "producto",
    "aplicador",
    "equipo",
    "equipo_id",
    "maquinaria_id",
    "problema",
)

SALIDAS_TABLAS_REQUERIDAS = (
    "campanas",
    "cultivos",
    "parcelas",
    "clientes",
    "proveedores",
    "productos_fito",
    "personas",
    "maquinaria",
    "equipos_aplicacion",
    "tratamiento_parcelas",
    "tratamiento_cultivos",
    "tratamientos_documentos",
    "fertilizacion_parcelas",
    "fertilizacion_cultivos",
    "practicas_culturales_parcelas",
    "practicas_culturales_cultivos",
    "cosecha_parcelas",
    "cosecha_cultivos",
    "movimientos_economicos_lineas_iva",
    "movimientos_economicos_documentos",
)

SALIDAS_COLUMNAS_REQUERIDAS = {
    "cultivos": (
        "id",
        "campana_id",
        "nombre",
        "codigo_siex",
        "marco_plantacion",
        "numero_arboles",
    ),
    "productos_fito": ("id", "nombre", "numero_registro"),
    "clientes": ("id", "nombre", "nif"),
    "proveedores": ("id", "nombre", "nif"),
    "personas": ("id", "nombre", "nif", "carnet_aplicador"),
    "equipos_aplicacion": ("id", "nombre", "tipo"),
}


def _resolver_ruta(ruta):

    ruta = Path(ruta).expanduser()

    if not ruta.is_absolute():

        ruta = APP_ROOT / ruta

    return ruta.resolve()


def _conectar_solo_lectura(ruta):

    uri = f"file:{ruta}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _columnas_tabla(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _diagnostico_cosecha(conn):

    columnas = _columnas_tabla(conn, "cosecha")
    faltan_limpias = sorted(set(COSECHA_LIMPIA_REQUERIDA) - columnas)
    legacy_detectadas = sorted(set(COSECHA_LEGACY_PROHIBIDA) & columnas)

    return {
        "missing_clean_columns": faltan_limpias,
        "legacy_columns": legacy_detectadas,
    }


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


def _diagnostico_tabla_limpia(conn, tabla, requeridas, prohibidas):

    columnas = _columnas_tabla(conn, tabla)
    faltan_limpias = sorted(set(requeridas) - columnas)
    legacy_detectadas = sorted(set(prohibidas) & columnas)

    return {
        "missing_clean_columns": faltan_limpias,
        "legacy_columns": legacy_detectadas,
    }


def _diagnostico_fertilizacion_practicas(conn):

    return {
        "fertilizaciones": _diagnostico_tabla_limpia(
            conn,
            "fertilizaciones",
            FERTILIZACION_LIMPIA_REQUERIDA,
            FERTILIZACION_LEGACY_PROHIBIDA,
        ),
        "fertilizacion_parcelas_exists": _tabla_existe(
            conn,
            "fertilizacion_parcelas",
        ),
        "fertilizacion_cultivos_exists": _tabla_existe(
            conn,
            "fertilizacion_cultivos",
        ),
        "practicas_culturales": _diagnostico_tabla_limpia(
            conn,
            "practicas_culturales",
            PRACTICAS_LIMPIA_REQUERIDA,
            PRACTICAS_LEGACY_PROHIBIDA,
        ),
        "practicas_culturales_parcelas_exists": _tabla_existe(
            conn,
            "practicas_culturales_parcelas",
        ),
        "practicas_culturales_cultivos_exists": _tabla_existe(
            conn,
            "practicas_culturales_cultivos",
        ),
    }


def _diagnostico_contabilidad(conn):

    return {
        "movimientos_economicos": _diagnostico_tabla_limpia(
            conn,
            "movimientos_economicos",
            MOVIMIENTOS_LIMPIA_REQUERIDA,
            MOVIMIENTOS_LEGACY_PROHIBIDA,
        ),
        "movimientos_economicos_lineas_iva_exists": _tabla_existe(
            conn,
            "movimientos_economicos_lineas_iva",
        ),
        "movimientos_economicos_documentos_exists": _tabla_existe(
            conn,
            "movimientos_economicos_documentos",
        ),
    }


def _diagnostico_tratamientos(conn):

    return {
        "tratamientos": _diagnostico_tabla_limpia(
            conn,
            "tratamientos",
            TRATAMIENTOS_LIMPIA_REQUERIDA,
            TRATAMIENTOS_LEGACY_PROHIBIDA,
        ),
        "tratamiento_parcelas_exists": _tabla_existe(
            conn,
            "tratamiento_parcelas",
        ),
        "tratamiento_cultivos_exists": _tabla_existe(
            conn,
            "tratamiento_cultivos",
        ),
        "tratamientos_documentos_exists": _tabla_existe(
            conn,
            "tratamientos_documentos",
        ),
    }


def _diagnostico_salidas(conn):

    tablas_faltantes = [
        tabla
        for tabla in SALIDAS_TABLAS_REQUERIDAS
        if not _tabla_existe(conn, tabla)
    ]
    columnas_faltantes = []

    for tabla, columnas_requeridas in SALIDAS_COLUMNAS_REQUERIDAS.items():

        columnas = _columnas_tabla(conn, tabla)

        for columna in columnas_requeridas:

            if columna not in columnas:

                columnas_faltantes.append(f"{tabla}.{columna}")

    return {
        "missing_tables": tablas_faltantes,
        "missing_columns": columnas_faltantes,
    }


def _imprimir_lista(titulo, valores):

    print(titulo)

    if not valores:

        print("- ninguno")
        return

    for valor in valores:

        print(f"- {valor}")


def _imprimir_resultado(ruta, resultado):

    print("Diagnostico esquema v7")
    print("======================")
    print(f"Ruta: {ruta}")
    print(f"Version esperada: {resultado['schema_version']}")
    print(f"PRAGMA user_version: {resultado['user_version']}")
    print(f"Numero de tablas: {resultado['table_count']}")
    print()
    _imprimir_lista("Tablas principales", resultado["principal_tables"])
    print()
    _imprimir_lista("Tablas faltantes", resultado["missing_tables"])
    print()
    _imprimir_lista("Columnas faltantes", resultado["missing_columns"])
    print()
    _imprimir_lista(
        "Columnas legacy prohibidas detectadas",
        resultado["legacy_columns"],
    )
    print()
    _imprimir_lista("Indices faltantes", resultado["missing_indexes"])
    print()
    _imprimir_lista("Errores de claves foraneas", resultado["foreign_key_errors"])
    print()
    cosecha = resultado.get("cosecha", {})
    _imprimir_lista(
        "Cosecha limpia - columnas requeridas faltantes",
        cosecha.get("missing_clean_columns", []),
    )
    print()
    _imprimir_lista(
        "Cosecha limpia - legacy detectado",
        cosecha.get("legacy_columns", []),
    )
    print()
    fert_pract = resultado.get("fertilizacion_practicas", {})
    fertilizaciones = fert_pract.get("fertilizaciones", {})
    _imprimir_lista(
        "Fertilizacion limpia - columnas requeridas faltantes",
        fertilizaciones.get("missing_clean_columns", []),
    )
    print()
    _imprimir_lista(
        "Fertilizacion limpia - legacy detectado",
        fertilizaciones.get("legacy_columns", []),
    )
    print()
    fertilizacion_parcelas_estado = (
        ["existe"]
        if fert_pract.get("fertilizacion_parcelas_exists")
        else ["no existe"]
    )
    _imprimir_lista(
        "Fertilizacion limpia - tabla fertilizacion_parcelas",
        fertilizacion_parcelas_estado,
    )
    print()
    fertilizacion_cultivos_estado = (
        ["existe"]
        if fert_pract.get("fertilizacion_cultivos_exists")
        else ["no existe"]
    )
    _imprimir_lista(
        "Fertilizacion limpia - tabla fertilizacion_cultivos",
        fertilizacion_cultivos_estado,
    )
    print()
    practicas = fert_pract.get("practicas_culturales", {})
    _imprimir_lista(
        "Practicas limpias - columnas requeridas faltantes",
        practicas.get("missing_clean_columns", []),
    )
    print()
    _imprimir_lista(
        "Practicas limpias - legacy detectado",
        practicas.get("legacy_columns", []),
    )
    print()
    practicas_parcelas_estado = (
        ["existe"]
        if fert_pract.get("practicas_culturales_parcelas_exists")
        else ["no existe"]
    )
    _imprimir_lista(
        "Practicas limpias - tabla practicas_culturales_parcelas",
        practicas_parcelas_estado,
    )
    print()
    practicas_cultivos_estado = (
        ["existe"]
        if fert_pract.get("practicas_culturales_cultivos_exists")
        else ["no existe"]
    )
    _imprimir_lista(
        "Practicas limpias - tabla practicas_culturales_cultivos",
        practicas_cultivos_estado,
    )
    print()
    contabilidad = resultado.get("contabilidad", {})
    movimientos = contabilidad.get("movimientos_economicos", {})
    _imprimir_lista(
        "Contabilidad limpia - columnas requeridas faltantes",
        movimientos.get("missing_clean_columns", []),
    )
    print()
    _imprimir_lista(
        "Contabilidad limpia - legacy detectado",
        movimientos.get("legacy_columns", []),
    )
    print()
    lineas_iva_estado = (
        ["existe"]
        if contabilidad.get("movimientos_economicos_lineas_iva_exists")
        else ["no existe"]
    )
    _imprimir_lista(
        "Contabilidad limpia - tabla movimientos_economicos_lineas_iva",
        lineas_iva_estado,
    )
    print()
    documentos_estado = (
        ["existe"]
        if contabilidad.get("movimientos_economicos_documentos_exists")
        else ["no existe"]
    )
    _imprimir_lista(
        "Contabilidad limpia - tabla movimientos_economicos_documentos",
        documentos_estado,
    )
    print()
    tratamientos = resultado.get("tratamientos_limpios", {})
    tratamientos_tabla = tratamientos.get("tratamientos", {})
    _imprimir_lista(
        "Tratamientos limpios - columnas requeridas faltantes",
        tratamientos_tabla.get("missing_clean_columns", []),
    )
    print()
    _imprimir_lista(
        "Tratamientos limpios - legacy detectado",
        tratamientos_tabla.get("legacy_columns", []),
    )
    print()
    tratamiento_parcelas_estado = (
        ["existe"]
        if tratamientos.get("tratamiento_parcelas_exists")
        else ["no existe"]
    )
    _imprimir_lista(
        "Tratamientos limpios - tabla tratamiento_parcelas",
        tratamiento_parcelas_estado,
    )
    print()
    tratamiento_cultivos_estado = (
        ["existe"]
        if tratamientos.get("tratamiento_cultivos_exists")
        else ["no existe"]
    )
    _imprimir_lista(
        "Tratamientos limpios - tabla tratamiento_cultivos",
        tratamiento_cultivos_estado,
    )
    print()
    tratamientos_documentos_estado = (
        ["existe"]
        if tratamientos.get("tratamientos_documentos_exists")
        else ["no existe"]
    )
    _imprimir_lista(
        "Tratamientos limpios - tabla tratamientos_documentos",
        tratamientos_documentos_estado,
    )
    print()
    salidas = resultado.get("salidas", {})
    _imprimir_lista(
        "Salidas v7 - tablas requeridas faltantes",
        salidas.get("missing_tables", []),
    )
    print()
    _imprimir_lista(
        "Salidas v7 - columnas requeridas faltantes",
        salidas.get("missing_columns", []),
    )
    print()

    if resultado["ok"]:

        print("Resultado: OK")

    else:

        print("Resultado: ERROR")
        _imprimir_lista("Errores graves", resultado["errors"])


def main():

    parser = argparse.ArgumentParser(
        description="Diagnostica una base SQLite con esquema CuadernoPro v7."
    )
    parser.add_argument(
        "ruta_db",
        help="Ruta de la base v7 a diagnosticar",
    )
    args = parser.parse_args()
    ruta = _resolver_ruta(args.ruta_db)

    if not ruta.exists():

        print(f"ERROR: no existe la base indicada: {ruta}", file=sys.stderr)
        return 2

    try:

        with _conectar_solo_lectura(ruta) as conn:

            resultado = validar_esquema_v7(conn)
            resultado["cosecha"] = _diagnostico_cosecha(conn)
            resultado["fertilizacion_practicas"] = (
                _diagnostico_fertilizacion_practicas(conn)
            )
            resultado["contabilidad"] = _diagnostico_contabilidad(conn)
            resultado["tratamientos_limpios"] = _diagnostico_tratamientos(conn)
            resultado["salidas"] = _diagnostico_salidas(conn)

            if resultado["cosecha"]["missing_clean_columns"]:

                resultado["ok"] = False
                for columna in resultado["cosecha"]["missing_clean_columns"]:

                    resultado["errors"].append(
                        f"Falta columna limpia cosecha.{columna}"
                    )

            if resultado["cosecha"]["legacy_columns"]:

                resultado["ok"] = False
                for columna in resultado["cosecha"]["legacy_columns"]:

                    resultado["errors"].append(
                        f"Columna legacy prohibida cosecha.{columna}"
                    )

            fert_pract = resultado["fertilizacion_practicas"]

            for tabla in ("fertilizaciones", "practicas_culturales"):

                diagnostico = fert_pract[tabla]

                if diagnostico["missing_clean_columns"]:

                    resultado["ok"] = False
                    for columna in diagnostico["missing_clean_columns"]:

                        resultado["errors"].append(
                            f"Falta columna limpia {tabla}.{columna}"
                        )

                if diagnostico["legacy_columns"]:

                    resultado["ok"] = False
                    for columna in diagnostico["legacy_columns"]:

                        resultado["errors"].append(
                            f"Columna legacy prohibida {tabla}.{columna}"
                        )

            if not fert_pract["fertilizacion_parcelas_exists"]:

                resultado["ok"] = False
                resultado["errors"].append("Falta tabla fertilizacion_parcelas")

            if not fert_pract["fertilizacion_cultivos_exists"]:

                resultado["ok"] = False
                resultado["errors"].append("Falta tabla fertilizacion_cultivos")

            if not fert_pract["practicas_culturales_parcelas_exists"]:

                resultado["ok"] = False
                resultado["errors"].append(
                    "Falta tabla practicas_culturales_parcelas"
                )

            if not fert_pract["practicas_culturales_cultivos_exists"]:

                resultado["ok"] = False
                resultado["errors"].append(
                    "Falta tabla practicas_culturales_cultivos"
                )

            contabilidad = resultado["contabilidad"]
            diagnostico_movimientos = contabilidad["movimientos_economicos"]

            if diagnostico_movimientos["missing_clean_columns"]:

                resultado["ok"] = False
                for columna in diagnostico_movimientos[
                    "missing_clean_columns"
                ]:

                    resultado["errors"].append(
                        "Falta columna limpia "
                        f"movimientos_economicos.{columna}"
                    )

            if diagnostico_movimientos["legacy_columns"]:

                resultado["ok"] = False
                for columna in diagnostico_movimientos["legacy_columns"]:

                    resultado["errors"].append(
                        "Columna legacy prohibida "
                        f"movimientos_economicos.{columna}"
                    )

            if not contabilidad["movimientos_economicos_lineas_iva_exists"]:

                resultado["ok"] = False
                resultado["errors"].append(
                    "Falta tabla movimientos_economicos_lineas_iva"
                )

            if not contabilidad["movimientos_economicos_documentos_exists"]:

                resultado["ok"] = False
                resultado["errors"].append(
                    "Falta tabla movimientos_economicos_documentos"
                )

            tratamientos_limpios = resultado["tratamientos_limpios"]
            diagnostico_tratamientos = tratamientos_limpios["tratamientos"]

            if diagnostico_tratamientos["missing_clean_columns"]:

                resultado["ok"] = False
                for columna in diagnostico_tratamientos[
                    "missing_clean_columns"
                ]:

                    resultado["errors"].append(
                        f"Falta columna limpia tratamientos.{columna}"
                    )

            if diagnostico_tratamientos["legacy_columns"]:

                resultado["ok"] = False
                for columna in diagnostico_tratamientos["legacy_columns"]:

                    resultado["errors"].append(
                        f"Columna legacy prohibida tratamientos.{columna}"
                    )

            if not tratamientos_limpios["tratamiento_parcelas_exists"]:

                resultado["ok"] = False
                resultado["errors"].append("Falta tabla tratamiento_parcelas")

            if not tratamientos_limpios["tratamiento_cultivos_exists"]:

                resultado["ok"] = False
                resultado["errors"].append("Falta tabla tratamiento_cultivos")

            if not tratamientos_limpios["tratamientos_documentos_exists"]:

                resultado["ok"] = False
                resultado["errors"].append("Falta tabla tratamientos_documentos")

            salidas = resultado["salidas"]

            if salidas["missing_tables"]:

                resultado["ok"] = False

                for tabla in salidas["missing_tables"]:

                    resultado["errors"].append(
                        f"Falta tabla requerida para salidas v7: {tabla}"
                    )

            if salidas["missing_columns"]:

                resultado["ok"] = False

                for columna in salidas["missing_columns"]:

                    resultado["errors"].append(
                        "Falta columna requerida para salidas v7: "
                        f"{columna}"
                    )

    except sqlite3.Error as error:

        print(f"ERROR: no se pudo abrir la base: {error}", file=sys.stderr)
        return 2

    _imprimir_resultado(ruta, resultado)
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":

    raise SystemExit(main())
