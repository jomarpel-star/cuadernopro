from datetime import datetime
import json

import pandas as pd
import streamlit as st

from core.borrado import borrar_registros_seguro
from core.db import conectar
from core.filtros import mostrar_filtros_dataframe
from core.ui_tablas import (
    mapear_columnas_visuales_a_tecnicas,
    preparar_dataframe_visual,
)
from services.sigpac import consultar_recinto_sigpac
from services.sigpac_catalogo import (
    buscar_municipio_por_label,
    buscar_provincia_por_label,
    obtener_municipios,
    obtener_provincias,
)


def _formatear_hectareas(valor):

    return f"{float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _referencia_sigpac(
    provincia_sigpac,
    municipio_sigpac,
    agregado_sigpac,
    zona_sigpac,
    poligono,
    parcela,
    recinto
):

    return {
        "provincia_sigpac": int(provincia_sigpac),
        "municipio_sigpac": int(municipio_sigpac),
        "agregado_sigpac": int(agregado_sigpac),
        "zona_sigpac": int(zona_sigpac),
        "poligono": str(poligono).strip(),
        "parcela": str(parcela).strip(),
        "recinto": str(recinto).strip(),
    }


def _label_por_codigo(opciones, codigo_buscado):

    for opcion in opciones:

        if opcion["codigo"] == codigo_buscado:

            return opcion["label"]

    return None


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

    columnas = list(valores)

    if not columnas:

        return None

    cursor = conn.execute(
        f"""
        INSERT INTO {tabla}
        ({','.join(columnas)})
        VALUES ({','.join(['?'] * len(columnas))})
        """,
        [valores[columna] for columna in columnas]
    )
    return cursor.lastrowid


def _expr_nombre_cultivo(columnas_cultivos):

    if "nombre" in columnas_cultivos:

        return "COALESCE(cultivos.nombre,'')"

    if "especie" in columnas_cultivos:

        return "COALESCE(cultivos.especie,'')"

    return "''"


def _select_parcelas_base(columnas):

    expr_provincia = (
        _expr_texto("parcelas", "provincia", columnas)
        if "provincia" in columnas
        else _expr_valor("parcelas", "provincia_sigpac", columnas, "''")
    )
    expr_municipio = (
        _expr_texto("parcelas", "municipio", columnas)
        if "municipio" in columnas
        else _expr_valor("parcelas", "municipio_sigpac", columnas, "''")
    )

    return f"""
        parcelas.id,
        {_expr_texto("parcelas", "nombre", columnas)} AS nombre,
        {expr_provincia} AS provincia,
        {expr_municipio} AS municipio,
        {_expr_valor("parcelas", "provincia_sigpac", columnas)}
            AS provincia_sigpac,
        {_expr_valor("parcelas", "municipio_sigpac", columnas)}
            AS municipio_sigpac,
        {_expr_valor("parcelas", "agregado_sigpac", columnas, "0")}
            AS agregado_sigpac,
        {_expr_valor("parcelas", "zona_sigpac", columnas, "0")}
            AS zona_sigpac,
        {_expr_texto("parcelas", "poligono", columnas)} AS poligono,
        {_expr_texto("parcelas", "parcela", columnas)} AS parcela,
        {_expr_texto("parcelas", "recinto", columnas)} AS recinto,
        {_expr_valor("parcelas", "superficie_sigpac", columnas, "0")}
            AS superficie_sigpac,
        {_expr_valor("parcelas", "superficie_cultivada", columnas)}
            AS superficie_cultivada,
        {_expr_valor("parcelas", "geometry", columnas)} AS geometry,
        {_expr_texto("parcelas", "observaciones", columnas)}
            AS observaciones
    """


def _leer_parcelas_guardadas():

    conn = conectar()

    try:

        columnas = _columnas_tabla_conn(conn, "parcelas")
        consulta = f"""
            SELECT
            {_select_parcelas_base(columnas)}
            FROM parcelas
            ORDER BY parcelas.id
        """
        return pd.read_sql_query(consulta, conn)

    finally:

        conn.close()


