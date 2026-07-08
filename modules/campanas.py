import pandas as pd
import streamlit as st

from core.borrado import borrar_registros_seguro
from core.campanas import (
    activar_campana,
    desactivar_campanas,
    obtener_campana_activa,
)
from core.db import conectar, leer
from core.fechas import formatear_fecha_es, hoy
from core.ui_tablas import (
    mapear_columnas_visuales_a_tecnicas,
    preparar_dataframe_visual,
)


def _texto_ui(valor):

    try:

        if valor is None or pd.isna(valor):

            return ""

    except (TypeError, ValueError):

        if valor is None:

            return ""

    return str(valor).strip()


def _etiqueta_campana(fila):

    if fila is None:

        return "Sin campaña"

    nombre = _texto_ui(fila.get("nombre")) or "Sin nombre"
    inicio = formatear_fecha_es(fila.get("fecha_inicio"))
    fin = formatear_fecha_es(fila.get("fecha_fin"))

    if inicio and fin:

        return f"{nombre} ({inicio} - {fin})"

    if inicio:

        return f"{nombre} ({inicio})"

    if fin:

        return f"{nombre} (hasta {fin})"

    return nombre


def _formatear_fechas_campanas_para_ui(campanas):

    if campanas is None or campanas.empty:

        return campanas

    resultado = campanas.copy()

    for columna in ["fecha_inicio", "fecha_fin"]:

        if columna in resultado.columns:

            resultado[columna] = resultado[columna].apply(formatear_fecha_es)

    return resultado


def _campanas_por_id(campanas):

    if campanas.empty:

        return {}

    return {
        int(fila["id"]): fila.to_dict()
        for _, fila in campanas.iterrows()
    }


def _limpiar_confirmaciones_campana():

    for clave in [
        "campana_activar_pendiente",
        "campana_desactivar_pendiente",
    ]:

        st.session_state.pop(clave, None)


def _render_campana_activa(campanas):

    st.subheader("Campaña activa")

    campanas_por_id = _campanas_por_id(campanas)
    conn = conectar()

    try:

        activa = obtener_campana_activa(conn)

    finally:

        conn.close()

    activa_id = int(activa["id"]) if activa else None

    if activa:

        st.info(f"Campaña activa actual: {_etiqueta_campana(activa)}")

    else:

        st.warning(
            "No hay campaña activa. Algunas altas nuevas pueden requerir "
            "seleccionar la campaña manualmente."
        )

    ids_campanas = list(campanas_por_id.keys())
    seleccion = st.selectbox(
        "Elegir campaña existente",
        ids_campanas,
        format_func=lambda valor: _etiqueta_campana(campanas_por_id.get(valor)),
        key="campana_activa_selector",
    )

    if seleccion == activa_id:

        st.caption("Esta campaña ya está activa.")

    if st.button(
        "Activar campaña seleccionada",
        disabled=seleccion == activa_id,
        key="campana_solicitar_activacion",
    ):

        st.session_state["campana_activar_pendiente"] = int(seleccion)
        st.session_state.pop("campana_desactivar_pendiente", None)

    pendiente = st.session_state.get("campana_activar_pendiente")

    if pendiente in campanas_por_id and pendiente != activa_id:

        destino = campanas_por_id[pendiente]
        origen = _etiqueta_campana(activa) if activa else "ninguna campaña activa"
        st.warning(
            "Vas a cambiar la campaña activa de "
            f"{origen} a {_etiqueta_campana(destino)}. ¿Estás seguro?"
        )
        confirmar = st.checkbox(
            "Confirmo que quiero cambiar la campaña activa.",
            key=f"confirmar_activar_campana_{pendiente}",
        )
        col_confirmar, col_cancelar = st.columns(2)

        with col_confirmar:

            if st.button(
                "Confirmar cambio de campaña activa",
                key=f"confirmar_cambio_campana_{pendiente}",
            ):

                if not confirmar:

                    st.warning("Marca la confirmación antes de cambiar la campaña.")

                else:

                    conn = conectar()

                    try:

                        activar_campana(conn, pendiente)

                    finally:

                        conn.close()

                    _limpiar_confirmaciones_campana()
                    st.session_state["mensaje_campanas"] = (
                        "Campaña activa actualizada"
                    )
                    st.rerun()

        with col_cancelar:

            if st.button(
                "Cancelar cambio",
                key=f"cancelar_cambio_campana_{pendiente}",
            ):

                st.session_state.pop("campana_activar_pendiente", None)
                st.rerun()

    if activa_id is not None:

        if st.button(
            "Desactivar campaña activa",
            key="campana_solicitar_desactivacion",
        ):

            st.session_state["campana_desactivar_pendiente"] = activa_id
            st.session_state.pop("campana_activar_pendiente", None)

        if st.session_state.get("campana_desactivar_pendiente") == activa_id:

            st.warning(
                "Vas a dejar la explotación sin campaña activa. Algunas altas "
                "nuevas pueden quedarse sin campaña activa automática o "
                "requerir selección manual."
            )
            confirmar = st.checkbox(
                "Confirmo que quiero desactivar la campaña activa.",
                key=f"confirmar_desactivar_campana_{activa_id}",
            )
            col_confirmar, col_cancelar = st.columns(2)

            with col_confirmar:

                if st.button(
                    "Confirmar desactivación",
                    key=f"confirmar_desactivacion_campana_{activa_id}",
                ):

                    if not confirmar:

                        st.warning(
                            "Marca la confirmación antes de desactivar la campaña."
                        )

                    else:

                        conn = conectar()

                        try:

                            desactivar_campanas(conn)

                        finally:

                            conn.close()

                        _limpiar_confirmaciones_campana()
                        st.session_state["mensaje_campanas"] = (
                            "Campaña activa desactivada"
                        )
                        st.rerun()

            with col_cancelar:

                if st.button(
                    "Cancelar desactivación",
                    key=f"cancelar_desactivacion_campana_{activa_id}",
                ):

                    st.session_state.pop("campana_desactivar_pendiente", None)
                    st.rerun()


