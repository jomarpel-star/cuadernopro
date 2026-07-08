import sqlite3

import pandas as pd
import streamlit as st

from core.borrado import borrar_registros_seguro
from core.db import conectar, leer
from core.fechas import (
    formatear_fecha_es,
    parsear_fecha_es,
    preparar_columnas_fecha_tabla,
    validar_fecha_en_campana,
)
from core.filtros import mostrar_filtros_dataframe
from core.ui_tablas import preparar_dataframe_visual


def _texto(valor):

    if valor is None or pd.isna(valor):

        return ""

    return str(valor).strip()


def _numero(valor, defecto=0.0):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return defecto

    return float(numero)


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


def _tabla_actual_tiene_columna(tabla, columna):

    return columna in _columnas_tabla(tabla)


def _df_vacio_parcelas_cultivo():

    return pd.DataFrame(
        columns=[
            "cultivo_id",
            "parcela_id",
            "nombre",
            "poligono",
            "parcela",
            "recinto",
            "superficie_sigpac",
            "superficie_cultivo_parcela",
        ]
    )


def _valor_texto_columna(tabla, columna, columnas, defecto="''"):

    if columna in columnas:

        return f"COALESCE({tabla}.{columna},{defecto})"

    return defecto


def _valor_numerico_columna(tabla, columna, columnas, defecto="NULL"):

    if columna in columnas:

        return f"{tabla}.{columna}"

    return defecto


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


def _kg_compatibilidad(cantidad, unidad):

    if _texto(unidad).lower() not in ("", "kg", "kilo", "kilos"):

        return None

    numero = pd.to_numeric(cantidad, errors="coerce")

    if pd.isna(numero):

        return None

    return float(numero)


def _anadir_si_existe(destino, columnas, columna, valor):

    if columna in columnas:

        destino[columna] = valor


def _insertar_relaciones_cosecha_parcelas(conn, cosecha_id, parcelas_ids):

    if not _tabla_existe_conn(conn, "cosecha_parcelas"):

        return

    columnas = _columnas_tabla_conn(conn, "cosecha_parcelas")

    if not {"cosecha_id", "parcela_id"}.issubset(columnas):

        return

    for parcela_id in parcelas_ids or []:

        conn.execute(
            """
            INSERT INTO cosecha_parcelas
            (cosecha_id,parcela_id)
            VALUES (?,?)
            """,
            (int(cosecha_id), int(parcela_id)),
        )


def _normalizar_detalles_cosecha(detalles_cultivos):

    detalles = []
    vistos = set()

    for detalle in detalles_cultivos or []:

        cultivo_id = _entero_o_none(detalle.get("cultivo_id"))
        parcela_id = _entero_o_none(detalle.get("parcela_id"))

        if cultivo_id is None:

            continue

        clave = (cultivo_id, parcela_id)

        if clave in vistos:

            continue

        numero_superficie = pd.to_numeric(
            detalle.get("superficie"),
            errors="coerce",
        )
        superficie = None if pd.isna(numero_superficie) else float(numero_superficie)
        detalles.append(
            {
                "cultivo_id": cultivo_id,
                "parcela_id": parcela_id,
                "superficie": superficie,
                "observaciones": _texto(detalle.get("observaciones")),
            }
        )
        vistos.add(clave)

    return detalles


def _insertar_relaciones_cosecha_cultivos(conn, cosecha_id, detalles_cultivos):

    if not _tabla_existe_conn(conn, "cosecha_cultivos"):

        return

    columnas = _columnas_tabla_conn(conn, "cosecha_cultivos")

    if not {"cosecha_id", "cultivo_id"}.issubset(columnas):

        return

    for detalle in _normalizar_detalles_cosecha(detalles_cultivos):

        valores = {}
        _anadir_si_existe(valores, columnas, "cosecha_id", int(cosecha_id))
        _anadir_si_existe(
            valores,
            columnas,
            "cultivo_id",
            int(detalle["cultivo_id"]),
        )
        _anadir_si_existe(
            valores,
            columnas,
            "parcela_id",
            detalle["parcela_id"],
        )
        _anadir_si_existe(
            valores,
            columnas,
            "superficie",
            detalle["superficie"],
        )
        _anadir_si_existe(
            valores,
            columnas,
            "observaciones",
            detalle["observaciones"],
        )

        nombres = list(valores)
        marcadores = ",".join(["?"] * len(nombres))
        conn.execute(
            f"INSERT INTO cosecha_cultivos ({','.join(nombres)}) "
            f"VALUES ({marcadores})",
            [valores[columna] for columna in nombres],
        )


def _ajustar_superficie_detalles(detalles_cultivos, superficie_total):

    detalles = [detalle.copy() for detalle in detalles_cultivos or []]

    if not detalles:

        return detalles

    superficie_total = pd.to_numeric(superficie_total, errors="coerce")

    if pd.isna(superficie_total):

        return detalles

    superficie_total = float(superficie_total)
    superficie_original = sum(
        float(detalle.get("superficie") or 0)
        for detalle in detalles
    )

    if superficie_original > 0:

        factor = superficie_total / superficie_original

        for detalle in detalles:

            detalle["superficie"] = round(
                float(detalle.get("superficie") or 0) * factor,
                6,
            )

    elif superficie_total > 0:

        detalles[0]["superficie"] = superficie_total

    return detalles


def _insertar_cosecha_compatible(
    conn,
    datos,
    parcelas_ids=None,
    detalles_cultivos=None,
):

    columnas = _columnas_tabla_conn(conn, "cosecha")
    valores = {}
    cantidad = datos.get("cantidad", datos.get("kg"))
    unidad = _texto(datos.get("unidad")) or "kg"

    _anadir_si_existe(valores, columnas, "campana_id", datos.get("campana_id"))
    _anadir_si_existe(valores, columnas, "fecha", datos.get("fecha"))
    _anadir_si_existe(valores, columnas, "cultivo_id", datos.get("cultivo_id"))
    _anadir_si_existe(valores, columnas, "cliente_id", datos.get("cliente_id"))
    _anadir_si_existe(valores, columnas, "cantidad", cantidad)
    _anadir_si_existe(valores, columnas, "unidad", unidad)
    _anadir_si_existe(valores, columnas, "destino", _texto(datos.get("destino")))
    _anadir_si_existe(
        valores,
        columnas,
        "observaciones",
        _texto(datos.get("observaciones")),
    )

    _anadir_si_existe(valores, columnas, "cultivo", _texto(datos.get("cultivo")))
    _anadir_si_existe(valores, columnas, "producto", _texto(datos.get("producto")))
    _anadir_si_existe(valores, columnas, "parcelas", _texto(datos.get("parcelas")))
    _anadir_si_existe(
        valores,
        columnas,
        "kg",
        _kg_compatibilidad(cantidad, unidad),
    )
    _anadir_si_existe(valores, columnas, "precio", datos.get("precio"))
    _anadir_si_existe(valores, columnas, "lote", _texto(datos.get("lote")))
    _anadir_si_existe(valores, columnas, "cliente", _texto(datos.get("cliente")))
    _anadir_si_existe(
        valores,
        columnas,
        "nif_cliente",
        _texto(datos.get("nif_cliente")),
    )
    _anadir_si_existe(valores, columnas, "albaran", _texto(datos.get("albaran")))
    _anadir_si_existe(valores, columnas, "factura", _texto(datos.get("factura")))

    if not valores:

        raise sqlite3.OperationalError("La tabla cosecha no tiene columnas utiles")

    nombres = list(valores)
    marcadores = ",".join(["?"] * len(nombres))
    sql = (
        f"INSERT INTO cosecha ({','.join(nombres)}) "
        f"VALUES ({marcadores})"
    )
    cursor = conn.execute(sql, [valores[columna] for columna in nombres])
    cosecha_id = cursor.lastrowid
    _insertar_relaciones_cosecha_parcelas(conn, cosecha_id, parcelas_ids)
    _insertar_relaciones_cosecha_cultivos(
        conn,
        cosecha_id,
        detalles_cultivos,
    )
    return cosecha_id


def _actualizar_cosecha_compatible(conn, cosecha_id, datos):

    columnas = _columnas_tabla_conn(conn, "cosecha")
    valores = {}
    cantidad = datos.get("cantidad", datos.get("kg"))
    unidad = _texto(datos.get("unidad")) or "kg"

    for columna in (
        "campana_id",
        "fecha",
        "cultivo_id",
        "cliente_id",
        "destino",
        "observaciones",
        "cultivo",
        "producto",
        "parcelas",
        "precio",
        "lote",
        "cliente",
        "nif_cliente",
        "albaran",
        "factura",
    ):

        if columna in columnas and columna in datos:

            valores[columna] = datos[columna]

    if "cantidad" in columnas and (
        "cantidad" in datos or "kg" in datos
    ):

        valores["cantidad"] = cantidad

    if "unidad" in columnas and ("unidad" in datos or cantidad is not None):

        valores["unidad"] = unidad

    if "kg" in columnas and ("cantidad" in datos or "kg" in datos):

        valores["kg"] = _kg_compatibilidad(cantidad, unidad)

    if not valores:

        return

    asignaciones = ",".join(f"{columna}=?" for columna in valores)
    conn.execute(
        f"UPDATE cosecha SET {asignaciones} WHERE id=?",
        [valores[columna] for columna in valores] + [int(cosecha_id)],
    )


