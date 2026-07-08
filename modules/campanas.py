import pandas as pd
import streamlit as st

from core.borrado import borrar_registros_seguro
from core.db import conectar, ejecutar, leer
from core.fechas import hoy
from core.ui_tablas import (
    mapear_columnas_visuales_a_tecnicas,
    preparar_dataframe_visual,
)


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
        columnas_campanas = [
            "id",
            "nombre",
            "fecha_inicio",
            "fecha_fin",
            "activa"
        ]
        campanas_editor_visual = preparar_dataframe_visual(
            campanas_editor,
            columnas=columnas_campanas,
            ocultar_tecnicas=False,
            etiquetas_extra={"nombre": "Campaña"}
        )

        st.dataframe(
            campanas_editor_visual.drop(columns=["ID"], errors="ignore"),
            use_container_width=True,
            hide_index=True
        )

        with st.expander("Editar campañas"):

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
                disabled=["ID"],
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

                if activas.sum() == 0:

                    errores.append("Debe haber una campaña activa")

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

                    conn.commit()
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

                ejecutar(
                    """
                    UPDATE campanas SET activa=0
                    """
                )

                ejecutar(
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
