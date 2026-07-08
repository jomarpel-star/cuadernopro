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


def _tabla_puente_practicas(conn):

    if _tabla_existe_conn(conn, "practicas_culturales_parcelas"):

        return "practicas_culturales_parcelas"

    if _tabla_existe_conn(conn, "practica_parcelas"):

        return "practica_parcelas"

    return None


def _anadir_si_existe(destino, columnas, columna, valor):

    if columna in columnas:

        destino[columna] = valor


def _insertar_relaciones_practica_parcelas(conn, practica_id, parcelas_ids):

    tabla = _tabla_puente_practicas(conn)

    if tabla is None:

        return

    columnas = _columnas_tabla_conn(conn, tabla)

    if not {"practica_id", "parcela_id"}.issubset(columnas):

        return

    for parcela in parcelas_ids or []:

        if isinstance(parcela, dict):

            parcela_id = parcela.get("parcela_id")
            superficie = parcela.get("superficie")

        else:

            parcela_id = parcela
            superficie = None

        valores = {
            "practica_id": int(practica_id),
            "parcela_id": int(parcela_id),
        }
        _anadir_si_existe(valores, columnas, "superficie", superficie)
        nombres = list(valores)
        conn.execute(
            f"""
            INSERT INTO {tabla}
            ({','.join(nombres)})
            VALUES ({','.join(['?'] * len(nombres))})
            """,
            [valores[columna] for columna in nombres],
        )


def _insertar_practica_compatible(
    conn,
    datos,
    parcelas_ids=None,
    detalles_cultivos=None,
):

    columnas = _columnas_tabla_conn(conn, "practicas_culturales")
    valores = {}
    detalles_normalizados = _normalizar_detalles_actuacion(detalles_cultivos)

    _anadir_si_existe(valores, columnas, "campana_id", datos.get("campana_id"))
    _anadir_si_existe(valores, columnas, "cultivo_id", datos.get("cultivo_id"))
    _anadir_si_existe(valores, columnas, "fecha", datos.get("fecha"))
    _anadir_si_existe(valores, columnas, "labor", _texto(datos.get("labor")))
    _anadir_si_existe(
        valores,
        columnas,
        "codigo_actuacion_siex",
        _texto(datos.get("codigo_actuacion_siex")),
    )
    _anadir_si_existe(valores, columnas, "superficie", datos.get("superficie"))
    _anadir_si_existe(
        valores,
        columnas,
        "maquinaria_id",
        datos.get("maquinaria_id"),
    )
    _anadir_si_existe(valores, columnas, "proveedor_id", datos.get("proveedor_id"))
    _anadir_si_existe(
        valores,
        columnas,
        "observaciones",
        _texto(datos.get("observaciones")),
    )
    _anadir_si_existe(valores, columnas, "cultivo", _texto(datos.get("cultivo")))
    _anadir_si_existe(valores, columnas, "operario_id", datos.get("operario_id"))

    if not valores:

        raise sqlite3.OperationalError(
            "La tabla practicas_culturales no tiene columnas utiles"
        )

    nombres = list(valores)
    cursor = conn.execute(
        f"""
        INSERT INTO practicas_culturales
        ({','.join(nombres)})
        VALUES ({','.join(['?'] * len(nombres))})
        """,
        [valores[columna] for columna in nombres],
    )
    practica_id = cursor.lastrowid
    parcelas_compatibles = (
        parcelas_ids
        if parcelas_ids is not None
        else _parcelas_compatibilidad_detalles(detalles_normalizados)
    )
    _insertar_relaciones_practica_parcelas(
        conn,
        practica_id,
        parcelas_compatibles,
    )
    _insertar_detalles_actuacion(
        conn,
        "practicas_culturales_cultivos",
        "practica_id",
        practica_id,
        detalles_normalizados,
    )
    return practica_id