def _formatear_hectareas(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return ""

    return f"{float(numero):.2f} ha"


def _texto_parcela(fila):

    nombre = _texto(fila.get("nombre"))
    poligono = _texto(fila.get("poligono"))
    parcela = _texto(fila.get("parcela"))
    recinto = _texto(fila.get("recinto"))

    if nombre:

        return nombre

    referencia = "-".join(
        parte
        for parte in [poligono, parcela, recinto]
        if parte
    )

    return referencia or f"ID {int(fila['parcela_id'])}"


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

        return "Sin cultivo estructurado"

    campana = _texto(fila.get("campana_cultivo") or fila.get("campana"))
    nombre = _nombre_cultivo(fila) or "Sin nombre"
    ano_plantacion = _entero_o_none(fila.get("ano_plantacion"))
    superficie = _formatear_hectareas(_superficie_cultivo_para_etiqueta(fila))
    codigo_siex = _texto(fila.get("codigo_siex"))
    partes = []

    if campana:

        partes.append(f"Campaña {campana}")

    partes.append(nombre.upper())

    if ano_plantacion is not None:

        partes.append(f"Plantación {ano_plantacion}")

    if superficie:

        partes.append(superficie)

    if codigo_siex:

        partes.append(f"SIEX {codigo_siex}")

    return " — ".join(partes)


def _leer_cultivos_v6(conn=None):

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
    expr_parcela_id = (
        "cultivos.parcela_id"
        if "parcela_id" in columnas_cultivos
        else "NULL"
    )
    expr_nombre = _expr_nombre_cultivo(columnas_cultivos)
    expr_variedad = _expr_variedad_cultivo(columnas_cultivos)
    expr_sistema = _expr_sistema_cultivo(columnas_cultivos)
    expr_codigo_siex = _expr_codigo_siex_cultivo(columnas_cultivos)
    expr_superficie = _expr_superficie_cultivo(columnas_cultivos)
    expr_ano_plantacion = _valor_numerico_columna(
        "cultivos",
        "ano_plantacion",
        columnas_cultivos,
    )
    expr_activo = _expr_activo_cultivo(columnas_cultivos)

    cultivos = _leer_dataframe(
        f"""
        SELECT
            cultivos.id,
            {expr_campana_id} AS campana_id,
            COALESCE(campanas.nombre,'') AS campana,
            {expr_nombre} AS especie,
            {expr_nombre} AS nombre,
            {expr_variedad} AS variedad,
            {expr_sistema} AS sistema,
            {expr_codigo_siex} AS codigo_siex,
            {expr_superficie} AS superficie,
            {expr_ano_plantacion} AS ano_plantacion,
            {expr_parcela_id} AS parcela_id,
            {expr_activo} AS activo
        FROM cultivos
        LEFT JOIN campanas ON campanas.id = cultivos.campana_id
        ORDER BY
            CASE WHEN {expr_campana_id} IS NULL THEN 1 ELSE 0 END,
            campanas.fecha_inicio DESC,
            especie,
            variedad,
            sistema,
            cultivos.id
        """,
        conn=conn,
    )

    if cultivos.empty:

        return cultivos

    cultivos["cultivo_texto"] = cultivos.apply(_nombre_cultivo, axis=1)
    cultivos["etiqueta"] = cultivos.apply(_etiqueta_cultivo, axis=1)
    return cultivos


def _leer_parcelas_disponibles(conn=None):

    return _leer_dataframe(
        """
        SELECT
            id AS parcela_id,
            nombre,
            poligono,
            parcela,
            recinto,
            superficie_sigpac
        FROM parcelas
        ORDER BY poligono,parcela,recinto,id
        """,
        conn=conn,
    )


def _leer_parcelas_cultivos(conn=None):

    if conn is not None:

        tiene_cultivo_parcelas = _tabla_existe_conn(conn, "cultivo_parcelas")
        tiene_parcelas = _tabla_existe_conn(conn, "parcelas")
        cultivos_cols = _columnas_tabla_conn(conn, "cultivos")

    else:

        conn_tmp = conectar()

        try:

            tiene_cultivo_parcelas = _tabla_existe_conn(
                conn_tmp,
                "cultivo_parcelas",
            )
            tiene_parcelas = _tabla_existe_conn(conn_tmp, "parcelas")
            cultivos_cols = _columnas_tabla_conn(conn_tmp, "cultivos")

        finally:

            conn_tmp.close()

    if tiene_cultivo_parcelas and tiene_parcelas:

        parcelas_v6 = _leer_dataframe(
            """
            SELECT
                cultivo_parcelas.cultivo_id,
                parcelas.id AS parcela_id,
                parcelas.nombre,
                parcelas.poligono,
                parcelas.parcela,
                parcelas.recinto,
                parcelas.superficie_sigpac,
                cultivo_parcelas.superficie AS superficie_cultivo_parcela
            FROM cultivo_parcelas
            JOIN parcelas ON parcelas.id = cultivo_parcelas.parcela_id
            ORDER BY cultivo_parcelas.cultivo_id,parcelas.id
            """,
            conn=conn,
        )

    else:

        parcelas_v6 = _df_vacio_parcelas_cultivo()

    if "parcela_id" in cultivos_cols and tiene_parcelas:

        parcelas_legacy = _leer_dataframe(
            """
            SELECT
                cultivos.id AS cultivo_id,
                parcelas.id AS parcela_id,
                parcelas.nombre,
                parcelas.poligono,
                parcelas.parcela,
                parcelas.recinto,
                parcelas.superficie_sigpac,
                cultivos.superficie AS superficie_cultivo_parcela
            FROM cultivos
            JOIN parcelas ON parcelas.id = cultivos.parcela_id
            ORDER BY cultivos.id,parcelas.id
            """,
            conn=conn,
        )

    else:

        parcelas_legacy = _df_vacio_parcelas_cultivo()

    return parcelas_v6, parcelas_legacy


def _parcelas_para_cultivo(cultivo_id, parcelas_v6, parcelas_legacy):

    cultivo_id = _entero_o_none(cultivo_id)

    if cultivo_id is None:

        return pd.DataFrame()

    if not parcelas_v6.empty:

        v6 = parcelas_v6[
            parcelas_v6["cultivo_id"].astype(int) == int(cultivo_id)
        ].copy()

        if not v6.empty:

            return v6

    if parcelas_legacy.empty:

        return pd.DataFrame()

    return parcelas_legacy[
        parcelas_legacy["cultivo_id"].astype(int) == int(cultivo_id)
    ].copy()


def _cultivo_por_id(cultivos, cultivo_id):

    cultivo_id = _entero_o_none(cultivo_id)

    if cultivo_id is None or cultivos.empty:

        return None

    coincidencias = cultivos[cultivos["id"].astype(int) == int(cultivo_id)]

    if coincidencias.empty:

        return None

    return coincidencias.iloc[0]


def _ids_parcelas(dataframe):

    if dataframe.empty or "parcela_id" not in dataframe.columns:

        return []

    return (
        pd.to_numeric(dataframe["parcela_id"], errors="coerce")
        .dropna()
        .astype(int)
        .drop_duplicates()
        .tolist()
    )


def _superficie_fila_parcela_cosecha(fila):

    for columna in ("superficie_cultivo_parcela", "superficie_sigpac"):

        superficie = pd.to_numeric(fila.get(columna), errors="coerce")

        if not pd.isna(superficie):

            return float(superficie)

    return 0.0


def _sumar_superficie_parcelas(parcelas):

    if parcelas.empty:

        return 0.0

    return float(
        sum(_superficie_fila_parcela_cosecha(fila) for _, fila in parcelas.iterrows())
    )


def _superficie_sugerida(cultivo, parcelas_cultivo):

    if cultivo is not None:

        superficie = pd.to_numeric(cultivo.get("superficie"), errors="coerce")

        if not pd.isna(superficie) and float(superficie) > 0:

            return float(superficie)

    return _sumar_superficie_parcelas(parcelas_cultivo)


def _selector_cultivo_estructurado(
    cultivos,
    key,
    campana_id=None,
    valor_actual=None,
    seleccionar_primero=False,
):

    ids = []

    if not cultivos.empty:

        cultivos_ordenados = cultivos.copy()
        campana_id = _entero_o_none(campana_id)

        if campana_id is not None:

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
        "Cultivo",
        opciones,
        index=indice,
        format_func=lambda valor: (
            "Sin cultivo estructurado"
            if valor is None
            else _etiqueta_cultivo(_cultivo_por_id(cultivos, valor))
        ),
        key=key,
    )


def _leer_clientes_cosecha(solo_activos=True):

    sql = "SELECT id,nombre,nif,activo FROM clientes"

    if solo_activos:

        sql += " WHERE COALESCE(activo,1)=1"

    sql += " ORDER BY nombre,id"

    return leer(sql)


def _etiqueta_cliente(fila):

    if fila is None:

        return "Sin cliente"

    nombre = _texto(fila.get("nombre")) or f"ID {int(fila['id'])}"
    nif = _texto(fila.get("nif"))

    if nif:

        etiqueta = f"{nombre} — NIF {nif}"

    else:

        etiqueta = nombre

    activo = pd.to_numeric(fila.get("activo", 1), errors="coerce")

    if not pd.isna(activo) and int(activo) == 0:

        etiqueta += " (inactivo)"

    return etiqueta


def _cliente_por_id(clientes, cliente_id):

    cliente_id = _entero_o_none(cliente_id)

    if cliente_id is None or clientes.empty:

        return None

    coincidencias = clientes[clientes["id"].astype(int) == int(cliente_id)]

    if coincidencias.empty:

        return None

    return coincidencias.iloc[0]


def _selector_cliente(
    clientes,
    key,
    valor_actual=None,
    seleccionar_primero=False,
):

    ids = (
        clientes["id"].dropna().astype(int).tolist()
        if not clientes.empty and "id" in clientes.columns
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
        "Cliente / comprador",
        opciones,
        index=indice,
        format_func=lambda valor: (
            "Sin cliente"
            if valor is None
            else _etiqueta_cliente(_cliente_por_id(clientes, valor))
        ),
        key=key,
    )


def _coalesce_sql(expresiones):

    return "COALESCE(" + ",".join(expresiones) + ")"


