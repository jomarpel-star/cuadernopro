import sqlite3

import pandas as pd
import streamlit as st

from core.db import conectar, leer
from core.ui_tablas import (
    preparar_column_config_visual,
    preparar_dataframe_visual,
)


CONFIGURACION_TERCEROS = {
    "clientes": {
        "titulo": "Clientes",
        "singular": "cliente",
        "campos": [
            ("nombre", "Nombre", True),
            ("nif", "NIF", False),
            ("telefono", "Teléfono", False),
            ("email", "Email", False),
            ("direccion", "Dirección", False),
            ("poblacion", "Población", False),
            ("provincia", "Provincia", False),
            ("codigo_postal", "Código postal", False),
            ("observaciones", "Observaciones", False),
        ],
    },
    "proveedores": {
        "titulo": "Proveedores",
        "singular": "proveedor",
        "campos": [
            ("nombre", "Nombre", True),
            ("nif", "NIF", False),
            ("telefono", "Teléfono", False),
            ("email", "Email", False),
            ("direccion", "Dirección", False),
            ("poblacion", "Población", False),
            ("provincia", "Provincia", False),
            ("codigo_postal", "Código postal", False),
            ("actividad", "Actividad", False),
            ("observaciones", "Observaciones", False),
        ],
    },
}


def _texto(valor):

    if valor is None or pd.isna(valor):

        return ""

    return str(valor).strip()


def _obtener_version(clave):

    if clave not in st.session_state:

        st.session_state[clave] = 0

    return st.session_state[clave]


def _mostrar_mensaje_tabla(tabla):

    mensaje = st.session_state.pop(f"mensaje_terceros_{tabla}", None)

    if mensaje:

        st.success(mensaje)


def _leer_terceros(tabla, solo_activos=True):

    configuracion = CONFIGURACION_TERCEROS[tabla]
    columnas = ["id"] + [
        campo
        for campo, _, _ in configuracion["campos"]
    ] + [
        "activo",
        "created_at",
        "updated_at",
    ]
    sql = (
        "SELECT "
        + ",".join(columnas)
        + f" FROM {tabla}"
    )
    params = ()

    if solo_activos:

        sql += " WHERE COALESCE(activo,1)=1"

    sql += " ORDER BY nombre,id"

    return leer(sql, params)


def _guardar_nuevo(tabla, valores):

    ahora = pd.Timestamp.now().isoformat()
    campos = list(valores.keys()) + ["activo", "created_at", "updated_at"]
    parametros = list(valores.values()) + [1, ahora, ahora]
    marcadores = ",".join(["?"] * len(campos))

    conn = conectar()

    try:

        conn.execute(
            f"INSERT INTO {tabla} ({','.join(campos)}) VALUES ({marcadores})",
            parametros
        )
        conn.commit()

    except sqlite3.Error:

        conn.rollback()
        raise

    finally:

        conn.close()


def _actualizar_terceros(tabla, dataframe, campos):

    ahora = pd.Timestamp.now().isoformat()
    asignaciones = ",".join([f"{campo}=?" for campo in campos])
    sql = (
        f"UPDATE {tabla} SET {asignaciones},updated_at=? WHERE id=?"
    )

    conn = conectar()

    try:

        for _, fila in dataframe.iterrows():

            valores = [_texto(fila[campo]) for campo in campos]
            conn.execute(
                sql,
                valores + [ahora, int(fila["id"])]
            )

        conn.commit()

    except sqlite3.Error:

        conn.rollback()
        raise

    finally:

        conn.close()


def _desactivar_tercero(tabla, registro_id):

    conn = conectar()

    try:

        conn.execute(
            f"UPDATE {tabla} SET activo=0,updated_at=? WHERE id=?",
            (pd.Timestamp.now().isoformat(), int(registro_id))
        )
        conn.commit()

    except sqlite3.Error:

        conn.rollback()
        raise

    finally:

        conn.close()


def _render_nuevo(tabla):

    configuracion = CONFIGURACION_TERCEROS[tabla]
    campos = configuracion["campos"]
    version = _obtener_version(f"form_nuevo_{tabla}_version")

    with st.expander(f"Nuevo {configuracion['singular']}", expanded=True):

        with st.form(f"form_nuevo_{tabla}_v{version}"):

            valores = {}

            for campo, etiqueta, _ in campos:

                if campo == "observaciones":

                    valores[campo] = st.text_area(
                        etiqueta,
                        key=f"nuevo_{tabla}_{campo}_{version}"
                    )

                else:

                    valores[campo] = st.text_input(
                        etiqueta,
                        key=f"nuevo_{tabla}_{campo}_{version}"
                    )

            guardar = st.form_submit_button(
                f"Guardar {configuracion['singular']}"
            )

        if guardar:

            valores = {
                campo: _texto(valor)
                for campo, valor in valores.items()
            }

            if not valores.get("nombre"):

                st.warning("El nombre es obligatorio")

            else:

                _guardar_nuevo(tabla, valores)
                st.session_state[f"mensaje_terceros_{tabla}"] = (
                    f"{configuracion['singular'].capitalize()} guardado"
                )
                st.session_state[f"form_nuevo_{tabla}_version"] += 1
                st.rerun()


