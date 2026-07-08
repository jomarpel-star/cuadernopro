from datetime import date, datetime
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
    obtener_campana_por_intervalo,
    parsear_fecha_es,
    preparar_columnas_fecha_tabla,
    validar_fecha_en_campana,
    validar_intervalo_en_campana,
)
from core.filtros import mostrar_filtros_dataframe
from core.ui_tablas import (
    preparar_column_config_visual,
    preparar_dataframe_visual,
)
from services.recetas import (
    eliminar_archivo_receta,
    eliminar_documento_receta,
    guardar_recetas_pdf,
    leer_recetas_tratamientos,
    ruta_receta_absoluta,
)


MATERIALES_ANALISIS = [
    "Hojas",
    "Fruto",
    "Árbol/planta",
    "Suelo",
    "Agua",
    "Cosecha",
    "Otro",
]


RESULTADOS_ANALISIS = [
    "Sin residuos detectados",
    "Residuos dentro de límite",
    "Residuos fuera de límite",
    "Pendiente de resultado",
    "Otro",
]


OPCIONES_EFICACIA = {
    "Sin evaluar": "",
    "Buena (B)": "B",
    "Regular (R)": "R",
    "Mala (M)": "M",
}
VALORES_EFICACIA = set(OPCIONES_EFICACIA.values())


def _normalizar_eficacia(valor):

    texto = "" if valor is None else str(valor).strip().upper()

    if texto in {"BUENA", "BUENO"}:

        return "B"

    if texto == "REGULAR":

        return "R"

    if texto in {"MALA", "MALO"}:

        return "M"

    return texto if texto in VALORES_EFICACIA else ""


def _etiqueta_eficacia(valor):

    codigo = _normalizar_eficacia(valor)

    for etiqueta, valor_opcion in OPCIONES_EFICACIA.items():

        if valor_opcion == codigo:

            return etiqueta

    return "Sin evaluar"


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


def _valor_texto_columna(tabla, columna, columnas, defecto="''"):

    if columna in columnas:

        return f"COALESCE({tabla}.{columna},{defecto})"

    return defecto


def _valor_numerico_columna(tabla, columna, columnas, defecto="NULL"):

    if columna in columnas:

        return f"{tabla}.{columna}"

    return defecto


def _coalesce_sql(expresiones):

    if len(expresiones) == 1:

        return expresiones[0]

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


def _expr_producto_registro(columnas_productos, tabla="productos_fito"):

    if "registro" in columnas_productos:

        return f"COALESCE({tabla}.registro,'')"

    if "numero_registro" in columnas_productos:

        return f"COALESCE({tabla}.numero_registro,'')"

    return "''"


def _expr_persona_carnet(columnas_personas, tabla="personas"):

    if "carnet_fitosanitario" in columnas_personas:

        return f"COALESCE({tabla}.carnet_fitosanitario,'')"

    if "carnet_aplicador" in columnas_personas:

        return f"COALESCE({tabla}.carnet_aplicador,'')"

    return "''"


def _texto_recetas(cantidad):

    cantidad = int(cantidad or 0)

    if cantidad == 0:

        return "Sin receta"

    if cantidad == 1:

        return "1 receta"

    return f"{cantidad} recetas"


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


def _formatear_tratamiento_recetas(valor, dataframe):

    fila = dataframe[dataframe["id"].astype(int) == int(valor)]

    if fila.empty:

        return f"Tratamiento {valor}"

    fila = fila.iloc[0]
    periodo = (
        f"{formatear_fecha_es(fila.get('fecha_inicio'))} a "
        f"{formatear_fecha_es(fila.get('fecha_fin'))}"
    )
    producto = _texto(fila.get("producto"))
    plaga = _texto(fila.get("plaga"))
    detalle = " · ".join(parte for parte in [producto, plaga] if parte)

    if detalle:

        return f"#{int(valor)} · {periodo} · {detalle}"

    return f"#{int(valor)} · {periodo}"