def _leer_detalles_cosecha_cultivos(conn=None, cosecha_ids=None):

    ids = [
        int(valor)
        for valor in cosecha_ids or []
        if _entero_o_none(valor) is not None
    ]

    if cosecha_ids is not None and not ids:

        return pd.DataFrame()

    conn_propia = conn is None

    if conn_propia:

        conn = conectar()

    try:

        if not _tabla_existe_conn(conn, "cosecha_cultivos"):

            return pd.DataFrame()

        where = ""
        params = ()

        if ids:

            marcadores = ",".join(["?"] * len(ids))
            where = f"WHERE cosecha_cultivos.cosecha_id IN ({marcadores})"
            params = tuple(ids)

        return _leer_dataframe(
            f"""
            SELECT
                cosecha_cultivos.cosecha_id,
                cosecha_cultivos.cultivo_id,
                cosecha_cultivos.parcela_id,
                cosecha_cultivos.superficie,
                cosecha_cultivos.observaciones,
                COALESCE(cultivos.nombre,'') AS cultivo_nombre,
                COALESCE(cultivos.variedad,'') AS variedad,
                COALESCE(cultivos.codigo_siex,'') AS codigo_siex,
                cultivos.superficie AS superficie_cultivo,
                cultivos.ano_plantacion AS ano_plantacion,
                COALESCE(campanas.nombre,'') AS campana_cultivo,
                COALESCE(parcelas.nombre,'') AS parcela_nombre,
                parcelas.poligono,
                parcelas.parcela,
                parcelas.recinto,
                parcelas.superficie_sigpac
            FROM cosecha_cultivos
            LEFT JOIN cultivos ON cultivos.id = cosecha_cultivos.cultivo_id
            LEFT JOIN campanas ON campanas.id = cultivos.campana_id
            LEFT JOIN parcelas ON parcelas.id = cosecha_cultivos.parcela_id
            {where}
            ORDER BY
                cosecha_cultivos.cosecha_id,
                cultivos.nombre,
                cultivos.ano_plantacion,
                parcelas.poligono,
                parcelas.parcela,
                parcelas.recinto,
                cosecha_cultivos.id
            """,
            params,
            conn=conn,
        )

    finally:

        if conn_propia:

            conn.close()


def _etiqueta_cultivo_detalle(fila):

    return _etiqueta_cultivo(
        {
            "campana_cultivo": fila.get("campana_cultivo"),
            "nombre": fila.get("cultivo_nombre"),
            "variedad": fila.get("variedad"),
            "codigo_siex": fila.get("codigo_siex"),
            "superficie_cultivo": fila.get("superficie_cultivo"),
            "ano_plantacion": fila.get("ano_plantacion"),
        }
    )


def _etiqueta_parcela_detalle(fila):

    parcela_id = _entero_o_none(fila.get("parcela_id"))

    if parcela_id is None:

        return ""

    return _texto_parcela(
        {
            "parcela_id": parcela_id,
            "nombre": fila.get("parcela_nombre"),
            "poligono": fila.get("poligono"),
            "parcela": fila.get("parcela"),
            "recinto": fila.get("recinto"),
        }
    )


def _agregar_detalles_cosecha_cultivos(cosechas_guardadas, conn=None):

    if cosechas_guardadas.empty:

        cosechas_guardadas["cultivos_detalle"] = ""
        cosechas_guardadas["superficie_detalle"] = pd.NA
        return cosechas_guardadas

    cosechas_guardadas = cosechas_guardadas.copy()
    cosechas_guardadas["cultivos_detalle"] = ""
    cosechas_guardadas["superficie_detalle"] = pd.NA
    detalles = _leer_detalles_cosecha_cultivos(
        conn=conn,
        cosecha_ids=cosechas_guardadas["id"].dropna().astype(int).tolist(),
    )

    if detalles.empty:

        return cosechas_guardadas

    ids_cosecha = pd.to_numeric(cosechas_guardadas["id"], errors="coerce")

    for cosecha_id, grupo in detalles.groupby("cosecha_id", dropna=True):

        cosecha_id = int(cosecha_id)
        cultivo_etiquetas = []
        parcelas_etiquetas = []

        for _, fila_cultivo in grupo.drop_duplicates("cultivo_id").iterrows():

            etiqueta = _etiqueta_cultivo_detalle(fila_cultivo)

            if etiqueta:

                cultivo_etiquetas.append(etiqueta)

        for _, fila_parcela in grupo.iterrows():

            etiqueta = _etiqueta_parcela_detalle(fila_parcela)

            if etiqueta:

                parcelas_etiquetas.append(etiqueta)

        superficie = pd.to_numeric(grupo["superficie"], errors="coerce")
        superficie_total = float(superficie.fillna(0).sum())
        mascara = ids_cosecha == cosecha_id

        if cultivo_etiquetas:

            cosechas_guardadas.loc[mascara, "cultivos_detalle"] = ", ".join(
                dict.fromkeys(cultivo_etiquetas)
            )

        if parcelas_etiquetas:

            cosechas_guardadas.loc[mascara, "parcelas"] = ", ".join(
                dict.fromkeys(parcelas_etiquetas)
            )

        if superficie.notna().any():

            cosechas_guardadas.loc[mascara, "superficie_detalle"] = (
                superficie_total
            )

    return cosechas_guardadas


def _leer_cosechas_guardadas(conn=None, cosecha_id=None):

    if conn is not None:

        cosecha_cols = _columnas_tabla_conn(conn, "cosecha")
        cultivos_cols = _columnas_tabla_conn(conn, "cultivos")
        clientes_cols = _columnas_tabla_conn(conn, "clientes")
        tiene_cosecha_parcelas = _tabla_existe_conn(conn, "cosecha_parcelas")
        tiene_parcelas = _tabla_existe_conn(conn, "parcelas")

    else:

        conn_tmp = conectar()

        try:

            cosecha_cols = _columnas_tabla_conn(conn_tmp, "cosecha")
            cultivos_cols = _columnas_tabla_conn(conn_tmp, "cultivos")
            clientes_cols = _columnas_tabla_conn(conn_tmp, "clientes")
            tiene_cosecha_parcelas = _tabla_existe_conn(
                conn_tmp,
                "cosecha_parcelas",
            )
            tiene_parcelas = _tabla_existe_conn(conn_tmp, "parcelas")

        finally:

            conn_tmp.close()

    if not cosecha_cols:

        return pd.DataFrame()

    expr_fecha = _valor_texto_columna("cosecha", "fecha", cosecha_cols)
    expr_campana_id = _valor_numerico_columna(
        "cosecha",
        "campana_id",
        cosecha_cols,
    )
    expr_cultivo_id = _valor_numerico_columna(
        "cosecha",
        "cultivo_id",
        cosecha_cols,
    )
    expr_cliente_id = _valor_numerico_columna(
        "cosecha",
        "cliente_id",
        cosecha_cols,
    )
    expr_producto = _valor_texto_columna("cosecha", "producto", cosecha_cols)
    expr_lote = _valor_texto_columna("cosecha", "lote", cosecha_cols)
    expr_albaran = _valor_texto_columna("cosecha", "albaran", cosecha_cols)
    expr_factura = _valor_texto_columna("cosecha", "factura", cosecha_cols)
    expr_destino = _valor_texto_columna("cosecha", "destino", cosecha_cols)
    expr_observaciones = _valor_texto_columna(
        "cosecha",
        "observaciones",
        cosecha_cols,
    )
    expr_precio = _valor_numerico_columna("cosecha", "precio", cosecha_cols)
    expr_cultivo_legacy = _valor_texto_columna(
        "cosecha",
        "cultivo",
        cosecha_cols,
    )

    if "cantidad" in cosecha_cols and "kg" in cosecha_cols:

        expr_cantidad = "COALESCE(cosecha.cantidad,cosecha.kg)"

    elif "cantidad" in cosecha_cols:

        expr_cantidad = "cosecha.cantidad"

    elif "kg" in cosecha_cols:

        expr_cantidad = "cosecha.kg"

    else:

        expr_cantidad = "NULL"

    if "unidad" in cosecha_cols:

        expr_unidad = "COALESCE(cosecha.unidad,'')"

    elif "kg" in cosecha_cols:

        expr_unidad = "'kg'"

    else:

        expr_unidad = "''"

    if "precio" in cosecha_cols:

        expr_importe = (
            f"COALESCE({expr_cantidad},0) * COALESCE(cosecha.precio,0)"
        )

    else:

        expr_importe = "NULL"

    expr_nombre_cultivo = _expr_nombre_cultivo(cultivos_cols)
    expr_variedad = _expr_variedad_cultivo(cultivos_cols)
    expr_sistema = _expr_sistema_cultivo(cultivos_cols)
    expr_codigo_siex = _expr_codigo_siex_cultivo(cultivos_cols)
    expr_superficie = _expr_superficie_cultivo(cultivos_cols)

    clientes_nombre = []
    clientes_nif = []

    if "cliente_id" in cosecha_cols and "nombre" in clientes_cols:

        clientes_nombre.append("clientes.nombre")

    if "cliente" in cosecha_cols:

        clientes_nombre.append("cosecha.cliente")

    clientes_nombre.append("''")

    if "cliente_id" in cosecha_cols and "nif" in clientes_cols:

        clientes_nif.append("clientes.nif")

    if "nif_cliente" in cosecha_cols:

        clientes_nif.append("cosecha.nif_cliente")

    clientes_nif.append("''")

    if tiene_cosecha_parcelas and tiene_parcelas:

        expr_parcelas_join = """
            GROUP_CONCAT(
                CASE
                    WHEN IFNULL(parcelas.nombre,'') != ''
                    THEN parcelas.nombre
                    ELSE parcelas.poligono || '-' ||
                         parcelas.parcela || '-' || parcelas.recinto
                END,
                ', '
            )
        """

        if "parcelas" in cosecha_cols:

            expr_parcelas = (
                "COALESCE("
                f"{expr_parcelas_join},"
                "cosecha.parcelas,"
                "''"
                ")"
            )

        else:

            expr_parcelas = f"COALESCE({expr_parcelas_join},'')"

    elif "parcelas" in cosecha_cols:

        expr_parcelas = "COALESCE(cosecha.parcelas,'')"

    else:

        expr_parcelas = "''"

    joins = [
        "LEFT JOIN campanas ON campanas.id = cosecha.campana_id",
        "LEFT JOIN cultivos ON cultivos.id = cosecha.cultivo_id",
        """
        LEFT JOIN campanas AS campanas_cultivo
        ON campanas_cultivo.id = cultivos.campana_id
        """,
    ]

    if "cliente_id" in cosecha_cols:

        joins.append("LEFT JOIN clientes ON clientes.id = cosecha.cliente_id")

    if tiene_cosecha_parcelas and tiene_parcelas:

        joins.extend(
            [
                """
                LEFT JOIN cosecha_parcelas
                ON cosecha_parcelas.cosecha_id = cosecha.id
                """,
                "LEFT JOIN parcelas ON parcelas.id = cosecha_parcelas.parcela_id",
            ]
        )

    where = ""
    params = ()

    if cosecha_id is not None:

        where = "WHERE cosecha.id=?"
        params = (int(cosecha_id),)

    sql = f"""
        SELECT
        cosecha.id,
        {expr_campana_id} AS campana_id,
        {expr_cultivo_id} AS cultivo_id,
        {expr_cliente_id} AS cliente_id,
        {expr_fecha} AS fecha,
        COALESCE(campanas.nombre,'') AS campana,
        {expr_cultivo_legacy} AS cultivo,
        {expr_nombre_cultivo} AS cultivo_v6,
        {expr_variedad} AS variedad_v6,
        {expr_sistema} AS sistema_v6,
        {expr_codigo_siex} AS codigo_siex,
        {expr_superficie} AS superficie_cultivo,
        COALESCE(campanas_cultivo.nombre,'') AS campana_cultivo,
        {expr_parcelas} AS parcelas,
        {expr_producto} AS producto,
        {expr_cantidad} AS cantidad,
        {expr_cantidad} AS kg,
        {expr_precio} AS precio,
        {expr_importe} AS importe_total,
        {expr_unidad} AS unidad,
        {expr_lote} AS lote,
        {_coalesce_sql(clientes_nombre)} AS cliente,
        {_coalesce_sql(clientes_nif)} AS nif_cliente,
        {expr_albaran} AS albaran,
        {expr_factura} AS factura,
        {expr_destino} AS destino,
        {expr_observaciones} AS observaciones
        FROM cosecha
        {" ".join(joins)}
        {where}
        GROUP BY cosecha.id
        ORDER BY cosecha.fecha DESC, cosecha.id DESC
    """

    cosechas_guardadas = _leer_dataframe(sql, params, conn=conn)
    return _agregar_detalles_cosecha_cultivos(
        cosechas_guardadas,
        conn=conn,
    )


