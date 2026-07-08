from datetime import date, datetime
import math
import re

import pandas as pd
import streamlit as st

from core.borrado import borrar_registros_seguro
from core.db import conectar, leer
from core.filtros import mostrar_filtros_dataframe
from core.ui_tablas import preparar_dataframe_visual
from services.siex_catalogos import buscar_items_catalogo


def _normalizar_texto(valor):

    return str(valor or "").strip()


def _entero_o_none(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return None

    return int(numero)


def parsear_marco_plantacion(texto):

    texto = _normalizar_texto(texto)

    if not texto:

        return None

    texto = (
        texto
        .replace(",", ".")
        .replace("×", "x")
        .replace("X", "x")
        .replace("*", "x")
    )
    coincidencia = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*",
        texto,
    )

    if coincidencia is None:

        return None

    try:

        distancia_1 = float(coincidencia.group(1))
        distancia_2 = float(coincidencia.group(2))

    except ValueError:

        return None

    if distancia_1 <= 0 or distancia_2 <= 0:

        return None

    return distancia_1, distancia_2


def calcular_numero_arboles(superficie_ha, marco_plantacion):

    superficie = pd.to_numeric(superficie_ha, errors="coerce")
    marco = parsear_marco_plantacion(marco_plantacion)

    if pd.isna(superficie) or float(superficie) <= 0 or marco is None:

        return None

    distancia_1, distancia_2 = marco
    numero = (float(superficie) * 10000) / (distancia_1 * distancia_2)
    return int(math.floor(numero + 0.5))


def _tabla_existe_conn(conn, tabla):

    fila = conn.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type='table' AND name=?
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


def _expr_texto(tabla, columna, columnas, defecto="''"):

    if columna in columnas:

        return f"COALESCE({tabla}.{columna},{defecto})"

    return defecto


def _expr_valor(tabla, columna, columnas, defecto="NULL"):

    if columna in columnas:

        return f"{tabla}.{columna}"

    return defecto


def _anadir_si_existe(destino, columnas, columna, valor):

    if columna in columnas:

        destino[columna] = valor


def _ejecutar_insert_dinamico(conn, tabla, valores):

    nombres = list(valores)

    if not nombres:

        raise RuntimeError(f"No hay columnas compatibles para insertar {tabla}")

    cursor = conn.execute(
        f"""
        INSERT INTO {tabla}
        ({','.join(nombres)})
        VALUES ({','.join(['?'] * len(nombres))})
        """,
        [valores[columna] for columna in nombres],
    )
    return cursor.lastrowid


def _ejecutar_update_dinamico(conn, tabla, registro_id, valores):

    nombres = list(valores)

    if not nombres:

        return

    conn.execute(
        f"""
        UPDATE {tabla}
        SET {','.join(f'{columna}=?' for columna in nombres)}
        WHERE id=?
        """,
        [valores[columna] for columna in nombres] + [int(registro_id)],
    )


