#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import os
import pandas as pd
import sqlite3
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
DB_PRUEBA = APP_ROOT / "runtime" / "v7" / "prueba_listados_v7.db"
EXPLOTACION_NOMBRE_PRUEBA = "EXPLOTACIÓN PRUEBA V7"
EXPLOTACION_IDENTIFICADOR_PRUEBA = "REGEPA-V7-001"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

os.environ.setdefault("CUADERNOPRO_DB_PATH", str(DB_PRUEBA))

from core.schema_v7 import asegurar_ampliaciones_v8_0_1, crear_base_v7  # noqa: E402


def _conectar():

    conn = sqlite3.connect(DB_PRUEBA)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _columnas(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _insertar(conn, tabla, valores):

    columnas = _columnas(conn, tabla)
    filtrados = {
        columna: valor
        for columna, valor in valores.items()
        if columna in columnas
    }
    nombres = list(filtrados)

    if not nombres:

        raise AssertionError(f"No hay columnas compatibles para {tabla}")

    cursor = conn.execute(
        f"""
        INSERT INTO {tabla}
        ({','.join(nombres)})
        VALUES ({','.join(['?'] * len(nombres))})
        """,
        [filtrados[columna] for columna in nombres],
    )
    return int(cursor.lastrowid)


def _uno(conn, sql, params=()):

    conn.row_factory = sqlite3.Row
    fila = conn.execute(sql, params).fetchone()
    conn.row_factory = None

    if fila is None:

        return {}

    return dict(fila)


def _texto(valor):

    if valor is None:

        return ""

    return str(valor).strip()


def _normalizar(valor):

    if isinstance(valor, float):

        return f"{valor:.4f}".rstrip("0").rstrip(".")

    return _texto(valor)


def _listado_explotacion_normalizado(fila):

    return {
        "Nombre de la explotación": _texto(fila.get("nombre_explotacion")),
        "Código REGEPA / identificador oficial": _texto(
            fila.get("identificador_oficial")
        ),
        "Titular": _texto(fila.get("titular")),
        "NIF": _texto(fila.get("nif")),
        "Municipio": _texto(fila.get("municipio")),
        "Provincia": _texto(fila.get("provincia")),
    }


def _comprobar(nombre, fila, esperados, opcionales_no_v7=None):

    opcionales_no_v7 = opcionales_no_v7 or []
    vacios = []
    recuperados = {}

    for campo, esperado in esperados.items():

        valor = fila.get(campo)
        recuperados[campo] = valor

        if _normalizar(valor) != _normalizar(esperado):

            vacios.append(
                f"{campo}: esperado={esperado!r}, recuperado={valor!r}"
            )

    estado = "OK" if not vacios else "FALLO"
    print(f"{nombre}: {estado}")
    print("  campos guardados:")

    for campo, valor in esperados.items():

        print(f"  - {campo}: {valor!r}")

    print("  campos recuperados:")

    for campo, valor in recuperados.items():

        print(f"  - {campo}: {valor!r}")

    if opcionales_no_v7:

        print("  campos no aplicables en v7 limpia:")

        for campo in opcionales_no_v7:

            print(f"  - {campo}")

    if vacios:

        print("  campos vacios o distintos inesperados:")

        for error in vacios:

            print(f"  - {error}")

    return estado == "OK"


def _preparar_datos(conn):

    marca = datetime.now().strftime("%Y%m%d%H%M%S")
    ahora = datetime.now().isoformat(timespec="seconds")
    prefijo = f"AUDITORIA LISTADOS V7 {marca}"

    explotacion_id = _insertar(
        conn,
        "explotacion",
        {
            "nombre_explotacion": EXPLOTACION_NOMBRE_PRUEBA,
            "titular": f"{prefijo} titular",
            "nif": "00000000T",
            "direccion": "Camino Explotacion 1",
            "municipio": "Jumilla",
            "provincia": "Murcia",
            "codigo_postal": "30520",
            "identificador_oficial": EXPLOTACION_IDENTIFICADOR_PRUEBA,
            "tipo_identificador_oficial": "REGEPA",
            "registro_autonomico": "REG-AUT-LISTADOS-V7",
            "tipo_explotacion": "Agraria",
            "orientacion_productiva": "Frutos secos",
            "fecha_alta": "2026-01-10",
            "agricultor_activo": 1,
            "joven_agricultor": 0,
            "observaciones": "explotacion auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    campana_id = _insertar(
        conn,
        "campanas",
        {
            "nombre": f"{prefijo} campana",
            "fecha_inicio": "2025-09-01",
            "fecha_fin": "2026-08-31",
            "activa": 0,
            "estado": "abierta",
            "observaciones": "campana auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    cliente_id = _insertar(
        conn,
        "clientes",
        {
            "nombre": f"{prefijo} cliente",
            "nif": "B00000001",
            "telefono": "600000001",
            "email": "cliente-listados@example.com",
            "direccion": "Calle Cliente 1",
            "poblacion": "Jumilla",
            "provincia": "Murcia",
            "codigo_postal": "30520",
            "observaciones": "cliente auditoria listados",
            "activo": 1,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    proveedor_id = _insertar(
        conn,
        "proveedores",
        {
            "nombre": f"{prefijo} proveedor",
            "nif": "B00000002",
            "telefono": "600000002",
            "email": "proveedor-listados@example.com",
            "direccion": "Calle Proveedor 1",
            "poblacion": "Jumilla",
            "provincia": "Murcia",
            "codigo_postal": "30520",
            "actividad": "Servicios agrarios",
            "observaciones": "proveedor auditoria listados",
            "activo": 1,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    persona_id = _insertar(
        conn,
        "personas",
        {
            "nombre": f"{prefijo} aplicador",
            "nif": "00000001A",
            "telefono": "600000003",
            "email": "aplicador-listados@example.com",
            "rol": "Aplicador fitosanitario",
            "carnet_aplicador": "AUD-CARNET-V7",
            "numero_asesor": "",
            "observaciones": "persona auditoria listados",
            "activo": 1,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    producto_id = _insertar(
        conn,
        "productos_fito",
        {
            "nombre": f"{prefijo} producto fito",
            "numero_registro": "REG-AUD-V7",
            "materia_activa": "Materia activa auditoria",
            "titular": "Titular auditoria",
            "uso_autorizado": "Uso auditoria",
            "plazo_seguridad": "7",
            "observaciones": "producto auditoria listados",
            "activo": 1,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    parcela_id = _insertar(
        conn,
        "parcelas",
        {
            "nombre": f"{prefijo} parcela",
            "provincia_sigpac": 30,
            "municipio_sigpac": 22,
            "agregado_sigpac": 0,
            "zona_sigpac": 0,
            "poligono": "10",
            "parcela": "20",
            "recinto": "30",
            "superficie_sigpac": 2.5,
            "uso_sigpac": "TA",
            "activa": 1,
            "observaciones": "parcela auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    cultivo_id = _insertar(
        conn,
        "cultivos",
        {
            "campana_id": campana_id,
            "nombre": f"{prefijo} almendro",
            "variedad": "Guara",
            "codigo_siex": "104",
            "superficie": 2.5,
            "ano_plantacion": 2020,
            "marco_plantacion": "7x7",
            "numero_arboles": 510,
            "activo": 1,
            "observaciones": "cultivo auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    _insertar(
        conn,
        "cultivo_parcelas",
        {
            "cultivo_id": cultivo_id,
            "parcela_id": parcela_id,
            "superficie": 2.5,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    maquinaria_id = _insertar(
        conn,
        "maquinaria",
        {
            "tipo": "Tractor",
            "marca": "Marca auditoria",
            "modelo": "Modelo auditoria",
            "matricula": "AUD-1234",
            "numero_roma": "ROMA-AUD-V7",
            "numero_serie": "SERIE-MAQ-AUD-V7",
            "fecha_compra": "2025-05-01",
            "horas_uso": 321.5,
            "descripcion": f"{prefijo} tractor",
            "observaciones": "maquinaria auditoria listados",
            "activa": 1,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    equipo_id = _insertar(
        conn,
        "equipos_aplicacion",
        {
            "nombre": f"{prefijo} equipo aplicacion",
            "marca": "Marca equipo auditoria",
            "modelo": "Modelo equipo auditoria",
            "tipo": "Pulverizador",
            "matricula": "EQ-AUD-1234",
            "numero_roma": "ROMA-EQ-AUD-V7",
            "numero_serie": "SERIE-AUD-V7",
            "fecha_adquisicion": "2025-06-01",
            "capacidad_litros": 650.0,
            "fecha_revision": "2026-01-15",
            "fecha_proxima_revision": "2027-01-15",
            "observaciones": "equipo auditoria listados",
            "activo": 1,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    tratamiento_id = _insertar(
        conn,
        "tratamientos",
        {
            "campana_id": campana_id,
            "cultivo_id": cultivo_id,
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-03-01",
            "producto_id": producto_id,
            "aplicador_id": persona_id,
            "equipo_aplicacion_id": equipo_id,
            "plaga_motivo": "Plaga auditoria",
            "dosis": "1 l/ha",
            "caldo": 250.0,
            "superficie_tratada": 2.5,
            "plazo_seguridad": "7",
            "eficacia": "B",
            "observaciones": "tratamiento auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    _insertar(
        conn,
        "tratamiento_parcelas",
        {
            "tratamiento_id": tratamiento_id,
            "parcela_id": parcela_id,
            "superficie": 2.5,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    fertilizacion_id = _insertar(
        conn,
        "fertilizaciones",
        {
            "campana_id": campana_id,
            "cultivo_id": cultivo_id,
            "fecha": "2026-02-01",
            "producto": "Abono auditoria",
            "tipo_fertilizante": "NPK",
            "cantidad": 120.0,
            "unidad": "kg",
            "unidad_normalizada": "kg",
            "superficie": 2.5,
            "codigo_actuacion_siex": "FERT-AUD",
            "observaciones": "fertilizacion auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    _insertar(
        conn,
        "fertilizacion_parcelas",
        {
            "fertilizacion_id": fertilizacion_id,
            "parcela_id": parcela_id,
            "superficie": 2.5,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    practica_id = _insertar(
        conn,
        "practicas_culturales",
        {
            "campana_id": campana_id,
            "cultivo_id": cultivo_id,
            "fecha": "2026-01-20",
            "labor": "Poda auditoria",
            "codigo_actuacion_siex": "PRAC-AUD",
            "superficie": 2.5,
            "maquinaria_id": maquinaria_id,
            "proveedor_id": proveedor_id,
            "observaciones": "practica auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    _insertar(
        conn,
        "practicas_culturales_parcelas",
        {
            "practica_id": practica_id,
            "parcela_id": parcela_id,
            "superficie": 2.5,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    cosecha_id = _insertar(
        conn,
        "cosecha",
        {
            "campana_id": campana_id,
            "cultivo_id": cultivo_id,
            "fecha": "2026-08-20",
            "cantidad": 1000.0,
            "unidad": "kg",
            "destino": "Venta auditoria",
            "cliente_id": cliente_id,
            "observaciones": "cosecha auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    _insertar(
        conn,
        "cosecha_parcelas",
        {
            "cosecha_id": cosecha_id,
            "parcela_id": parcela_id,
            "superficie": 2.5,
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    ingreso_id = _insertar(
        conn,
        "movimientos_economicos",
        {
            "campana_id": campana_id,
            "cultivo_id": cultivo_id,
            "fecha": "2026-09-01",
            "tipo": "ingreso",
            "categoria": "Venta cosecha",
            "concepto": "Ingreso auditoria",
            "numero_factura": "FAC-AUD-I",
            "cliente_id": cliente_id,
            "base_imponible": 1000.0,
            "iva": 100.0,
            "retencion": 0.0,
            "total": 1100.0,
            "pendiente": 0,
            "fecha_pago": "2026-09-10",
            "observaciones": "ingreso auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    gasto_id = _insertar(
        conn,
        "movimientos_economicos",
        {
            "campana_id": campana_id,
            "cultivo_id": cultivo_id,
            "fecha": "2026-04-01",
            "tipo": "gasto",
            "categoria": "Servicios",
            "concepto": "Gasto auditoria",
            "numero_factura": "FAC-AUD-G",
            "proveedor_id": proveedor_id,
            "base_imponible": 300.0,
            "iva": 63.0,
            "retencion": 0.0,
            "total": 363.0,
            "pendiente": 1,
            "fecha_pago": "",
            "observaciones": "gasto auditoria listados",
            "created_at": ahora,
            "updated_at": ahora,
        },
    )
    conn.commit()
    return {
        "prefijo": prefijo,
        "explotacion_id": explotacion_id,
        "campana_id": campana_id,
        "cliente_id": cliente_id,
        "proveedor_id": proveedor_id,
        "persona_id": persona_id,
        "producto_id": producto_id,
        "parcela_id": parcela_id,
        "cultivo_id": cultivo_id,
        "maquinaria_id": maquinaria_id,
        "equipo_id": equipo_id,
        "tratamiento_id": tratamiento_id,
        "fertilizacion_id": fertilizacion_id,
        "practica_id": practica_id,
        "cosecha_id": cosecha_id,
        "ingreso_id": ingreso_id,
        "gasto_id": gasto_id,
    }


def _comprobar_explotacion(conn, ctx):

    columnas = _columnas(conn, "explotacion")
    fila = _uno(
        conn,
        """
        SELECT
            id,
            nombre_explotacion,
            titular,
            nif,
            municipio,
            provincia,
            codigo_postal,
            identificador_oficial,
            registro_autonomico,
            tipo_explotacion,
            orientacion_productiva,
            fecha_alta,
            agricultor_activo,
            joven_agricultor,
            observaciones
        FROM explotacion
        WHERE id=?
        """,
        (ctx["explotacion_id"],),
    )
    legacy = {}

    for columna in ("codigo_regea", "codigo_regepa"):

        if columna in columnas:

            legacy[columna] = _uno(
                conn,
                f"SELECT {columna} FROM explotacion WHERE id=?",
                (ctx["explotacion_id"],),
            ).get(columna)

    listado = _listado_explotacion_normalizado(fila)
    import modules.explotacion as explotacion_mod

    datos_modulo = explotacion_mod._normalizar_alias_explotacion(
        pd.DataFrame([fila])
    )

    for columna in explotacion_mod.COLUMNAS_EXPLOTACION:

        if columna not in datos_modulo:

            if columna in explotacion_mod.COLUMNAS_BOOLEANAS_EXPLOTACION:

                datos_modulo[columna] = False

            else:

                datos_modulo[columna] = ""

    datos_modulo["fecha_alta"] = pd.to_datetime(
        datos_modulo["fecha_alta"],
        errors="coerce",
    )
    columnas_editor = (
        explotacion_mod._columnas_visuales_datos_explotacion(columnas)
    )
    listado_visual = explotacion_mod._preparar_dataframe_editor_explotacion(
        datos_modulo,
        columnas_editor
    )
    listado_borrado = (
        explotacion_mod._preparar_dataframe_borrado_explotacion(
            datos_modulo
        )
    )
    columnas_visuales = list(listado_visual.columns)
    columnas_borrado = list(listado_borrado.columns)
    nombre_recuperado = listado["Nombre de la explotación"]
    identificador_recuperado = listado[
        "Código REGEPA / identificador oficial"
    ]
    errores = []

    if nombre_recuperado != EXPLOTACION_NOMBRE_PRUEBA:

        errores.append(
            "nombre_explotacion no recuperado con el valor esperado"
        )

    if identificador_recuperado != EXPLOTACION_IDENTIFICADOR_PRUEBA:

        errores.append(
            "identificador_oficial no recuperado con el valor esperado"
        )

    if not nombre_recuperado:

        errores.append("nombre_explotacion queda vacio o None")

    if not identificador_recuperado:

        errores.append("identificador_oficial queda vacio")

    if fila.get("registro_autonomico") != "REG-AUT-LISTADOS-V7":

        errores.append("registro_autonomico no recuperado")

    if fila.get("tipo_explotacion") != "Agraria":

        errores.append("tipo_explotacion no recuperado")

    if fila.get("orientacion_productiva") != "Frutos secos":

        errores.append("orientacion_productiva no recuperada")

    if (
        legacy.get("codigo_regea") == EXPLOTACION_IDENTIFICADOR_PRUEBA
        and not identificador_recuperado
    ):

        errores.append("el identificador cae solo en codigo_regea legacy")

    columnas_crudas = {
        "nombre_explotacion",
        "codigo_regea",
        "codigo_regepa",
        "identificador_oficial",
    }

    if columnas_crudas.intersection(columnas_visuales):

        errores.append("el listado visual contiene nombres tecnicos")

    if columnas_crudas.intersection(columnas_borrado):

        errores.append("la vista de borrado contiene nombres tecnicos")

    for columna_obligatoria in (
        "Nombre de la explotación",
        "Código REGEPA / identificador oficial",
        "Registro autonómico",
        "Tipo de explotación",
        "Orientación productiva",
        "Fecha de alta",
        "Agricultor activo",
        "Joven agricultor",
    ):

        if columna_obligatoria not in columnas_visuales:

            errores.append(
                f"falta columna visual obligatoria: {columna_obligatoria}"
            )

    nombre_visual = _texto(
        listado_visual.iloc[0].get("Nombre de la explotación")
    )
    identificador_visual = _texto(
        listado_visual.iloc[0].get(
            "Código REGEPA / identificador oficial"
        )
    )

    if not nombre_visual:

        errores.append("Nombre de la explotación queda vacio en editor")

    if not identificador_visual:

        errores.append(
            "Código REGEPA / identificador oficial queda vacio en editor"
        )

    estado = "OK" if not errores else "FALLO"
    print(f"Explotacion: {estado}")
    print(f"  Nombre guardado: {EXPLOTACION_NOMBRE_PRUEBA!r}")
    print(
        "  Identificador guardado: "
        f"{EXPLOTACION_IDENTIFICADOR_PRUEBA!r}"
    )
    print(f"  Nombre recuperado: {nombre_recuperado!r}")
    print(f"  Identificador recuperado: {identificador_recuperado!r}")
    print("  listado normalizado:")

    for campo, valor in listado.items():

        print(f"  - {campo}: {valor!r}")

    print("  columnas visuales del editor:")

    for columna in columnas_visuales:

        print(f"  - {columna}")

    print("  columnas visuales de borrado:")

    for columna in columnas_borrado:

        print(f"  - {columna}")

    print("  aliases legacy reales en tabla:")
    print(
        "  - codigo_regea: "
        f"{legacy.get('codigo_regea', 'ausente')!r}"
    )
    print(
        "  - codigo_regepa: "
        f"{legacy.get('codigo_regepa', 'ausente')!r}"
    )

    if errores:

        print("  campos vacios o distintos inesperados:")

        for error in errores:

            print(f"  - {error}")

    return estado == "OK"


def _comprobar_explotacion_fallback_titular(conn, ctx):

    import modules.asistente_inicio as asistente_mod
    import modules.explotacion as explotacion_mod

    titular = f"{ctx['prefijo']} titular fallback"
    nombre_explotacion = asistente_mod._nombre_explotacion_o_titular(
        "",
        titular
    )
    fallback_id = _insertar(
        conn,
        "explotacion",
        {
            "nombre_explotacion": nombre_explotacion,
            "titular": titular,
            "nif": "00000002F",
            "municipio": "Jumilla",
            "provincia": "Murcia",
            "identificador_oficial": "REGEPA-V7-FALLBACK",
            "tipo_identificador_oficial": "REGEPA",
            "observaciones": "fallback nombre explotacion",
        },
    )
    fila = _uno(
        conn,
        """
        SELECT
            id,
            nombre_explotacion,
            titular,
            nif,
            municipio,
            provincia,
            identificador_oficial,
            observaciones
        FROM explotacion
        WHERE id=?
        """,
        (fallback_id,),
    )
    datos_modulo = explotacion_mod._normalizar_alias_explotacion(
        pd.DataFrame([fila])
    )

    for columna in explotacion_mod.COLUMNAS_EXPLOTACION:

        if columna not in datos_modulo:

            datos_modulo[columna] = (
                False
                if columna in explotacion_mod.COLUMNAS_BOOLEANAS_EXPLOTACION
                else ""
            )

    datos_modulo["fecha_alta"] = pd.to_datetime(
        datos_modulo["fecha_alta"],
        errors="coerce",
    )
    columnas_editor = (
        explotacion_mod._columnas_visuales_datos_explotacion(
            _columnas(conn, "explotacion")
        )
    )
    listado_visual = explotacion_mod._preparar_dataframe_editor_explotacion(
        datos_modulo,
        columnas_editor
    )
    errores = []

    if fila.get("nombre_explotacion") != titular:

        errores.append(
            "nombre_explotacion no queda persistido con el titular"
        )

    if _texto(
        listado_visual.iloc[0].get("Nombre de la explotación")
    ) != titular:

        errores.append(
            "Datos de la explotación muestra nombre vacío tras fallback"
        )

    estado = "OK" if not errores else "FALLO"
    print(f"Explotacion fallback titular: {estado}")
    print(f"  Titular: {titular!r}")
    print(f"  Nombre persistido: {fila.get('nombre_explotacion')!r}")

    if errores:

        print("  campos vacios o distintos inesperados:")

        for error in errores:

            print(f"  - {error}")

    return estado == "OK"


def _comprobar_maquinaria(conn, ctx):

    fila = _uno(
        conn,
        """
        SELECT
            descripcion AS nombre,
            tipo,
            marca,
            modelo,
            matricula,
            numero_roma,
            numero_serie,
            fecha_compra,
            horas_uso,
            observaciones
        FROM maquinaria
        WHERE id=?
        """,
        (ctx["maquinaria_id"],),
    )
    return _comprobar(
        "Maquinaria",
        fila,
        {
            "nombre": f"{ctx['prefijo']} tractor",
            "tipo": "Tractor",
            "marca": "Marca auditoria",
            "modelo": "Modelo auditoria",
            "matricula": "AUD-1234",
            "numero_roma": "ROMA-AUD-V7",
            "numero_serie": "SERIE-MAQ-AUD-V7",
            "fecha_compra": "2025-05-01",
            "horas_uso": 321.5,
            "observaciones": "maquinaria auditoria listados",
        },
        [],
    )


def _comprobar_equipo(conn, ctx):

    fila = _uno(
        conn,
        """
        SELECT
            nombre,
            tipo,
            marca,
            modelo,
            matricula,
            numero_roma,
            numero_serie,
            fecha_adquisicion,
            capacidad_litros,
            fecha_revision,
            fecha_proxima_revision,
            observaciones
        FROM equipos_aplicacion
        WHERE id=?
        """,
        (ctx["equipo_id"],),
    )
    return _comprobar(
        "Equipo aplicacion",
        fila,
        {
            "nombre": f"{ctx['prefijo']} equipo aplicacion",
            "tipo": "Pulverizador",
            "marca": "Marca equipo auditoria",
            "modelo": "Modelo equipo auditoria",
            "matricula": "EQ-AUD-1234",
            "numero_roma": "ROMA-EQ-AUD-V7",
            "numero_serie": "SERIE-AUD-V7",
            "fecha_adquisicion": "2025-06-01",
            "capacidad_litros": 650.0,
            "fecha_revision": "2026-01-15",
            "fecha_proxima_revision": "2027-01-15",
            "observaciones": "equipo auditoria listados",
        },
        [],
    )


def _comprobar_parcela(conn, ctx):

    fila = _uno(
        conn,
        """
        SELECT
            nombre,
            provincia_sigpac,
            municipio_sigpac,
            agregado_sigpac,
            zona_sigpac,
            poligono,
            parcela,
            recinto,
            superficie_sigpac,
            uso_sigpac,
            observaciones
        FROM parcelas
        WHERE id=?
        """,
        (ctx["parcela_id"],),
    )
    return _comprobar(
        "Parcela",
        fila,
        {
            "nombre": f"{ctx['prefijo']} parcela",
            "provincia_sigpac": 30,
            "municipio_sigpac": 22,
            "agregado_sigpac": 0,
            "zona_sigpac": 0,
            "poligono": "10",
            "parcela": "20",
            "recinto": "30",
            "superficie_sigpac": 2.5,
            "uso_sigpac": "TA",
            "observaciones": "parcela auditoria listados",
        },
    )


def _comprobar_cultivo(conn, ctx):

    fila = _uno(
        conn,
        """
        SELECT
            cultivos.nombre AS cultivo,
            cultivos.codigo_siex,
            cultivos.superficie,
            cultivos.marco_plantacion,
            cultivos.numero_arboles,
            campanas.nombre AS campana,
            GROUP_CONCAT(parcelas.nombre, ', ') AS parcelas
        FROM cultivos
        JOIN campanas ON campanas.id = cultivos.campana_id
        JOIN cultivo_parcelas ON cultivo_parcelas.cultivo_id = cultivos.id
        JOIN parcelas ON parcelas.id = cultivo_parcelas.parcela_id
        WHERE cultivos.id=?
        GROUP BY cultivos.id
        """,
        (ctx["cultivo_id"],),
    )
    return _comprobar(
        "Cultivo",
        fila,
        {
            "cultivo": f"{ctx['prefijo']} almendro",
            "codigo_siex": "104",
            "superficie": 2.5,
            "marco_plantacion": "7x7",
            "numero_arboles": 510,
            "campana": f"{ctx['prefijo']} campana",
            "parcelas": f"{ctx['prefijo']} parcela",
        },
        ["cultivos.parcela_id", "cultivos.especie"],
    )


def _comprobar_tratamiento(conn, ctx):

    fila = _uno(
        conn,
        """
        SELECT
            campanas.nombre AS campana,
            cultivos.nombre AS cultivo,
            productos_fito.nombre AS producto,
            productos_fito.numero_registro,
            personas.nombre AS aplicador,
            equipos_aplicacion.nombre AS equipo,
            tratamientos.fecha_inicio,
            tratamientos.fecha_fin,
            tratamientos.plaga_motivo,
            tratamientos.dosis,
            tratamientos.caldo,
            tratamientos.superficie_tratada,
            tratamientos.eficacia,
            tratamientos.observaciones,
            GROUP_CONCAT(parcelas.nombre, ', ') AS parcelas
        FROM tratamientos
        JOIN campanas ON campanas.id = tratamientos.campana_id
        JOIN cultivos ON cultivos.id = tratamientos.cultivo_id
        JOIN productos_fito ON productos_fito.id = tratamientos.producto_id
        LEFT JOIN personas ON personas.id = tratamientos.aplicador_id
        LEFT JOIN equipos_aplicacion
            ON equipos_aplicacion.id = tratamientos.equipo_aplicacion_id
        LEFT JOIN tratamiento_parcelas
            ON tratamiento_parcelas.tratamiento_id = tratamientos.id
        LEFT JOIN parcelas ON parcelas.id = tratamiento_parcelas.parcela_id
        WHERE tratamientos.id=?
        GROUP BY tratamientos.id
        """,
        (ctx["tratamiento_id"],),
    )
    return _comprobar(
        "Tratamiento",
        fila,
        {
            "campana": f"{ctx['prefijo']} campana",
            "cultivo": f"{ctx['prefijo']} almendro",
            "producto": f"{ctx['prefijo']} producto fito",
            "numero_registro": "REG-AUD-V7",
            "aplicador": f"{ctx['prefijo']} aplicador",
            "equipo": f"{ctx['prefijo']} equipo aplicacion",
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-03-01",
            "plaga_motivo": "Plaga auditoria",
            "dosis": "1 l/ha",
            "caldo": 250.0,
            "superficie_tratada": 2.5,
            "eficacia": "B",
            "observaciones": "tratamiento auditoria listados",
            "parcelas": f"{ctx['prefijo']} parcela",
        },
    )


def _comprobar_fertilizacion(conn, ctx):

    fila = _uno(
        conn,
        """
        SELECT
            campanas.nombre AS campana,
            cultivos.nombre AS cultivo,
            fertilizaciones.fecha,
            fertilizaciones.producto,
            fertilizaciones.tipo_fertilizante,
            fertilizaciones.cantidad,
            fertilizaciones.unidad,
            fertilizaciones.superficie,
            fertilizaciones.observaciones,
            GROUP_CONCAT(parcelas.nombre, ', ') AS parcelas
        FROM fertilizaciones
        JOIN campanas ON campanas.id = fertilizaciones.campana_id
        JOIN cultivos ON cultivos.id = fertilizaciones.cultivo_id
        LEFT JOIN fertilizacion_parcelas
            ON fertilizacion_parcelas.fertilizacion_id = fertilizaciones.id
        LEFT JOIN parcelas ON parcelas.id = fertilizacion_parcelas.parcela_id
        WHERE fertilizaciones.id=?
        GROUP BY fertilizaciones.id
        """,
        (ctx["fertilizacion_id"],),
    )
    return _comprobar(
        "Fertilizacion",
        fila,
        {
            "campana": f"{ctx['prefijo']} campana",
            "cultivo": f"{ctx['prefijo']} almendro",
            "fecha": "2026-02-01",
            "producto": "Abono auditoria",
            "tipo_fertilizante": "NPK",
            "cantidad": 120.0,
            "unidad": "kg",
            "superficie": 2.5,
            "observaciones": "fertilizacion auditoria listados",
            "parcelas": f"{ctx['prefijo']} parcela",
        },
    )


def _comprobar_practica(conn, ctx):

    fila = _uno(
        conn,
        """
        SELECT
            campanas.nombre AS campana,
            cultivos.nombre AS cultivo,
            practicas_culturales.fecha,
            practicas_culturales.labor,
            practicas_culturales.superficie,
            maquinaria.descripcion AS maquinaria,
            proveedores.nombre AS proveedor,
            practicas_culturales.observaciones,
            GROUP_CONCAT(parcelas.nombre, ', ') AS parcelas
        FROM practicas_culturales
        JOIN campanas ON campanas.id = practicas_culturales.campana_id
        JOIN cultivos ON cultivos.id = practicas_culturales.cultivo_id
        LEFT JOIN maquinaria ON maquinaria.id = practicas_culturales.maquinaria_id
        LEFT JOIN proveedores ON proveedores.id = practicas_culturales.proveedor_id
        LEFT JOIN practicas_culturales_parcelas
            ON practicas_culturales_parcelas.practica_id =
               practicas_culturales.id
        LEFT JOIN parcelas
            ON parcelas.id = practicas_culturales_parcelas.parcela_id
        WHERE practicas_culturales.id=?
        GROUP BY practicas_culturales.id
        """,
        (ctx["practica_id"],),
    )
    return _comprobar(
        "Practica cultural",
        fila,
        {
            "campana": f"{ctx['prefijo']} campana",
            "cultivo": f"{ctx['prefijo']} almendro",
            "fecha": "2026-01-20",
            "labor": "Poda auditoria",
            "superficie": 2.5,
            "maquinaria": f"{ctx['prefijo']} tractor",
            "proveedor": f"{ctx['prefijo']} proveedor",
            "observaciones": "practica auditoria listados",
            "parcelas": f"{ctx['prefijo']} parcela",
        },
    )


def _comprobar_cosecha(conn, ctx):

    fila = _uno(
        conn,
        """
        SELECT
            campanas.nombre AS campana,
            cultivos.nombre AS cultivo,
            cosecha.fecha,
            cosecha.cantidad,
            cosecha.unidad,
            clientes.nombre AS cliente,
            cosecha.destino,
            cosecha.observaciones,
            GROUP_CONCAT(parcelas.nombre, ', ') AS parcelas
        FROM cosecha
        JOIN campanas ON campanas.id = cosecha.campana_id
        JOIN cultivos ON cultivos.id = cosecha.cultivo_id
        LEFT JOIN clientes ON clientes.id = cosecha.cliente_id
        LEFT JOIN cosecha_parcelas ON cosecha_parcelas.cosecha_id = cosecha.id
        LEFT JOIN parcelas ON parcelas.id = cosecha_parcelas.parcela_id
        WHERE cosecha.id=?
        GROUP BY cosecha.id
        """,
        (ctx["cosecha_id"],),
    )
    return _comprobar(
        "Cosecha",
        fila,
        {
            "campana": f"{ctx['prefijo']} campana",
            "cultivo": f"{ctx['prefijo']} almendro",
            "fecha": "2026-08-20",
            "cantidad": 1000.0,
            "unidad": "kg",
            "cliente": f"{ctx['prefijo']} cliente",
            "destino": "Venta auditoria",
            "observaciones": "cosecha auditoria listados",
            "parcelas": f"{ctx['prefijo']} parcela",
        },
        ["kg", "precio"],
    )


def _comprobar_contabilidad(conn, ctx, movimiento_id, tipo):

    tabla_tercero = "clientes" if tipo == "ingreso" else "proveedores"
    columna_id = "cliente_id" if tipo == "ingreso" else "proveedor_id"
    fila = _uno(
        conn,
        f"""
        SELECT
            movimientos_economicos.fecha,
            movimientos_economicos.tipo,
            movimientos_economicos.concepto,
            campanas.nombre AS campana,
            cultivos.nombre AS cultivo,
            {tabla_tercero}.nombre AS tercero,
            movimientos_economicos.base_imponible,
            movimientos_economicos.iva,
            movimientos_economicos.total,
            movimientos_economicos.pendiente,
            movimientos_economicos.numero_factura,
            movimientos_economicos.observaciones
        FROM movimientos_economicos
        JOIN campanas ON campanas.id = movimientos_economicos.campana_id
        JOIN cultivos ON cultivos.id = movimientos_economicos.cultivo_id
        LEFT JOIN {tabla_tercero}
            ON {tabla_tercero}.id = movimientos_economicos.{columna_id}
        WHERE movimientos_economicos.id=?
        """,
        (movimiento_id,),
    )
    esperado_tercero = (
        f"{ctx['prefijo']} cliente"
        if tipo == "ingreso"
        else f"{ctx['prefijo']} proveedor"
    )
    return _comprobar(
        f"Contabilidad {tipo}",
        fila,
        {
            "fecha": "2026-09-01" if tipo == "ingreso" else "2026-04-01",
            "tipo": tipo,
            "concepto": (
                "Ingreso auditoria"
                if tipo == "ingreso"
                else "Gasto auditoria"
            ),
            "campana": f"{ctx['prefijo']} campana",
            "cultivo": f"{ctx['prefijo']} almendro",
            "tercero": esperado_tercero,
            "base_imponible": 1000.0 if tipo == "ingreso" else 300.0,
            "iva": 100.0 if tipo == "ingreso" else 63.0,
            "total": 1100.0 if tipo == "ingreso" else 363.0,
            "pendiente": 0 if tipo == "ingreso" else 1,
            "numero_factura": "FAC-AUD-I" if tipo == "ingreso" else "FAC-AUD-G",
            "observaciones": (
                "ingreso auditoria listados"
                if tipo == "ingreso"
                else "gasto auditoria listados"
            ),
        },
    )


def _asegurar_base_prueba():

    if DB_PRUEBA.exists():

        return

    crear_base_v7(DB_PRUEBA, sobrescribir=True)


def main():

    print("Prueba listados v7")
    print("==================")
    print(f"Base usada: {DB_PRUEBA}")

    try:

        _asegurar_base_prueba()

    except Exception as exc:

        print("Resultado: FALLO")
        print(f"No se pudo preparar la base de prueba: {exc}")
        return 1

    with _conectar() as conn:

        asegurar_ampliaciones_v8_0_1(conn)
        conn.commit()

        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        print(f"PRAGMA user_version: {version}")

        if version != 7:

            print("Resultado: FALLO")
            print("La base no es v7")
            return 1

        ctx = _preparar_datos(conn)
        comprobaciones = [
            _comprobar_explotacion(conn, ctx),
            _comprobar_explotacion_fallback_titular(conn, ctx),
            _comprobar_maquinaria(conn, ctx),
            _comprobar_equipo(conn, ctx),
            _comprobar_parcela(conn, ctx),
            _comprobar_cultivo(conn, ctx),
            _comprobar_tratamiento(conn, ctx),
            _comprobar_fertilizacion(conn, ctx),
            _comprobar_practica(conn, ctx),
            _comprobar_cosecha(conn, ctx),
            _comprobar_contabilidad(conn, ctx, ctx["ingreso_id"], "ingreso"),
            _comprobar_contabilidad(conn, ctx, ctx["gasto_id"], "gasto"),
        ]

    if all(comprobaciones):

        print("Resultado: OK")
        return 0

    print("Resultado: FALLO")
    return 1


if __name__ == "__main__":

    raise SystemExit(main())
