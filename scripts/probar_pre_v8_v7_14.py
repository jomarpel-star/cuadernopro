#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import os
import sqlite3
import sys
import traceback

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = APP_ROOT / "scripts"
DB_PRE_V8 = APP_ROOT / "runtime" / "v7" / "prueba_pre_v8_v7_14.db"
EXPORTS_DIR = APP_ROOT / "runtime" / "v7" / "exports_pre_v8_v7_14"
DOCS_DIR = APP_ROOT / "runtime" / "v7" / "documentos_pre_v8_v7_14"

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_PRE_V8)

for ruta in (APP_ROOT, SCRIPTS_DIR):

    if str(ruta) not in sys.path:

        sys.path.insert(0, str(ruta))

import modules.mapas as mapas_mod  # noqa: E402
import probar_flujo_integral_v7 as flujo_integral  # noqa: E402


flujo_integral.DB_V7 = DB_PRE_V8
flujo_integral.EXPORTS_DIR = EXPORTS_DIR
flujo_integral.DOCS_DIR = DOCS_DIR


CAMPOS_V7_13 = {
    "explotacion": {
        "registro_autonomico",
        "tipo_explotacion",
        "orientacion_productiva",
        "fecha_alta",
        "agricultor_activo",
        "joven_agricultor",
    },
    "maquinaria": {
        "matricula",
        "numero_roma",
        "numero_serie",
        "fecha_compra",
        "horas_uso",
    },
    "equipos_aplicacion": {
        "matricula",
        "numero_roma",
        "numero_serie",
        "fecha_adquisicion",
        "capacidad_litros",
        "fecha_revision",
        "fecha_proxima_revision",
    },
}