def _leer_campanas_analisis():

    return leer(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin,activa
        FROM campanas
        ORDER BY fecha_inicio DESC,id DESC
        """
    )


def _leer_parcelas_analisis():

    return leer(
        """
        SELECT id,nombre,poligono,parcela,recinto
        FROM parcelas
        ORDER BY nombre,poligono,parcela,recinto,id
        """
    )


def _etiqueta_parcela(fila):

    nombre = _texto(fila.get("nombre"))
    referencia = "-".join(
        parte
        for parte in [
            _texto(fila.get("poligono")),
            _texto(fila.get("parcela")),
            _texto(fila.get("recinto")),
        ]
        if parte
    )

    if nombre and referencia:

        return f"{nombre} - {referencia}"

    return nombre or referencia or f"Parcela {int(fila['id'])}"


def _ids_parcelas_desde_texto(valor):

    texto = _texto(valor)

    if not texto:

        return []

    ids = []

    for parte in texto.split(","):

        parte = parte.strip()

        if parte.isdigit():

            ids.append(int(parte))

    return ids


def _parcelas_a_texto(ids_parcelas):

    ids_limpios = []

    for parcela_id in ids_parcelas or []:

        try:

            ids_limpios.append(int(parcela_id))

        except (TypeError, ValueError):

            continue

    return ",".join(str(parcela_id) for parcela_id in ids_limpios)


def _resumen_parcelas(valor, parcelas):

    ids = _ids_parcelas_desde_texto(valor)

    if not ids:

        return _texto(valor)

    parcelas_por_id = {
        int(fila["id"]): _etiqueta_parcela(fila)
        for _, fila in parcelas.iterrows()
    }
    return ", ".join(
        parcelas_por_id.get(parcela_id, str(parcela_id))
        for parcela_id in ids
    )


def _preparar_cultivos_analisis(cultivos):

    if cultivos.empty:

        return cultivos.copy()

    cultivos_preparados = cultivos.copy()

    for columna in ["especie", "variedad", "sistema", "parcela"]:

        if columna not in cultivos_preparados:

            cultivos_preparados[columna] = ""

        cultivos_preparados[columna] = (
            cultivos_preparados[columna].fillna("").astype(str).str.strip()
        )

    cultivos_preparados["etiqueta"] = (
        cultivos_preparados["especie"]
        + " / "
        + cultivos_preparados["variedad"]
        + " / "
        + cultivos_preparados["sistema"]
    )
    cultivos_preparados["etiqueta"] = (
        cultivos_preparados["etiqueta"]
        .str.replace(r"\s*/\s*/", " / ", regex=True)
        .str.strip(" /")
    )
    cultivos_preparados["etiqueta"] = cultivos_preparados.apply(
        lambda fila: (
            f"{fila['etiqueta']} - {fila['parcela']}"
            if _texto(fila["parcela"])
            else fila["etiqueta"]
        ) or f"Cultivo {int(fila['id'])}",
        axis=1
    )
    return cultivos_preparados.drop_duplicates(subset=["id"]).copy()


def _etiqueta_cultivo(cultivos, cultivo_id):

    if cultivo_id is None or cultivos.empty:

        return "Sin cultivo"

    fila = cultivos[cultivos["id"].astype(int) == int(cultivo_id)]

    if fila.empty:

        return f"Cultivo {cultivo_id}"

    return _texto(fila.iloc[0]["etiqueta"]) or f"Cultivo {cultivo_id}"


def _nombre_cultivo_fila(fila):

    partes = [
        _texto(fila.get("especie")),
        _texto(fila.get("variedad")),
        _texto(fila.get("sistema")),
    ]

    return " / ".join(parte for parte in partes if parte)


def _formatear_hectareas(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return ""

    return f"{float(numero):.2f} ha"


def _etiqueta_cultivo_v6(fila):

    if fila is None:

        return "Sin cultivo estructurado"

    partes = []
    campana = _texto(fila.get("campana"))
    nombre = _nombre_cultivo_fila(fila) or f"Cultivo {int(fila['id'])}"
    superficie = _formatear_hectareas(fila.get("superficie"))
    ano_plantacion = _entero_o_none(fila.get("ano_plantacion"))
    codigo_siex = _texto(fila.get("codigo_siex"))

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


def _cultivo_por_id(cultivos, cultivo_id):

    cultivo_id = _entero_o_none(cultivo_id)

    if cultivo_id is None or cultivos.empty:

        return None

    coincidencias = cultivos[cultivos["id"].astype(int) == int(cultivo_id)]

    if coincidencias.empty:

        return None

    return coincidencias.iloc[0]


def _selector_cultivo_tratamiento(
    cultivos,
    key,
    campana_id=None,
    valor_actual=None,
    placeholder="Selecciona cultivo...",
    seleccionar_primero=False,
):

    ids = []

    if not cultivos.empty:

        cultivos_ordenados = cultivos.copy()
        campana_id = _entero_o_none(campana_id)

        if campana_id is not None and "campana_id" in cultivos_ordenados:

            cultivos_ordenados["prioridad_campana"] = (
                pd.to_numeric(
                    cultivos_ordenados["campana_id"],
                    errors="coerce"
                ) != campana_id
            ).astype(int)
            cultivos_ordenados = cultivos_ordenados.sort_values(
                by=["prioridad_campana", "campana", "especie", "id"]
            )

        ids = cultivos_ordenados["id"].dropna().astype(int).tolist()

    opciones = [None] + ids
    valor_actual = _entero_o_none(valor_actual)

    if valor_actual in opciones:

        indice = opciones.index(valor_actual)

    elif ids and seleccionar_primero:

        indice = 1

    else:

        indice = 0

    return st.selectbox(
        "Cultivo",
        opciones,
        index=indice,
        format_func=lambda valor: (
            placeholder
            if valor is None
            else _etiqueta_cultivo_v6(_cultivo_por_id(cultivos, valor))
        ),
        key=key,
    )


def _opciones_cultivo(cultivos):

    if cultivos.empty:

        return [None]

    return [None] + cultivos["id"].astype(int).tolist()


def _etiqueta_producto_fito(fila):

    if fila is None:

        return "Sin producto estructurado"

    nombre = _texto(fila.get("nombre")) or f"Producto {int(fila['id'])}"
    registro = _texto(fila.get("registro"))
    materia = _texto(fila.get("materia_activa"))
    partes = [nombre]

    if registro:

        partes.append(f"Nº registro {registro}")

    if materia:

        partes.append(materia)

    return " — ".join(partes)


def _fila_por_id(dataframe, registro_id):

    registro_id = _entero_o_none(registro_id)

    if registro_id is None or dataframe is None or dataframe.empty:

        return None

    coincidencias = dataframe[dataframe["id"].astype(int) == int(registro_id)]

    if coincidencias.empty:

        return None

    return coincidencias.iloc[0]


def _etiqueta_persona(fila):

    if fila is None:

        return "Sin aplicador"

    nombre = _texto(fila.get("nombre")) or f"Persona {int(fila['id'])}"
    nif = _texto(fila.get("nif"))
    carnet = _texto(fila.get("carnet_fitosanitario"))
    partes = [nombre]

    if nif:

        partes.append(f"NIF {nif}")

    if carnet:

        partes.append(f"Carné {carnet}")

    return " — ".join(partes)


def _etiqueta_equipo_aplicacion(fila):

    if fila is None:

        return "Sin equipo"

    nombre = _texto(fila.get("nombre")) or f"Equipo {int(fila['id'])}"
    tipo = _texto(fila.get("tipo")) or "Equipo aplicación"
    marca = _texto(fila.get("marca"))
    modelo = _texto(fila.get("modelo"))
    detalle = " ".join(parte for parte in [marca, modelo] if parte)

    if detalle and detalle.lower() not in nombre.lower():

        nombre = f"{nombre} — {detalle}"

    return f"{nombre} — {tipo}"


def _parcelas_para_cultivo_tratamiento(cultivo, cultivo_parcelas):

    if cultivo is None:

        return pd.DataFrame()

    cultivo_id = int(cultivo["id"])

    if not cultivo_parcelas.empty:

        parcelas_v6 = cultivo_parcelas[
            cultivo_parcelas["cultivo_id"].astype(int) == cultivo_id
        ].copy()

        if not parcelas_v6.empty:

            return parcelas_v6

    parcela_id = _entero_o_none(cultivo.get("parcela_id"))

    if parcela_id is None:

        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "cultivo_id": cultivo_id,
                "parcela_id": parcela_id,
                "parcela": _texto(cultivo.get("parcela")),
                "poligono": _texto(cultivo.get("poligono")),
                "numero_parcela": _texto(cultivo.get("numero_parcela")),
                "recinto": _texto(cultivo.get("recinto")),
                "superficie_sigpac": cultivo.get("superficie_sigpac"),
            }
        ]
    )


def _leer_productos_fito_tratamiento(conn=None):

    columnas = (
        _columnas_tabla_conn(conn, "productos_fito")
        if conn is not None
        else _columnas_tabla("productos_fito")
    )

    if not columnas:

        return pd.DataFrame()

    expr_nombre = _valor_texto_columna("productos_fito", "nombre", columnas)
    expr_registro = _expr_producto_registro(columnas)
    expr_materia = _valor_texto_columna(
        "productos_fito",
        "materia_activa",
        columnas,
    )
    expr_dosis = _valor_texto_columna("productos_fito", "dosis", columnas)
    expr_plazo = _valor_texto_columna(
        "productos_fito",
        "plazo_seguridad",
        columnas,
    )
    expr_activo = (
        "COALESCE(productos_fito.activo,1)"
        if "activo" in columnas
        else "1"
    )

    return _leer_dataframe(
        f"""
        SELECT
            id,
            {expr_registro} AS registro,
            {expr_registro} AS numero_registro,
            {expr_nombre} AS nombre,
            {expr_materia} AS materia_activa,
            {expr_dosis} AS dosis,
            {expr_plazo} AS plazo_seguridad,
            {expr_activo} AS activo
        FROM productos_fito
        ORDER BY nombre,id
        """,
        conn=conn,
    )


def _leer_cultivos_tratamiento(conn=None):

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
    join_parcelas = (
        "LEFT JOIN parcelas ON parcelas.id = cultivos.parcela_id"
        if "parcela_id" in columnas_cultivos
        else ""
    )
    expr_poligono = (
        "COALESCE(parcelas.poligono,'')"
        if "parcela_id" in columnas_cultivos
        else "''"
    )
    expr_numero_parcela = (
        "COALESCE(parcelas.parcela,'')"
        if "parcela_id" in columnas_cultivos
        else "''"
    )
    expr_recinto = (
        "COALESCE(parcelas.recinto,'')"
        if "parcela_id" in columnas_cultivos
        else "''"
    )
    expr_superficie_sigpac = (
        "parcelas.superficie_sigpac"
        if "parcela_id" in columnas_cultivos
        else "NULL"
    )
    expr_parcela = (
        """
        TRIM(
            CASE
                WHEN IFNULL(parcelas.nombre,'') != ''
                THEN parcelas.nombre || ' - '
                ELSE ''
            END
            || IFNULL(parcelas.poligono,'')
            || '-'
            || IFNULL(parcelas.parcela,'')
            || '-'
            || IFNULL(parcelas.recinto,'')
        )
        """
        if "parcela_id" in columnas_cultivos
        else "''"
    )

    cultivos = _leer_dataframe(
        f"""
        SELECT
            cultivos.id,
            {expr_campana_id} AS campana_id,
            COALESCE(campanas.nombre,'') AS campana,
            {expr_parcela_id} AS parcela_id,
            {expr_nombre} AS especie,
            {expr_nombre} AS nombre,
            {expr_variedad} AS variedad,
            {expr_sistema} AS sistema,
            {expr_codigo_siex} AS codigo_siex,
            {expr_superficie} AS superficie,
            {expr_ano_plantacion} AS ano_plantacion,
            {expr_poligono} AS poligono,
            {expr_numero_parcela} AS numero_parcela,
            {expr_recinto} AS recinto,
            {expr_superficie_sigpac} AS superficie_sigpac,
            {expr_parcela} AS parcela,
            {expr_activo} AS activo
        FROM cultivos
        LEFT JOIN campanas ON campanas.id = cultivos.campana_id
        {join_parcelas}
        ORDER BY campanas.fecha_inicio DESC, especie, variedad, cultivos.id
        """,
        conn=conn,
    )
    return cultivos


def _df_vacio_cultivo_parcelas():

    return pd.DataFrame(
        columns=[
            "cultivo_id",
            "parcela_id",
            "nombre",
            "poligono",
            "numero_parcela",
            "recinto",
            "superficie_sigpac",
            "superficie",
            "parcela",
        ]
    )


def _leer_cultivo_parcelas_tratamiento(conn=None):

    if conn is not None:

        tiene_tabla = _tabla_existe_conn(conn, "cultivo_parcelas")
        tiene_parcelas = _tabla_existe_conn(conn, "parcelas")

    else:

        conn_tmp = conectar()

        try:

            tiene_tabla = _tabla_existe_conn(conn_tmp, "cultivo_parcelas")
            tiene_parcelas = _tabla_existe_conn(conn_tmp, "parcelas")

        finally:

            conn_tmp.close()

    if not tiene_tabla or not tiene_parcelas:

        return _df_vacio_cultivo_parcelas()

    return _leer_dataframe(
        """
        SELECT
        cultivo_parcelas.cultivo_id,
        parcelas.id AS parcela_id,
        parcelas.nombre,
        parcelas.poligono,
        parcelas.parcela AS numero_parcela,
        parcelas.recinto,
        parcelas.superficie_sigpac,
        cultivo_parcelas.superficie,
        TRIM(
            CASE
                WHEN IFNULL(parcelas.nombre,'') != ''
                THEN parcelas.nombre || ' - '
                ELSE ''
            END
            || IFNULL(parcelas.poligono,'')
            || '-'
            || IFNULL(parcelas.parcela,'')
            || '-'
            || IFNULL(parcelas.recinto,'')
        ) parcela
        FROM cultivo_parcelas
        INNER JOIN parcelas
        ON parcelas.id=cultivo_parcelas.parcela_id
        ORDER BY cultivo_parcelas.cultivo_id,parcelas.id
        """,
        conn=conn,
    )


def _leer_personas_tratamiento(conn=None):

    columnas = (
        _columnas_tabla_conn(conn, "personas")
        if conn is not None
        else _columnas_tabla("personas")
    )

    if not columnas:

        return pd.DataFrame()

    expr_nombre = _valor_texto_columna("personas", "nombre", columnas)
    expr_nif = _valor_texto_columna("personas", "nif", columnas)
    expr_rol = _valor_texto_columna("personas", "rol", columnas)
    expr_carnet = _expr_persona_carnet(columnas)
    expr_activo = (
        "COALESCE(personas.activo,1)"
        if "activo" in columnas
        else "1"
    )

    return _leer_dataframe(
        f"""
        SELECT
            id,
            {expr_nombre} AS nombre,
            {expr_nif} AS nif,
            {expr_rol} AS rol,
            {expr_carnet} AS carnet_fitosanitario,
            {expr_carnet} AS carnet_aplicador,
            {expr_activo} AS activo
        FROM personas
        ORDER BY
        CASE
            WHEN {expr_rol}='Aplicador fitosanitario' THEN 0
            ELSE 1
        END,
        nombre
        """,
        conn=conn,
    )


def _leer_equipos_aplicacion_tratamiento(conn=None):

    columnas = (
        _columnas_tabla_conn(conn, "equipos_aplicacion")
        if conn is not None
        else _columnas_tabla("equipos_aplicacion")
    )

    if not columnas:

        return pd.DataFrame()

    expr_nombre = _valor_texto_columna("equipos_aplicacion", "nombre", columnas)
    expr_tipo = _valor_texto_columna("equipos_aplicacion", "tipo", columnas)
    expr_marca = _valor_texto_columna("equipos_aplicacion", "marca", columnas)
    expr_modelo = _valor_texto_columna("equipos_aplicacion", "modelo", columnas)
    expr_roma = _valor_texto_columna(
        "equipos_aplicacion",
        "numero_roma",
        columnas,
    )
    expr_serie = _valor_texto_columna(
        "equipos_aplicacion",
        "numero_serie",
        columnas,
    )
    expr_activo = (
        "COALESCE(equipos_aplicacion.activo,1)"
        if "activo" in columnas
        else "1"
    )

    return _leer_dataframe(
        f"""
        SELECT
            id,
            {expr_nombre} AS nombre,
            {expr_tipo} AS tipo,
            {expr_marca} AS marca,
            {expr_modelo} AS modelo,
            {expr_roma} AS numero_roma,
            {expr_serie} AS numero_serie,
            {expr_activo} AS activo
        FROM equipos_aplicacion
        ORDER BY nombre,id
        """,
        conn=conn,
    )


def _insertar_relaciones_tratamiento_parcelas(conn, tratamiento_id, parcelas):

    if not _tabla_existe_conn(conn, "tratamiento_parcelas"):

        return

    columnas = _columnas_tabla_conn(conn, "tratamiento_parcelas")

    if not {"tratamiento_id", "parcela_id"}.issubset(columnas):

        return

    ahora = datetime.now().isoformat(timespec="seconds")

    for parcela in parcelas or []:

        if isinstance(parcela, dict):

            parcela_id = parcela.get("parcela_id")
            superficie = parcela.get("superficie")

        else:

            parcela_id = parcela
            superficie = None

        valores = {
            "tratamiento_id": int(tratamiento_id),
            "parcela_id": int(parcela_id),
        }
        _anadir_si_existe(valores, columnas, "superficie", superficie)
        _anadir_si_existe(valores, columnas, "created_at", ahora)
        _anadir_si_existe(valores, columnas, "updated_at", ahora)
        nombres = list(valores)
        conn.execute(
            f"""
            INSERT INTO tratamiento_parcelas
            ({','.join(nombres)})
            VALUES ({','.join(['?'] * len(nombres))})
            """,
            [valores[columna] for columna in nombres],
        )


def _insertar_tratamiento_compatible(
    conn,
    datos,
    parcelas=None,
    detalles_cultivos=None,
):

    columnas = _columnas_tabla_conn(conn, "tratamientos")
    valores = {}
    detalles_normalizados = _normalizar_detalles_actuacion(detalles_cultivos)
    fecha_inicio = datos.get("fecha_inicio") or datos.get("fecha")
    fecha_fin = datos.get("fecha_fin") or fecha_inicio
    plaga_motivo = _texto(
        datos.get("plaga_motivo")
        or datos.get("plaga")
        or datos.get("problema")
    )
    equipo_aplicacion_id = _entero_o_none(
        datos.get("equipo_aplicacion_id", datos.get("equipo_id"))
    )
    ahora = datetime.now().isoformat(timespec="seconds")

    _anadir_si_existe(valores, columnas, "campana_id", datos.get("campana_id"))
    _anadir_si_existe(valores, columnas, "cultivo_id", datos.get("cultivo_id"))
    _anadir_si_existe(valores, columnas, "fecha_inicio", fecha_inicio)
    _anadir_si_existe(valores, columnas, "fecha_fin", fecha_fin)
    _anadir_si_existe(valores, columnas, "fecha", fecha_inicio)
    _anadir_si_existe(valores, columnas, "producto_id", datos.get("producto_id"))
    _anadir_si_existe(
        valores,
        columnas,
        "producto",
        _texto(datos.get("producto")),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "aplicador_id",
        datos.get("aplicador_id"),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "aplicador",
        _texto(datos.get("aplicador")),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "equipo_aplicacion_id",
        equipo_aplicacion_id,
    )
    _anadir_si_existe(valores, columnas, "equipo_id", equipo_aplicacion_id)
    _anadir_si_existe(
        valores,
        columnas,
        "maquinaria_id",
        datos.get("maquinaria_id"),
    )
    _anadir_si_existe(valores, columnas, "equipo", _texto(datos.get("equipo")))
    _anadir_si_existe(valores, columnas, "plaga_motivo", plaga_motivo)
    _anadir_si_existe(valores, columnas, "plaga", plaga_motivo)
    _anadir_si_existe(valores, columnas, "problema", plaga_motivo)
    _anadir_si_existe(
        valores,
        columnas,
        "justificacion",
        _texto(datos.get("justificacion")),
    )
    _anadir_si_existe(valores, columnas, "dosis", _texto(datos.get("dosis")))
    _anadir_si_existe(valores, columnas, "caldo", datos.get("caldo"))
    _anadir_si_existe(
        valores,
        columnas,
        "superficie_tratada",
        datos.get("superficie_tratada"),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "plazo_seguridad",
        _texto(datos.get("plazo_seguridad")),
    )
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_recoleccion_segura",
        _texto(datos.get("fecha_recoleccion_segura")),
    )
    condiciones = _texto(
        datos.get("condiciones_meteorologicas")
        or datos.get("condiciones")
    )
    _anadir_si_existe(valores, columnas, "condiciones", condiciones)
    _anadir_si_existe(
        valores,
        columnas,
        "condiciones_meteorologicas",
        condiciones,
    )
    _anadir_si_existe(
        valores,
        columnas,
        "eficacia",
        _normalizar_eficacia(datos.get("eficacia")),
    )
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
            "La tabla tratamientos no tiene columnas utiles"
        )

    nombres = list(valores)
    cursor = conn.execute(
        f"""
        INSERT INTO tratamientos
        ({','.join(nombres)})
        VALUES ({','.join(['?'] * len(nombres))})
        """,
        [valores[columna] for columna in nombres],
    )
    tratamiento_id = int(cursor.lastrowid)
    parcelas_compatibles = (
        parcelas
        if parcelas is not None
        else _parcelas_compatibilidad_detalles(detalles_normalizados)
    )
    _insertar_relaciones_tratamiento_parcelas(
        conn,
        tratamiento_id,
        parcelas_compatibles,
    )
    _insertar_detalles_actuacion(
        conn,
        "tratamiento_cultivos",
        "tratamiento_id",
        tratamiento_id,
        detalles_normalizados,
    )
    return tratamiento_id


def _actualizar_tratamiento_compatible(conn, tratamiento_id, datos):

    columnas = _columnas_tabla_conn(conn, "tratamientos")
    valores = {}
    fecha_inicio = datos.get("fecha_inicio", datos.get("fecha"))
    fecha_fin = datos.get("fecha_fin", fecha_inicio)
    plaga_motivo = _texto(
        datos.get("plaga_motivo")
        or datos.get("plaga")
        or datos.get("problema")
    )

    for columna in (
        "campana_id",
        "cultivo_id",
        "producto_id",
        "aplicador_id",
        "maquinaria_id",
        "caldo",
        "superficie_tratada",
    ):

        if columna in columnas and columna in datos:

            valores[columna] = datos[columna]

    if "fecha_inicio" in columnas and fecha_inicio is not None:

        valores["fecha_inicio"] = fecha_inicio

    if "fecha_fin" in columnas and fecha_fin is not None:

        valores["fecha_fin"] = fecha_fin

    if "fecha" in columnas and fecha_inicio is not None:

        valores["fecha"] = fecha_inicio

    equipo_aplicacion_id = _entero_o_none(
        datos.get("equipo_aplicacion_id", datos.get("equipo_id"))
    )

    if "equipo_aplicacion_id" in columnas and (
        "equipo_aplicacion_id" in datos
        or "equipo_id" in datos
    ):

        valores["equipo_aplicacion_id"] = equipo_aplicacion_id

    if "equipo_id" in columnas and (
        "equipo_aplicacion_id" in datos
        or "equipo_id" in datos
    ):

        valores["equipo_id"] = equipo_aplicacion_id

    for columna in (
        "producto",
        "aplicador",
        "equipo",
        "justificacion",
        "dosis",
        "plazo_seguridad",
        "fecha_recoleccion_segura",
        "observaciones",
    ):

        if columna in columnas and columna in datos:

            valores[columna] = _texto(datos.get(columna))

    for columna in ("plaga_motivo", "plaga", "problema"):

        if columna in columnas and (
            "plaga_motivo" in datos
            or "plaga" in datos
            or "problema" in datos
        ):

            valores[columna] = plaga_motivo

    condiciones = _texto(
        datos.get("condiciones_meteorologicas")
        or datos.get("condiciones")
    )

    for columna in ("condiciones", "condiciones_meteorologicas"):

        if columna in columnas and (
            "condiciones_meteorologicas" in datos
            or "condiciones" in datos
        ):

            valores[columna] = condiciones

    if "eficacia" in columnas and "eficacia" in datos:

        valores["eficacia"] = _normalizar_eficacia(datos.get("eficacia"))

    if "updated_at" in columnas:

        valores["updated_at"] = datetime.now().isoformat(timespec="seconds")

    if not valores:

        return

    asignaciones = ",".join(f"{columna}=?" for columna in valores)
    conn.execute(
        f"UPDATE tratamientos SET {asignaciones} WHERE id=?",
        [valores[columna] for columna in valores] + [int(tratamiento_id)],
    )


def _fecha_defecto_analisis(campanas, campana_id):

    fecha_defecto = date.today()
    campana = campanas[campanas["id"].astype(int) == int(campana_id)]

    if campana.empty:

        return fecha_defecto

    inicio = pd.to_datetime(campana.iloc[0]["fecha_inicio"], errors="coerce")
    fin = pd.to_datetime(campana.iloc[0]["fecha_fin"], errors="coerce")

    if (
        not pd.isna(inicio)
        and not pd.isna(fin)
        and not inicio.date() <= fecha_defecto <= fin.date()
    ):

        return inicio.date()

    return fecha_defecto


def _leer_analisis_fitosanitarios(parcelas):

    analisis = leer(
        """
        SELECT
        analisis_fitosanitarios.id,
        analisis_fitosanitarios.campana_id,
        COALESCE(campanas.nombre,'') AS campana,
        analisis_fitosanitarios.fecha,
        analisis_fitosanitarios.material_analizado,
        analisis_fitosanitarios.cultivo_id,
        TRIM(
            COALESCE(cultivos.especie,'') || ' / ' ||
            COALESCE(cultivos.variedad,'') || ' / ' ||
            COALESCE(cultivos.sistema,'')
        ) AS cultivo,
        analisis_fitosanitarios.parcelas,
        analisis_fitosanitarios.boletin_numero,
        analisis_fitosanitarios.laboratorio,
        analisis_fitosanitarios.sustancias_detectadas,
        analisis_fitosanitarios.resultado,
        analisis_fitosanitarios.observaciones,
        analisis_fitosanitarios.documento
        FROM analisis_fitosanitarios
        LEFT JOIN campanas
        ON campanas.id = analisis_fitosanitarios.campana_id
        LEFT JOIN cultivos
        ON cultivos.id = analisis_fitosanitarios.cultivo_id
        ORDER BY analisis_fitosanitarios.fecha DESC,
        analisis_fitosanitarios.id DESC
        """
    )

    if analisis.empty:

        return analisis

    analisis["parcelas_resumen"] = analisis["parcelas"].apply(
        lambda valor: _resumen_parcelas(valor, parcelas)
    )
    analisis["cultivo"] = analisis["cultivo"].fillna("").astype(str).str.strip(" /")
    return analisis


def _filtrar_analisis(analisis, campanas):

    if analisis.empty:

        return analisis

    filtros_col1, filtros_col2, filtros_col3 = st.columns(3)

    with filtros_col1:

        campanas_opciones = ["Todas"] + campanas["nombre"].fillna("").tolist()
        campana_filtro = st.selectbox(
            "Campaña",
            campanas_opciones,
            key="analisis_filtro_campana"
        )
        fecha_desde_texto = st.text_input(
            "Desde",
            placeholder="DD/MM/AAAA",
            key="analisis_filtro_desde"
        )

    with filtros_col2:

        materiales = ["Todos"] + MATERIALES_ANALISIS
        material_filtro = st.selectbox(
            "Material analizado",
            materiales,
            key="analisis_filtro_material"
        )
        fecha_hasta_texto = st.text_input(
            "Hasta",
            placeholder="DD/MM/AAAA",
            key="analisis_filtro_hasta"
        )

    with filtros_col3:

        cultivos_opciones = ["Todos"] + sorted(
            valor
            for valor in analisis["cultivo"].fillna("").astype(str).unique()
            if valor.strip()
        )
        cultivo_filtro = st.selectbox(
            "Cultivo",
            cultivos_opciones,
            key="analisis_filtro_cultivo"
        )
        texto_filtro = st.text_input(
            "Texto libre",
            key="analisis_filtro_texto"
        )

    filtrados = analisis.copy()

    if campana_filtro != "Todas":

        filtrados = filtrados[filtrados["campana"] == campana_filtro]

    if material_filtro != "Todos":

        filtrados = filtrados[
            filtrados["material_analizado"] == material_filtro
        ]

    if cultivo_filtro != "Todos":

        filtrados = filtrados[filtrados["cultivo"] == cultivo_filtro]

    for etiqueta, texto, operador in [
        ("Desde", fecha_desde_texto, ">="),
        ("Hasta", fecha_hasta_texto, "<="),
    ]:

        if not texto.strip():

            continue

        try:

            fecha_iso = parsear_fecha_es(texto)

        except ValueError:

            st.warning(f"{etiqueta}: la fecha debe tener formato DD/MM/AAAA")
            continue

        fechas = pd.to_datetime(filtrados["fecha"], errors="coerce")

        if operador == ">=":

            filtrados = filtrados[fechas >= pd.Timestamp(fecha_iso)]

        else:

            filtrados = filtrados[fechas <= pd.Timestamp(fecha_iso)]

    if texto_filtro.strip():

        texto = texto_filtro.strip().casefold()
        columnas_busqueda = [
            "material_analizado",
            "cultivo",
            "parcelas_resumen",
            "boletin_numero",
            "laboratorio",
            "sustancias_detectadas",
            "resultado",
            "observaciones",
            "documento",
        ]
        mascara = pd.Series(False, index=filtrados.index)

        for columna in columnas_busqueda:

            mascara = mascara | (
                filtrados[columna]
                .fillna("")
                .astype(str)
                .str.casefold()
                .str.contains(texto, regex=False)
            )

        filtrados = filtrados[mascara]

    return filtrados


def _mostrar_listado_analisis(analisis, campanas):

    filtrados = _filtrar_analisis(analisis, campanas)
    columnas = [
        "id",
        "campana",
        "fecha",
        "material_analizado",
        "cultivo",
        "parcelas_resumen",
        "boletin_numero",
        "laboratorio",
        "sustancias_detectadas",
        "resultado",
        "observaciones",
        "documento",
    ]
    listado = preparar_dataframe_visual(
        preparar_columnas_fecha_tabla(
            filtrados[columnas].copy(),
            ["fecha"]
        ),
        ocultar_tecnicas=True,
        etiquetas_extra={
            "material_analizado": "Material analizado",
            "parcelas_resumen": "Parcelas",
            "boletin_numero": "Nº boletín",
            "sustancias_detectadas": "Sustancias detectadas",
            "resultado": "Resultado",
            "documento": "Documento",
        }
    )
    st.dataframe(
        listado,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Fecha": st.column_config.DateColumn(
                "Fecha",
                format="DD/MM/YYYY"
            )
        }
    )


def _render_nuevo_analisis(campanas, cultivos, parcelas, campana_actual):

    campana_ids = campanas["id"].astype(int).tolist()
    indice_campana = (
        campana_ids.index(int(campana_actual))
        if int(campana_actual) in campana_ids
        else 0
    )
    campana_id = st.selectbox(
        "Campaña",
        campana_ids,
        index=indice_campana,
        format_func=lambda valor: campanas.loc[
            campanas["id"] == valor,
            "nombre"
        ].iloc[0],
        key="analisis_nuevo_campana"
    )
    fecha_texto = st.text_input(
        "Fecha",
        value=formatear_fecha_es(
            _fecha_defecto_analisis(campanas, campana_id)
        ),
        placeholder="DD/MM/AAAA",
        key="analisis_nuevo_fecha"
    )
    material = st.selectbox(
        "Material analizado",
        MATERIALES_ANALISIS,
        key="analisis_nuevo_material"
    )
    cultivo_id = st.selectbox(
        "Cultivo",
        _opciones_cultivo(cultivos),
        format_func=lambda valor: _etiqueta_cultivo(cultivos, valor),
        key="analisis_nuevo_cultivo"
    )
    ids_parcelas = (
        parcelas["id"].astype(int).tolist()
        if not parcelas.empty
        else []
    )
    parcelas_sel = st.multiselect(
        "Parcelas",
        ids_parcelas,
        format_func=lambda valor: _etiqueta_parcela(
            parcelas[parcelas["id"] == valor].iloc[0]
        ),
        key="analisis_nuevo_parcelas"
    )
    boletin_numero = st.text_input(
        "Nº boletín de análisis",
        key="analisis_nuevo_boletin"
    )
    laboratorio = st.text_input(
        "Laboratorio",
        key="analisis_nuevo_laboratorio"
    )
    sustancias_detectadas = st.text_area(
        "Sustancias activas detectadas",
        key="analisis_nuevo_sustancias"
    )
    resultado = st.selectbox(
        "Resultado",
        RESULTADOS_ANALISIS,
        key="analisis_nuevo_resultado"
    )
    observaciones = st.text_area(
        "Observaciones",
        key="analisis_nuevo_observaciones"
    )
    documento = st.text_input(
        "Documento / referencia del boletín",
        key="analisis_nuevo_documento"
    )
    confirmar_fecha = st.checkbox(
        "Confirmo que quiero guardar el análisis aunque la fecha esté fuera "
        "de la campaña seleccionada",
        key="analisis_nuevo_confirmar_fecha"
    )

    if st.button("Registrar análisis", key="analisis_nuevo_guardar"):

        errores = []

        try:

            fecha_iso = parsear_fecha_es(fecha_texto)

        except ValueError:

            fecha_iso = None
            errores.append("La fecha debe tener formato DD/MM/AAAA")

        if not fecha_iso:

            errores.append("La fecha es obligatoria")

        if not _texto(material):

            errores.append("El material analizado es obligatorio")

        if fecha_iso:

            validacion = validar_fecha_en_campana(campana_id, fecha_iso)

            if validacion["mensaje"]:

                st.warning(validacion["mensaje"])

            if validacion["requiere_confirmacion"] and not confirmar_fecha:

                errores.append(
                    "Confirma expresamente la fecha fuera de campaña"
                )

        if errores:

            for error in errores:

                st.error(error)

            return

        if not _texto(boletin_numero):

            st.warning("Análisis registrado sin nº de boletín")

        if not _texto(laboratorio):

            st.warning("Análisis registrado sin laboratorio")

        ahora = datetime.now().isoformat(timespec="seconds")
        conn = conectar()

        try:

            conn.execute(
                """
                INSERT INTO analisis_fitosanitarios
                (campana_id,fecha,material_analizado,cultivo_id,parcelas,
                boletin_numero,laboratorio,sustancias_detectadas,resultado,
                observaciones,documento,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    int(campana_id),
                    fecha_iso,
                    material,
                    cultivo_id,
                    _parcelas_a_texto(parcelas_sel),
                    boletin_numero.strip(),
                    laboratorio.strip(),
                    sustancias_detectadas.strip(),
                    resultado,
                    observaciones.strip(),
                    documento.strip(),
                    ahora,
                    ahora,
                )
            )
            conn.commit()

        finally:

            conn.close()

        st.success("Análisis fitosanitario registrado")


