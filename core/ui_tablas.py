import pandas as pd


MAPA_ETIQUETAS_COLUMNAS = {
    "id": "ID",
    "campana": "Campaña",
    "campana_id": "ID campaña",
    "cultivo": "Cultivo",
    "cultivo_id": "ID cultivo",
    "producto": "Producto",
    "producto_id": "ID producto",
    "persona_id": "ID persona",
    "aplicador": "Aplicador",
    "aplicador_id": "ID aplicador",
    "cliente": "Cliente",
    "cliente_id": "ID cliente",
    "proveedor": "Proveedor",
    "proveedor_id": "ID proveedor",
    "maquinaria": "Maquinaria",
    "maquinaria_id": "ID maquinaria",
    "equipo": "Equipo",
    "equipo_id": "ID equipo",
    "equipo_aplicacion_id": "ID equipo aplicación",
    "nombre": "Nombre",
    "localidad": "Municipio / localidad",
    "nombre_explotacion": "Nombre de la explotación",
    "identificador_oficial": "Código REGEPA / identificador oficial",
    "identificador_oficial_visual": "Código REGEPA / identificador oficial",
    "registro_autonomico": "Registro autonómico",
    "codigo_regea": "Código REGEA",
    "codigo_regepa": "Código REGEPA",
    "registro_explotacion": "Registro explotación",
    "fecha": "Fecha",
    "fecha_inicio": "Fecha inicio",
    "fecha_fin": "Fecha fin",
    "fecha_alta": "Fecha de alta",
    "fecha_revision": "Fecha revisión",
    "fecha_proxima_revision": "Próxima revisión",
    "fecha_ultima_inspeccion": "Fecha revisión",
    "fecha_proxima_inspeccion": "Próxima revisión",
    "fecha_adquisicion": "Fecha de adquisición",
    "fecha_compra": "Fecha de compra",
    "provincia": "Provincia",
    "municipio": "Municipio",
    "provincia_sigpac": "Provincia SIGPAC",
    "municipio_sigpac": "Municipio SIGPAC",
    "agregado_sigpac": "Agregado SIGPAC",
    "zona_sigpac": "Zona SIGPAC",
    "poligono": "Polígono",
    "parcela": "Parcela",
    "recinto": "Recinto",
    "superficie": "Superficie",
    "superficie_sigpac": "Superficie SIGPAC",
    "superficie_cultivada": "Superficie cultivada",
    "superficie_tratada": "Superficie tratada",
    "uso_sigpac": "Uso SIGPAC",
    "cultivo_asociado": "Cultivo asociado",
    "parcelas": "Parcelas",
    "numero_roma": "Nº ROMA",
    "numero_serie": "Número de serie",
    "horas_uso": "Horas de uso",
    "num_horas": "Horas de uso",
    "matricula": "Matrícula",
    "marca": "Marca",
    "modelo": "Modelo",
    "tipo": "Tipo",
    "tipo_explotacion": "Tipo de explotación",
    "orientacion_productiva": "Orientación productiva",
    "agricultor_activo": "Agricultor activo",
    "joven_agricultor": "Joven agricultor",
    "activa": "Activa",
    "activo": "Activo",
    "fecha_baja": "Fecha de baja",
    "version": "Versión",
    "origen": "Origen",
    "filas": "Filas",
    "estado": "Estado",
    "observaciones": "Observaciones",
    "registro_producto": "Nº registro producto",
    "numero_registro": "Nº registro",
    "dosis": "Dosis",
    "caldo": "Caldo",
    "plaga": "Plaga",
    "plaga_motivo": "Plaga / motivo",
    "problema": "Plaga / problema",
    "justificacion": "Justificación",
    "eficacia": "Eficacia",
    "aplicador_selector": "Aplicador",
    "equipo_selector": "Equipo",
    "cultivo_selector": "Cultivo",
    "producto_selector": "Producto",
    "recetas": "Recetas",
    "recetas_count": "Recetas",
    "condiciones_meteorologicas": "Condiciones meteorológicas",
    "fecha_recoleccion_segura": "Fecha recolección segura",
    "titular": "Titular",
    "nif": "NIF",
    "direccion": "Dirección",
    "codigo_postal": "Código postal",
    "telefono": "Teléfono",
    "email": "Email",
    "descripcion": "Nombre / descripción",
    "variedad": "Variedad",
    "codigo_siex": "Código SIEX",
    "codigo": "Código",
    "codigo_secundario": "Código secundario",
    "codigo_catalogo": "Código catálogo",
    "nombre_catalogo": "Catálogo",
    "archivo_origen": "Archivo origen",
    "items": "Elementos",
    "total_items": "Elementos",
    "items_activos": "Elementos activos",
    "duracion_segundos": "Duración (s)",
    "descripcion_secundaria": "Descripción secundaria",
    "ano_plantacion": "Año plantación",
    "marco_plantacion": "Marco de plantación",
    "numero_arboles": "Nº árboles",
    "marco": "Marco",
    "arboles": "Árboles",
    "sistema": "Sistema",
    "materia_activa": "Materia activa",
    "uso_autorizado": "Uso autorizado",
    "plazo_seguridad": "Plazo seguridad",
    "cantidad": "Cantidad",
    "unidad": "Unidad",
    "labor": "Labor",
    "concepto": "Concepto",
    "categoria": "Categoría",
    "base_imponible": "Base imponible",
    "tipo_iva": "Tipo IVA",
    "cuota_iva": "Cuota IVA",
    "total_linea": "Total línea",
    "iva": "IVA",
    "total": "Total",
    "pendiente": "Pendiente",
    "ingresos": "Ingresos",
    "gastos": "Gastos",
    "resultado": "Resultado",
    "movimientos": "Movimientos",
    "numero_factura": "Nº factura",
    "tercero": "Cliente / proveedor",
    "tercero_resuelto": "Cliente / proveedor",
    "nif_tercero_resuelto": "NIF",
    "nombre_original": "Documento",
    "size_bytes": "Tamaño",
    "codigo_actuacion_siex": "Código actuación SIEX",
    "nif_cliente": "NIF cliente",
    "prestador": "Prestador",
    "destino": "Destino",
    "created_at": "Creado",
    "updated_at": "Actualizado",
    "responsable_nombre": "Responsable",
    "responsable_nif": "NIF responsable",
    "responsable_telefono": "Teléfono responsable",
    "asesor_nombre": "Asesor",
    "asesor_nif": "NIF asesor",
    "asesor_numero_registro": "Nº registro asesor",
    "asesor_telefono": "Teléfono asesor",
    "area": "Área",
    "registro_id": "Registro",
    "gravedad": "Gravedad",
    "campo": "Campo",
    "recomendacion": "Recomendación",
    "bloquea_exportacion": "Bloquea exportación",
    "sigpac_geojson_estado": "Estado SIGPAC",
    "sigpac_geojson_error": "Aviso SIGPAC",
    "poblacion": "Población",
    "rol": "Rol",
    "forma_pago": "Forma de pago",
    "pagado": "Pagado",
    "fecha_pago": "Fecha de pago",
    "iva_porcentaje": "IVA %",
    "iva_importe": "IVA importe",
    "retencion": "Retención",
    "desglose_iva": "Desglose IVA",
    "facturas": "Facturas",
}

