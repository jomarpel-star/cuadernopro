import sqlite3
import pandas as pd
import streamlit as st

from core.borrado import borrar_registros_seguro
from core.actuaciones_multicultivo import (
    agregar_detalles as _agregar_detalles_actuacion,
    detalles_registro as _detalles_actuacion_registro,
    insertar_detalles as _insertar_detalles_actuacion,
    normalizar_detalles as _normalizar_detalles_actuacion,
    parcelas_compatibilidad as _parcelas_compatibilidad_detalles,
)
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


def _anadir_si_existe(destino, columnas, columna, valor):

    if columna in columnas:

        destino[columna] = valor


def _insertar_relaciones_fertilizacion_parcelas(
    conn,
    fertilizacion_id,
    parcelas_ids,
):

    if not _tabla_existe_conn(conn, "fertilizacion_parcelas"):

        return

    columnas = _columnas_tabla_conn(conn, "fertilizacion_parcelas")

    if not {"fertilizacion_id", "parcela_id"}.issubset(columnas):

        return

    for parcela in parcelas_ids or []:

        if isinstance(parcela, dict):

            parcela_id = parcela.get("parcela_id")
            superficie = parcela.get("superficie")

        else:

            parcela_id = parcela
            superficie = None

        valores = {
            "fertilizacion_id": int(fertilizacion_id),
            "parcela_id": int(parcela_id),
        }
        _anadir_si_existe(valores, columnas, "superficie", superficie)
        nombres = list(valores)
        conn.execute(
            f"""
            INSERT INTO fertilizacion_parcelas
            ({','.join(nombres)})
            VALUES ({','.join(['?'] * len(nombres))})
            """,
            [valores[columna] for columna in nombres],
        )


def _insertar_fertilizacion_compatible(
    conn,
    datos,
    parcelas_ids=None,
    detalles_cultivos=None,
):

    columnas = _columnas_tabla_conn(conn, "fertilizaciones")
    valores = {}
    detalles_normalizados = _normalizar_detalles_actuacion(detalles_cultivos)
    tipo = _texto(datos.get("tipo_fertilizante") or datos.get("tipo"))
    unidad = _texto(datos.get("unidad"))

    _anadir_si_existe(valores, columnas, "campana_id", datos.get("campana_id"))
    _anadir_si_existe(valores, columnas, "cultivo_id", datos.get("cultivo_id"))
    _anadir_si_existe(valores, columnas, "fecha", datos.get("fecha"))
    _anadir_si_existe(valores, columnas, "producto", _texto(datos.get("producto")))
    _anadir_si_existe(valores, columnas, "tipo_fertilizante", tipo)
    _anadir_si_existe(valores, columnas, "tipo", tipo)
    _anadir_si_existe(valores, columnas, "cantidad", datos.get("cantidad"))
    _anadir_si_existe(valores, columnas, "unidad", unidad)
    _anadir_si_existe(
        valores,
        columnas,
        "unidad_normalizada",
        _texto(datos.get("unidad_normalizada") or unidad.lower()),
    )
    _anadir_si_existe(valores, columnas, "superficie", datos.get("superficie"))
    _anadir_si_existe(
        valores,
        columnas,
        "codigo_actuacion_siex",
        _texto(datos.get("codigo_actuacion_siex")),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "observaciones",
        _texto(datos.get("observaciones")),
    )
    _anadir_si_existe(valores, columnas, "cultivo", _texto(datos.get("cultivo")))
    _anadir_si_existe(
        valores,
        columnas,
        "riqueza_npk",
        _texto(datos.get("riqueza_npk")),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "metodo_aplicacion",
        _texto(datos.get("metodo_aplicacion")),
    )
    _anadir_si_existe(valores, columnas, "operario_id", datos.get("operario_id"))

    if not valores:

        raise sqlite3.OperationalError(
            "La tabla fertilizaciones no tiene columnas utiles"
        )

    nombres = list(valores)
    cursor = conn.execute(
        f"""
        INSERT INTO fertilizaciones
        ({','.join(nombres)})
        VALUES ({','.join(['?'] * len(nombres))})
        """,
        [valores[columna] for columna in nombres],
    )
    fertilizacion_id = cursor.lastrowid
    parcelas_compatibles = (
        parcelas_ids
        if parcelas_ids is not None
        else _parcelas_compatibilidad_detalles(detalles_normalizados)
    )
    _insertar_relaciones_fertilizacion_parcelas(
        conn,
        fertilizacion_id,
        parcelas_compatibles,
    )
    _insertar_detalles_actuacion(
        conn,
        "fertilizacion_cultivos",
        "fertilizacion_id",
        fertilizacion_id,
        detalles_normalizados,
    )
    return fertilizacion_id