def _formatear_hectareas(valor):

    if pd.isna(valor):

        return "0,00"

    return (
        f"{float(valor or 0):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def _texto_parcela(fila):

    partes = [f"ID {int(fila['id'])}"]
    nombre = _normalizar_texto(fila.get("nombre"))

    if nombre:

        partes.append(nombre)

    partes.extend(
        [
            f"Polígono {_normalizar_texto(fila.get('poligono')) or '-'}",
            f"Parcela {_normalizar_texto(fila.get('parcela')) or '-'}",
            f"Recinto {_normalizar_texto(fila.get('recinto')) or '-'}",
            f"{_formatear_hectareas(fila.get('superficie_sigpac'))} ha",
        ]
    )

    return " · ".join(partes)


def _etiqueta_cultivo(fila):

    partes = [
        _normalizar_texto(fila.get("cultivo")),
        _normalizar_texto(fila.get("variedad")),
        _normalizar_texto(fila.get("sistema")),
    ]
    texto = " / ".join(parte for parte in partes if parte)
    campana = _normalizar_texto(fila.get("campana")) or "Sin campaña"
    return f"#{int(fila['id'])} · {campana} · {texto or 'Sin cultivo'}"


def _ids_desde_texto(valor):

    if not _normalizar_texto(valor):

        return []

    ids = []

    for parte in str(valor).split(","):

        numero = _entero_o_none(parte)

        if numero is not None:

            ids.append(numero)

    return ids


def _leer_campanas():

    try:

        return leer(
            """
            SELECT id,nombre,fecha_inicio,fecha_fin,activa
            FROM campanas
            ORDER BY fecha_inicio DESC,id DESC
            """
        )

    except Exception:

        return pd.DataFrame()


def _leer_parcelas():

    columnas = _columnas_tabla("parcelas")
    expr_municipio = (
        _expr_texto("parcelas", "municipio", columnas)
        if "municipio" in columnas
        else _expr_valor("parcelas", "municipio_sigpac", columnas, "''")
    )

    return leer(
        f"""
        SELECT
            parcelas.id,
            {_expr_texto("parcelas", "nombre", columnas)} AS nombre,
            {expr_municipio} AS municipio,
            {_expr_texto("parcelas", "poligono", columnas)} AS poligono,
            {_expr_texto("parcelas", "parcela", columnas)} AS parcela,
            {_expr_texto("parcelas", "recinto", columnas)} AS recinto,
            {_expr_valor("parcelas", "superficie_sigpac", columnas, "0")}
                AS superficie_sigpac
        FROM parcelas
        ORDER BY municipio,poligono,parcela,recinto,id
        """
    )


def _campana_por_defecto(campanas, valor_actual=None):

    ids = (
        campanas["id"].dropna().astype(int).tolist()
        if not campanas.empty and "id" in campanas.columns
        else []
    )

    valor_actual = _entero_o_none(valor_actual)

    if valor_actual in ids:

        return valor_actual

    if not campanas.empty and "activa" in campanas.columns:

        activas = campanas[pd.to_numeric(campanas["activa"], errors="coerce") == 1]

        if not activas.empty:

            return int(activas.iloc[0]["id"])

    return ids[0] if ids else None


def _selector_campana(campanas, key, valor_actual=None):

    if campanas.empty:

        st.warning(
            "No hay campañas disponibles. Crea una campaña antes de guardar "
            "cultivos v6."
        )
        return None

    ids = campanas["id"].dropna().astype(int).tolist()
    valor = _campana_por_defecto(campanas, valor_actual)
    indice = ids.index(valor) if valor in ids else 0

    return st.selectbox(
        "Campaña",
        ids,
        index=indice,
        format_func=lambda campana_id: (
            campanas.loc[
                campanas["id"].astype(int) == int(campana_id),
                "nombre",
            ].astype(str).iloc[0]
        ),
        key=key,
    )


def _sumar_superficie(parcelas, ids_parcelas):

    if parcelas.empty or not ids_parcelas:

        return 0.0

    seleccionadas = parcelas[
        parcelas["id"].astype(int).isin([int(valor) for valor in ids_parcelas])
    ].copy()
    superficies = pd.to_numeric(
        seleccionadas["superficie_sigpac"],
        errors="coerce",
    )
    return float(superficies.fillna(0).sum())


def _superficie_parcela(parcelas, parcela_id):

    if parcelas.empty:

        return None

    fila = parcelas[parcelas["id"].astype(int) == int(parcela_id)]

    if fila.empty:

        return None

    numero = pd.to_numeric(fila.iloc[0].get("superficie_sigpac"), errors="coerce")
    return None if pd.isna(numero) else float(numero)


def _buscar_catalogo_cultivos(texto=""):

    try:

        return buscar_items_catalogo(
            "cultivo",
            texto=texto,
            solo_activos=True,
        )

    except Exception:

        return pd.DataFrame()


def _selector_codigo_siex(key, valor_actual=""):

    valor_actual = _normalizar_texto(valor_actual)
    busqueda = st.text_input(
        "Buscar catálogo SIEX de cultivos",
        value="",
        placeholder="Ejemplo: ALMENDRO o 104",
        key=f"{key}_busqueda",
    )
    catalogo = _buscar_catalogo_cultivos(busqueda)

    if catalogo.empty:

        st.info(
            "No hay catálogo SIEX de cultivos importado o no hay resultados. "
            "Puede dejar el código vacío por ahora."
        )
        return st.text_input(
            "Código SIEX",
            value=valor_actual,
            key=f"{key}_manual",
        ).strip()

    opciones = [""]
    etiquetas = {"": "Sin código por ahora"}

    if valor_actual:

        opciones.append(valor_actual)
        etiquetas[valor_actual] = f"{valor_actual} - Código actual"

    for _, fila in catalogo.iterrows():

        codigo = _normalizar_texto(fila.get("codigo"))
        descripcion = _normalizar_texto(fila.get("descripcion"))

        if not codigo or codigo in etiquetas:

            continue

        opciones.append(codigo)
        etiquetas[codigo] = f"{codigo} - {descripcion}".strip(" -")

    indice = opciones.index(valor_actual) if valor_actual in opciones else 0

    return st.selectbox(
        "Código SIEX",
        opciones,
        index=indice,
        format_func=lambda codigo: etiquetas.get(codigo, codigo),
        key=f"{key}_selector",
    )


def _leer_parcelas_cultivo():

    conn = conectar()

    try:

        if not (
            _tabla_existe_conn(conn, "cultivo_parcelas")
            and _tabla_existe_conn(conn, "parcelas")
        ):

            return pd.DataFrame()

        columnas_parcelas = _columnas_tabla_conn(conn, "parcelas")
        expr_municipio = (
            _expr_texto("parcelas", "municipio", columnas_parcelas)
            if "municipio" in columnas_parcelas
            else _expr_valor(
                "parcelas",
                "municipio_sigpac",
                columnas_parcelas,
                "''"
            )
        )

        return pd.read_sql_query(
            f"""
            SELECT
                cultivo_parcelas.cultivo_id,
                parcelas.id AS parcela_id,
                {_expr_texto("parcelas", "nombre", columnas_parcelas)}
                    AS nombre,
                {expr_municipio} AS municipio,
                {_expr_texto("parcelas", "poligono", columnas_parcelas)}
                    AS poligono,
                {_expr_texto("parcelas", "parcela", columnas_parcelas)}
                    AS parcela,
                {_expr_texto("parcelas", "recinto", columnas_parcelas)}
                    AS recinto,
                {_expr_valor(
                    "parcelas",
                    "superficie_sigpac",
                    columnas_parcelas,
                    "0"
                )} AS superficie_sigpac
            FROM cultivo_parcelas
            JOIN parcelas ON parcelas.id = cultivo_parcelas.parcela_id
            ORDER BY cultivo_parcelas.cultivo_id,
            municipio,parcelas.poligono,parcelas.parcela,
            parcelas.recinto,parcelas.id
            """,
            conn,
        )

    except Exception:

        return pd.DataFrame()

    finally:

        conn.close()


def _leer_parcelas_legacy():

    conn = conectar()

    try:

        columnas_cultivos = _columnas_tabla_conn(conn, "cultivos")

        if (
            "parcela_id" not in columnas_cultivos
            or not _tabla_existe_conn(conn, "parcelas")
        ):

            return pd.DataFrame()

        columnas_parcelas = _columnas_tabla_conn(conn, "parcelas")
        expr_municipio = (
            _expr_texto("parcelas", "municipio", columnas_parcelas)
            if "municipio" in columnas_parcelas
            else _expr_valor(
                "parcelas",
                "municipio_sigpac",
                columnas_parcelas,
                "''"
            )
        )

        return pd.read_sql_query(
            f"""
            SELECT
                cultivos.id AS cultivo_id,
                parcelas.id AS parcela_id,
                {_expr_texto("parcelas", "nombre", columnas_parcelas)}
                    AS nombre,
                {expr_municipio} AS municipio,
                {_expr_texto("parcelas", "poligono", columnas_parcelas)}
                    AS poligono,
                {_expr_texto("parcelas", "parcela", columnas_parcelas)}
                    AS parcela,
                {_expr_texto("parcelas", "recinto", columnas_parcelas)}
                    AS recinto,
                {_expr_valor(
                    "parcelas",
                    "superficie_sigpac",
                    columnas_parcelas,
                    "0"
                )} AS superficie_sigpac
            FROM cultivos
            JOIN parcelas ON parcelas.id = cultivos.parcela_id
            ORDER BY cultivos.id
            """,
            conn,
        )

    except Exception:

        return pd.DataFrame()

    finally:

        conn.close()


def _agrupar_parcelas(dataframe):

    agrupadas = {}

    if dataframe.empty:

        return agrupadas

    for _, fila in dataframe.iterrows():

        cultivo_id = _entero_o_none(fila.get("cultivo_id"))
        parcela_id = _entero_o_none(fila.get("parcela_id"))

        if cultivo_id is None or parcela_id is None:

            continue

        agrupadas.setdefault(cultivo_id, []).append({
            "id": parcela_id,
            "texto": _texto_parcela({
                "id": parcela_id,
                "nombre": fila.get("nombre"),
                "poligono": fila.get("poligono"),
                "parcela": fila.get("parcela"),
                "recinto": fila.get("recinto"),
                "superficie_sigpac": fila.get("superficie_sigpac"),
            }),
        })

    return agrupadas


def _leer_cultivos_guardados():

    columnas = _columnas_tabla("cultivos")

    if not columnas:

        return pd.DataFrame()

    expr_nombre = (
        _expr_texto("cultivos", "nombre", columnas)
        if "nombre" in columnas
        else _expr_texto("cultivos", "especie", columnas)
    )
    expr_campana_id = _expr_valor("cultivos", "campana_id", columnas)
    expr_parcela_id = _expr_valor("cultivos", "parcela_id", columnas)
    expr_marco_plantacion = (
        _expr_texto("cultivos", "marco_plantacion", columnas)
        if "marco_plantacion" in columnas
        else _expr_texto("cultivos", "marco", columnas)
    )
    expr_numero_arboles = (
        _expr_valor("cultivos", "numero_arboles", columnas, "0")
        if "numero_arboles" in columnas
        else _expr_valor("cultivos", "arboles", columnas, "0")
    )
    expr_activo = (
        "COALESCE(cultivos.activo,1)"
        if "activo" in columnas
        else "1"
    )

    cultivos = leer(
        f"""
        SELECT
            cultivos.id,
            {expr_campana_id} AS campana_id,
            COALESCE(campanas.nombre,'') AS campana,
            {expr_parcela_id} AS parcela_id,
            {expr_nombre} AS cultivo,
            {_expr_texto("cultivos", "variedad", columnas)} AS variedad,
            {_expr_texto("cultivos", "codigo_siex", columnas)}
                AS codigo_siex,
            {_expr_valor("cultivos", "superficie", columnas, "0")}
                AS superficie,
            {_expr_valor("cultivos", "ano_plantacion", columnas)}
                AS ano_plantacion,
            {expr_marco_plantacion} AS marco_plantacion,
            {expr_numero_arboles} AS numero_arboles,
            {_expr_texto("cultivos", "sistema", columnas)} AS sistema,
            {_expr_texto("cultivos", "observaciones", columnas)}
                AS observaciones,
            {expr_activo} AS activo
        FROM cultivos
        LEFT JOIN campanas ON campanas.id = cultivos.campana_id
        ORDER BY campanas.fecha_inicio DESC,cultivos.id
        """
    )

    if cultivos.empty:

        cultivos["parcelas_ids"] = ""
        cultivos["parcelas_asociadas"] = ""
        cultivos["activo_texto"] = ""
        return cultivos

    parcelas_v6 = _agrupar_parcelas(_leer_parcelas_cultivo())
    parcelas_legacy = _agrupar_parcelas(_leer_parcelas_legacy())
    parcelas_textos = []
    parcelas_ids = []

    for _, cultivo in cultivos.iterrows():

        cultivo_id = int(cultivo["id"])
        parcelas = parcelas_v6.get(cultivo_id) or parcelas_legacy.get(cultivo_id, [])
        ids = [item["id"] for item in parcelas]
        textos = [item["texto"] for item in parcelas]
        parcelas_ids.append(",".join(str(valor) for valor in ids))
        parcelas_textos.append(", ".join(textos))

    cultivos["parcelas_ids"] = parcelas_ids
    cultivos["parcelas_asociadas"] = parcelas_textos
    cultivos["campana"] = cultivos["campana"].replace("", "Sin campaña")
    cultivos["activo"] = (
        pd.to_numeric(cultivos["activo"], errors="coerce")
        .fillna(1)
        .astype(int)
    )
    cultivos["activo_texto"] = (
        cultivos["activo"].map({1: "Sí", 0: "No"}).fillna("Sí")
    )
    return cultivos


def _insertar_cultivo_parcelas(conn, cultivo_id, ids_parcelas, parcelas):

    if not _tabla_existe_conn(conn, "cultivo_parcelas"):

        return

    columnas = _columnas_tabla_conn(conn, "cultivo_parcelas")

    if not {"cultivo_id", "parcela_id"}.issubset(columnas):

        return

    ahora = datetime.now().isoformat(timespec="seconds")

    for parcela_id in ids_parcelas:

        valores = {
            "cultivo_id": int(cultivo_id),
            "parcela_id": int(parcela_id),
        }
        _anadir_si_existe(
            valores,
            columnas,
            "superficie",
            _superficie_parcela(parcelas, parcela_id)
        )
        _anadir_si_existe(valores, columnas, "created_at", ahora)
        _anadir_si_existe(valores, columnas, "updated_at", ahora)
        _ejecutar_insert_dinamico(
            conn,
            "cultivo_parcelas",
            valores
        )


def _guardar_cultivo(
    *,
    cultivo_id=None,
    campana_id,
    cultivo,
    variedad,
    codigo_siex,
    superficie,
    ano_plantacion,
    marco_plantacion,
    numero_arboles,
    sistema,
    observaciones,
    activo,
    ids_parcelas,
    parcelas,
):

    conn = conectar()

    try:

        conn.execute("BEGIN")
        columnas = _columnas_tabla_conn(conn, "cultivos")
        parcela_legacy = int(ids_parcelas[0]) if ids_parcelas else None
        ahora = datetime.now().isoformat(timespec="seconds")
        valores = {}

        _anadir_si_existe(valores, columnas, "campana_id", campana_id)
        _anadir_si_existe(valores, columnas, "parcela_id", parcela_legacy)
        _anadir_si_existe(valores, columnas, "nombre", cultivo)
        _anadir_si_existe(valores, columnas, "especie", cultivo)
        _anadir_si_existe(valores, columnas, "variedad", variedad)
        _anadir_si_existe(valores, columnas, "codigo_siex", codigo_siex)
        _anadir_si_existe(valores, columnas, "superficie", superficie)
        _anadir_si_existe(
            valores,
            columnas,
            "ano_plantacion",
            ano_plantacion
        )
        _anadir_si_existe(
            valores,
            columnas,
            "marco_plantacion",
            marco_plantacion,
        )
        _anadir_si_existe(
            valores,
            columnas,
            "numero_arboles",
            numero_arboles,
        )
        _anadir_si_existe(valores, columnas, "marco", marco_plantacion)
        _anadir_si_existe(valores, columnas, "arboles", numero_arboles)
        _anadir_si_existe(valores, columnas, "sistema", sistema)
        _anadir_si_existe(valores, columnas, "observaciones", observaciones)
        _anadir_si_existe(valores, columnas, "activo", int(bool(activo)))

        if cultivo_id is None:

            _anadir_si_existe(valores, columnas, "created_at", ahora)
            _anadir_si_existe(valores, columnas, "updated_at", ahora)
            cultivo_id = _ejecutar_insert_dinamico(
                conn,
                "cultivos",
                valores
            )

        else:

            _anadir_si_existe(valores, columnas, "updated_at", ahora)
            _ejecutar_update_dinamico(
                conn,
                "cultivos",
                int(cultivo_id),
                valores
            )

            if _tabla_existe_conn(conn, "cultivo_parcelas"):

                conn.execute(
                    "DELETE FROM cultivo_parcelas WHERE cultivo_id=?",
                    (int(cultivo_id),),
                )

        _insertar_cultivo_parcelas(conn, cultivo_id, ids_parcelas, parcelas)
        conn.commit()
        return int(cultivo_id)

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


def _validar_cultivo(campana_id, cultivo, ids_parcelas, ano_plantacion):

    errores = []

    if campana_id is None:

        errores.append("Selecciona una campaña.")

    if not _normalizar_texto(cultivo):

        errores.append("El cultivo no puede quedar vacío.")

    if not ids_parcelas:

        errores.append("Selecciona al menos una parcela.")

    if ano_plantacion is not None and (
        int(ano_plantacion) < 1900 or int(ano_plantacion) > date.today().year + 1
    ):

        errores.append("Año plantación fuera de rango.")

    return errores


def _render_nuevo_cultivo(campanas, parcelas):

    if "form_cultivo_version" not in st.session_state:

        st.session_state["form_cultivo_version"] = 0

    form_version = st.session_state["form_cultivo_version"]

    etiquetas_parcelas = {
        int(fila["id"]): _texto_parcela(fila)
        for _, fila in parcelas.iterrows()
    } if not parcelas.empty else {}

    campana_id = _selector_campana(
        campanas,
        f"cultivo_campana_{form_version}",
    )
    cultivo = st.text_input(
        "Cultivo",
        "Almendro",
        key=f"cultivo_nombre_{form_version}",
    )
    variedad = st.text_input(
        "Variedad",
        key=f"cultivo_variedad_{form_version}",
    )
    codigo_siex = _selector_codigo_siex(
        f"cultivo_codigo_siex_{form_version}",
    )
    parcelas_seleccionadas = st.multiselect(
        "Parcelas asociadas",
        list(etiquetas_parcelas.keys()),
        format_func=lambda parcela_id: etiquetas_parcelas.get(
            int(parcela_id),
            f"ID {parcela_id}",
        ),
        key=f"cultivo_parcelas_{form_version}",
    )
    superficie_sugerida = _sumar_superficie(parcelas, parcelas_seleccionadas)
    firma_parcelas = (
        "_".join(str(valor) for valor in sorted(parcelas_seleccionadas))
        or "sin_parcelas"
    )
    st.caption(
        "Superficie SIGPAC de parcelas seleccionadas: "
        f"{superficie_sugerida:.2f} ha"
    )
    superficie = st.number_input(
        "Superficie del cultivo (ha)",
        min_value=0.0,
        value=float(superficie_sugerida),
        step=0.01,
        format="%.4f",
        key=f"cultivo_superficie_{form_version}_{firma_parcelas}",
    )
    columnas = st.columns(4)

    with columnas[0]:

        ano_plantacion = st.number_input(
            "Año plantación",
            min_value=1900,
            max_value=date.today().year + 1,
            value=2020,
            step=1,
            key=f"cultivo_ano_{form_version}",
        )

    with columnas[1]:

        marco_plantacion = st.text_input(
            "Marco de plantación",
            "7x6",
            key=f"cultivo_marco_plantacion_{form_version}",
        )

    marco_parseado = parsear_marco_plantacion(marco_plantacion)
    numero_arboles_calculado = (
        calcular_numero_arboles(superficie, marco_plantacion)
        if marco_parseado is not None
        else None
    )

    if numero_arboles_calculado is not None:

        st.info(f"Árboles estimados: {numero_arboles_calculado}")

    elif _normalizar_texto(marco_plantacion) and marco_parseado is None:

        st.warning(
            "Marco de plantación no válido. Usa formatos como 7x7 o 6,5x5."
        )

    with columnas[2]:

        numero_arboles = st.number_input(
            "Nº árboles",
            min_value=0,
            value=numero_arboles_calculado or 0,
            step=1,
            key=(
                f"cultivo_numero_arboles_{form_version}_"
                f"{superficie:.4f}_{_normalizar_texto(marco_plantacion)}"
            ),
        )

    with columnas[3]:

        activo = st.checkbox(
            "Activo",
            value=True,
            key=f"cultivo_activo_{form_version}",
        )

    sistema = st.selectbox(
        "Sistema",
        [
            "Secano",
            "Regadío",
        ],
        key=f"cultivo_sistema_{form_version}",
    )
    observaciones = st.text_area(
        "Observaciones",
        key=f"cultivo_observaciones_{form_version}",
    )

    if st.button(
        "Guardar",
        key=f"cultivo_guardar_{form_version}",
        type="primary",
    ):

        cultivo_limpio = _normalizar_texto(cultivo)
        variedad_limpia = _normalizar_texto(variedad)
        sistema_limpio = _normalizar_texto(sistema)
        marco_limpio = _normalizar_texto(marco_plantacion)
        errores = _validar_cultivo(
            campana_id,
            cultivo_limpio,
            parcelas_seleccionadas,
            ano_plantacion,
        )

        if errores:

            st.warning(" ".join(errores))
            return

        try:

            cultivo_id = _guardar_cultivo(
                campana_id=int(campana_id),
                cultivo=cultivo_limpio,
                variedad=variedad_limpia,
                codigo_siex=_normalizar_texto(codigo_siex),
                superficie=float(superficie),
                ano_plantacion=int(ano_plantacion),
                marco_plantacion=marco_limpio,
                numero_arboles=int(numero_arboles),
                sistema=sistema_limpio,
                observaciones=_normalizar_texto(observaciones),
                activo=activo,
                ids_parcelas=[int(valor) for valor in parcelas_seleccionadas],
                parcelas=parcelas,
            )

        except Exception as error:

            st.error(f"No se ha guardado el cultivo. Error: {error}")
            return

        st.success(f"Cultivo #{cultivo_id} guardado.")
        st.session_state["form_cultivo_version"] += 1
        st.session_state["cultivos_version_visual"] += 1
        st.rerun()


def _render_listado(cultivos_guardados, version_visual):

    cultivos_filtrados = mostrar_filtros_dataframe(
        cultivos_guardados,
        f"cultivos_listado_v{version_visual}",
        columnas_texto=[
            "campana",
            "cultivo",
            "variedad",
            "codigo_siex",
            "marco_plantacion",
            "sistema",
            "parcelas_asociadas",
            "observaciones",
            "activo_texto",
        ],
        filtros_select={
            "Campaña": "campana",
            "Cultivo": "cultivo",
            "Variedad": "variedad",
            "Sistema": "sistema",
            "Activo": "activo_texto",
        },
    )
    columnas = [
        "id",
        "cultivo",
        "campana",
        "codigo_siex",
        "superficie",
        "marco_plantacion",
        "numero_arboles",
        "parcelas_asociadas",
        "observaciones",
    ]
    st.dataframe(
        preparar_dataframe_visual(
            cultivos_filtrados,
            columnas=columnas,
            ocultar_tecnicas=False,
            etiquetas_extra={
                "campana": "Campaña",
                "cultivo": "Cultivo",
                "parcelas_asociadas": "Parcelas asociadas",
                "marco_plantacion": "Marco de plantación",
                "numero_arboles": "Nº árboles",
                "activo_texto": "Activo",
            },
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Superficie": st.column_config.NumberColumn(
                "Superficie",
                format="%.4f ha",
            ),
            "Año plantación": st.column_config.NumberColumn(
                "Año plantación",
                min_value=1900,
                max_value=date.today().year + 1,
                step=1,
                format="%d",
            ),
            "Nº árboles": st.column_config.NumberColumn(
                "Nº árboles",
                min_value=0,
                step=1,
                format="%d",
            ),
            "activo_texto": "Activo",
        },
    )