def _actualizar_practica_compatible(conn, practica_id, datos):

    columnas = _columnas_tabla_conn(conn, "practicas_culturales")
    valores = {}

    for columna in (
        "campana_id",
        "cultivo_id",
        "fecha",
        "labor",
        "codigo_actuacion_siex",
        "superficie",
        "maquinaria_id",
        "proveedor_id",
        "observaciones",
        "cultivo",
        "operario_id",
    ):

        if columna in columnas and columna in datos:

            valores[columna] = datos[columna]

    if not valores:

        return

    asignaciones = ",".join(f"{columna}=?" for columna in valores)
    conn.execute(
        f"UPDATE practicas_culturales SET {asignaciones} WHERE id=?",
        [valores[columna] for columna in valores] + [int(practica_id)],
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
    superficie = _formatear_hectareas(_superficie_cultivo_para_etiqueta(fila))
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


def _leer_proveedores_practicas(solo_activos=True):

    sql = "SELECT id,nombre,activo FROM proveedores"

    if solo_activos:

        sql += " WHERE COALESCE(activo,1)=1"

    sql += " ORDER BY nombre,id"

    return leer(sql)


def _leer_maquinaria_practicas():

    columnas = _columnas_tabla("maquinaria")

    if not columnas:

        return pd.DataFrame(columns=["id", "nombre", "tipo"])

    expr_nombre = "''"

    if "nombre" in columnas:

        expr_nombre = "COALESCE(nombre,'')"

    elif "descripcion" in columnas:

        expr_nombre = "COALESCE(descripcion,'')"

    elif "marca" in columnas and "modelo" in columnas:

        expr_nombre = "TRIM(COALESCE(marca,'') || ' ' || COALESCE(modelo,''))"

    elif "marca" in columnas:

        expr_nombre = "COALESCE(marca,'')"

    expr_tipo = "COALESCE(tipo,'')" if "tipo" in columnas else "''"

    return leer(
        f"""
        SELECT
            id,
            {expr_nombre} AS nombre,
            {expr_tipo} AS tipo
        FROM maquinaria
        ORDER BY nombre,id
        """
    )


def _opciones_proveedores_editor(proveedores):

    texto_sin = "Sin prestador externo"
    opciones = [texto_sin]
    id_a_etiqueta = {}
    etiqueta_a_id = {texto_sin: None}

    if proveedores is None or proveedores.empty:

        return opciones, id_a_etiqueta, etiqueta_a_id

    for _, fila in proveedores.iterrows():

        proveedor_id = int(fila["id"])
        nombre = _texto(fila["nombre"]) or f"ID {proveedor_id}"
        etiqueta = f"{proveedor_id} - {nombre}"
        activo = pd.to_numeric(fila.get("activo", 1), errors="coerce")

        if not pd.isna(activo) and int(activo) == 0:

            etiqueta += " (inactivo)"

        opciones.append(etiqueta)
        id_a_etiqueta[proveedor_id] = etiqueta
        etiqueta_a_id[etiqueta] = proveedor_id

    return opciones, id_a_etiqueta, etiqueta_a_id


def _etiqueta_proveedor_desde_id(valor, id_a_etiqueta):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return "Sin prestador externo"

    return id_a_etiqueta.get(int(numero), "Sin prestador externo")


def _leer_practicas_guardadas(conn=None, practica_id=None):

    if conn is not None:

        practicas_cols = _columnas_tabla_conn(conn, "practicas_culturales")
        cultivos_cols = _columnas_tabla_conn(conn, "cultivos")
        maquinaria_cols = _columnas_tabla_conn(conn, "maquinaria")
        tabla_puente = _tabla_puente_practicas(conn)
        tiene_parcelas = _tabla_existe_conn(conn, "parcelas")

    else:

        conn_tmp = conectar()

        try:

            practicas_cols = _columnas_tabla_conn(
                conn_tmp,
                "practicas_culturales",
            )
            cultivos_cols = _columnas_tabla_conn(conn_tmp, "cultivos")
            maquinaria_cols = _columnas_tabla_conn(conn_tmp, "maquinaria")
            tabla_puente = _tabla_puente_practicas(conn_tmp)
            tiene_parcelas = _tabla_existe_conn(conn_tmp, "parcelas")

        finally:

            conn_tmp.close()

    if not practicas_cols:

        return pd.DataFrame()

    expr_fecha = _valor_texto_columna(
        "practicas_culturales",
        "fecha",
        practicas_cols,
    )
    expr_campana_id = _valor_numerico_columna(
        "practicas_culturales",
        "campana_id",
        practicas_cols,
    )
    expr_cultivo_id = _valor_numerico_columna(
        "practicas_culturales",
        "cultivo_id",
        practicas_cols,
    )
    expr_cultivo_legacy = _valor_texto_columna(
        "practicas_culturales",
        "cultivo",
        practicas_cols,
    )
    expr_labor = _valor_texto_columna(
        "practicas_culturales",
        "labor",
        practicas_cols,
    )
    expr_codigo = _valor_texto_columna(
        "practicas_culturales",
        "codigo_actuacion_siex",
        practicas_cols,
    )
    expr_superficie = _valor_numerico_columna(
        "practicas_culturales",
        "superficie",
        practicas_cols,
    )
    expr_maquinaria_id = _valor_numerico_columna(
        "practicas_culturales",
        "maquinaria_id",
        practicas_cols,
    )
    expr_operario_id = _valor_numerico_columna(
        "practicas_culturales",
        "operario_id",
        practicas_cols,
    )
    expr_proveedor_id = _valor_numerico_columna(
        "practicas_culturales",
        "proveedor_id",
        practicas_cols,
    )
    expr_observaciones = _valor_texto_columna(
        "practicas_culturales",
        "observaciones",
        practicas_cols,
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

    if tabla_puente and tiene_parcelas:

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
        """
        LEFT JOIN campanas
        ON campanas.id = practicas_culturales.campana_id
        """,
        """
        LEFT JOIN cultivos
        ON cultivos.id = practicas_culturales.cultivo_id
        """,
        """
        LEFT JOIN campanas AS campanas_cultivo
        ON campanas_cultivo.id = cultivos.campana_id
        """,
    ]

    if tabla_puente and tiene_parcelas:

        joins.extend(
            [
                f"""
                LEFT JOIN {tabla_puente}
                ON {tabla_puente}.practica_id = practicas_culturales.id
                """,
                f"LEFT JOIN parcelas ON parcelas.id = {tabla_puente}.parcela_id",
            ]
        )

    if "maquinaria_id" in practicas_cols:

        joins.append(
            "LEFT JOIN maquinaria ON maquinaria.id = practicas_culturales.maquinaria_id"
        )

        if "nombre" in maquinaria_cols:

            expr_maquinaria = "COALESCE(maquinaria.nombre,'')"

        elif "descripcion" in maquinaria_cols:

            expr_maquinaria = "COALESCE(maquinaria.descripcion,'')"

        elif "marca" in maquinaria_cols and "modelo" in maquinaria_cols:

            expr_maquinaria = (
                "TRIM(COALESCE(maquinaria.marca,'') || ' ' || "
                "COALESCE(maquinaria.modelo,''))"
            )

        elif "marca" in maquinaria_cols:

            expr_maquinaria = "COALESCE(maquinaria.marca,'')"

        else:

            expr_maquinaria = "''"

    else:

        expr_maquinaria = "''"

    if "operario_id" in practicas_cols:

        joins.append(
            "LEFT JOIN personas ON personas.id = practicas_culturales.operario_id"
        )
        expr_operario = "COALESCE(personas.nombre,'')"

    else:

        expr_operario = "''"

    if "proveedor_id" in practicas_cols:

        joins.append(
            "LEFT JOIN proveedores ON proveedores.id = practicas_culturales.proveedor_id"
        )
        expr_prestador = "COALESCE(proveedores.nombre,'')"

    else:

        expr_prestador = "''"

    where = ""
    params = ()

    if practica_id is not None:

        where = "WHERE practicas_culturales.id=?"
        params = (int(practica_id),)

    sql = f"""
        SELECT
        practicas_culturales.id,
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
        {expr_labor} AS labor,
        {expr_codigo} AS codigo_actuacion_siex,
        {expr_superficie} AS superficie,
        {expr_maquinaria_id} AS maquinaria_id,
        {expr_maquinaria} AS maquinaria,
        {expr_operario_id} AS operario_id,
        {expr_operario} AS operario,
        {expr_proveedor_id} AS proveedor_id,
        {expr_prestador} AS prestador,
        {expr_observaciones} AS observaciones
        FROM practicas_culturales
        {" ".join(joins)}
        {where}
        GROUP BY practicas_culturales.id
        ORDER BY practicas_culturales.fecha DESC,
        practicas_culturales.id DESC
    """

    practicas = _leer_dataframe(sql, params, conn=conn)

    if practicas.empty:

        return practicas

    if conn is not None:

        practicas = _agregar_detalles_actuacion(
            practicas,
            conn,
            "practicas_culturales_cultivos",
            "practica_id",
        )

    else:

        conn_detalles = conectar()

        try:

            practicas = _agregar_detalles_actuacion(
                practicas,
                conn_detalles,
                "practicas_culturales_cultivos",
                "practica_id",
            )

        finally:

            conn_detalles.close()

    tiene_detalle = practicas["tiene_detalle_multicultivo"].fillna(False)
    practicas["parcelas"] = practicas["parcelas_detalle"].where(
        tiene_detalle & (practicas["parcelas_detalle"].astype(str) != ""),
        practicas["parcelas"],
    )
    return practicas


def _preparar_practicas_presentacion(practicas_guardadas):

    if not practicas_guardadas.empty:

        practicas_guardadas = practicas_guardadas.copy()
        practicas_guardadas["cultivo_estructurado"] = (
            practicas_guardadas.apply(
                lambda fila: (
                    _etiqueta_cultivo(fila)
                    if _entero_o_none(fila.get("cultivo_id")) is not None
                    else ""
                ),
                axis=1,
            )
        )
        practicas_guardadas["cultivo_mostrado"] = (
            practicas_guardadas["cultivos_detalle"].where(
                practicas_guardadas["tiene_detalle_multicultivo"].fillna(False)
                & (practicas_guardadas["cultivos_detalle"].astype(str) != ""),
                practicas_guardadas["cultivo_estructurado"].where(
                    practicas_guardadas["cultivo_estructurado"] != "",
                    practicas_guardadas["cultivo"].fillna("").astype(str),
                ),
            )
        )
        practicas_guardadas["cultivo_origen"] = (
            practicas_guardadas.apply(
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
        return practicas_guardadas

    practicas_guardadas["cultivo_estructurado"] = ""
    practicas_guardadas["cultivo_mostrado"] = ""
    practicas_guardadas["cultivo_origen"] = ""
    practicas_guardadas["cultivos_detalle"] = ""
    practicas_guardadas["parcelas_detalle"] = ""
    practicas_guardadas["superficie_detalle"] = 0.0
    practicas_guardadas["tiene_detalle_multicultivo"] = False
    return practicas_guardadas


def _leer_ids_parcelas_practica(practica_id):

    conn = conectar()

    try:

        tabla = _tabla_puente_practicas(conn)

    finally:

        conn.close()

    if tabla is None:

        return pd.DataFrame(columns=["parcela_id"])

    return leer(
        f"""
        SELECT parcela_id
        FROM {tabla}
        WHERE practica_id=?
        ORDER BY id, parcela_id
        """,
        (practica_id,),
    )


def render(CAMPANA):

    st.title("🌿 Prácticas culturales")

    opciones_practicas = [
        "📋 Listado",
        "➕ Nueva práctica",
        "🔁 Duplicar",
        "✏️ Editar",
        "🗑️ Borrar",
    ]
    seccion_practicas = st.radio(
        "Opciones de prácticas culturales",
        opciones_practicas,
        horizontal=True,
        key="practicas_seccion"
    )

    labores_culturales = [
        "Poda",
        "Triturado restos poda",
        "Laboreo",
        "Desbroce",
        "Siega",
        "Riego",
        "Recolección",
        "Mantenimiento suelo",
        "Otro"
    ]

    cultivos_practicas = _leer_cultivos_v6()
    parcelas_cultivos_v6, parcelas_cultivos_legacy = _leer_parcelas_cultivos()
    parcelas_disponibles = _leer_parcelas_disponibles()

    maquinaria_practicas = _leer_maquinaria_practicas()
    personas_practicas = leer(
        "SELECT id,nombre FROM personas ORDER BY nombre"
    )
    proveedores_practicas = _leer_proveedores_practicas()
    proveedores_edicion_practicas = _leer_proveedores_practicas(
        solo_activos=False
    )
    columnas_practicas = _columnas_tabla("practicas_culturales")
    practicas_tiene_cultivo_legacy = "cultivo" in columnas_practicas
    practicas_tiene_codigo_siex = "codigo_actuacion_siex" in columnas_practicas
    practicas_tiene_maquinaria = "maquinaria_id" in columnas_practicas
    practicas_tiene_operario = "operario_id" in columnas_practicas
    practicas_tiene_proveedor = "proveedor_id" in columnas_practicas


    if seccion_practicas == "➕ Nueva práctica":

        if "form_practica_version" not in st.session_state:

            st.session_state["form_practica_version"] = 0

        form_practica_version = st.session_state["form_practica_version"]

        if cultivos_practicas.empty:

            if practicas_tiene_cultivo_legacy:

                st.info(
                    "No hay cultivos estructurados disponibles. Puede "
                    "registrar una práctica con cultivo textual para mantener "
                    "compatibilidad."
                )

            else:

                st.info(
                    "No hay cultivos estructurados disponibles. Crea un "
                    "cultivo antes de registrar prácticas."
                )

        cultivos_ordenados = cultivos_practicas.copy()
        cultivos_ordenados["prioridad_campana"] = (
            pd.to_numeric(
                cultivos_ordenados["campana_id"],
                errors="coerce",
            ) != int(CAMPANA)
        ).astype(int)
        cultivos_ordenados = cultivos_ordenados.sort_values(
            by=["prioridad_campana", "campana", "cultivo_texto", "id"]
        )
        ids_cultivos_practicas = (
            cultivos_ordenados["id"].dropna().astype(int).tolist()
        )
        cultivos_ids_practica = st.multiselect(
            "Cultivos afectados",
            ids_cultivos_practicas,
            default=(
                [ids_cultivos_practicas[0]]
                if ids_cultivos_practicas
                else []
            ),
            format_func=lambda valor: _etiqueta_cultivo(
                _cultivo_por_id(cultivos_practicas, valor)
            ),
            key=f"cultivos_practica_{form_practica_version}",
        )
        cultivo_id_practica = (
            int(cultivos_ids_practica[0])
            if cultivos_ids_practica
            else None
        )
        cultivo_seleccionado = _cultivo_por_id(
            cultivos_practicas,
            cultivo_id_practica,
        )
        cultivo_practica = (
            _nombre_cultivo(cultivo_seleccionado)
            if cultivo_seleccionado is not None
            else ""
        )
        detalles_practica = []
        parcelas_practicas_sel = []
        parcelas_practicas_sin_superficie = False

        for cultivo_id_detalle in cultivos_ids_practica:

            cultivo_detalle = _cultivo_por_id(
                cultivos_practicas,
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
                f"Parcelas afectadas de {etiqueta_cultivo}",
                opciones_parcelas,
                default=opciones_parcelas,
                format_func=lambda valor: etiquetas_parcelas.get(
                    int(valor),
                    str(valor),
                ),
                key=(
                    f"parcelas_practicas_{form_practica_version}_"
                    f"{int(cultivo_id_detalle)}"
                ),
            )
            parcelas_practicas_sel.extend(
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

                    parcelas_practicas_sin_superficie = True
                    superficie = None

                detalles_practica.append(
                    {
                        "cultivo_id": int(cultivo_id_detalle),
                        "parcela_id": int(parcela_detalle["parcela_id"]),
                        "superficie": superficie,
                    }
                )

        detalles_practica = _normalizar_detalles_actuacion(detalles_practica)
        superficie_total_seleccionada = float(
            sum(
                float(detalle["superficie"] or 0)
                for detalle in detalles_practica
            )
        )
        firma_parcelas_practicas = (
            "_".join(
                f"{detalle['cultivo_id']}-{detalle['parcela_id']}"
                for detalle in detalles_practica
            )
            if detalles_practica
            else "sin_parcelas"
        )
        superficie_practica_sugerida = superficie_total_seleccionada

        st.info(
            "Superficie seleccionada: "
            f"{superficie_total_seleccionada:.2f} ha"
        )

        if parcelas_practicas_sin_superficie:

            st.warning("Hay parcelas seleccionadas sin superficie informada.")

        with st.form(f"nueva_practica_cultural_v{form_practica_version}"):

            fecha_practica_texto = st.text_input(
                "Fecha",
                value=formatear_fecha_es(pd.Timestamp.today()),
                placeholder="DD/MM/AAAA",
                key=f"practica_fecha_{form_practica_version}"
            )
            error_formato_fecha_practica = False

            try:

                fecha_practica_iso = parsear_fecha_es(fecha_practica_texto)
                fecha_practica = pd.to_datetime(
                    fecha_practica_iso,
                    errors="coerce"
                ).date() if fecha_practica_iso else None

            except ValueError:

                error_formato_fecha_practica = True
                fecha_practica = None

            validacion_fecha_practica = (
                validar_fecha_en_campana(CAMPANA, fecha_practica)
                if fecha_practica is not None
                else {
                    "requiere_confirmacion": False,
                    "mensaje": ""
                }
            )
            confirmar_fecha_practica = False

            if validacion_fecha_practica["requiere_confirmacion"]:

                st.warning(validacion_fecha_practica["mensaje"])
                confirmar_fecha_practica = st.checkbox(
                    "Confirmo que quiero guardar este registro aunque esté "
                    "fuera del periodo de campaña",
                    key=f"confirmar_fecha_fuera_practica_{form_practica_version}"
                )

            elif validacion_fecha_practica["mensaje"]:

                st.info(validacion_fecha_practica["mensaje"])

            labor_practica = st.selectbox(
                "Labor",
                labores_culturales,
                key=f"practica_labor_{form_practica_version}"
            )
            if practicas_tiene_codigo_siex:

                codigo_actuacion_siex = st.text_input(
                    "Código actuación SIEX",
                    key=f"practica_codigo_siex_{form_practica_version}",
                )

            else:

                codigo_actuacion_siex = ""

            superficie_practica = st.number_input(
                "Superficie",
                min_value=0.0,
                value=max(0.0, float(superficie_practica_sugerida)),
                key=(
                    f"practica_superficie_{form_practica_version}_"
                    f"{cultivo_id_practica or 'sin_cultivo'}_"
                    f"{firma_parcelas_practicas}"
                )
            )

            st.markdown("**Maquinaria / prestador**")
            maquinaria_practica = None

            if not practicas_tiene_maquinaria:

                maquinaria_practica = None

            elif maquinaria_practicas.empty:

                st.info("No hay maquinaria registrada para seleccionar")

            else:

                maquinaria_practica = st.selectbox(
                    "Maquinaria",
                    [None] + maquinaria_practicas.id.tolist(),
                    format_func=lambda x: (
                        "Sin maquinaria"
                        if x is None
                        else (
                            f"{maquinaria_practicas[maquinaria_practicas.id == x].nombre.values[0]}"
                            f" - {maquinaria_practicas[maquinaria_practicas.id == x].tipo.fillna('').values[0]}"
                        ).strip(" -")
                    ),
                    key=f"practica_maquinaria_{form_practica_version}"
                )

            proveedor_practica = None

            if not practicas_tiene_proveedor:

                proveedor_practica = None

            elif proveedores_practicas.empty:

                st.info(
                    "No hay proveedores activos para seleccionar "
                    "prestador externo"
                )

            else:

                proveedores_por_id = proveedores_practicas.set_index(
                    "id",
                    drop=False
                )
                proveedor_practica = st.selectbox(
                    "Prestador externo",
                    [None]
                    + proveedores_practicas["id"].astype(int).tolist(),
                    format_func=lambda valor: (
                        "Sin prestador externo"
                        if valor is None
                        else proveedores_por_id.loc[valor]["nombre"]
                    ),
                    key=f"practica_proveedor_{form_practica_version}"
                )

            operario_practica = None

            if not practicas_tiene_operario:

                operario_practica = None

            elif personas_practicas.empty:

                st.info("No hay personas registradas para seleccionar operario")

            else:

                operario_practica = st.selectbox(
                    "Operario",
                    [None] + personas_practicas.id.tolist(),
                    format_func=lambda x: (
                        "Sin operario"
                        if x is None
                        else personas_practicas[
                            personas_practicas.id == x
                        ].nombre.values[0]
                    ),
                    key=f"practica_operario_{form_practica_version}"
                )

            observaciones_practica = st.text_area(
                "Observaciones",
                key=f"practica_observaciones_{form_practica_version}"
            )

            guardar_practica = st.form_submit_button(
                "Registrar práctica cultural"
            )

        if guardar_practica:

            if (
                error_formato_fecha_practica
            ):

                st.warning("La fecha debe tener formato DD/MM/AAAA")

            elif fecha_practica is None:

                st.warning("La fecha es obligatoria")

            elif (
                validacion_fecha_practica["requiere_confirmacion"]
                and not confirmar_fecha_practica
            ):

                st.warning(
                    "Marca la confirmación para guardar la práctica cultural"
                )

            elif not cultivos_ids_practica:

                st.warning("Selecciona al menos un cultivo")

            elif not detalles_practica:

                st.warning("Selecciona al menos una parcela afectada")

            else:

                if superficie_practica == 0:

                    st.warning("La superficie de la práctica es 0 ha")

                conn = conectar()
                try:

                    _insertar_practica_compatible(
                        conn,
                        {
                            "campana_id": CAMPANA,
                            "fecha": fecha_practica.isoformat(),
                            "cultivo_id": _entero_o_none(cultivo_id_practica),
                            "cultivo": _texto(cultivo_practica),
                            "labor": labor_practica,
                            "codigo_actuacion_siex": (
                                codigo_actuacion_siex.strip()
                            ),
                            "superficie": superficie_practica,
                            "maquinaria_id": maquinaria_practica,
                            "operario_id": operario_practica,
                            "proveedor_id": proveedor_practica,
                            "observaciones": observaciones_practica.strip(),
                        },
                        _parcelas_compatibilidad_detalles(detalles_practica),
                        detalles_cultivos=detalles_practica,
                    )

                    conn.commit()

                except sqlite3.Error:

                    conn.rollback()
                    raise

                finally:

                    conn.close()

                st.success("Práctica cultural registrada")
                st.session_state["form_practica_version"] += 1
                st.rerun()

    practicas_guardadas = _preparar_practicas_presentacion(
        _leer_practicas_guardadas()
    )


    if seccion_practicas == "📋 Listado":

        practicas_filtradas = mostrar_filtros_dataframe(
            practicas_guardadas,
            "practicas_listado",
            columnas_texto=[
                "cultivo_mostrado",
                "parcelas",
                "labor",
                "operario",
                "prestador",
                "observaciones"
            ],
            columna_fecha="fecha",
            filtros_select={
                "Campaña": "campana",
                "Cultivo": "cultivo_mostrado",
                "Labor": "labor",
                "Operario": "operario",
                "Prestador": "prestador"
            }
        )
        columnas_ocultas = [
            "campana_id",
            "cultivo_id",
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
            "maquinaria_id",
            "operario_id",
            "proveedor_id",
            "cultivos_detalle",
            "parcelas_detalle",
            "superficie_detalle",
            "tiene_detalle_multicultivo",
        ]
        practicas_listado = practicas_filtradas.drop(
            columns=columnas_ocultas,
            errors="ignore"
        )
        columnas_listado = [
            "id",
            "campana",
            "fecha",
            "cultivo_mostrado",
            "parcelas",
            "labor",
        ]

        if practicas_tiene_codigo_siex:

            columnas_listado.append("codigo_actuacion_siex")

        columnas_listado.append("superficie")

        if practicas_tiene_maquinaria:

            columnas_listado.append("maquinaria")

        if practicas_tiene_operario:

            columnas_listado.append("operario")

        if practicas_tiene_proveedor:

            columnas_listado.append("prestador")

        columnas_listado.append("observaciones")
        practicas_visual = preparar_dataframe_visual(
            preparar_columnas_fecha_tabla(practicas_listado, ["fecha"]),
            columnas=columnas_listado,
            ocultar_tecnicas=True,
            etiquetas_extra={
                "cultivo_mostrado": "Cultivo",
                "codigo_actuacion_siex": "Código actuación SIEX",
                "labor": "Labor",
                "operario": "Operario",
                "prestador": "Prestador",
            },
        )
        st.dataframe(
            practicas_visual,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Fecha": st.column_config.DateColumn(
                    "Fecha",
                    format="DD/MM/YYYY"
                ),
            }
        )


    if seccion_practicas == "🔁 Duplicar":

        mensaje_duplicacion_practica = st.session_state.pop(
            "duplicar_practica_mensaje",
            None
        )

        if mensaje_duplicacion_practica:

            st.success(mensaje_duplicacion_practica)

        with st.expander("Duplicar registro existente"):

            if practicas_guardadas.empty:

                st.info("No hay prácticas culturales para duplicar")

            else:

                practicas_por_id = (
                    practicas_guardadas
                    .copy()
                    .set_index("id", drop=False)
                )
                ids_practicas = [
                    int(valor)
                    for valor in practicas_por_id.index.tolist()
                ]

                def formato_practica_origen(practica_id):

                    fila = practicas_por_id.loc[practica_id]
                    fecha = formatear_fecha_es(fila["fecha"])
                    labor = _texto(fila["labor"])
                    cultivo = _texto(fila["cultivo_mostrado"])

                    return f"#{practica_id} · {fecha} · {labor} · {cultivo}"

                practica_origen_id = st.selectbox(
                    "Práctica a duplicar",
                    ids_practicas,
                    format_func=formato_practica_origen,
                    key="dup_pract_origen_id"
                )
                claves_duplicar_practica = [
                    f"dup_pract_fecha_{practica_origen_id}",
                    f"dup_pract_labor_{practica_origen_id}",
                    f"dup_pract_superficie_{practica_origen_id}",
                    f"dup_pract_obs_{practica_origen_id}",
                    f"dup_pract_confirm_fecha_{practica_origen_id}",
                    f"dup_pract_confirm_{practica_origen_id}",
                    f"dup_pract_btn_{practica_origen_id}"
                ]

                if (
                    st.session_state.get("dup_pract_origen_id_anterior")
                    != practica_origen_id
                ):

                    for clave in claves_duplicar_practica:

                        st.session_state.pop(clave, None)

                    st.session_state["dup_pract_origen_id_anterior"] = (
                        practica_origen_id
                )

                practica_resumen = practicas_por_id.loc[practica_origen_id]
                practica_origen_df = _leer_practicas_guardadas(
                    practica_id=practica_origen_id,
                )

                if practica_origen_df.empty:

                    st.warning("No se encontró el registro origen")

                else:

                    practica_origen = practica_origen_df.iloc[0]

                    st.write(
                        "Origen: "
                        f"campaña {_texto(practica_origen['campana'])} · "
                        f"cultivo {_texto(practica_resumen['cultivo_mostrado'])} · "
                        f"parcelas {_texto(practica_resumen['parcelas']) or 'Sin parcelas'} · "
                        f"operario {_texto(practica_resumen['operario']) or 'Sin operario'} · "
                        f"prestador {_texto(practica_resumen['prestador']) or 'Sin prestador'}"
                    )

                    with st.form(
                        f"dup_pract_form_{practica_origen_id}"
                    ):

                        fecha_copia_texto = st.text_input(
                            "Fecha",
                            value=formatear_fecha_es(practica_origen["fecha"]),
                            placeholder="DD/MM/AAAA",
                            key=f"dup_pract_fecha_{practica_origen_id}"
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
                            practica_origen["campana_id"]
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
                                key=f"dup_pract_confirm_fecha_{practica_origen_id}"
                            )

                        elif validacion_fecha_copia["mensaje"]:

                            st.info(validacion_fecha_copia["mensaje"])

                        labor_origen = _texto(practica_origen["labor"])
                        opciones_labor_copia = labores_culturales.copy()

                        if (
                            labor_origen
                            and labor_origen not in opciones_labor_copia
                        ):

                            opciones_labor_copia.insert(0, labor_origen)

                        indice_labor_copia = (
                            opciones_labor_copia.index(labor_origen)
                            if labor_origen in opciones_labor_copia
                            else 0
                        )
                        labor_copia = st.selectbox(
                            "Labor",
                            opciones_labor_copia,
                            index=indice_labor_copia,
                            key=f"dup_pract_labor_{practica_origen_id}"
                        )
                        superficie_copia = st.number_input(
                            "Superficie",
                            min_value=0.0,
                            value=max(
                                0.0,
                                _numero(practica_origen["superficie"])
                            ),
                            key=f"dup_pract_superficie_{practica_origen_id}"
                        )
                        observaciones_copia = st.text_area(
                            "Observaciones",
                            value=_texto(practica_origen["observaciones"]),
                            key=f"dup_pract_obs_{practica_origen_id}"
                        )
                        confirmar_copia = st.checkbox(
                            "Confirmo que quiero crear una copia nueva de este registro",
                            key=f"dup_pract_confirm_{practica_origen_id}"
                        )
                        crear_copia = st.form_submit_button(
                            "Crear copia como nuevo registro",
                            key=f"dup_pract_btn_{practica_origen_id}"
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

                        elif not labor_copia.strip():

                            st.warning("La labor es obligatoria")

                        else:

                            parcelas_copia = _leer_ids_parcelas_practica(
                                practica_origen_id
                            )
                            conn = conectar()

                            try:

                                conn.execute("BEGIN")
                                detalles_copia = _detalles_actuacion_registro(
                                    conn,
                                    "practicas_culturales_cultivos",
                                    "practica_id",
                                    practica_origen_id,
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
                                nueva_practica_id = _insertar_practica_compatible(
                                    conn,
                                    {
                                        "campana_id": campana_copia,
                                        "fecha": fecha_copia.isoformat(),
                                        "cultivo_id": _entero_o_none(
                                            practica_origen["cultivo_id"]
                                        ),
                                        "cultivo": _texto(
                                            practica_origen["cultivo"]
                                        ),
                                        "labor": labor_copia.strip(),
                                        "codigo_actuacion_siex": _texto(
                                            practica_origen[
                                                "codigo_actuacion_siex"
                                            ]
                                        ),
                                        "superficie": superficie_copia,
                                        "maquinaria_id": _entero_o_none(
                                            practica_origen["maquinaria_id"]
                                        ),
                                        "operario_id": _entero_o_none(
                                            practica_origen["operario_id"]
                                        ),
                                        "proveedor_id": _entero_o_none(
                                            practica_origen["proveedor_id"]
                                        ),
                                        "observaciones": (
                                            observaciones_copia.strip()
                                        ),
                                    },
                                    parcelas_compatibles_copia,
                                    detalles_cultivos=detalles_copia,
                                )

                                conn.commit()

                            except Exception as exc:

                                conn.rollback()
                                st.error(
                                    "No se pudo crear la copia de práctica "
                                    f"cultural: {exc}"
                                )

                            else:

                                st.session_state["duplicar_practica_mensaje"] = (
                                    "Copia de práctica cultural creada como "
                                    f"nuevo registro #{nueva_practica_id}"
                                )
                                for clave in claves_duplicar_practica:

                                    st.session_state.pop(clave, None)

                                st.rerun()

                            finally:

                                conn.close()


    if seccion_practicas == "✏️ Editar":

        st.subheader("Edición segura")

        if practicas_guardadas.empty:

            st.info("No hay prácticas culturales registradas")

        else:

            with st.expander("Asignar cultivo estructurado"):

                practicas_por_id_asignar = (
                    practicas_guardadas
                    .copy()
                    .set_index("id", drop=False)
                )
                ids_asignar = [
                    int(valor)
                    for valor in practicas_por_id_asignar.index.tolist()
                ]
                practica_asignar_id = st.selectbox(
                    "Práctica cultural",
                    ids_asignar,
                    format_func=lambda valor: (
                        f"#{valor} · "
                        f"{_texto(practicas_por_id_asignar.loc[valor]['campana'])} · "
                        f"{_texto(practicas_por_id_asignar.loc[valor]['cultivo_mostrado'])}"
                    ),
                    key="practica_asignar_cultivo_id"
                )
                practica_asignar = practicas_por_id_asignar.loc[
                    practica_asignar_id
                ]
                cultivo_legacy_actual = _texto(practica_asignar["cultivo"])

                if (
                    _entero_o_none(practica_asignar["cultivo_id"]) is None
                    and cultivo_legacy_actual
                ):

                    st.caption(
                        "Cultivo legacy actual: "
                        f"{cultivo_legacy_actual}."
                    )

                cultivo_id_asignado = _selector_cultivo_estructurado(
                    cultivos_practicas,
                    f"practica_nuevo_cultivo_id_{practica_asignar_id}",
                    campana_id=practica_asignar["campana_id"],
                    valor_actual=practica_asignar["cultivo_id"],
                )
                cultivo_asignado = _cultivo_por_id(
                    cultivos_practicas,
                    cultivo_id_asignado,
                )

                if cultivo_asignado is None:

                    if cultivo_legacy_actual:

                        st.info(
                            "La práctica conserva cultivo legacy. Selecciona "
                            "un cultivo estructurado para actualizarlo o "
                            "guarda sin cultivo para mantener el texto actual."
                        )
                        cultivo_texto_asignado = cultivo_legacy_actual

                    elif practicas_tiene_cultivo_legacy:

                        cultivo_texto_asignado = st.text_input(
                            "Cultivo textual de compatibilidad",
                            value=cultivo_legacy_actual,
                            key=(
                                "practica_cultivo_texto_asignado_"
                                f"{practica_asignar_id}"
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
                    "Confirmo que quiero actualizar el cultivo de esta práctica",
                    key=f"practica_confirmar_cultivo_{practica_asignar_id}"
                )

                if st.button(
                    "Guardar cultivo estructurado",
                    key=f"practica_guardar_cultivo_{practica_asignar_id}",
                    type="primary",
                ):

                    if not confirmar_asignacion_cultivo:

                        st.warning("Marca la confirmación antes de guardar")

                    elif (
                        _entero_o_none(cultivo_id_asignado) is None
                        and not _texto(cultivo_texto_asignado)
                    ):

                        if practicas_tiene_cultivo_legacy:

                            st.warning(
                                "Selecciona un cultivo estructurado o indica "
                                "un cultivo textual"
                            )

                        else:

                            st.warning("Selecciona un cultivo estructurado")

                    else:

                        conn = conectar()

                        try:

                            _actualizar_practica_compatible(
                                conn,
                                int(practica_asignar_id),
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

                        st.success("Cultivo de práctica cultural actualizado")
                        st.rerun()

            (
                opciones_prestadores_editor,
                proveedor_id_a_etiqueta,
                proveedor_etiqueta_a_id
            ) = _opciones_proveedores_editor(proveedores_edicion_practicas)
            editor_practicas = practicas_guardadas.copy()
            if practicas_tiene_proveedor:

                editor_practicas["prestador"] = (
                    editor_practicas["proveedor_id"].apply(
                        lambda valor: _etiqueta_proveedor_desde_id(
                            valor,
                            proveedor_id_a_etiqueta
                        )
                    )
                )

            columnas_editor_ocultas = [
                "campana_id",
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
                "maquinaria_id",
                "operario_id",
                "proveedor_id",
                "cultivos_detalle",
                "parcelas_detalle",
                "superficie_detalle",
                "tiene_detalle_multicultivo",
            ]

            if not practicas_tiene_codigo_siex:

                columnas_editor_ocultas.append("codigo_actuacion_siex")

            if not practicas_tiene_maquinaria:

                columnas_editor_ocultas.append("maquinaria")

            if not practicas_tiene_operario:

                columnas_editor_ocultas.append("operario")

            if not practicas_tiene_proveedor:

                columnas_editor_ocultas.append("prestador")

            editor_practicas = editor_practicas.drop(
                columns=columnas_editor_ocultas,
                errors="ignore"
            )
            editor_practicas["fecha"] = pd.to_datetime(
                editor_practicas["fecha"],
                errors="coerce"
            )

            columnas_editor = [
                "id",
                "fecha",
                "cultivo_mostrado",
                "parcelas",
                "labor",
            ]

            if practicas_tiene_codigo_siex:

                columnas_editor.append("codigo_actuacion_siex")

            columnas_editor.append("superficie")

            if practicas_tiene_maquinaria:

                columnas_editor.append("maquinaria")

            if practicas_tiene_operario:

                columnas_editor.append("operario")

            if practicas_tiene_proveedor:

                columnas_editor.append("prestador")

            columnas_editor.append("observaciones")

            practicas_editadas = st.data_editor(
                editor_practicas,
                num_rows="fixed",
                disabled=[
                    "id",
                    "cultivo_mostrado",
                    "parcelas",
                    "maquinaria",
                    "operario",
                ],
                hide_index=True,
                use_container_width=True,
                column_order=columnas_editor,
                column_config={
                    "id": st.column_config.NumberColumn("id", disabled=True),
                    "labor": st.column_config.SelectboxColumn(
                        "labor",
                        options=labores_culturales
                    ),
                    "fecha": st.column_config.DateColumn(
                        "fecha",
                        format="DD/MM/YYYY",
                        required=True
                    ),
                    "cultivo_mostrado": st.column_config.TextColumn(
                        "cultivo",
                        disabled=True
                    ),
                    "prestador": st.column_config.SelectboxColumn(
                        "prestador",
                        options=opciones_prestadores_editor
                    ),
                    "codigo_actuacion_siex": st.column_config.TextColumn(
                        "código actuación SIEX"
                    ),
                },
                key="editor_practicas_culturales"
            )

            confirmar_practicas = st.checkbox(
                "Confirmo que quiero guardar los cambios de prácticas culturales",
                key="confirmar_practicas_culturales"
            )

            if st.button(
                "💾 Guardar cambios de prácticas culturales",
                key="guardar_cambios_practicas_culturales"
            ):

                ids_originales = editor_practicas["id"].astype(int).tolist()
                ids_editados = practicas_editadas["id"].astype(int).tolist()

                if not confirmar_practicas:

                    st.warning("Marca la confirmación antes de guardar")

                elif ids_editados != ids_originales:

                    st.warning("No se permite añadir, borrar ni cambiar registros")

                else:

                    practicas_para_guardar = practicas_editadas.copy()

                    for columna in [
                        "labor",
                        "codigo_actuacion_siex",
                        "observaciones"
                    ]:

                        if columna in practicas_para_guardar.columns:

                            practicas_para_guardar[columna] = (
                                practicas_para_guardar[columna]
                                .fillna("")
                                .astype(str)
                                .str.strip()
                            )

                    practicas_para_guardar["superficie"] = pd.to_numeric(
                        practicas_para_guardar["superficie"],
                        errors="coerce"
                    )
                    if practicas_tiene_proveedor:

                        practicas_para_guardar["proveedor_id"] = (
                            practicas_para_guardar["prestador"]
                            .fillna("Sin prestador externo")
                            .astype(str)
                            .str.strip()
                            .map(proveedor_etiqueta_a_id)
                        )

                    else:

                        practicas_para_guardar["proveedor_id"] = None

                    practicas_para_guardar["fecha"] = pd.to_datetime(
                        practicas_para_guardar["fecha"],
                        errors="coerce"
                    )

                    campos_invalidos = (
                        practicas_para_guardar["fecha"].isna()
                        | (practicas_para_guardar["labor"] == "")
                        | practicas_para_guardar["superficie"].isna()
                        | (practicas_para_guardar["superficie"] < 0)
                    )

                    if campos_invalidos.any():

                        st.warning("Revisa fecha, labor y superficie")

                    else:

                        conn = conectar()

                        try:

                            for _, fila in practicas_para_guardar.iterrows():

                                _actualizar_practica_compatible(
                                    conn,
                                    int(fila["id"]),
                                    {
                                        "fecha": (
                                            fila["fecha"]
                                            .date()
                                            .isoformat()
                                        ),
                                        "labor": fila["labor"],
                                        "codigo_actuacion_siex": fila.get(
                                            "codigo_actuacion_siex",
                                            "",
                                        ),
                                        "superficie": float(fila["superficie"]),
                                        "proveedor_id": (
                                            None
                                            if pd.isna(fila["proveedor_id"])
                                            else int(fila["proveedor_id"])
                                        ),
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

                        st.success("Cambios de prácticas culturales guardados")
                        st.rerun()




    if seccion_practicas == "🗑️ Borrar":

        st.subheader("Borrado seguro")
        tabla_hija_practicas = (
            "practicas_culturales_parcelas"
            if _columnas_tabla("practicas_culturales_parcelas")
            else "practica_parcelas"
        )

        borrar_registros_seguro(
            "practicas_culturales",
            "id",
            practicas_guardadas,
            "prácticas culturales",
            tablas_hijas=[
                ("practicas_culturales_cultivos", "practica_id"),
                (tabla_hija_practicas, "practica_id"),
            ],
            campo_descripcion="labor",
            key="practicas_culturales"
        )