def _actualizar_fertilizacion_compatible(conn, fertilizacion_id, datos):

    columnas = _columnas_tabla_conn(conn, "fertilizaciones")
    valores = {}
    tipo = _texto(datos.get("tipo_fertilizante") or datos.get("tipo"))

    for columna in (
        "campana_id",
        "cultivo_id",
        "fecha",
        "producto",
        "cantidad",
        "unidad",
        "unidad_normalizada",
        "superficie",
        "codigo_actuacion_siex",
        "observaciones",
        "cultivo",
        "riqueza_npk",
        "metodo_aplicacion",
        "operario_id",
    ):

        if columna in columnas and columna in datos:

            valores[columna] = datos[columna]

    if "tipo_fertilizante" in columnas and (
        "tipo_fertilizante" in datos or "tipo" in datos
    ):

        valores["tipo_fertilizante"] = tipo

    if "tipo" in columnas and ("tipo_fertilizante" in datos or "tipo" in datos):

        valores["tipo"] = tipo

    if not valores:

        return

    asignaciones = ",".join(f"{columna}=?" for columna in valores)
    conn.execute(
        f"UPDATE fertilizaciones SET {asignaciones} WHERE id=?",
        [valores[columna] for columna in valores] + [int(fertilizacion_id)],
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


def _etiqueta_cultivo(fila):

    if fila is None:

        return "Sin cultivo estructurado"

    campana = _texto(fila.get("campana_cultivo") or fila.get("campana"))
    nombre = _nombre_cultivo(fila) or "Sin nombre"
    superficie = _formatear_hectareas(
        fila.get("superficie")
        if not _texto(fila.get("superficie_cultivo"))
        else fila.get("superficie_cultivo")
    )
    ano_plantacion = _entero_o_none(fila.get("ano_plantacion"))
    codigo_siex = _texto(fila.get("codigo_siex"))
    partes = []

    if campana:

        partes.append(f"Campaña {campana}")

    partes.append(nombre.upper())

    if superficie:

        partes.append(superficie)

    if ano_plantacion is not None:

        partes.append(f"Plant. {ano_plantacion}")

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
                parcelas.superficie_sigpac
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
                parcelas.superficie_sigpac
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


def _sumar_superficie_parcelas(parcelas):

    if parcelas.empty or "superficie_sigpac" not in parcelas.columns:

        return 0.0

    return float(
        pd.to_numeric(parcelas["superficie_sigpac"], errors="coerce")
        .fillna(0)
        .sum()
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


def _coalesce_sql(expresiones):

    return "COALESCE(" + ",".join(expresiones) + ")"


def _leer_fertilizaciones_guardadas(conn=None, fertilizacion_id=None):

    if conn is not None:

        fertilizacion_cols = _columnas_tabla_conn(conn, "fertilizaciones")
        cultivos_cols = _columnas_tabla_conn(conn, "cultivos")
        tiene_fertilizacion_parcelas = _tabla_existe_conn(
            conn,
            "fertilizacion_parcelas",
        )
        tiene_parcelas = _tabla_existe_conn(conn, "parcelas")

    else:

        conn_tmp = conectar()

        try:

            fertilizacion_cols = _columnas_tabla_conn(
                conn_tmp,
                "fertilizaciones",
            )
            cultivos_cols = _columnas_tabla_conn(conn_tmp, "cultivos")
            tiene_fertilizacion_parcelas = _tabla_existe_conn(
                conn_tmp,
                "fertilizacion_parcelas",
            )
            tiene_parcelas = _tabla_existe_conn(conn_tmp, "parcelas")

        finally:

            conn_tmp.close()

    if not fertilizacion_cols:

        return pd.DataFrame()

    expr_fecha = _valor_texto_columna(
        "fertilizaciones",
        "fecha",
        fertilizacion_cols,
    )
    expr_campana_id = _valor_numerico_columna(
        "fertilizaciones",
        "campana_id",
        fertilizacion_cols,
    )
    expr_cultivo_id = _valor_numerico_columna(
        "fertilizaciones",
        "cultivo_id",
        fertilizacion_cols,
    )
    expr_cultivo_legacy = _valor_texto_columna(
        "fertilizaciones",
        "cultivo",
        fertilizacion_cols,
    )
    expr_producto = _valor_texto_columna(
        "fertilizaciones",
        "producto",
        fertilizacion_cols,
    )

    tipo_exprs = []

    if "tipo_fertilizante" in fertilizacion_cols:

        tipo_exprs.append("fertilizaciones.tipo_fertilizante")

    if "tipo" in fertilizacion_cols:

        tipo_exprs.append("fertilizaciones.tipo")

    tipo_exprs.append("''")
    expr_tipo = _coalesce_sql(tipo_exprs)
    expr_riqueza = _valor_texto_columna(
        "fertilizaciones",
        "riqueza_npk",
        fertilizacion_cols,
    )
    expr_cantidad = _valor_numerico_columna(
        "fertilizaciones",
        "cantidad",
        fertilizacion_cols,
    )
    expr_unidad = _valor_texto_columna(
        "fertilizaciones",
        "unidad",
        fertilizacion_cols,
    )
    expr_unidad_normalizada = _valor_texto_columna(
        "fertilizaciones",
        "unidad_normalizada",
        fertilizacion_cols,
    )
    expr_metodo = _valor_texto_columna(
        "fertilizaciones",
        "metodo_aplicacion",
        fertilizacion_cols,
    )
    expr_superficie = _valor_numerico_columna(
        "fertilizaciones",
        "superficie",
        fertilizacion_cols,
    )
    expr_codigo = _valor_texto_columna(
        "fertilizaciones",
        "codigo_actuacion_siex",
        fertilizacion_cols,
    )
    expr_operario_id = _valor_numerico_columna(
        "fertilizaciones",
        "operario_id",
        fertilizacion_cols,
    )
    expr_observaciones = _valor_texto_columna(
        "fertilizaciones",
        "observaciones",
        fertilizacion_cols,
    )
    expr_nombre_cultivo = _expr_nombre_cultivo(cultivos_cols)
    expr_variedad = _expr_variedad_cultivo(cultivos_cols)
    expr_sistema = _expr_sistema_cultivo(cultivos_cols)
    expr_codigo_siex = _expr_codigo_siex_cultivo(cultivos_cols)
    expr_superficie_cultivo = _expr_superficie_cultivo(cultivos_cols)
    expr_ano_plantacion = _valor_numerico_columna(
        "cultivos",
        "ano_plantacion",
        cultivos_cols,
    )

    if tiene_fertilizacion_parcelas and tiene_parcelas:

        expr_parcelas = """
            COALESCE(
                GROUP_CONCAT(
                    CASE
                        WHEN IFNULL(parcelas.nombre,'') != ''
                        THEN parcelas.nombre
                        ELSE parcelas.poligono || '-' ||
                             parcelas.parcela || '-' || parcelas.recinto
                    END,
                    ', '
                ),
                ''
            )
        """

    else:

        expr_parcelas = "''"

    joins = [
        "LEFT JOIN campanas ON campanas.id = fertilizaciones.campana_id",
        "LEFT JOIN cultivos ON cultivos.id = fertilizaciones.cultivo_id",
        """
        LEFT JOIN campanas AS campanas_cultivo
        ON campanas_cultivo.id = cultivos.campana_id
        """,
    ]

    if tiene_fertilizacion_parcelas and tiene_parcelas:

        joins.extend(
            [
                """
                LEFT JOIN fertilizacion_parcelas
                ON fertilizacion_parcelas.fertilizacion_id =
                   fertilizaciones.id
                """,
                "LEFT JOIN parcelas ON parcelas.id = fertilizacion_parcelas.parcela_id",
            ]
        )

    if "operario_id" in fertilizacion_cols:

        joins.append("LEFT JOIN personas ON personas.id = fertilizaciones.operario_id")
        expr_operario = "COALESCE(personas.nombre,'')"

    else:

        expr_operario = "''"

    where = ""
    params = ()

    if fertilizacion_id is not None:

        where = "WHERE fertilizaciones.id=?"
        params = (int(fertilizacion_id),)

    sql = f"""
        SELECT
        fertilizaciones.id,
        {expr_campana_id} AS campana_id,
        {expr_cultivo_id} AS cultivo_id,
        {expr_fecha} AS fecha,
        COALESCE(campanas.nombre,'') AS campana,
        {expr_cultivo_legacy} AS cultivo,
        {expr_nombre_cultivo} AS cultivo_v6,
        {expr_variedad} AS variedad_v6,
        {expr_sistema} AS sistema_v6,
        {expr_codigo_siex} AS codigo_siex,
        {expr_superficie_cultivo} AS superficie_cultivo,
        {expr_ano_plantacion} AS ano_plantacion,
        COALESCE(campanas_cultivo.nombre,'') AS campana_cultivo,
        {expr_parcelas} AS parcelas,
        {expr_producto} AS producto,
        {expr_tipo} AS tipo,
        {expr_riqueza} AS riqueza_npk,
        {expr_cantidad} AS cantidad,
        {expr_unidad} AS unidad,
        {expr_unidad_normalizada} AS unidad_normalizada,
        {expr_metodo} AS metodo_aplicacion,
        {expr_superficie} AS superficie,
        {expr_codigo} AS codigo_actuacion_siex,
        {expr_operario_id} AS operario_id,
        {expr_operario} AS operario,
        {expr_observaciones} AS observaciones
        FROM fertilizaciones
        {" ".join(joins)}
        {where}
        GROUP BY fertilizaciones.id
        ORDER BY fertilizaciones.fecha DESC, fertilizaciones.id DESC
    """

    fertilizaciones = _leer_dataframe(sql, params, conn=conn)

    if fertilizaciones.empty:

        return fertilizaciones

    if conn is not None:

        fertilizaciones = _agregar_detalles_actuacion(
            fertilizaciones,
            conn,
            "fertilizacion_cultivos",
            "fertilizacion_id",
        )

    else:

        conn_detalles = conectar()

        try:

            fertilizaciones = _agregar_detalles_actuacion(
                fertilizaciones,
                conn_detalles,
                "fertilizacion_cultivos",
                "fertilizacion_id",
            )

        finally:

            conn_detalles.close()

    tiene_detalle = fertilizaciones["tiene_detalle_multicultivo"].fillna(False)
    fertilizaciones["parcelas"] = fertilizaciones["parcelas_detalle"].where(
        tiene_detalle & (fertilizaciones["parcelas_detalle"].astype(str) != ""),
        fertilizaciones["parcelas"],
    )
    return fertilizaciones


def _preparar_fertilizaciones_presentacion(fertilizaciones_guardadas):

    if not fertilizaciones_guardadas.empty:

        fertilizaciones_guardadas = fertilizaciones_guardadas.copy()
        fertilizaciones_guardadas["cultivo_estructurado"] = (
            fertilizaciones_guardadas.apply(
                lambda fila: (
                    _etiqueta_cultivo(fila)
                    if _entero_o_none(fila.get("cultivo_id")) is not None
                    else ""
                ),
                axis=1,
            )
        )
        fertilizaciones_guardadas["cultivo_mostrado"] = (
            fertilizaciones_guardadas["cultivos_detalle"].where(
                fertilizaciones_guardadas["tiene_detalle_multicultivo"].fillna(False)
                & (fertilizaciones_guardadas["cultivos_detalle"].astype(str) != ""),
                fertilizaciones_guardadas["cultivo_estructurado"].where(
                    fertilizaciones_guardadas["cultivo_estructurado"] != "",
                    fertilizaciones_guardadas["cultivo"].fillna("").astype(str),
                ),
            )
        )
        fertilizaciones_guardadas["cultivo_origen"] = (
            fertilizaciones_guardadas.apply(
                lambda fila: (
                    "detalle"
                    if bool(fila.get("tiene_detalle_multicultivo"))
                    else (
                        "cultivo_id"
                        if _entero_o_none(fila.get("cultivo_id")) is not None
                        else "texto"
                    )
                ),
                axis=1,
            )
        )
        return fertilizaciones_guardadas

    fertilizaciones_guardadas["cultivo_estructurado"] = ""
    fertilizaciones_guardadas["cultivo_mostrado"] = ""
    fertilizaciones_guardadas["cultivo_origen"] = ""
    fertilizaciones_guardadas["cultivos_detalle"] = ""
    fertilizaciones_guardadas["parcelas_detalle"] = ""
    fertilizaciones_guardadas["superficie_detalle"] = 0.0
    fertilizaciones_guardadas["tiene_detalle_multicultivo"] = False
    return fertilizaciones_guardadas


def _leer_ids_parcelas_fertilizacion(fertilizacion_id):

    if not _columnas_tabla("fertilizacion_parcelas"):

        return pd.DataFrame(columns=["parcela_id"])

    return leer(
        """
        SELECT parcela_id
        FROM fertilizacion_parcelas
        WHERE fertilizacion_id=?
        ORDER BY id, parcela_id
        """,
        (fertilizacion_id,),
    )


def render(CAMPANA):

    st.title("🌱 Fertilización")

    opciones_fertilizacion = [
        "📋 Listado",
        "➕ Nueva fertilización",
        "🔁 Duplicar",
        "✏️ Editar",
        "🗑️ Borrar",
    ]
    seccion_fertilizacion = st.radio(
        "Opciones de fertilización",
        opciones_fertilizacion,
        horizontal=True,
        key="fertilizacion_seccion"
    )

    cultivos_fertilizacion = _leer_cultivos_v6()
    parcelas_cultivos_v6, parcelas_cultivos_legacy = _leer_parcelas_cultivos()
    parcelas_disponibles = _leer_parcelas_disponibles()

    personas_fertilizacion = leer(
        "SELECT id,nombre FROM personas ORDER BY nombre"
    )
    columnas_fertilizaciones = _columnas_tabla("fertilizaciones")
    fertilizacion_tiene_cultivo_legacy = "cultivo" in columnas_fertilizaciones
    fertilizacion_tiene_riqueza = "riqueza_npk" in columnas_fertilizaciones
    fertilizacion_tiene_metodo = (
        "metodo_aplicacion" in columnas_fertilizaciones
    )
    fertilizacion_tiene_operario = "operario_id" in columnas_fertilizaciones
    fertilizacion_tiene_codigo_siex = (
        "codigo_actuacion_siex" in columnas_fertilizaciones
    )
    fertilizacion_tiene_unidad_normalizada = (
        "unidad_normalizada" in columnas_fertilizaciones
    )


    if seccion_fertilizacion == "➕ Nueva fertilización":

        if "form_fertilizacion_version" not in st.session_state:

            st.session_state["form_fertilizacion_version"] = 0

        form_fertilizacion_version = (
            st.session_state["form_fertilizacion_version"]
        )

        if cultivos_fertilizacion.empty:

            if fertilizacion_tiene_cultivo_legacy:

                st.info(
                    "No hay cultivos estructurados disponibles. Puede "
                    "registrar una fertilización con cultivo textual para "
                    "mantener compatibilidad."
                )

            else:

                st.info(
                    "No hay cultivos estructurados disponibles. Crea un "
                    "cultivo antes de registrar fertilización."
                )

        cultivos_ordenados = cultivos_fertilizacion.copy()
        cultivos_ordenados["prioridad_campana"] = (
            pd.to_numeric(
                cultivos_ordenados["campana_id"],
                errors="coerce",
            ) != int(CAMPANA)
        ).astype(int)
        cultivos_ordenados = cultivos_ordenados.sort_values(
            by=["prioridad_campana", "campana", "cultivo_texto", "id"]
        )
        ids_cultivos_fertilizacion = (
            cultivos_ordenados["id"].dropna().astype(int).tolist()
        )
        cultivos_ids_fertilizacion = st.multiselect(
            "Cultivos fertilizados",
            ids_cultivos_fertilizacion,
            default=(
                [ids_cultivos_fertilizacion[0]]
                if ids_cultivos_fertilizacion
                else []
            ),
            format_func=lambda valor: _etiqueta_cultivo(
                _cultivo_por_id(cultivos_fertilizacion, valor)
            ),
            key=f"cultivos_fertilizacion_{form_fertilizacion_version}",
        )
        cultivo_id_fertilizacion = (
            int(cultivos_ids_fertilizacion[0])
            if cultivos_ids_fertilizacion
            else None
        )
        cultivo_seleccionado = _cultivo_por_id(
            cultivos_fertilizacion,
            cultivo_id_fertilizacion,
        )
        cultivo_fertilizacion = (
            _nombre_cultivo(cultivo_seleccionado)
            if cultivo_seleccionado is not None
            else ""
        )
        detalles_fertilizacion = []
        parcelas_fertilizacion_sel = []
        parcelas_sin_superficie = False

        for cultivo_id_detalle in cultivos_ids_fertilizacion:

            cultivo_detalle = _cultivo_por_id(
                cultivos_fertilizacion,
                cultivo_id_detalle,
            )
            parcelas_cultivo = _parcelas_para_cultivo(
                cultivo_id_detalle,
                parcelas_cultivos_v6,
                parcelas_cultivos_legacy,
            )
            etiqueta_cultivo = _etiqueta_cultivo(cultivo_detalle)

            if parcelas_cultivo.empty:

                st.info(
                    "El cultivo seleccionado no tiene parcelas asociadas: "
                    f"{etiqueta_cultivo}."
                )
                continue

            etiquetas_parcelas = {
                int(fila["parcela_id"]): _texto_parcela(fila)
                for _, fila in parcelas_cultivo.iterrows()
            }
            opciones_parcelas = _ids_parcelas(parcelas_cultivo)
            parcelas_cultivo_sel = st.multiselect(
                f"Parcelas fertilizadas de {etiqueta_cultivo}",
                opciones_parcelas,
                default=opciones_parcelas,
                format_func=lambda valor: etiquetas_parcelas.get(
                    int(valor),
                    str(valor),
                ),
                key=(
                    f"parcelas_fertilizacion_{form_fertilizacion_version}_"
                    f"{int(cultivo_id_detalle)}"
                ),
            )
            parcelas_fertilizacion_sel.extend(
                int(valor) for valor in parcelas_cultivo_sel
            )
            parcelas_detalle = parcelas_cultivo[
                parcelas_cultivo["parcela_id"]
                .astype(int)
                .isin([int(valor) for valor in parcelas_cultivo_sel])
            ].copy()

            for _, parcela_detalle in parcelas_detalle.iterrows():

                superficie = pd.to_numeric(
                    parcela_detalle.get("superficie"),
                    errors="coerce",
                )

                if pd.isna(superficie) or float(superficie) <= 0:

                    superficie = pd.to_numeric(
                        parcela_detalle.get("superficie_sigpac"),
                        errors="coerce",
                    )

                if pd.isna(superficie):

                    parcelas_sin_superficie = True
                    superficie = None

                detalles_fertilizacion.append(
                    {
                        "cultivo_id": int(cultivo_id_detalle),
                        "parcela_id": int(parcela_detalle["parcela_id"]),
                        "superficie": superficie,
                    }
                )

        detalles_fertilizacion = _normalizar_detalles_actuacion(
            detalles_fertilizacion
        )
        superficie_sugerida = float(
            sum(
                float(detalle["superficie"] or 0)
                for detalle in detalles_fertilizacion
            )
        )
        clave_superficie = (
            f"fertilizacion_superficie_{form_fertilizacion_version}_"
            + (
                "_".join(
                    f"{detalle['cultivo_id']}-{detalle['parcela_id']}"
                    for detalle in detalles_fertilizacion
                )
                if detalles_fertilizacion
                else "sin_parcelas"
            )
        )
        st.info(f"Superficie seleccionada: {superficie_sugerida:.2f} ha")

        if parcelas_sin_superficie:

            st.warning("Hay parcelas seleccionadas sin superficie informada.")

        with st.form(f"nueva_fertilizacion_v{form_fertilizacion_version}"):

            fecha_fertilizacion_texto = st.text_input(
                "Fecha",
                value=formatear_fecha_es(pd.Timestamp.today()),
                placeholder="DD/MM/AAAA",
                key=f"fertilizacion_fecha_{form_fertilizacion_version}"
            )

            error_formato_fecha_fertilizacion = False

            try:

                fecha_fertilizacion_iso = parsear_fecha_es(
                    fecha_fertilizacion_texto
                )
                fecha_fertilizacion = pd.to_datetime(
                    fecha_fertilizacion_iso,
                    errors="coerce"
                ).date() if fecha_fertilizacion_iso else None

            except ValueError:

                error_formato_fecha_fertilizacion = True
                fecha_fertilizacion = None

            validacion_fecha_fertilizacion = (
                validar_fecha_en_campana(CAMPANA, fecha_fertilizacion)
                if fecha_fertilizacion is not None
                else {
                    "requiere_confirmacion": False,
                    "mensaje": ""
                }
            )
            confirmar_fecha_fertilizacion = False

            if validacion_fecha_fertilizacion["requiere_confirmacion"]:

                st.warning(validacion_fecha_fertilizacion["mensaje"])
                confirmar_fecha_fertilizacion = st.checkbox(
                    "Confirmo que quiero guardar este registro aunque esté "
                    "fuera del periodo de campaña",
                    key=(
                        "confirmar_fecha_fuera_fertilizacion_"
                        f"{form_fertilizacion_version}"
                    )
                )

            elif validacion_fecha_fertilizacion["mensaje"]:

                st.info(validacion_fecha_fertilizacion["mensaje"])

            producto_fertilizacion = st.text_input(
                "Producto fertilizante",
                key=f"fertilizacion_producto_{form_fertilizacion_version}"
            )

            tipo_fertilizacion = st.selectbox(
                "Tipo",
                ["Orgánico", "Mineral", "Foliar", "Otro"],
                key=f"fertilizacion_tipo_{form_fertilizacion_version}"
            )

            if fertilizacion_tiene_codigo_siex:

                codigo_actuacion_siex = st.text_input(
                    "Código actuación SIEX",
                    key=f"fertilizacion_codigo_siex_{form_fertilizacion_version}",
                )

            else:

                codigo_actuacion_siex = ""

            if fertilizacion_tiene_riqueza:

                riqueza_npk = st.text_input(
                    "Riqueza NPK",
                    key=f"fertilizacion_riqueza_{form_fertilizacion_version}"
                )

            else:

                riqueza_npk = ""

            cantidad_fertilizacion = st.number_input(
                "Cantidad",
                min_value=0.0,
                value=0.0,
                key=f"fertilizacion_cantidad_{form_fertilizacion_version}"
            )

            unidad_fertilizacion = st.selectbox(
                "Unidad",
                ["kg", "litros"],
                key=f"fertilizacion_unidad_{form_fertilizacion_version}"
            )

            if fertilizacion_tiene_metodo:

                metodo_fertilizacion = st.text_input(
                    "Método de aplicación",
                    key=f"fertilizacion_metodo_{form_fertilizacion_version}"
                )

            else:

                metodo_fertilizacion = ""

            superficie_fertilizacion = st.number_input(
                "Superficie",
                min_value=0.0,
                value=max(0.0, float(superficie_sugerida)),
                key=clave_superficie
            )

            operario_fertilizacion = None

            if not fertilizacion_tiene_operario:

                operario_fertilizacion = None

            elif personas_fertilizacion.empty:

                st.info("No hay personas registradas para seleccionar operario")

            else:

                operario_fertilizacion = st.selectbox(
                    "Operario",
                    [None] + personas_fertilizacion.id.tolist(),
                    format_func=lambda x: (
                        "Sin operario"
                        if x is None
                        else personas_fertilizacion[
                            personas_fertilizacion.id == x
                        ].nombre.values[0]
                    ),
                    key=f"fertilizacion_operario_{form_fertilizacion_version}"
                )

            observaciones_fertilizacion = st.text_area(
                "Observaciones",
                key=f"fertilizacion_observaciones_{form_fertilizacion_version}"
            )

            guardar_fertilizacion = st.form_submit_button(
                "Registrar fertilización"
            )

        if guardar_fertilizacion:

            if (
                error_formato_fecha_fertilizacion
            ):

                st.warning("La fecha debe tener formato DD/MM/AAAA")

            elif fecha_fertilizacion is None:

                st.warning("La fecha es obligatoria")

            elif (
                validacion_fecha_fertilizacion["requiere_confirmacion"]
                and not confirmar_fecha_fertilizacion
            ):

                st.warning(
                    "Marca la confirmación para guardar la fertilización"
                )

            elif not cultivos_ids_fertilizacion:

                st.warning("Selecciona al menos un cultivo")

            elif not detalles_fertilizacion:

                st.warning("Selecciona al menos una parcela fertilizada")

            elif not producto_fertilizacion.strip():

                st.warning("Indica el producto fertilizante")

            else:

                conn = conectar()
                try:

                    _insertar_fertilizacion_compatible(
                        conn,
                        {
                            "campana_id": CAMPANA,
                            "fecha": fecha_fertilizacion.isoformat(),
                            "cultivo_id": _entero_o_none(
                                cultivo_id_fertilizacion
                            ),
                            "cultivo": _texto(cultivo_fertilizacion),
                            "producto": producto_fertilizacion.strip(),
                            "tipo_fertilizante": tipo_fertilizacion,
                            "riqueza_npk": riqueza_npk.strip(),
                            "cantidad": cantidad_fertilizacion,
                            "unidad": unidad_fertilizacion,
                            "unidad_normalizada": unidad_fertilizacion.lower(),
                            "metodo_aplicacion": metodo_fertilizacion.strip(),
                            "superficie": superficie_fertilizacion,
                            "codigo_actuacion_siex": (
                                codigo_actuacion_siex.strip()
                            ),
                            "operario_id": operario_fertilizacion,
                            "observaciones": (
                                observaciones_fertilizacion.strip()
                            ),
                        },
                        _parcelas_compatibilidad_detalles(
                            detalles_fertilizacion
                        ),
                        detalles_cultivos=detalles_fertilizacion,
                    )

                    conn.commit()

                except sqlite3.Error:

                    conn.rollback()
                    raise

                finally:

                    conn.close()

                st.success("Fertilización registrada")
                st.session_state["form_fertilizacion_version"] += 1
                st.rerun()

    fertilizaciones_guardadas = _preparar_fertilizaciones_presentacion(
        _leer_fertilizaciones_guardadas()
    )


    if seccion_fertilizacion == "📋 Listado":

        fertilizaciones_filtradas = mostrar_filtros_dataframe(
            fertilizaciones_guardadas,
            "fertilizacion_listado",
            columnas_texto=[
                "producto",
                "cultivo_mostrado",
                "parcelas",
                "observaciones"
            ],
            columna_fecha="fecha",
            filtros_select={
                "Campaña": "campana",
                "Cultivo": "cultivo_mostrado",
                "Producto": "producto",
                "Tipo": "tipo"
            }
        )
        columnas_ocultas = [
            "campana_id",
            "cultivo_id",
            "operario_id",
            "cultivo",
            "cultivo_origen",
            "cultivo_v6",
            "variedad_v6",
            "sistema_v6",
            "codigo_siex",
            "superficie_cultivo",
            "ano_plantacion",
            "campana_cultivo",
            "cultivo_estructurado",
            "unidad_normalizada",
            "cultivos_detalle",
            "parcelas_detalle",
            "superficie_detalle",
            "tiene_detalle_multicultivo",
        ]
        columnas_listado = [
            "id",
            "campana",
            "fecha",
            "cultivo_mostrado",
            "parcelas",
            "producto",
            "tipo",
        ]

        if fertilizacion_tiene_codigo_siex:

            columnas_listado.append("codigo_actuacion_siex")

        if fertilizacion_tiene_riqueza:

            columnas_listado.append("riqueza_npk")

        columnas_listado.extend(["cantidad", "unidad"])

        if fertilizacion_tiene_metodo:

            columnas_listado.append("metodo_aplicacion")

        columnas_listado.append("superficie")

        if fertilizacion_tiene_operario:

            columnas_listado.append("operario")

        columnas_listado.append("observaciones")
        fertilizaciones_visual = preparar_dataframe_visual(
            preparar_columnas_fecha_tabla(
                fertilizaciones_filtradas.drop(
                    columns=columnas_ocultas,
                    errors="ignore"
                ),
                ["fecha"]
            ),
            columnas=columnas_listado,
            ocultar_tecnicas=True,
            etiquetas_extra={
                "cultivo_mostrado": "Cultivo",
                "codigo_actuacion_siex": "Código actuación SIEX",
                "riqueza_npk": "Riqueza NPK",
                "metodo_aplicacion": "Método aplicación",
                "operario": "Operario",
            },
        )
        st.dataframe(
            fertilizaciones_visual,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Fecha": st.column_config.DateColumn(
                    "Fecha",
                    format="DD/MM/YYYY"
                ),
            }
        )


    if seccion_fertilizacion == "🔁 Duplicar":

        mensaje_duplicacion_fertilizacion = st.session_state.pop(
            "duplicar_fertilizacion_mensaje",
            None
        )

        if mensaje_duplicacion_fertilizacion:

            st.success(mensaje_duplicacion_fertilizacion)

        with st.expander("Duplicar registro existente"):

            if fertilizaciones_guardadas.empty:

                st.info("No hay fertilizaciones para duplicar")

            else:

                fertilizaciones_por_id = (
                    fertilizaciones_guardadas
                    .copy()
                    .set_index("id", drop=False)
                )
                ids_fertilizaciones = [
                    int(valor)
                    for valor in fertilizaciones_por_id.index.tolist()
                ]

                def formato_fertilizacion_origen(fertilizacion_id):

                    fila = fertilizaciones_por_id.loc[fertilizacion_id]
                    fecha = formatear_fecha_es(fila["fecha"])
                    producto = _texto(fila["producto"])
                    cultivo = _texto(fila["cultivo_mostrado"])

                    return f"#{fertilizacion_id} · {fecha} · {producto} · {cultivo}"

                fertilizacion_origen_id = st.selectbox(
                    "Fertilización a duplicar",
                    ids_fertilizaciones,
                    format_func=formato_fertilizacion_origen,
                    key="dup_fert_origen_id"
                )
                claves_duplicar_fertilizacion = [
                    f"dup_fert_fecha_{fertilizacion_origen_id}",
                    f"dup_fert_producto_{fertilizacion_origen_id}",
                    f"dup_fert_cantidad_{fertilizacion_origen_id}",
                    f"dup_fert_obs_{fertilizacion_origen_id}",
                    f"dup_fert_confirm_fecha_{fertilizacion_origen_id}",
                    f"dup_fert_confirm_{fertilizacion_origen_id}",
                    f"dup_fert_btn_{fertilizacion_origen_id}"
                ]

                if (
                    st.session_state.get("dup_fert_origen_id_anterior")
                    != fertilizacion_origen_id
                ):

                    for clave in claves_duplicar_fertilizacion:

                        st.session_state.pop(clave, None)

                    st.session_state["dup_fert_origen_id_anterior"] = (
                        fertilizacion_origen_id
                    )

                fertilizacion_origen = fertilizaciones_por_id.loc[
                    fertilizacion_origen_id
                ]

                st.write(
                    "Origen: "
                    f"campaña {_texto(fertilizacion_origen['campana'])} · "
                    f"cultivo {_texto(fertilizacion_origen['cultivo_mostrado'])} · "
                    f"parcelas {_texto(fertilizacion_origen['parcelas']) or 'Sin parcelas'} · "
                    f"tipo {_texto(fertilizacion_origen['tipo'])}"
                )

                with st.form(
                    f"dup_fert_form_{fertilizacion_origen_id}"
                ):

                    fecha_copia_texto = st.text_input(
                        "Fecha",
                        value=formatear_fecha_es(fertilizacion_origen["fecha"]),
                        placeholder="DD/MM/AAAA",
                        key=f"dup_fert_fecha_{fertilizacion_origen_id}"
                    )

                    error_fecha_copia = False

                    try:

                        fecha_copia_iso = parsear_fecha_es(fecha_copia_texto)
                        fecha_copia = pd.to_datetime(
                            fecha_copia_iso,
                            errors="coerce"
                        ).date() if fecha_copia_iso else None

                    except ValueError:

                        error_fecha_copia = True
                        fecha_copia = None

                    campana_origen = _entero_o_none(
                        fertilizacion_origen["campana_id"]
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
                            "Confirmo que quiero guardar esta copia aunque esté "
                            "fuera del periodo de campaña",
                            key=f"dup_fert_confirm_fecha_{fertilizacion_origen_id}"
                        )

                    elif validacion_fecha_copia["mensaje"]:

                        st.info(validacion_fecha_copia["mensaje"])

                    producto_copia = st.text_input(
                        "Producto fertilizante",
                        value=_texto(fertilizacion_origen["producto"]),
                        key=f"dup_fert_producto_{fertilizacion_origen_id}"
                    )
                    cantidad_copia = st.number_input(
                        "Cantidad",
                        min_value=0.0,
                        value=max(
                            0.0,
                            _numero(fertilizacion_origen["cantidad"])
                        ),
                        key=f"dup_fert_cantidad_{fertilizacion_origen_id}"
                    )
                    observaciones_copia = st.text_area(
                        "Observaciones",
                        value=_texto(fertilizacion_origen["observaciones"]),
                        key=f"dup_fert_obs_{fertilizacion_origen_id}"
                    )
                    confirmar_copia = st.checkbox(
                        "Confirmo que quiero crear una copia nueva de este registro",
                        key=f"dup_fert_confirm_{fertilizacion_origen_id}"
                    )
                    crear_copia = st.form_submit_button(
                        "Crear copia como nuevo registro",
                        key=f"dup_fert_btn_{fertilizacion_origen_id}"
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

                    elif not producto_copia.strip():

                        st.warning("Indica el producto fertilizante")

                    else:

                        parcelas_copia = _leer_ids_parcelas_fertilizacion(
                            fertilizacion_origen_id
                        )
                        conn = conectar()

                        try:

                            conn.execute("BEGIN")
                            detalles_copia = _detalles_actuacion_registro(
                                conn,
                                "fertilizacion_cultivos",
                                "fertilizacion_id",
                                fertilizacion_origen_id,
                            )
                            parcelas_compatibles_copia = (
                                _parcelas_compatibilidad_detalles(
                                    detalles_copia
                                )
                                if detalles_copia
                                else [
                                    int(parcela["parcela_id"])
                                    for _, parcela
                                    in parcelas_copia.iterrows()
                                ]
                            )
                            nueva_fertilizacion_id = (
                                _insertar_fertilizacion_compatible(
                                    conn,
                                    {
                                        "campana_id": campana_copia,
                                        "fecha": fecha_copia.isoformat(),
                                        "cultivo_id": _entero_o_none(
                                            fertilizacion_origen["cultivo_id"]
                                        ),
                                        "cultivo": _texto(
                                            fertilizacion_origen["cultivo"]
                                        ),
                                        "producto": producto_copia.strip(),
                                        "tipo_fertilizante": _texto(
                                            fertilizacion_origen["tipo"]
                                        ),
                                        "riqueza_npk": _texto(
                                            fertilizacion_origen["riqueza_npk"]
                                        ),
                                        "cantidad": cantidad_copia,
                                        "unidad": _texto(
                                            fertilizacion_origen["unidad"]
                                        ),
                                        "unidad_normalizada": _texto(
                                            fertilizacion_origen[
                                                "unidad_normalizada"
                                            ]
                                        ),
                                        "metodo_aplicacion": _texto(
                                            fertilizacion_origen[
                                                "metodo_aplicacion"
                                            ]
                                        ),
                                        "superficie": _numero(
                                            fertilizacion_origen["superficie"]
                                        ),
                                        "codigo_actuacion_siex": _texto(
                                            fertilizacion_origen[
                                                "codigo_actuacion_siex"
                                            ]
                                        ),
                                        "operario_id": _entero_o_none(
                                            fertilizacion_origen["operario_id"]
                                        ),
                                        "observaciones": (
                                            observaciones_copia.strip()
                                        ),
                                    },
                                    parcelas_compatibles_copia,
                                    detalles_cultivos=detalles_copia,
                                )
                            )

                            conn.commit()

                        except Exception as exc:

                            conn.rollback()
                            st.error(
                                "No se pudo crear la copia de fertilización: "
                                f"{exc}"
                            )

                        else:

                            st.session_state[
                                "duplicar_fertilizacion_mensaje"
                            ] = (
                                "Copia de fertilización creada como nuevo "
                                f"registro #{nueva_fertilizacion_id}"
                            )
                            for clave in claves_duplicar_fertilizacion:

                                st.session_state.pop(clave, None)

                            st.rerun()

                        finally:

                            conn.close()


    if seccion_fertilizacion == "✏️ Editar":

        st.subheader("Edición segura de fertilizaciones")

        with st.expander("Asignar cultivo estructurado"):

            if fertilizaciones_guardadas.empty:

                st.info("No hay fertilizaciones para asignar cultivo")

            else:

                fertilizaciones_por_id_asignar = (
                    fertilizaciones_guardadas
                    .copy()
                    .set_index("id", drop=False)
                )
                ids_asignar = [
                    int(valor)
                    for valor in fertilizaciones_por_id_asignar.index.tolist()
                ]
                fertilizacion_asignar_id = st.selectbox(
                    "Fertilización",
                    ids_asignar,
                    format_func=lambda valor: (
                        f"#{valor} · "
                        f"{_texto(fertilizaciones_por_id_asignar.loc[valor]['campana'])} · "
                        f"{_texto(fertilizaciones_por_id_asignar.loc[valor]['cultivo_mostrado'])}"
                    ),
                    key="fertilizacion_asignar_cultivo_id"
                )
                fertilizacion_asignar = fertilizaciones_por_id_asignar.loc[
                    fertilizacion_asignar_id
                ]
                cultivo_legacy_actual = _texto(fertilizacion_asignar["cultivo"])

                if (
                    _entero_o_none(fertilizacion_asignar["cultivo_id"]) is None
                    and cultivo_legacy_actual
                ):

                    st.caption(
                        "Cultivo legacy actual: "
                        f"{cultivo_legacy_actual}."
                    )

                cultivo_id_asignado = _selector_cultivo_estructurado(
                    cultivos_fertilizacion,
                    f"fertilizacion_nuevo_cultivo_id_{fertilizacion_asignar_id}",
                    campana_id=fertilizacion_asignar["campana_id"],
                    valor_actual=fertilizacion_asignar["cultivo_id"],
                )
                cultivo_asignado = _cultivo_por_id(
                    cultivos_fertilizacion,
                    cultivo_id_asignado,
                )

                if cultivo_asignado is None:

                    if cultivo_legacy_actual:

                        st.info(
                            "La fertilización conserva cultivo legacy. "
                            "Selecciona un cultivo estructurado para "
                            "actualizarlo o guarda sin cultivo para mantener "
                            "el texto actual."
                        )
                        cultivo_texto_asignado = cultivo_legacy_actual

                    elif fertilizacion_tiene_cultivo_legacy:

                        cultivo_texto_asignado = st.text_input(
                            "Cultivo textual de compatibilidad",
                            value=cultivo_legacy_actual,
                            key=(
                                "fertilizacion_cultivo_texto_asignado_"
                                f"{fertilizacion_asignar_id}"
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
                    "Confirmo que quiero actualizar el cultivo de esta fertilización",
                    key=f"fertilizacion_confirmar_cultivo_{fertilizacion_asignar_id}"
                )

                if st.button(
                    "Guardar cultivo estructurado",
                    key=f"fertilizacion_guardar_cultivo_{fertilizacion_asignar_id}",
                    type="primary",
                ):

                    if not confirmar_asignacion_cultivo:

                        st.warning("Marca la confirmación antes de guardar")

                    elif (
                        _entero_o_none(cultivo_id_asignado) is None
                        and not _texto(cultivo_texto_asignado)
                    ):

                        if fertilizacion_tiene_cultivo_legacy:

                            st.warning(
                                "Selecciona un cultivo estructurado o indica "
                                "un cultivo textual"
                            )

                        else:

                            st.warning("Selecciona un cultivo estructurado")

                    else:

                        conn = conectar()

                        try:

                            _actualizar_fertilizacion_compatible(
                                conn,
                                int(fertilizacion_asignar_id),
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

                        st.success("Cultivo de fertilización actualizado")
                        st.rerun()

        fertilizaciones_filtradas_editor = mostrar_filtros_dataframe(
            fertilizaciones_guardadas,
            "fertilizacion_editar",
            columnas_texto=[
                "producto",
                "cultivo_mostrado",
                "parcelas",
                "observaciones"
            ],
            columna_fecha="fecha",
            filtros_select={
                "Campaña": "campana",
                "Cultivo": "cultivo_mostrado",
                "Producto": "producto",
                "Tipo": "tipo"
            }
        )

        if fertilizaciones_filtradas_editor.empty:

            st.info("No hay fertilizaciones visibles para editar")

        else:

            editor_fertilizaciones = fertilizaciones_filtradas_editor.copy()
            columnas_editor_ocultas = [
                "cultivo_id",
                "cultivo",
                "cultivo_v6",
                "variedad_v6",
                "sistema_v6",
                "codigo_siex",
                "superficie_cultivo",
                "ano_plantacion",
                "campana_cultivo",
                "cultivo_estructurado",
                "cultivo_origen",
                "unidad_normalizada",
                "cultivos_detalle",
                "parcelas_detalle",
                "superficie_detalle",
                "tiene_detalle_multicultivo",
            ]

            if not fertilizacion_tiene_riqueza:

                columnas_editor_ocultas.append("riqueza_npk")

            if not fertilizacion_tiene_metodo:

                columnas_editor_ocultas.append("metodo_aplicacion")

            if not fertilizacion_tiene_operario:

                columnas_editor_ocultas.extend(["operario_id", "operario"])

            if not fertilizacion_tiene_codigo_siex:

                columnas_editor_ocultas.append("codigo_actuacion_siex")

            editor_fertilizaciones = editor_fertilizaciones.drop(
                columns=columnas_editor_ocultas,
                errors="ignore"
            )
            editor_fertilizaciones["fecha"] = pd.to_datetime(
                editor_fertilizaciones["fecha"],
                errors="coerce"
            )

            columnas_editor = [
                "id",
                "fecha",
                "campana",
                "cultivo_mostrado",
                "parcelas",
                "producto",
                "tipo",
            ]

            if fertilizacion_tiene_codigo_siex:

                columnas_editor.append("codigo_actuacion_siex")

            if fertilizacion_tiene_riqueza:

                columnas_editor.append("riqueza_npk")

            columnas_editor.extend(["cantidad", "unidad"])

            if fertilizacion_tiene_metodo:

                columnas_editor.append("metodo_aplicacion")

            columnas_editor.append("superficie")

            if fertilizacion_tiene_operario:

                columnas_editor.append("operario")

            columnas_editor.append("observaciones")

            fertilizaciones_editadas = st.data_editor(
                editor_fertilizaciones,
                num_rows="fixed",
                disabled=[
                    "id",
                    "campana_id",
                    "campana",
                    "cultivo_mostrado",
                    "parcelas",
                    "operario",
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
                    "tipo": st.column_config.SelectboxColumn(
                        "tipo",
                        options=["Orgánico", "Mineral", "Foliar", "Otro"]
                    ),
                    "unidad": st.column_config.SelectboxColumn(
                        "unidad",
                        options=["kg", "litros"]
                    ),
                    "cantidad": st.column_config.NumberColumn(
                        "cantidad",
                        min_value=0.0
                    ),
                    "superficie": st.column_config.NumberColumn(
                        "superficie",
                        min_value=0.0
                    ),
                },
                key="editor_seguro_fertilizaciones"
            )

            confirmar_fertilizaciones = st.checkbox(
                "Confirmo que quiero guardar los cambios de fertilización",
                key="confirmar_edicion_segura_fertilizaciones"
            )
            confirmar_fechas_fertilizaciones = st.checkbox(
                "Confirmo que quiero guardar fertilizaciones con fecha fuera de "
                "la campaña asociada",
                key="confirmar_fechas_fuera_fertilizaciones_editor"
            )

            if st.button(
                "Guardar cambios de fertilización",
                key="guardar_edicion_segura_fertilizacion"
            ):

                ids_originales = editor_fertilizaciones["id"].astype(int).tolist()
                ids_editados = fertilizaciones_editadas["id"].astype(int).tolist()
                errores = []
                avisos_fechas = []

                if not confirmar_fertilizaciones:

                    errores.append(
                        "Marca la confirmación antes de guardar fertilizaciones"
                    )

                if ids_editados != ids_originales:

                    errores.append("No se permite añadir, borrar ni cambiar IDs")

                fertilizaciones_para_guardar = fertilizaciones_editadas.copy()

                columnas_texto_fertilizaciones = [
                    "producto",
                    "tipo",
                    "riqueza_npk",
                    "unidad",
                    "unidad_normalizada",
                    "metodo_aplicacion",
                    "codigo_actuacion_siex",
                    "observaciones"
                ]

                for columna in columnas_texto_fertilizaciones:

                    if columna in fertilizaciones_para_guardar.columns:

                        fertilizaciones_para_guardar[columna] = (
                            fertilizaciones_para_guardar[columna]
                            .fillna("")
                            .astype(str)
                            .str.strip()
                        )

                fertilizaciones_para_guardar["fecha"] = pd.to_datetime(
                    fertilizaciones_para_guardar["fecha"],
                    errors="coerce"
                )

                for columna in [
                    "campana_id",
                    "cantidad",
                    "superficie",
                    "operario_id"
                ]:

                    if columna in fertilizaciones_para_guardar.columns:

                        fertilizaciones_para_guardar[columna] = pd.to_numeric(
                            fertilizaciones_para_guardar[columna],
                            errors="coerce"
                        )

                operarios_validos = set(
                    personas_fertilizacion["id"].astype(int).tolist()
                )

                for _, fila in fertilizaciones_para_guardar.iterrows():

                    etiqueta = f"ID {int(fila['id'])}"

                    if pd.isna(fila["fecha"]):

                        errores.append(f"{etiqueta}: fecha obligatoria")

                    if not fila["producto"]:

                        errores.append(f"{etiqueta}: producto obligatorio")

                    if pd.isna(fila["cantidad"]):

                        errores.append(f"{etiqueta}: cantidad debe ser numérica")

                    elif fila["cantidad"] < 0:

                        errores.append(f"{etiqueta}: cantidad no puede ser negativa")

                    if pd.isna(fila["superficie"]):

                        errores.append(f"{etiqueta}: superficie debe ser numérica")

                    elif fila["superficie"] < 0:

                        errores.append(
                            f"{etiqueta}: superficie no puede ser negativa"
                        )

                    if (
                        not pd.isna(fila["cantidad"])
                        and fila["cantidad"] > 0
                        and not fila["unidad"]
                    ):

                        errores.append(
                            f"{etiqueta}: unidad obligatoria si hay cantidad"
                        )

                    if (
                        fertilizacion_tiene_operario
                        and "operario_id" in fila
                        and not pd.isna(fila["operario_id"])
                        and int(fila["operario_id"]) not in operarios_validos
                    ):

                        errores.append(f"{etiqueta}: operario_id no válido")

                    if (
                        not pd.isna(fila["campana_id"])
                        and not pd.isna(fila["fecha"])
                    ):

                        validacion = validar_fecha_en_campana(
                            int(fila["campana_id"]),
                            fila["fecha"].date()
                        )

                        if validacion["mensaje"]:

                            avisos_fechas.append(
                                f"{etiqueta}: {validacion['mensaje']}"
                            )

                        if (
                            validacion["requiere_confirmacion"]
                            and not confirmar_fechas_fertilizaciones
                        ):

                            errores.append(
                                f"{etiqueta}: confirma la fecha fuera de campaña "
                                "para guardar"
                            )

                if errores:

                    for error in errores:

                        st.error(error)

                else:

                    for aviso in dict.fromkeys(avisos_fechas):

                        st.warning(aviso)

                    conn = conectar()

                    try:

                        for _, fila in fertilizaciones_para_guardar.iterrows():

                            operario_valor = fila.get("operario_id")
                            operario_id = (
                                None
                                if pd.isna(operario_valor)
                                else int(operario_valor)
                            )
                            unidad = fila.get("unidad", "")
                            _actualizar_fertilizacion_compatible(
                                conn,
                                int(fila["id"]),
                                {
                                    "fecha": fila["fecha"].date().isoformat(),
                                    "producto": fila.get("producto", ""),
                                    "tipo_fertilizante": fila.get("tipo", ""),
                                    "riqueza_npk": fila.get("riqueza_npk", ""),
                                    "cantidad": float(fila["cantidad"]),
                                    "unidad": unidad,
                                    "unidad_normalizada": _texto(unidad).lower(),
                                    "metodo_aplicacion": fila.get(
                                        "metodo_aplicacion",
                                        "",
                                    ),
                                    "superficie": float(fila["superficie"]),
                                    "codigo_actuacion_siex": fila.get(
                                        "codigo_actuacion_siex",
                                        "",
                                    ),
                                    "operario_id": operario_id,
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

                    st.success("Cambios de fertilización guardados")
                    st.rerun()




    if seccion_fertilizacion == "🗑️ Borrar":

        st.subheader("Borrado seguro")

        borrar_registros_seguro(
            "fertilizaciones",
            "id",
            fertilizaciones_guardadas,
            "fertilizaciones",
            tablas_hijas=[
                ("fertilizacion_cultivos", "fertilizacion_id"),
                ("fertilizacion_parcelas", "fertilizacion_id")
            ],
            campo_descripcion="producto",
            key="fertilizaciones"
        )