def _render_editar(cultivos_guardados, campanas, parcelas):

    st.subheader("Edición segura")

    if cultivos_guardados.empty:

        st.info("No hay cultivos guardados para editar.")
        return

    ids_cultivos = cultivos_guardados["id"].astype(int).tolist()
    cultivo_id = st.selectbox(
        "Cultivo",
        ids_cultivos,
        format_func=lambda valor: _etiqueta_cultivo(
            cultivos_guardados[
                cultivos_guardados["id"].astype(int) == int(valor)
            ].iloc[0]
        ),
        key="cultivos_editar_id",
    )
    fila = cultivos_guardados[
        cultivos_guardados["id"].astype(int) == int(cultivo_id)
    ].iloc[0]
    ids_parcelas_actuales = _ids_desde_texto(fila.get("parcelas_ids"))
    etiquetas_parcelas = {
        int(parcela["id"]): _texto_parcela(parcela)
        for _, parcela in parcelas.iterrows()
    } if not parcelas.empty else {}
    campana_id = _selector_campana(
        campanas,
        f"cultivo_editar_campana_{cultivo_id}",
        fila.get("campana_id"),
    )
    cultivo = st.text_input(
        "Cultivo",
        value=_normalizar_texto(fila.get("cultivo")),
        key=f"cultivo_editar_nombre_{cultivo_id}",
    )
    variedad = st.text_input(
        "Variedad",
        value=_normalizar_texto(fila.get("variedad")),
        key=f"cultivo_editar_variedad_{cultivo_id}",
    )
    codigo_siex = _selector_codigo_siex(
        f"cultivo_editar_codigo_siex_{cultivo_id}",
        fila.get("codigo_siex"),
    )
    parcelas_seleccionadas = st.multiselect(
        "Parcelas asociadas",
        list(etiquetas_parcelas.keys()),
        default=[
            parcela_id
            for parcela_id in ids_parcelas_actuales
            if parcela_id in etiquetas_parcelas
        ],
        format_func=lambda parcela_id: etiquetas_parcelas.get(
            int(parcela_id),
            f"ID {parcela_id}",
        ),
        key=f"cultivo_editar_parcelas_{cultivo_id}",
    )
    superficie_sugerida = _sumar_superficie(parcelas, parcelas_seleccionadas)
    superficie_actual = pd.to_numeric(fila.get("superficie"), errors="coerce")
    superficie_valor = (
        float(superficie_actual)
        if not pd.isna(superficie_actual)
        else float(superficie_sugerida)
    )
    st.caption(
        "Superficie SIGPAC de parcelas seleccionadas: "
        f"{superficie_sugerida:.2f} ha"
    )
    firma_parcelas = (
        "_".join(str(valor) for valor in sorted(parcelas_seleccionadas))
        or "sin_parcelas"
    )
    superficie = st.number_input(
        "Superficie del cultivo (ha)",
        min_value=0.0,
        value=superficie_valor,
        step=0.01,
        format="%.4f",
        key=f"cultivo_editar_superficie_{cultivo_id}_{firma_parcelas}",
    )
    columnas = st.columns(4)

    with columnas[0]:

        ano_original = _entero_o_none(fila.get("ano_plantacion"))
        ano_plantacion = st.number_input(
            "Año plantación",
            min_value=1900,
            max_value=date.today().year + 1,
            value=ano_original or 2020,
            step=1,
            key=f"cultivo_editar_ano_{cultivo_id}",
        )

    with columnas[1]:

        marco_original = _normalizar_texto(fila.get("marco_plantacion"))
        marco_plantacion = st.text_input(
            "Marco de plantación",
            value=marco_original,
            key=f"cultivo_editar_marco_plantacion_{cultivo_id}",
        )

    marco_parseado = parsear_marco_plantacion(marco_plantacion)
    numero_arboles_calculado = (
        calcular_numero_arboles(superficie, marco_plantacion)
        if marco_parseado is not None
        else None
    )
    numero_arboles_original = max(
        0,
        _entero_o_none(fila.get("numero_arboles")) or 0,
    )
    superficie_cambiada = (
        pd.isna(superficie_actual)
        or abs(float(superficie) - float(superficie_actual)) > 0.000001
    )
    marco_cambiado = _normalizar_texto(marco_plantacion) != marco_original
    recalcular_por_cambio = superficie_cambiada or marco_cambiado
    numero_arboles_defecto = (
        numero_arboles_calculado
        if numero_arboles_calculado is not None
        and (recalcular_por_cambio or numero_arboles_original == 0)
        else numero_arboles_original
    )

    if numero_arboles_calculado is not None:

        mensaje = f"Árboles estimados con superficie y marco actuales: {numero_arboles_calculado}"

        if (
            numero_arboles_original
            and numero_arboles_calculado != numero_arboles_original
        ):

            mensaje += (
                f" · valor guardado actual: {numero_arboles_original}"
            )

        st.info(mensaje)

    elif _normalizar_texto(marco_plantacion) and marco_parseado is None:

        st.warning(
            "Marco de plantación no válido. Usa formatos como 7x7 o 6,5x5."
        )

    with columnas[2]:

        numero_arboles = st.number_input(
            "Nº árboles",
            min_value=0,
            value=numero_arboles_defecto,
            step=1,
            key=(
                f"cultivo_editar_numero_arboles_{cultivo_id}_"
                f"{superficie:.4f}_{_normalizar_texto(marco_plantacion)}"
            ),
        )

    with columnas[3]:

        activo = st.checkbox(
            "Activo",
            value=int(fila.get("activo", 1)) == 1,
            key=f"cultivo_editar_activo_{cultivo_id}",
        )

    sistema_actual = _normalizar_texto(fila.get("sistema")) or "Secano"
    opciones_sistema = ["Secano", "Regadío"]

    if sistema_actual not in opciones_sistema:

        opciones_sistema.insert(0, sistema_actual)

    sistema = st.selectbox(
        "Sistema",
        opciones_sistema,
        index=opciones_sistema.index(sistema_actual),
        key=f"cultivo_editar_sistema_{cultivo_id}",
    )
    observaciones = st.text_area(
        "Observaciones",
        value=_normalizar_texto(fila.get("observaciones")),
        key=f"cultivo_editar_observaciones_{cultivo_id}",
    )
    confirmar = st.checkbox(
        "Confirmo que quiero guardar los cambios del cultivo",
        key=f"cultivo_editar_confirmar_{cultivo_id}",
    )

    if st.button(
        "💾 Guardar cambios",
        key=f"cultivo_editar_guardar_{cultivo_id}",
        type="primary",
    ):

        cultivo_limpio = _normalizar_texto(cultivo)
        errores = _validar_cultivo(
            campana_id,
            cultivo_limpio,
            parcelas_seleccionadas,
            ano_plantacion,
        )

        if not confirmar:

            errores.append("Marca la confirmación antes de guardar.")

        if errores:

            st.warning(" ".join(errores))
            return

        try:

            _guardar_cultivo(
                cultivo_id=int(cultivo_id),
                campana_id=int(campana_id),
                cultivo=cultivo_limpio,
                variedad=_normalizar_texto(variedad),
                codigo_siex=_normalizar_texto(codigo_siex),
                superficie=float(superficie),
                ano_plantacion=int(ano_plantacion),
                marco_plantacion=_normalizar_texto(marco_plantacion),
                numero_arboles=int(numero_arboles),
                sistema=_normalizar_texto(sistema),
                observaciones=_normalizar_texto(observaciones),
                activo=activo,
                ids_parcelas=[int(valor) for valor in parcelas_seleccionadas],
                parcelas=parcelas,
            )

        except Exception as error:

            st.error(f"No se han guardado los cambios. Error: {error}")
            return

        st.success("Cultivo actualizado.")
        st.session_state["cultivos_version_visual"] += 1
        st.rerun()


