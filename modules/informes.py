import io
from datetime import date

import pandas as pd
import streamlit as st
from openpyxl.styles import Font

from core.db import conectar, leer
from core.fechas import (
    formatear_columnas_fecha_es,
    formatear_fecha_es,
    preparar_columnas_fecha_tabla,
)
from core.ui_tablas import preparar_dataframe_visual
from modules.contabilidad import (
    _leer_movimientos_contabilidad,
    _resolver_tercero_movimiento,
)
from modules.cosecha import (
    _leer_cosechas_guardadas,
    _preparar_cosechas_presentacion,
)
from modules.fertilizacion import (
    _leer_fertilizaciones_guardadas,
    _preparar_fertilizaciones_presentacion,
)
from modules.practicas_culturales import (
    _leer_practicas_guardadas,
    _preparar_practicas_presentacion,
)
from modules.tratamientos import _leer_tratamientos_guardados


def _filtrar_campana_informes(dataframe, campana_id):

    if dataframe is None or dataframe.empty:

        return pd.DataFrame()

    if "campana_id" not in dataframe.columns:

        return dataframe.iloc[0:0].copy()

    return dataframe[
        pd.to_numeric(dataframe["campana_id"], errors="coerce")
        == int(campana_id)
    ].copy()


def _asegurar_columnas_informes(dataframe, columnas):

    preparado = dataframe.copy() if dataframe is not None else pd.DataFrame()

    for columna, valor_defecto in columnas.items():

        if columna not in preparado.columns:

            preparado[columna] = valor_defecto

    return preparado


