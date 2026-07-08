import sqlite3

import pandas as pd
import streamlit as st

from core.borrado import borrar_registros_seguro
from core.db import conectar, leer
from core.fechas import (
    detectar_campana_por_fecha,
    fecha_es_a_datetime,
    formatear_fecha_es,
    parsear_fecha_es,
    preparar_columnas_fecha_tabla,
)
from core.filtros import mostrar_filtros_dataframe
from core.ui_tablas import (
    preparar_column_config_visual,
    preparar_dataframe_visual,
)
from services.facturas import (
    eliminar_archivo_factura,
    eliminar_documento_factura,
    guardar_facturas_pdf,
    leer_facturas_movimientos,
    ruta_factura_absoluta,
)


TIPOS_IVA_HABITUALES = [21.0, 10.0, 7.0, 5.0, 4.0, 0.0]


def _redondear_importe(valor):

    if valor is None or pd.isna(valor):

        valor = 0

    return round(float(valor), 2)


def _formatear_importe(valor):

    return f"{_redondear_importe(valor):.2f} €".replace(".", ",")


def _formatear_porcentaje(valor):

    if valor is None or pd.isna(valor):

        valor = 0

    numero = float(valor)

    if numero.is_integer():

        return f"{int(numero)}%"

    return f"{numero:.2f}%".replace(".", ",")


def _texto(valor):

    if valor is None or pd.isna(valor):

        return ""

    return str(valor).strip()