def _conectar():

    conn = sqlite3.connect(DB_PRE_V8)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _columnas(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _fila(conn, tabla, registro_id):

    fila = conn.execute(
        f'SELECT * FROM "{tabla}" WHERE id=?',
        (int(registro_id),),
    ).fetchone()

    if fila is None:

        raise AssertionError(f"No existe {tabla}.id={registro_id}")

    return dict(fila)


def _assert_igual(actual, esperado, campo):

    if actual != esperado:

        raise AssertionError(
            f"{campo}: esperado {esperado!r}, obtenido {actual!r}"
        )


def _assert_float(actual, esperado, campo):

    if abs(float(actual or 0) - float(esperado)) > 0.0001:

        raise AssertionError(
            f"{campo}: esperado {esperado!r}, obtenido {actual!r}"
        )


def _assert_no_vacio(valor, campo):

    if valor is None or str(valor).strip() == "":

        raise AssertionError(f"{campo} queda vacio")


def _registrar(resultados, modulo, funcion):

    try:

        detalle = funcion() or ""
        resultados.append((modulo, "OK", detalle, ""))
        return True

    except Exception as exc:

        resultados.append(
            (
                modulo,
                "FALLO",
                str(exc),
                traceback.format_exc(),
            )
        )
        return False


def _validar_campos_v7_13(conn):

    faltantes = []

    for tabla, columnas_esperadas in CAMPOS_V7_13.items():

        columnas_reales = _columnas(conn, tabla)
        faltantes.extend(
            f"{tabla}.{columna}"
            for columna in sorted(columnas_esperadas - columnas_reales)
        )

    if faltantes:

        raise AssertionError(
            "Faltan columnas v7.13: " + ", ".join(faltantes)
        )

    return "campos v7.13 disponibles"


def _validar_explotacion(ctx):

    with _conectar() as conn:

        fila = conn.execute("SELECT * FROM explotacion LIMIT 1").fetchone()

    if fila is None:

        raise AssertionError("No existe explotacion")

    fila = dict(fila)
    _assert_igual(fila["titular"], "Titular Integral V7", "titular")
    _assert_igual(fila["nif"], "00000000T", "nif")
    _assert_igual(
        fila["nombre_explotacion"],
        "Explotacion integral v7",
        "nombre_explotacion",
    )
    _assert_no_vacio(fila["identificador_oficial"], "identificador_oficial")
    _assert_no_vacio(fila["registro_autonomico"], "registro_autonomico")
    _assert_igual(fila["municipio"], "Jumilla", "municipio")
    _assert_igual(fila["provincia"], "Murcia", "provincia")
    _assert_igual(fila["tipo_explotacion"], "Agraria", "tipo_explotacion")
    _assert_igual(
        fila["orientacion_productiva"],
        "Frutos secos",
        "orientacion_productiva",
    )
    _assert_igual(fila["fecha_alta"], "2026-01-01", "fecha_alta")
    _assert_igual(int(fila["agricultor_activo"]), 1, "agricultor_activo")
    _assert_igual(int(fila["joven_agricultor"]), 0, "joven_agricultor")
    return "titular, REGEPA/identificador y registro autonomico persistidos"


def _validar_campana(ctx):

    with _conectar() as conn:

        fila = _fila(conn, "campanas", ctx["campana_id"])

    _assert_igual(fila["nombre"], "2025/2026", "campana")
    _assert_igual(fila["fecha_inicio"], "2025-10-01", "fecha_inicio")
    _assert_igual(fila["fecha_fin"], "2026-09-30", "fecha_fin")
    _assert_igual(int(fila["activa"]), 1, "activa")
    return "campana activa 2025/2026"


def _validar_terceros_personas(ctx):

    with _conectar() as conn:

        cliente = _fila(conn, "clientes", ctx["cliente_id"])
        proveedor = _fila(conn, "proveedores", ctx["proveedor_id"])
        aplicador = _fila(conn, "personas", ctx["aplicador_id"])

    _assert_no_vacio(cliente["nombre"], "cliente")
    _assert_no_vacio(proveedor["nombre"], "proveedor")
    _assert_no_vacio(aplicador["nombre"], "aplicador")
    _assert_no_vacio(aplicador["carnet_aplicador"], "carnet_aplicador")
    return "cliente, proveedor y aplicador creados"


def _validar_parcela_cultivo(ctx):

    with _conectar() as conn:

        parcela = _fila(conn, "parcelas", ctx["parcela_id"])
        cultivo = _fila(conn, "cultivos", ctx["cultivo_id"])
        puente = conn.execute(
            """
            SELECT parcela_id, superficie
            FROM cultivo_parcelas
            WHERE cultivo_id=?
            """,
            (ctx["cultivo_id"],),
        ).fetchone()

    _assert_igual(parcela["provincia_sigpac"], 30, "provincia_sigpac")
    _assert_igual(parcela["municipio_sigpac"], 22, "municipio_sigpac")
    _assert_igual(parcela["agregado_sigpac"], 0, "agregado_sigpac")
    _assert_igual(parcela["zona_sigpac"], 0, "zona_sigpac")
    _assert_igual(parcela["poligono"], "7", "poligono")
    _assert_igual(parcela["parcela"], "45", "parcela")
    _assert_igual(parcela["recinto"], "2", "recinto")
    _assert_float(parcela["superficie_sigpac"], 4.5, "superficie_sigpac")
    _assert_igual(cultivo["nombre"], "ALMENDRO", "cultivo")
    _assert_igual(cultivo["codigo_siex"], "104", "codigo_siex")
    _assert_float(cultivo["superficie"], 4.5, "superficie cultivo")
    _assert_igual(
        cultivo["marco_plantacion"],
        "6x5",
        "marco_plantacion",
    )
    _assert_igual(
        int(cultivo["numero_arboles"]),
        1500,
        "numero_arboles",
    )

    if puente is None:

        raise AssertionError("No existe relacion cultivo_parcelas")

    _assert_igual(puente["parcela_id"], ctx["parcela_id"], "parcela asociada")
    return "parcela SIGPAC y cultivo_parcelas OK"


def _validar_maquinaria_equipos(ctx):

    with _conectar() as conn:

        maquinaria = _fila(conn, "maquinaria", ctx["maquinaria_id"])
        equipo = _fila(conn, "equipos_aplicacion", ctx["equipo_id"])

    _assert_igual(maquinaria["matricula"], "0000AAA", "matricula maquinaria")
    _assert_igual(maquinaria["numero_roma"], "ROMA-MAQ-V7", "ROMA maquinaria")
    _assert_igual(
        maquinaria["numero_serie"],
        "SER-MAQ-INTEGRAL-V7",
        "serie maquinaria",
    )
    _assert_igual(maquinaria["fecha_compra"], "2025-01-15", "fecha_compra")
    _assert_float(maquinaria["horas_uso"], 100.0, "horas_uso")
    _assert_igual(equipo["matricula"], "EQ-0000AAA", "matricula equipo")
    _assert_igual(equipo["numero_roma"], "ROMA-EQ-INTEGRAL-V7", "ROMA equipo")
    _assert_igual(equipo["numero_serie"], "SER-EQ-V7", "serie equipo")
    _assert_igual(
        equipo["fecha_adquisicion"],
        "2025-02-15",
        "fecha_adquisicion",
    )
    _assert_float(equipo["capacidad_litros"], 600.0, "capacidad_litros")
    _assert_igual(equipo["fecha_revision"], "2026-02-01", "fecha_revision")
    _assert_igual(
        equipo["fecha_proxima_revision"],
        "2027-02-01",
        "fecha_proxima_revision",
    )
    return "maquinaria y equipo con campos v7.13 persistidos"


def _validar_producto(ctx):

    with _conectar() as conn:

        producto = _fila(conn, "productos_fito", ctx["producto_id"])

    _assert_igual(producto["numero_registro"], "REG-V7-0001", "registro")
    _assert_no_vacio(producto["materia_activa"], "materia_activa")
    _assert_no_vacio(producto["plazo_seguridad"], "plazo_seguridad")
    _assert_igual(int(producto["activo"]), 1, "activo")
    return "producto fitosanitario completo"


def _validar_actuaciones(ctx):

    with _conectar() as conn:

        tratamiento = _fila(conn, "tratamientos", ctx["tratamiento_id"])
        fertilizacion = _fila(conn, "fertilizaciones", ctx["fertilizacion_id"])
        practica = _fila(conn, "practicas_culturales", ctx["practica_id"])
        cosecha = _fila(conn, "cosecha", ctx["cosecha_id"])
        tp = conn.execute(
            "SELECT COUNT(*) FROM tratamiento_parcelas WHERE tratamiento_id=?",
            (ctx["tratamiento_id"],),
        ).fetchone()[0]
        tc = conn.execute(
            "SELECT COUNT(*) FROM tratamiento_cultivos WHERE tratamiento_id=?",
            (ctx["tratamiento_id"],),
        ).fetchone()[0]
        fp = conn.execute(
            "SELECT COUNT(*) FROM fertilizacion_parcelas WHERE fertilizacion_id=?",
            (ctx["fertilizacion_id"],),
        ).fetchone()[0]
        fc = conn.execute(
            """
            SELECT COUNT(*)
            FROM fertilizacion_cultivos
            WHERE fertilizacion_id=?
            """,
            (ctx["fertilizacion_id"],),
        ).fetchone()[0]
        pp = conn.execute(
            """
            SELECT COUNT(*)
            FROM practicas_culturales_parcelas
            WHERE practica_id=?
            """,
            (ctx["practica_id"],),
        ).fetchone()[0]
        pc = conn.execute(
            """
            SELECT COUNT(*)
            FROM practicas_culturales_cultivos
            WHERE practica_id=?
            """,
            (ctx["practica_id"],),
        ).fetchone()[0]
        cp = conn.execute(
            "SELECT COUNT(*) FROM cosecha_parcelas WHERE cosecha_id=?",
            (ctx["cosecha_id"],),
        ).fetchone()[0]
        cc = conn.execute(
            "SELECT COUNT(*) FROM cosecha_cultivos WHERE cosecha_id=?",
            (ctx["cosecha_id"],),
        ).fetchone()[0]

    _assert_igual(tratamiento["cultivo_id"], ctx["cultivo_id"], "cultivo trat")
    _assert_igual(tratamiento["producto_id"], ctx["producto_id"], "producto")
    _assert_igual(tratamiento["aplicador_id"], ctx["aplicador_id"], "aplicador")
    _assert_igual(
        tratamiento["equipo_aplicacion_id"],
        ctx["equipo_id"],
        "equipo tratamiento",
    )
    _assert_no_vacio(tratamiento["dosis"], "dosis tratamiento")
    _assert_float(tratamiento["caldo"], 400.0, "caldo")
    _assert_float(tratamiento["superficie_tratada"], 4.5, "superficie tratada")
    _assert_igual(tp, 1, "tratamiento_parcelas")
    _assert_igual(tc, 1, "tratamiento_cultivos")

    _assert_igual(fertilizacion["cultivo_id"], ctx["cultivo_id"], "cultivo fert")
    _assert_no_vacio(fertilizacion["producto"], "producto fertilizacion")
    _assert_float(fertilizacion["cantidad"], 250.0, "cantidad fertilizacion")
    _assert_igual(fp, 1, "fertilizacion_parcelas")
    _assert_igual(fc, 1, "fertilizacion_cultivos")

    _assert_igual(practica["cultivo_id"], ctx["cultivo_id"], "cultivo practica")
    _assert_igual(practica["maquinaria_id"], ctx["maquinaria_id"], "maquinaria")
    _assert_igual(practica["proveedor_id"], ctx["proveedor_id"], "proveedor")
    _assert_no_vacio(practica["labor"], "labor")
    _assert_igual(pp, 1, "practicas_culturales_parcelas")
    _assert_igual(pc, 1, "practicas_culturales_cultivos")

    _assert_igual(cosecha["cultivo_id"], ctx["cultivo_id"], "cultivo cosecha")
    _assert_igual(cosecha["cliente_id"], ctx["cliente_id"], "cliente cosecha")
    _assert_float(cosecha["cantidad"], 1200.0, "cantidad cosecha")
    _assert_igual(cosecha["unidad"], "kg", "unidad cosecha")
    _assert_igual(cp, 1, "cosecha_parcelas")
    _assert_igual(cc, 1, "cosecha_cultivos")
    return "tratamientos, fertilizacion, practicas y cosecha completos"


def _validar_contabilidad(ctx):

    with _conectar() as conn:

        ingreso = _fila(conn, "movimientos_economicos", ctx["ingreso_id"])
        gasto = _fila(conn, "movimientos_economicos", ctx["gasto_id"])
        lineas = conn.execute(
            "SELECT COUNT(*) FROM movimientos_economicos_lineas_iva"
        ).fetchone()[0]

    _assert_igual(ingreso["cliente_id"], ctx["cliente_id"], "cliente ingreso")
    _assert_igual(ingreso["campana_id"], ctx["campana_id"], "campana ingreso")
    _assert_float(ingreso["base_imponible"], 1000.0, "base ingreso")
    _assert_float(ingreso["iva"], 210.0, "iva ingreso")
    _assert_float(ingreso["total"], 1210.0, "total ingreso")
    _assert_igual(int(ingreso["pendiente"]), 0, "ingreso cobrado")
    _assert_igual(gasto["proveedor_id"], ctx["proveedor_id"], "proveedor gasto")
    _assert_float(gasto["total"], 363.0, "total gasto")
    _assert_igual(int(gasto["pendiente"]), 1, "gasto pendiente")
    _assert_igual(lineas, 2, "lineas IVA")
    return "ingreso, gasto, IVA y totales OK"


def _validar_mapas_sigpac(ctx):

    estado = mapas_mod._leer_estado_geometrias()
    parcelas = mapas_mod._leer_parcelas_mapa()
    cultivos = mapas_mod._leer_cultivos_mapa()

    if estado.empty or parcelas.empty:

        raise AssertionError("Mapas/SIGPAC no recupera parcelas")

    if "sigpac_geojson_estado" not in estado.columns:

        raise AssertionError("Mapas no devuelve estado SIGPAC normalizado")

    fila_estado = estado[estado["id"].astype(int) == int(ctx["parcela_id"])]
    if fila_estado.empty:

        raise AssertionError("Mapas no recupera parcela pre-v8")

    _assert_igual(
        fila_estado.iloc[0]["sigpac_geojson_estado"],
        "Sin geometría",
        "estado SIGPAC derivado",
    )
    _assert_igual(
        int(parcelas.iloc[0]["id"]),
        int(ctx["parcela_id"]),
        "parcela mapa",
    )

    if cultivos.empty:

        raise AssertionError("Mapas no recupera cultivos asociados")

    return "sin geometria disponible y sin error"


def _imprimir_resumen(resultados, ctx, schema_info):

    print("Prueba completa pre-v8 v7.14")
    print("============================")
    print(f"Base usada: {DB_PRE_V8}")
    print(f"PRAGMA user_version: {schema_info.get('user_version')}")
    print(f"Numero de tablas: {schema_info.get('table_count')}")
    print("")
    print("| Modulo | Resultado | Observaciones |")
    print("| --- | --- | --- |")

    for modulo, estado, detalle, _ in resultados:

        print(f"| {modulo} | {estado} | {detalle} |")

    print("")
    print("Salidas")
    print(
        "- Revision SIEX: "
        f"{ctx.get('revision_siex_registros')} registros, "
        f"{ctx.get('revision_siex_filas')} avisos/info, "
        f"{ctx.get('revision_siex_bloqueos')} bloqueos"
    )
    print(
        "- Excel SIEX: "
        f"{ctx.get('excel_siex_nombre')} "
        f"({ctx.get('excel_siex_bytes')} bytes)"
    )
    print(
        "- PDF oficial: "
        f"{ctx.get('pdf_oficial')} "
        f"({ctx.get('pdf_oficial_bytes')} bytes)"
    )

    fallos = [fila for fila in resultados if fila[1] != "OK"]

    if fallos:

        print("")
        print("Errores")

        for modulo, _, detalle, traza in fallos:

            print(f"- {modulo}: {detalle}")
            print(traza)

    print("")
    print("Candidata v8.0: " + ("No" if fallos else "Si"))
    print("Resultado: " + ("FALLO" if fallos else "OK"))


def main():

    resultados = []
    schema_info = {}
    revision = pd.DataFrame()
    ctx = {
        "ahora": datetime.now().isoformat(timespec="seconds"),
    }

    _registrar(
        resultados,
        "Base v7 limpia",
        lambda: (
            flujo_integral._preparar_base_v7(),
            "base aislada creada",
        )[1],
    )

    with flujo_integral._conectar_v7() as conn:

        _registrar(
            resultados,
            "Diagnostico esquema",
            lambda: schema_info.update(
                flujo_integral._validar_schema(conn)
            ) or "schema v7 limpio",
        )
        _registrar(
            resultados,
            "Campos v7.13",
            lambda: _validar_campos_v7_13(conn),
        )
        _registrar(
            resultados,
            "Configuracion inicial / explotacion",
            lambda: flujo_integral._insertar_explotacion(conn, ctx),
        )
        _registrar(resultados, "Campana", lambda: flujo_integral._insertar_campana(conn, ctx))
        _registrar(
            resultados,
            "Terceros",
            lambda: flujo_integral._insertar_cliente_proveedor(conn, ctx),
        )
        _registrar(resultados, "Parcelas", lambda: flujo_integral._insertar_parcela(conn, ctx))
        _registrar(resultados, "Cultivos", lambda: flujo_integral._insertar_cultivo(conn, ctx))
        _registrar(
            resultados,
            "Maquinaria y equipos",
            lambda: flujo_integral._insertar_maquinaria_equipo(conn, ctx),
        )
        _registrar(
            resultados,
            "Productos fito / aplicador",
            lambda: flujo_integral._insertar_producto_persona(conn, ctx),
        )
        _registrar(
            resultados,
            "Tratamientos",
            lambda: flujo_integral._insertar_tratamiento(conn, ctx),
        )
        _registrar(
            resultados,
            "Fertilizacion",
            lambda: flujo_integral._insertar_fertilizacion(conn, ctx),
        )
        _registrar(
            resultados,
            "Practicas culturales",
            lambda: flujo_integral._insertar_practica(conn, ctx),
        )
        _registrar(resultados, "Cosecha", lambda: flujo_integral._insertar_cosecha(conn, ctx))
        _registrar(
            resultados,
            "Contabilidad",
            lambda: flujo_integral._insertar_contabilidad(conn, ctx),
        )
        conn.commit()
        _registrar(
            resultados,
            "Conteos relacionales",
            lambda: flujo_integral._validar_conteos(conn) or "conteos OK",
        )

    _registrar(resultados, "Validacion explotacion", lambda: _validar_explotacion(ctx))
    _registrar(resultados, "Validacion campana", lambda: _validar_campana(ctx))
    _registrar(
        resultados,
        "Validacion terceros/personas",
        lambda: _validar_terceros_personas(ctx),
    )
    _registrar(
        resultados,
        "Validacion parcelas/cultivos",
        lambda: _validar_parcela_cultivo(ctx),
    )
    _registrar(
        resultados,
        "Validacion maquinaria/equipos",
        lambda: _validar_maquinaria_equipos(ctx),
    )
    _registrar(resultados, "Validacion productos", lambda: _validar_producto(ctx))
    _registrar(
        resultados,
        "Validacion actuaciones",
        lambda: _validar_actuaciones(ctx),
    )
    _registrar(
        resultados,
        "Validacion contabilidad",
        lambda: _validar_contabilidad(ctx),
    )

    with flujo_integral._conectar_v7() as conn:

        _registrar(
            resultados,
            "Informes",
            lambda: flujo_integral._validar_informes(conn, ctx) or "informes OK",
        )

        def _revision():

            nonlocal revision
            revision = flujo_integral._validar_revision_siex(conn, ctx)
            return (
                f"{ctx.get('revision_siex_registros')} registros, "
                f"{ctx.get('revision_siex_bloqueos')} bloqueos"
            )

        _registrar(resultados, "Revision SIEX", _revision)

    _registrar(
        resultados,
        "Excel SIEX",
        lambda: flujo_integral._validar_excel_siex(ctx, revision) or "Excel generado",
    )
    _registrar(
        resultados,
        "PDF oficial",
        lambda: flujo_integral._validar_pdf_oficial(ctx) or "PDF generado",
    )
    _registrar(
        resultados,
        "Mapas / SIGPAC",
        lambda: _validar_mapas_sigpac(ctx),
    )

    _imprimir_resumen(resultados, ctx, schema_info)

    return 1 if any(fila[1] != "OK" for fila in resultados) else 0


if __name__ == "__main__":

    raise SystemExit(main())