def _render_editar_analisis(analisis, cultivos, parcelas):

    if analisis.empty:

        st.info("No hay análisis para editar")
        return

    analisis_por_id = analisis.set_index("id", drop=False)
    ids = analisis_por_id.index.astype(int).tolist()
    analisis_id = st.selectbox(
        "Análisis a editar",
        ids,
        format_func=lambda valor: (
            f"#{valor} · "
            f"{formatear_fecha_es(analisis_por_id.loc[valor]['fecha'])} · "
            f"{_texto(analisis_por_id.loc[valor]['material_analizado'])}"
        ),
        key="analisis_editar_id"
    )
    fila = analisis_por_id.loc[analisis_id]
    st.caption(f"Campaña: {_texto(fila['campana'])}")
    fecha_texto = st.text_input(
        "Fecha",
        value=formatear_fecha_es(fila["fecha"]),
        placeholder="DD/MM/AAAA",
        key=f"analisis_editar_fecha_{analisis_id}"
    )
    material_actual = _texto(fila["material_analizado"])
    material = st.selectbox(
        "Material analizado",
        MATERIALES_ANALISIS,
        index=(
            MATERIALES_ANALISIS.index(material_actual)
            if material_actual in MATERIALES_ANALISIS
            else 0
        ),
        key=f"analisis_editar_material_{analisis_id}"
    )
    cultivos_opciones = _opciones_cultivo(cultivos)
    cultivo_actual = _entero_o_none(fila["cultivo_id"])
    cultivo_id = st.selectbox(
        "Cultivo",
        cultivos_opciones,
        index=(
            cultivos_opciones.index(cultivo_actual)
            if cultivo_actual in cultivos_opciones
            else 0
        ),
        format_func=lambda valor: _etiqueta_cultivo(cultivos, valor),
        key=f"analisis_editar_cultivo_{analisis_id}"
    )
    ids_parcelas = (
        parcelas["id"].astype(int).tolist()
        if not parcelas.empty
        else []
    )
    parcelas_actuales = [
        parcela_id
        for parcela_id in _ids_parcelas_desde_texto(fila["parcelas"])
        if parcela_id in ids_parcelas
    ]
    parcelas_sel = st.multiselect(
        "Parcelas",
        ids_parcelas,
        default=parcelas_actuales,
        format_func=lambda valor: _etiqueta_parcela(
            parcelas[parcelas["id"] == valor].iloc[0]
        ),
        key=f"analisis_editar_parcelas_{analisis_id}"
    )
    boletin_numero = st.text_input(
        "Nº boletín de análisis",
        value=_texto(fila["boletin_numero"]),
        key=f"analisis_editar_boletin_{analisis_id}"
    )
    laboratorio = st.text_input(
        "Laboratorio",
        value=_texto(fila["laboratorio"]),
        key=f"analisis_editar_laboratorio_{analisis_id}"
    )
    sustancias_detectadas = st.text_area(
        "Sustancias activas detectadas",
        value=_texto(fila["sustancias_detectadas"]),
        key=f"analisis_editar_sustancias_{analisis_id}"
    )
    resultado_actual = _texto(fila["resultado"])
    resultado = st.selectbox(
        "Resultado",
        RESULTADOS_ANALISIS,
        index=(
            RESULTADOS_ANALISIS.index(resultado_actual)
            if resultado_actual in RESULTADOS_ANALISIS
            else 0
        ),
        key=f"analisis_editar_resultado_{analisis_id}"
    )
    observaciones = st.text_area(
        "Observaciones",
        value=_texto(fila["observaciones"]),
        key=f"analisis_editar_observaciones_{analisis_id}"
    )
    documento = st.text_input(
        "Documento / referencia del boletín",
        value=_texto(fila["documento"]),
        key=f"analisis_editar_documento_{analisis_id}"
    )
    confirmar_fecha = st.checkbox(
        "Confirmo que quiero guardar el análisis aunque la fecha esté fuera "
        "de la campaña seleccionada",
        key=f"analisis_editar_confirmar_fecha_{analisis_id}"
    )

    if st.button("Guardar cambios del análisis", key=f"analisis_editar_guardar_{analisis_id}"):

        errores = []

        try:

            fecha_iso = parsear_fecha_es(fecha_texto)

        except ValueError:

            fecha_iso = None
            errores.append("La fecha debe tener formato DD/MM/AAAA")

        if not fecha_iso:

            errores.append("La fecha es obligatoria")

        if fecha_iso:

            validacion = validar_fecha_en_campana(
                int(fila["campana_id"]),
                fecha_iso
            )

            if validacion["mensaje"]:

                st.warning(validacion["mensaje"])

            if validacion["requiere_confirmacion"] and not confirmar_fecha:

                errores.append(
                    "Confirma expresamente la fecha fuera de campaña"
                )

        if errores:

            for error in errores:

                st.error(error)

            return

        conn = conectar()

        try:

            conn.execute(
                """
                UPDATE analisis_fitosanitarios
                SET fecha=?,
                    material_analizado=?,
                    cultivo_id=?,
                    parcelas=?,
                    boletin_numero=?,
                    laboratorio=?,
                    sustancias_detectadas=?,
                    resultado=?,
                    observaciones=?,
                    documento=?,
                    updated_at=?
                WHERE id=?
                """,
                (
                    fecha_iso,
                    material,
                    cultivo_id,
                    _parcelas_a_texto(parcelas_sel),
                    boletin_numero.strip(),
                    laboratorio.strip(),
                    sustancias_detectadas.strip(),
                    resultado,
                    observaciones.strip(),
                    documento.strip(),
                    datetime.now().isoformat(timespec="seconds"),
                    int(analisis_id),
                )
            )
            conn.commit()

        finally:

            conn.close()

        st.success("Análisis actualizado")
        st.rerun()


def _render_analisis_fitosanitarios(CAMPANA, cultivos):

    st.subheader("🧪 Análisis realizados")
    campanas = _leer_campanas_analisis()

    if campanas.empty:

        st.warning("Primero crea una campaña")
        return

    cultivos_analisis = _preparar_cultivos_analisis(cultivos)
    parcelas = _leer_parcelas_analisis()
    analisis = _leer_analisis_fitosanitarios(parcelas)

    with st.expander("Nuevo análisis", expanded=True):

        _render_nuevo_analisis(
            campanas,
            cultivos_analisis,
            parcelas,
            CAMPANA
        )

    with st.expander("Listado de análisis", expanded=True):

        if analisis.empty:

            st.info("No hay análisis fitosanitarios registrados")

        else:

            _mostrar_listado_analisis(
                analisis,
                campanas
            )

    with st.expander("Editar análisis"):

        _render_editar_analisis(analisis, cultivos_analisis, parcelas)

    with st.expander("Borrar análisis"):

        if analisis.empty:

            st.info("No hay análisis para borrar")

        else:

            borrar_registros_seguro(
                "analisis_fitosanitarios",
                "id",
                analisis[
                    [
                        "id",
                        "fecha",
                        "material_analizado",
                        "resultado",
                        "boletin_numero",
                    ]
                ],
                "análisis fitosanitarios",
                campo_descripcion="material_analizado",
                key="analisis_fitosanitarios"
            )