def _render_listado_y_edicion(tabla, activos):

    configuracion = CONFIGURACION_TERCEROS[tabla]
    campos = [
        campo
        for campo, _, _ in configuracion["campos"]
    ]
    columnas_editor = ["id"] + campos

    st.subheader("Registros activos")

    if activos.empty:

        st.info(f"No hay {configuracion['titulo'].lower()} activos")
        return

    st.dataframe(
        preparar_dataframe_visual(
            activos[columnas_editor],
            mostrar_id=True,
        ),
        hide_index=True,
        use_container_width=True
    )

    with st.expander("Editar datos básicos"):

        editor_version = _obtener_version(f"editor_{tabla}_version")
        editables = activos[columnas_editor].copy()
        editados = st.data_editor(
            editables,
            num_rows="fixed",
            disabled=["id"],
            hide_index=True,
            use_container_width=True,
            column_config=preparar_column_config_visual(editables),
            key=f"editor_{tabla}_{editor_version}"
        )

        confirmar = st.checkbox(
            "Confirmo que quiero guardar los cambios",
            key=f"confirmar_edicion_{tabla}_{editor_version}"
        )

        if st.button(
            "Guardar cambios",
            key=f"guardar_edicion_{tabla}_{editor_version}"
        ):

            ids_originales = editables["id"].astype(int).tolist()
            ids_editados = editados["id"].astype(int).tolist()
            editados = editados.copy()

            for campo in campos:

                editados[campo] = (
                    editados[campo]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

            if not confirmar:

                st.warning("Marca la confirmación antes de guardar")

            elif ids_editados != ids_originales:

                st.warning("No se permite añadir, borrar ni cambiar IDs")

            elif (editados["nombre"] == "").any():

                st.warning("Todos los registros deben tener nombre")

            else:

                _actualizar_terceros(tabla, editados, campos)
                st.session_state[f"mensaje_terceros_{tabla}"] = (
                    "Cambios guardados"
                )
                st.session_state[f"editor_{tabla}_version"] += 1
                st.rerun()


def _render_desactivar(tabla, activos):

    configuracion = CONFIGURACION_TERCEROS[tabla]

    with st.expander(f"Desactivar {configuracion['singular']}"):

        if activos.empty:

            st.info(f"No hay {configuracion['titulo'].lower()} activos")
            return

        desactivar_version = _obtener_version(f"desactivar_{tabla}_version")
        activos_por_id = activos.set_index("id", drop=False)
        ids = activos_por_id.index.astype(int).tolist()
        registro_id = st.selectbox(
            f"{configuracion['singular'].capitalize()}",
            ids,
            format_func=lambda valor: activos_por_id.loc[valor]["nombre"],
            key=f"desactivar_{tabla}_id_{desactivar_version}"
        )
        confirmar = st.checkbox(
            "Confirmo que quiero desactivar este registro",
            key=f"confirmar_desactivar_{tabla}_{desactivar_version}"
        )

        if st.button(
            "Desactivar",
            key=f"boton_desactivar_{tabla}_{desactivar_version}"
        ):

            if not confirmar:

                st.warning("Marca la confirmación antes de desactivar")

            else:

                _desactivar_tercero(tabla, registro_id)
                st.session_state[f"mensaje_terceros_{tabla}"] = (
                    "Registro desactivado"
                )
                st.session_state[f"desactivar_{tabla}_version"] += 1
                st.rerun()


def _render_tabla(tabla):

    configuracion = CONFIGURACION_TERCEROS[tabla]
    st.subheader(configuracion["titulo"])
    _mostrar_mensaje_tabla(tabla)
    activos = _leer_terceros(tabla)

    _render_nuevo(tabla)
    _render_listado_y_edicion(tabla, activos)
    _render_desactivar(tabla, activos)


def render():

    st.title("Clientes / Proveedores")

    tab_clientes, tab_proveedores = st.tabs(["Clientes", "Proveedores"])

    with tab_clientes:

        _render_tabla("clientes")

    with tab_proveedores:

        _render_tabla("proveedores")
