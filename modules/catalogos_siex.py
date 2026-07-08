import json

import pandas as pd
import streamlit as st

from core.ui_tablas import preparar_dataframe_visual
from services.siex_catalogos import (
    buscar_items_catalogo,
    listar_catalogos,
)
from services.catalogos_siex_importer import (
    diagnosticar_catalogos_siex,
    importar_catalogos_siex_desde_zip,
    resumen_catalogos_siex,
)


def _mostrar_json_item(items):

    if items.empty or "datos_json" not in items.columns:

        return

    opciones = items["id"].astype(int).tolist()

    if not opciones:

        return

    item_id = st.selectbox(
        "Detalle de fila original",
        opciones,
        format_func=lambda valor: (
            items.loc[items["id"].astype(int) == int(valor), "descripcion"]
            .fillna("")
            .astype(str)
            .iloc[0]
            or f"Item {valor}"
        ),
        key="catalogos_siex_detalle_item",
    )
    fila = items[items["id"].astype(int) == int(item_id)].iloc[0]
    datos_json = fila.get("datos_json", "")

    if not datos_json:

        st.info("Este item no tiene datos_json.")
        return

    try:

        st.json(json.loads(datos_json))

    except json.JSONDecodeError:

        st.code(datos_json)


def _mostrar_estado_actual(resumen):

    columnas = st.columns(4)
    columnas[0].metric("Catálogos", resumen["total_catalogos"])
    columnas[1].metric("Elementos", resumen["total_items"])
    columnas[2].metric("Activos", resumen["items_activos"])
    columnas[3].metric(
        "Última importación",
        resumen["ultima_importacion"] or "Sin importar",
    )

    if resumen["total_catalogos"] == 0:

        st.warning(
            "No hay catálogos SIEX cargados. Puedes importarlos desde esta "
            "pantalla usando el ZIP oficial."
        )
        return

    principales = resumen.get("catalogos_principales") or []

    if principales:

        st.caption(
            "Catálogos principales: "
            + ", ".join(
                f"{item['nombre_catalogo']} ({item['total_items']})"
                for item in principales[:5]
            )
        )


def _mostrar_resultado_importacion():

    resumen = st.session_state.get("catalogos_siex_ultimo_resumen")

    if not resumen:

        return

    if resumen.get("errores"):

        st.error("La importación terminó con errores en algunos archivos.")

    else:

        st.success("Importación de catálogos SIEX completada.")

    st.write(
        f"{resumen.get('total_catalogos', 0)} catálogos, "
        f"{resumen.get('total_items', 0)} elementos, "
        f"{len(resumen.get('ignorados', []))} archivos ignorados, "
        f"{resumen.get('duracion_segundos', 0)} s."
    )

    if resumen.get("catalogos"):

        st.dataframe(
            preparar_dataframe_visual(
                pd.DataFrame(resumen["catalogos"]),
                columnas=[
                    "codigo_catalogo",
                    "nombre_catalogo",
                    "archivo_origen",
                    "items",
                ],
                ocultar_tecnicas=True,
            ),
            hide_index=True,
            use_container_width=True,
        )

    if resumen.get("errores"):

        with st.expander("Errores de importación", expanded=True):

            for error in resumen["errores"]:

                st.error(f"{error['archivo']}: {error['error']}")

    if resumen.get("ignorados"):

        with st.expander("Archivos ignorados"):

            for ignorado in resumen["ignorados"]:

                st.caption(f"{ignorado['archivo']}: {ignorado['motivo']}")


def _render_importacion():

    st.subheader("Importar catálogos")
    archivo = st.file_uploader(
        "ZIP oficial de catálogos SIEX",
        type=["zip"],
        key="catalogos_siex_zip",
    )

    if st.button(
        "Importar catálogos SIEX",
        type="primary",
        disabled=archivo is None,
        key="catalogos_siex_importar",
    ):

        try:

            with st.spinner("Importando catálogos SIEX..."):

                resultado = importar_catalogos_siex_desde_zip(
                    archivo.getvalue(),
                    nombre_archivo=archivo.name,
                )

            st.session_state["catalogos_siex_ultimo_resumen"] = resultado
            st.rerun()

        except Exception as exc:

            st.error(f"No se pudo importar el ZIP: {exc}")

    st.caption(
        "El ZIP se procesa y no se guarda como archivo. Los catálogos quedan "
        "persistidos en la base de datos configurada."
    )
    _mostrar_resultado_importacion()


def _render_diagnostico():

    st.subheader("Diagnóstico")
    diagnostico = diagnosticar_catalogos_siex()
    estado = diagnostico["estado"]

    if estado == "OK":

        st.success("Catálogos SIEX: OK.")

    elif estado == "ADVERTENCIAS":

        st.warning("Catálogos SIEX cargados con advertencias.")

    else:

        st.error("Catálogos SIEX incompletos.")

    for error in diagnostico["errores"]:

        st.error(error)

    for aviso in diagnostico["advertencias"]:

        st.warning(aviso)


def render():

    st.title("Catálogos SIEX")
    st.info(
        "Importa y consulta catálogos SIEX/CUE oficiales. CuadernoPro no se "
        "conecta directamente con SIEX/CUE ni envía datos oficiales."
    )

    resumen = resumen_catalogos_siex()
    _mostrar_estado_actual(resumen)
    _render_importacion()
    _render_diagnostico()

    catalogos = listar_catalogos()

    if catalogos.empty:

        return

    st.subheader("Catálogos importados")
    st.dataframe(
        preparar_dataframe_visual(
            catalogos.drop(columns=["observaciones"], errors="ignore"),
            ocultar_tecnicas=True,
        ),
        hide_index=True,
        use_container_width=True,
    )

    opciones = catalogos["codigo_catalogo"].astype(str).tolist()
    codigo_catalogo = st.selectbox(
        "Catálogo",
        opciones,
        format_func=lambda valor: (
            catalogos.loc[
                catalogos["codigo_catalogo"] == valor,
                "nombre_catalogo",
            ].iloc[0]
        ),
        key="catalogos_siex_codigo",
    )
    columnas = st.columns([3, 1])

    with columnas[0]:

        texto = st.text_input(
            "Buscar",
            value="",
            placeholder="Código o descripción",
            key="catalogos_siex_busqueda",
        )

    with columnas[1]:

        solo_activos = st.checkbox(
            "Solo activos",
            value=True,
            key="catalogos_siex_solo_activos",
        )

    items = buscar_items_catalogo(
        codigo_catalogo,
        texto=texto,
        solo_activos=solo_activos,
    )

    st.subheader("Items")

    if items.empty:

        st.info("No hay items para los filtros seleccionados.")
        return

    columnas_visibles = [
        "codigo",
        "codigo_secundario",
        "descripcion",
        "descripcion_secundaria",
        "fecha_alta",
        "fecha_baja",
        "activo",
    ]
    st.dataframe(
        preparar_dataframe_visual(
            items,
            columnas=columnas_visibles,
            ocultar_tecnicas=True,
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.caption(
        "La consulta muestra un máximo de 1000 items. La fila original se "
        "conserva completa en datos_json."
    )
    _mostrar_json_item(items)