def _columnas_tabla_informes(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _expr_texto_informes(tabla, columna, columnas, defecto=""):

    if columna in columnas:

        return f"COALESCE({tabla}.{columna}, '')"

    return f"'{defecto}'"


def _expr_valor_informes(tabla, columna, columnas, defecto="NULL"):

    if columna in columnas:

        return f"{tabla}.{columna}"

    return defecto


def _leer_cultivos_informes(conn, campana_id):

    columnas_cultivos = _columnas_tabla_informes(conn, "cultivos")

    if not columnas_cultivos:

        return pd.DataFrame()

    expr_nombre = (
        _expr_texto_informes("cultivos", "nombre", columnas_cultivos)
        if "nombre" in columnas_cultivos
        else _expr_texto_informes("cultivos", "especie", columnas_cultivos)
    )
    expr_marco = (
        _expr_texto_informes("cultivos", "marco_plantacion", columnas_cultivos)
        if "marco_plantacion" in columnas_cultivos
        else _expr_texto_informes("cultivos", "marco", columnas_cultivos)
    )
    expr_arboles = (
        _expr_valor_informes("cultivos", "numero_arboles", columnas_cultivos)
        if "numero_arboles" in columnas_cultivos
        else _expr_valor_informes("cultivos", "arboles", columnas_cultivos)
    )
    filtro_campana = ""
    params = []

    if "campana_id" in columnas_cultivos:

        filtro_campana = "WHERE cultivos.campana_id=?"
        params.append(int(campana_id))

    consulta = f"""
        SELECT
            cultivos.id,
            {_expr_valor_informes("cultivos", "campana_id", columnas_cultivos)}
                AS campana_id,
            COALESCE(campanas.nombre, '') AS campana,
            {expr_nombre} AS cultivo,
            {_expr_texto_informes("cultivos", "codigo_siex", columnas_cultivos)}
                AS codigo_siex,
            {_expr_valor_informes("cultivos", "superficie", columnas_cultivos, "0")}
                AS superficie,
            {_expr_valor_informes("cultivos", "ano_plantacion", columnas_cultivos)}
                AS ano_plantacion,
            {expr_marco} AS marco_plantacion,
            {expr_arboles} AS numero_arboles,
            GROUP_CONCAT(parcelas.nombre, ', ') AS parcelas,
            {_expr_texto_informes("cultivos", "observaciones", columnas_cultivos)}
                AS observaciones
        FROM cultivos
        LEFT JOIN campanas ON campanas.id = cultivos.campana_id
        LEFT JOIN cultivo_parcelas
            ON cultivo_parcelas.cultivo_id = cultivos.id
        LEFT JOIN parcelas ON parcelas.id = cultivo_parcelas.parcela_id
        {filtro_campana}
        GROUP BY cultivos.id
        ORDER BY campanas.fecha_inicio DESC, cultivos.nombre, cultivos.id
    """

    return pd.read_sql_query(consulta, conn, params=params)


def cargar_datos_informes(conn, campana_id):

    avisos = []

    try:

        cultivos = _leer_cultivos_informes(conn, campana_id)
        cultivos = _asegurar_columnas_informes(
            cultivos,
            {
                "id": "",
                "campana_id": "",
                "campana": "",
                "cultivo": "",
                "codigo_siex": "",
                "superficie": 0.0,
                "ano_plantacion": "",
                "marco_plantacion": "",
                "numero_arboles": "",
                "parcelas": "",
                "observaciones": "",
            },
        )

    except Exception as exc:

        cultivos = pd.DataFrame()
        avisos.append(f"El listado de cultivos no está disponible: {exc}")

    try:

        movimientos = _filtrar_campana_informes(
            _leer_movimientos_contabilidad(conn=conn),
            campana_id,
        )

        if not movimientos.empty:

            terceros = movimientos.apply(
                _resolver_tercero_movimiento,
                axis=1,
            )
            movimientos = pd.concat([movimientos, terceros], axis=1)
            movimientos["tercero"] = movimientos[
                "tercero_resuelto"
            ].fillna("")
            movimientos["facturas"] = movimientos.get(
                "facturas_count",
                0,
            )

        movimientos = _asegurar_columnas_informes(
            movimientos,
            {
                "id": "",
                "fecha": "",
                "tipo": "",
                "categoria": "",
                "concepto": "",
                "tercero": "",
                "numero_factura": "",
                "base_imponible": 0.0,
                "iva_importe": 0.0,
                "total": 0.0,
                "pagado": 0,
                "fecha_pago": "",
                "cultivo": "",
                "facturas": 0,
            },
        )

    except Exception as exc:

        movimientos = pd.DataFrame()
        avisos.append(f"No se puede generar el informe económico: {exc}")

    try:

        tratamientos = _filtrar_campana_informes(
            _leer_tratamientos_guardados(conn=conn),
            campana_id,
        )

        if not tratamientos.empty:

            tratamientos["fecha"] = tratamientos.get("fecha_inicio", "")
            tratamientos["superficie"] = tratamientos.get(
                "superficie_tratada",
                0,
            )
            tratamientos["producto"] = tratamientos.get("producto", "")
            tratamientos["recetas"] = tratamientos.get("recetas_count", 0)
            eficacia_serie = (
                tratamientos["eficacia"]
                if "eficacia" in tratamientos.columns
                else pd.Series("", index=tratamientos.index)
            )
            tratamientos["eficacia"] = (
                eficacia_serie
                .fillna("")
                .astype(str)
                .str.upper()
                .map(
                    {
                        "BUENA": "B",
                        "BUENO": "B",
                        "REGULAR": "R",
                        "MALA": "M",
                        "MALO": "M",
                        "B": "B",
                        "R": "R",
                        "M": "M",
                    }
                )
                .fillna("")
            )

        tratamientos = _asegurar_columnas_informes(
            tratamientos,
            {
                "id": "",
                "fecha": "",
                "fecha_inicio": "",
                "fecha_fin": "",
                "cultivo": "",
                "parcelas": "",
                "producto": "",
                "eficacia": "",
                "superficie": 0.0,
                "recetas": 0,
            },
        )

    except Exception as exc:

        tratamientos = pd.DataFrame()
        avisos.append(f"El resumen de tratamientos no está disponible: {exc}")

    try:

        fertilizaciones = _filtrar_campana_informes(
            _preparar_fertilizaciones_presentacion(
                _leer_fertilizaciones_guardadas(conn=conn)
            ),
            campana_id,
        )

        if not fertilizaciones.empty:

            fertilizaciones["cultivo"] = fertilizaciones.get(
                "cultivo_mostrado",
                fertilizaciones.get("cultivo", ""),
            )
            fertilizaciones["tipo"] = fertilizaciones.get(
                "tipo",
                fertilizaciones.get("tipo_fertilizante", ""),
            )

        fertilizaciones = _asegurar_columnas_informes(
            fertilizaciones,
            {
                "id": "",
                "fecha": "",
                "cultivo": "",
                "parcelas": "",
                "producto": "",
                "cantidad": 0.0,
                "superficie": 0.0,
            },
        )

    except Exception as exc:

        fertilizaciones = pd.DataFrame()
        avisos.append(f"El resumen de fertilización no está disponible: {exc}")

    try:

        practicas = _filtrar_campana_informes(
            _preparar_practicas_presentacion(
                _leer_practicas_guardadas(conn=conn)
            ),
            campana_id,
        )

        if not practicas.empty:

            practicas["cultivo"] = practicas.get(
                "cultivo_mostrado",
                practicas.get("cultivo", ""),
            )
            practicas["prestador"] = practicas.get(
                "proveedor",
                practicas.get("prestador", ""),
            )

        practicas = _asegurar_columnas_informes(
            practicas,
            {
                "id": "",
                "fecha": "",
                "cultivo": "",
                "parcelas": "",
                "labor": "",
                "prestador": "",
                "superficie": 0.0,
            },
        )

    except Exception as exc:

        practicas = pd.DataFrame()
        avisos.append(
            f"El resumen de prácticas culturales no está disponible: {exc}"
        )

    try:

        cosechas = _filtrar_campana_informes(
            _preparar_cosechas_presentacion(
                _leer_cosechas_guardadas(conn=conn)
            ),
            campana_id,
        )

        if not cosechas.empty:

            cosechas["cultivo"] = cosechas.get(
                "cultivo_mostrado",
                cosechas.get("cultivo", ""),
            )
            cosechas["kg"] = cosechas.get("cantidad", cosechas.get("kg", 0))
            cosechas["producto"] = cosechas.get("producto", "")

        cosechas = _asegurar_columnas_informes(
            cosechas,
            {
                "id": "",
                "fecha": "",
                "cultivo": "",
                "producto": "",
                "parcelas": "",
                "superficie_detalle": 0.0,
                "kg": 0.0,
                "precio": 0.0,
                "lote": "",
                "cliente": "",
                "nif_cliente": "",
                "albaran": "",
                "factura": "",
                "destino": "",
                "observaciones": "",
            },
        )

    except Exception as exc:

        cosechas = pd.DataFrame()
        avisos.append(f"El contador de cosechas no está disponible: {exc}")

    return {
        "avisos": avisos,
        "cultivos": cultivos,
        "movimientos": movimientos,
        "tratamientos": tratamientos,
        "fertilizaciones": fertilizaciones,
        "practicas": practicas,
        "cosechas": cosechas,
    }


def render(CAMPANA):

    st.title("📊 Informes")

    campanas_informe = leer(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin
        FROM campanas
        ORDER BY fecha_inicio DESC,id DESC
        """
    )

    campana_informe_id = st.selectbox(
        "Campaña",
        campanas_informe["id"].astype(int).tolist(),
        index=(
            campanas_informe["id"].astype(int).tolist().index(CAMPANA)
            if CAMPANA in campanas_informe["id"].astype(int).tolist()
            else 0
        ),
        format_func=lambda valor: campanas_informe.loc[
            campanas_informe["id"] == valor,
            "nombre"
        ].iloc[0],
        key="campana_informes"
    )

    campana_seleccionada = campanas_informe[
        campanas_informe["id"] == campana_informe_id
    ].iloc[0]
    fecha_inicio_campana = pd.to_datetime(
        campana_seleccionada["fecha_inicio"],
        errors="coerce"
    )
    fecha_fin_campana = pd.to_datetime(
        campana_seleccionada["fecha_fin"],
        errors="coerce"
    )
    fecha_desde_defecto = (
        fecha_inicio_campana.date()
        if not pd.isna(fecha_inicio_campana)
        else date(date.today().year, 1, 1)
    )
    fecha_hasta_defecto = (
        fecha_fin_campana.date()
        if not pd.isna(fecha_fin_campana)
        else date.today()
    )

    conn_informes = conectar()

    try:

        datos_informes = cargar_datos_informes(
            conn_informes,
            campana_informe_id,
        )

    finally:

        conn_informes.close()

    avisos_informes = datos_informes["avisos"]
    cultivos_maestros_informe = datos_informes["cultivos"]
    movimientos_informe = datos_informes["movimientos"]
    tratamientos_informe = datos_informes["tratamientos"]
    fertilizaciones_informe = datos_informes["fertilizaciones"]
    practicas_informe = datos_informes["practicas"]
    cosechas_informe = datos_informes["cosechas"]

    cultivos_informe = set()

    for dataframe_informe in [
        cultivos_maestros_informe,
        movimientos_informe,
        tratamientos_informe,
        fertilizaciones_informe,
        practicas_informe,
        cosechas_informe
    ]:

        if "cultivo" in dataframe_informe.columns:

            cultivos_informe.update(
                dataframe_informe["cultivo"]
                .fillna("")
                .astype(str)
                .str.strip()
                .loc[lambda serie: serie != ""]
                .tolist()
            )

    cultivo_informe = st.selectbox(
        "Cultivo (opcional)",
        [None] + sorted(cultivos_informe),
        format_func=lambda valor: (
            "Todos los cultivos" if valor is None else valor
        ),
        key=f"cultivo_informes_{campana_informe_id}"
    )

    fechas_reales_informe = []

    for dataframe_informe in [
        movimientos_informe,
        tratamientos_informe,
        fertilizaciones_informe,
        practicas_informe,
        cosechas_informe
    ]:

        if "fecha" in dataframe_informe.columns:

            fechas_reales_informe.extend(
                pd.to_datetime(
                    dataframe_informe["fecha"],
                    errors="coerce"
                ).dropna().tolist()
            )

        if "fecha_fin" in dataframe_informe.columns:

            fechas_reales_informe.extend(
                pd.to_datetime(
                    dataframe_informe["fecha_fin"],
                    errors="coerce"
                ).dropna().tolist()
            )

    if fechas_reales_informe:

        fecha_real_minima = min(fechas_reales_informe).date()
        fecha_real_maxima = max(fechas_reales_informe).date()
        fecha_desde_defecto = fecha_real_minima
        fecha_hasta_defecto = fecha_real_maxima

        fuera_periodo_campana = (
            (
                not pd.isna(fecha_inicio_campana)
                and fecha_real_minima < fecha_inicio_campana.date()
            )
            or (
                not pd.isna(fecha_fin_campana)
                and fecha_real_maxima > fecha_fin_campana.date()
            )
        )

        if fuera_periodo_campana:

            st.warning(
                "Hay registros con fechas fuera del periodo oficial de la "
                "campaña. El rango inicial se ha ampliado para mostrarlos."
            )

    columna_fecha_desde, columna_fecha_hasta = st.columns(2)

    with columna_fecha_desde:

        fecha_desde_informe = st.date_input(
            "Fecha desde",
            value=fecha_desde_defecto,
            format="DD/MM/YYYY",
            key=f"fecha_desde_informes_v2_{campana_informe_id}"
        )

    with columna_fecha_hasta:

        fecha_hasta_informe = st.date_input(
            "Fecha hasta",
            value=fecha_hasta_defecto,
            format="DD/MM/YYYY",
            key=f"fecha_hasta_informes_v2_{campana_informe_id}"
        )

    def aplicar_filtros_informe(dataframe, usar_intervalo=False):

        filtrado = dataframe.copy()

        if filtrado.empty:

            return filtrado

        fechas = pd.to_datetime(filtrado["fecha"], errors="coerce").dt.date

        if usar_intervalo and "fecha_fin" in filtrado.columns:

            fechas_fin = pd.to_datetime(
                filtrado["fecha_fin"],
                errors="coerce"
            ).dt.date
            filtrado = filtrado[
                (fechas <= fecha_hasta_informe)
                & (fechas_fin >= fecha_desde_informe)
            ]

        else:

            filtrado = filtrado[
                (fechas >= fecha_desde_informe)
                & (fechas <= fecha_hasta_informe)
            ]

        if cultivo_informe is not None and "cultivo" in filtrado.columns:

            filtrado = filtrado[
                filtrado["cultivo"].fillna("").astype(str)
                == cultivo_informe
            ]

        return filtrado.copy()

    if fecha_desde_informe > fecha_hasta_informe:

        st.warning("La fecha desde no puede ser posterior a la fecha hasta")
        movimientos_filtrados_informe = movimientos_informe.iloc[0:0]
        cultivos_maestros_filtrados = cultivos_maestros_informe.iloc[0:0]
        tratamientos_filtrados_informe = tratamientos_informe.iloc[0:0]
        fertilizaciones_filtradas_informe = (
            fertilizaciones_informe.iloc[0:0]
        )
        practicas_filtradas_informe = practicas_informe.iloc[0:0]
        cosechas_filtradas_informe = cosechas_informe.iloc[0:0]

    else:

        movimientos_filtrados_informe = aplicar_filtros_informe(
            movimientos_informe
        )
        tratamientos_filtrados_informe = aplicar_filtros_informe(
            tratamientos_informe,
            usar_intervalo=True
        )
        fertilizaciones_filtradas_informe = aplicar_filtros_informe(
            fertilizaciones_informe
        )
        practicas_filtradas_informe = aplicar_filtros_informe(
            practicas_informe
        )
        cosechas_filtradas_informe = aplicar_filtros_informe(
            cosechas_informe
        )
        cultivos_maestros_filtrados = cultivos_maestros_informe.copy()

        if (
            cultivo_informe is not None
            and "cultivo" in cultivos_maestros_filtrados.columns
        ):

            cultivos_maestros_filtrados = cultivos_maestros_filtrados[
                cultivos_maestros_filtrados["cultivo"].fillna("").astype(str)
                == cultivo_informe
            ].copy()

    for aviso in avisos_informes:

        st.info(aviso)

    movimientos_economicos = movimientos_filtrados_informe.copy()

    for columna in ["base_imponible", "iva_importe", "total"]:

        if columna in movimientos_economicos.columns:

            movimientos_economicos[columna] = pd.to_numeric(
                movimientos_economicos[columna],
                errors="coerce"
            ).fillna(0.0)

    ingresos_informe = 0.0
    gastos_informe = 0.0
    iva_soportado_informe = 0.0
    iva_repercutido_informe = 0.0
    pendiente_pagar_informe = 0.0
    pendiente_cobrar_informe = 0.0
    resumen_categoria = pd.DataFrame()
    resumen_cultivo = pd.DataFrame()
    pendientes_pagar = pd.DataFrame()
    pendientes_cobrar = pd.DataFrame()

    if not movimientos_economicos.empty:

        es_ingreso = movimientos_economicos["tipo"] == "Ingreso"
        es_gasto = movimientos_economicos["tipo"] == "Gasto"
        pendiente = (
            pd.to_numeric(
                movimientos_economicos["pagado"],
                errors="coerce"
            ).fillna(0) == 0
        )
        ingresos_informe = movimientos_economicos.loc[
            es_ingreso, "total"
        ].sum()
        gastos_informe = movimientos_economicos.loc[
            es_gasto, "total"
        ].sum()
        iva_soportado_informe = movimientos_economicos.loc[
            es_gasto, "iva_importe"
        ].sum()
        iva_repercutido_informe = movimientos_economicos.loc[
            es_ingreso, "iva_importe"
        ].sum()
        pendiente_pagar_informe = movimientos_economicos.loc[
            es_gasto & pendiente, "total"
        ].sum()
        pendiente_cobrar_informe = movimientos_economicos.loc[
            es_ingreso & pendiente, "total"
        ].sum()

        resumen_categoria = (
            movimientos_economicos
            .assign(
                categoria=movimientos_economicos["categoria"]
                .fillna("")
                .replace("", "Sin categoría")
            )
            .groupby(["tipo", "categoria"], as_index=False)
            .agg(
                base_imponible=("base_imponible", "sum"),
                iva=("iva_importe", "sum"),
                total=("total", "sum"),
                movimientos=("id", "count")
            )
        )

        movimientos_por_cultivo = movimientos_economicos.copy()
        movimientos_por_cultivo["cultivo"] = (
            movimientos_por_cultivo["cultivo"]
            .fillna("")
            .replace("", "Sin cultivo")
        )
        resumen_cultivo = (
            movimientos_por_cultivo
            .assign(
                ingresos=lambda df: df["total"].where(
                    df["tipo"] == "Ingreso", 0.0
                ),
                gastos=lambda df: df["total"].where(
                    df["tipo"] == "Gasto", 0.0
                )
            )
            .groupby("cultivo", as_index=False)
            .agg(
                ingresos=("ingresos", "sum"),
                gastos=("gastos", "sum"),
                movimientos=("id", "count")
            )
        )
        resumen_cultivo["resultado"] = (
            resumen_cultivo["ingresos"] - resumen_cultivo["gastos"]
        )

        columnas_pendientes = [
            "fecha",
            "tercero",
            "facturas",
            "concepto",
            "numero_factura",
            "total",
            "fecha_pago"
        ]
        pendientes_pagar = movimientos_economicos.loc[
            es_gasto & pendiente, columnas_pendientes
        ].rename(columns={"numero_factura": "factura"})
        pendientes_cobrar = movimientos_economicos.loc[
            es_ingreso & pendiente, columnas_pendientes
        ].rename(columns={"numero_factura": "factura"})

    resumen_tratamientos = pd.DataFrame()

    if not tratamientos_filtrados_informe.empty:

        resumen_tratamientos = (
            tratamientos_filtrados_informe
            .assign(
                superficie=lambda df: pd.to_numeric(
                    df["superficie"], errors="coerce"
                ).fillna(0.0)
            )
            .groupby(["cultivo", "producto"], as_index=False)
            .agg(
                aplicaciones=("id", "count"),
                superficie_total=("superficie", "sum")
            )
        )

    resumen_fertilizaciones = pd.DataFrame()

    if not fertilizaciones_filtradas_informe.empty:

        resumen_fertilizaciones = (
            fertilizaciones_filtradas_informe
            .assign(
                cantidad=lambda df: pd.to_numeric(
                    df["cantidad"], errors="coerce"
                ).fillna(0.0),
                superficie=lambda df: pd.to_numeric(
                    df["superficie"], errors="coerce"
                ).fillna(0.0)
            )
            .groupby(["cultivo", "producto"], as_index=False)
            .agg(
                cantidad_total=("cantidad", "sum"),
                superficie_total=("superficie", "sum")
            )
        )

    resumen_practicas = pd.DataFrame()

    if not practicas_filtradas_informe.empty:

        resumen_practicas = (
            practicas_filtradas_informe
            .assign(
                superficie=lambda df: pd.to_numeric(
                    df["superficie"], errors="coerce"
                ).fillna(0.0)
            )
            .groupby(["cultivo", "labor"], as_index=False)
            .agg(
                labores=("id", "count"),
                superficie_total=("superficie", "sum")
            )
        )

    resumen_excel = pd.DataFrame(
        [
            ("Campaña", str(campana_seleccionada["nombre"])),
            ("Fecha desde", formatear_fecha_es(fecha_desde_informe)),
            ("Fecha hasta", formatear_fecha_es(fecha_hasta_informe)),
            ("Ingresos totales", float(ingresos_informe)),
            ("Gastos totales", float(gastos_informe)),
            (
                "Resultado",
                float(ingresos_informe - gastos_informe)
            ),
            ("IVA soportado", float(iva_soportado_informe)),
            ("IVA repercutido", float(iva_repercutido_informe)),
            (
                "Diferencia IVA",
                float(iva_repercutido_informe - iva_soportado_informe)
            ),
            ("Pendiente de pagar", float(pendiente_pagar_informe)),
            ("Pendiente de cobrar", float(pendiente_cobrar_informe)),
            (
                "Número de tratamientos",
                len(tratamientos_filtrados_informe)
            ),
            (
                "Número de cultivos",
                len(cultivos_maestros_filtrados)
            ),
            (
                "Número de fertilizaciones",
                len(fertilizaciones_filtradas_informe)
            ),
            (
                "Número de prácticas culturales",
                len(practicas_filtradas_informe)
            ),
            (
                "Número de movimientos económicos",
                len(movimientos_economicos)
            )
        ],
        columns=["Indicador", "Valor"]
    )

    def preparar_dataframe_excel(dataframe):

        if dataframe is None or dataframe.empty:

            return pd.DataFrame(
                {"Aviso": ["Sin datos para los filtros seleccionados"]}
            )

        preparado = dataframe.copy()
        preparado = formatear_columnas_fecha_es(preparado)

        columnas_texto_excel = [
            columna
            for columna in preparado.columns
            if (
                pd.api.types.is_object_dtype(preparado[columna].dtype)
                or pd.api.types.is_string_dtype(preparado[columna].dtype)
            )
        ]

        for columna in columnas_texto_excel:

            preparado[columna] = preparado[columna].map(
                lambda valor: (
                    "'" + valor
                    if isinstance(valor, str)
                    and valor.startswith(("=", "+", "-", "@"))
                    else valor
                )
            )

        return preparado

    def mostrar_dataframe_con_fechas(dataframe, columnas_fecha):

        preparado = preparar_columnas_fecha_tabla(dataframe, columnas_fecha)
        preparado = formatear_columnas_fecha_es(preparado, columnas_fecha)
        st.dataframe(
            preparar_dataframe_visual(preparado),
            hide_index=True,
            use_container_width=True,
        )

    def escribir_secciones_excel(writer, nombre_hoja, secciones):

        fila_inicio = 0
        filas_negrita = []

        for titulo, dataframe in secciones:

            pd.DataFrame([[titulo]]).to_excel(
                writer,
                sheet_name=nombre_hoja,
                index=False,
                header=False,
                startrow=fila_inicio
            )
            filas_negrita.append(fila_inicio + 1)
            fila_inicio += 1
            preparado = preparar_dataframe_excel(dataframe)
            preparado.to_excel(
                writer,
                sheet_name=nombre_hoja,
                index=False,
                startrow=fila_inicio
            )
            filas_negrita.append(fila_inicio + 1)
            fila_inicio += len(preparado) + 3

        return filas_negrita

    buffer_excel = io.BytesIO()
    filas_negrita_excel = {}

    with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:

        filas_negrita_excel["Resumen"] = escribir_secciones_excel(
            writer,
            "Resumen",
            [("Resumen general", resumen_excel)]
        )
        filas_negrita_excel["Cultivos"] = escribir_secciones_excel(
            writer,
            "Cultivos",
            [("Cultivos de la campaña", cultivos_maestros_filtrados)]
        )
        filas_negrita_excel["Economico"] = escribir_secciones_excel(
            writer,
            "Economico",
            [
                ("Resumen por categoría", resumen_categoria),
                ("Resumen por cultivo", resumen_cultivo)
            ]
        )
        filas_negrita_excel["Movimientos"] = escribir_secciones_excel(
            writer,
            "Movimientos",
            [("Movimientos filtrados", movimientos_economicos)]
        )
        filas_negrita_excel["Pendiente pagar"] = escribir_secciones_excel(
            writer,
            "Pendiente pagar",
            [("Pendiente de pagar", pendientes_pagar)]
        )
        filas_negrita_excel["Pendiente cobrar"] = escribir_secciones_excel(
            writer,
            "Pendiente cobrar",
            [("Pendiente de cobrar", pendientes_cobrar)]
        )
        filas_negrita_excel["Tratamientos"] = escribir_secciones_excel(
            writer,
            "Tratamientos",
            [
                ("Resumen por cultivo y producto", resumen_tratamientos),
                ("Detalle", tratamientos_filtrados_informe)
            ]
        )
        filas_negrita_excel["Fertilizacion"] = escribir_secciones_excel(
            writer,
            "Fertilizacion",
            [
                (
                    "Resumen por cultivo y producto",
                    resumen_fertilizaciones
                ),
                ("Detalle", fertilizaciones_filtradas_informe)
            ]
        )
        filas_negrita_excel["Practicas"] = escribir_secciones_excel(
            writer,
            "Practicas",
            [
                ("Resumen por cultivo y labor", resumen_practicas),
                ("Detalle", practicas_filtradas_informe)
            ]
        )
        filas_negrita_excel["Cosecha"] = escribir_secciones_excel(
            writer,
            "Cosecha",
            [("Detalle de cosecha", cosechas_filtradas_informe)]
        )

        for nombre_hoja, hoja in writer.sheets.items():

            hoja.freeze_panes = "A2"

            for numero_fila in filas_negrita_excel.get(nombre_hoja, []):

                for celda in hoja[numero_fila]:

                    celda.font = Font(bold=True)

            for columna_celdas in hoja.columns:

                ancho = min(
                    max(
                        len(str(celda.value))
                        if celda.value is not None
                        else 0
                        for celda in columna_celdas
                    ) + 2,
                    45
                )
                hoja.column_dimensions[
                    columna_celdas[0].column_letter
                ].width = max(ancho, 10)

            for fila in hoja.iter_rows():

                for celda in fila:

                    if isinstance(celda.value, float):

                        celda.number_format = "#,##0.00"

    buffer_excel.seek(0)
    nombre_campana_archivo = "".join(
        caracter if caracter.isalnum() else "_"
        for caracter in str(campana_seleccionada["nombre"])
    ).strip("_")
    nombre_archivo_excel = (
        f"cuadernopro_informe_{nombre_campana_archivo}_"
        f"{date.today().strftime('%Y%m%d')}.xlsx"
    )

    st.download_button(
        "📥 Descargar informe Excel",
        data=buffer_excel.getvalue(),
        file_name=nombre_archivo_excel,
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        key="descargar_informe_excel"
    )

    st.divider()

    (
        tab_resumen,
        tab_cultivos,
        tab_economico,
        tab_tratamientos,
        tab_fertilizacion,
        tab_practicas,
        tab_pendientes
    ) = st.tabs(
        [
            "Resumen general",
            "Cultivos",
            "Informe económico",
            "Tratamientos",
            "Fertilización",
            "Prácticas culturales",
            "Pendientes"
        ]
    )

    with tab_resumen:

        st.caption(
            "Periodo consultado: "
            f"{formatear_fecha_es(fecha_desde_informe)} a "
            f"{formatear_fecha_es(fecha_hasta_informe)}"
        )
        fila_resumen_uno = st.columns(4)
        fila_resumen_uno[0].metric(
            "Campaña seleccionada",
            str(campana_seleccionada["nombre"])
        )
        fila_resumen_uno[1].metric(
            "Ingresos totales", f"{ingresos_informe:.2f} €"
        )
        fila_resumen_uno[2].metric(
            "Gastos totales", f"{gastos_informe:.2f} €"
        )
        fila_resumen_uno[3].metric(
            "Resultado",
            f"{ingresos_informe - gastos_informe:.2f} €"
        )

        fila_resumen_dos = st.columns(4)
        fila_resumen_dos[0].metric(
            "Cultivos", len(cultivos_maestros_filtrados)
        )
        fila_resumen_dos[1].metric(
            "Tratamientos", len(tratamientos_filtrados_informe)
        )
        fila_resumen_dos[2].metric(
            "Fertilizaciones", len(fertilizaciones_filtradas_informe)
        )
        fila_resumen_dos[3].metric(
            "Prácticas culturales", len(practicas_filtradas_informe)
        )

    with tab_cultivos:

        st.caption(
            f"Mostrando {len(cultivos_maestros_filtrados)} cultivos"
        )

        if cultivos_maestros_filtrados.empty:

            st.info("No hay cultivos para los filtros seleccionados")

        else:

            st.dataframe(
                preparar_dataframe_visual(
                    cultivos_maestros_filtrados,
                    columnas=[
                        "cultivo",
                        "campana",
                        "codigo_siex",
                        "superficie",
                        "ano_plantacion",
                        "marco_plantacion",
                        "numero_arboles",
                        "parcelas",
                        "observaciones",
                    ],
                    etiquetas_extra={
                        "campana": "Campaña",
                        "cultivo": "Cultivo",
                        "codigo_siex": "Código SIEX",
                        "superficie": "Superficie",
                        "ano_plantacion": "Año plantación",
                        "marco_plantacion": "Marco de plantación",
                        "numero_arboles": "Nº árboles",
                        "parcelas": "Parcelas",
                    },
                ),
                hide_index=True,
                use_container_width=True,
            )

    with tab_economico:

        st.caption(
            f"Mostrando {len(movimientos_economicos)} movimientos económicos"
        )
        fila_economica_uno = st.columns(4)
        fila_economica_uno[0].metric(
            "Ingresos", f"{ingresos_informe:.2f} €"
        )
        fila_economica_uno[1].metric(
            "Gastos", f"{gastos_informe:.2f} €"
        )
        fila_economica_uno[2].metric(
            "Resultado", f"{ingresos_informe - gastos_informe:.2f} €"
        )
        fila_economica_uno[3].metric(
            "Diferencia IVA",
            f"{iva_repercutido_informe - iva_soportado_informe:.2f} €"
        )

        fila_economica_dos = st.columns(4)
        fila_economica_dos[0].metric(
            "IVA soportado", f"{iva_soportado_informe:.2f} €"
        )
        fila_economica_dos[1].metric(
            "IVA repercutido", f"{iva_repercutido_informe:.2f} €"
        )
        fila_economica_dos[2].metric(
            "Pendiente de pagar", f"{pendiente_pagar_informe:.2f} €"
        )
        fila_economica_dos[3].metric(
            "Pendiente de cobrar", f"{pendiente_cobrar_informe:.2f} €"
        )

        st.subheader("Resumen por categoría")

        if resumen_categoria.empty:

            st.info("No hay movimientos para los filtros seleccionados")

        else:

            st.dataframe(
                preparar_dataframe_visual(resumen_categoria),
                hide_index=True,
                use_container_width=True
            )
            gastos_categoria = resumen_categoria[
                resumen_categoria["tipo"] == "Gasto"
            ][["categoria", "total"]].set_index("categoria")

            if not gastos_categoria.empty:

                st.bar_chart(gastos_categoria)

        st.subheader("Resumen por cultivo")

        if resumen_cultivo.empty:

            st.info("No hay movimientos asociados a cultivos")

        else:

            st.dataframe(
                preparar_dataframe_visual(
                    resumen_cultivo,
                    columnas=[
                        "cultivo",
                        "ingresos",
                        "gastos",
                        "resultado",
                        "movimientos"
                    ],
                ),
                hide_index=True,
                use_container_width=True
            )
            st.bar_chart(
                resumen_cultivo.set_index("cultivo")[
                    ["ingresos", "gastos"]
                ]
            )

        st.subheader("Movimientos filtrados")

        if movimientos_economicos.empty:

            st.info("No hay movimientos económicos para mostrar")

        else:

            mostrar_dataframe_con_fechas(
                movimientos_economicos,
                ["fecha", "fecha_pago"]
            )

    with tab_tratamientos:

        st.caption(
            f"Mostrando {len(tratamientos_filtrados_informe)} tratamientos"
        )

        if resumen_tratamientos.empty:

            st.info("No hay tratamientos para los filtros seleccionados")

        else:

            st.subheader("Resumen por cultivo y producto")
            st.dataframe(
                preparar_dataframe_visual(resumen_tratamientos),
                hide_index=True,
                use_container_width=True
            )

        st.subheader("Detalle de tratamientos")

        if not tratamientos_filtrados_informe.empty:

            mostrar_dataframe_con_fechas(
                tratamientos_filtrados_informe,
                ["fecha", "fecha_inicio", "fecha_fin"]
            )

    with tab_fertilizacion:

        st.caption(
            f"Mostrando {len(fertilizaciones_filtradas_informe)} "
            "fertilizaciones"
        )

        if resumen_fertilizaciones.empty:

            st.info("No hay fertilizaciones para los filtros seleccionados")

        else:

            st.subheader("Resumen por cultivo y producto")
            st.dataframe(
                preparar_dataframe_visual(resumen_fertilizaciones),
                hide_index=True,
                use_container_width=True
            )

        st.subheader("Detalle de fertilizaciones")

        if not fertilizaciones_filtradas_informe.empty:

            mostrar_dataframe_con_fechas(
                fertilizaciones_filtradas_informe,
                ["fecha"]
            )

    with tab_practicas:

        st.caption(
            f"Mostrando {len(practicas_filtradas_informe)} "
            "prácticas culturales"
        )

        if resumen_practicas.empty:

            st.info("No hay prácticas culturales para los filtros seleccionados")

        else:

            st.subheader("Resumen por cultivo y labor")
            st.dataframe(
                preparar_dataframe_visual(resumen_practicas),
                hide_index=True,
                use_container_width=True
            )

        st.subheader("Detalle de prácticas culturales")

        if not practicas_filtradas_informe.empty:

            mostrar_dataframe_con_fechas(
                practicas_filtradas_informe,
                ["fecha"]
            )

    with tab_pendientes:

        st.caption(
            f"Mostrando {len(pendientes_pagar)} pagos pendientes y "
            f"{len(pendientes_cobrar)} cobros pendientes"
        )
        st.subheader("Pendiente de pagar")

        if pendientes_pagar.empty:

            st.info("No hay pagos pendientes")

        else:

            mostrar_dataframe_con_fechas(
                pendientes_pagar,
                ["fecha", "fecha_pago"]
            )

        st.subheader("Pendiente de cobrar")

        if pendientes_cobrar.empty:

            st.info("No hay cobros pendientes")

        else:

            mostrar_dataframe_con_fechas(
                pendientes_cobrar,
                ["fecha", "fecha_pago"]
            )