COLUMNAS_TECNICAS_OCULTAS = {
    "id",
    "campana_id",
    "cultivo_id",
    "producto_id",
    "persona_id",
    "aplicador_id",
    "cliente_id",
    "proveedor_id",
    "maquinaria_id",
    "equipo_id",
    "equipo_aplicacion_id",
    "geometry",
    "sigpac_geojson",
    "sigpac_geojson_actualizado",
    "created_at",
    "updated_at",
}


def normalizar_vacios(dataframe):

    preparado = dataframe.copy() if dataframe is not None else pd.DataFrame()

    if preparado.empty:

        return preparado

    for columna in preparado.columns:

        if pd.api.types.is_bool_dtype(preparado[columna]):

            preparado[columna] = preparado[columna].fillna(False)

        elif not pd.api.types.is_datetime64_any_dtype(preparado[columna]):

            preparado[columna] = preparado[columna].where(
                preparado[columna].notna(),
                ""
            )

    return preparado


def normalizar_valores_vacios(dataframe):

    return normalizar_vacios(dataframe)


def aplicar_etiquetas_columnas(dataframe, etiquetas=None):

    mapa = dict(MAPA_ETIQUETAS_COLUMNAS)

    if etiquetas:

        mapa.update(etiquetas)

    columnas = []
    usadas = {}

    for columna in dataframe.columns:

        etiqueta = mapa.get(columna, columna)
        contador = usadas.get(etiqueta, 0)

        if contador:

            etiqueta_visual = f"{etiqueta} ({contador + 1})"

        else:

            etiqueta_visual = etiqueta

        usadas[etiqueta] = contador + 1
        columnas.append(etiqueta_visual)

    resultado = dataframe.copy()
    resultado.columns = columnas
    return resultado