def _preparar_cosechas_presentacion(cosechas_guardadas):

    if not cosechas_guardadas.empty:

        cosechas_guardadas = cosechas_guardadas.copy()
        cosechas_guardadas["cultivo_estructurado"] = (
            cosechas_guardadas.apply(
                lambda fila: (
                    _etiqueta_cultivo(fila)
                    if _entero_o_none(fila.get("cultivo_id")) is not None
                    else ""
                ),
                axis=1,
            )
        )
        cultivo_base = cosechas_guardadas["cultivo_estructurado"].where(
            cosechas_guardadas["cultivo_estructurado"] != "",
            cosechas_guardadas["cultivo"].fillna("").astype(str),
        )
        cultivos_detalle = (
            cosechas_guardadas["cultivos_detalle"].fillna("").astype(str)
            if "cultivos_detalle" in cosechas_guardadas.columns
            else pd.Series("", index=cosechas_guardadas.index)
        )
        cosechas_guardadas["cultivo_mostrado"] = (
            cultivos_detalle.where(cultivos_detalle != "", cultivo_base)
        )
        cosechas_guardadas["cultivo_origen"] = (
            cosechas_guardadas.apply(
                lambda fila: (
                    "cosecha_cultivos"
                    if _texto(fila.get("cultivos_detalle"))
                    else (
                        "cultivo_id"
                        if _entero_o_none(fila.get("cultivo_id")) is not None
                        else "texto"
                    )
                ),
                axis=1,
            )
        )
        return cosechas_guardadas

    cosechas_guardadas["cultivo_estructurado"] = ""
    cosechas_guardadas["cultivo_mostrado"] = ""
    cosechas_guardadas["cultivo_origen"] = ""
    cosechas_guardadas["cultivos_detalle"] = ""
    cosechas_guardadas["superficie_detalle"] = pd.NA
    return cosechas_guardadas


