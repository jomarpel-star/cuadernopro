from pathlib import Path

import streamlit as st

from core.config import APP_NAME
from core.db import leer
from services.cuadernopro_pdf import generar_cuadernopro_pdf
from services.revision_cuaderno import revisar_cuaderno


def _importe(valor):

    return (
        f"{float(valor or 0):,.2f} €"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def _superficie(valor):

    return (
        f"{float(valor or 0):,.2f} ha"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def _mostrar_item_revision(item, funcion):

    detalle = item.get("detalle") or ""
    mensaje = item.get("mensaje") or ""
    seccion = item.get("seccion") or "Revisión"
    texto = f"**{seccion}:** {mensaje}"

    if detalle:

        texto += f"  \n{detalle}"

    funcion(texto)


def _mostrar_resumen_revision(resumen):

    if not resumen:

        return

    metricas = [
        ("Parcelas", resumen.get("parcelas", 0)),
        ("Cultivos", resumen.get("cultivos", 0)),
        ("Tratamientos", resumen.get("tratamientos", 0)),
        ("Fertilizaciones", resumen.get("fertilizaciones", 0)),
        ("Prácticas", resumen.get("practicas_culturales", 0)),
        ("Cosechas", resumen.get("cosechas", 0)),
        ("Análisis", resumen.get("analisis_fitosanitarios", 0)),
        ("Movimientos", resumen.get("movimientos_economicos", 0)),
    ]

    for inicio in range(0, len(metricas), 4):

        columnas = st.columns(4)

        for columna, (etiqueta, valor) in zip(columnas, metricas[inicio:inicio + 4]):

            columna.metric(etiqueta, valor)

    columnas = st.columns(3)
    columnas[0].metric(
        "Superficie SIGPAC",
        _superficie(resumen.get("superficie_sigpac_total", 0))
    )
    columnas[1].metric("Ingresos", _importe(resumen.get("ingresos", 0)))
    columnas[2].metric("Gastos", _importe(resumen.get("gastos", 0)))


def _mostrar_revision(revision):

    resumen = revision.get("resumen", {})
    errores = revision.get("errores", [])
    avisos = revision.get("avisos", [])
    correctos = revision.get("correctos", [])

    _mostrar_resumen_revision(resumen)

    st.markdown("#### ❌ Errores")

    if errores:

        for item in errores:

            _mostrar_item_revision(item, st.error)

        st.warning(
            "El PDF puede generarse, pero conviene revisar los errores antes "
            "de usarlo oficialmente."
        )

    else:

        st.success("No se han detectado errores importantes.")
        st.success("El cuaderno está listo para generar el PDF.")

    with st.expander(f"⚠️ Avisos ({len(avisos)})", expanded=bool(avisos)):

        if avisos:

            for item in avisos:

                _mostrar_item_revision(item, st.warning)

        else:

            st.info("No hay avisos relevantes.")

    with st.expander(
        f"✅ Correcto ({len(correctos)})",
        expanded=not avisos and not errores
    ):

        if correctos:

            for item in correctos:

                _mostrar_item_revision(item, st.success)

        else:

            st.info("No hay comprobaciones correctas que mostrar.")


def _render_panel_revision(campana_id):

    st.subheader("Revisión del cuaderno")
    st.write(
        "Comprueba datos básicos, avisos y posibles errores antes de generar "
        "el PDF."
    )
    clave_campana = campana_id if campana_id is not None else "sin_campana"
    clave_revision = f"revision_cuaderno_{clave_campana}"

    if st.button(
        "Comprobar cuaderno",
        key=f"comprobar_cuaderno_{clave_campana}"
    ):

        try:

            st.session_state[clave_revision] = revisar_cuaderno(campana_id)

        except Exception as exc:

            st.error(f"No se pudo revisar el cuaderno: {exc}")

    revision = st.session_state.get(clave_revision)

    if revision:

        _mostrar_revision(revision)


def render(CAMPANA):

    st.title("Cuaderno oficial")

    st.write(
        "Genera un cuaderno de explotación completo y legible en formato "
        f"{APP_NAME} PDF."
    )

    campanas = leer(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin,activa
        FROM campanas
        ORDER BY fecha_inicio DESC,id DESC
        """
    )

    if campanas.empty:

        st.warning("No hay campañas registradas")
        _render_panel_revision(None)
        return

    ids_campanas = campanas["id"].astype(int).tolist()
    indice_campana = (
        ids_campanas.index(int(CAMPANA))
        if int(CAMPANA) in ids_campanas
        else 0
    )
    campana_id = st.selectbox(
        "Campaña",
        ids_campanas,
        index=indice_campana,
        format_func=lambda valor: campanas.loc[
            campanas["id"] == valor,
            "nombre"
        ].iloc[0]
    )

    _render_panel_revision(campana_id)

    if st.button(f"Generar cuaderno {APP_NAME} PDF", type="primary"):

        try:

            ruta_cuadernopro_pdf = generar_cuadernopro_pdf(campana_id)

        except Exception as exc:

            st.error(f"No se pudo generar el cuaderno {APP_NAME} PDF: {exc}")

        else:

            ruta_cuadernopro = Path(ruta_cuadernopro_pdf)
            st.success(f"Cuaderno {APP_NAME} PDF generado")
            st.caption(
                "Archivo generado: "
                f"{ruta_cuadernopro}"
            )

            with ruta_cuadernopro.open("rb") as archivo:

                st.download_button(
                    f"Descargar cuaderno {APP_NAME} PDF",
                    archivo,
                    file_name=ruta_cuadernopro.name,
                    mime="application/pdf"
                )