def _subconsulta_cultivos_asociados(conn):

    if not _tabla_existe_conn(conn, "cultivos"):

        return None

    columnas_cultivos = _columnas_tabla_conn(conn, "cultivos")
    expr_nombre = _expr_nombre_cultivo(columnas_cultivos)
    expr_variedad = _expr_texto("cultivos", "variedad", columnas_cultivos)
    expr_sistema = _expr_texto("cultivos", "sistema", columnas_cultivos)
    expr_etiqueta = (
        "TRIM("
        f"{expr_nombre} || ' / ' || {expr_variedad} || ' / ' || "
        f"{expr_sistema}"
        ")"
    )

    if (
        _tabla_existe_conn(conn, "cultivo_parcelas")
        and {"cultivo_id", "parcela_id"}.issubset(
            _columnas_tabla_conn(conn, "cultivo_parcelas")
        )
    ):

        return f"""
            SELECT
                cultivo_parcelas.parcela_id,
                GROUP_CONCAT(DISTINCT {expr_etiqueta})
                    AS cultivo_asociado
            FROM cultivo_parcelas
            JOIN cultivos ON cultivos.id = cultivo_parcelas.cultivo_id
            GROUP BY cultivo_parcelas.parcela_id
        """

    if "parcela_id" in columnas_cultivos:

        return f"""
            SELECT
                cultivos.parcela_id,
                GROUP_CONCAT(DISTINCT {expr_etiqueta})
                    AS cultivo_asociado
            FROM cultivos
            GROUP BY cultivos.parcela_id
        """

    return None


def _leer_parcelas_consulta():

    conn = conectar()

    try:

        columnas = _columnas_tabla_conn(conn, "parcelas")
        subconsulta_cultivos = _subconsulta_cultivos_asociados(conn)
        joins = ""
        expr_cultivo = "'' AS cultivo_asociado"

        if subconsulta_cultivos:

            joins = (
                "LEFT JOIN ("
                f"{subconsulta_cultivos}"
                ") cultivos_asociados "
                "ON cultivos_asociados.parcela_id = parcelas.id"
            )
            expr_cultivo = (
                "COALESCE(cultivos_asociados.cultivo_asociado,'') "
                "AS cultivo_asociado"
            )

        consulta = f"""
            SELECT
            {_select_parcelas_base(columnas)},
            {_expr_valor(
                "parcelas",
                "sigpac_geojson_actualizado",
                columnas
            )} AS sigpac_geojson_actualizado,
            {_expr_texto(
                "parcelas",
                "sigpac_geojson_estado",
                columnas
            )} AS sigpac_geojson_estado,
            {_expr_texto(
                "parcelas",
                "sigpac_geojson_error",
                columnas
            )} AS sigpac_geojson_error,
            {expr_cultivo}
            FROM parcelas
            {joins}
            ORDER BY parcelas.id
        """
        return pd.read_sql_query(consulta, conn)

    finally:

        conn.close()


def _actualizar_parcela(conn, fila, invalidar_geojson):

    columnas = _columnas_tabla_conn(conn, "parcelas")
    valores = {}

    for columna in (
        "nombre",
        "provincia",
        "municipio",
        "provincia_sigpac",
        "municipio_sigpac",
        "agregado_sigpac",
        "zona_sigpac",
        "poligono",
        "parcela",
        "recinto",
        "superficie_sigpac",
    ):

        _anadir_si_existe(valores, columnas, columna, fila[columna])

    if invalidar_geojson:

        _anadir_si_existe(valores, columnas, "sigpac_geojson", None)
        _anadir_si_existe(valores, columnas, "sigpac_geojson_actualizado", None)
        _anadir_si_existe(
            valores,
            columnas,
            "sigpac_geojson_estado",
            "pendiente_actualizacion"
        )
        _anadir_si_existe(valores, columnas, "sigpac_geojson_error", None)

    _anadir_si_existe(
        valores,
        columnas,
        "updated_at",
        datetime.now().isoformat(timespec="seconds")
    )

    nombres = list(valores)

    if not nombres:

        return

    conn.execute(
        f"""
        UPDATE parcelas
        SET {','.join(f'{columna}=?' for columna in nombres)}
        WHERE id=?
        """,
        [valores[columna] for columna in nombres] + [int(fila["id"])]
    )