def render(CAMPANA):


    st.title("🌰 Cosecha")

    opciones_cosecha = [
        "📋 Listado",
        "➕ Nueva cosecha",
        "🔁 Duplicar",
        "✏️ Editar",
        "🗑️ Borrar",
    ]
    seccion_cosecha = st.radio(
        "Opciones de cosecha",
        opciones_cosecha,
        horizontal=True,
        key="cosecha_seccion"
    )

    campana_cosecha = leer(
        "SELECT nombre FROM campanas WHERE id=?",
        (CAMPANA,)
    )
    nombre_campana_cosecha = (
        str(campana_cosecha.iloc[0]["nombre"])
        if not campana_cosecha.empty
        else str(CAMPANA)
    )

    st.info(f"Campaña activa: {nombre_campana_cosecha}")

    cultivos_cosecha = _leer_cultivos_v6()
    parcelas_cultivos_v6, parcelas_cultivos_legacy = _leer_parcelas_cultivos()
    parcelas_disponibles = _leer_parcelas_disponibles()
    clientes_activos_cosecha = _leer_clientes_cosecha()
    clientes_edicion_cosecha = _leer_clientes_cosecha(solo_activos=False)
    columnas_cosecha = _columnas_tabla("cosecha")
    cosecha_tiene_producto = "producto" in columnas_cosecha
    cosecha_tiene_precio = "precio" in columnas_cosecha
    cosecha_tiene_lote = "lote" in columnas_cosecha
    cosecha_tiene_albaran = "albaran" in columnas_cosecha
    cosecha_tiene_factura = "factura" in columnas_cosecha
    cosecha_tiene_cultivo_legacy = "cultivo" in columnas_cosecha
    cosecha_tiene_cliente_legacy = "cliente" in columnas_cosecha
    cosecha_tiene_nif_cliente_legacy = "nif_cliente" in columnas_cosecha
    cosecha_tiene_unidad = "unidad" in columnas_cosecha


    if seccion_cosecha == "➕ Nueva cosecha":

        if "form_cosecha_version" not in st.session_state:

            st.session_state["form_cosecha_version"] = 0

        form_cosecha_version = st.session_state["form_cosecha_version"]

        if cultivos_cosecha.empty:

            if cosecha_tiene_cultivo_legacy:

                st.info(
                    "No hay cultivos estructurados disponibles. Puede "
                    "registrar una cosecha con cultivo textual para mantener "
                    "compatibilidad."
                )

            else:

                st.info(
                    "No hay cultivos estructurados disponibles. Crea un "
                    "cultivo antes de registrar cosecha."
                )

        cultivos_ids_disponibles = (
            cultivos_cosecha["id"].dropna().astype(int).tolist()
            if not cultivos_cosecha.empty
            else []
        )
        cultivos_ids_cosecha = []

        if cultivos_ids_disponibles:

            cultivos_campana = cultivos_cosecha[
                pd.to_numeric(
                    cultivos_cosecha["campana_id"],
                    errors="coerce",
                ) == int(CAMPANA)
            ]
            cultivos_default = (
                cultivos_campana["id"].dropna().astype(int).head(1).tolist()
                if not cultivos_campana.empty
                else cultivos_ids_disponibles[:1]
            )
            cultivos_ids_cosecha = st.multiselect(
                "Cultivos cosechados",
                cultivos_ids_disponibles,
                default=cultivos_default,
                format_func=lambda valor: _etiqueta_cultivo(
                    _cultivo_por_id(cultivos_cosecha, valor)
                ),
                key=f"cultivos_cosecha_{form_cosecha_version}",
            )

        cultivo_id_cosecha = (
            int(cultivos_ids_cosecha[0])
            if cultivos_ids_cosecha
            else None
        )
        cultivos_seleccionados = [
            _cultivo_por_id(cultivos_cosecha, cultivo_id)
            for cultivo_id in cultivos_ids_cosecha
        ]
        cultivo_cosecha = ", ".join(
            _nombre_cultivo(cultivo)
            for cultivo in cultivos_seleccionados
            if cultivo is not None and _nombre_cultivo(cultivo)
        )

        if not cultivos_ids_cosecha and cosecha_tiene_cultivo_legacy:

            cultivo_cosecha = st.text_input(
                "Cultivo textual de compatibilidad",
                key=f"cultivo_texto_cosecha_{form_cosecha_version}",
            )

        elif not cultivos_ids_cosecha:

            st.info("Selecciona al menos un cultivo estructurado.")

        else:

            st.caption(
                "Cultivos seleccionados: "
                f"{len(cultivos_ids_cosecha)}."
            )

        etiquetas_parcelas_cosecha = {
            int(fila["parcela_id"]): _texto_parcela(fila)
            for _, fila in parcelas_disponibles.iterrows()
        } if not parcelas_disponibles.empty else {}

        if parcelas_disponibles.empty:

            st.warning("No hay parcelas registradas para asociar a la cosecha")

        detalles_cosecha = []
        resumen_detalles_cosecha = []
        parcelas_cosecha_sel_ids = []
        parcelas_cosecha_sin_superficie = False

        for cultivo_id in cultivos_ids_cosecha:

            cultivo = _cultivo_por_id(cultivos_cosecha, cultivo_id)
            etiqueta_cultivo = _etiqueta_cultivo(cultivo)
            parcelas_cultivo = _parcelas_para_cultivo(
                cultivo_id,
                parcelas_cultivos_v6,
                parcelas_cultivos_legacy,
            )
            parcelas_sugeridas = _ids_parcelas(parcelas_cultivo)

            if not parcelas_sugeridas:

                st.info(
                    "El cultivo seleccionado no tiene parcelas asociadas: "
                    f"{etiqueta_cultivo}."
                )
                continue

            etiquetas_parcelas_cultivo = {
                int(fila["parcela_id"]): _texto_parcela(fila)
                for _, fila in parcelas_cultivo.iterrows()
            }
            parcelas_cultivo_sel = st.multiselect(
                f"Parcelas cosechadas de {etiqueta_cultivo}",
                parcelas_sugeridas,
                default=parcelas_sugeridas,
                format_func=lambda valor: etiquetas_parcelas_cultivo.get(
                    int(valor),
                    str(valor),
                ),
                key=(
                    f"parcelas_cosecha_cultivo_{form_cosecha_version}_"
                    f"{cultivo_id}"
                ),
            )

            for parcela_id in parcelas_cultivo_sel:

                parcela_id = int(parcela_id)
                fila_parcela = parcelas_cultivo[
                    parcelas_cultivo["parcela_id"].astype(int) == parcela_id
                ].iloc[0]
                superficie = _superficie_fila_parcela_cosecha(fila_parcela)

                if superficie <= 0:

                    parcelas_cosecha_sin_superficie = True

                detalles_cosecha.append(
                    {
                        "cultivo_id": int(cultivo_id),
                        "parcela_id": parcela_id,
                        "superficie": superficie,
                    }
                )
                parcelas_cosecha_sel_ids.append(parcela_id)
                resumen_detalles_cosecha.append(
                    {
                        "Cultivo": _nombre_cultivo(cultivo),
                        "Parcela": etiquetas_parcelas_cultivo.get(
                            parcela_id,
                            str(parcela_id),
                        ),
                        "Superficie": superficie,
                    }
                )

        parcelas_cosecha_sel_ids = list(dict.fromkeys(parcelas_cosecha_sel_ids))
        parcelas_cosecha_sel = parcelas_cosecha_sel_ids
        superficie_total_seleccionada = float(
            sum(detalle["superficie"] or 0 for detalle in detalles_cosecha)
        )

        if resumen_detalles_cosecha:

            resumen_detalles_df = pd.DataFrame(resumen_detalles_cosecha)
            resumen_detalles_visual = preparar_dataframe_visual(
                resumen_detalles_df,
                columnas=["Cultivo", "Parcela", "Superficie"],
                ocultar_tecnicas=True,
            )
            st.dataframe(
                resumen_detalles_visual,
                hide_index=True,
                use_container_width=True,
            )

        superficie_total_guardar = st.number_input(
            "Superficie cosechada total (ha)",
            min_value=0.0,
            value=round(superficie_total_seleccionada, 4),
            step=0.01,
            key=f"cosecha_superficie_total_{form_cosecha_version}",
        )

        st.info(
            "Superficie seleccionada: "
            f"{superficie_total_seleccionada:.2f} ha"
        )

        if parcelas_cosecha_sin_superficie:

            st.warning(
                "Hay parcelas seleccionadas sin superficie informada."
            )

        if clientes_activos_cosecha.empty:

            st.info(
                "No hay clientes dados de alta. Puede crear clientes en "
                "Clientes / Proveedores."
            )
            cliente_id_cosecha = None

        else:

            cliente_id_cosecha = _selector_cliente(
                clientes_activos_cosecha,
                f"cliente_id_cosecha_v610_{form_cosecha_version}",
                seleccionar_primero=True,
            )

        cliente_seleccionado = _cliente_por_id(
            clientes_activos_cosecha,
            cliente_id_cosecha,
        )
        nombre_cliente_sugerido = (
            _texto(cliente_seleccionado.get("nombre"))
            if cliente_seleccionado is not None
            else ""
        )
        nif_cliente_sugerido = (
            _texto(cliente_seleccionado.get("nif"))
            if cliente_seleccionado is not None
            else ""
        )
        with st.form(f"nueva_cosecha_v{form_cosecha_version}"):

            fecha_cosecha_texto = st.text_input(
                "Fecha",
                value=formatear_fecha_es(pd.Timestamp.today()),
                placeholder="DD/MM/AAAA",
                key=f"cosecha_fecha_{form_cosecha_version}"
            )
            error_formato_fecha_cosecha = False

            try:

                fecha_cosecha_iso = parsear_fecha_es(fecha_cosecha_texto)
                fecha_cosecha = pd.to_datetime(
                    fecha_cosecha_iso,
                    errors="coerce"
                ).date() if fecha_cosecha_iso else None

            except ValueError:

                error_formato_fecha_cosecha = True
                fecha_cosecha = None

            validacion_fecha_cosecha = (
                validar_fecha_en_campana(CAMPANA, fecha_cosecha)
                if fecha_cosecha is not None
                else {
                    "requiere_confirmacion": False,
                    "mensaje": ""
                }
            )
            confirmar_fecha_cosecha = False

            if validacion_fecha_cosecha["requiere_confirmacion"]:

                st.warning(validacion_fecha_cosecha["mensaje"])
                confirmar_fecha_cosecha = st.checkbox(
                    "Confirmo que quiero guardar este registro aunque esté "
                    "fuera del periodo de campaña",
                    key=f"confirmar_fecha_fuera_cosecha_{form_cosecha_version}"
                )

            elif validacion_fecha_cosecha["mensaje"]:

                st.info(validacion_fecha_cosecha["mensaje"])

            if cosecha_tiene_producto:

                producto_cosecha = st.text_input(
                    "Producto cosechado",
                    key=f"cosecha_producto_{form_cosecha_version}"
                )

            else:

                producto_cosecha = ""

            kg_cosecha = st.number_input(
                "Cantidad",
                min_value=0.0,
                value=0.0,
                key=f"cosecha_kg_{form_cosecha_version}"
            )
            if cosecha_tiene_unidad:

                unidad_cosecha = st.selectbox(
                    "Unidad",
                    ["kg", "t", "l", "ud"],
                    key=f"cosecha_unidad_{form_cosecha_version}",
                )

            else:

                unidad_cosecha = "kg"
                st.caption("Unidad: kg")

            if cosecha_tiene_precio:

                precio_cosecha = st.number_input(
                    "Precio €/kg",
                    min_value=0.0,
                    value=0.0,
                    key=f"cosecha_precio_{form_cosecha_version}"
                )

            else:

                precio_cosecha = None

            if cosecha_tiene_lote:

                lote_cosecha = st.text_input(
                    "Lote",
                    key=f"cosecha_lote_{form_cosecha_version}"
                )

            else:

                lote_cosecha = ""

            if (
                cliente_seleccionado is None
                and (
                    cosecha_tiene_cliente_legacy
                    or cosecha_tiene_nif_cliente_legacy
                )
            ):

                cliente_cosecha = st.text_input(
                    "Cliente / comprador manual",
                    key=f"cosecha_cliente_manual_{form_cosecha_version}",
                )
                nif_cliente_cosecha = st.text_input(
                    "NIF cliente manual",
                    key=f"cosecha_nif_cliente_manual_{form_cosecha_version}",
                )

            else:

                cliente_cosecha = nombre_cliente_sugerido
                nif_cliente_cosecha = nif_cliente_sugerido

                if cliente_seleccionado is not None:

                    resumen_cliente = (
                        f"{cliente_cosecha}"
                        + (
                            f" — NIF {nif_cliente_cosecha}"
                            if nif_cliente_cosecha
                            else ""
                        )
                    )
                    st.caption(
                        "Cliente seleccionado: "
                        f"{resumen_cliente or 'Sin nombre'}."
                    )

            if cosecha_tiene_albaran:

                albaran_cosecha = st.text_input(
                    "Albarán",
                    key=f"cosecha_albaran_{form_cosecha_version}"
                )

            else:

                albaran_cosecha = ""

            if cosecha_tiene_factura:

                factura_cosecha = st.text_input(
                    "Factura",
                    key=f"cosecha_factura_{form_cosecha_version}"
                )

            else:

                factura_cosecha = ""

            destino_cosecha = st.text_input(
                "Destino",
                key=f"cosecha_destino_{form_cosecha_version}"
            )
            observaciones_cosecha = st.text_area(
                "Observaciones",
                key=f"cosecha_observaciones_{form_cosecha_version}"
            )

            guardar_cosecha = st.form_submit_button("Registrar cosecha")

        if guardar_cosecha:

            if (
                error_formato_fecha_cosecha
            ):

                st.warning("La fecha debe tener formato DD/MM/AAAA")

            elif fecha_cosecha is None:

                st.warning("La fecha es obligatoria")

            elif (
                validacion_fecha_cosecha["requiere_confirmacion"]
                and not confirmar_fecha_cosecha
            ):

                st.warning("Marca la confirmación para guardar la cosecha")

            elif not cultivos_ids_cosecha and not _texto(cultivo_cosecha):

                st.warning(
                    "Selecciona un cultivo estructurado o indica un cultivo textual"
                )

            elif not detalles_cosecha:

                st.warning("Selecciona al menos una parcela")

            elif cosecha_tiene_producto and not producto_cosecha.strip():

                st.warning("El producto cosechado no puede estar vacío")

            elif kg_cosecha <= 0:

                st.warning("La cantidad debe ser mayor que 0")

            else:

                if not cliente_cosecha.strip():

                    st.warning(
                        "Se recomienda indicar el cliente o comprador"
                    )

                texto_parcelas_cosecha = ", ".join(
                    dict.fromkeys(
                        etiquetas_parcelas_cosecha.get(
                            int(parcela_id),
                            str(parcela_id)
                        )
                        for parcela_id in parcelas_cosecha_sel
                    )
                )
                detalles_cosecha_guardar = _ajustar_superficie_detalles(
                    detalles_cosecha,
                    superficie_total_guardar,
                )

                conn = conectar()

                try:

                    _insertar_cosecha_compatible(
                        conn,
                        {
                            "campana_id": CAMPANA,
                            "fecha": fecha_cosecha.isoformat(),
                            "cultivo_id": _entero_o_none(cultivo_id_cosecha),
                            "cultivo": _texto(cultivo_cosecha),
                            "producto": producto_cosecha.strip(),
                            "parcelas": texto_parcelas_cosecha,
                            "cantidad": kg_cosecha,
                            "unidad": unidad_cosecha,
                            "precio": precio_cosecha,
                            "lote": lote_cosecha.strip(),
                            "cliente_id": _entero_o_none(cliente_id_cosecha),
                            "cliente": cliente_cosecha.strip(),
                            "nif_cliente": nif_cliente_cosecha.strip(),
                            "albaran": albaran_cosecha.strip(),
                            "factura": factura_cosecha.strip(),
                            "destino": destino_cosecha.strip(),
                            "observaciones": observaciones_cosecha.strip(),
                        },
                        parcelas_cosecha_sel,
                        detalles_cultivos=detalles_cosecha_guardar,
                    )

                    conn.commit()

                except sqlite3.Error:

                    conn.rollback()
                    raise

                finally:

                    conn.close()

                st.success("Cosecha registrada")
                st.session_state["form_cosecha_version"] += 1
                st.rerun()

    cosechas_guardadas = _preparar_cosechas_presentacion(
        _leer_cosechas_guardadas()
    )


    if seccion_cosecha == "📋 Listado":

        cosechas_filtradas = mostrar_filtros_dataframe(
            cosechas_guardadas,
            "cosecha_listado",
            columnas_texto=[
                "producto",
                "cultivo_mostrado",
                "parcelas",
                "cliente",
                "nif_cliente",
                "lote",
                "albaran",
                "factura",
                "destino",
                "observaciones"
            ],
            columna_fecha="fecha",
            filtros_select={
                "Campaña": "campana",
                "Cultivo": "cultivo_mostrado",
                "Producto": "producto",
                "Cliente": "cliente"
            }
        )
        columnas_ocultas = [
            "campana_id",
            "cultivo_id",
            "cliente_id",
            "cultivo",
            "cultivo_origen",
            "cultivo_v6",
            "variedad_v6",
            "sistema_v6",
            "codigo_siex",
            "superficie_cultivo",
            "campana_cultivo",
            "cultivo_estructurado",
            "cultivos_detalle",
            "cantidad",
        ]
        cosechas_listado = cosechas_filtradas.drop(
            columns=columnas_ocultas,
            errors="ignore"
        )
        columnas_listado = [
            "id",
            "campana",
            "fecha",
            "cultivo_mostrado",
            "parcelas",
            "superficie_detalle",
        ]

        if cosecha_tiene_producto:

            columnas_listado.append("producto")

        columnas_listado.extend(["kg", "unidad"])

        if cosecha_tiene_precio:

            columnas_listado.extend(["precio", "importe_total"])

        if cosecha_tiene_lote:

            columnas_listado.append("lote")

        columnas_listado.append("cliente")

        if cosecha_tiene_nif_cliente_legacy or "cliente_id" in columnas_cosecha:

            columnas_listado.append("nif_cliente")

        if cosecha_tiene_albaran:

            columnas_listado.append("albaran")

        if cosecha_tiene_factura:

            columnas_listado.append("factura")

        columnas_listado.extend(["destino", "observaciones"])
        cosechas_visual = preparar_dataframe_visual(
            preparar_columnas_fecha_tabla(cosechas_listado, ["fecha"]),
            columnas=columnas_listado,
            ocultar_tecnicas=True,
            etiquetas_extra={
                "cultivo_mostrado": "Cultivo",
                "nif_cliente": "NIF cliente",
                "albaran": "Albarán",
                "factura": "Factura",
                "destino": "Destino",
                "kg": "Cantidad",
                "superficie_detalle": "Superficie",
            },
        )
        st.dataframe(
            cosechas_visual,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Fecha": st.column_config.DateColumn(
                    "Fecha",
                    format="DD/MM/YYYY"
                ),
            }
        )


    if seccion_cosecha == "🔁 Duplicar":

        mensaje_duplicacion_cosecha = st.session_state.pop(
            "duplicar_cosecha_mensaje",
            None
        )

        if mensaje_duplicacion_cosecha:

            st.success(mensaje_duplicacion_cosecha)

        with st.expander("Duplicar registro existente"):

            if cosechas_guardadas.empty:

                st.info("No hay cosechas para duplicar")

            else:

                cosechas_por_id = (
                    cosechas_guardadas
                    .copy()
                    .set_index("id", drop=False)
                )
                ids_cosechas = [
                    int(valor)
                    for valor in cosechas_por_id.index.tolist()
                ]

                def formato_cosecha_origen(cosecha_id):

                    fila = cosechas_por_id.loc[cosecha_id]
                    fecha = formatear_fecha_es(fila["fecha"])
                    producto = _texto(fila["producto"])
                    kg = _numero(fila["kg"])
                    unidad = _texto(fila.get("unidad")) or "kg"
                    cultivo = _texto(fila["cultivo_mostrado"])

                    return (
                        f"#{cosecha_id} · {fecha} · {producto} · "
                        f"{kg:g} {unidad} · {cultivo}"
                    )

                cosecha_origen_id = st.selectbox(
                    "Cosecha a duplicar",
                    ids_cosechas,
                    format_func=formato_cosecha_origen,
                    key="dup_cosecha_origen_id"
                )
                claves_duplicar_cosecha = [
                    f"dup_cosecha_fecha_{cosecha_origen_id}",
                    f"dup_cosecha_kg_{cosecha_origen_id}",
                    f"dup_cosecha_albaran_{cosecha_origen_id}",
                    f"dup_cosecha_factura_{cosecha_origen_id}",
                    f"dup_cosecha_obs_{cosecha_origen_id}",
                    f"dup_cosecha_confirm_fecha_{cosecha_origen_id}",
                    f"dup_cosecha_confirm_{cosecha_origen_id}",
                    f"dup_cosecha_btn_{cosecha_origen_id}"
                ]

                if (
                    st.session_state.get("dup_cosecha_origen_id_anterior")
                    != cosecha_origen_id
                ):

                    for clave in claves_duplicar_cosecha:

                        st.session_state.pop(clave, None)

                    st.session_state["dup_cosecha_origen_id_anterior"] = (
                        cosecha_origen_id
                    )

                cosecha_resumen = cosechas_por_id.loc[cosecha_origen_id]
                cosecha_origen_df = _leer_cosechas_guardadas(
                    cosecha_id=cosecha_origen_id,
                )

                if cosecha_origen_df.empty:

                    st.warning("No se encontró el registro origen")

                else:

                    cosecha_origen = cosecha_origen_df.iloc[0]

                    st.write(
                        "Origen: "
                        f"campaña {_texto(cosecha_origen['campana'])} · "
                        f"cultivo {_texto(cosecha_resumen['cultivo_mostrado'])} · "
                        f"parcelas {_texto(cosecha_resumen['parcelas']) or 'Sin parcelas'} · "
                        f"cliente {_texto(cosecha_origen['cliente']) or 'Sin cliente'}"
                    )

                    with st.form(
                        f"dup_cosecha_form_{cosecha_origen_id}"
                    ):

                        fecha_copia_texto = st.text_input(
                            "Fecha",
                            value=formatear_fecha_es(cosecha_origen["fecha"]),
                            placeholder="DD/MM/AAAA",
                            key=f"dup_cosecha_fecha_{cosecha_origen_id}"
                        )
                        error_fecha_copia = False

                        try:

                            fecha_copia_iso = parsear_fecha_es(
                                fecha_copia_texto
                            )
                            fecha_copia = pd.to_datetime(
                                fecha_copia_iso,
                                errors="coerce"
                            ).date() if fecha_copia_iso else None

                        except ValueError:

                            error_fecha_copia = True
                            fecha_copia = None

                        campana_origen = _entero_o_none(
                            cosecha_origen["campana_id"]
                        )
                        campana_copia = (
                            campana_origen
                            if campana_origen is not None
                            else int(CAMPANA)
                        )

                        if campana_origen is None:

                            st.warning(
                                "El registro origen no tiene campaña asociada; "
                                "la copia se guardará en la campaña activa."
                            )

                        validacion_fecha_copia = (
                            validar_fecha_en_campana(campana_copia, fecha_copia)
                            if fecha_copia is not None
                            else {
                                "requiere_confirmacion": False,
                                "mensaje": ""
                            }
                        )
                        confirmar_fecha_copia = False

                        if validacion_fecha_copia["requiere_confirmacion"]:

                            st.warning(validacion_fecha_copia["mensaje"])
                            confirmar_fecha_copia = st.checkbox(
                                "Confirmo que quiero guardar esta copia aunque "
                                "esté fuera del periodo de campaña",
                                key=f"dup_cosecha_confirm_fecha_{cosecha_origen_id}"
                            )

                        elif validacion_fecha_copia["mensaje"]:

                            st.info(validacion_fecha_copia["mensaje"])

                        kg_copia = st.number_input(
                            "Cantidad",
                            min_value=0.0,
                            value=max(0.0, _numero(cosecha_origen["kg"])),
                            key=f"dup_cosecha_kg_{cosecha_origen_id}"
                        )
                        if cosecha_tiene_unidad:

                            unidad_copia = st.selectbox(
                                "Unidad",
                                ["kg", "t", "l", "ud"],
                                index=(
                                    ["kg", "t", "l", "ud"].index(
                                        _texto(cosecha_origen["unidad"])
                                    )
                                    if _texto(cosecha_origen["unidad"])
                                    in ["kg", "t", "l", "ud"]
                                    else 0
                                ),
                                key=f"dup_cosecha_unidad_{cosecha_origen_id}",
                            )

                        else:

                            unidad_copia = "kg"
                            st.caption("Unidad: kg")

                        if cosecha_tiene_albaran:

                            albaran_copia = st.text_input(
                                "Albarán",
                                value=_texto(cosecha_origen["albaran"]),
                                key=f"dup_cosecha_albaran_{cosecha_origen_id}"
                            )

                        else:

                            albaran_copia = ""

                        if cosecha_tiene_factura:

                            factura_copia = st.text_input(
                                "Factura",
                                value=_texto(cosecha_origen["factura"]),
                                key=f"dup_cosecha_factura_{cosecha_origen_id}"
                            )

                        else:

                            factura_copia = ""

                        observaciones_copia = st.text_area(
                            "Observaciones",
                            value=_texto(cosecha_origen["observaciones"]),
                            key=f"dup_cosecha_obs_{cosecha_origen_id}"
                        )
                        confirmar_copia = st.checkbox(
                            "Confirmo que quiero crear una copia nueva de este registro",
                            key=f"dup_cosecha_confirm_{cosecha_origen_id}"
                        )
                        crear_copia = st.form_submit_button(
                            "Crear copia como nuevo registro",
                            key=f"dup_cosecha_btn_{cosecha_origen_id}"
                        )

                    if crear_copia:

                        if not confirmar_copia:

                            st.warning(
                                "Marca la confirmación para crear la copia"
                            )

                        elif error_fecha_copia:

                            st.warning("La fecha debe tener formato DD/MM/AAAA")

                        elif fecha_copia is None:

                            st.warning("La fecha es obligatoria")

                        elif (
                            validacion_fecha_copia["requiere_confirmacion"]
                            and not confirmar_fecha_copia
                        ):

                            st.warning(
                                "Marca la confirmación de fecha fuera de campaña"
                            )

                        elif kg_copia <= 0:

                            st.warning("La cantidad debe ser mayor que 0")

                        else:

                            parcelas_copia = leer(
                                """
                                SELECT parcela_id
                                FROM cosecha_parcelas
                                WHERE cosecha_id=?
                                ORDER BY id, parcela_id
                                """,
                                (cosecha_origen_id,)
                            )
                            texto_parcelas_copia = (
                                _texto(cosecha_origen["parcelas"])
                                or _texto(cosecha_resumen["parcelas"])
                            )
                            conn = conectar()

                            try:

                                conn.execute("BEGIN")
                                detalles_copia = []

                                if _tabla_existe_conn(conn, "cosecha_cultivos"):

                                    detalles_copia_df = pd.read_sql_query(
                                        """
                                        SELECT cultivo_id, parcela_id,
                                               superficie, observaciones
                                        FROM cosecha_cultivos
                                        WHERE cosecha_id=?
                                        ORDER BY id
                                        """,
                                        conn,
                                        params=(int(cosecha_origen_id),),
                                    )
                                    detalles_copia = detalles_copia_df.to_dict(
                                        "records"
                                    )

                                nueva_cosecha_id = (
                                    _insertar_cosecha_compatible(
                                        conn,
                                        {
                                            "campana_id": campana_copia,
                                            "fecha": fecha_copia.isoformat(),
                                            "cultivo_id": _entero_o_none(
                                                cosecha_origen["cultivo_id"]
                                            ),
                                            "cultivo": _texto(
                                                cosecha_origen["cultivo"]
                                            ),
                                            "producto": _texto(
                                                cosecha_origen["producto"]
                                            ),
                                            "parcelas": texto_parcelas_copia,
                                            "cantidad": kg_copia,
                                            "unidad": unidad_copia,
                                            "precio": _numero(
                                                cosecha_origen["precio"]
                                            ),
                                            "lote": _texto(
                                                cosecha_origen["lote"]
                                            ),
                                            "cliente_id": _entero_o_none(
                                                cosecha_origen["cliente_id"]
                                            ),
                                            "cliente": _texto(
                                                cosecha_origen["cliente"]
                                            ),
                                            "nif_cliente": _texto(
                                                cosecha_origen["nif_cliente"]
                                            ),
                                            "albaran": albaran_copia.strip(),
                                            "factura": factura_copia.strip(),
                                            "destino": _texto(
                                                cosecha_origen["destino"]
                                            ),
                                            "observaciones": (
                                                observaciones_copia.strip()
                                            ),
                                        },
                                        [
                                            int(parcela["parcela_id"])
                                            for _, parcela
                                            in parcelas_copia.iterrows()
                                        ],
                                        detalles_cultivos=detalles_copia,
                                    )
                                )

                                conn.commit()

                            except Exception as exc:

                                conn.rollback()
                                st.error(
                                    "No se pudo crear la copia de cosecha: "
                                    f"{exc}"
                                )

                            else:

                                st.session_state["duplicar_cosecha_mensaje"] = (
                                    "Copia de cosecha creada como nuevo "
                                    f"registro #{nueva_cosecha_id}"
                                )
                                for clave in claves_duplicar_cosecha:

                                    st.session_state.pop(clave, None)

                                st.rerun()

                            finally:

                                conn.close()


    if seccion_cosecha == "✏️ Editar":

        st.subheader("Edición segura")

        if not cosechas_guardadas.empty:

            with st.expander("Asignar cultivo estructurado"):

                cosechas_por_id_asignar = (
                    cosechas_guardadas
                    .copy()
                    .set_index("id", drop=False)
                )
                ids_asignar = [
                    int(valor)
                    for valor in cosechas_por_id_asignar.index.tolist()
                ]
                cosecha_asignar_id = st.selectbox(
                    "Cosecha",
                    ids_asignar,
                    format_func=lambda valor: (
                        f"#{valor} · "
                        f"{_texto(cosechas_por_id_asignar.loc[valor]['campana'])} · "
                        f"{_texto(cosechas_por_id_asignar.loc[valor]['cultivo_mostrado'])}"
                    ),
                    key="cosecha_asignar_cultivo_id"
                )
                cosecha_asignar = cosechas_por_id_asignar.loc[
                    cosecha_asignar_id
                ]
                cultivo_legacy_actual = _texto(cosecha_asignar["cultivo"])

                if (
                    _entero_o_none(cosecha_asignar["cultivo_id"]) is None
                    and cultivo_legacy_actual
                ):

                    st.caption(
                        "Cultivo legacy actual: "
                        f"{cultivo_legacy_actual}."
                    )

                cultivo_id_asignado = _selector_cultivo_estructurado(
                    cultivos_cosecha,
                    f"cosecha_nuevo_cultivo_id_{cosecha_asignar_id}",
                    campana_id=cosecha_asignar["campana_id"],
                    valor_actual=cosecha_asignar["cultivo_id"],
                )
                cultivo_asignado = _cultivo_por_id(
                    cultivos_cosecha,
                    cultivo_id_asignado,
                )

                if cultivo_asignado is None:

                    if cultivo_legacy_actual:

                        st.info(
                            "La cosecha conserva cultivo legacy. Selecciona "
                            "un cultivo estructurado para actualizarlo o "
                            "guarda sin cultivo para mantener el texto actual."
                        )
                        cultivo_texto_asignado = cultivo_legacy_actual

                    elif cosecha_tiene_cultivo_legacy:

                        cultivo_texto_asignado = st.text_input(
                            "Cultivo textual de compatibilidad",
                            value=cultivo_legacy_actual,
                            key=(
                                "cosecha_cultivo_texto_asignado_"
                                f"{cosecha_asignar_id}"
                            ),
                        )

                    else:

                        cultivo_texto_asignado = ""
                        st.info("Selecciona un cultivo estructurado.")

                else:

                    cultivo_texto_asignado = _nombre_cultivo(cultivo_asignado)
                    st.caption(
                        "Se guardará como cultivo: "
                        f"{cultivo_texto_asignado or 'Sin nombre'}."
                    )

                confirmar_asignacion_cultivo = st.checkbox(
                    "Confirmo que quiero actualizar el cultivo de esta cosecha",
                    key=f"cosecha_confirmar_cultivo_{cosecha_asignar_id}"
                )

                if st.button(
                    "Guardar cultivo estructurado",
                    key=f"cosecha_guardar_cultivo_{cosecha_asignar_id}",
                    type="primary",
                ):

                    if not confirmar_asignacion_cultivo:

                        st.warning("Marca la confirmación antes de guardar")

                    elif (
                        _entero_o_none(cultivo_id_asignado) is None
                        and not _texto(cultivo_texto_asignado)
                    ):

                        st.warning(
                            "Selecciona un cultivo estructurado o indica un "
                            "cultivo textual"
                        )

                    else:

                        conn = conectar()

                        try:

                            _actualizar_cosecha_compatible(
                                conn,
                                int(cosecha_asignar_id),
                                {
                                    "cultivo_id": _entero_o_none(
                                        cultivo_id_asignado
                                    ),
                                    "cultivo": _texto(cultivo_texto_asignado),
                                },
                            )
                            conn.commit()

                        except sqlite3.Error:

                            conn.rollback()
                            raise

                        finally:

                            conn.close()

                        st.success("Cultivo de cosecha actualizado")
                        st.rerun()

            with st.expander("Asignar cliente"):

                cosechas_por_id_cliente = (
                    cosechas_guardadas
                    .copy()
                    .set_index("id", drop=False)
                )
                ids_cliente = [
                    int(valor)
                    for valor in cosechas_por_id_cliente.index.tolist()
                ]
                cosecha_cliente_id = st.selectbox(
                    "Cosecha",
                    ids_cliente,
                    format_func=lambda valor: (
                        f"#{valor} · "
                        f"{_texto(cosechas_por_id_cliente.loc[valor]['campana'])} · "
                        f"{_texto(cosechas_por_id_cliente.loc[valor]['cliente']) or 'Sin cliente'}"
                    ),
                    key="cosecha_asignar_cliente_id"
                )
                cosecha_cliente = cosechas_por_id_cliente.loc[
                    cosecha_cliente_id
                ]
                cliente_legacy_actual = _texto(cosecha_cliente["cliente"])
                nif_legacy_actual = _texto(cosecha_cliente["nif_cliente"])

                if cliente_legacy_actual or nif_legacy_actual:

                    st.caption(
                        "Cliente legacy actual: "
                        + (
                            cliente_legacy_actual
                            if cliente_legacy_actual
                            else "Sin nombre"
                        )
                        + (
                            f" — NIF {nif_legacy_actual}"
                            if nif_legacy_actual
                            else ""
                        )
                        + "."
                    )

                if clientes_edicion_cosecha.empty:

                    st.info(
                        "No hay clientes dados de alta. Puede crear clientes "
                        "en Clientes / Proveedores."
                    )
                    cliente_id_asignado = None

                else:

                    cliente_id_asignado = _selector_cliente(
                        clientes_edicion_cosecha,
                        f"cosecha_nuevo_cliente_id_v610_{cosecha_cliente_id}",
                        valor_actual=cosecha_cliente["cliente_id"],
                    )

                cliente_asignado = _cliente_por_id(
                    clientes_edicion_cosecha,
                    cliente_id_asignado,
                )

                if cliente_asignado is None:

                    if cliente_legacy_actual or nif_legacy_actual:

                        st.info(
                            "La cosecha conserva cliente/NIF legacy. "
                            "Selecciona un cliente para estructurarlo o "
                            "guarda sin cliente para mantener el texto actual."
                        )
                        cliente_texto_asignado = cliente_legacy_actual
                        nif_texto_asignado = nif_legacy_actual

                    elif (
                        cosecha_tiene_cliente_legacy
                        or cosecha_tiene_nif_cliente_legacy
                    ):

                        cliente_texto_asignado = st.text_input(
                            "Cliente / comprador manual",
                            value=cliente_legacy_actual,
                            key=(
                                "cosecha_cliente_texto_asignado_"
                                f"{cosecha_cliente_id}_manual"
                            ),
                        )
                        nif_texto_asignado = st.text_input(
                            "NIF cliente manual",
                            value=nif_legacy_actual,
                            key=(
                                "cosecha_nif_cliente_asignado_"
                                f"{cosecha_cliente_id}_manual"
                            ),
                        )

                    else:

                        cliente_texto_asignado = ""
                        nif_texto_asignado = ""
                        st.info("Selecciona un cliente estructurado.")

                else:

                    cliente_texto_asignado = _texto(
                        cliente_asignado.get("nombre")
                    )
                    nif_texto_asignado = _texto(cliente_asignado.get("nif"))
                    st.caption(
                        "Se guardará como cliente: "
                        + (
                            cliente_texto_asignado
                            if cliente_texto_asignado
                            else "Sin nombre"
                        )
                        + (
                            f" — NIF {nif_texto_asignado}"
                            if nif_texto_asignado
                            else ""
                        )
                        + "."
                    )

                confirmar_asignacion_cliente = st.checkbox(
                    "Confirmo que quiero actualizar el cliente de esta cosecha",
                    key=f"cosecha_confirmar_cliente_{cosecha_cliente_id}"
                )

                if st.button(
                    "Guardar cliente",
                    key=f"cosecha_guardar_cliente_{cosecha_cliente_id}",
                    type="primary",
                ):

                    if not confirmar_asignacion_cliente:

                        st.warning("Marca la confirmación antes de guardar")

                    else:

                        conn = conectar()

                        try:

                            _actualizar_cosecha_compatible(
                                conn,
                                int(cosecha_cliente_id),
                                {
                                    "cliente_id": _entero_o_none(
                                        cliente_id_asignado
                                    ),
                                    "cliente": _texto(cliente_texto_asignado),
                                    "nif_cliente": _texto(nif_texto_asignado),
                                },
                            )
                            conn.commit()

                        except sqlite3.Error:

                            conn.rollback()
                            raise

                        finally:

                            conn.close()

                        st.success("Cliente de cosecha actualizado")
                        st.rerun()

        cosechas_filtradas_editor = mostrar_filtros_dataframe(
            cosechas_guardadas,
            "cosecha_editar",
            columnas_texto=[
                "producto",
                "cultivo_mostrado",
                "parcelas",
                "cliente",
                "nif_cliente",
                "lote",
                "albaran",
                "factura",
                "destino",
                "observaciones"
            ],
            columna_fecha="fecha",
            filtros_select={
                "Campaña": "campana",
                "Cultivo": "cultivo_mostrado",
                "Producto": "producto",
                "Cliente": "cliente"
            }
        )

        if cosechas_filtradas_editor.empty:

            st.info("No hay cosechas registradas")

        else:

            editor_cosechas = cosechas_filtradas_editor.copy()
            columnas_editor_ocultas = [
                "campana_id",
                "cultivo_id",
                "cliente_id",
                "cultivo",
                "cultivo_v6",
                "variedad_v6",
                "sistema_v6",
                "codigo_siex",
                "superficie_cultivo",
                "campana_cultivo",
                "cultivo_estructurado",
                "cultivos_detalle",
                "cultivo_origen",
                "cantidad",
            ]

            if not cosecha_tiene_producto:

                columnas_editor_ocultas.append("producto")

            if not cosecha_tiene_precio:

                columnas_editor_ocultas.extend(["precio", "importe_total"])

            if not cosecha_tiene_lote:

                columnas_editor_ocultas.append("lote")

            if not cosecha_tiene_albaran:

                columnas_editor_ocultas.append("albaran")

            if not cosecha_tiene_factura:

                columnas_editor_ocultas.append("factura")

            if not cosecha_tiene_unidad:

                columnas_editor_ocultas.append("unidad")

            editor_cosechas = editor_cosechas.drop(
                columns=columnas_editor_ocultas,
                errors="ignore"
            )
            editor_cosechas["fecha"] = pd.to_datetime(
                editor_cosechas["fecha"],
                errors="coerce"
            )
            columnas_editor = [
                "id",
                "fecha",
                "campana",
                "cultivo_mostrado",
                "parcelas",
                "superficie_detalle",
            ]

            if cosecha_tiene_producto:

                columnas_editor.append("producto")

            columnas_editor.append("kg")

            if cosecha_tiene_unidad:

                columnas_editor.append("unidad")

            if cosecha_tiene_precio:

                columnas_editor.extend(["precio", "importe_total"])

            if cosecha_tiene_lote:

                columnas_editor.append("lote")

            columnas_editor.append("cliente")

            if cosecha_tiene_nif_cliente_legacy or "cliente_id" in columnas_cosecha:

                columnas_editor.append("nif_cliente")

            if cosecha_tiene_albaran:

                columnas_editor.append("albaran")

            if cosecha_tiene_factura:

                columnas_editor.append("factura")

            columnas_editor.extend(["destino", "observaciones"])

            cosechas_editadas = st.data_editor(
                editor_cosechas,
                num_rows="fixed",
                disabled=[
                    "id",
                    "campana",
                    "cultivo_mostrado",
                    "parcelas",
                    "superficie_detalle",
                    "importe_total",
                    "cliente",
                    "nif_cliente",
                ],
                hide_index=True,
                use_container_width=True,
                column_order=columnas_editor,
                column_config={
                    "id": st.column_config.NumberColumn("id", disabled=True),
                    "fecha": st.column_config.DateColumn(
                        "fecha",
                        format="DD/MM/YYYY",
                        required=True
                    ),
                    "cultivo_mostrado": st.column_config.TextColumn(
                        "cultivo",
                        disabled=True
                    ),
                    "kg": st.column_config.NumberColumn(
                        "cantidad",
                        min_value=0.0,
                    ),
                    "superficie_detalle": st.column_config.NumberColumn(
                        "superficie",
                        disabled=True,
                        format="%.2f ha",
                    ),
                    "unidad": st.column_config.SelectboxColumn(
                        "unidad",
                        options=["kg", "t", "l", "ud"],
                    ),
                    "precio": st.column_config.NumberColumn(
                        "precio €/kg",
                        min_value=0.0,
                        format="%.2f"
                    ),
                    "importe_total": st.column_config.NumberColumn(
                        "importe total",
                        disabled=True,
                        format="%.2f"
                    )
                },
                key="editor_cosechas"
            )

            confirmar_cosechas = st.checkbox(
                "Confirmo que quiero guardar los cambios de cosecha",
                key="confirmar_cosechas"
            )

            if st.button(
                "💾 Guardar cambios de cosecha",
                key="guardar_cambios_cosecha"
            ):

                ids_originales = editor_cosechas["id"].astype(int).tolist()
                ids_editados = cosechas_editadas["id"].astype(int).tolist()

                if not confirmar_cosechas:

                    st.warning("Marca la confirmación antes de guardar")

                elif ids_editados != ids_originales:

                    st.warning("No se permite añadir, borrar ni cambiar registros")

                else:

                    cosechas_para_guardar = cosechas_editadas.copy()

                    columnas_texto_cosecha = [
                        "producto",
                        "lote",
                        "unidad",
                        "albaran",
                        "factura",
                        "destino",
                        "observaciones"
                    ]

                    for columna in columnas_texto_cosecha:

                        if columna in cosechas_para_guardar.columns:

                            cosechas_para_guardar[columna] = (
                                cosechas_para_guardar[columna]
                                .fillna("")
                                .astype(str)
                                .str.strip()
                            )

                    cosechas_para_guardar["kg"] = pd.to_numeric(
                        cosechas_para_guardar["kg"],
                        errors="coerce"
                    )

                    if "precio" in cosechas_para_guardar.columns:

                        cosechas_para_guardar["precio"] = pd.to_numeric(
                            cosechas_para_guardar["precio"],
                            errors="coerce"
                        )

                    cosechas_para_guardar["fecha"] = pd.to_datetime(
                        cosechas_para_guardar["fecha"],
                        errors="coerce"
                    )

                    originales_por_id = editor_cosechas.set_index("id")
                    filas_invalidas = []

                    for _, fila in cosechas_para_guardar.iterrows():

                        original = originales_por_id.loc[int(fila["id"])]
                        producto_original = str(
                            original.get("producto", "") or ""
                        ).strip()
                        kg_original = pd.to_numeric(
                            original["kg"],
                            errors="coerce"
                        )

                        producto_nuevo_invalido = (
                            cosecha_tiene_producto
                            and fila.get("producto", "") == ""
                            and producto_original != ""
                        )
                        if pd.isna(fila["kg"]):

                            kg_nuevo_invalido = not pd.isna(kg_original)

                        elif fila["kg"] <= 0:

                            kg_nuevo_invalido = (
                                pd.isna(kg_original)
                                or kg_original > 0
                                or fila["kg"] != kg_original
                            )

                        else:

                            kg_nuevo_invalido = False

                        precio_original = pd.to_numeric(
                            original.get("precio"),
                            errors="coerce"
                        )

                        if not cosecha_tiene_precio:

                            precio_invalido = False

                        elif pd.isna(fila["precio"]):

                            precio_invalido = not pd.isna(precio_original)

                        elif fila["precio"] < 0:

                            precio_invalido = (
                                pd.isna(precio_original)
                                or precio_original >= 0
                                or fila["precio"] != precio_original
                            )

                        else:

                            precio_invalido = False

                        if (
                            producto_nuevo_invalido
                            or kg_nuevo_invalido
                            or precio_invalido
                            or pd.isna(fila["fecha"])
                        ):

                            filas_invalidas.append(str(int(fila["id"])))

                    if filas_invalidas:

                        st.warning(
                            "Revisa fecha, cantidad y datos económicos en los "
                            "registros: "
                            + ", ".join(filas_invalidas)
                        )

                    else:

                        conn = conectar()

                        try:

                            for _, fila in cosechas_para_guardar.iterrows():

                                precio = fila.get("precio")
                                _actualizar_cosecha_compatible(
                                    conn,
                                    int(fila["id"]),
                                    {
                                        "fecha": (
                                            fila["fecha"]
                                            .date()
                                            .isoformat()
                                        ),
                                        "producto": fila.get("producto", ""),
                                        "cantidad": (
                                            None
                                            if pd.isna(fila["kg"])
                                            else float(fila["kg"])
                                        ),
                                        "unidad": fila.get("unidad", "kg"),
                                        "precio": (
                                            None
                                            if pd.isna(precio)
                                            else float(precio)
                                        ),
                                        "lote": fila.get("lote", ""),
                                        "albaran": fila.get("albaran", ""),
                                        "factura": fila.get("factura", ""),
                                        "destino": fila.get("destino", ""),
                                        "observaciones": fila.get(
                                            "observaciones",
                                            "",
                                        ),
                                    },
                                )

                            conn.commit()

                        except sqlite3.Error:

                            conn.rollback()
                            raise

                        finally:

                            conn.close()

                        st.success("Cambios de cosecha guardados")
                        st.rerun()






    if seccion_cosecha == "🗑️ Borrar":

        st.subheader("Borrado seguro")

        borrar_registros_seguro(
            "cosecha",
            "id",
            cosechas_guardadas,
            "cosechas",
            tablas_hijas=[
                ("cosecha_cultivos", "cosecha_id"),
                ("cosecha_parcelas", "cosecha_id"),
            ],
            campo_descripcion="producto",
            key="cosecha"
        )