def _leer_tratamientos_guardados(conn=None, tratamiento_id=None):

    if conn is not None:

        tratamientos_cols = _columnas_tabla_conn(conn, "tratamientos")
        productos_cols = _columnas_tabla_conn(conn, "productos_fito")
        cultivos_cols = _columnas_tabla_conn(conn, "cultivos")
        personas_cols = _columnas_tabla_conn(conn, "personas")
        equipos_cols = _columnas_tabla_conn(conn, "equipos_aplicacion")
        maquinaria_cols = _columnas_tabla_conn(conn, "maquinaria")
        tiene_tratamiento_parcelas = _tabla_existe_conn(
            conn,
            "tratamiento_parcelas",
        )
        tiene_parcelas = _tabla_existe_conn(conn, "parcelas")
        tiene_documentos = _tabla_existe_conn(
            conn,
            "tratamientos_documentos",
        )

    else:

        conn_tmp = conectar()

        try:

            tratamientos_cols = _columnas_tabla_conn(conn_tmp, "tratamientos")
            productos_cols = _columnas_tabla_conn(conn_tmp, "productos_fito")
            cultivos_cols = _columnas_tabla_conn(conn_tmp, "cultivos")
            personas_cols = _columnas_tabla_conn(conn_tmp, "personas")
            equipos_cols = _columnas_tabla_conn(conn_tmp, "equipos_aplicacion")
            maquinaria_cols = _columnas_tabla_conn(conn_tmp, "maquinaria")
            tiene_tratamiento_parcelas = _tabla_existe_conn(
                conn_tmp,
                "tratamiento_parcelas",
            )
            tiene_parcelas = _tabla_existe_conn(conn_tmp, "parcelas")
            tiene_documentos = _tabla_existe_conn(
                conn_tmp,
                "tratamientos_documentos",
            )

        finally:

            conn_tmp.close()

    if not tratamientos_cols:

        return pd.DataFrame()

    expr_campana_id = _valor_numerico_columna(
        "tratamientos",
        "campana_id",
        tratamientos_cols,
    )
    expr_cultivo_id = _valor_numerico_columna(
        "tratamientos",
        "cultivo_id",
        tratamientos_cols,
    )
    expr_producto_id = _valor_numerico_columna(
        "tratamientos",
        "producto_id",
        tratamientos_cols,
    )
    expr_aplicador_id = _valor_numerico_columna(
        "tratamientos",
        "aplicador_id",
        tratamientos_cols,
    )
    expr_equipo_aplicacion_id = _valor_numerico_columna(
        "tratamientos",
        "equipo_aplicacion_id",
        tratamientos_cols,
    )
    expr_equipo_id = _valor_numerico_columna(
        "tratamientos",
        "equipo_id",
        tratamientos_cols,
    )
    expr_maquinaria_id = _valor_numerico_columna(
        "tratamientos",
        "maquinaria_id",
        tratamientos_cols,
    )

    fecha_inicio_exprs = []
    fecha_fin_exprs = []

    if "fecha_inicio" in tratamientos_cols:

        fecha_inicio_exprs.append("NULLIF(tratamientos.fecha_inicio,'')")
        fecha_fin_exprs.append("NULLIF(tratamientos.fecha_inicio,'')")

    if "fecha_fin" in tratamientos_cols:

        fecha_fin_exprs.insert(0, "NULLIF(tratamientos.fecha_fin,'')")

    if "fecha" in tratamientos_cols:

        fecha_inicio_exprs.append("NULLIF(tratamientos.fecha,'')")
        fecha_fin_exprs.append("NULLIF(tratamientos.fecha,'')")

    fecha_inicio_exprs.append("''")
    fecha_fin_exprs.append("''")
    expr_fecha_inicio = _coalesce_sql(fecha_inicio_exprs)
    expr_fecha_fin = _coalesce_sql(fecha_fin_exprs)
    expr_fecha_recoleccion = _valor_texto_columna(
        "tratamientos",
        "fecha_recoleccion_segura",
        tratamientos_cols,
    )
    expr_dosis = _valor_texto_columna("tratamientos", "dosis", tratamientos_cols)
    expr_caldo = _valor_numerico_columna(
        "tratamientos",
        "caldo",
        tratamientos_cols,
    )
    expr_superficie = _valor_numerico_columna(
        "tratamientos",
        "superficie_tratada",
        tratamientos_cols,
    )
    expr_plazo = _valor_texto_columna(
        "tratamientos",
        "plazo_seguridad",
        tratamientos_cols,
    )
    expr_eficacia = _valor_texto_columna(
        "tratamientos",
        "eficacia",
        tratamientos_cols,
    )
    expr_observaciones = _valor_texto_columna(
        "tratamientos",
        "observaciones",
        tratamientos_cols,
    )
    expr_justificacion = _valor_texto_columna(
        "tratamientos",
        "justificacion",
        tratamientos_cols,
    )
    expr_producto_legacy = _valor_texto_columna(
        "tratamientos",
        "producto",
        tratamientos_cols,
    )
    expr_aplicador_legacy = _valor_texto_columna(
        "tratamientos",
        "aplicador",
        tratamientos_cols,
    )
    expr_equipo_legacy = _valor_texto_columna(
        "tratamientos",
        "equipo",
        tratamientos_cols,
    )
    plaga_exprs = []

    for columna in ("plaga_motivo", "plaga", "problema"):

        if columna in tratamientos_cols:

            plaga_exprs.append(f"NULLIF(tratamientos.{columna},'')")

    plaga_exprs.append("''")
    expr_plaga = _coalesce_sql(plaga_exprs)
    condiciones_exprs = []

    for columna in ("condiciones_meteorologicas", "condiciones"):

        if columna in tratamientos_cols:

            condiciones_exprs.append(f"NULLIF(tratamientos.{columna},'')")

    condiciones_exprs.append("''")
    expr_condiciones = _coalesce_sql(condiciones_exprs)

    joins = []
    expr_campana = "''"

    if "campana_id" in tratamientos_cols:

        joins.append("LEFT JOIN campanas ON campanas.id = tratamientos.campana_id")
        expr_campana = "COALESCE(campanas.nombre,'')"

    if "producto_id" in tratamientos_cols and productos_cols:

        joins.append(
            """
            LEFT JOIN productos_fito
            ON productos_fito.id = tratamientos.producto_id
            """
        )
        expr_producto_nombre = _valor_texto_columna(
            "productos_fito",
            "nombre",
            productos_cols,
        )
        expr_producto = _coalesce_sql(
            [f"NULLIF({expr_producto_nombre},'')", expr_producto_legacy, "''"]
        )
        expr_registro = _expr_producto_registro(productos_cols)
        expr_producto_plazo = _valor_texto_columna(
            "productos_fito",
            "plazo_seguridad",
            productos_cols,
        )

    else:

        expr_producto = expr_producto_legacy
        expr_registro = "''"
        expr_producto_plazo = "''"

    if "cultivo_id" in tratamientos_cols and cultivos_cols:

        joins.append("LEFT JOIN cultivos ON cultivos.id = tratamientos.cultivo_id")
        expr_nombre_cultivo = _expr_nombre_cultivo(cultivos_cols)
        expr_variedad = _expr_variedad_cultivo(cultivos_cols)
        expr_sistema = _expr_sistema_cultivo(cultivos_cols)
        expr_ano_plantacion = (
            """
            CASE
                WHEN cultivos.ano_plantacion IS NULL THEN ''
                ELSE 'Plant. ' || cultivos.ano_plantacion
            END
            """
            if "ano_plantacion" in cultivos_cols
            else "''"
        )
        expr_cultivo = (
            "TRIM("
            f"{expr_nombre_cultivo} || ' / ' || "
            f"{expr_variedad} || ' / ' || "
            f"{expr_sistema} || ' / ' || "
            f"{expr_ano_plantacion}"
            ")"
        )

    else:

        expr_cultivo = _valor_texto_columna(
            "tratamientos",
            "cultivo",
            tratamientos_cols,
        )

    if "aplicador_id" in tratamientos_cols and personas_cols:

        joins.append("LEFT JOIN personas ON personas.id = tratamientos.aplicador_id")
        expr_aplicador = _coalesce_sql(
            ["NULLIF(personas.nombre,'')", expr_aplicador_legacy, "''"]
        )

    else:

        expr_aplicador = expr_aplicador_legacy

    equipo_join_ids = []

    if "equipo_aplicacion_id" in tratamientos_cols:

        equipo_join_ids.append("tratamientos.equipo_aplicacion_id")

    if "equipo_id" in tratamientos_cols:

        equipo_join_ids.append("tratamientos.equipo_id")

    if equipo_join_ids and equipos_cols:

        joins.append(
            "LEFT JOIN equipos_aplicacion ON equipos_aplicacion.id = "
            + _coalesce_sql(equipo_join_ids + ["NULL"])
        )
        equipo_exprs = ["NULLIF(equipos_aplicacion.nombre,'')"]

    else:

        equipo_exprs = []

    if "maquinaria_id" in tratamientos_cols and maquinaria_cols:

        joins.append("LEFT JOIN maquinaria ON maquinaria.id = tratamientos.maquinaria_id")

        if "nombre" in maquinaria_cols:

            equipo_exprs.append("NULLIF(maquinaria.nombre,'')")

    equipo_exprs.extend([expr_equipo_legacy, "''"])
    expr_equipo = _coalesce_sql(equipo_exprs)

    if tiene_documentos:

        joins.append(
            """
            LEFT JOIN (
                SELECT tratamiento_id,COUNT(*) AS recetas
                FROM tratamientos_documentos
                WHERE tipo_documento='receta'
                GROUP BY tratamiento_id
            ) documentos
            ON documentos.tratamiento_id = tratamientos.id
            """
        )
        expr_recetas = "COALESCE(documentos.recetas,0)"

    else:

        expr_recetas = "0"

    if tiene_tratamiento_parcelas and tiene_parcelas:

        joins.extend(
            [
                """
                LEFT JOIN tratamiento_parcelas
                ON tratamiento_parcelas.tratamiento_id = tratamientos.id
                """,
                "LEFT JOIN parcelas ON parcelas.id = tratamiento_parcelas.parcela_id",
            ]
        )
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

    where = ""
    params = ()

    if tratamiento_id is not None:

        where = "WHERE tratamientos.id=?"
        params = (int(tratamiento_id),)

    sql = f"""
        SELECT
        tratamientos.id,
        {expr_campana_id} AS campana_id,
        {expr_campana} AS campana,
        {expr_fecha_inicio} AS fecha_inicio,
        {expr_fecha_fin} AS fecha_fin,
        {expr_fecha_inicio} || ' a ' || {expr_fecha_fin} AS periodo,
        {expr_producto_id} AS producto_id,
        {expr_producto} AS producto,
        {expr_registro} AS registro_producto,
        {expr_cultivo_id} AS cultivo_id,
        {expr_cultivo} AS cultivo,
        {expr_aplicador} AS aplicador,
        {expr_aplicador_id} AS aplicador_id,
        {expr_equipo} AS equipo,
        {expr_equipo_id} AS equipo_id,
        {expr_equipo_aplicacion_id} AS equipo_aplicacion_id,
        {expr_maquinaria_id} AS maquinaria_id,
        {expr_plaga} AS plaga,
        {expr_justificacion} AS justificacion,
        {expr_dosis} AS dosis,
        {expr_caldo} AS caldo,
        {expr_superficie} AS superficie_tratada,
        {expr_plazo} AS plazo_seguridad,
        {expr_producto_plazo} AS plazo_seguridad_producto,
        {expr_fecha_recoleccion} AS fecha_recoleccion_segura,
        {expr_condiciones} AS condiciones_meteorologicas,
        {expr_eficacia} AS eficacia,
        {expr_observaciones} AS observaciones,
        {expr_parcelas} AS parcelas,
        {expr_recetas} AS recetas_count
        FROM tratamientos
        {" ".join(joins)}
        {where}
        GROUP BY tratamientos.id
        ORDER BY fecha_inicio DESC, tratamientos.id DESC
    """

    tratamientos = _leer_dataframe(sql, params, conn=conn)

    if tratamientos.empty:

        return tratamientos

    tratamientos = tratamientos.copy()
    if conn is not None:

        tratamientos = _agregar_detalles_actuacion(
            tratamientos,
            conn,
            "tratamiento_cultivos",
            "tratamiento_id",
        )

    else:

        conn_detalles = conectar()

        try:

            tratamientos = _agregar_detalles_actuacion(
                tratamientos,
                conn_detalles,
                "tratamiento_cultivos",
                "tratamiento_id",
            )

        finally:

            conn_detalles.close()

    tiene_detalle = tratamientos["tiene_detalle_multicultivo"].fillna(False)
    tratamientos["cultivo"] = tratamientos["cultivos_detalle"].where(
        tiene_detalle & (tratamientos["cultivos_detalle"].astype(str) != ""),
        tratamientos["cultivo"],
    )
    tratamientos["parcelas"] = tratamientos["parcelas_detalle"].where(
        tiene_detalle & (tratamientos["parcelas_detalle"].astype(str) != ""),
        tratamientos["parcelas"],
    )
    tratamientos["cultivo"] = (
        tratamientos["cultivo"]
        .fillna("")
        .astype(str)
        .str.strip(" /")
    )
    tratamientos["plazo_seguridad"] = tratamientos["plazo_seguridad"].where(
        tratamientos["plazo_seguridad"].fillna("").astype(str).str.strip() != "",
        tratamientos["plazo_seguridad_producto"],
    )
    tratamientos = tratamientos.drop(
        columns=["plazo_seguridad_producto"],
        errors="ignore",
    )
    return tratamientos