def _insertar_parcela(datos):

    conn = conectar()

    try:

        columnas = _columnas_tabla_conn(conn, "parcelas")
        ahora = datetime.now().isoformat(timespec="seconds")
        valores = {}

        for columna in (
            "nombre",
            "provincia",
            "municipio",
            "provincia_sigpac",
            "municipio_sigpac",
            "agregado_sigpac",
            "zona_sigpac",
            "poligono",
            "parcela",
            "recinto",
            "superficie_sigpac",
            "observaciones",
            "sigpac_geojson",
            "sigpac_geojson_actualizado",
            "sigpac_geojson_estado",
            "sigpac_geojson_error",
        ):

            _anadir_si_existe(valores, columnas, columna, datos.get(columna))

        _anadir_si_existe(valores, columnas, "activa", 1)
        _anadir_si_existe(valores, columnas, "created_at", ahora)
        _anadir_si_existe(valores, columnas, "updated_at", ahora)
        _ejecutar_insert_dinamico(conn, "parcelas", valores)
        conn.commit()

    finally:

        conn.close()


def render():

    st.title("📍 Parcelas SIGPAC")
    mensajes_parcelas = st.session_state.pop("mensajes_parcelas", [])

    for mensaje_parcela in mensajes_parcelas:

        st.success(mensaje_parcela)


    opciones_parcelas = [
        "📋 Listado",
        "➕ Nueva parcela",
        "✏️ Editar",
        "🗑️ Borrar",
    ]
    seccion_parcelas = st.radio(
        "Opciones de parcelas",
        opciones_parcelas,
        horizontal=True,
        key="parcelas_seccion"
    )

    parcelas_guardadas = _leer_parcelas_guardadas()

    if seccion_parcelas == "📋 Listado":

        parcelas_consulta = _leer_parcelas_consulta()

        parcelas_filtradas = mostrar_filtros_dataframe(
            parcelas_consulta,
            "parcelas",
            columnas_texto=[
                "nombre",
                "municipio",
                "poligono",
                "parcela",
                "recinto",
                "cultivo_asociado",
                "observaciones"
            ],
            filtros_select={
                "Municipio": "municipio",
                "Polígono": "poligono",
                "Parcela": "parcela",
                "Recinto": "recinto",
                "Cultivo asociado": "cultivo_asociado"
            }
        )
        columnas_listado_parcelas = [
            "nombre",
            "provincia",
            "municipio",
            "provincia_sigpac",
            "municipio_sigpac",
            "agregado_sigpac",
            "zona_sigpac",
            "poligono",
            "parcela",
            "recinto",
            "superficie_sigpac",
            "superficie_cultivada",
            "cultivo_asociado",
            "observaciones",
        ]
        st.dataframe(
            preparar_dataframe_visual(
                parcelas_filtradas,
                columnas=columnas_listado_parcelas,
                ocultar_tecnicas=True,
            ),
            hide_index=True,
            use_container_width=True
        )

    elif seccion_parcelas == "✏️ Editar":

        st.subheader("Edición segura")
        if "parcelas_editor_version" not in st.session_state:

            st.session_state["parcelas_editor_version"] = 0

        parcelas_editor_version = st.session_state["parcelas_editor_version"]

        columnas_editables_parcelas = [
            "nombre",
            "provincia",
            "municipio",
            "provincia_sigpac",
            "municipio_sigpac",
            "agregado_sigpac",
            "zona_sigpac",
            "poligono",
            "parcela",
            "recinto",
            "superficie_sigpac"
        ]

        columnas_texto_parcelas = [
            "nombre",
            "provincia",
            "municipio",
            "poligono",
            "parcela",
            "recinto"
        ]

        columnas_sigpac_invalidacion = [
            "provincia_sigpac",
            "municipio_sigpac",
            "agregado_sigpac",
            "zona_sigpac",
            "poligono",
            "parcela",
            "recinto"
        ]

        def _valores_distintos(valor_nuevo, valor_original):

            if pd.isna(valor_nuevo) and pd.isna(valor_original):

                return False

            return valor_nuevo != valor_original

        columnas_editor_parcelas = [
            "id",
            "nombre",
            "provincia",
            "municipio",
            "provincia_sigpac",
            "municipio_sigpac",
            "agregado_sigpac",
            "zona_sigpac",
            "poligono",
            "parcela",
            "recinto",
            "superficie_sigpac",
            "superficie_cultivada",
            "observaciones"
        ]
        parcelas_editor_visual = preparar_dataframe_visual(
            parcelas_guardadas,
            columnas=columnas_editor_parcelas,
            ocultar_tecnicas=False,
        )
        parcelas_editadas_visual = st.data_editor(
            parcelas_editor_visual,
            num_rows="fixed",
            disabled=[
                "ID",
                "Superficie cultivada",
                "Observaciones"
            ],
            use_container_width=True,
            column_order=[
                "ID",
                "Nombre",
                "Provincia",
                "Municipio",
                "Provincia SIGPAC",
                "Municipio SIGPAC",
                "Agregado SIGPAC",
                "Zona SIGPAC",
                "Polígono",
                "Parcela",
                "Recinto",
                "Superficie SIGPAC",
                "Superficie cultivada",
                "Observaciones"
            ],
            column_config={
                "Provincia SIGPAC": st.column_config.NumberColumn(
                    "Provincia SIGPAC",
                    min_value=1,
                    step=1,
                    format="%d"
                ),
                "Municipio SIGPAC": st.column_config.NumberColumn(
                    "Municipio SIGPAC",
                    min_value=1,
                    step=1,
                    format="%d"
                ),
                "Agregado SIGPAC": st.column_config.NumberColumn(
                    "Agregado SIGPAC",
                    min_value=0,
                    step=1,
                    format="%d"
                ),
                "Zona SIGPAC": st.column_config.NumberColumn(
                    "Zona SIGPAC",
                    min_value=0,
                    step=1,
                    format="%d"
                )
            },
            key=(
                "editor_parcelas_guardadas_v7_etiquetas_"
                f"{parcelas_editor_version}"
            )
        )
        parcelas_editadas = mapear_columnas_visuales_a_tecnicas(
            parcelas_editadas_visual
        )

        confirmar_cambios_parcelas = st.checkbox(
            "Confirmo que quiero guardar los cambios",
            key=f"confirmar_cambios_parcelas_{parcelas_editor_version}"
        )

        if st.button(
            "💾 Guardar cambios",
            key=f"guardar_cambios_parcelas_{parcelas_editor_version}"
        ):

            if parcelas_guardadas.empty:

                st.info(
                    "No hay parcelas guardadas para actualizar"
                )

            elif not confirmar_cambios_parcelas:

                st.warning(
                    "Marca la confirmación antes de guardar los cambios"
                )

            else:

                parcelas_para_guardar = parcelas_editadas.copy()

                for columna in columnas_texto_parcelas:

                    parcelas_para_guardar[columna] = (
                        parcelas_para_guardar[columna]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )

                parcelas_para_guardar["superficie_sigpac"] = (
                    pd.to_numeric(
                        parcelas_para_guardar["superficie_sigpac"],
                        errors="coerce"
                    )
                    .fillna(0.0)
                )

                for columna in [
                    "provincia_sigpac",
                    "municipio_sigpac"
                ]:

                    parcelas_para_guardar[columna] = pd.to_numeric(
                        parcelas_para_guardar[columna],
                        errors="coerce"
                    )

                for columna in ["agregado_sigpac", "zona_sigpac"]:

                    parcelas_para_guardar[columna] = (
                        pd.to_numeric(
                            parcelas_para_guardar[columna],
                            errors="coerce"
                        )
                        .fillna(0)
                    )

                clave_parcela = [
                    "provincia",
                    "municipio",
                    "poligono",
                    "parcela",
                    "recinto"
                ]

                parcelas_duplicadas = (
                    parcelas_para_guardar[clave_parcela]
                    .duplicated(keep=False)
                )

                if parcelas_duplicadas.any():

                    ids_duplicados = (
                        parcelas_para_guardar.loc[
                            parcelas_duplicadas,
                            "id"
                        ]
                        .astype(str)
                        .tolist()
                    )

                    st.warning(
                        "No se pueden guardar parcelas duplicadas. "
                        "Revisa id: "
                        f"{', '.join(ids_duplicados)}"
                    )

                else:

                    parcelas_originales = parcelas_guardadas.copy()

                    for columna in columnas_texto_parcelas:

                        parcelas_originales[columna] = (
                            parcelas_originales[columna]
                            .fillna("")
                            .astype(str)
                            .str.strip()
                        )

                    parcelas_originales["superficie_sigpac"] = (
                        pd.to_numeric(
                            parcelas_originales["superficie_sigpac"],
                            errors="coerce"
                        )
                        .fillna(0.0)
                    )

                    for columna in [
                        "provincia_sigpac",
                        "municipio_sigpac"
                    ]:

                        parcelas_originales[columna] = pd.to_numeric(
                            parcelas_originales[columna],
                            errors="coerce"
                        )

                    for columna in ["agregado_sigpac", "zona_sigpac"]:

                        parcelas_originales[columna] = (
                            pd.to_numeric(
                                parcelas_originales[columna],
                                errors="coerce"
                            )
                            .fillna(0)
                        )

                    filas_actualizadas = []
                    parcelas_sigpac_invalidadas = []

                    conn = conectar()
                    for _, fila in parcelas_para_guardar.iterrows():

                        parcela_id = int(fila["id"])
                        original = parcelas_originales[
                            parcelas_originales["id"] == parcela_id
                        ]

                        if original.empty:

                            continue

                        cambios = any(
                            _valores_distintos(
                                fila[columna],
                                original.iloc[0][columna]
                            )
                            for columna in columnas_editables_parcelas
                        )

                        if cambios:

                            referencia_sigpac_cambiada = any(
                                _valores_distintos(
                                    fila[columna],
                                    original.iloc[0][columna]
                                )
                                for columna in columnas_sigpac_invalidacion
                            )
                            invalidar_geojson = (
                                1 if referencia_sigpac_cambiada else 0
                            )

                            fila_guardar = fila.copy()
                            fila_guardar["provincia_sigpac"] = (
                                None
                                if pd.isna(fila_guardar["provincia_sigpac"])
                                else int(fila_guardar["provincia_sigpac"])
                            )
                            fila_guardar["municipio_sigpac"] = (
                                None
                                if pd.isna(fila_guardar["municipio_sigpac"])
                                else int(fila_guardar["municipio_sigpac"])
                            )
                            fila_guardar["agregado_sigpac"] = int(
                                fila_guardar["agregado_sigpac"]
                            )
                            fila_guardar["zona_sigpac"] = int(
                                fila_guardar["zona_sigpac"]
                            )
                            fila_guardar["superficie_sigpac"] = float(
                                fila_guardar["superficie_sigpac"]
                            )
                            _actualizar_parcela(
                                conn,
                                fila_guardar,
                                bool(invalidar_geojson)
                            )

                            filas_actualizadas.append(
                                parcela_id
                            )

                            if referencia_sigpac_cambiada:

                                parcelas_sigpac_invalidadas.append(
                                    parcela_id
                                )

                    conn.commit()
                    conn.close()

                    if filas_actualizadas:

                        mensajes_guardado = [
                            "Filas actualizadas: "
                            f"{len(filas_actualizadas)}"
                        ]

                        if parcelas_sigpac_invalidadas:

                            mensajes_guardado.append(
                                "La referencia SIGPAC ha cambiado en "
                                f"{len(parcelas_sigpac_invalidadas)} "
                                "parcela(s). La geometría se actualizará al "
                                "abrir Mapas/SIGPAC."
                            )

                        st.session_state["mensajes_parcelas"] = (
                            mensajes_guardado
                        )
                        st.session_state["parcelas_editor_version"] += 1
                        st.rerun()

                    else:

                        st.info(
                            "No había cambios para guardar"
                        )


    elif seccion_parcelas == "🗑️ Borrar":

        st.subheader("Borrado seguro")

        borrar_registros_seguro(
            "parcelas",
            "id",
            parcelas_guardadas,
            "parcelas",
            bloqueos=[
                (
                    "cultivo_parcelas",
                    "parcela_id",
                    "la parcela tiene cultivos"
                ),
                ("cultivos", "parcela_id", "la parcela tiene cultivos"),
                (
                    "tratamiento_parcelas",
                    "parcela_id",
                    "la parcela está usada en tratamientos"
                ),
                (
                    "fertilizacion_parcelas",
                    "parcela_id",
                    "la parcela está usada en fertilizaciones"
                ),
                (
                    "practica_parcelas",
                    "parcela_id",
                    "la parcela está usada en prácticas culturales"
                ),
                (
                    "practicas_culturales_parcelas",
                    "parcela_id",
                    "la parcela está usada en prácticas culturales"
                ),
                (
                    "cosecha_parcelas",
                    "parcela_id",
                    "la parcela está usada en cosechas"
                )
            ],
            campo_descripcion="nombre",
            key="parcelas"
        )

    elif seccion_parcelas == "➕ Nueva parcela":

        if "form_parcela_version" not in st.session_state:

            st.session_state["form_parcela_version"] = 0

        form_parcela_version = st.session_state["form_parcela_version"]
        provincia_key = f"parcela_provincia_label_{form_parcela_version}"
        municipio_key = f"parcela_municipio_label_{form_parcela_version}"
        superficie_key = f"parcela_superficie_sigpac_{form_parcela_version}"
        consulta_key = f"parcela_sigpac_consulta_{form_parcela_version}"
        superficie_pendiente_key = (
            f"parcela_superficie_sigpac_pendiente_{form_parcela_version}"
        )
        mensaje_consulta_key = (
            f"parcela_sigpac_mensaje_{form_parcela_version}"
        )

        provincias = obtener_provincias()
        etiquetas_provincias = [
            provincia["label"]
            for provincia in provincias
        ]

        if not etiquetas_provincias:

            st.error("No hay provincias SIGPAC configuradas.")
            st.stop()

        if st.session_state.get(provincia_key) not in etiquetas_provincias:

            st.session_state[provincia_key] = (
                _label_por_codigo(provincias, 30)
                or etiquetas_provincias[0]
            )

        if superficie_pendiente_key in st.session_state:

            superficie_pendiente = st.session_state.pop(
                superficie_pendiente_key
            )

            if superficie_pendiente is not None:

                st.session_state[superficie_key] = float(
                    superficie_pendiente
                )

        if superficie_key not in st.session_state:

            st.session_state[superficie_key] = 0.0

        nombre = st.text_input(
            "Nombre",
            key=f"parcela_nombre_{form_parcela_version}"
        )

        provincia_label = st.selectbox(
            "Provincia",
            etiquetas_provincias,
            key=provincia_key
        )
        provincia_opcion = buscar_provincia_por_label(provincia_label)
        provincia_sigpac = (
            provincia_opcion["codigo"]
            if provincia_opcion
            else None
        )
        provincia = (
            provincia_opcion["nombre"]
            if provincia_opcion
            else ""
        )

        municipios = obtener_municipios(provincia_sigpac)
        etiquetas_municipios = [
            municipio["label"]
            for municipio in municipios
        ]

        if (
            etiquetas_municipios
            and st.session_state.get(municipio_key)
            not in etiquetas_municipios
        ):

            st.session_state[municipio_key] = (
                _label_por_codigo(municipios, 22)
                if provincia_sigpac == 30
                else None
            ) or etiquetas_municipios[0]

        if not etiquetas_municipios:

            st.session_state[municipio_key] = (
                "Selecciona provincia y municipio"
            )

        municipio_label = st.selectbox(
            "Municipio",
            etiquetas_municipios or ["Selecciona provincia y municipio"],
            disabled=not etiquetas_municipios,
            key=municipio_key
        )
        municipio_opcion = buscar_municipio_por_label(
            provincia_sigpac,
            municipio_label
        )
        municipio_sigpac = (
            municipio_opcion["codigo"]
            if municipio_opcion
            else None
        )
        municipio = (
            municipio_opcion["nombre"]
            if municipio_opcion
            else ""
        )

        columna_agregado, columna_zona = st.columns(2)

        with columna_agregado:

            agregado_sigpac = st.number_input(
                "agregado_sigpac",
                min_value=0,
                step=1,
                value=0,
                format="%d",
                key=f"parcela_agregado_sigpac_{form_parcela_version}"
            )

        with columna_zona:

            zona_sigpac = st.number_input(
                "zona_sigpac",
                min_value=0,
                step=1,
                value=0,
                format="%d",
                key=f"parcela_zona_sigpac_{form_parcela_version}"
            )

        columna_poligono, columna_parcela, columna_recinto = st.columns(3)

        with columna_poligono:

            pol = st.text_input(
                "Polígono",
                key=f"parcela_poligono_{form_parcela_version}"
            )

        with columna_parcela:

            par = st.text_input(
                "Parcela",
                key=f"parcela_parcela_{form_parcela_version}"
            )

        with columna_recinto:

            rec = st.text_input(
                "Recinto",
                key=f"parcela_recinto_{form_parcela_version}"
            )

        referencia_actual = None

        if provincia_sigpac is not None and municipio_sigpac is not None:

            referencia_actual = _referencia_sigpac(
                provincia_sigpac,
                municipio_sigpac,
                agregado_sigpac,
                zona_sigpac,
                pol,
                par,
                rec
            )

        consulta_guardada = st.session_state.get(consulta_key) or {}

        if (
            consulta_guardada
            and consulta_guardada.get("referencia") != referencia_actual
        ):

            st.session_state.pop(consulta_key, None)

        sup = st.number_input(
            "Superficie SIGPAC ha",
            key=superficie_key
        )
        st.caption(
            "Puedes modificar la superficie antes de guardar si lo necesitas."
        )

        mensaje_consulta = st.session_state.pop(
            mensaje_consulta_key,
            None
        )

        if mensaje_consulta:

            st.success(mensaje_consulta["texto"])

            if mensaje_consulta.get("superficie_ha") is not None:

                st.info(
                    "Superficie SIGPAC: "
                    f"{_formatear_hectareas(mensaje_consulta['superficie_ha'])} ha"
                )
                st.success("Superficie SIGPAC rellenada automáticamente.")

            for aviso in mensaje_consulta.get("avisos", []):

                st.warning(aviso)

        consulta_sigpac = st.button(
            "Consultar SIGPAC y rellenar superficie",
            key=f"parcela_consultar_sigpac_{form_parcela_version}",
            use_container_width=True
        )

        if consulta_sigpac:

            faltan_datos_consulta = (
                provincia_opcion is None
                or municipio_opcion is None
                or provincia_sigpac is None
                or municipio_sigpac is None
                or agregado_sigpac is None
                or zona_sigpac is None
                or not all(str(valor).strip() for valor in [pol, par, rec])
            )

            if faltan_datos_consulta:

                st.warning(
                    "Introduce provincia, municipio, polígono, parcela y "
                    "recinto antes de consultar SIGPAC."
                )

            else:

                referencia_actual = _referencia_sigpac(
                    provincia_sigpac,
                    municipio_sigpac,
                    agregado_sigpac,
                    zona_sigpac,
                    pol,
                    par,
                    rec
                )

                try:

                    resultado = consultar_recinto_sigpac(
                        provincia_sigpac,
                        municipio_sigpac,
                        agregado_sigpac,
                        zona_sigpac,
                        str(pol).strip(),
                        str(par).strip(),
                        str(rec).strip()
                    )

                except Exception:

                    resultado = {
                        "ok": False,
                        "geojson": None,
                        "superficie_ha": None,
                        "error": (
                            "No se pudo consultar SIGPAC en este momento."
                        ),
                        "diagnostico": {}
                    }

                if resultado.get("ok"):

                    superficie_sigpac = resultado.get("superficie_ha")
                    diagnostico = resultado.get("diagnostico", {})
                    st.session_state[consulta_key] = {
                        "referencia": referencia_actual,
                        "geojson": resultado.get("geojson"),
                        "superficie_ha": superficie_sigpac
                    }
                    avisos = diagnostico.get("avisos", [])

                    if superficie_sigpac is not None:

                        st.session_state[mensaje_consulta_key] = {
                            "texto": "Recinto localizado en SIGPAC.",
                            "superficie_ha": superficie_sigpac,
                            "avisos": avisos
                        }
                        st.session_state[superficie_pendiente_key] = (
                            superficie_sigpac
                        )
                        st.rerun()

                    st.success("Recinto localizado en SIGPAC.")
                    st.warning(
                        "SIGPAC devolvió geometría, pero no se encontró "
                        "superficie en las propiedades."
                    )

                    for aviso in avisos:

                        if "superficie" not in aviso.casefold():

                            st.warning(aviso)

                else:

                    st.session_state.pop(consulta_key, None)
                    mensaje_error_sigpac = (
                        resultado.get("error")
                        or "SIGPAC no devolvió información para ese recinto."
                    )

                    if "No se pudo consultar" in mensaje_error_sigpac:

                        st.error(
                            "No se pudo consultar SIGPAC en este momento."
                        )

                    else:

                        st.warning(
                            "SIGPAC no devolvió información para ese recinto."
                        )

        obs = st.text_area(
            "Observaciones",
            key=f"parcela_observaciones_{form_parcela_version}"
        )

        if st.button(
            "Guardar",
            key=f"parcela_guardar_{form_parcela_version}",
            type="primary"
        ):

            errores = []

            if provincia_opcion is None or municipio_opcion is None:

                errores.append("Selecciona provincia y municipio.")

            if not str(pol).strip():

                errores.append("Polígono obligatorio")

            if not str(par).strip():

                errores.append("Parcela obligatoria")

            if not str(rec).strip():

                errores.append("Recinto obligatorio")

            if provincia_sigpac is None:

                errores.append("provincia_sigpac obligatoria")

            if municipio_sigpac is None:

                errores.append("municipio_sigpac obligatoria")

            if errores:

                st.warning(". ".join(errores))

            else:

                referencia_actual = _referencia_sigpac(
                    provincia_sigpac,
                    municipio_sigpac,
                    agregado_sigpac,
                    zona_sigpac,
                    pol,
                    par,
                    rec
                )
                consulta_guardada = st.session_state.get(consulta_key) or {}
                geojson_consultado = None

                if consulta_guardada.get("referencia") == referencia_actual:

                    geojson_consultado = consulta_guardada.get("geojson")

                if geojson_consultado:

                    sigpac_geojson = json.dumps(
                        geojson_consultado,
                        ensure_ascii=False
                    )
                    sigpac_geojson_actualizado = (
                        datetime.now().isoformat(timespec="seconds")
                    )
                    sigpac_geojson_estado = "ok"
                    sigpac_geojson_error = ""

                else:

                    sigpac_geojson = None
                    sigpac_geojson_actualizado = None
                    sigpac_geojson_estado = "pendiente_actualizacion"
                    sigpac_geojson_error = ""

                _insertar_parcela(
                    {
                        "nombre": nombre,
                        "provincia": provincia,
                        "municipio": municipio,
                        "provincia_sigpac": int(provincia_sigpac),
                        "municipio_sigpac": int(municipio_sigpac),
                        "agregado_sigpac": int(agregado_sigpac),
                        "zona_sigpac": int(zona_sigpac),
                        "poligono": str(pol).strip(),
                        "parcela": str(par).strip(),
                        "recinto": str(rec).strip(),
                        "superficie_sigpac": sup,
                        "observaciones": obs,
                        "sigpac_geojson": sigpac_geojson,
                        "sigpac_geojson_actualizado": (
                            sigpac_geojson_actualizado
                        ),
                        "sigpac_geojson_estado": sigpac_geojson_estado,
                        "sigpac_geojson_error": sigpac_geojson_error
                    }
                )

                if geojson_consultado:

                    st.success(
                        "Parcela guardada con datos SIGPAC consultados."
                    )

                else:

                    st.success(
                        "Parcela guardada. La geometría SIGPAC se "
                        "actualizará automáticamente al abrir Mapas/SIGPAC."
                    )

                for clave in [
                    consulta_key,
                    superficie_pendiente_key,
                    mensaje_consulta_key
                ]:

                    st.session_state.pop(clave, None)

                st.session_state["form_parcela_version"] += 1
                st.rerun()
