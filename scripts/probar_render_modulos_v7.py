#!/usr/bin/env python3
from pathlib import Path
import os
import sqlite3
import sys
import tempfile
import traceback


APP_ROOT = Path(__file__).resolve().parents[1]
DB_RENDER = APP_ROOT / "runtime" / "v7" / "prueba_render_v7.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_RENDER)

from core.schema_v7 import asegurar_ampliaciones_v8_0_1, crear_base_v7  # noqa: E402


def _conectar():

    conn = sqlite3.connect(DB_RENDER)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _user_version(conn):

    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _contar(conn, tabla):

    return int(conn.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0])


def _insertar_explotacion_minima(conn):

    if _contar(conn, "explotacion"):

        return

    conn.execute(
        """
        INSERT INTO explotacion
        (nombre_explotacion,titular,nif,direccion,municipio,provincia,
         codigo_postal,telefono,email,identificador_oficial,
         tipo_identificador_oficial,registro_autonomico,tipo_explotacion,
         orientacion_productiva,fecha_alta,agricultor_activo,
         joven_agricultor,responsable,asesor,numero_asesor,
         observaciones,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Explotacion render v7",
            "Titular render v7",
            "00000000T",
            "Camino Render 1",
            "Jumilla",
            "Murcia",
            "30520",
            "600000000",
            "render-v7@example.com",
            "REGEA-RENDER-V7",
            "REGEA",
            "REG-AUT-RENDER-V7",
            "Agraria",
            "Frutos secos",
            "2026-01-01",
            1,
            0,
            "Responsable render v7",
            "Asesor render v7",
            "ASE-RENDER-V7",
            "Datos minimos render v7",
            "2026-07-02T00:00:00",
            "2026-07-02T00:00:00",
        ),
    )


def _insertar_campana_minima(conn):

    fila = conn.execute("SELECT id FROM campanas ORDER BY id LIMIT 1").fetchone()

    if fila:

        return int(fila[0])

    cursor = conn.execute(
        """
        INSERT INTO campanas
        (nombre,fecha_inicio,fecha_fin,activa,estado,observaciones,
         created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            "2025/2026",
            "2025-09-01",
            "2026-08-31",
            1,
            "abierta",
            "Campana render v7",
            "2026-07-02T00:00:00",
            "2026-07-02T00:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _insertar_parcela_minima(conn):

    fila = conn.execute("SELECT id FROM parcelas ORDER BY id LIMIT 1").fetchone()

    if fila:

        return int(fila[0])

    cursor = conn.execute(
        """
        INSERT INTO parcelas
        (nombre,provincia_sigpac,municipio_sigpac,agregado_sigpac,
         zona_sigpac,poligono,parcela,recinto,superficie_sigpac,
         uso_sigpac,activa,observaciones,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Parcela render v7",
            30,
            22,
            0,
            0,
            "1",
            "2",
            "3",
            1.75,
            "TA",
            1,
            "Parcela minima render v7",
            "2026-07-02T00:00:00",
            "2026-07-02T00:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _preparar_datos_minimos():

    with _conectar() as conn:

        asegurar_ampliaciones_v8_0_1(conn)
        _insertar_explotacion_minima(conn)
        campana_id = _insertar_campana_minima(conn)
        parcela_id = _insertar_parcela_minima(conn)
        conn.commit()

    import modules.cultivos as cultivos_mod
    import modules.explotacion as explotacion_mod
    import modules.maquinaria as maquinaria_mod

    with _conectar() as conn:

        hay_cultivos = _contar(conn, "cultivos") > 0
        hay_equipos = _contar(conn, "equipos_aplicacion") > 0
        hay_maquinaria = _contar(conn, "maquinaria") > 0

    if not hay_cultivos:

        parcelas = cultivos_mod._leer_parcelas()
        cultivos_mod._guardar_cultivo(
            campana_id=campana_id,
            cultivo="ALMENDRO",
            variedad="Render",
            codigo_siex="104",
            superficie=1.75,
            ano_plantacion=2020,
            marco_plantacion="7x6",
            numero_arboles=417,
            sistema="Secano",
            observaciones="Cultivo minimo render v7",
            activo=True,
            ids_parcelas=[parcela_id],
            parcelas=parcelas,
        )

    if not hay_equipos:

        explotacion_mod._insertar_equipo(
            {
                "nombre": "Equipo render v7",
                "tipo": "Pulverizador",
                "marca": "Marca render",
                "modelo": "Modelo render",
                "matricula": "EQ-RENDER-MAT",
                "numero_roma": "ROMA-EQ-RENDER-V7",
                "numero_serie": "EQ-RENDER-V7",
                "fecha_adquisicion": "2025-01-15",
                "fecha_ultima_inspeccion": "2026-01-15",
                "fecha_proxima_inspeccion": "2027-01-15",
                "capacidad_litros": 500.0,
                "observaciones": "Equipo minimo render v7",
            }
        )

    if not hay_maquinaria:

        maquinaria_mod._insertar_maquinaria(
            {
                "nombre": "Tractor render v7",
                "tipo": "Tractor",
                "marca": "Marca render",
                "modelo": "Modelo render",
                "matricula": "MU-RENDER",
                "numero_roma": "ROMA-RENDER-V7",
                "numero_serie": "SER-MAQ-RENDER-V7",
                "fecha_compra": "2025-02-15",
                "horas_uso": 25.0,
                "observaciones": "Maquinaria minima render v7",
            }
        )


def _crear_app_temporal(modulo, llamada=None):

    llamada = llamada or "modulo.render()"

    contenido = f"""
from pathlib import Path
import os
import sys

APP_ROOT = Path({str(APP_ROOT)!r})
DB_RENDER = Path({str(DB_RENDER)!r})
os.environ["CUADERNOPRO_DB_PATH"] = str(DB_RENDER)

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import {modulo} as modulo

{llamada}
"""
    temporal = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".py",
        prefix="render_modulo_v7_",
        dir=DB_RENDER.parent,
        delete=False,
    )

    with temporal:

        temporal.write(contenido)

    return Path(temporal.name)


def _descripcion_excepcion(excepcion):

    for atributo in ("value", "message", "exception"):

        valor = getattr(excepcion, atributo, None)

        if valor:

            return str(valor)

    return str(excepcion)


def _renderizar_modulo(nombre, modulo, llamada=None):

    from streamlit.testing.v1 import AppTest

    app_temporal = _crear_app_temporal(modulo, llamada=llamada)

    try:

        prueba = AppTest.from_file(app_temporal, default_timeout=10)
        prueba.run(timeout=10)
        excepciones = list(prueba.exception)
        errores_streamlit = list(getattr(prueba, "error", []))

        if excepciones:

            return False, "\n".join(
                _descripcion_excepcion(excepcion)
                for excepcion in excepciones
            )

        if errores_streamlit:

            return False, "\n".join(
                _descripcion_excepcion(error)
                for error in errores_streamlit
            )

        return True, ""

    except Exception:

        return False, traceback.format_exc()

    finally:

        try:

            app_temporal.unlink()

        except OSError:

            pass


def _comprobar_vista_campanas_asistente():

    import pandas as pd
    import modules.asistente_inicio as asistente_inicio

    vista = asistente_inicio._vista_campanas_asistente(
        pd.DataFrame(
            [
                {
                    "nombre": "2025/2026",
                    "fecha_inicio": "2025-10-01",
                    "fecha_fin": "2026-09-30",
                    "activa": 1,
                }
            ]
        )
    )
    columnas = list(vista.columns)
    esperadas = ["Campaña", "Fecha inicio", "Fecha fin", "Activa"]
    prohibidas = {"nombre", "fecha_inicio", "fecha_fin"}

    if columnas != esperadas:

        return False, f"columnas inesperadas: {columnas}"

    if prohibidas & set(columnas):

        return False, f"columnas tecnicas visibles: {prohibidas & set(columnas)}"

    fila = vista.iloc[0].to_dict()

    if fila["Fecha inicio"] != "01/10/2025":

        return False, f"fecha inicio no formateada: {fila['Fecha inicio']!r}"

    if fila["Fecha fin"] != "30/09/2026":

        return False, f"fecha fin no formateada: {fila['Fecha fin']!r}"

    return True, ""


def _comprobar_nombre_explotacion_asistente():

    import modules.asistente_inicio as asistente_inicio

    nombre_explicito = asistente_inicio._nombre_explotacion_o_titular(
        "Finca Los Olivos",
        "Titular SL"
    )
    nombre_fallback = asistente_inicio._nombre_explotacion_o_titular(
        "",
        "Titular SL"
    )

    if nombre_explicito != "Finca Los Olivos":

        return False, "no respeta el nombre de explotacion explicito"

    if nombre_fallback != "Titular SL":

        return False, "no usa el titular como fallback"

    return True, ""


def _asegurar_base_prueba():

    if DB_RENDER.exists():

        return

    crear_base_v7(DB_RENDER, sobrescribir=True)


def main():

    try:

        _asegurar_base_prueba()

    except Exception as exc:

        print("Prueba render modulos v7")
        print("========================")
        print(f"Base usada: {DB_RENDER}")
        print(f"FALLO: no se pudo preparar la base de prueba: {exc}")
        return 1

    with _conectar() as conn:

        version = _user_version(conn)

    print("Prueba render modulos v7")
    print("========================")
    print(f"Base usada: {DB_RENDER}")
    print(f"PRAGMA user_version: {version}")

    if version != 7:

        print("FALLO: la base no tiene user_version 7")
        return 1

    try:

        _preparar_datos_minimos()
        print("Datos minimos runtime/v7: OK")

    except Exception:

        print("Datos minimos runtime/v7: FALLO")
        print(traceback.format_exc())
        return 1

    ok_vista, error_vista = _comprobar_vista_campanas_asistente()
    print(
        "Asistente Campaña vista visual: "
        + ("OK" if ok_vista else "FALLO")
    )

    if error_vista:

        print(error_vista)

    if not ok_vista:

        return 1

    ok_nombre, error_nombre = _comprobar_nombre_explotacion_asistente()
    print(
        "Asistente Nombre explotacion fallback: "
        + ("OK" if ok_nombre else "FALLO")
    )

    if error_nombre:

        print(error_nombre)

    if not ok_nombre:

        return 1

    modulos = [
        ("Explotacion", "modules.explotacion", None),
        (
            "Explotacion Responsable / Asesor",
            "modules.explotacion",
            "datos = modulo._leer_datos_explotacion()\n"
            "modulo._render_responsable_asesor(datos)"
        ),
        ("Cultivos", "modules.cultivos", None),
        ("Parcelas", "modules.parcelas", None),
        ("Maquinaria", "modules.maquinaria", None),
        ("Productos fito", "modules.productos_fito", None),
        ("Mapas / SIGPAC", "modules.mapas", None),
        (
            "Contabilidad Listado vacio",
            "modules.contabilidad",
            "import streamlit as st\n"
            "import sqlite3\n"
            f"conn = sqlite3.connect({str(DB_RENDER)!r})\n"
            "campana_id = conn.execute("
            "'SELECT id FROM campanas ORDER BY id LIMIT 1'"
            ").fetchone()[0]\n"
            "conn.close()\n"
            "st.session_state['contabilidad_seccion'] = '📋 Listado'\n"
            "modulo.render(campana_id)"
        ),
    ]
    resultados = []

    for nombre, modulo, llamada in modulos:

        ok, error = _renderizar_modulo(nombre, modulo, llamada=llamada)
        resultados.append((nombre, ok, error))
        estado = "OK" if ok else "FALLO"
        print(f"{nombre}: {estado}")

        if error:

            print(error)

    if all(ok for _, ok, _ in resultados):

        print("Resultado: OK")
        return 0

    print("Resultado: FALLO")
    return 1


if __name__ == "__main__":

    raise SystemExit(main())