def render(CAMPANA):

    st.title("📖 Tratamientos")

    opciones_tratamientos = [
        "📋 Listado",
        "➕ Nuevo tratamiento",
        "🔁 Duplicar",
        "✏️ Editar",
        "🗑️ Borrar",
        "🧪 Análisis realizados",
    ]
    seccion_tratamientos = st.radio(
        "Opciones de tratamientos",
        opciones_tratamientos,
        horizontal=True,
        key="tratamientos_seccion"
    )

    productos = _leer_productos_fito_tratamiento()
    cultivos = _leer_cultivos_tratamiento()
    cultivo_parcelas = _leer_cultivo_parcelas_tratamiento()
    personas_tratamiento = _leer_personas_tratamiento()

    aplicadores = personas_tratamiento[
        personas_tratamiento["rol"] == "Aplicador fitosanitario"
    ].copy()

    if aplicadores.empty:

        aplicadores = personas_tratamiento.copy()

    equipos = _leer_equipos_aplicacion_tratamiento()



    if seccion_tratamientos == "➕ Nuevo tratamiento":

        if productos.empty:

            st.warning(
                "No hay productos fitosanitarios dados de alta. "
                "Crea uno en Productos Fito."
            )

        elif cultivos.empty:

            st.warning(
                "Primero añade cultivos"
            )


        else:

            if "form_tratamiento_version" not in st.session_state:

                st.session_state["form_tratamiento_version"] = 0

            form_tratamiento_version = (
                st.session_state["form_tratamiento_version"]
            )

            cultivos_ordenados = cultivos.copy()
            cultivos_ordenados["prioridad_campana"] = (
                pd.to_numeric(
                    cultivos_ordenados["campana_id"],
                    errors="coerce",
                ) != int(CAMPANA)
            ).astype(int)
            cultivos_ordenados = cultivos_ordenados.sort_values(
                by=["prioridad_campana", "campana", "especie", "id"]
            )
            ids_cultivos_tratamiento = (
                cultivos_ordenados["id"].dropna().astype(int).tolist()
            )
            cultivos_ids_tratamiento = st.multiselect(
                "Cultivos tratados",
                ids_cultivos_tratamiento,
                default=(
                    [ids_cultivos_tratamiento[0]]
                    if ids_cultivos_tratamiento
                    else []
                ),
                format_func=lambda valor: _etiqueta_cultivo_v6(
                    _cultivo_por_id(cultivos, valor)
                ),
                key=f"tratamiento_cultivos_{form_tratamiento_version}",
            )
            cultivo = (
                int(cultivos_ids_tratamiento[0])
                if cultivos_ids_tratamiento
                else None
            )
            detalles_tratamiento = []
            parcelas_sel = []
            parcelas_sin_superficie = False

            for cultivo_id_detalle in cultivos_ids_tratamiento:

                cultivo_detalle = _cultivo_por_id(
                    cultivos,
                    cultivo_id_detalle,
                )
                parcelas_cultivo = _parcelas_para_cultivo_tratamiento(
                    cultivo_detalle,
                    cultivo_parcelas,
                )
                etiqueta_cultivo_detalle = _etiqueta_cultivo_v6(
                    cultivo_detalle
                )

                if parcelas_cultivo.empty:

                    st.info(
                        "El cultivo seleccionado no tiene parcelas asociadas: "
                        f"{etiqueta_cultivo_detalle}."
                    )
                    continue

                etiquetas_parcelas = {
                    int(fila["parcela_id"]): (
                        str(fila["parcela"]).strip()
                        if str(fila["parcela"]).strip()
                        else (
                            f"{fila['poligono']}-"
                            f"{fila['numero_parcela']}-"
                            f"{fila['recinto']}"
                        )
                    )
                    for _, fila in parcelas_cultivo.iterrows()
                }
                opciones_parcelas = (
                    parcelas_cultivo["parcela_id"]
                    .dropna()
                    .astype(int)
                    .drop_duplicates()
                    .tolist()
                )
                parcelas_cultivo_sel = st.multiselect(
                    f"Parcelas tratadas de {etiqueta_cultivo_detalle}",
                    opciones_parcelas,
                    default=opciones_parcelas,
                    format_func=lambda valor: etiquetas_parcelas.get(
                        int(valor),
                        str(valor),
                    ),
                    key=(
                        f"tratamiento_parcelas_{form_tratamiento_version}_"
                        f"{int(cultivo_id_detalle)}"
                    ),
                )
                parcelas_sel.extend(int(valor) for valor in parcelas_cultivo_sel)
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

                    detalles_tratamiento.append(
                        {
                            "cultivo_id": int(cultivo_id_detalle),
                            "parcela_id": int(parcela_detalle["parcela_id"]),
                            "superficie": superficie,
                        }
                    )

            detalles_tratamiento = _normalizar_detalles_actuacion(
                detalles_tratamiento
            )
            superficie_total_seleccionada = float(
                sum(
                    float(detalle["superficie"] or 0)
                    for detalle in detalles_tratamiento
                )
            )
            firma_parcelas_superficie = (
                "_".join(
                    f"{detalle['cultivo_id']}-{detalle['parcela_id']}"
                    for detalle in detalles_tratamiento
                )
                if detalles_tratamiento
                else "sin_parcelas"
            )
            st.info(
                "Superficie seleccionada: "
                f"{superficie_total_seleccionada:.2f} ha"
            )

            if parcelas_sin_superficie:

                st.warning(
                    "Hay parcelas seleccionadas sin superficie informada."
                )

            superficie_sugerida_tratamiento = superficie_total_seleccionada

            campanas_tratamiento = leer(
                """
                SELECT id,nombre,fecha_inicio,fecha_fin,activa
                FROM campanas
                ORDER BY fecha_inicio DESC,id DESC
                """
            )
            fecha_tratamiento_defecto = date.today()
            campana_activa_tratamiento = campanas_tratamiento[
                campanas_tratamiento["id"] == CAMPANA
            ]

            if not campana_activa_tratamiento.empty:

                inicio_campana_tratamiento = pd.to_datetime(
                    campana_activa_tratamiento.iloc[0]["fecha_inicio"],
                    errors="coerce"
                )
                fin_campana_tratamiento = pd.to_datetime(
                    campana_activa_tratamiento.iloc[0]["fecha_fin"],
                    errors="coerce"
                )

                if (
                    not pd.isna(inicio_campana_tratamiento)
                    and not pd.isna(fin_campana_tratamiento)
                    and not (
                        inicio_campana_tratamiento.date()
                        <= fecha_tratamiento_defecto
                        <= fin_campana_tratamiento.date()
                    )
                ):

                    fecha_tratamiento_defecto = (
                        inicio_campana_tratamiento.date()
                    )

            columna_inicio_tratamiento, columna_fin_tratamiento = st.columns(2)

            with columna_inicio_tratamiento:

                fecha_inicio_tratamiento_texto = st.text_input(
                    "Fecha inicio tratamiento",
                    value=formatear_fecha_es(fecha_tratamiento_defecto),
                    placeholder="DD/MM/AAAA",
                    key=f"tratamiento_fecha_inicio_{form_tratamiento_version}"
                )

            with columna_fin_tratamiento:

                fecha_fin_tratamiento_texto = st.text_input(
                    "Fecha fin tratamiento",
                    value=formatear_fecha_es(fecha_tratamiento_defecto),
                    placeholder="DD/MM/AAAA",
                    key=f"tratamiento_fecha_fin_{form_tratamiento_version}"
                )

            error_formato_fecha_tratamiento = False

            try:

                fecha_inicio_iso_tratamiento = parsear_fecha_es(
                    fecha_inicio_tratamiento_texto
                )
                fecha_fin_iso_tratamiento = parsear_fecha_es(
                    fecha_fin_tratamiento_texto
                )
                fecha_inicio_tratamiento = pd.to_datetime(
                    fecha_inicio_iso_tratamiento,
                    errors="coerce"
                ).date() if fecha_inicio_iso_tratamiento else None
                fecha_fin_tratamiento = pd.to_datetime(
                    fecha_fin_iso_tratamiento,
                    errors="coerce"
                ).date() if fecha_fin_iso_tratamiento else None

            except ValueError:

                error_formato_fecha_tratamiento = True
                fecha_inicio_tratamiento = None
                fecha_fin_tratamiento = None
                st.warning("La fecha debe tener formato DD/MM/AAAA")

            ids_campanas_tratamiento = (
                campanas_tratamiento["id"].astype(int).tolist()
            )
            opciones_campanas_tratamiento = [None] + ids_campanas_tratamiento
            indice_campana_activa = (
                opciones_campanas_tratamiento.index(int(CAMPANA))
                if int(CAMPANA) in ids_campanas_tratamiento
                else 0
            )
            campana_seleccionada_tratamiento = st.selectbox(
                "Campaña del tratamiento",
                opciones_campanas_tratamiento,
                index=indice_campana_activa,
                format_func=lambda valor: (
                    "Selecciona campaña..."
                    if valor is None
                    else campanas_tratamiento.loc[
                        campanas_tratamiento["id"] == valor,
                        "nombre"
                    ].iloc[0]
                ),
                key=(
                    "campana_seleccionada_tratamiento_v611_"
                    f"{form_tratamiento_version}"
                )
            )

            conn_campanas_tratamiento = conectar()

            try:

                resultado_campana_tratamiento = obtener_campana_por_intervalo(
                    conn_campanas_tratamiento,
                    fecha_inicio_tratamiento,
                    fecha_fin_tratamiento
                )

            finally:

                conn_campanas_tratamiento.close()

            campana_sugerida_tratamiento = resultado_campana_tratamiento[
                "campana"
            ]
            usar_campana_sugerida = False
            campana_difiere_sugerencia = False

            if resultado_campana_tratamiento["estado"] == "cruza_campanas":

                st.error(resultado_campana_tratamiento["mensaje"])

            elif campana_sugerida_tratamiento is None:

                st.warning(resultado_campana_tratamiento["mensaje"])

            elif (
                campana_seleccionada_tratamiento is not None
                and
                campana_sugerida_tratamiento["id"]
                != int(campana_seleccionada_tratamiento)
            ):

                campana_difiere_sugerencia = True
                nombre_campana_seleccionada = campanas_tratamiento.loc[
                    campanas_tratamiento["id"]
                    == int(campana_seleccionada_tratamiento),
                    "nombre"
                ].iloc[0]
                st.warning(
                    "La fecha del tratamiento corresponde a la campaña "
                    f"{campana_sugerida_tratamiento['nombre']}, pero está "
                    f"seleccionada la campaña {nombre_campana_seleccionada}."
                )
                usar_campana_sugerida = st.checkbox(
                    "Usar la campaña sugerida por las fechas",
                    key=f"usar_campana_sugerida_tratamiento_{form_tratamiento_version}"
                )

            campana_guardar_tratamiento = (
                int(campana_seleccionada_tratamiento)
                if campana_seleccionada_tratamiento is not None
                else None
            )

            if usar_campana_sugerida:

                campana_guardar_tratamiento = campana_sugerida_tratamiento["id"]
                campana_difiere_sugerencia = False
                st.info(
                    "El tratamiento se guardará en la campaña "
                    f"{campana_sugerida_tratamiento['nombre']}."
                )

            validacion_fecha_tratamiento = {
                "requiere_confirmacion": False,
                "mensaje": "",
            }

            if campana_guardar_tratamiento is not None:

                validacion_fecha_tratamiento = validar_intervalo_en_campana(
                    campana_guardar_tratamiento,
                    fecha_inicio_tratamiento,
                    fecha_fin_tratamiento
                )

            confirmar_fecha_tratamiento = False

            if validacion_fecha_tratamiento["requiere_confirmacion"]:

                st.warning(validacion_fecha_tratamiento["mensaje"])

            elif validacion_fecha_tratamiento["mensaje"]:

                st.info(validacion_fecha_tratamiento["mensaje"])

            if (
                validacion_fecha_tratamiento["requiere_confirmacion"]
                or campana_difiere_sugerencia
            ):

                confirmar_fecha_tratamiento = st.checkbox(
                    "Confirmo expresamente que quiero guardar el tratamiento "
                    "en la campaña seleccionada aunque sus fechas no "
                    "correspondan a su periodo oficial",
                    key=f"confirmar_fecha_fuera_tratamiento_{form_tratamiento_version}"
                )

            with st.form(f"tratamiento_v{form_tratamiento_version}"):

                producto_ids = productos["id"].astype(int).tolist()
                producto = st.selectbox(
                    "Producto",
                    [None] + producto_ids,
                    index=0,
                    format_func=lambda valor: (
                        "Selecciona producto..."
                        if valor is None
                        else _etiqueta_producto_fito(
                            _fila_por_id(productos, valor)
                        )
                    ),
                    key=f"tratamiento_producto_v611_{form_tratamiento_version}"
                )

                producto_seleccionado = _fila_por_id(productos, producto)

                if producto_seleccionado is not None:

                    st.caption(
                        "Producto seleccionado: "
                        f"{_etiqueta_producto_fito(producto_seleccionado)}."
                    )

                aplicador = None

                if aplicadores.empty:

                    st.info(
                        "No hay personas registradas para seleccionar aplicador."
                    )

                else:

                    aplicador = st.selectbox(
                        "Aplicador",
                        [None] + aplicadores.id.tolist(),
                        format_func=lambda x: (
                            "Selecciona aplicador..."
                            if x is None
                            else _etiqueta_persona(
                                _fila_por_id(aplicadores, x)
                            )
                        ),
                        key=f"tratamiento_aplicador_v611_{form_tratamiento_version}"
                    )

                equipo = None

                if equipos.empty:

                    st.info(
                        "No hay equipos de aplicación dados de alta. "
                        "Se gestionan en Explotación."
                    )

                else:

                    equipo = st.selectbox(
                        "Equipo de aplicación",
                        [None] + equipos.id.tolist(),
                        format_func=lambda x: (
                            "Selecciona equipo de aplicación..."
                            if x is None
                            else _etiqueta_equipo_aplicacion(
                                _fila_por_id(equipos, x)
                            )
                        ),
                        key=f"tratamiento_equipo_v611_{form_tratamiento_version}"
                    )


                plaga = st.text_input(
                    "Plaga / enfermedad",
                    key=f"tratamiento_plaga_{form_tratamiento_version}"
                )

                justificacion = st.text_area(
                    "Justificación",
                    key=f"tratamiento_justificacion_{form_tratamiento_version}"
                )

                recetas_tratamiento = st.file_uploader(
                    "Recetas fitosanitarias PDF",
                    type=["pdf"],
                    accept_multiple_files=True,
                    key=f"tratamiento_recetas_{form_tratamiento_version}"
                )
                st.caption(
                    "Solo se admiten recetas en PDF. El tratamiento puede "
                    "guardarse sin receta adjunta."
                )


                dosis = st.text_input(
                    "Dosis aplicada",
                    key=f"tratamiento_dosis_{form_tratamiento_version}"
                )

                superficie_tratada = st.number_input(
                    "Superficie tratada",
                    value=max(0.0, float(superficie_sugerida_tratamiento)),
                    min_value=0.0,
                    key=(
                        f"tratamiento_superficie_{form_tratamiento_version}_"
                        f"{firma_parcelas_superficie}"
                    )
                )

                caldo = st.number_input(
                    "Litros caldo",
                    value=0.0,
                    key=f"tratamiento_caldo_{form_tratamiento_version}"
                )

                condiciones_meteorologicas = st.text_area(
                    "Condiciones meteorológicas",
                    key=f"tratamiento_condiciones_{form_tratamiento_version}"
                )

                eficacia_tratamiento = st.selectbox(
                    "Eficacia del tratamiento",
                    list(OPCIONES_EFICACIA.keys()),
                    key=f"tratamiento_eficacia_{form_tratamiento_version}"
                )

                plazo_seguridad_defecto = ""

                if producto_seleccionado is not None:

                    plazo_seguridad_defecto = _texto(
                        producto_seleccionado.get("plazo_seguridad")
                    )

                plazo_seguridad = st.text_input(
                    "Plazo seguridad",
                    value=plazo_seguridad_defecto,
                    key=(
                        "tratamiento_plazo_seguridad_v611_"
                        f"{form_tratamiento_version}_"
                        f"{producto if producto is not None else 'sin_producto'}"
                    )
                )

                fecha_recoleccion_segura = st.text_input(
                    "Fecha recolección segura",
                    placeholder="DD/MM/AAAA",
                    key=f"tratamiento_recoleccion_{form_tratamiento_version}"
                )


                obs = st.text_area(
                    "Observaciones",
                    key=f"tratamiento_observaciones_{form_tratamiento_version}"
                )

                if st.form_submit_button(
                    "Registrar tratamiento"
                ):

                    errores_tratamiento = []

                    if campana_guardar_tratamiento is None:

                        errores_tratamiento.append("Selecciona una campaña.")

                    if fecha_inicio_tratamiento is None:

                        if error_formato_fecha_tratamiento:

                            errores_tratamiento.append(
                                "La fecha debe tener formato DD/MM/AAAA."
                            )

                        else:

                            errores_tratamiento.append(
                                "La fecha de inicio es obligatoria."
                            )

                    elif fecha_fin_tratamiento is None:

                        if error_formato_fecha_tratamiento:

                            errores_tratamiento.append(
                                "La fecha debe tener formato DD/MM/AAAA."
                            )

                        else:

                            errores_tratamiento.append(
                                "La fecha de fin es obligatoria."
                            )

                    elif fecha_fin_tratamiento < fecha_inicio_tratamiento:

                        errores_tratamiento.append(
                            "La fecha de fin no puede ser anterior a la fecha "
                            "de inicio."
                        )

                    if (
                        resultado_campana_tratamiento["estado"]
                        == "cruza_campanas"
                    ):

                        errores_tratamiento.append(
                            resultado_campana_tratamiento["mensaje"]
                        )

                    if (
                        (
                            validacion_fecha_tratamiento[
                                "requiere_confirmacion"
                            ]
                            or campana_difiere_sugerencia
                        )
                        and not confirmar_fecha_tratamiento
                    ):

                        errores_tratamiento.append(
                            "Marca la confirmación para guardar el tratamiento."
                        )

                    if not cultivos_ids_tratamiento:

                        errores_tratamiento.append(
                            "Selecciona al menos un cultivo."
                        )

                    if not detalles_tratamiento:

                        errores_tratamiento.append(
                            "Selecciona al menos una parcela tratada."
                        )

                    if producto is None:

                        errores_tratamiento.append(
                            "Selecciona un producto fitosanitario."
                        )

                    if float(superficie_tratada) <= 0:

                        errores_tratamiento.append(
                            "La superficie tratada debe ser mayor que 0."
                        )

                    if not aplicadores.empty and aplicador is None:

                        errores_tratamiento.append(
                            "Selecciona un aplicador."
                        )

                    if not equipos.empty and equipo is None:

                        errores_tratamiento.append(
                            "Selecciona un equipo de aplicación."
                        )

                    if errores_tratamiento:

                        for error in errores_tratamiento:

                            st.error(error)

                    else:

                        try:

                            fecha_recoleccion_segura_iso = parsear_fecha_es(
                                fecha_recoleccion_segura
                            )

                        except ValueError:

                            st.warning("La fecha debe tener formato DD/MM/AAAA")
                            fecha_recoleccion_segura_iso = None

                        if fecha_recoleccion_segura and (
                            fecha_recoleccion_segura_iso is None
                        ):

                            pass

                        else:

                            conn = conectar()
                            resultado_recetas = {"guardados": [], "errores": []}

                            try:

                                conn.execute("BEGIN")
                                parcelas_insertar = (
                                    _parcelas_compatibilidad_detalles(
                                        detalles_tratamiento
                                    )
                                )

                                producto_texto = (
                                    _texto(producto_seleccionado.get("nombre"))
                                    if producto_seleccionado is not None
                                    else ""
                                )
                                aplicador_texto = (
                                    ""
                                    if aplicador is None
                                    else _texto(
                                        aplicadores[
                                            aplicadores.id == aplicador
                                        ].nombre.values[0]
                                    )
                                )
                                equipo_seleccionado = _fila_por_id(
                                    equipos,
                                    equipo,
                                )
                                equipo_texto = (
                                    _texto(equipo_seleccionado.get("nombre"))
                                    if equipo_seleccionado is not None
                                    else ""
                                )
                                tratamiento_id = (
                                    _insertar_tratamiento_compatible(
                                        conn,
                                        {
                                            "campana_id": (
                                                campana_guardar_tratamiento
                                            ),
                                            "fecha": (
                                                fecha_inicio_tratamiento
                                                .isoformat()
                                            ),
                                            "fecha_inicio": (
                                                fecha_inicio_tratamiento
                                                .isoformat()
                                            ),
                                            "fecha_fin": (
                                                fecha_fin_tratamiento
                                                .isoformat()
                                            ),
                                            "producto_id": producto,
                                            "producto": producto_texto,
                                            "plaga_motivo": plaga,
                                            "plaga": plaga,
                                            "problema": plaga,
                                            "justificacion": justificacion,
                                            "dosis": dosis,
                                            "caldo": caldo,
                                            "aplicador": aplicador_texto,
                                            "aplicador_id": aplicador,
                                            "equipo": equipo_texto,
                                            "equipo_id": equipo,
                                            "equipo_aplicacion_id": equipo,
                                            "cultivo_id": cultivo,
                                            "superficie_tratada": (
                                                superficie_tratada
                                            ),
                                            "plazo_seguridad": plazo_seguridad,
                                            "fecha_recoleccion_segura": (
                                                fecha_recoleccion_segura_iso
                                            ),
                                            "condiciones": (
                                                condiciones_meteorologicas
                                            ),
                                            "condiciones_meteorologicas": (
                                                condiciones_meteorologicas
                                            ),
                                            "eficacia": OPCIONES_EFICACIA[
                                                eficacia_tratamiento
                                            ],
                                            "observaciones": obs,
                                        },
                                        parcelas_insertar,
                                        detalles_cultivos=(
                                            detalles_tratamiento
                                        ),
                                    )
                                )

                                resultado_recetas = guardar_recetas_pdf(
                                    conn,
                                    tratamiento_id,
                                    recetas_tratamiento
                                )
                                conn.commit()

                            except (sqlite3.Error, OSError, ValueError) as error:

                                conn.rollback()
                                st.error(
                                    "No se pudo registrar el tratamiento: "
                                    f"{error}"
                                )

                            else:

                                for error_receta in resultado_recetas["errores"]:

                                    st.warning(error_receta)

                                if resultado_recetas["guardados"]:

                                    st.success(
                                        "Tratamiento registrado con recetas"
                                    )

                                else:

                                    st.success("Tratamiento registrado")

                                st.session_state[
                                    "form_tratamiento_version"
                                ] += 1
                                st.rerun()

                            finally:

                                conn.close()


    tratamientos_listado = _leer_tratamientos_guardados()

    if "recetas_count" in tratamientos_listado.columns:

        tratamientos_listado["recetas"] = (
            tratamientos_listado["recetas_count"].fillna(0).astype(int)
            .apply(_texto_recetas)
        )

    if "eficacia" in tratamientos_listado.columns:

        tratamientos_listado["eficacia"] = (
            tratamientos_listado["eficacia"].apply(_normalizar_eficacia)
        )


    if seccion_tratamientos == "📋 Listado":

        tratamientos_listado_visible = tratamientos_listado.drop(
            columns=["id", "recetas_count"],
            errors="ignore"
        )
        tratamientos_filtrados = mostrar_filtros_dataframe(
            tratamientos_listado_visible,
            "tratamientos_listado",
            columnas_texto=[
                "producto",
                "registro_producto",
                "cultivo",
                "parcelas",
                "observaciones",
                "plaga",
                "eficacia",
                "aplicador",
                "equipo",
                "recetas"
            ],
            columna_fecha="fecha_inicio",
            columna_fecha_fin="fecha_fin",
            filtros_select={
                "Campaña": "campana",
                "Cultivo": "cultivo",
                "Producto": "producto",
                "Registro": "registro_producto",
                "Plaga": "plaga",
                "Aplicador": "aplicador",
                "Equipo": "equipo"
            }
        )
        columnas_listado_tratamientos = [
            "campana",
            "cultivo",
            "parcelas",
            "fecha_inicio",
            "fecha_fin",
            "producto",
            "registro_producto",
            "dosis",
            "caldo",
            "superficie_tratada",
            "aplicador",
            "equipo",
            "eficacia",
            "observaciones",
            "recetas",
        ]
        tratamientos_filtrados_visual = preparar_dataframe_visual(
            preparar_columnas_fecha_tabla(
                tratamientos_filtrados,
                ["fecha_inicio", "fecha_fin"]
            ),
            columnas=columnas_listado_tratamientos,
            ocultar_tecnicas=True,
        )
        st.dataframe(
            tratamientos_filtrados_visual,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Fecha inicio": st.column_config.DateColumn(
                    "Fecha inicio",
                    format="DD/MM/YYYY"
                ),
                "Fecha fin": st.column_config.DateColumn(
                    "Fecha fin",
                    format="DD/MM/YYYY"
                )
            }
        )


    if seccion_tratamientos == "🔁 Duplicar":

        mensaje_duplicacion_tratamiento = st.session_state.pop(
            "duplicar_tratamiento_mensaje",
            None
        )

        if mensaje_duplicacion_tratamiento:

            st.success(mensaje_duplicacion_tratamiento)

        with st.expander("Duplicar registro existente"):

            if tratamientos_listado.empty:

                st.info("No hay tratamientos para duplicar")

            else:

                tratamientos_por_id = (
                    tratamientos_listado
                    .copy()
                    .set_index("id", drop=False)
                )
                ids_tratamientos = [
                    int(valor)
                    for valor in tratamientos_por_id.index.tolist()
                ]

                def formato_tratamiento_origen(tratamiento_id):

                    fila = tratamientos_por_id.loc[tratamiento_id]
                    periodo = (
                        f"{formatear_fecha_es(fila['fecha_inicio'])} a "
                        f"{formatear_fecha_es(fila['fecha_fin'])}"
                    )
                    producto = _texto(fila["producto"])
                    plaga = _texto(fila["plaga"])

                    return f"#{tratamiento_id} · {periodo} · {producto} · {plaga}"

                tratamiento_origen_id = st.selectbox(
                    "Tratamiento a duplicar",
                    ids_tratamientos,
                    format_func=formato_tratamiento_origen,
                    key="dup_trat_origen_id"
                )
                claves_duplicar_tratamiento = [
                    f"dup_trat_fecha_inicio_{tratamiento_origen_id}",
                    f"dup_trat_fecha_fin_{tratamiento_origen_id}",
                    f"dup_trat_producto_{tratamiento_origen_id}",
                    f"dup_trat_plaga_{tratamiento_origen_id}",
                    f"dup_trat_obs_{tratamiento_origen_id}",
                    f"dup_trat_confirm_fecha_{tratamiento_origen_id}",
                    f"dup_trat_confirm_{tratamiento_origen_id}",
                    f"dup_trat_btn_{tratamiento_origen_id}"
                ]

                if (
                    st.session_state.get("dup_trat_origen_id_anterior")
                    != tratamiento_origen_id
                ):

                    for clave in claves_duplicar_tratamiento:

                        st.session_state.pop(clave, None)

                    st.session_state["dup_trat_origen_id_anterior"] = (
                        tratamiento_origen_id
                    )

                tratamiento_resumen = tratamientos_por_id.loc[
                    tratamiento_origen_id
                ]
                tratamiento_origen_df = _leer_tratamientos_guardados(
                    tratamiento_id=tratamiento_origen_id
                )

                if tratamiento_origen_df.empty:

                    st.warning("No se encontró el registro origen")

                else:

                    tratamiento_origen = tratamiento_origen_df.iloc[0]

                    st.write(
                        "Origen: "
                        f"campaña {_texto(tratamiento_origen['campana'])} · "
                        f"cultivo {_texto(tratamiento_origen['cultivo'])} · "
                        f"parcelas {_texto(tratamiento_resumen['parcelas']) or 'Sin parcelas'} · "
                        f"aplicador {_texto(tratamiento_origen['aplicador']) or 'Sin aplicador'}"
                    )

                    with st.form(
                        f"dup_trat_form_{tratamiento_origen_id}"
                    ):

                        columna_inicio_copia, columna_fin_copia = st.columns(2)

                        with columna_inicio_copia:

                            fecha_inicio_copia_texto = st.text_input(
                                "Fecha inicio tratamiento",
                                value=formatear_fecha_es(
                                    tratamiento_origen["fecha_inicio"]
                                ),
                                placeholder="DD/MM/AAAA",
                                key=f"dup_trat_fecha_inicio_{tratamiento_origen_id}"
                            )

                        with columna_fin_copia:

                            fecha_fin_copia_texto = st.text_input(
                                "Fecha fin tratamiento",
                                value=formatear_fecha_es(
                                    tratamiento_origen["fecha_fin"]
                                ),
                                placeholder="DD/MM/AAAA",
                                key=f"dup_trat_fecha_fin_{tratamiento_origen_id}"
                            )

                        error_fecha_copia = False

                        try:

                            fecha_inicio_copia_iso = parsear_fecha_es(
                                fecha_inicio_copia_texto
                            )
                            fecha_fin_copia_iso = parsear_fecha_es(
                                fecha_fin_copia_texto
                            )
                            fecha_inicio_copia = pd.to_datetime(
                                fecha_inicio_copia_iso,
                                errors="coerce"
                            ).date() if fecha_inicio_copia_iso else None
                            fecha_fin_copia = pd.to_datetime(
                                fecha_fin_copia_iso,
                                errors="coerce"
                            ).date() if fecha_fin_copia_iso else None

                        except ValueError:

                            error_fecha_copia = True
                            fecha_inicio_copia = None
                            fecha_fin_copia = None

                        campana_origen = _entero_o_none(
                            tratamiento_origen["campana_id"]
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

                        resultado_campana_copia = {
                            "campana": None,
                            "estado": "sin_campana",
                            "mensaje": ""
                        }
                        conn_campanas_copia = conectar()

                        try:

                            resultado_campana_copia = (
                                obtener_campana_por_intervalo(
                                    conn_campanas_copia,
                                    fecha_inicio_copia,
                                    fecha_fin_copia
                                )
                            )

                        finally:

                            conn_campanas_copia.close()

                        campana_sugerida_copia = resultado_campana_copia[
                            "campana"
                        ]
                        campana_difiere_copia = False

                        if (
                            resultado_campana_copia["estado"]
                            == "cruza_campanas"
                        ):

                            st.error(resultado_campana_copia["mensaje"])

                        elif resultado_campana_copia["mensaje"]:

                            st.warning(resultado_campana_copia["mensaje"])

                        if (
                            campana_sugerida_copia is not None
                            and campana_sugerida_copia["id"] != campana_copia
                        ):

                            campana_difiere_copia = True
                            st.warning(
                                "La fecha del tratamiento corresponde a la "
                                f"campaña {campana_sugerida_copia['nombre']}, "
                                "pero la copia conservará la campaña original "
                                f"{_texto(tratamiento_origen['campana'])}."
                            )

                        validacion_fecha_copia = validar_intervalo_en_campana(
                            campana_copia,
                            fecha_inicio_copia,
                            fecha_fin_copia
                        )
                        confirmar_fecha_copia = False

                        if validacion_fecha_copia["requiere_confirmacion"]:

                            st.warning(validacion_fecha_copia["mensaje"])

                        elif validacion_fecha_copia["mensaje"]:

                            st.info(validacion_fecha_copia["mensaje"])

                        if (
                            validacion_fecha_copia["requiere_confirmacion"]
                            or campana_difiere_copia
                        ):

                            confirmar_fecha_copia = st.checkbox(
                                "Confirmo expresamente que quiero guardar esta "
                                "copia en la campaña original aunque sus fechas "
                                "no correspondan a su periodo oficial",
                                key=f"dup_trat_confirm_fecha_{tratamiento_origen_id}"
                            )

                        producto_ids = productos["id"].astype(int).tolist()
                        producto_origen_id = _entero_o_none(
                            tratamiento_origen["producto_id"]
                        )
                        opciones_producto_copia = [None] + producto_ids
                        indice_producto_copia = (
                            opciones_producto_copia.index(producto_origen_id)
                            if producto_origen_id in producto_ids
                            else 0
                        )
                        producto_copia = st.selectbox(
                            "Producto",
                            opciones_producto_copia,
                            index=indice_producto_copia,
                            format_func=lambda valor: (
                                "Selecciona producto..."
                                if valor is None
                                else _etiqueta_producto_fito(
                                    _fila_por_id(productos, valor)
                                )
                            ),
                            key=f"dup_trat_producto_{tratamiento_origen_id}"
                        )
                        plaga_copia = st.text_input(
                            "Plaga / enfermedad",
                            value=_texto(tratamiento_origen["plaga"]),
                            key=f"dup_trat_plaga_{tratamiento_origen_id}"
                        )
                        observaciones_copia = st.text_area(
                            "Observaciones",
                            value=_texto(tratamiento_origen["observaciones"]),
                            key=f"dup_trat_obs_{tratamiento_origen_id}"
                        )
                        confirmar_copia = st.checkbox(
                            "Confirmo que quiero crear una copia nueva de este registro",
                            key=f"dup_trat_confirm_{tratamiento_origen_id}"
                        )
                        crear_copia = st.form_submit_button(
                            "Crear copia como nuevo registro",
                            key=f"dup_trat_btn_{tratamiento_origen_id}"
                        )

                    if crear_copia:

                        if not confirmar_copia:

                            st.warning(
                                "Marca la confirmación para crear la copia"
                            )

                        elif error_fecha_copia:

                            st.warning("La fecha debe tener formato DD/MM/AAAA")

                        elif fecha_inicio_copia is None:

                            st.warning("La fecha de inicio es obligatoria")

                        elif fecha_fin_copia is None:

                            st.warning("La fecha de fin es obligatoria")

                        elif fecha_fin_copia < fecha_inicio_copia:

                            st.warning(
                                "La fecha de fin no puede ser anterior a la "
                                "fecha de inicio"
                            )

                        elif (
                            (
                                validacion_fecha_copia["requiere_confirmacion"]
                                or campana_difiere_copia
                            )
                            and not confirmar_fecha_copia
                        ):

                            st.warning(
                                "Marca la confirmación de fechas fuera de campaña"
                            )

                        elif producto_copia is None:

                            st.warning(
                                "Selecciona un producto fitosanitario para la copia"
                            )

                        else:

                            parcelas_copia = leer(
                                """
                                SELECT parcela_id, superficie
                                FROM tratamiento_parcelas
                                WHERE tratamiento_id=?
                                ORDER BY rowid, parcela_id
                                """,
                                (tratamiento_origen_id,)
                            )
                            conn = conectar()

                            try:

                                conn.execute("BEGIN")
                                detalles_copia = _detalles_actuacion_registro(
                                    conn,
                                    "tratamiento_cultivos",
                                    "tratamiento_id",
                                    tratamiento_origen_id,
                                )
                                parcelas_compatibles_copia = (
                                    _parcelas_compatibilidad_detalles(
                                        detalles_copia
                                    )
                                    if detalles_copia
                                    else [
                                        {
                                            "parcela_id": int(
                                                parcela["parcela_id"]
                                            ),
                                            "superficie": _numero(
                                                parcela["superficie"]
                                            ),
                                        }
                                        for _, parcela
                                        in parcelas_copia.iterrows()
                                    ]
                                )
                                producto_copia_fila = _fila_por_id(
                                    productos,
                                    producto_copia,
                                )
                                nuevo_tratamiento_id = (
                                    _insertar_tratamiento_compatible(
                                        conn,
                                        {
                                            "campana_id": campana_copia,
                                            "fecha": (
                                                fecha_inicio_copia.isoformat()
                                            ),
                                            "fecha_inicio": (
                                                fecha_inicio_copia.isoformat()
                                            ),
                                            "fecha_fin": (
                                                fecha_fin_copia.isoformat()
                                            ),
                                            "producto_id": int(producto_copia),
                                            "producto": (
                                                _texto(
                                                    producto_copia_fila.get(
                                                        "nombre"
                                                    )
                                                )
                                                if producto_copia_fila
                                                is not None
                                                else ""
                                            ),
                                            "plaga_motivo": plaga_copia.strip(),
                                            "plaga": plaga_copia.strip(),
                                            "problema": plaga_copia.strip(),
                                            "justificacion": _texto(
                                                tratamiento_origen[
                                                    "justificacion"
                                                ]
                                            ),
                                            "dosis": _texto(
                                                tratamiento_origen["dosis"]
                                            ),
                                            "caldo": _numero(
                                                tratamiento_origen["caldo"]
                                            ),
                                            "aplicador": _texto(
                                                tratamiento_origen["aplicador"]
                                            ),
                                            "aplicador_id": _entero_o_none(
                                                tratamiento_origen[
                                                    "aplicador_id"
                                                ]
                                            ),
                                            "equipo": _texto(
                                                tratamiento_origen["equipo"]
                                            ),
                                            "equipo_id": _entero_o_none(
                                                tratamiento_origen["equipo_id"]
                                            ),
                                            "equipo_aplicacion_id": (
                                                _entero_o_none(
                                                    tratamiento_origen[
                                                        "equipo_aplicacion_id"
                                                    ]
                                                )
                                            ),
                                            "maquinaria_id": _entero_o_none(
                                                tratamiento_origen[
                                                    "maquinaria_id"
                                                ]
                                            ),
                                            "cultivo_id": _entero_o_none(
                                                tratamiento_origen["cultivo_id"]
                                            ),
                                            "superficie_tratada": _numero(
                                                tratamiento_origen[
                                                    "superficie_tratada"
                                                ]
                                            ),
                                            "plazo_seguridad": _texto(
                                                tratamiento_origen[
                                                    "plazo_seguridad"
                                                ]
                                            ),
                                            "fecha_recoleccion_segura": _texto(
                                                tratamiento_origen[
                                                    "fecha_recoleccion_segura"
                                                ]
                                            ),
                                            "condiciones": _texto(
                                                tratamiento_origen[
                                                    "condiciones_meteorologicas"
                                                ]
                                            ),
                                            "condiciones_meteorologicas": (
                                                _texto(
                                                    tratamiento_origen[
                                                        "condiciones_meteorologicas"
                                                    ]
                                                )
                                            ),
                                            "eficacia": "",
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
                                    "No se pudo crear la copia de tratamiento: "
                                    f"{exc}"
                                )

                            else:

                                st.session_state[
                                    "duplicar_tratamiento_mensaje"
                                ] = (
                                    "Copia de tratamiento creada como nuevo "
                                    f"registro #{nuevo_tratamiento_id}"
                                )
                                for clave in claves_duplicar_tratamiento:

                                    st.session_state.pop(clave, None)

                                st.rerun()

                            finally:

                                conn.close()


    if seccion_tratamientos == "✏️ Editar":

        st.subheader("Edición segura de tratamientos")

        tratamientos_listado_visible = tratamientos_listado.drop(
            columns=["recetas_count"],
            errors="ignore"
        )
        tratamientos_filtrados_editor = mostrar_filtros_dataframe(
            tratamientos_listado_visible,
            "tratamientos_editar",
            columnas_texto=[
                "producto",
                "cultivo",
                "parcelas",
                "observaciones",
                "plaga",
                "eficacia",
                "aplicador",
                "equipo",
                "recetas"
            ],
            columna_fecha="fecha_inicio",
            columna_fecha_fin="fecha_fin",
            filtros_select={
                "Campaña": "campana",
                "Cultivo": "cultivo",
                "Producto": "producto",
                "Plaga": "plaga",
                "Aplicador": "aplicador",
                "Equipo": "equipo"
            }
        )

        tratamientos_editor = _leer_tratamientos_guardados()

        ids_tratamientos_visibles = (
            tratamientos_filtrados_editor["id"].astype(int).tolist()
            if "id" in tratamientos_filtrados_editor
            else []
        )

        tratamientos_editor = tratamientos_editor[
            tratamientos_editor["id"].astype(int).isin(ids_tratamientos_visibles)
        ].copy()
        recetas_guardadas = leer_recetas_tratamientos()

        if "recetas_count" in tratamientos_editor.columns:

            tratamientos_editor["recetas"] = (
                tratamientos_editor["recetas_count"].fillna(0).astype(int)
                .apply(_texto_recetas)
            )
            tratamientos_editor = tratamientos_editor.drop(
                columns=["recetas_count"]
            )

        if "eficacia" in tratamientos_editor.columns:

            tratamientos_editor["eficacia"] = (
                tratamientos_editor["eficacia"].apply(_normalizar_eficacia)
            )

        if tratamientos_editor.empty:

            st.info("No hay tratamientos visibles para editar")

        else:

            with st.expander("Asignar parcelas"):

                parcelas_editor = leer(
                    """
                    SELECT id,nombre,poligono,parcela,recinto,superficie_sigpac
                    FROM parcelas
                    ORDER BY nombre,poligono,parcela,recinto,id
                    """
                )

                if parcelas_editor.empty:

                    st.info("No hay parcelas registradas para asignar")

                else:

                    tratamientos_parcelas_por_id = (
                        tratamientos_editor
                        .copy()
                        .set_index("id", drop=False)
                    )
                    ids_tratamientos_parcelas = [
                        int(valor)
                        for valor in tratamientos_parcelas_por_id.index.tolist()
                    ]
                    tratamiento_parcelas_id = st.selectbox(
                        "Tratamiento",
                        ids_tratamientos_parcelas,
                        format_func=lambda valor: _formatear_tratamiento_recetas(
                            valor,
                            tratamientos_editor
                        ),
                        key="tratamientos_asignar_parcelas_id"
                    )
                    parcelas_actuales = leer(
                        """
                        SELECT parcela_id
                        FROM tratamiento_parcelas
                        WHERE tratamiento_id=?
                        ORDER BY rowid, parcela_id
                        """,
                        (int(tratamiento_parcelas_id),)
                    )
                    ids_parcelas_actuales = (
                        parcelas_actuales["parcela_id"]
                        .dropna()
                        .astype(int)
                        .tolist()
                        if not parcelas_actuales.empty
                        else []
                    )
                    ids_parcelas_disponibles = (
                        parcelas_editor["id"].astype(int).tolist()
                    )
                    parcelas_por_id = parcelas_editor.set_index(
                        "id",
                        drop=False
                    )
                    parcelas_sel_editor = st.multiselect(
                        "Parcelas",
                        ids_parcelas_disponibles,
                        default=[
                            parcela_id
                            for parcela_id in ids_parcelas_actuales
                            if parcela_id in ids_parcelas_disponibles
                        ],
                        format_func=lambda valor: _etiqueta_parcela(
                            parcelas_por_id.loc[valor]
                        ),
                        key=(
                            "tratamientos_parcelas_selector_"
                            f"{tratamiento_parcelas_id}"
                        )
                    )
                    confirmar_parcelas_tratamiento = st.checkbox(
                        "Confirmo que quiero actualizar las parcelas de este tratamiento",
                        key=(
                            "tratamientos_confirmar_parcelas_"
                            f"{tratamiento_parcelas_id}"
                        )
                    )

                    if st.button(
                        "Guardar parcelas",
                        key=(
                            "tratamientos_guardar_parcelas_"
                            f"{tratamiento_parcelas_id}"
                        ),
                        type="primary",
                    ):

                        if not confirmar_parcelas_tratamiento:

                            st.warning("Marca la confirmación antes de guardar")

                        elif not parcelas_sel_editor:

                            st.warning("Selecciona al menos una parcela")

                        else:

                            conn = conectar()

                            try:

                                conn.execute("BEGIN")
                                conn.execute(
                                    """
                                    DELETE FROM tratamiento_parcelas
                                    WHERE tratamiento_id=?
                                    """,
                                    (int(tratamiento_parcelas_id),)
                                )

                                for parcela_id in parcelas_sel_editor:

                                    superficie = pd.to_numeric(
                                        parcelas_por_id.loc[
                                            int(parcela_id),
                                            "superficie_sigpac"
                                        ],
                                        errors="coerce"
                                    )
                                    conn.execute(
                                        """
                                        INSERT INTO tratamiento_parcelas
                                        (tratamiento_id,parcela_id,superficie)
                                        VALUES (?,?,?)
                                        """,
                                        (
                                            int(tratamiento_parcelas_id),
                                            int(parcela_id),
                                            (
                                                None
                                                if pd.isna(superficie)
                                                else float(superficie)
                                            )
                                        )
                                    )

                                conn.commit()

                            except sqlite3.Error:

                                conn.rollback()
                                raise

                            finally:

                                conn.close()

                            st.success("Parcelas de tratamiento actualizadas")
                            st.rerun()

            st.markdown("### Recetas adjuntas")
            ids_tratamientos_recetas = (
                tratamientos_editor["id"].astype(int).tolist()
            )
            tratamiento_recetas_id = st.selectbox(
                "Tratamiento para gestionar recetas",
                ids_tratamientos_recetas,
                format_func=lambda valor: _formatear_tratamiento_recetas(
                    valor,
                    tratamientos_editor
                ),
                key="tratamientos_recetas_tratamiento_id"
            )
            recetas_tratamiento_editor = recetas_guardadas[
                recetas_guardadas["tratamiento_id"].astype(int)
                == int(tratamiento_recetas_id)
            ].copy()

            if recetas_tratamiento_editor.empty:

                st.info("Este tratamiento no tiene recetas adjuntas")

            else:

                listado_recetas = recetas_tratamiento_editor[
                    [
                        "id",
                        "nombre_original",
                        "size_bytes",
                        "created_at",
                    ]
                ].copy()
                listado_recetas["size_bytes"] = (
                    listado_recetas["size_bytes"].apply(_formatear_bytes)
                )
                st.dataframe(
                    preparar_dataframe_visual(
                        listado_recetas,
                        mostrar_id=True
                    ),
                    hide_index=True,
                    use_container_width=True
                )

                for _, receta in recetas_tratamiento_editor.iterrows():

                    try:

                        ruta_receta = ruta_receta_absoluta(
                            receta["ruta_relativa"]
                        )
                        datos_receta = ruta_receta.read_bytes()

                    except (OSError, ValueError):

                        st.warning(
                            "No se pudo abrir la receta "
                            f"{receta['nombre_original']}"
                        )
                        continue

                    st.download_button(
                        f"Descargar {receta['nombre_original']}",
                        datos_receta,
                        file_name=receta["nombre_original"],
                        mime="application/pdf",
                        key=f"descargar_receta_{int(receta['id'])}"
                    )

            nuevas_recetas_editor = st.file_uploader(
                "Añadir recetas PDF a este tratamiento",
                type=["pdf"],
                accept_multiple_files=True,
                key=f"tratamientos_nuevas_recetas_{tratamiento_recetas_id}"
            )

            if st.button(
                "Añadir recetas PDF",
                key=f"tratamientos_guardar_recetas_{tratamiento_recetas_id}"
            ):

                if not nuevas_recetas_editor:

                    st.warning("Selecciona al menos una receta PDF")

                else:

                    conn = conectar()

                    try:

                        conn.execute("BEGIN")
                        resultado_recetas_editor = guardar_recetas_pdf(
                            conn,
                            tratamiento_recetas_id,
                            nuevas_recetas_editor
                        )
                        conn.commit()

                    except (sqlite3.Error, OSError, ValueError) as error:

                        conn.rollback()
                        st.error(f"No se pudieron guardar las recetas: {error}")

                    else:

                        for error_receta in resultado_recetas_editor["errores"]:

                            st.warning(error_receta)

                        if resultado_recetas_editor["guardados"]:

                            st.success("Recetas guardadas")
                            st.rerun()

                        else:

                            st.warning("No se guardó ninguna receta")

                    finally:

                        conn.close()

            if not recetas_tratamiento_editor.empty:

                recetas_por_id = recetas_tratamiento_editor.set_index(
                    "id",
                    drop=False
                )
                receta_eliminar_id = st.selectbox(
                    "Receta a eliminar",
                    recetas_por_id.index.astype(int).tolist(),
                    format_func=lambda valor: (
                        recetas_por_id.loc[valor]["nombre_original"]
                    ),
                    key=f"tratamientos_eliminar_receta_id_{tratamiento_recetas_id}"
                )
                confirmar_eliminar_receta = st.checkbox(
                    "Confirmo que quiero eliminar esta receta adjunta",
                    key=(
                        "tratamientos_confirmar_eliminar_receta_"
                        f"{tratamiento_recetas_id}"
                    )
                )

                if st.button(
                    "Eliminar receta adjunta",
                    key=f"tratamientos_eliminar_receta_{tratamiento_recetas_id}"
                ):

                    if not confirmar_eliminar_receta:

                        st.warning("Marca la confirmación antes de eliminar")

                    else:

                        conn = conectar()
                        ruta_eliminar = None

                        try:

                            conn.execute("BEGIN")
                            ruta_eliminar = eliminar_documento_receta(
                                conn,
                                receta_eliminar_id
                            )
                            conn.commit()

                        except sqlite3.Error as error:

                            conn.rollback()
                            st.error(
                                "No se pudo eliminar la receta adjunta: "
                                f"{error}"
                            )

                        else:

                            try:

                                eliminar_archivo_receta(ruta_eliminar)

                            except (OSError, ValueError) as error:

                                st.warning(
                                    "La receta se desvinculó, pero no se "
                                    f"pudo borrar el archivo físico: {error}"
                                )

                            st.success("Receta adjunta eliminada")
                            st.rerun()

                        finally:

                            conn.close()

            for columna in [
                "fecha_inicio",
                "fecha_fin",
                "fecha_recoleccion_segura"
            ]:

                if columna in tratamientos_editor.columns:

                    tratamientos_editor[columna] = pd.to_datetime(
                        tratamientos_editor[columna],
                        errors="coerce"
                    )

            def registrar_opcion(opciones, etiqueta_a_id, id_a_etiqueta, base, registro_id):

                etiqueta = _texto(base)

                if not etiqueta:

                    etiqueta = "Sin nombre"

                etiqueta_unica = etiqueta
                contador = 2

                while etiqueta_unica in etiqueta_a_id:

                    etiqueta_unica = f"{etiqueta} ({contador})"
                    contador += 1

                opciones.append(etiqueta_unica)
                etiqueta_a_id[etiqueta_unica] = registro_id

                if registro_id is not None:

                    id_a_etiqueta[int(registro_id)] = etiqueta_unica

                return etiqueta_unica

            opciones_producto = ["Sin producto estructurado"]
            producto_etiqueta_a_id = {"Sin producto estructurado": None}
            producto_id_a_etiqueta = {}

            for _, fila_producto in productos.iterrows():

                registrar_opcion(
                    opciones_producto,
                    producto_etiqueta_a_id,
                    producto_id_a_etiqueta,
                    _etiqueta_producto_fito(fila_producto),
                    int(fila_producto["id"]),
                )

            opciones_cultivo_editor = ["Sin cultivo estructurado"]
            cultivo_etiqueta_a_id = {"Sin cultivo estructurado": None}
            cultivo_id_a_etiqueta = {}

            for _, fila_cultivo in cultivos.iterrows():

                registrar_opcion(
                    opciones_cultivo_editor,
                    cultivo_etiqueta_a_id,
                    cultivo_id_a_etiqueta,
                    _etiqueta_cultivo_v6(fila_cultivo),
                    int(fila_cultivo["id"]),
                )

            opciones_aplicador = ["Sin aplicador"]
            aplicador_etiqueta_a_id = {"Sin aplicador": None}
            aplicador_id_a_etiqueta = {}

            for _, fila_aplicador in aplicadores.iterrows():

                registrar_opcion(
                    opciones_aplicador,
                    aplicador_etiqueta_a_id,
                    aplicador_id_a_etiqueta,
                    _etiqueta_persona(fila_aplicador),
                    int(fila_aplicador["id"]),
                )

            opciones_equipo = ["Sin equipo"]
            equipo_etiqueta_a_id = {"Sin equipo": None}
            equipo_id_a_etiqueta = {}

            for _, fila_equipo in equipos.iterrows():

                registrar_opcion(
                    opciones_equipo,
                    equipo_etiqueta_a_id,
                    equipo_id_a_etiqueta,
                    _etiqueta_equipo_aplicacion(fila_equipo),
                    int(fila_equipo["id"]),
                )

            def etiqueta_producto_editor(fila):

                producto_id = _entero_o_none(fila.get("producto_id"))

                if producto_id in producto_id_a_etiqueta:

                    return producto_id_a_etiqueta[producto_id]

                etiqueta = _texto(fila.get("producto"))

                if etiqueta:

                    etiqueta = f"Texto legacy: {etiqueta}"
                    if etiqueta not in producto_etiqueta_a_id:

                        producto_etiqueta_a_id[etiqueta] = None
                        opciones_producto.append(etiqueta)

                    return etiqueta

                return opciones_producto[0] if opciones_producto else ""

            def etiqueta_cultivo_editor(fila):

                cultivo_id = _entero_o_none(fila.get("cultivo_id"))

                if cultivo_id in cultivo_id_a_etiqueta:

                    return cultivo_id_a_etiqueta[cultivo_id]

                return "Sin cultivo estructurado"

            def etiqueta_aplicador_editor(fila):

                aplicador_id = _entero_o_none(fila.get("aplicador_id"))

                if aplicador_id in aplicador_id_a_etiqueta:

                    return aplicador_id_a_etiqueta[aplicador_id]

                aplicador_texto = _texto(fila.get("aplicador"))

                if aplicador_texto:

                    etiqueta = f"Texto legacy: {aplicador_texto}"

                    if etiqueta not in aplicador_etiqueta_a_id:

                        aplicador_etiqueta_a_id[etiqueta] = None
                        opciones_aplicador.append(etiqueta)

                    return etiqueta

                return "Sin aplicador"

            def etiqueta_equipo_editor(fila):

                equipo_id = (
                    _entero_o_none(fila.get("equipo_aplicacion_id"))
                    or _entero_o_none(fila.get("equipo_id"))
                )

                if equipo_id in equipo_id_a_etiqueta:

                    return equipo_id_a_etiqueta[equipo_id]

                equipo_texto = _texto(fila.get("equipo"))

                if equipo_texto:

                    etiqueta = f"Texto legacy: {equipo_texto}"

                    if etiqueta not in equipo_etiqueta_a_id:

                        equipo_etiqueta_a_id[etiqueta] = None
                        opciones_equipo.append(etiqueta)

                    return etiqueta

                return "Sin equipo"

            tratamientos_editor["producto_selector"] = (
                tratamientos_editor.apply(etiqueta_producto_editor, axis=1)
            )
            tratamientos_editor["cultivo_selector"] = (
                tratamientos_editor.apply(etiqueta_cultivo_editor, axis=1)
            )
            tratamientos_editor["aplicador_selector"] = (
                tratamientos_editor.apply(etiqueta_aplicador_editor, axis=1)
            )
            tratamientos_editor["equipo_selector"] = (
                tratamientos_editor.apply(etiqueta_equipo_editor, axis=1)
            )

            tratamientos_editor_visible = tratamientos_editor.drop(
                columns=[
                    "cultivo",
                    "cultivo_id",
                    "producto",
                    "registro_producto",
                    "producto_id",
                    "aplicador",
                    "aplicador_id",
                    "equipo",
                    "equipo_id",
                    "equipo_aplicacion_id",
                    "maquinaria_id",
                    "campana_id",
                    "cultivos_detalle",
                    "parcelas_detalle",
                    "superficie_detalle",
                    "tiene_detalle_multicultivo",
                ],
                errors="ignore"
            )

            column_config_tratamientos = preparar_column_config_visual(
                tratamientos_editor_visible
            )
            column_config_tratamientos.update({
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "campana": st.column_config.TextColumn(
                    "Campaña",
                    disabled=True
                ),
                "fecha_inicio": st.column_config.DateColumn(
                    "Fecha inicio",
                    format="DD/MM/YYYY",
                    required=True
                ),
                "fecha_fin": st.column_config.DateColumn(
                    "Fecha fin",
                    format="DD/MM/YYYY",
                    required=True
                ),
                "producto_selector": st.column_config.SelectboxColumn(
                    "Producto",
                    options=opciones_producto,
                    required=True
                ),
                "cultivo_selector": st.column_config.SelectboxColumn(
                    "Cultivo",
                    options=opciones_cultivo_editor
                ),
                "aplicador_selector": st.column_config.SelectboxColumn(
                    "Aplicador",
                    options=opciones_aplicador
                ),
                "equipo_selector": st.column_config.SelectboxColumn(
                    "Equipo aplicación",
                    options=opciones_equipo
                ),
                "caldo": st.column_config.NumberColumn(
                    "Caldo",
                    min_value=0.0
                ),
                "superficie_tratada": st.column_config.NumberColumn(
                    "Superficie tratada",
                    min_value=0.0
                ),
                "fecha_recoleccion_segura": st.column_config.DateColumn(
                    "Fecha recolección segura",
                    format="DD/MM/YYYY"
                ),
                "eficacia": st.column_config.SelectboxColumn(
                    "Eficacia",
                    options=["", "B", "R", "M"]
                ),
            })
            tratamientos_editados = st.data_editor(
                tratamientos_editor_visible,
                num_rows="fixed",
                disabled=[
                    "id",
                    "campana",
                    "recetas"
                ],
                hide_index=True,
                use_container_width=True,
                column_order=[
                    "id",
                    "campana",
                    "fecha_inicio",
                    "fecha_fin",
                    "cultivo_selector",
                    "producto_selector",
                    "dosis",
                    "caldo",
                    "aplicador_selector",
                    "equipo_selector",
                    "plaga",
                    "justificacion",
                    "eficacia",
                    "superficie_tratada",
                    "condiciones_meteorologicas",
                    "plazo_seguridad",
                    "fecha_recoleccion_segura",
                    "observaciones",
                    "recetas"
                ],
                column_config=column_config_tratamientos,
                key="editor_seguro_tratamientos"
            )

            confirmar_tratamientos = st.checkbox(
                "Confirmo que quiero guardar los cambios de tratamientos",
                key="confirmar_edicion_segura_tratamientos"
            )
            confirmar_fechas_tratamientos = st.checkbox(
                "Confirmo que quiero guardar tratamientos con fechas fuera de "
                "la campaña asociada",
                key="confirmar_fechas_fuera_tratamientos_editor"
            )

            if st.button(
                "Guardar cambios de tratamientos",
                key="guardar_edicion_segura_tratamientos"
            ):

                ids_originales = tratamientos_editor["id"].astype(int).tolist()
                ids_editados = tratamientos_editados["id"].astype(int).tolist()
                errores = []
                avisos_fechas = []

                if not confirmar_tratamientos:

                    errores.append(
                        "Marca la confirmación antes de guardar tratamientos"
                    )

                if ids_editados != ids_originales:

                    errores.append("No se permite añadir, borrar ni cambiar IDs")

                tratamientos_para_guardar = tratamientos_editados.copy()
                campana_por_tratamiento = (
                    tratamientos_editor
                    .set_index("id")["campana_id"]
                )
                tratamientos_para_guardar["campana_id"] = (
                    tratamientos_para_guardar["id"].map(
                        campana_por_tratamiento
                    )
                )

                for columna in [
                    "dosis",
                    "plaga",
                    "justificacion",
                    "condiciones_meteorologicas",
                    "plazo_seguridad",
                    "eficacia",
                    "observaciones"
                ]:

                    tratamientos_para_guardar[columna] = (
                        tratamientos_para_guardar[columna]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )

                tratamientos_para_guardar["fecha_inicio"] = pd.to_datetime(
                    tratamientos_para_guardar["fecha_inicio"],
                    errors="coerce"
                )
                tratamientos_para_guardar["fecha_fin"] = pd.to_datetime(
                    tratamientos_para_guardar["fecha_fin"],
                    errors="coerce"
                )
                tratamientos_para_guardar["fecha_recoleccion_segura"] = (
                    pd.to_datetime(
                        tratamientos_para_guardar["fecha_recoleccion_segura"],
                        errors="coerce"
                    )
                )
                tratamientos_para_guardar["producto_id"] = (
                    tratamientos_para_guardar["producto_selector"]
                    .map(producto_etiqueta_a_id)
                )
                tratamientos_para_guardar["cultivo_id"] = (
                    tratamientos_para_guardar["cultivo_selector"]
                    .map(cultivo_etiqueta_a_id)
                )
                tratamientos_para_guardar["aplicador_id"] = (
                    tratamientos_para_guardar["aplicador_selector"]
                    .map(aplicador_etiqueta_a_id)
                )
                tratamientos_para_guardar["equipo_aplicacion_id"] = (
                    tratamientos_para_guardar["equipo_selector"]
                    .map(equipo_etiqueta_a_id)
                )

                for columna in [
                    "campana_id",
                    "producto_id",
                    "cultivo_id",
                    "aplicador_id",
                    "equipo_aplicacion_id",
                    "caldo",
                    "superficie_tratada"
                ]:

                    tratamientos_para_guardar[columna] = pd.to_numeric(
                        tratamientos_para_guardar[columna],
                        errors="coerce"
                    )

                productos_validos = set(productos["id"].astype(int).tolist())
                cultivos_validos = set(cultivos["id"].astype(int).tolist())
                aplicadores_validos = set(
                    personas_tratamiento["id"].astype(int).tolist()
                )
                equipos_validos = set(equipos["id"].astype(int).tolist())
                conn_campanas_editor = conectar()

                try:

                    for _, fila in tratamientos_para_guardar.iterrows():

                        etiqueta = f"ID {int(fila['id'])}"

                        if pd.isna(fila["fecha_inicio"]):

                            errores.append(f"{etiqueta}: fecha_inicio obligatoria")

                        if pd.isna(fila["fecha_fin"]):

                            errores.append(f"{etiqueta}: fecha_fin obligatoria")

                        if (
                            not pd.isna(fila["fecha_inicio"])
                            and not pd.isna(fila["fecha_fin"])
                            and fila["fecha_fin"] < fila["fecha_inicio"]
                        ):

                            errores.append(
                                f"{etiqueta}: fecha_fin no puede ser anterior a "
                                "fecha_inicio"
                            )

                        if pd.isna(fila["producto_id"]) or int(
                            fila["producto_id"]
                        ) not in productos_validos:

                            errores.append(f"{etiqueta}: producto no válido")

                        if (
                            not pd.isna(fila["cultivo_id"])
                            and int(fila["cultivo_id"]) not in cultivos_validos
                        ):

                            errores.append(f"{etiqueta}: cultivo no válido")

                        if (
                            not pd.isna(fila["aplicador_id"])
                            and int(fila["aplicador_id"])
                            not in aplicadores_validos
                        ):

                            errores.append(f"{etiqueta}: aplicador no válido")

                        if (
                            not pd.isna(fila["equipo_aplicacion_id"])
                            and int(fila["equipo_aplicacion_id"])
                            not in equipos_validos
                        ):

                            errores.append(
                                f"{etiqueta}: equipo de aplicación no válido"
                            )

                        if pd.isna(fila["superficie_tratada"]):

                            errores.append(
                                f"{etiqueta}: superficie_tratada debe ser numérica"
                            )

                        elif fila["superficie_tratada"] < 0:

                            errores.append(
                                f"{etiqueta}: superficie_tratada no puede ser "
                                "negativa"
                            )

                        if not pd.isna(fila["caldo"]) and fila["caldo"] < 0:

                            errores.append(
                                f"{etiqueta}: caldo no puede ser negativo"
                            )

                        if (
                            not pd.isna(fila["campana_id"])
                            and not pd.isna(fila["fecha_inicio"])
                            and not pd.isna(fila["fecha_fin"])
                        ):

                            validacion = validar_intervalo_en_campana(
                                int(fila["campana_id"]),
                                fila["fecha_inicio"].date(),
                                fila["fecha_fin"].date()
                            )

                            if validacion["mensaje"]:

                                avisos_fechas.append(
                                    f"{etiqueta}: {validacion['mensaje']}"
                                )

                            if validacion["requiere_confirmacion"]:

                                resultado_campana = obtener_campana_por_intervalo(
                                    conn_campanas_editor,
                                    fila["fecha_inicio"].date(),
                                    fila["fecha_fin"].date()
                                )

                                if (
                                    resultado_campana["estado"]
                                    == "cruza_campanas"
                                ):

                                    errores.append(
                                        f"{etiqueta}: "
                                        f"{resultado_campana['mensaje']}"
                                    )

                                elif not confirmar_fechas_tratamientos:

                                    errores.append(
                                        f"{etiqueta}: confirma las fechas fuera "
                                        "de campaña para guardar"
                                    )

                finally:

                    conn_campanas_editor.close()

                if errores:

                    for error in errores:

                        st.error(error)

                else:

                    for aviso in dict.fromkeys(avisos_fechas):

                        st.warning(aviso)

                    nombres_aplicadores = {
                        int(fila["id"]): fila["nombre"]
                        for _, fila in personas_tratamiento.iterrows()
                    }
                    tratamientos_originales_por_id = (
                        tratamientos_editor
                        .copy()
                        .set_index("id", drop=False)
                    )
                    conn = conectar()

                    try:

                        for _, fila in tratamientos_para_guardar.iterrows():

                            original = tratamientos_originales_por_id.loc[
                                int(fila["id"])
                            ]
                            aplicador_id = (
                                None
                                if pd.isna(fila["aplicador_id"])
                                else int(fila["aplicador_id"])
                            )
                            aplicador_texto = (
                                nombres_aplicadores.get(aplicador_id, "")
                                if aplicador_id is not None
                                else (
                                    _texto(original["aplicador"])
                                    if _texto(
                                        fila.get("aplicador_selector")
                                    ).startswith("Texto legacy:")
                                    else ""
                                )
                            )
                            equipo_id = (
                                None
                                if pd.isna(fila["equipo_aplicacion_id"])
                                else int(fila["equipo_aplicacion_id"])
                            )
                            cultivo_id = (
                                None
                                if pd.isna(fila["cultivo_id"])
                                else int(fila["cultivo_id"])
                            )
                            caldo_guardar = (
                                None
                                if pd.isna(fila["caldo"])
                                else float(fila["caldo"])
                            )
                            fecha_recoleccion_guardar = (
                                None
                                if pd.isna(fila["fecha_recoleccion_segura"])
                                else (
                                    fila["fecha_recoleccion_segura"]
                                    .date()
                                    .isoformat()
                                )
                            )
                            producto_fila = _fila_por_id(
                                productos,
                                int(fila["producto_id"]),
                            )
                            equipo_fila = (
                                _fila_por_id(equipos, equipo_id)
                                if equipo_id is not None
                                else None
                            )

                            _actualizar_tratamiento_compatible(
                                conn,
                                fila["id"],
                                {
                                    "fecha": (
                                        fila["fecha_inicio"]
                                        .date()
                                        .isoformat()
                                    ),
                                    "fecha_inicio": (
                                        fila["fecha_inicio"]
                                        .date()
                                        .isoformat()
                                    ),
                                    "fecha_fin": (
                                        fila["fecha_fin"]
                                        .date()
                                        .isoformat()
                                    ),
                                    "producto_id": int(fila["producto_id"]),
                                    "producto": (
                                        _texto(producto_fila.get("nombre"))
                                        if producto_fila is not None
                                        else _texto(original["producto"])
                                    ),
                                    "cultivo_id": cultivo_id,
                                    "aplicador": aplicador_texto,
                                    "aplicador_id": aplicador_id,
                                    "equipo": (
                                        _texto(equipo_fila.get("nombre"))
                                        if equipo_fila is not None
                                        else _texto(original["equipo"])
                                    ),
                                    "equipo_id": equipo_id,
                                    "equipo_aplicacion_id": equipo_id,
                                    "plaga_motivo": fila["plaga"],
                                    "plaga": fila["plaga"],
                                    "problema": fila["plaga"],
                                    "justificacion": fila["justificacion"],
                                    "dosis": fila["dosis"],
                                    "caldo": caldo_guardar,
                                    "superficie_tratada": float(
                                        fila["superficie_tratada"]
                                    ),
                                    "plazo_seguridad": fila["plazo_seguridad"],
                                    "fecha_recoleccion_segura": (
                                        fecha_recoleccion_guardar
                                    ),
                                    "condiciones": (
                                        fila["condiciones_meteorologicas"]
                                    ),
                                    "condiciones_meteorologicas": (
                                        fila["condiciones_meteorologicas"]
                                    ),
                                    "eficacia": _normalizar_eficacia(
                                        fila["eficacia"]
                                    ),
                                    "observaciones": fila["observaciones"],
                                },
                            )

                        conn.commit()

                    except Exception:

                        conn.rollback()
                        raise

                    finally:

                        conn.close()

                    st.success("Cambios de tratamientos guardados")
                    st.rerun()






    if seccion_tratamientos == "🗑️ Borrar":

        st.subheader("Borrado seguro")

        tratamientos_para_eliminar = _leer_tratamientos_guardados()

        if not tratamientos_para_eliminar.empty:

            tratamientos_para_eliminar = (
                tratamientos_para_eliminar[
                    ["id", "fecha_inicio", "producto", "dosis"]
                ]
                .rename(columns={"fecha_inicio": "fecha"})
                .copy()
            )
        recetas_para_borrar = leer_recetas_tratamientos()

        def borrar_archivos_recetas(ids_tratamientos):

            if recetas_para_borrar.empty:

                return

            ids = {int(valor) for valor in ids_tratamientos}
            recetas = recetas_para_borrar[
                recetas_para_borrar["tratamiento_id"].astype(int).isin(ids)
            ]

            for _, receta in recetas.iterrows():

                eliminar_archivo_receta(receta["ruta_relativa"])

        borrar_registros_seguro(
            "tratamientos",
            "id",
            tratamientos_para_eliminar,
            "tratamientos",
            tablas_hijas=[
                ("tratamiento_cultivos", "tratamiento_id"),
                ("tratamiento_parcelas", "tratamiento_id"),
                ("tratamientos_documentos", "tratamiento_id")
            ],
            campo_descripcion="producto",
            key="tratamientos",
            post_borrar=borrar_archivos_recetas
        )

    if seccion_tratamientos == "🧪 Análisis realizados":

        _render_analisis_fitosanitarios(CAMPANA, cultivos)