def render():

    st.title("📅 Campañas agrícolas")
    mensaje_campanas = st.session_state.pop("mensaje_campanas", None)

    if mensaje_campanas:

        st.success(mensaje_campanas)

    campanas = leer(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin,activa
        FROM campanas
        ORDER BY id
        """
    )

    if campanas.empty:

        st.info("No hay campañas registradas")

    else:

        _render_campana_activa(campanas)

        columnas_campanas = [
            "id",
            "nombre",
            "fecha_inicio",
            "fecha_fin",
            "activa"
        ]
        campanas_resumen = _formatear_fechas_campanas_para_ui(campanas)
        campanas_resumen["activa"] = campanas_resumen["activa"].astype(bool)
        campanas_resumen_visual = preparar_dataframe_visual(
            campanas_resumen,
            columnas=columnas_campanas,
            ocultar_tecnicas=False,
            etiquetas_extra={"nombre": "Campaña"}
        )

        st.dataframe(
            campanas_resumen_visual.drop(columns=["ID"], errors="ignore"),
            use_container_width=True,
            hide_index=True
        )

        campanas_editor = campanas.copy()
        campanas_editor["activa"] = campanas_editor["activa"].astype(bool)
        campanas_editor["fecha_inicio"] = pd.to_datetime(
            campanas_editor["fecha_inicio"],
            errors="coerce"
        )
        campanas_editor["fecha_fin"] = pd.to_datetime(
            campanas_editor["fecha_fin"],
            errors="coerce"
        )
        campanas_editor_visual = preparar_dataframe_visual(
            campanas_editor,
            columnas=columnas_campanas,
            ocultar_tecnicas=False,
            etiquetas_extra={"nombre": "Campaña"}
        )

        with st.expander("Editar campañas"):

            st.caption(
                "Usa el bloque Campaña activa para activar o desactivar campañas."
            )

            if "campanas_editor_version" not in st.session_state:

                st.session_state["campanas_editor_version"] = 0

            campanas_editor_version = st.session_state[
                "campanas_editor_version"
            ]
            editadas_visual = st.data_editor(
                campanas_editor_visual,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                disabled=["ID", "Activa"],
                column_order=[
                    "ID",
                    "Campaña",
                    "Fecha inicio",
                    "Fecha fin",
                    "Activa"
                ],
                column_config={
                    "ID": st.column_config.NumberColumn(
                        "ID",
                        disabled=True
                    ),
                    "Campaña": st.column_config.TextColumn(
                        "Campaña",
                        required=True
                    ),
                    "Fecha inicio": st.column_config.DateColumn(
                        "Fecha inicio",
                        format="DD/MM/YYYY"
                    ),
                    "Fecha fin": st.column_config.DateColumn(
                        "Fecha fin",
                        format="DD/MM/YYYY"
                    ),
                    "Activa": st.column_config.CheckboxColumn(
                        "Activa"
                    )
                },
                key=f"campanas_editor_v7_etiquetas_v2_{campanas_editor_version}"
            )
            editadas = mapear_columnas_visuales_a_tecnicas(
                editadas_visual,
                etiquetas_extra={"nombre": "Campaña"}
            )

            confirmar_campanas = st.checkbox(
                "Confirmo que quiero guardar los cambios de campañas",
                key=f"campanas_confirmar_{campanas_editor_version}"
            )

            if st.button(
                "💾 Guardar cambios",
                key=f"campanas_guardar_{campanas_editor_version}"
            ):

                errores = []
                editadas = editadas.copy()
                editadas["nombre"] = editadas["nombre"].fillna("").astype(str).str.strip()

                if (editadas["nombre"] == "").any():

                    errores.append("El nombre no puede estar vacío")

                if editadas["nombre"].str.lower().duplicated().any():

                    errores.append("No puede haber dos campañas con el mismo nombre")

                activas = editadas["activa"].fillna(False).astype(bool)

                if activas.sum() > 1:

                    errores.append("Solo puede haber una campaña activa")

                for _, fila in editadas.iterrows():

                    fecha_inicio = fila["fecha_inicio"]
                    fecha_fin = fila["fecha_fin"]

                    if pd.isna(fecha_inicio):

                        errores.append(
                            f"La campaña '{fila['nombre']}' necesita fecha_inicio"
                        )

                        continue

                    if not pd.isna(fecha_fin) and fecha_fin < fecha_inicio:

                        errores.append(
                            f"La fecha_fin de '{fila['nombre']}' debe ser igual o posterior a fecha_inicio"
                        )

                if not confirmar_campanas:

                    errores.append("Marca la casilla de confirmación antes de guardar")

                if errores:

                    for error in errores:

                        st.error(error)

                else:

                    conn = conectar()

                    try:

                        with conn:

                            for _, fila in editadas.iterrows():

                                fecha_inicio = pd.to_datetime(
                                    fila["fecha_inicio"]
                                ).date().isoformat()
                                fecha_fin = None

                                if not pd.isna(fila["fecha_fin"]):

                                    fecha_fin = pd.to_datetime(
                                        fila["fecha_fin"]
                                    ).date().isoformat()

                                conn.execute(
                                    """
                                    UPDATE campanas
                                    SET nombre=?,
                                        fecha_inicio=?,
                                        fecha_fin=?,
                                        activa=?
                                    WHERE id=?
                                    """,
                                    (
                                        fila["nombre"],
                                        fecha_inicio,
                                        fecha_fin,
                                        int(bool(fila["activa"])),
                                        int(fila["id"])
                                    )
                                )

                    finally:

                        conn.close()

                    st.session_state["mensaje_campanas"] = (
                        "Cambios de campañas guardados"
                    )
                    st.session_state["campanas_editor_version"] += 1
                    st.rerun()


    if "form_campana_version" not in st.session_state:

        st.session_state["form_campana_version"] = 0

    form_campana_version = st.session_state["form_campana_version"]

    with st.form(f"camp_v{form_campana_version}"):

        nombre = st.text_input(
            "Nueva campaña",
            "2026/2027",
            key=f"campana_nombre_{form_campana_version}"
        )

        if st.form_submit_button("Crear"):

            existe = leer(
                "SELECT id FROM campanas WHERE nombre=?",
                (nombre,)
            )

            if not existe.empty:

                st.warning("Ya existe una campaña con ese nombre")

            else:

                conn = conectar()

                try:

                    with conn:

                        conn.execute("UPDATE campanas SET activa=0")
                        conn.execute(
                            """
                            INSERT INTO campanas
                            (nombre,fecha_inicio,activa)
                            VALUES (?,?,1)
                            """,
                            (
                                nombre,
                                hoy()
                            )
                        )

                finally:

                    conn.close()

                st.session_state["mensaje_campanas"] = "Campaña creada"
                st.session_state["form_campana_version"] += 1
                st.rerun()




    borrar_registros_seguro(
        "campanas",
        "id",
        campanas,
        "campañas",
        bloqueos=[
            (
                "tratamientos",
                "campana_id",
                "la campaña tiene tratamientos"
            ),
            (
                "fertilizaciones",
                "campana_id",
                "la campaña tiene fertilizaciones"
            ),
            (
                "practicas_culturales",
                "campana_id",
                "la campaña tiene prácticas culturales"
            ),
            (
                "cosecha",
                "campana_id",
                "la campaña tiene cosechas"
            ),
            (
                "movimientos_economicos",
                "campana_id",
                "la campaña tiene movimientos económicos"
            )
        ],
        campo_descripcion="nombre",
        key="campanas"
    )
