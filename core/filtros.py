import pandas as pd
import streamlit as st


def mostrar_filtros_dataframe(
    dataframe,
    key,
    columnas_texto=None,
    columna_fecha=None,
    columna_fecha_fin=None,
    filtros_select=None
):

    total_registros = len(dataframe)
    filtrado = dataframe.copy()
    columnas_texto = [
        columna
        for columna in (columnas_texto or [])
        if columna in filtrado.columns
    ]
    filtros_select = {
        etiqueta: columna
        for etiqueta, columna in (filtros_select or {}).items()
        if columna in filtrado.columns
    }

    with st.expander("🔎 Filtros"):

        texto = st.text_input(
            "Buscar texto",
            key=f"filtro_texto_{key}"
        ).strip()

        if texto and columnas_texto:

            coincidencias = pd.Series(False, index=filtrado.index)

            for columna in columnas_texto:

                coincidencias = coincidencias | (
                    filtrado[columna]
                    .fillna("")
                    .astype(str)
                    .str.contains(texto, case=False, na=False, regex=False)
                )

            filtrado = filtrado[coincidencias]

        for etiqueta, columna in filtros_select.items():

            valores = sorted(
                dataframe[columna]
                .dropna()
                .astype(str)
                .loc[lambda serie: serie.str.strip() != ""]
                .unique()
                .tolist()
            )
            seleccionados = st.multiselect(
                etiqueta,
                valores,
                key=f"filtro_{key}_{columna}"
            )

            if seleccionados:

                filtrado = filtrado[
                    filtrado[columna].fillna("").astype(str).isin(
                        seleccionados
                    )
                ]

        if columna_fecha and columna_fecha in dataframe.columns:

            activar_fechas = st.checkbox(
                "Filtrar por rango de fechas",
                key=f"filtro_fechas_{key}"
            )

            if activar_fechas:

                fechas_disponibles = pd.to_datetime(
                    dataframe[columna_fecha],
                    errors="coerce"
                )
                fechas_fin_disponibles = pd.to_datetime(
                    dataframe[columna_fecha_fin],
                    errors="coerce"
                ) if (
                    columna_fecha_fin
                    and columna_fecha_fin in dataframe.columns
                ) else fechas_disponibles
                fechas_validas = fechas_disponibles.dropna()
                fechas_fin_validas = fechas_fin_disponibles.dropna()

                if fechas_validas.empty:

                    st.info("No hay fechas válidas para filtrar")

                else:

                    fecha_minima = fechas_validas.min().date()
                    fecha_maxima = (
                        fechas_fin_validas.max().date()
                        if not fechas_fin_validas.empty
                        else fechas_validas.max().date()
                    )
                    columna_desde, columna_hasta = st.columns(2)

                    with columna_desde:

                        fecha_desde = st.date_input(
                            "Fecha desde",
                            value=fecha_minima,
                            format="DD/MM/YYYY",
                            key=f"filtro_desde_{key}"
                        )

                    with columna_hasta:

                        fecha_hasta = st.date_input(
                            "Fecha hasta",
                            value=fecha_maxima,
                            format="DD/MM/YYYY",
                            key=f"filtro_hasta_{key}"
                        )

                    if fecha_desde > fecha_hasta:

                        st.warning(
                            "La fecha desde no puede ser posterior a la "
                            "fecha hasta"
                        )
                        filtrado = filtrado.iloc[0:0]

                    else:

                        fechas_filtrado = pd.to_datetime(
                            filtrado[columna_fecha],
                            errors="coerce"
                        ).dt.date
                        if (
                            columna_fecha_fin
                            and columna_fecha_fin in filtrado.columns
                        ):

                            fechas_fin_filtrado = pd.to_datetime(
                                filtrado[columna_fecha_fin],
                                errors="coerce"
                            ).dt.date
                            filtrado = filtrado[
                                (fechas_filtrado <= fecha_hasta)
                                & (fechas_fin_filtrado >= fecha_desde)
                            ]

                        else:

                            filtrado = filtrado[
                                (fechas_filtrado >= fecha_desde)
                                & (fechas_filtrado <= fecha_hasta)
                            ]

    st.caption(
        f"Mostrando {len(filtrado)} de {total_registros} registros"
    )

    return filtrado.copy()