def _entero_o_none(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return None

    return int(numero)


def _leer_dataframe(sql, params=None, conn=None):

    if params is None:

        params = ()

    if conn is not None:

        return pd.read_sql_query(sql, conn, params=params)

    return leer(sql, params)


def _tabla_existe_conn(conn, tabla):

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


def _columnas_tabla_conn(conn, tabla):

    if not _tabla_existe_conn(conn, tabla):

        return set()

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _columnas_tabla(tabla):

    conn = conectar()

    try:

        return _columnas_tabla_conn(conn, tabla)

    finally:

        conn.close()


def tabla_tiene_columna(conn, tabla, columna):

    return columna in _columnas_tabla_conn(conn, tabla)


def _valor_texto_columna(tabla, columna, columnas, defecto="''"):

    if columna in columnas:

        return f"COALESCE({tabla}.{columna},{defecto})"

    return defecto


def _valor_numerico_columna(tabla, columna, columnas, defecto="NULL"):

    if columna in columnas:

        return f"{tabla}.{columna}"

    return defecto


def _coalesce_sql(expresiones):

    return "COALESCE(" + ",".join(expresiones) + ")"


def _expr_nombre_cultivo(columnas_cultivos, tabla="cultivos"):

    if "especie" in columnas_cultivos:

        return f"COALESCE({tabla}.especie,'')"

    if "nombre" in columnas_cultivos:

        return f"COALESCE({tabla}.nombre,'')"

    return "''"


def _expr_variedad_cultivo(columnas_cultivos, tabla="cultivos"):

    return _valor_texto_columna(tabla, "variedad", columnas_cultivos)


def _expr_sistema_cultivo(columnas_cultivos, tabla="cultivos"):

    return _valor_texto_columna(tabla, "sistema", columnas_cultivos)


def _expr_codigo_siex_cultivo(columnas_cultivos, tabla="cultivos"):

    return _valor_texto_columna(tabla, "codigo_siex", columnas_cultivos)


def _expr_superficie_cultivo(columnas_cultivos, tabla="cultivos"):

    return _valor_numerico_columna(tabla, "superficie", columnas_cultivos)


def _expr_activo_cultivo(columnas_cultivos, tabla="cultivos"):

    if "activo" in columnas_cultivos:

        return f"COALESCE({tabla}.activo,1)"

    return "1"


def _anadir_si_existe(destino, columnas, columna, valor):

    if columna in columnas:

        destino[columna] = valor


def _calcular_linea_iva(base_imponible, tipo_iva):

    base = _redondear_importe(base_imponible)
    tipo = float(tipo_iva or 0)
    cuota = _redondear_importe(base * tipo / 100)

    return {
        "base_imponible": base,
        "tipo_iva": tipo,
        "cuota_iva": cuota,
        "total_linea": _redondear_importe(base + cuota)
    }


def _numeros_distintos(valor_original, valor_editado, tolerancia=0.005):

    original = pd.to_numeric(
        pd.Series([valor_original]),
        errors="coerce"
    ).iloc[0]
    editado = pd.to_numeric(
        pd.Series([valor_editado]),
        errors="coerce"
    ).iloc[0]

    if pd.isna(original) and pd.isna(editado):

        return False

    if pd.isna(original) or pd.isna(editado):

        return True

    return abs(float(original) - float(editado)) > tolerancia


def _resumen_desglose_iva(lineas_iva):

    if lineas_iva is None or lineas_iva.empty:

        return {}

    lineas = lineas_iva.copy()
    lineas["movimiento_id"] = pd.to_numeric(
        lineas["movimiento_id"],
        errors="coerce"
    )
    lineas["base_imponible"] = pd.to_numeric(
        lineas["base_imponible"],
        errors="coerce"
    ).fillna(0)
    lineas["tipo_iva"] = pd.to_numeric(
        lineas["tipo_iva"],
        errors="coerce"
    ).fillna(0)
    lineas = lineas.dropna(subset=["movimiento_id"])

    if lineas.empty:

        return {}

    resumen = {}
    agrupadas = (
        lineas
        .groupby(["movimiento_id", "tipo_iva"], as_index=False)
        ["base_imponible"]
        .sum()
    )

    for movimiento_id, grupo in agrupadas.groupby("movimiento_id"):

        partes = []

        for _, fila in grupo.sort_values("tipo_iva").iterrows():

            partes.append(
                f"{_formatear_porcentaje(fila['tipo_iva'])}: "
                f"{_formatear_importe(fila['base_imponible'])}"
            )

        resumen[int(movimiento_id)] = "; ".join(partes)

    return resumen


def _leer_terceros_contabilidad(tabla, solo_activos=True):

    sql = (
        f"SELECT id,nombre,nif,activo FROM {tabla}"
    )
    params = ()

    if solo_activos:

        sql += " WHERE COALESCE(activo,1)=1"

    sql += " ORDER BY nombre,id"

    return leer(sql, params)


def _etiqueta_tercero(fila, texto_sin):

    if fila is None:

        return texto_sin

    nombre = _texto(fila.get("nombre")) or f"ID {int(fila['id'])}"
    nif = _texto(fila.get("nif"))
    etiqueta = nombre

    if nif:

        etiqueta += f" — NIF {nif}"

    activo = pd.to_numeric(fila.get("activo", 1), errors="coerce")

    if not pd.isna(activo) and int(activo) == 0:

        etiqueta += " (inactivo)"

    return etiqueta


def _tercero_por_id(terceros, tercero_id):

    tercero_id = _entero_o_none(tercero_id)

    if tercero_id is None or terceros is None or terceros.empty:

        return None

    coincidencias = terceros[
        terceros["id"].astype(int) == int(tercero_id)
    ]

    if coincidencias.empty:

        return None

    return coincidencias.iloc[0]


def _selector_tercero(
    terceros,
    label,
    key,
    texto_sin,
    valor_actual=None,
    seleccionar_primero=False,
):

    ids = (
        terceros["id"].dropna().astype(int).tolist()
        if terceros is not None
        and not terceros.empty
        and "id" in terceros.columns
        else []
    )
    opciones = [None] + ids
    valor_actual = _entero_o_none(valor_actual)

    if valor_actual is not None and valor_actual in opciones:

        indice = opciones.index(valor_actual)

    elif seleccionar_primero and ids:

        indice = 1

    else:

        indice = 0

    return st.selectbox(
        label,
        opciones,
        index=indice,
        format_func=lambda valor: (
            texto_sin
            if valor is None
            else _etiqueta_tercero(
                _tercero_por_id(terceros, valor),
                texto_sin
            )
        ),
        key=key,
    )


def _formatear_hectareas(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return ""

    return f"{float(numero):.2f} ha"


def _nombre_cultivo(fila):

    if fila is None:

        return ""

    partes = [
        _texto(
            fila.get("especie")
            or fila.get("nombre")
            or fila.get("cultivo_v6")
        ),
        _texto(fila.get("variedad") or fila.get("variedad_v6")),
        _texto(fila.get("sistema") or fila.get("sistema_v6")),
    ]

    return " / ".join(parte for parte in partes if parte)


def _superficie_cultivo_para_etiqueta(fila):

    if fila is None:

        return None

    columnas = getattr(fila, "index", [])

    if "superficie_cultivo" in columnas:

        return fila.get("superficie_cultivo")

    return fila.get("superficie")


def _etiqueta_cultivo(fila):

    if fila is None:

        return "Sin cultivo"

    campana = _texto(fila.get("campana_cultivo") or fila.get("campana"))
    nombre = _nombre_cultivo(fila) or "Sin nombre"
    superficie = _formatear_hectareas(_superficie_cultivo_para_etiqueta(fila))
    codigo_siex = _texto(fila.get("codigo_siex"))
    partes = []

    if campana:

        partes.append(f"Campaña {campana}")

    partes.append(nombre.upper())

    if superficie:

        partes.append(superficie)

    if codigo_siex:

        partes.append(f"SIEX {codigo_siex}")

    return " — ".join(partes)


def _leer_cultivos_contabilidad(conn=None):

    columnas_cultivos = (
        _columnas_tabla_conn(conn, "cultivos")
        if conn is not None
        else _columnas_tabla("cultivos")
    )

    if not columnas_cultivos:

        return pd.DataFrame()

    expr_campana_id = (
        "cultivos.campana_id"
        if "campana_id" in columnas_cultivos
        else "NULL"
    )
    expr_nombre = _expr_nombre_cultivo(columnas_cultivos)
    expr_variedad = _expr_variedad_cultivo(columnas_cultivos)
    expr_sistema = _expr_sistema_cultivo(columnas_cultivos)
    expr_codigo_siex = _expr_codigo_siex_cultivo(columnas_cultivos)
    expr_superficie = _expr_superficie_cultivo(columnas_cultivos)
    expr_activo = _expr_activo_cultivo(columnas_cultivos)
    join_campanas = (
        "LEFT JOIN campanas ON campanas.id = cultivos.campana_id"
        if "campana_id" in columnas_cultivos
        else ""
    )
    expr_campana = (
        "COALESCE(campanas.nombre,'')"
        if "campana_id" in columnas_cultivos
        else "''"
    )

    cultivos = _leer_dataframe(
        f"""
        SELECT
            cultivos.id,
            {expr_campana_id} AS campana_id,
            {expr_campana} AS campana,
            {expr_nombre} AS especie,
            {expr_nombre} AS nombre,
            {expr_variedad} AS variedad,
            {expr_sistema} AS sistema,
            {expr_codigo_siex} AS codigo_siex,
            {expr_superficie} AS superficie,
            {expr_activo} AS activo
        FROM cultivos
        {join_campanas}
        ORDER BY campana DESC, especie, variedad, sistema, cultivos.id
        """,
        conn=conn,
    )

    if cultivos.empty:

        return cultivos

    cultivos["cultivo_texto"] = cultivos.apply(_nombre_cultivo, axis=1)
    cultivos["etiqueta"] = cultivos.apply(_etiqueta_cultivo, axis=1)
    return cultivos


def _cultivo_por_id(cultivos, cultivo_id):

    cultivo_id = _entero_o_none(cultivo_id)

    if cultivo_id is None or cultivos is None or cultivos.empty:

        return None

    coincidencias = cultivos[cultivos["id"].astype(int) == int(cultivo_id)]

    if coincidencias.empty:

        return None

    return coincidencias.iloc[0]


def _selector_cultivo_contabilidad(
    cultivos,
    key,
    campana_id=None,
    valor_actual=None,
    seleccionar_primero=False,
):

    ids = []

    if cultivos is not None and not cultivos.empty:

        cultivos_ordenados = cultivos.copy()
        campana_id = _entero_o_none(campana_id)

        if campana_id is not None and "campana_id" in cultivos_ordenados.columns:

            cultivos_ordenados["prioridad_campana"] = (
                pd.to_numeric(
                    cultivos_ordenados["campana_id"],
                    errors="coerce",
                ) != campana_id
            ).astype(int)
            cultivos_ordenados = cultivos_ordenados.sort_values(
                by=["prioridad_campana", "campana", "cultivo_texto", "id"]
            )

        ids = cultivos_ordenados["id"].dropna().astype(int).tolist()

    opciones = [None] + ids
    valor_actual = _entero_o_none(valor_actual)

    if valor_actual is not None and valor_actual in opciones:

        indice = opciones.index(valor_actual)

    elif seleccionar_primero and ids:

        indice = 1

    else:

        indice = 0

    return st.selectbox(
        "Cultivo (opcional)",
        opciones,
        index=indice,
        format_func=lambda valor: (
            "Sin cultivo"
            if valor is None
            else _etiqueta_cultivo(_cultivo_por_id(cultivos, valor))
        ),
        key=key,
    )


def _cultivo_legacy_para_guardar(cultivo_id, cultivos, cultivo_legacy=""):

    cultivo = _cultivo_por_id(cultivos, cultivo_id)

    if cultivo is None:

        return _texto(cultivo_legacy)

    return _nombre_cultivo(cultivo)


def _insertar_movimiento_compatible(conn, datos):

    columnas = _columnas_tabla_conn(conn, "movimientos_economicos")
    valores = {}
    tipo = _texto(datos.get("tipo"))
    pagado = bool(datos.get("pagado"))
    cliente_id = (
        _entero_o_none(datos.get("cliente_id"))
        if tipo == "Ingreso"
        else None
    )
    proveedor_id = (
        _entero_o_none(datos.get("proveedor_id"))
        if tipo == "Gasto"
        else None
    )
    iva_importe = datos.get("iva_importe", datos.get("iva"))
    pendiente = datos.get("pendiente", 0 if pagado else 1)
    ahora = pd.Timestamp.now().isoformat()

    _anadir_si_existe(valores, columnas, "campana_id", datos.get("campana_id"))
    _anadir_si_existe(valores, columnas, "cultivo_id", datos.get("cultivo_id"))
    _anadir_si_existe(valores, columnas, "fecha", datos.get("fecha"))
    _anadir_si_existe(valores, columnas, "tipo", tipo)
    _anadir_si_existe(
        valores,
        columnas,
        "categoria",
        _texto(datos.get("categoria")),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "concepto",
        _texto(datos.get("concepto")),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "numero_factura",
        _texto(datos.get("numero_factura")),
    )
    _anadir_si_existe(valores, columnas, "cliente_id", cliente_id)
    _anadir_si_existe(valores, columnas, "proveedor_id", proveedor_id)
    _anadir_si_existe(
        valores,
        columnas,
        "base_imponible",
        datos.get("base_imponible"),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "iva_porcentaje",
        datos.get("iva_porcentaje"),
    )
    _anadir_si_existe(valores, columnas, "iva_importe", iva_importe)
    _anadir_si_existe(valores, columnas, "iva", iva_importe)
    _anadir_si_existe(valores, columnas, "retencion", datos.get("retencion"))
    _anadir_si_existe(valores, columnas, "total", datos.get("total"))
    _anadir_si_existe(
        valores,
        columnas,
        "forma_pago",
        _texto(datos.get("forma_pago")),
    )
    _anadir_si_existe(valores, columnas, "pagado", int(pagado))
    _anadir_si_existe(valores, columnas, "pendiente", int(pendiente))
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_pago",
        _texto(datos.get("fecha_pago")),
    )
    _anadir_si_existe(valores, columnas, "tercero", _texto(datos.get("tercero")))
    _anadir_si_existe(
        valores,
        columnas,
        "nif_tercero",
        _texto(datos.get("nif_tercero")),
    )
    _anadir_si_existe(valores, columnas, "cultivo", _texto(datos.get("cultivo")))
    _anadir_si_existe(
        valores,
        columnas,
        "observaciones",
        _texto(datos.get("observaciones")),
    )
    _anadir_si_existe(valores, columnas, "created_at", ahora)
    _anadir_si_existe(valores, columnas, "updated_at", ahora)

    if not valores:

        raise sqlite3.OperationalError(
            "La tabla movimientos_economicos no tiene columnas utiles"
        )

    nombres = list(valores)
    cursor = conn.execute(
        f"""
        INSERT INTO movimientos_economicos
        ({','.join(nombres)})
        VALUES ({','.join(['?'] * len(nombres))})
        """,
        [valores[columna] for columna in nombres],
    )
    return int(cursor.lastrowid)


def _actualizar_movimiento_compatible(conn, movimiento_id, datos):

    columnas = _columnas_tabla_conn(conn, "movimientos_economicos")
    valores = {}
    tipo = _texto(datos.get("tipo"))

    for columna in (
        "campana_id",
        "cultivo_id",
        "fecha",
        "tipo",
        "categoria",
        "concepto",
        "numero_factura",
        "base_imponible",
        "retencion",
        "total",
        "fecha_pago",
        "observaciones",
    ):

        if columna in columnas and columna in datos:

            valores[columna] = datos[columna]

    if "cliente_id" in columnas and (
        "cliente_id" in datos
        or "tipo" in datos
    ):

        valores["cliente_id"] = (
            _entero_o_none(datos.get("cliente_id"))
            if tipo == "Ingreso"
            else None
        )

    if "proveedor_id" in columnas and (
        "proveedor_id" in datos
        or "tipo" in datos
    ):

        valores["proveedor_id"] = (
            _entero_o_none(datos.get("proveedor_id"))
            if tipo == "Gasto"
            else None
        )

    if "iva_porcentaje" in columnas and "iva_porcentaje" in datos:

        valores["iva_porcentaje"] = datos.get("iva_porcentaje")

    if "iva_importe" in columnas and (
        "iva_importe" in datos
        or "iva" in datos
    ):

        valores["iva_importe"] = datos.get("iva_importe", datos.get("iva"))

    if "iva" in columnas and ("iva_importe" in datos or "iva" in datos):

        valores["iva"] = datos.get("iva_importe", datos.get("iva"))

    if "forma_pago" in columnas and "forma_pago" in datos:

        valores["forma_pago"] = _texto(datos.get("forma_pago"))

    if "pagado" in columnas and "pagado" in datos:

        valores["pagado"] = int(bool(datos.get("pagado")))

    if "pendiente" in columnas and "pagado" in datos:

        valores["pendiente"] = 0 if bool(datos.get("pagado")) else 1

    for columna in ("tercero", "nif_tercero", "cultivo"):

        if columna in columnas and columna in datos:

            valores[columna] = _texto(datos.get(columna))

    if "updated_at" in columnas:

        valores["updated_at"] = pd.Timestamp.now().isoformat()

    if not valores:

        return

    asignaciones = ",".join(f"{columna}=?" for columna in valores)
    conn.execute(
        f"UPDATE movimientos_economicos SET {asignaciones} WHERE id=?",
        [valores[columna] for columna in valores] + [int(movimiento_id)],
    )


def _resolver_tercero_movimiento(fila):

    tipo = _texto(fila.get("tipo"))
    tercero_legacy = _texto(fila.get("tercero"))
    nif_legacy = _texto(fila.get("nif_tercero"))

    if (
        tipo == "Ingreso"
        and _entero_o_none(fila.get("cliente_id")) is not None
    ):

        return pd.Series(
            {
                "tercero_resuelto": (
                    _texto(fila.get("cliente")) or tercero_legacy
                ),
                "nif_tercero_resuelto": (
                    _texto(fila.get("cliente_nif")) or nif_legacy
                ),
                "origen_tercero": "cliente_id",
            }
        )

    if (
        tipo == "Gasto"
        and _entero_o_none(fila.get("proveedor_id")) is not None
    ):

        return pd.Series(
            {
                "tercero_resuelto": (
                    _texto(fila.get("proveedor")) or tercero_legacy
                ),
                "nif_tercero_resuelto": (
                    _texto(fila.get("proveedor_nif")) or nif_legacy
                ),
                "origen_tercero": "proveedor_id",
            }
        )

    return pd.Series(
        {
            "tercero_resuelto": tercero_legacy,
            "nif_tercero_resuelto": nif_legacy,
            "origen_tercero": "texto",
        }
    )


def _tercero_legacy_para_guardar(
    tipo,
    cliente_id,
    proveedor_id,
    clientes,
    proveedores,
    tercero_legacy="",
    nif_legacy="",
):

    if tipo == "Ingreso" and cliente_id is not None:

        cliente = _tercero_por_id(clientes, cliente_id)

        if cliente is None:

            return _texto(tercero_legacy), _texto(nif_legacy)

        return (
            _texto(cliente.get("nombre")),
            _texto(cliente.get("nif")),
        )

    if tipo == "Gasto" and proveedor_id is not None:

        proveedor = _tercero_por_id(proveedores, proveedor_id)

        if proveedor is None:

            return _texto(tercero_legacy), _texto(nif_legacy)

        return (
            _texto(proveedor.get("nombre")),
            _texto(proveedor.get("nif")),
        )

    return _texto(tercero_legacy), _texto(nif_legacy)


def _texto_facturas(numero):

    numero = pd.to_numeric(numero, errors="coerce")

    if pd.isna(numero) or int(numero) <= 0:

        return "Sin factura"

    numero = int(numero)

    if numero == 1:

        return "1 factura"

    return f"{numero} facturas"


def _formatear_bytes(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return ""

    numero = int(numero)

    if numero < 1024:

        return f"{numero} B"

    if numero < 1024 * 1024:

        return f"{numero / 1024:.1f} KB"

    return f"{numero / (1024 * 1024):.1f} MB"


def _formatear_movimiento_facturas(valor, movimientos):

    fila = movimientos[
        movimientos["id"].astype(int) == int(valor)
    ].iloc[0]
    fecha = formatear_fecha_es(fila["fecha"])
    concepto = _texto(fila["concepto"]) or "Sin concepto"

    return f"#{int(valor)} · {fecha} · {fila['tipo']} · {concepto}"


def _leer_campana_contabilidad(conn, campana_id):

    campana_id = _entero_o_none(campana_id)

    if campana_id is None:

        return None

    fila = conn.execute(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin,activa
        FROM campanas
        WHERE id=?
        """,
        (int(campana_id),),
    ).fetchone()

    if fila is None:

        return None

    return {
        "id": int(fila[0]),
        "nombre": fila[1],
        "fecha_inicio": fila[2],
        "fecha_fin": fila[3],
        "activa": int(fila[4] or 0),
    }


def _leer_campana_activa_contabilidad(conn):

    fila = conn.execute(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin,activa
        FROM campanas
        WHERE COALESCE(activa,0)=1
        ORDER BY id
        LIMIT 1
        """
    ).fetchone()

    if fila is None:

        return None

    return {
        "id": int(fila[0]),
        "nombre": fila[1],
        "fecha_inicio": fila[2],
        "fecha_fin": fila[3],
        "activa": int(fila[4] or 0),
    }


def _resolver_campana_movimiento_por_fecha(
    fecha_movimiento,
    campana_activa_id=None,
    conn=None,
):

    cerrar_conn = False

    if conn is None:

        conn = conectar()
        cerrar_conn = True

    try:

        campana_detectada = detectar_campana_por_fecha(
            fecha_movimiento,
            conn=conn,
        )

        if campana_detectada is not None:

            campana_activa_id = _entero_o_none(campana_activa_id)
            mensaje = ""

            if (
                campana_activa_id is not None
                and int(campana_detectada["id"]) != int(campana_activa_id)
            ):

                mensaje = (
                    "Movimiento asignado a la campaña "
                    f"{campana_detectada['nombre']} según la fecha "
                    f"{formatear_fecha_es(fecha_movimiento)}."
                )

            estado = (
                "detectada_solape"
                if int(campana_detectada.get("coincidencias", 1)) > 1
                else "detectada"
            )
            return {
                "campana_id": int(campana_detectada["id"]),
                "campana": campana_detectada,
                "estado": estado,
                "mensaje": mensaje,
                "aviso": campana_detectada.get("aviso", ""),
            }

        campana_fallback = (
            _leer_campana_contabilidad(conn, campana_activa_id)
            or _leer_campana_activa_contabilidad(conn)
        )

        if campana_fallback is None:

            return {
                "campana_id": None,
                "campana": None,
                "estado": "sin_campana",
                "mensaje": (
                    "La fecha no pertenece a ninguna campaña configurada y "
                    "no hay campaña activa disponible."
                ),
                "aviso": "",
            }

        return {
            "campana_id": int(campana_fallback["id"]),
            "campana": campana_fallback,
            "estado": "fallback_activa",
            "mensaje": (
                "La fecha no pertenece a ninguna campaña configurada. "
                "Se usará la campaña activa."
            ),
            "aviso": "",
        }

    finally:

        if cerrar_conn:

            conn.close()


def _mostrar_resolucion_campana_movimiento(resolucion):

    if not resolucion:

        return

    if resolucion.get("aviso"):

        st.warning(resolucion["aviso"])

    if resolucion.get("estado") == "fallback_activa":

        st.warning(resolucion["mensaje"])

    elif resolucion.get("estado") == "sin_campana":

        st.error(resolucion["mensaje"])

    elif resolucion.get("mensaje"):

        st.info(resolucion["mensaje"])

    campana = resolucion.get("campana") or {}

    if campana:

        st.caption(
            "Campaña del movimiento: "
            f"{campana.get('nombre', '')} "
            f"({formatear_fecha_es(campana.get('fecha_inicio'))} a "
            f"{formatear_fecha_es(campana.get('fecha_fin'))})."
        )


def _leer_resumen_contabilidad(campana_id, conn=None):

    columnas = (
        _columnas_tabla_conn(conn, "movimientos_economicos")
        if conn is not None
        else _columnas_tabla("movimientos_economicos")
    )

    if not columnas:

        return pd.Series(
            {
                "ingresos": 0,
                "gastos": 0,
                "iva_soportado": 0,
                "iva_repercutido": 0,
                "pendiente_pagar": 0,
                "pendiente_cobrar": 0,
            }
        )

    expr_total = (
        "COALESCE(movimientos_economicos.total,0)"
        if "total" in columnas
        else "0"
    )
    expr_iva = (
        "COALESCE(movimientos_economicos.iva_importe,0)"
        if "iva_importe" in columnas
        else (
            "COALESCE(movimientos_economicos.iva,0)"
            if "iva" in columnas
            else "0"
        )
    )

    if "pagado" in columnas:

        condicion_pendiente = "COALESCE(movimientos_economicos.pagado,0)=0"

    elif "pendiente" in columnas:

        condicion_pendiente = "COALESCE(movimientos_economicos.pendiente,0)=1"

    else:

        condicion_pendiente = "0"

    where = ""
    params = ()

    if "campana_id" in columnas:

        where = "WHERE movimientos_economicos.campana_id=?"
        params = (campana_id,)

    resumen = _leer_dataframe(
        f"""
        SELECT
        COALESCE(SUM(
            CASE WHEN tipo='Ingreso' THEN {expr_total} ELSE 0 END
        ),0) AS ingresos,
        COALESCE(SUM(
            CASE WHEN tipo='Gasto' THEN {expr_total} ELSE 0 END
        ),0) AS gastos,
        COALESCE(SUM(
            CASE WHEN tipo='Gasto' THEN {expr_iva} ELSE 0 END
        ),0) AS iva_soportado,
        COALESCE(SUM(
            CASE WHEN tipo='Ingreso' THEN {expr_iva} ELSE 0 END
        ),0) AS iva_repercutido,
        COALESCE(SUM(
            CASE WHEN tipo='Gasto' AND {condicion_pendiente}
            THEN {expr_total} ELSE 0 END
        ),0) AS pendiente_pagar,
        COALESCE(SUM(
            CASE WHEN tipo='Ingreso' AND {condicion_pendiente}
            THEN {expr_total} ELSE 0 END
        ),0) AS pendiente_cobrar
        FROM movimientos_economicos
        {where}
        """,
        params,
        conn=conn,
    )

    return resumen.iloc[0]


def _leer_movimientos_contabilidad(conn=None, movimiento_id=None):

    if conn is not None:

        movimientos_cols = _columnas_tabla_conn(conn, "movimientos_economicos")
        cultivos_cols = _columnas_tabla_conn(conn, "cultivos")
        tiene_documentos = _tabla_existe_conn(
            conn,
            "movimientos_economicos_documentos",
        )

    else:

        conn_tmp = conectar()

        try:

            movimientos_cols = _columnas_tabla_conn(
                conn_tmp,
                "movimientos_economicos",
            )
            cultivos_cols = _columnas_tabla_conn(conn_tmp, "cultivos")
            tiene_documentos = _tabla_existe_conn(
                conn_tmp,
                "movimientos_economicos_documentos",
            )

        finally:

            conn_tmp.close()

    if not movimientos_cols:

        return pd.DataFrame()

    expr_campana_id = _valor_numerico_columna(
        "movimientos_economicos",
        "campana_id",
        movimientos_cols,
    )
    expr_cultivo_id = _valor_numerico_columna(
        "movimientos_economicos",
        "cultivo_id",
        movimientos_cols,
    )
    expr_cliente_id = _valor_numerico_columna(
        "movimientos_economicos",
        "cliente_id",
        movimientos_cols,
    )
    expr_proveedor_id = _valor_numerico_columna(
        "movimientos_economicos",
        "proveedor_id",
        movimientos_cols,
    )
    expr_fecha = _valor_texto_columna(
        "movimientos_economicos",
        "fecha",
        movimientos_cols,
    )
    expr_tipo = _valor_texto_columna(
        "movimientos_economicos",
        "tipo",
        movimientos_cols,
    )
    expr_categoria = _valor_texto_columna(
        "movimientos_economicos",
        "categoria",
        movimientos_cols,
    )
    expr_concepto = _valor_texto_columna(
        "movimientos_economicos",
        "concepto",
        movimientos_cols,
    )
    expr_numero_factura = _valor_texto_columna(
        "movimientos_economicos",
        "numero_factura",
        movimientos_cols,
    )
    expr_base = _valor_numerico_columna(
        "movimientos_economicos",
        "base_imponible",
        movimientos_cols,
        "0",
    )
    expr_retencion = _valor_numerico_columna(
        "movimientos_economicos",
        "retencion",
        movimientos_cols,
        "0",
    )
    expr_total = _valor_numerico_columna(
        "movimientos_economicos",
        "total",
        movimientos_cols,
        "0",
    )
    expr_fecha_pago = _valor_texto_columna(
        "movimientos_economicos",
        "fecha_pago",
        movimientos_cols,
    )
    expr_observaciones = _valor_texto_columna(
        "movimientos_economicos",
        "observaciones",
        movimientos_cols,
    )
    expr_tercero = _valor_texto_columna(
        "movimientos_economicos",
        "tercero",
        movimientos_cols,
    )
    expr_nif_tercero = _valor_texto_columna(
        "movimientos_economicos",
        "nif_tercero",
        movimientos_cols,
    )
    expr_cultivo_legacy = _valor_texto_columna(
        "movimientos_economicos",
        "cultivo",
        movimientos_cols,
    )
    expr_forma_pago = _valor_texto_columna(
        "movimientos_economicos",
        "forma_pago",
        movimientos_cols,
    )

    if "iva_importe" in movimientos_cols:

        expr_iva_importe = "COALESCE(movimientos_economicos.iva_importe,0)"

    elif "iva" in movimientos_cols:

        expr_iva_importe = "COALESCE(movimientos_economicos.iva,0)"

    else:

        expr_iva_importe = "0"

    if "iva_porcentaje" in movimientos_cols:

        expr_iva_porcentaje = (
            "COALESCE(movimientos_economicos.iva_porcentaje,0)"
        )

    elif "base_imponible" in movimientos_cols and (
        "iva" in movimientos_cols
        or "iva_importe" in movimientos_cols
    ):

        expr_iva_porcentaje = (
            "CASE WHEN COALESCE(movimientos_economicos.base_imponible,0) > 0 "
            f"THEN ({expr_iva_importe} * 100.0 / "
            "movimientos_economicos.base_imponible) ELSE 0 END"
        )

    else:

        expr_iva_porcentaje = "0"

    if "pagado" in movimientos_cols:

        expr_pagado = "COALESCE(movimientos_economicos.pagado,0)"
        expr_pendiente = (
            "CASE WHEN COALESCE(movimientos_economicos.pagado,0)=1 "
            "THEN 0 ELSE 1 END"
        )

    elif "pendiente" in movimientos_cols:

        expr_pagado = (
            "CASE WHEN COALESCE(movimientos_economicos.pendiente,0)=1 "
            "THEN 0 ELSE 1 END"
        )
        expr_pendiente = "COALESCE(movimientos_economicos.pendiente,0)"

    else:

        expr_pagado = "0"
        expr_pendiente = "1"

    joins = []
    expr_campana = "''"

    if "campana_id" in movimientos_cols:

        joins.append(
            "LEFT JOIN campanas ON campanas.id = movimientos_economicos.campana_id"
        )
        expr_campana = "COALESCE(campanas.nombre,'')"

    if "cliente_id" in movimientos_cols:

        joins.append(
            "LEFT JOIN clientes ON clientes.id = movimientos_economicos.cliente_id"
        )
        expr_cliente = "COALESCE(clientes.nombre,'')"
        expr_cliente_nif = "COALESCE(clientes.nif,'')"

    else:

        expr_cliente = "''"
        expr_cliente_nif = "''"

    if "proveedor_id" in movimientos_cols:

        joins.append(
            """
            LEFT JOIN proveedores
            ON proveedores.id = movimientos_economicos.proveedor_id
            """
        )
        expr_proveedor = "COALESCE(proveedores.nombre,'')"
        expr_proveedor_nif = "COALESCE(proveedores.nif,'')"

    else:

        expr_proveedor = "''"
        expr_proveedor_nif = "''"

    if "cultivo_id" in movimientos_cols:

        joins.append(
            "LEFT JOIN cultivos ON cultivos.id = movimientos_economicos.cultivo_id"
        )
        joins.append(
            """
            LEFT JOIN campanas AS campanas_cultivo
            ON campanas_cultivo.id = cultivos.campana_id
            """
        )
        expr_nombre_cultivo = _expr_nombre_cultivo(cultivos_cols)
        expr_variedad = _expr_variedad_cultivo(cultivos_cols)
        expr_sistema = _expr_sistema_cultivo(cultivos_cols)
        expr_codigo_siex = _expr_codigo_siex_cultivo(cultivos_cols)
        expr_superficie = _expr_superficie_cultivo(cultivos_cols)
        expr_campana_cultivo = "COALESCE(campanas_cultivo.nombre,'')"

    else:

        expr_nombre_cultivo = "''"
        expr_variedad = "''"
        expr_sistema = "''"
        expr_codigo_siex = "''"
        expr_superficie = "NULL"
        expr_campana_cultivo = "''"

    if tiene_documentos:

        joins.append(
            """
            LEFT JOIN (
                SELECT movimiento_id,COUNT(*) AS facturas
                FROM movimientos_economicos_documentos
                WHERE tipo_documento='factura'
                GROUP BY movimiento_id
            ) documentos
            ON documentos.movimiento_id = movimientos_economicos.id
            """
        )
        expr_facturas = "COALESCE(documentos.facturas,0)"

    else:

        expr_facturas = "0"

    where = ""
    params = ()

    if movimiento_id is not None:

        where = "WHERE movimientos_economicos.id=?"
        params = (int(movimiento_id),)

    sql = f"""
        SELECT
        movimientos_economicos.id,
        {expr_campana_id} AS campana_id,
        {expr_cultivo_id} AS cultivo_id,
        {expr_cliente_id} AS cliente_id,
        {expr_proveedor_id} AS proveedor_id,
        {expr_campana} AS campana,
        {expr_fecha} AS fecha,
        {expr_tipo} AS tipo,
        {expr_categoria} AS categoria,
        {expr_concepto} AS concepto,
        {expr_tercero} AS tercero,
        {expr_nif_tercero} AS nif_tercero,
        {expr_numero_factura} AS numero_factura,
        {expr_base} AS base_imponible,
        {expr_iva_porcentaje} AS iva_porcentaje,
        {expr_iva_importe} AS iva_importe,
        {expr_iva_importe} AS iva,
        {expr_retencion} AS retencion,
        {expr_total} AS total,
        {expr_forma_pago} AS forma_pago,
        {expr_pagado} AS pagado,
        {expr_pendiente} AS pendiente,
        {expr_fecha_pago} AS fecha_pago,
        {expr_cultivo_legacy} AS cultivo,
        {expr_nombre_cultivo} AS cultivo_v6,
        {expr_variedad} AS variedad_v6,
        {expr_sistema} AS sistema_v6,
        {expr_codigo_siex} AS codigo_siex,
        {expr_superficie} AS superficie_cultivo,
        {expr_campana_cultivo} AS campana_cultivo,
        {expr_cliente} AS cliente,
        {expr_cliente_nif} AS cliente_nif,
        {expr_proveedor} AS proveedor,
        {expr_proveedor_nif} AS proveedor_nif,
        {expr_facturas} AS facturas_count,
        {expr_observaciones} AS observaciones
        FROM movimientos_economicos
        {" ".join(joins)}
        {where}
        ORDER BY {expr_fecha} DESC, movimientos_economicos.id DESC
    """

    movimientos = _leer_dataframe(sql, params, conn=conn)

    if movimientos.empty:

        return movimientos

    movimientos = movimientos.copy()
    movimientos["cultivo_estructurado"] = movimientos.apply(
        lambda fila: (
            _etiqueta_cultivo(fila)
            if _entero_o_none(fila.get("cultivo_id")) is not None
            else ""
        ),
        axis=1,
    )
    movimientos["cultivo"] = movimientos["cultivo_estructurado"].where(
        movimientos["cultivo_estructurado"] != "",
        movimientos["cultivo"].fillna("").astype(str),
    )
    movimientos["cultivo_origen"] = movimientos["cultivo_id"].apply(
        lambda valor: (
            "cultivo_id"
            if _entero_o_none(valor) is not None
            else "texto"
        )
    )
    return movimientos


def render(CAMPANA):

    st.title("🧾 Contabilidad agrícola")
    mensaje_contabilidad = st.session_state.pop(
        "mensaje_contabilidad",
        None,
    )

    if mensaje_contabilidad:

        st.info(mensaje_contabilidad)

    campana_contabilidad = leer(
        "SELECT nombre FROM campanas WHERE id=?",
        (CAMPANA,)
    )
    nombre_campana_contabilidad = (
        str(campana_contabilidad.iloc[0]["nombre"])
        if not campana_contabilidad.empty
        else str(CAMPANA)
    )

    st.info(f"Campaña activa: {nombre_campana_contabilidad}")

    seccion = st.radio(
        "Opciones de contabilidad",
        [
            "📊 Resumen",
            "📋 Listado",
            "➕ Nuevo movimiento",
            "💰 Pendientes",
            "✏️ Editar",
            "🗑️ Borrar"
        ],
        horizontal=True,
        key="contabilidad_seccion"
    )

    columnas_movimientos_contabilidad = _columnas_tabla(
        "movimientos_economicos"
    )
    admite_tercero_legacy = bool(
        {"tercero", "nif_tercero"} & columnas_movimientos_contabilidad
    )
    cultivos_contabilidad = _leer_cultivos_contabilidad()

    categorias_contabilidad = {
        "Ingreso": [
            "Venta de cosecha",
            "Subvenciones",
            "Indemnizaciones",
            "Servicios",
            "Otros ingresos"
        ],
        "Gasto": [
            "Fertilizantes",
            "Fitosanitarios",
            "Semillas y plantas",
            "Gasóleo",
            "Maquinaria",
            "Reparaciones",
            "Mano de obra",
            "Riegos y suministros",
            "Seguros",
            "Arrendamientos",
            "Otros gastos"
        ]
    }

    formas_pago_contabilidad = [
        "Transferencia",
        "Domiciliación",
        "Tarjeta",
        "Efectivo",
        "Cheque",
        "Compensación",
        "Otro"
    ]

    clientes_activos_contabilidad = _leer_terceros_contabilidad("clientes")
    proveedores_activos_contabilidad = _leer_terceros_contabilidad(
        "proveedores"
    )
    clientes_edicion_contabilidad = _leer_terceros_contabilidad(
        "clientes",
        solo_activos=False
    )
    proveedores_edicion_contabilidad = _leer_terceros_contabilidad(
        "proveedores",
        solo_activos=False
    )

    if seccion == "➕ Nuevo movimiento":
        st.subheader("Nuevo movimiento")

        if "form_movimiento_version" not in st.session_state:

            st.session_state["form_movimiento_version"] = 0

        form_movimiento_version = st.session_state["form_movimiento_version"]

        fecha_movimiento_texto = st.text_input(
            "Fecha",
            value=formatear_fecha_es(pd.Timestamp.today()),
            placeholder="DD/MM/AAAA",
            key=f"fecha_movimiento_contabilidad_{form_movimiento_version}"
        )
        tipo_movimiento = st.selectbox(
            "Tipo",
            ["Ingreso", "Gasto"],
            key=f"tipo_movimiento_contabilidad_{form_movimiento_version}"
        )
        categoria_movimiento = st.selectbox(
            "Categoría",
            categorias_contabilidad[tipo_movimiento],
            key=f"categoria_movimiento_contabilidad_{form_movimiento_version}"
        )
        concepto_movimiento = st.text_input(
            "Concepto",
            key=f"concepto_movimiento_contabilidad_{form_movimiento_version}"
        )
        factura_movimiento = st.text_input(
            "Nº factura",
            key=f"factura_movimiento_contabilidad_{form_movimiento_version}"
        )
        cliente_id_movimiento = None
        proveedor_id_movimiento = None
        tercero_movimiento = ""
        nif_tercero_movimiento = ""

        if tipo_movimiento == "Ingreso":

            if clientes_activos_contabilidad.empty:

                st.info(
                    "No hay clientes activos. Puedes guardar el ingreso "
                    "sin cliente."
                )
                cliente_id_movimiento = None

            else:

                cliente_id_movimiento = _selector_tercero(
                    clientes_activos_contabilidad,
                    "Cliente",
                    (
                        "cliente_movimiento_contabilidad_v610_"
                        f"{form_movimiento_version}"
                    ),
                    "Sin cliente",
                    seleccionar_primero=True,
                )

            cliente_seleccionado = _tercero_por_id(
                clientes_activos_contabilidad,
                cliente_id_movimiento,
            )

            if cliente_seleccionado is None:

                if admite_tercero_legacy:

                    tercero_movimiento = st.text_input(
                        "Tercero manual",
                        key=(
                            "tercero_manual_ingreso_contabilidad_"
                            f"{form_movimiento_version}"
                        )
                    )
                    nif_tercero_movimiento = st.text_input(
                        "NIF tercero manual",
                        key=(
                            "nif_tercero_manual_ingreso_contabilidad_"
                            f"{form_movimiento_version}"
                        )
                    )

                else:

                    st.info(
                        "Selecciona un cliente para guardar la relación "
                        "estructurada."
                    )

            else:

                tercero_movimiento = _texto(cliente_seleccionado.get("nombre"))
                nif_tercero_movimiento = _texto(
                    cliente_seleccionado.get("nif")
                )
                st.caption(
                    "Se guardará como tercero: "
                    + (
                        tercero_movimiento
                        if tercero_movimiento
                        else "Sin nombre"
                    )
                    + (
                        f" — NIF {nif_tercero_movimiento}"
                        if nif_tercero_movimiento
                        else ""
                    )
                    + "."
                )

        else:

            if proveedores_activos_contabilidad.empty:

                st.info(
                    "No hay proveedores activos. Puedes guardar el gasto "
                    "sin proveedor."
                )
                proveedor_id_movimiento = None

            else:

                proveedor_id_movimiento = _selector_tercero(
                    proveedores_activos_contabilidad,
                    "Proveedor",
                    (
                        "proveedor_movimiento_contabilidad_v610_"
                        f"{form_movimiento_version}"
                    ),
                    "Sin proveedor",
                    seleccionar_primero=True,
                )

            proveedor_seleccionado = _tercero_por_id(
                proveedores_activos_contabilidad,
                proveedor_id_movimiento,
            )

            if proveedor_seleccionado is None:

                if admite_tercero_legacy:

                    tercero_movimiento = st.text_input(
                        "Tercero manual",
                        key=(
                            "tercero_manual_gasto_contabilidad_"
                            f"{form_movimiento_version}"
                        )
                    )
                    nif_tercero_movimiento = st.text_input(
                        "NIF tercero manual",
                        key=(
                            "nif_tercero_manual_gasto_contabilidad_"
                            f"{form_movimiento_version}"
                        )
                    )

                else:

                    st.info(
                        "Selecciona un proveedor para guardar la relación "
                        "estructurada."
                    )

            else:

                tercero_movimiento = _texto(
                    proveedor_seleccionado.get("nombre")
                )
                nif_tercero_movimiento = _texto(
                    proveedor_seleccionado.get("nif")
                )
                st.caption(
                    "Se guardará como tercero: "
                    + (
                        tercero_movimiento
                        if tercero_movimiento
                        else "Sin nombre"
                    )
                    + (
                        f" — NIF {nif_tercero_movimiento}"
                        if nif_tercero_movimiento
                        else ""
                    )
                    + "."
                )

        st.markdown("**Detalle de IVA**")
        st.caption(
            "Tipos habituales: 0%, 4%, 5%, 7%, 10% y 21%. "
            "Usa Otro para introducir un tipo manual."
        )

        numero_lineas_iva = int(
            st.number_input(
                "¿Cuántas bases tiene la factura?",
                min_value=1,
                max_value=20,
                value=1,
                step=1,
                key=(
                    "numero_lineas_iva_movimiento_contabilidad_"
                    f"{form_movimiento_version}"
                )
            )
        )

        lineas_iva_movimiento = []

        for indice_linea in range(numero_lineas_iva):

            st.caption(f"Línea IVA {indice_linea + 1}")
            (
                columna_descripcion,
                columna_base,
                columna_tipo_iva,
                columna_cuota,
                columna_total_linea
            ) = st.columns([2.2, 1.2, 1.1, 1.1, 1.1])

            with columna_descripcion:

                descripcion_linea = st.text_input(
                    "Descripción",
                    key=(
                        "descripcion_linea_iva_movimiento_contabilidad_"
                        f"{form_movimiento_version}_{indice_linea}"
                    )
                )

            with columna_base:

                base_linea = st.number_input(
                    "Base imponible (€)",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f",
                    key=(
                        "base_linea_iva_movimiento_contabilidad_"
                        f"{form_movimiento_version}_{indice_linea}"
                    )
                )

            with columna_tipo_iva:

                tipo_iva_opcion = st.selectbox(
                    "Tipo IVA %",
                    TIPOS_IVA_HABITUALES + ["Otro"],
                    format_func=lambda valor: (
                        "Otro"
                        if valor == "Otro"
                        else _formatear_porcentaje(valor)
                    ),
                    key=(
                        "tipo_linea_iva_movimiento_contabilidad_"
                        f"{form_movimiento_version}_{indice_linea}"
                    )
                )

                if tipo_iva_opcion == "Otro":

                    tipo_iva_linea = st.number_input(
                        "IVA manual %",
                        min_value=0.0,
                        value=21.0,
                        step=0.01,
                        format="%.2f",
                        key=(
                            "tipo_manual_linea_iva_movimiento_contabilidad_"
                            f"{form_movimiento_version}_{indice_linea}"
                        )
                    )

                else:

                    tipo_iva_linea = float(tipo_iva_opcion)

            linea_calculada = _calcular_linea_iva(
                base_linea,
                tipo_iva_linea
            )

            with columna_cuota:

                st.metric(
                    "Cuota IVA",
                    f"{linea_calculada['cuota_iva']:.2f} €"
                )

            with columna_total_linea:

                st.metric(
                    "Total línea",
                    f"{linea_calculada['total_linea']:.2f} €"
                )

            lineas_iva_movimiento.append(
                {
                    "descripcion": descripcion_linea.strip(),
                    **linea_calculada
                }
            )

        retencion_movimiento = st.number_input(
            "Retención (€)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key=f"retencion_movimiento_contabilidad_{form_movimiento_version}"
        )

        lineas_iva_validas = [
            linea
            for linea in lineas_iva_movimiento
            if linea["base_imponible"] > 0
        ]
        base_movimiento = _redondear_importe(
            sum(linea["base_imponible"] for linea in lineas_iva_validas)
        )
        iva_importe_movimiento = _redondear_importe(
            sum(linea["cuota_iva"] for linea in lineas_iva_validas)
        )
        iva_porcentaje_movimiento = (
            _redondear_importe(
                iva_importe_movimiento * 100 / base_movimiento
            )
            if base_movimiento > 0
            else 0.0
        )
        total_factura_movimiento = _redondear_importe(
            base_movimiento + iva_importe_movimiento
        )
        total_movimiento = _redondear_importe(
            total_factura_movimiento - retencion_movimiento
        )

        columnas_totales = st.columns(4)
        columnas_totales[0].metric(
            "Base imponible total",
            f"{base_movimiento:.2f} €"
        )
        columnas_totales[1].metric(
            "IVA total",
            f"{iva_importe_movimiento:.2f} €"
        )
        columnas_totales[2].metric(
            "Total factura",
            f"{total_factura_movimiento:.2f} €"
        )
        columnas_totales[3].metric(
            "Total",
            f"{total_movimiento:.2f} €"
        )

        forma_pago_movimiento = st.selectbox(
            "Forma de pago",
            formas_pago_contabilidad,
            key=f"forma_pago_movimiento_contabilidad_{form_movimiento_version}"
        )
        pagado_movimiento = st.checkbox(
            "Pagado / cobrado",
            key=f"pagado_movimiento_contabilidad_{form_movimiento_version}"
        )

        fecha_pago_movimiento = None

        if pagado_movimiento:

            fecha_pago_movimiento_texto = st.text_input(
                "Fecha de pago / cobro",
                value=formatear_fecha_es(pd.Timestamp.today()),
                placeholder="DD/MM/AAAA",
                key=f"fecha_pago_movimiento_contabilidad_{form_movimiento_version}"
            )

        else:

            fecha_pago_movimiento_texto = ""

        error_formato_fecha_movimiento = False

        try:

            fecha_movimiento_iso = parsear_fecha_es(fecha_movimiento_texto)
            fecha_movimiento = pd.to_datetime(
                fecha_movimiento_iso,
                errors="coerce"
            ).date() if fecha_movimiento_iso else None
            fecha_pago_movimiento_iso = parsear_fecha_es(
                fecha_pago_movimiento_texto
            )
            fecha_pago_movimiento = pd.to_datetime(
                fecha_pago_movimiento_iso,
                errors="coerce"
            ).date() if fecha_pago_movimiento_iso else None

        except ValueError:

            error_formato_fecha_movimiento = True
            fecha_movimiento = None
            fecha_pago_movimiento = None

        resolucion_campana_movimiento = None
        campana_id_movimiento = CAMPANA

        if fecha_movimiento is not None:

            resolucion_campana_movimiento = (
                _resolver_campana_movimiento_por_fecha(
                    fecha_movimiento,
                    CAMPANA,
                )
            )
            campana_id_movimiento = (
                resolucion_campana_movimiento["campana_id"]
                or campana_id_movimiento
            )
            _mostrar_resolucion_campana_movimiento(
                resolucion_campana_movimiento
            )

        if cultivos_contabilidad.empty:

            st.info("No hay cultivos registrados para asociar al movimiento.")
            cultivo_id_movimiento = None
            cultivo_movimiento = ""

        else:

            cultivo_id_movimiento = _selector_cultivo_contabilidad(
                cultivos_contabilidad,
                f"cultivo_id_movimiento_contabilidad_{form_movimiento_version}",
                campana_id=campana_id_movimiento,
            )
            cultivo_movimiento = _cultivo_legacy_para_guardar(
                cultivo_id_movimiento,
                cultivos_contabilidad,
            )

        facturas_movimiento = st.file_uploader(
            "Facturas PDF",
            type=["pdf"],
            accept_multiple_files=True,
            key=f"facturas_movimiento_contabilidad_{form_movimiento_version}"
        )
        st.caption(
            "Opcional. Solo se admiten archivos PDF; no se guardan Word, "
            "Excel, imágenes ni otros formatos."
        )
        observaciones_movimiento = ""

        if st.button(
            "Registrar movimiento",
            key=f"registrar_movimiento_contabilidad_{form_movimiento_version}"
        ):

            if error_formato_fecha_movimiento:

                st.warning("La fecha debe tener formato DD/MM/AAAA")

            elif fecha_movimiento is None:

                st.warning("La fecha es obligatoria")

            elif not concepto_movimiento.strip():

                st.warning("Indica el concepto del movimiento")

            elif not lineas_iva_validas:

                st.warning("Añade al menos una línea con base imponible")

            elif any(
                pd.isna(linea["tipo_iva"])
                for linea in lineas_iva_validas
            ):

                st.warning("El tipo de IVA debe ser numérico")

            elif any(
                linea["base_imponible"] < 0
                or linea["tipo_iva"] < 0
                for linea in lineas_iva_validas
            ):

                st.warning("Revisa las bases imponibles y tipos de IVA")

            elif total_movimiento < 0:

                st.warning("El total no puede ser negativo")

            else:

                conn = conectar()

                try:

                    conn.execute("BEGIN")
                    resolucion_guardado = (
                        _resolver_campana_movimiento_por_fecha(
                            fecha_movimiento,
                            CAMPANA,
                            conn=conn,
                        )
                    )
                    campana_id_guardado = resolucion_guardado["campana_id"]

                    if campana_id_guardado is None:

                        raise sqlite3.IntegrityError(
                            "No hay campaña disponible para el movimiento"
                        )

                    movimiento_id = _insertar_movimiento_compatible(
                        conn,
                        {
                            "campana_id": campana_id_guardado,
                            "cultivo_id": _entero_o_none(
                                cultivo_id_movimiento
                            ),
                            "fecha": fecha_movimiento.isoformat(),
                            "tipo": tipo_movimiento,
                            "categoria": categoria_movimiento,
                            "concepto": concepto_movimiento.strip(),
                            "tercero": tercero_movimiento.strip(),
                            "nif_tercero": nif_tercero_movimiento.strip(),
                            "numero_factura": factura_movimiento.strip(),
                            "base_imponible": base_movimiento,
                            "iva_porcentaje": iva_porcentaje_movimiento,
                            "iva_importe": iva_importe_movimiento,
                            "retencion": retencion_movimiento,
                            "total": total_movimiento,
                            "forma_pago": forma_pago_movimiento,
                            "pagado": pagado_movimiento,
                            "pendiente": 0 if pagado_movimiento else 1,
                            "fecha_pago": (
                                fecha_pago_movimiento.isoformat()
                                if fecha_pago_movimiento is not None
                                else ""
                            ),
                            "cultivo": cultivo_movimiento or "",
                            "cliente_id": cliente_id_movimiento,
                            "proveedor_id": proveedor_id_movimiento,
                            "observaciones": observaciones_movimiento.strip(),
                        },
                    )
                    ahora = pd.Timestamp.now().isoformat()

                    for linea in lineas_iva_validas:

                        conn.execute(
                            """
                            INSERT INTO movimientos_economicos_lineas_iva
                            (movimiento_id,descripcion,base_imponible,
                            tipo_iva,cuota_iva,total_linea,created_at,
                            updated_at)
                            VALUES (?,?,?,?,?,?,?,?)
                            """,
                            (
                                movimiento_id,
                                linea["descripcion"],
                                linea["base_imponible"],
                                linea["tipo_iva"],
                                linea["cuota_iva"],
                                linea["total_linea"],
                                ahora,
                                ahora
                            )
                        )

                    resultado_facturas = guardar_facturas_pdf(
                        conn,
                        movimiento_id,
                        facturas_movimiento
                    )

                    conn.commit()

                except sqlite3.Error as error:

                    conn.rollback()
                    st.error(f"No se pudo registrar el movimiento: {error}")

                except (OSError, ValueError) as error:

                    conn.rollback()
                    st.error(f"No se pudieron guardar las facturas: {error}")

                else:

                    mensajes_exito = ["Movimiento registrado."]

                    if resolucion_guardado.get("aviso"):

                        mensajes_exito.append(resolucion_guardado["aviso"])

                    if resolucion_guardado.get("mensaje"):

                        mensajes_exito.append(resolucion_guardado["mensaje"])

                    st.session_state["mensaje_contabilidad"] = " ".join(
                        mensajes_exito
                    )

                    for error_factura in resultado_facturas["errores"]:

                        st.warning(error_factura)

                    if resultado_facturas["guardados"]:

                        st.success(
                            "Facturas guardadas: "
                            + ", ".join(resultado_facturas["guardados"])
                        )

                    st.session_state["form_movimiento_version"] += 1
                    st.rerun()

                finally:

                    conn.close()

    if seccion == "📊 Resumen":
        st.divider()
        st.subheader("Resumen de la campaña activa")

        resumen_contabilidad = _leer_resumen_contabilidad(CAMPANA)

        ingresos_contabilidad = float(resumen_contabilidad["ingresos"])
        gastos_contabilidad = float(resumen_contabilidad["gastos"])
        iva_soportado_contabilidad = float(
            resumen_contabilidad["iva_soportado"]
        )
        iva_repercutido_contabilidad = float(
            resumen_contabilidad["iva_repercutido"]
        )

        resumen_fila_uno = st.columns(3)
        resumen_fila_uno[0].metric(
            "Ingresos totales",
            f"{ingresos_contabilidad:.2f} €"
        )
        resumen_fila_uno[1].metric(
            "Gastos totales",
            f"{gastos_contabilidad:.2f} €"
        )
        resumen_fila_uno[2].metric(
            "Beneficio",
            f"{ingresos_contabilidad - gastos_contabilidad:.2f} €"
        )

        resumen_fila_dos = st.columns(5)
        resumen_fila_dos[0].metric(
            "IVA soportado",
            f"{iva_soportado_contabilidad:.2f} €"
        )
        resumen_fila_dos[1].metric(
            "IVA repercutido",
            f"{iva_repercutido_contabilidad:.2f} €"
        )
        resumen_fila_dos[2].metric(
            "Diferencia IVA",
            f"{iva_repercutido_contabilidad - iva_soportado_contabilidad:.2f} €"
        )
        resumen_fila_dos[3].metric(
            "Pendiente de pagar",
            f"{float(resumen_contabilidad['pendiente_pagar']):.2f} €"
        )
        resumen_fila_dos[4].metric(
            "Pendiente de cobrar",
            f"{float(resumen_contabilidad['pendiente_cobrar']):.2f} €"
        )


    movimientos_guardados = _leer_movimientos_contabilidad()
    documentos_guardados = leer_facturas_movimientos()

    lineas_iva_guardadas = leer(
        """
        SELECT id,movimiento_id,descripcion,base_imponible,tipo_iva,
        cuota_iva,total_linea,created_at,updated_at
        FROM movimientos_economicos_lineas_iva
        ORDER BY movimiento_id,id
        """
    )
    desglose_iva_por_movimiento = _resumen_desglose_iva(
        lineas_iva_guardadas
    )
    ids_movimientos_con_lineas_iva = set(desglose_iva_por_movimiento.keys())

    if "id" in movimientos_guardados.columns:

        movimientos_guardados["desglose_iva"] = (
            movimientos_guardados["id"]
            .astype(int)
            .map(desglose_iva_por_movimiento)
            .fillna("sin desglose")
        )

    if "facturas_count" in movimientos_guardados.columns:

        movimientos_guardados["facturas"] = (
            movimientos_guardados["facturas_count"].apply(_texto_facturas)
        )

    if not movimientos_guardados.empty:

        movimientos_guardados = pd.concat(
            [
                movimientos_guardados,
                movimientos_guardados.apply(
                    _resolver_tercero_movimiento,
                    axis=1,
                ),
            ],
            axis=1,
        )

    else:

        movimientos_guardados["tercero_resuelto"] = ""
        movimientos_guardados["nif_tercero_resuelto"] = ""
        movimientos_guardados["origen_tercero"] = ""

    if seccion == "📋 Listado":

        st.subheader("Listado de movimientos")
        movimientos_consulta = movimientos_guardados.copy()
        movimientos_consulta["estado_pago"] = (
            movimientos_consulta["pagado"]
            .fillna(0)
            .astype(bool)
            .map({True: "Pagado / cobrado", False: "Pendiente"})
        )
        movimientos_filtrados = mostrar_filtros_dataframe(
            movimientos_consulta,
            "contabilidad_listado",
            columnas_texto=[
                "concepto",
                "tercero_resuelto",
                "nif_tercero_resuelto",
                "numero_factura",
                "cultivo",
                "observaciones",
                "desglose_iva",
                "facturas"
            ],
            columna_fecha="fecha",
            filtros_select={
                "Campaña": "campana",
                "Tipo": "tipo",
                "Categoría": "categoria",
                "Cliente / proveedor": "tercero_resuelto",
                "Estado": "estado_pago",
                "Cultivo": "cultivo",
                "Facturas": "facturas"
            }
        )

        movimientos_listado = movimientos_filtrados.copy()
        movimientos_listado = movimientos_listado.drop(
            columns=[
                "campana_id",
                "cultivo_id",
                "cliente_id",
                "proveedor_id",
                "tercero",
                "nif_tercero",
                "cliente",
                "cliente_nif",
                "proveedor",
                "proveedor_nif",
                "origen_tercero",
                "cultivo_estructurado",
                "cultivo_origen",
                "iva",
                "pendiente",
                "facturas_count",
            ],
            errors="ignore"
        )

        if "fecha" in movimientos_listado.columns:

            movimientos_listado["fecha"] = pd.to_datetime(
                movimientos_listado["fecha"].map(fecha_es_a_datetime),
                errors="coerce"
            )

            movimientos_listado = movimientos_listado.sort_values(
                "fecha",
                ascending=False,
                na_position="last"
            )

        if "fecha_pago" in movimientos_listado.columns:

            movimientos_listado["fecha_pago"] = pd.to_datetime(
                movimientos_listado["fecha_pago"].map(fecha_es_a_datetime),
                errors="coerce"
            )

        column_config_listado = {}

        if "fecha" in movimientos_listado.columns:

            column_config_listado["fecha"] = st.column_config.DateColumn(
                "Fecha",
                format="DD/MM/YYYY"
            )

        if "fecha_pago" in movimientos_listado.columns:

            column_config_listado["fecha_pago"] = st.column_config.DateColumn(
                "Fecha pago",
                format="DD/MM/YYYY"
            )

        if "total" in movimientos_listado.columns:

            column_config_listado["total"] = st.column_config.NumberColumn(
                "Total",
                format="%.2f"
            )

        column_config_listado["tercero_resuelto"] = "Cliente / proveedor"
        column_config_listado["nif_tercero_resuelto"] = "NIF"

        columnas_movimientos_listado = [
            "id",
            "campana",
            "fecha",
            "tipo",
            "categoria",
            "concepto",
            "tercero_resuelto",
            "nif_tercero_resuelto",
            "numero_factura",
            "base_imponible",
            "iva_porcentaje",
            "iva_importe",
            "retencion",
            "total",
            "estado_pago",
            "forma_pago",
            "fecha_pago",
            "cultivo",
            "desglose_iva",
            "facturas",
            "observaciones",
        ]
        movimientos_listado_visual = preparar_dataframe_visual(
            movimientos_listado,
            columnas=columnas_movimientos_listado,
            ocultar_tecnicas=False,
            etiquetas_extra={
                "tercero_resuelto": "Cliente / proveedor",
                "nif_tercero_resuelto": "NIF",
                "iva_porcentaje": "% IVA",
                "iva_importe": "IVA",
                "retencion": "Retención",
                "estado_pago": "Estado pago",
                "forma_pago": "Forma pago",
                "fecha_pago": "Fecha pago",
                "desglose_iva": "Desglose IVA",
                "facturas": "Facturas",
            },
        )
        st.dataframe(
            movimientos_listado_visual,
            hide_index=True,
            use_container_width=True,
            key="contabilidad_listado_movimientos_dataframe_fecha_datetime_v3"
        )

    if seccion == "💰 Pendientes":

        st.subheader("Pagos y cobros pendientes")

        if movimientos_guardados.empty:

            st.info("No hay movimientos económicos registrados")

        else:

            movimientos_pendientes = movimientos_guardados.copy()
            movimientos_pendientes["pagado"] = (
                movimientos_pendientes["pagado"].fillna(0).astype(bool)
            )
            movimientos_pendientes["total"] = pd.to_numeric(
                movimientos_pendientes["total"],
                errors="coerce"
            ).fillna(0)
            movimientos_pendientes = movimientos_pendientes[
                ~movimientos_pendientes["pagado"]
            ].copy()

            if movimientos_pendientes.empty:

                st.success("No hay pagos ni cobros pendientes")

            else:

                pendientes_pagar = movimientos_pendientes[
                    movimientos_pendientes["tipo"] == "Gasto"
                ].copy()
                pendientes_cobrar = movimientos_pendientes[
                    movimientos_pendientes["tipo"] == "Ingreso"
                ].copy()

                resumen_pendientes = st.columns(2)
                resumen_pendientes[0].metric(
                    "Pendiente de pagar",
                    f"{pendientes_pagar['total'].sum():.2f} €"
                )
                resumen_pendientes[1].metric(
                    "Pendiente de cobrar",
                    f"{pendientes_cobrar['total'].sum():.2f} €"
                )

                columnas_pendientes = [
                    "fecha",
                    "tipo",
                    "concepto",
                    "tercero_resuelto",
                    "nif_tercero_resuelto",
                    "facturas",
                    "numero_factura",
                    "total",
                    "campana",
                    "observaciones"
                ]

                st.markdown("**Pendiente de pagar**")

                if pendientes_pagar.empty:

                    st.info("No hay pagos pendientes")

                else:

                    pendientes_pagar_visual = preparar_dataframe_visual(
                        preparar_columnas_fecha_tabla(
                            pendientes_pagar[columnas_pendientes],
                            ["fecha"]
                        ),
                        ocultar_tecnicas=True
                    )
                    st.dataframe(
                        pendientes_pagar_visual,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Fecha": st.column_config.DateColumn(
                                "Fecha",
                                format="DD/MM/YYYY"
                            ),
                        }
                    )

                st.markdown("**Pendiente de cobrar**")

                if pendientes_cobrar.empty:

                    st.info("No hay cobros pendientes")

                else:

                    pendientes_cobrar_visual = preparar_dataframe_visual(
                        preparar_columnas_fecha_tabla(
                            pendientes_cobrar[columnas_pendientes],
                            ["fecha"]
                        ),
                        ocultar_tecnicas=True
                    )
                    st.dataframe(
                        pendientes_cobrar_visual,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Fecha": st.column_config.DateColumn(
                                "Fecha",
                                format="DD/MM/YYYY"
                            ),
                        }
                    )

    if seccion == "✏️ Editar":

        st.subheader("Editar movimientos")
        if movimientos_guardados.empty:

            st.info("No hay movimientos económicos registrados")

        else:

            movimientos_originales_por_id = (
                movimientos_guardados
                .copy()
                .set_index("id", drop=False)
            )

            with st.expander("Asignar cliente/proveedor"):

                ids_asignar_tercero = [
                    int(valor)
                    for valor in movimientos_originales_por_id.index.tolist()
                ]
                movimiento_asignar_id = st.selectbox(
                    "Movimiento",
                    ids_asignar_tercero,
                    format_func=lambda valor: (
                        f"#{valor} · "
                        f"{_texto(movimientos_originales_por_id.loc[valor]['tipo'])} · "
                        f"{_texto(movimientos_originales_por_id.loc[valor]['tercero_resuelto']) or 'Sin tercero'}"
                    ),
                    key="contabilidad_asignar_tercero_movimiento_id"
                )
                movimiento_asignar = movimientos_originales_por_id.loc[
                    movimiento_asignar_id
                ]
                tipo_asignar = _texto(movimiento_asignar["tipo"])
                tercero_legacy_actual = _texto(
                    movimiento_asignar["tercero"]
                )
                nif_legacy_actual = _texto(
                    movimiento_asignar["nif_tercero"]
                )
                tercero_texto_asignado = tercero_legacy_actual
                nif_texto_asignado = nif_legacy_actual
                cliente_id_asignado = None
                proveedor_id_asignado = None

                if tercero_legacy_actual or nif_legacy_actual:

                    st.caption(
                        "Tercero legacy actual: "
                        + (
                            tercero_legacy_actual
                            if tercero_legacy_actual
                            else "Sin nombre"
                        )
                        + (
                            f" — NIF {nif_legacy_actual}"
                            if nif_legacy_actual
                            else ""
                        )
                        + "."
                    )

                if tipo_asignar == "Ingreso":

                    if clientes_edicion_contabilidad.empty:

                        if admite_tercero_legacy:

                            st.info(
                                "No hay clientes registrados. Puedes mantener "
                                "tercero/NIF manual como compatibilidad."
                            )

                        else:

                            st.info("No hay clientes registrados.")

                    else:

                        cliente_id_asignado = _selector_tercero(
                            clientes_edicion_contabilidad,
                            "Cliente",
                            (
                                "contabilidad_nuevo_cliente_id_"
                                f"{movimiento_asignar_id}"
                            ),
                            "Sin cliente",
                            valor_actual=movimiento_asignar["cliente_id"],
                            seleccionar_primero=True,
                        )

                    cliente_asignado = _tercero_por_id(
                        clientes_edicion_contabilidad,
                        cliente_id_asignado,
                    )

                    if cliente_asignado is None:

                        if tercero_legacy_actual or nif_legacy_actual:

                            st.info(
                                "El movimiento conserva tercero/NIF legacy. "
                                "Selecciona un cliente para estructurarlo o "
                                "guarda sin cliente para mantener el texto actual."
                            )

                        else:

                            if admite_tercero_legacy:

                                tercero_texto_asignado = st.text_input(
                                    "Tercero manual",
                                    value=tercero_legacy_actual,
                                    key=(
                                        "contabilidad_tercero_manual_"
                                        f"{movimiento_asignar_id}_cliente"
                                    ),
                                )
                                nif_texto_asignado = st.text_input(
                                    "NIF tercero manual",
                                    value=nif_legacy_actual,
                                    key=(
                                        "contabilidad_nif_manual_"
                                        f"{movimiento_asignar_id}_cliente"
                                    ),
                                )

                            else:

                                st.info(
                                    "Selecciona un cliente para estructurar "
                                    "este ingreso."
                                )

                    else:

                        tercero_texto_asignado = _texto(
                            cliente_asignado.get("nombre")
                        )
                        nif_texto_asignado = _texto(cliente_asignado.get("nif"))
                        st.caption(
                            "Se guardará como tercero: "
                            + (
                                tercero_texto_asignado
                                if tercero_texto_asignado
                                else "Sin nombre"
                            )
                            + (
                                f" — NIF {nif_texto_asignado}"
                                if nif_texto_asignado
                                else ""
                            )
                            + "."
                        )

                elif tipo_asignar == "Gasto":

                    if proveedores_edicion_contabilidad.empty:

                        if admite_tercero_legacy:

                            st.info(
                                "No hay proveedores registrados. Puedes "
                                "mantener tercero/NIF manual como "
                                "compatibilidad."
                            )

                        else:

                            st.info("No hay proveedores registrados.")

                    else:

                        proveedor_id_asignado = _selector_tercero(
                            proveedores_edicion_contabilidad,
                            "Proveedor",
                            (
                                "contabilidad_nuevo_proveedor_id_"
                                f"{movimiento_asignar_id}"
                            ),
                            "Sin proveedor",
                            valor_actual=movimiento_asignar["proveedor_id"],
                            seleccionar_primero=True,
                        )

                    proveedor_asignado = _tercero_por_id(
                        proveedores_edicion_contabilidad,
                        proveedor_id_asignado,
                    )

                    if proveedor_asignado is None:

                        if tercero_legacy_actual or nif_legacy_actual:

                            st.info(
                                "El movimiento conserva tercero/NIF legacy. "
                                "Selecciona un proveedor para estructurarlo o "
                                "guarda sin proveedor para mantener el texto actual."
                            )

                        else:

                            if admite_tercero_legacy:

                                tercero_texto_asignado = st.text_input(
                                    "Tercero manual",
                                    value=tercero_legacy_actual,
                                    key=(
                                        "contabilidad_tercero_manual_"
                                        f"{movimiento_asignar_id}_proveedor"
                                    ),
                                )
                                nif_texto_asignado = st.text_input(
                                    "NIF tercero manual",
                                    value=nif_legacy_actual,
                                    key=(
                                        "contabilidad_nif_manual_"
                                        f"{movimiento_asignar_id}_proveedor"
                                    ),
                                )

                            else:

                                st.info(
                                    "Selecciona un proveedor para estructurar "
                                    "este gasto."
                                )

                    else:

                        tercero_texto_asignado = _texto(
                            proveedor_asignado.get("nombre")
                        )
                        nif_texto_asignado = _texto(
                            proveedor_asignado.get("nif")
                        )
                        st.caption(
                            "Se guardará como tercero: "
                            + (
                                tercero_texto_asignado
                                if tercero_texto_asignado
                                else "Sin nombre"
                            )
                            + (
                                f" — NIF {nif_texto_asignado}"
                                if nif_texto_asignado
                                else ""
                            )
                            + "."
                        )

                confirmar_asignacion_tercero = st.checkbox(
                    "Confirmo que quiero actualizar el cliente/proveedor de este movimiento",
                    key=(
                        "contabilidad_confirmar_tercero_"
                        f"{movimiento_asignar_id}"
                    )
                )

                if st.button(
                    "Guardar cliente/proveedor",
                    key=(
                        "contabilidad_guardar_tercero_"
                        f"{movimiento_asignar_id}"
                    ),
                    type="primary",
                ):

                    if not confirmar_asignacion_tercero:

                        st.warning("Marca la confirmación antes de guardar")

                    else:

                        conn = conectar()

                        try:

                            _actualizar_movimiento_compatible(
                                conn,
                                movimiento_asignar_id,
                                {
                                    "tipo": tipo_asignar,
                                    "tercero": _texto(tercero_texto_asignado),
                                    "nif_tercero": _texto(nif_texto_asignado),
                                    "cliente_id": (
                                        _entero_o_none(cliente_id_asignado)
                                        if tipo_asignar == "Ingreso"
                                        else None
                                    ),
                                    "proveedor_id": (
                                        _entero_o_none(proveedor_id_asignado)
                                        if tipo_asignar == "Gasto"
                                        else None
                                    ),
                                },
                            )
                            conn.commit()

                        except sqlite3.Error:

                            conn.rollback()
                            raise

                        finally:

                            conn.close()

                        st.success("Cliente/proveedor actualizado")
                        st.rerun()

            with st.expander("Asignar cultivo"):

                if cultivos_contabilidad.empty:

                    st.info("No hay cultivos registrados.")

                else:

                    ids_asignar_cultivo = [
                        int(valor)
                        for valor in movimientos_originales_por_id.index.tolist()
                    ]
                    movimiento_asignar_cultivo_id = st.selectbox(
                        "Movimiento",
                        ids_asignar_cultivo,
                        format_func=lambda valor: (
                            f"#{valor} · "
                            f"{_texto(movimientos_originales_por_id.loc[valor]['tipo'])} · "
                            f"{_texto(movimientos_originales_por_id.loc[valor]['concepto']) or 'Sin concepto'}"
                        ),
                        key="contabilidad_asignar_cultivo_movimiento_id",
                    )
                    movimiento_asignar_cultivo = movimientos_originales_por_id.loc[
                        movimiento_asignar_cultivo_id
                    ]
                    cultivo_actual_texto = _texto(
                        movimiento_asignar_cultivo["cultivo"]
                    )

                    if cultivo_actual_texto:

                        st.caption(f"Cultivo actual: {cultivo_actual_texto}.")

                    cultivo_id_asignado = _selector_cultivo_contabilidad(
                        cultivos_contabilidad,
                        (
                            "contabilidad_nuevo_cultivo_id_"
                            f"{movimiento_asignar_cultivo_id}"
                        ),
                        campana_id=movimiento_asignar_cultivo["campana_id"],
                        valor_actual=movimiento_asignar_cultivo["cultivo_id"],
                    )
                    cultivo_texto_asignado = _cultivo_legacy_para_guardar(
                        cultivo_id_asignado,
                        cultivos_contabilidad,
                    )
                    confirmar_asignacion_cultivo = st.checkbox(
                        "Confirmo que quiero actualizar el cultivo de este movimiento",
                        key=(
                            "contabilidad_confirmar_cultivo_"
                            f"{movimiento_asignar_cultivo_id}"
                        ),
                    )

                    if st.button(
                        "Guardar cultivo",
                        key=(
                            "contabilidad_guardar_cultivo_"
                            f"{movimiento_asignar_cultivo_id}"
                        ),
                    ):

                        if not confirmar_asignacion_cultivo:

                            st.warning("Marca la confirmación antes de guardar")

                        else:

                            conn = conectar()

                            try:

                                _actualizar_movimiento_compatible(
                                    conn,
                                    movimiento_asignar_cultivo_id,
                                    {
                                        "cultivo_id": _entero_o_none(
                                            cultivo_id_asignado
                                        ),
                                        "cultivo": cultivo_texto_asignado,
                                    },
                                )
                                conn.commit()

                            except sqlite3.Error:

                                conn.rollback()
                                raise

                            finally:

                                conn.close()

                            st.success("Cultivo actualizado")
                            st.rerun()

            editor_movimientos = movimientos_guardados.copy()
            editor_movimientos = editor_movimientos.drop(
                columns=[
                    "campana_id",
                    "cultivo_id",
                    "cliente_id",
                    "proveedor_id",
                    "tercero",
                    "nif_tercero",
                    "cliente",
                    "cliente_nif",
                    "proveedor",
                    "proveedor_nif",
                    "origen_tercero",
                    "cultivo_estructurado",
                    "cultivo_origen",
                    "iva",
                    "pendiente",
                    "facturas_count",
                ],
                errors="ignore"
            )

            movimientos_con_desglose = editor_movimientos[
                editor_movimientos["id"].astype(int).isin(
                    ids_movimientos_con_lineas_iva
                )
            ].copy()

            if not movimientos_con_desglose.empty:

                st.warning(
                    "Este movimiento tiene desglose de IVA. Para modificar "
                    "bases e IVA, usa la sección de detalle de IVA."
                )
                st.markdown("**Detalle de IVA del movimiento seleccionado**")
                ids_detalle_iva = (
                    movimientos_con_desglose["id"]
                    .astype(int)
                    .tolist()
                )

                def formatear_movimiento_detalle_iva(valor):

                    fila = movimientos_con_desglose[
                        movimientos_con_desglose["id"].astype(int)
                        == int(valor)
                    ].iloc[0]

                    return f"{valor} - {fila['concepto']}"

                movimiento_detalle_iva = st.selectbox(
                    "Movimiento",
                    ids_detalle_iva,
                    format_func=formatear_movimiento_detalle_iva,
                    key="contabilidad_detalle_iva_movimiento"
                )
                detalle_iva_movimiento = lineas_iva_guardadas[
                    lineas_iva_guardadas["movimiento_id"].astype(int)
                    == int(movimiento_detalle_iva)
                ].copy()

                st.dataframe(
                    preparar_dataframe_visual(
                        detalle_iva_movimiento[
                            [
                                "descripcion",
                                "base_imponible",
                                "tipo_iva",
                                "cuota_iva",
                                "total_linea"
                            ]
                        ],
                        ocultar_tecnicas=True
                    ),
                    hide_index=True,
                    use_container_width=True
                )

            st.markdown("### Facturas adjuntas")
            ids_movimientos_facturas = (
                editor_movimientos["id"].astype(int).tolist()
            )
            movimiento_facturas_id = st.selectbox(
                "Movimiento para gestionar facturas",
                ids_movimientos_facturas,
                format_func=lambda valor: _formatear_movimiento_facturas(
                    valor,
                    editor_movimientos
                ),
                key="contabilidad_facturas_movimiento_id"
            )
            facturas_movimiento_editor = documentos_guardados[
                documentos_guardados["movimiento_id"].astype(int)
                == int(movimiento_facturas_id)
            ].copy()

            if facturas_movimiento_editor.empty:

                st.info("Este movimiento no tiene facturas adjuntas")

            else:

                listado_facturas = facturas_movimiento_editor[
                    [
                        "id",
                        "nombre_original",
                        "size_bytes",
                        "created_at",
                    ]
                ].copy()
                listado_facturas["size_bytes"] = (
                    listado_facturas["size_bytes"].apply(_formatear_bytes)
                )
                st.dataframe(
                    preparar_dataframe_visual(
                        listado_facturas,
                        mostrar_id=True
                    ),
                    hide_index=True,
                    use_container_width=True
                )

                for _, factura in facturas_movimiento_editor.iterrows():

                    try:

                        ruta_factura = ruta_factura_absoluta(
                            factura["ruta_relativa"]
                        )
                        datos_factura = ruta_factura.read_bytes()

                    except (OSError, ValueError):

                        st.warning(
                            "No se pudo abrir la factura "
                            f"{factura['nombre_original']}"
                        )
                        continue

                    st.download_button(
                        f"Descargar {factura['nombre_original']}",
                        datos_factura,
                        file_name=factura["nombre_original"],
                        mime="application/pdf",
                        key=f"descargar_factura_{int(factura['id'])}"
                    )

            nuevas_facturas_editor = st.file_uploader(
                "Añadir facturas PDF a este movimiento",
                type=["pdf"],
                accept_multiple_files=True,
                key=f"contabilidad_nuevas_facturas_{movimiento_facturas_id}"
            )

            if st.button(
                "Añadir facturas PDF",
                key=f"contabilidad_guardar_facturas_{movimiento_facturas_id}"
            ):

                if not nuevas_facturas_editor:

                    st.warning("Selecciona al menos una factura PDF")

                else:

                    conn = conectar()

                    try:

                        conn.execute("BEGIN")
                        resultado_facturas_editor = guardar_facturas_pdf(
                            conn,
                            movimiento_facturas_id,
                            nuevas_facturas_editor
                        )
                        conn.commit()

                    except (sqlite3.Error, OSError, ValueError) as error:

                        conn.rollback()
                        st.error(f"No se pudieron guardar las facturas: {error}")

                    else:

                        for error_factura in resultado_facturas_editor["errores"]:

                            st.warning(error_factura)

                        if resultado_facturas_editor["guardados"]:

                            st.success("Facturas guardadas")
                            st.rerun()

                        else:

                            st.warning("No se guardó ninguna factura")

                    finally:

                        conn.close()

            if not facturas_movimiento_editor.empty:

                facturas_por_id = facturas_movimiento_editor.set_index(
                    "id",
                    drop=False
                )
                factura_eliminar_id = st.selectbox(
                    "Factura a eliminar",
                    facturas_por_id.index.astype(int).tolist(),
                    format_func=lambda valor: (
                        facturas_por_id.loc[valor]["nombre_original"]
                    ),
                    key=f"contabilidad_eliminar_factura_id_{movimiento_facturas_id}"
                )
                confirmar_eliminar_factura = st.checkbox(
                    "Confirmo que quiero eliminar esta factura adjunta",
                    key=f"contabilidad_confirmar_eliminar_factura_{movimiento_facturas_id}"
                )

                if st.button(
                    "Eliminar factura adjunta",
                    key=f"contabilidad_eliminar_factura_{movimiento_facturas_id}"
                ):

                    if not confirmar_eliminar_factura:

                        st.warning("Marca la confirmación antes de eliminar")

                    else:

                        conn = conectar()
                        ruta_eliminar = None

                        try:

                            conn.execute("BEGIN")
                            ruta_eliminar = eliminar_documento_factura(
                                conn,
                                factura_eliminar_id
                            )
                            conn.commit()

                        except sqlite3.Error as error:

                            conn.rollback()
                            st.error(
                                "No se pudo eliminar la factura adjunta: "
                                f"{error}"
                            )

                        else:

                            try:

                                eliminar_archivo_factura(ruta_eliminar)

                            except (OSError, ValueError) as error:

                                st.warning(
                                    "La factura se desvinculó, pero no se "
                                    f"pudo borrar el archivo físico: {error}"
                                )

                            st.success("Factura adjunta eliminada")
                            st.rerun()

                        finally:

                            conn.close()

            editor_movimientos["pagado"] = (
                editor_movimientos["pagado"].fillna(0).astype(bool)
            )
            for columna in ["fecha", "fecha_pago"]:

                editor_movimientos[columna] = pd.to_datetime(
                    editor_movimientos[columna],
                    errors="coerce"
                )

            column_config_movimientos = preparar_column_config_visual(
                editor_movimientos
            )
            column_config_movimientos.update({
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "tipo": st.column_config.SelectboxColumn(
                    "Tipo",
                    options=["Ingreso", "Gasto"],
                    required=True
                ),
                "pagado": st.column_config.CheckboxColumn("Pagado"),
                "fecha": st.column_config.DateColumn(
                    "Fecha",
                    format="DD/MM/YYYY",
                    required=True
                ),
                "fecha_pago": st.column_config.DateColumn(
                    "Fecha de pago",
                    format="DD/MM/YYYY"
                ),
                "tercero_resuelto": st.column_config.TextColumn(
                    "Cliente / proveedor",
                    disabled=True
                ),
                "nif_tercero_resuelto": st.column_config.TextColumn(
                    "NIF",
                    disabled=True
                ),
                "iva_importe": st.column_config.NumberColumn(
                    "IVA importe",
                    disabled=True,
                    format="%.2f"
                ),
                "total": st.column_config.NumberColumn(
                    "Total",
                    disabled=True,
                    format="%.2f"
                ),
            })
            movimientos_editados = st.data_editor(
                editor_movimientos,
                num_rows="fixed",
                disabled=[
                    "id",
                    "campana",
                    "tercero_resuelto",
                    "nif_tercero_resuelto",
                    "iva_importe",
                    "total",
                    "cultivo",
                    "desglose_iva",
                    "facturas"
                ],
                hide_index=True,
                use_container_width=True,
                column_order=[
                    "id",
                    "campana",
                    "fecha",
                    "tipo",
                    "categoria",
                    "concepto",
                    "tercero_resuelto",
                    "nif_tercero_resuelto",
                    "numero_factura",
                    "base_imponible",
                    "iva_porcentaje",
                    "iva_importe",
                    "retencion",
                    "total",
                    "forma_pago",
                    "pagado",
                    "fecha_pago",
                    "cultivo",
                    "desglose_iva",
                    "facturas",
                    "observaciones",
                ],
                column_config=column_config_movimientos,
                key="contabilidad_editor_movimientos_economicos"
            )

            confirmar_movimientos = st.checkbox(
                "Confirmo que quiero guardar los cambios contables",
                key="contabilidad_confirmar_movimientos_economicos"
            )

            if st.button(
                "💾 Guardar cambios contables",
                key="contabilidad_guardar_cambios_movimientos_economicos"
            ):

                ids_originales = editor_movimientos["id"].astype(int).tolist()
                ids_editados = movimientos_editados["id"].astype(int).tolist()

                if not confirmar_movimientos:

                    st.warning("Marca la confirmación antes de guardar")

                elif ids_editados != ids_originales:

                    st.warning("No se permite añadir, borrar ni cambiar registros")

                else:

                    movimientos_para_guardar = movimientos_editados.copy()
                    ids_con_desglose_editados = (
                        set(ids_editados) & ids_movimientos_con_lineas_iva
                    )
                    cambios_importes_con_desglose = False

                    for movimiento_id in ids_con_desglose_editados:

                        fila_original = editor_movimientos[
                            editor_movimientos["id"].astype(int)
                            == int(movimiento_id)
                        ].iloc[0]
                        fila_editada = movimientos_para_guardar[
                            movimientos_para_guardar["id"].astype(int)
                            == int(movimiento_id)
                        ].iloc[0]

                        for columna_bloqueada in [
                            "base_imponible",
                            "iva_porcentaje",
                            "retencion"
                        ]:

                            if _numeros_distintos(
                                fila_original[columna_bloqueada],
                                fila_editada[columna_bloqueada]
                            ):

                                cambios_importes_con_desglose = True

                    if cambios_importes_con_desglose:

                        st.warning(
                            "Este movimiento tiene desglose de IVA. Para "
                            "modificar bases e IVA, usa la sección de "
                            "detalle de IVA."
                        )

                        return

                    for movimiento_id in ids_con_desglose_editados:

                        fila_original = editor_movimientos[
                            editor_movimientos["id"].astype(int)
                            == int(movimiento_id)
                        ].iloc[0]
                        mascara_movimiento = (
                            movimientos_para_guardar["id"].astype(int)
                            == int(movimiento_id)
                        )

                        for columna_total in [
                            "base_imponible",
                            "iva_porcentaje",
                            "iva_importe",
                            "retencion",
                            "total"
                        ]:

                            movimientos_para_guardar.loc[
                                mascara_movimiento,
                                columna_total
                            ] = fila_original[columna_total]

                    columnas_texto_movimientos = [
                        "tipo",
                        "categoria",
                        "concepto",
                        "numero_factura",
                        "forma_pago",
                        "cultivo",
                        "observaciones"
                    ]

                    for columna in columnas_texto_movimientos:

                        movimientos_para_guardar[columna] = (
                            movimientos_para_guardar[columna]
                            .fillna("")
                            .astype(str)
                            .str.strip()
                        )

                    for columna in [
                        "base_imponible",
                        "iva_porcentaje",
                        "retencion"
                    ]:

                        movimientos_para_guardar[columna] = pd.to_numeric(
                            movimientos_para_guardar[columna],
                            errors="coerce"
                        )

                    for columna in ["fecha", "fecha_pago"]:

                        movimientos_para_guardar[columna] = pd.to_datetime(
                            movimientos_para_guardar[columna],
                            errors="coerce"
                        )

                    campos_invalidos = (
                        movimientos_para_guardar["fecha"].isna()
                        | (movimientos_para_guardar["concepto"] == "")
                        | movimientos_para_guardar["base_imponible"].isna()
                        | movimientos_para_guardar["iva_porcentaje"].isna()
                        | movimientos_para_guardar["retencion"].isna()
                        | (movimientos_para_guardar["base_imponible"] < 0)
                        | (movimientos_para_guardar["iva_porcentaje"] < 0)
                        | (movimientos_para_guardar["retencion"] < 0)
                    )

                    if campos_invalidos.any():

                        st.warning(
                            "Revisa fecha, concepto, base, IVA y retención"
                        )

                    else:

                        movimientos_para_guardar["iva_importe"] = (
                            movimientos_para_guardar["base_imponible"]
                            * movimientos_para_guardar["iva_porcentaje"]
                            / 100
                        )
                        movimientos_para_guardar["total"] = (
                            movimientos_para_guardar["base_imponible"]
                            + movimientos_para_guardar["iva_importe"]
                            - movimientos_para_guardar["retencion"]
                        )

                        for movimiento_id in ids_con_desglose_editados:

                            fila_original = editor_movimientos[
                                editor_movimientos["id"].astype(int)
                                == int(movimiento_id)
                            ].iloc[0]
                            mascara_movimiento = (
                                movimientos_para_guardar["id"].astype(int)
                                == int(movimiento_id)
                            )

                            for columna_total in [
                                "base_imponible",
                                "iva_porcentaje",
                                "iva_importe",
                                "retencion",
                                "total"
                            ]:

                                movimientos_para_guardar.loc[
                                    mascara_movimiento,
                                    columna_total
                                ] = fila_original[columna_total]

                        if (movimientos_para_guardar["total"] < 0).any():

                            st.warning("El total no puede ser negativo")

                        else:

                            avisos_campana_edicion = []
                            conn = conectar()

                            try:

                                for _, fila in movimientos_para_guardar.iterrows():

                                    pagado_fila = bool(fila["pagado"])
                                    fila_original = (
                                        movimientos_originales_por_id.loc[
                                            int(fila["id"])
                                        ]
                                    )
                                    fecha_original = pd.to_datetime(
                                        fila_original["fecha"],
                                        errors="coerce",
                                    )
                                    fecha_editada = fila["fecha"].date()
                                    fecha_cambiada = (
                                        pd.isna(fecha_original)
                                        or fecha_original.date()
                                        != fecha_editada
                                    )
                                    campana_id_fila = _entero_o_none(
                                        fila_original.get("campana_id")
                                    )

                                    if fecha_cambiada:

                                        resolucion_campana_fila = (
                                            _resolver_campana_movimiento_por_fecha(
                                                fecha_editada,
                                                CAMPANA,
                                                conn=conn,
                                            )
                                        )

                                        if (
                                            resolucion_campana_fila[
                                                "campana_id"
                                            ]
                                            is None
                                        ):

                                            raise sqlite3.IntegrityError(
                                                "No hay campaña disponible "
                                                "para el movimiento"
                                            )

                                        campana_id_detectada = int(
                                            resolucion_campana_fila[
                                                "campana_id"
                                            ]
                                        )
                                        campana = (
                                            resolucion_campana_fila[
                                                "campana"
                                            ]
                                            or {}
                                        )

                                        if campana_id_detectada != campana_id_fila:

                                            avisos_campana_edicion.append(
                                                "Movimiento "
                                                f"#{int(fila['id'])} "
                                                "asignado a la campaña "
                                                f"{campana.get('nombre', '')} "
                                                "según la fecha "
                                                f"{formatear_fecha_es(fecha_editada)}."
                                            )

                                        for texto_aviso in [
                                            resolucion_campana_fila.get(
                                                "aviso"
                                            ),
                                            resolucion_campana_fila.get(
                                                "mensaje"
                                            ),
                                        ]:

                                            if texto_aviso:

                                                avisos_campana_edicion.append(
                                                    "Movimiento "
                                                    f"#{int(fila['id'])}: "
                                                    f"{texto_aviso}"
                                                )

                                        campana_id_fila = campana_id_detectada

                                    cliente_id_fila = (
                                        _entero_o_none(
                                            fila_original["cliente_id"]
                                        )
                                        if fila["tipo"] == "Ingreso"
                                        else None
                                    )
                                    proveedor_id_fila = (
                                        _entero_o_none(
                                            fila_original["proveedor_id"]
                                        )
                                        if fila["tipo"] == "Gasto"
                                        else None
                                    )
                                    tercero_fila, nif_tercero_fila = (
                                        _tercero_legacy_para_guardar(
                                            fila["tipo"],
                                            cliente_id_fila,
                                            proveedor_id_fila,
                                            clientes_edicion_contabilidad,
                                            proveedores_edicion_contabilidad,
                                            fila_original["tercero"],
                                            fila_original["nif_tercero"],
                                        )
                                    )

                                    _actualizar_movimiento_compatible(
                                        conn,
                                        fila["id"],
                                        {
                                            "campana_id": campana_id_fila,
                                            "fecha": (
                                                fecha_editada.isoformat()
                                            ),
                                            "tipo": fila["tipo"],
                                            "categoria": fila["categoria"],
                                            "concepto": fila["concepto"],
                                            "tercero": tercero_fila,
                                            "nif_tercero": nif_tercero_fila,
                                            "numero_factura": (
                                                fila["numero_factura"]
                                            ),
                                            "base_imponible": float(
                                                fila["base_imponible"]
                                            ),
                                            "iva_porcentaje": float(
                                                fila["iva_porcentaje"]
                                            ),
                                            "iva_importe": float(
                                                fila["iva_importe"]
                                            ),
                                            "retencion": float(
                                                fila["retencion"]
                                            ),
                                            "total": float(fila["total"]),
                                            "forma_pago": fila["forma_pago"],
                                            "pagado": pagado_fila,
                                            "fecha_pago": (
                                                (
                                                    ""
                                                    if pd.isna(fila["fecha_pago"])
                                                    else (
                                                        fila["fecha_pago"]
                                                        .date()
                                                        .isoformat()
                                                    )
                                                )
                                                if pagado_fila
                                                else ""
                                            ),
                                            "cultivo": fila["cultivo"],
                                            "cultivo_id": _entero_o_none(
                                                fila_original.get("cultivo_id")
                                            ),
                                            "cliente_id": cliente_id_fila,
                                            "proveedor_id": proveedor_id_fila,
                                            "observaciones": (
                                                fila["observaciones"]
                                            ),
                                        },
                                    )

                                conn.commit()

                            except sqlite3.Error:

                                conn.rollback()
                                raise

                            finally:

                                conn.close()

                            mensajes_editor = ["Cambios contables guardados."]

                            for aviso in avisos_campana_edicion:

                                if aviso not in mensajes_editor:

                                    mensajes_editor.append(aviso)

                            st.session_state["mensaje_contabilidad"] = " ".join(
                                mensajes_editor
                            )
                            st.rerun()



    if seccion == "🗑️ Borrar":

        st.subheader("Borrar movimientos")

        def borrar_archivos_facturas(ids_movimientos):

            documentos_borrar = documentos_guardados[
                documentos_guardados["movimiento_id"].astype(int).isin(
                    [int(valor) for valor in ids_movimientos]
                )
            ]

            for _, documento in documentos_borrar.iterrows():

                eliminar_archivo_factura(documento["ruta_relativa"])

        borrar_registros_seguro(
            "movimientos_economicos",
            "id",
            movimientos_guardados,
            "movimientos económicos",
            tablas_hijas=[
                ("movimientos_economicos_lineas_iva", "movimiento_id"),
                ("movimientos_economicos_documentos", "movimiento_id")
            ],
            campo_descripcion="concepto",
            key="contabilidad_borrar_movimientos_economicos",
            post_borrar=borrar_archivos_facturas
        )