def renombrar_columnas_visual(dataframe, etiquetas_extra=None):

    return aplicar_etiquetas_columnas(dataframe, etiquetas_extra)


def ocultar_columnas_tecnicas(dataframe, extra=None, mostrar_id=False):

    preparado = dataframe.copy() if dataframe is not None else pd.DataFrame()
    ocultas = set(COLUMNAS_TECNICAS_OCULTAS)

    if mostrar_id:

        ocultas.discard("id")

    if extra:

        ocultas.update(extra)

    return preparado.drop(columns=list(ocultas), errors="ignore")


def preparar_column_config_visual(dataframe, etiquetas=None):

    import streamlit as st

    mapa = dict(MAPA_ETIQUETAS_COLUMNAS)

    if etiquetas:

        mapa.update(etiquetas)

    preparado = dataframe.copy() if dataframe is not None else pd.DataFrame()
    config = {}

    for columna in preparado.columns:

        etiqueta = mapa.get(columna, columna)

        if columna == "id":

            config[columna] = st.column_config.NumberColumn(
                etiqueta,
                disabled=True
            )

        elif pd.api.types.is_bool_dtype(preparado[columna]):

            config[columna] = st.column_config.CheckboxColumn(etiqueta)

        elif pd.api.types.is_datetime64_any_dtype(preparado[columna]):

            config[columna] = st.column_config.DateColumn(
                etiqueta,
                format="DD/MM/YYYY"
            )

        elif pd.api.types.is_numeric_dtype(preparado[columna]):

            config[columna] = st.column_config.NumberColumn(etiqueta)

        else:

            config[columna] = st.column_config.TextColumn(etiqueta)

    return config


def preparar_dataframe_visual(
    dataframe,
    columnas=None,
    ocultar=None,
    etiquetas=None,
    mostrar_id=False,
    ocultar_tecnicas=True,
    ocultar_id=None,
    etiquetas_extra=None,
):

    preparado = dataframe.copy() if dataframe is not None else pd.DataFrame()

    if columnas is not None:

        columnas_existentes = [
            columna
            for columna in columnas
            if columna in preparado.columns
        ]
        preparado = preparado[columnas_existentes].copy()

    if ocultar_id is not None:

        mostrar_id = not ocultar_id

    etiquetas_finales = {}

    if etiquetas_extra:

        etiquetas_finales.update(etiquetas_extra)

    if etiquetas:

        etiquetas_finales.update(etiquetas)

    if ocultar_tecnicas and not preparado.empty:

        preparado = ocultar_columnas_tecnicas(
            preparado,
            extra=ocultar,
            mostrar_id=mostrar_id
        )

    elif ocultar:

        preparado = preparado.drop(columns=list(ocultar), errors="ignore")

    preparado = normalizar_vacios(preparado)
    return aplicar_etiquetas_columnas(preparado, etiquetas_finales)


def mapear_columnas_visuales_a_tecnicas(
    dataframe,
    etiquetas_extra=None,
    etiquetas=None
):

    mapa = dict(MAPA_ETIQUETAS_COLUMNAS)

    if etiquetas_extra:

        mapa.update(etiquetas_extra)

    if etiquetas:

        mapa.update(etiquetas)

    inverso = {
        etiqueta: columna
        for columna, etiqueta in mapa.items()
    }
    return dataframe.rename(columns={
        columna: inverso.get(columna, columna)
        for columna in dataframe.columns
    })