def _render_borrar(cultivos_guardados):

    st.subheader("Borrado seguro")

    borrar_registros_seguro(
        "cultivos",
        "id",
        cultivos_guardados,
        "cultivos",
        tablas_hijas=[
            ("cultivo_parcelas", "cultivo_id"),
        ],
        bloqueos=[
            (
                "tratamientos",
                "cultivo_id",
                "el cultivo está usado en tratamientos",
            ),
            (
                "fertilizaciones",
                "cultivo_id",
                "el cultivo está usado en fertilización",
            ),
            (
                "practicas_culturales",
                "cultivo_id",
                "el cultivo está usado en prácticas culturales",
            ),
            (
                "cosecha",
                "cultivo_id",
                "el cultivo está usado en cosecha",
            ),
            (
                "analisis_fitosanitarios",
                "cultivo_id",
                "el cultivo está usado en análisis fitosanitarios",
            ),
        ],
        campo_descripcion="cultivo",
        advertencia=(
            "Los cultivos sin referencias directas pueden eliminarse. "
            "Se borrarán antes sus relaciones en cultivo_parcelas."
        ),
        key="cultivos",
    )


def render():

    st.title("🌳 Cultivos")

    resultado_borrado_cultivos = st.session_state.get(
        "resultado_borrado_cultivos"
    )

    if "cultivos_version_visual" not in st.session_state:

        st.session_state["cultivos_version_visual"] = 0

    if (
        resultado_borrado_cultivos
        and st.session_state.get("cultivos_ultimo_borrado_procesado")
        != resultado_borrado_cultivos
    ):

        st.session_state["cultivos_version_visual"] += 1
        st.session_state["cultivos_ultimo_borrado_procesado"] = (
            resultado_borrado_cultivos
        )

    version_visual = st.session_state["cultivos_version_visual"]
    opciones_cultivos = [
        "📋 Listado",
        "➕ Nuevo cultivo",
        "✏️ Editar",
        "🗑️ Borrar",
    ]
    seccion_cultivos = st.radio(
        "Opciones de cultivos",
        opciones_cultivos,
        horizontal=True,
        key="cultivos_seccion",
    )
    campanas = _leer_campanas()
    parcelas = _leer_parcelas()
    cultivos_guardados = _leer_cultivos_guardados()

    if seccion_cultivos == "➕ Nuevo cultivo":

        _render_nuevo_cultivo(campanas, parcelas)

    if seccion_cultivos == "📋 Listado":

        _render_listado(cultivos_guardados, version_visual)

    if seccion_cultivos == "✏️ Editar":

        _render_editar(cultivos_guardados, campanas, parcelas)

    if seccion_cultivos == "🗑️ Borrar":

        _render_borrar(cultivos_guardados)
