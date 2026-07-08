import sqlite3

import pandas as pd
import streamlit as st

from core.actuaciones_multicultivo import leer_detalles as _leer_detalles_actuacion
from core.db import conectar
from core.ui_tablas import preparar_dataframe_visual
from services.exportacion_siex import (
    AVISO_NO_OFICIAL,
    MIME_XLSX,
    generar_excel_asistido_siex,
)


COLUMNAS_REVISION = [
    "area",
    "registro_id",
    "gravedad",
    "campo",
    "problema",
    "recomendacion",
    "bloquea_exportacion",
]

AREAS_REVISION = [
    "Explotación",
    "Parcelas SIGPAC",
    "Cultivos",
    "Tratamientos",
    "Fertilización",
    "Prácticas culturales",
    "Cosecha",
    "Maquinaria",
    "Documentos",
]


def _texto(valor):

    if valor is None:

        return ""

    try:

        if pd.isna(valor):

            return ""

    except (TypeError, ValueError):

        pass

    return str(valor).strip()


def _es_vacio(valor):

    return _texto(valor) == ""


def _entero_o_none(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return None

    return int(numero)


def _numero_vacio_o_cero(valor):

    if _es_vacio(valor):

        return True

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return True

    return float(numero) <= 0


def _tabla_existe(conn, tabla):

    try:

        fila = conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table'
            AND name=?
            """,
            (tabla,),
        ).fetchone()

    except sqlite3.Error:

        return False

    return fila is not None


def _columnas(conn, tabla):

    if not _tabla_existe(conn, tabla):

        return set()

    try:

        return {
            fila[1]
            for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
        }

    except sqlite3.Error:

        return set()


def _leer_tabla(conn, tabla):

    if not _tabla_existe(conn, tabla):

        return pd.DataFrame()

    try:

        return pd.read_sql_query(f'SELECT * FROM "{tabla}"', conn)

    except Exception:

        return pd.DataFrame()


def _filtrar_campana(dataframe, campana_id):

    if (
        dataframe.empty
        or campana_id is None
        or "campana_id" not in dataframe.columns
    ):

        return dataframe

    campanas = pd.to_numeric(dataframe["campana_id"], errors="coerce")
    return dataframe[campanas == int(campana_id)].copy()


def _agregar(filas, area, registro_id, gravedad, campo, problema, recomendacion,
             bloquea="No"):

    filas.append({
        "area": area,
        "registro_id": "" if registro_id is None else str(registro_id),
        "gravedad": gravedad,
        "campo": campo,
        "problema": problema,
        "recomendacion": recomendacion,
        "bloquea_exportacion": bloquea,
    })


def _campanas(conn):

    columnas = _columnas(conn, "campanas")

    if not {"id", "nombre"}.issubset(columnas):

        return pd.DataFrame()

    try:

        return pd.read_sql_query(
            """
            SELECT id,nombre,fecha_inicio,fecha_fin,activa
            FROM campanas
            ORDER BY fecha_inicio DESC,id DESC
            """,
            conn,
        )

    except Exception:

        return pd.DataFrame()


def _seleccionar_campana(conn, campana_actual):

    campanas = _campanas(conn)

    if campanas.empty:

        st.info(
            "No hay campañas disponibles. La revisión se hará de forma "
            "general cuando sea posible."
        )
        return None

    ids_campanas = campanas["id"].astype(int).tolist()
    indice = 0

    if campana_actual is not None and int(campana_actual) in ids_campanas:

        indice = ids_campanas.index(int(campana_actual))

    return st.selectbox(
        "Campaña",
        ids_campanas,
        index=indice,
        format_func=lambda valor: campanas.loc[
            campanas["id"].astype(int) == int(valor),
            "nombre",
        ].iloc[0],
        key="revision_siex_campana",
    )


def _mostrar_filtro_cultivo(conn):

    columnas_cultivos = _columnas(conn, "cultivos")

    tiene_nombre_cultivo = (
        "especie" in columnas_cultivos
        or "nombre" in columnas_cultivos
    )

    if "id" not in columnas_cultivos or not tiene_nombre_cultivo:

        st.caption(
            "Filtro de cultivo no disponible: no hay una estructura de "
            "cultivos suficiente para aplicarlo de forma segura."
        )
        return None

    st.caption(
        "Filtro de cultivo no aplicado en esta primera versión: algunas "
        "áreas guardan el cultivo como texto y no como referencia estructurada."
    )
    return None


def _contar_relaciones(dataframe, campo_id):

    if dataframe.empty or campo_id not in dataframe.columns:

        return {}

    datos = dataframe.copy()
    datos[campo_id] = pd.to_numeric(datos[campo_id], errors="coerce")
    datos = datos.dropna(subset=[campo_id])

    if datos.empty:

        return {}

    return datos.groupby(campo_id).size().astype(int).to_dict()


def _contar_detalles_multicultivo(conn, tabla, campo_registro):

    detalles = _leer_detalles_actuacion(conn, tabla, campo_registro)

    if detalles.empty:

        return {}, {}

    detalles_con_parcela = detalles.copy()

    if "parcela_id" in detalles_con_parcela.columns:

        detalles_con_parcela["parcela_id"] = pd.to_numeric(
            detalles_con_parcela["parcela_id"],
            errors="coerce",
        )
        detalles_con_parcela = detalles_con_parcela.dropna(
            subset=["parcela_id"],
        )

    parcelas_por_registro = _contar_relaciones(
        detalles_con_parcela,
        "registro_id",
    )
    cultivos_por_registro = _contar_relaciones(detalles, "registro_id")
    return parcelas_por_registro, cultivos_por_registro


def _revisar_explotacion(conn, filas):

    area = "Explotación"
    explotacion = _leer_tabla(conn, "explotacion")

    if not _tabla_existe(conn, "explotacion"):

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "explotacion",
            "No existe la tabla de explotación.",
            "Revisar la instalación antes de preparar exportación asistida.",
        )
        return 0

    if explotacion.empty:

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "explotacion",
            "No hay datos de explotación registrados.",
            "Completar los datos básicos de la explotación.",
        )
        return 0

    fila = explotacion.iloc[0]
    registro_id = fila.get("id", 1)
    campos_basicos = [
        ("titular", "titular", "Completar el titular de la explotación."),
        ("nif", "NIF", "Completar el NIF del titular."),
        (
            "nombre_explotacion",
            "nombre de explotación",
            "Completar el nombre de la explotación si procede.",
        ),
    ]

    for columna, etiqueta, recomendacion in campos_basicos:

        if columna in explotacion.columns and _es_vacio(fila.get(columna)):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                columna,
                f"Falta {etiqueta}.",
                recomendacion,
            )

    candidatos_identificador = [
        columna
        for columna in [
            "registro_explotacion",
            "codigo_regea",
            "codigo_regepa",
        ]
        if columna in explotacion.columns
    ]

    if candidatos_identificador and all(
        _es_vacio(fila.get(columna))
        for columna in candidatos_identificador
    ):

        _agregar(
            filas,
            area,
            registro_id,
            "Aviso",
            "identificador_REA_REGEA_REGEPA",
            "No hay identificador oficial de explotación informado.",
            "Confirmar qué identificador aplica y completarlo antes de exportar.",
        )

    if (
        "responsable_nombre" in explotacion.columns
        and _es_vacio(fila.get("responsable_nombre"))
    ):

        _agregar(
            filas,
            area,
            registro_id,
            "Aviso",
            "responsable_nombre",
            "No hay responsable informado.",
            "Completar responsable si procede para la revisión SIEX/CUE.",
        )

    if (
        "asesor_nombre" in explotacion.columns
        and _es_vacio(fila.get("asesor_nombre"))
    ):

        _agregar(
            filas,
            area,
            registro_id,
            "Aviso",
            "asesor_nombre",
            "No hay asesor informado.",
            "Completar asesor o dejar constancia si no procede.",
        )

    return 1


def _revisar_parcelas(conn, filas):

    area = "Parcelas SIGPAC"
    parcelas = _leer_tabla(conn, "parcelas")

    if not _tabla_existe(conn, "parcelas"):

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "parcelas",
            "No existe la tabla de parcelas.",
            "Crear o revisar parcelas antes de preparar exportación asistida.",
        )
        return 0

    if parcelas.empty:

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "parcelas",
            "No hay parcelas registradas.",
            "Añadir parcelas SIGPAC antes de revisar SIEX/CUE.",
        )
        return 0

    cultivos = _leer_tabla(conn, "cultivos")
    cultivos_por_parcela = (
        _contar_relaciones(cultivos, "parcela_id")
        if "parcela_id" in cultivos.columns
        else {}
    )
    campos_obligatorios = [
        ("provincia_sigpac", "provincia SIGPAC"),
        ("municipio_sigpac", "municipio SIGPAC"),
        ("poligono", "polígono"),
        ("parcela", "parcela"),
        ("recinto", "recinto"),
    ]

    for _, parcela in parcelas.iterrows():

        registro_id = parcela.get("id")

        for columna, etiqueta in campos_obligatorios:

            if columna in parcelas.columns and _es_vacio(parcela.get(columna)):

                _agregar(
                    filas,
                    area,
                    registro_id,
                    "Aviso",
                    columna,
                    f"Parcela sin {etiqueta}.",
                    "Completar la referencia SIGPAC.",
                )

        if (
            "superficie_sigpac" in parcelas.columns
            and _numero_vacio_o_cero(parcela.get("superficie_sigpac"))
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "superficie_sigpac",
                "Parcela sin superficie SIGPAC válida.",
                "Completar o revisar la superficie SIGPAC.",
            )

        if cultivos_por_parcela is not None:

            parcela_id = pd.to_numeric(registro_id, errors="coerce")

            if (
                not pd.isna(parcela_id)
                and int(parcela_id) not in cultivos_por_parcela
            ):

                _agregar(
                    filas,
                    area,
                    registro_id,
                    "Aviso",
                    "cultivo_asociado",
                    "Parcela sin cultivo asociado.",
                    "Asociar al menos un cultivo si procede.",
                )

        geometria_disponible = any(
            columna in parcelas.columns and not _es_vacio(parcela.get(columna))
            for columna in ["geometry", "sigpac_geojson"]
        )

        if not geometria_disponible:

            _agregar(
                filas,
                area,
                registro_id,
                "Info",
                "geometria",
                "No hay geometría disponible para la parcela.",
                "No bloquea la revisión; confirmar si el paquete asistido la necesitará.",
            )

    return len(parcelas)


def _revisar_cultivos(conn, filas):

    area = "Cultivos"
    cultivos = _leer_tabla(conn, "cultivos")

    if not _tabla_existe(conn, "cultivos"):

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "cultivos",
            "No existe la tabla de cultivos.",
            "Revisar la instalación antes de preparar exportación asistida.",
        )
        return 0

    if cultivos.empty:

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "cultivos",
            "No hay cultivos registrados.",
            "Añadir cultivos antes de revisar SIEX/CUE.",
        )
        return 0

    if "campana_id" not in cultivos.columns:

        _agregar(
            filas,
            area,
            None,
            "Info",
            "campana_id",
            "Los cultivos no tienen relación directa con campaña.",
            "Revisar si será necesario modelar cultivo por campaña antes de exportar.",
        )

    if "superficie" not in cultivos.columns:

        _agregar(
            filas,
            area,
            None,
            "Info",
            "superficie",
            "No hay superficie propia por cultivo.",
            "La superficie se infiere de parcelas; revisar si basta para exportación asistida.",
        )

    for _, cultivo in cultivos.iterrows():

        registro_id = cultivo.get("id")
        nombre_cultivo = (
            cultivo.get("especie")
            if "especie" in cultivos.columns
            else cultivo.get("nombre")
        )

        if _es_vacio(nombre_cultivo):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "nombre",
                "Cultivo sin nombre/especie.",
                "Completar el nombre del cultivo.",
            )

        codigo_cultivo = (
            cultivo.get("codigo_siex")
            if "codigo_siex" in cultivos.columns
            else cultivo.get("codigo_cultivo_siex")
        )

        if _es_vacio(codigo_cultivo):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "codigo_cultivo_siex",
                "No existe código normalizado SIEX/CUE para el cultivo.",
                "Pendiente de catálogo oficial; no inventar códigos.",
            )

    return len(cultivos)


def _producto_por_id(conn):

    productos = _leer_tabla(conn, "productos_fito")

    if productos.empty or "id" not in productos.columns:

        return {}

    return {
        int(fila["id"]): fila
        for _, fila in productos.iterrows()
        if not pd.isna(pd.to_numeric(fila.get("id"), errors="coerce"))
    }


def _revisar_tratamientos(conn, filas, campana_id):

    area = "Tratamientos"
    tratamientos = _filtrar_campana(
        _leer_tabla(conn, "tratamientos"),
        campana_id,
    )

    if not _tabla_existe(conn, "tratamientos"):

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "tratamientos",
            "No existe la tabla de tratamientos.",
            "Revisar la instalación antes de preparar exportación asistida.",
        )
        return 0

    if tratamientos.empty:

        _agregar(
            filas,
            area,
            None,
            "Info",
            "tratamientos",
            "No hay tratamientos para la campaña seleccionada.",
            "No hay datos de tratamientos que revisar en esta campaña.",
        )
        return 0

    productos = _producto_por_id(conn)
    tratamiento_parcelas = _leer_tabla(conn, "tratamiento_parcelas")
    parcelas_por_tratamiento = _contar_relaciones(
        tratamiento_parcelas,
        "tratamiento_id",
    )
    (
        parcelas_por_detalle_tratamiento,
        cultivos_por_detalle_tratamiento,
    ) = _contar_detalles_multicultivo(
        conn,
        "tratamiento_cultivos",
        "tratamiento_id",
    )
    parcelas_por_tratamiento.update(parcelas_por_detalle_tratamiento)
    documentos = _leer_tabla(conn, "tratamientos_documentos")
    recetas_por_tratamiento = {}

    if not documentos.empty and "tratamiento_id" in documentos.columns:

        documentos_receta = documentos.copy()

        if "tipo_documento" in documentos_receta.columns:

            documentos_receta = documentos_receta[
                documentos_receta["tipo_documento"].fillna("").astype(str)
                == "receta"
            ]

        recetas_por_tratamiento = _contar_relaciones(
            documentos_receta,
            "tratamiento_id",
        )

    for _, tratamiento in tratamientos.iterrows():

        registro_id = tratamiento.get("id")

        for columna in ["fecha_inicio", "fecha_fin"]:

            if columna in tratamientos.columns and _es_vacio(tratamiento.get(columna)):

                _agregar(
                    filas,
                    area,
                    registro_id,
                    "Aviso",
                    columna,
                    f"Tratamiento sin {columna}.",
                    "Completar fechas del tratamiento.",
                )

        producto_id = pd.to_numeric(
            tratamiento.get("producto_id"),
            errors="coerce",
        )
        producto = None

        if pd.isna(producto_id) or int(producto_id) not in productos:

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "producto_id",
                "Tratamiento sin producto asociado.",
                "Seleccionar producto fitosanitario.",
            )

        else:

            producto = productos[int(producto_id)]
            registro_producto = (
                producto.get("registro")
                if "registro" in producto.index
                else producto.get("numero_registro")
            )

            if _es_vacio(registro_producto):

                _agregar(
                    filas,
                    area,
                    registro_id,
                    "Aviso",
                    "registro",
                    "Producto sin número de registro.",
                    "Completar el número de registro del producto si procede.",
                )

        cultivo_id = pd.to_numeric(
            tratamiento.get("cultivo_id"),
            errors="coerce",
        )

        tratamiento_id = pd.to_numeric(registro_id, errors="coerce")

        if (
            pd.isna(cultivo_id)
            and (
                pd.isna(tratamiento_id)
                or int(tratamiento_id) not in cultivos_por_detalle_tratamiento
            )
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "cultivo_id",
                "Tratamiento sin cultivo estructurado.",
                "Seleccionar el cultivo desde el módulo Tratamientos.",
            )

        aplicador_id = pd.to_numeric(
            tratamiento.get("aplicador_id"),
            errors="coerce",
        )
        aplicador_texto = tratamiento.get("aplicador")

        if pd.isna(aplicador_id) and _es_vacio(aplicador_texto):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "aplicador_id",
                "Tratamiento sin aplicador.",
                "Seleccionar aplicador/persona cuando proceda.",
            )

        equipo_id = pd.to_numeric(
            (
                tratamiento.get("equipo_aplicacion_id")
                if not _es_vacio(tratamiento.get("equipo_aplicacion_id"))
                else tratamiento.get("equipo_id")
            ),
            errors="coerce",
        )
        maquinaria_id = pd.to_numeric(
            tratamiento.get("maquinaria_id"),
            errors="coerce",
        )

        if pd.isna(equipo_id) and pd.isna(maquinaria_id):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "equipo_aplicacion_id",
                "Tratamiento sin equipo de aplicación.",
                "Seleccionar equipo de aplicación cuando proceda.",
            )

        if (
            not pd.isna(tratamiento_id)
            and int(tratamiento_id) not in parcelas_por_tratamiento
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "parcelas",
                "Tratamiento sin parcelas asociadas.",
                "Asociar las parcelas o recintos tratados.",
            )

        if (
            "superficie_tratada" in tratamientos.columns
            and _numero_vacio_o_cero(tratamiento.get("superficie_tratada"))
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "superficie_tratada",
                "Tratamiento sin superficie tratada válida.",
                "Completar la superficie tratada.",
            )

        eficacia = _texto(tratamiento.get("eficacia")).upper()

        if "eficacia" in tratamientos.columns and eficacia not in {"B", "R", "M"}:

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "eficacia",
                "Tratamiento sin eficacia B/R/M evaluada.",
                "Informar B, R, M o dejar vacío solo si aún no se ha evaluado.",
            )

        if (
            not pd.isna(tratamiento_id)
            and int(tratamiento_id) not in recetas_por_tratamiento
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "receta_pdf",
                "Tratamiento sin receta PDF asociada.",
                "Adjuntar receta si procede; no bloquea esta revisión.",
            )

    return len(tratamientos)


def _revisar_fertilizacion(conn, filas, campana_id):

    area = "Fertilización"
    fertilizaciones = _filtrar_campana(
        _leer_tabla(conn, "fertilizaciones"),
        campana_id,
    )

    if not _tabla_existe(conn, "fertilizaciones"):

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "fertilizaciones",
            "No existe la tabla de fertilizaciones.",
            "Revisar la instalación antes de preparar exportación asistida.",
        )
        return 0

    if fertilizaciones.empty:

        _agregar(
            filas,
            area,
            None,
            "Info",
            "fertilizaciones",
            "No hay fertilizaciones para la campaña seleccionada.",
            "No hay datos de fertilización que revisar en esta campaña.",
        )
        return 0

    fertilizacion_parcelas = _leer_tabla(conn, "fertilizacion_parcelas")
    parcelas_por_fertilizacion = _contar_relaciones(
        fertilizacion_parcelas,
        "fertilizacion_id",
    )
    (
        parcelas_por_detalle_fertilizacion,
        cultivos_por_detalle_fertilizacion,
    ) = _contar_detalles_multicultivo(
        conn,
        "fertilizacion_cultivos",
        "fertilizacion_id",
    )
    parcelas_por_fertilizacion.update(parcelas_por_detalle_fertilizacion)

    _agregar(
        filas,
        area,
        None,
        "Info",
        "unidad",
        "Las unidades de fertilización pueden requerir normalización futura.",
        "Confirmar unidades oficiales antes de generar exportaciones asistidas.",
    )

    for _, fertilizacion in fertilizaciones.iterrows():

        registro_id = fertilizacion.get("id")

        for columna, etiqueta, recomendacion in [
            ("fecha", "fecha", "Completar la fecha de fertilización."),
            ("producto", "producto/fertilizante", "Completar el producto."),
            ("cantidad", "cantidad/dosis", "Completar una cantidad válida."),
            ("unidad", "unidad", "Completar la unidad aplicada."),
        ]:

            if columna not in fertilizaciones.columns:

                continue

            falta = (
                _numero_vacio_o_cero(fertilizacion.get(columna))
                if columna == "cantidad"
                else _es_vacio(fertilizacion.get(columna))
            )

            if falta:

                _agregar(
                    filas,
                    area,
                    registro_id,
                    "Aviso",
                    columna,
                    f"Fertilización sin {etiqueta}.",
                    recomendacion,
                )

        fertilizacion_id = pd.to_numeric(registro_id, errors="coerce")

        if (
            not pd.isna(fertilizacion_id)
            and int(fertilizacion_id) not in parcelas_por_fertilizacion
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "parcelas",
                "Fertilización sin parcelas asociadas.",
                "Asociar parcelas si procede.",
            )

        cultivo_id = (
            pd.to_numeric(
                fertilizacion.get("cultivo_id"),
                errors="coerce",
            )
            if "cultivo_id" in fertilizaciones.columns
            else pd.NA
        )
        tiene_cultivo_id = not pd.isna(cultivo_id)
        cultivo_texto = (
            fertilizacion.get("cultivo")
            if "cultivo" in fertilizaciones.columns
            else None
        )

        tiene_detalle_cultivo = (
            not pd.isna(fertilizacion_id)
            and int(fertilizacion_id) in cultivos_por_detalle_fertilizacion
        )

        if (
            not tiene_cultivo_id
            and not tiene_detalle_cultivo
            and not _es_vacio(cultivo_texto)
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Info",
                "cultivo",
                "El cultivo de fertilización está como texto pendiente de estructurar.",
                "Asignar cultivo_id desde el módulo Fertilización cuando proceda.",
            )

        elif not tiene_cultivo_id and not tiene_detalle_cultivo:

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "cultivo",
                "Fertilización sin cultivo asociado.",
                "Seleccionar un cultivo estructurado o completar el texto de cultivo.",
            )

    return len(fertilizaciones)


def _revisar_practicas(conn, filas, campana_id):

    area = "Prácticas culturales"
    practicas = _filtrar_campana(
        _leer_tabla(conn, "practicas_culturales"),
        campana_id,
    )

    if not _tabla_existe(conn, "practicas_culturales"):

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "practicas_culturales",
            "No existe la tabla de prácticas culturales.",
            "Revisar la instalación antes de preparar exportación asistida.",
        )
        return 0

    if practicas.empty:

        _agregar(
            filas,
            area,
            None,
            "Info",
            "practicas_culturales",
            "No hay prácticas culturales para la campaña seleccionada.",
            "No hay datos de prácticas que revisar en esta campaña.",
        )
        return 0

    practica_parcelas = _leer_tabla(conn, "practicas_culturales_parcelas")

    if practica_parcelas.empty:

        practica_parcelas = _leer_tabla(conn, "practica_parcelas")

    parcelas_por_practica = _contar_relaciones(
        practica_parcelas,
        "practica_id",
    )
    (
        parcelas_por_detalle_practica,
        cultivos_por_detalle_practica,
    ) = _contar_detalles_multicultivo(
        conn,
        "practicas_culturales_cultivos",
        "practica_id",
    )
    parcelas_por_practica.update(parcelas_por_detalle_practica)

    _agregar(
        filas,
        area,
        None,
        "Info",
        "labor",
        "Las labores/actuaciones pueden requerir catálogo oficial futuro.",
        "Confirmar catálogo antes de generar exportaciones asistidas.",
    )

    for _, practica in practicas.iterrows():

        registro_id = practica.get("id")

        for columna, etiqueta in [
            ("fecha", "fecha"),
            ("labor", "labor"),
        ]:

            if columna in practicas.columns and _es_vacio(practica.get(columna)):

                _agregar(
                    filas,
                    area,
                    registro_id,
                    "Aviso",
                    columna,
                    f"Práctica cultural sin {etiqueta}.",
                    f"Completar {etiqueta}.",
                )

        if (
            "superficie" in practicas.columns
            and _numero_vacio_o_cero(practica.get("superficie"))
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "superficie",
                "Práctica cultural sin superficie válida.",
                "Completar la superficie afectada.",
            )

        practica_id = pd.to_numeric(registro_id, errors="coerce")

        if (
            not pd.isna(practica_id)
            and int(practica_id) not in parcelas_por_practica
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "parcelas",
                "Práctica cultural sin parcelas asociadas.",
                "Asociar parcelas si procede.",
            )

        sin_maquinaria = (
            "maquinaria_id" in practicas.columns
            and _es_vacio(practica.get("maquinaria_id"))
        )
        sin_prestador = (
            "proveedor_id" in practicas.columns
            and _es_vacio(practica.get("proveedor_id"))
        )

        if sin_maquinaria and sin_prestador:

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "maquinaria_prestador",
                "Práctica cultural sin maquinaria ni prestador.",
                "Informar maquinaria o prestador si procede.",
            )

        cultivo_id = (
            pd.to_numeric(
                practica.get("cultivo_id"),
                errors="coerce",
            )
            if "cultivo_id" in practicas.columns
            else pd.NA
        )
        tiene_cultivo_id = not pd.isna(cultivo_id)
        cultivo_texto = (
            practica.get("cultivo")
            if "cultivo" in practicas.columns
            else None
        )

        tiene_detalle_cultivo = (
            not pd.isna(practica_id)
            and int(practica_id) in cultivos_por_detalle_practica
        )

        if (
            not tiene_cultivo_id
            and not tiene_detalle_cultivo
            and not _es_vacio(cultivo_texto)
        ):

            _agregar(
                filas,
                area,
                registro_id,
                "Info",
                "cultivo",
                "El cultivo de la práctica está como texto pendiente de estructurar.",
                "Asignar cultivo_id desde el módulo Prácticas culturales cuando proceda.",
            )

        elif not tiene_cultivo_id and not tiene_detalle_cultivo:

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "cultivo",
                "Práctica cultural sin cultivo asociado.",
                "Seleccionar un cultivo estructurado o completar el texto de cultivo.",
            )

    return len(practicas)


def _revisar_cosecha(conn, filas, campana_id):

    area = "Cosecha"
    cosechas = _filtrar_campana(
        _leer_tabla(conn, "cosecha"),
        campana_id,
    )

    if not _tabla_existe(conn, "cosecha"):

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "cosecha",
            "No existe la tabla de cosecha.",
            "Revisar la instalación antes de preparar exportación asistida.",
        )
        return 0

    if cosechas.empty:

        _agregar(
            filas,
            area,
            None,
            "Info",
            "cosecha",
            "No hay cosechas para la campaña seleccionada.",
            "No hay datos de cosecha que revisar en esta campaña.",
        )
        return 0

    detalles_cosecha = _leer_tabla(conn, "cosecha_cultivos")
    cosechas_con_detalle = set()

    if (
        not detalles_cosecha.empty
        and "cosecha_id" in detalles_cosecha.columns
        and "cultivo_id" in detalles_cosecha.columns
    ):

        detalles_validos = detalles_cosecha[
            pd.to_numeric(
                detalles_cosecha["cultivo_id"],
                errors="coerce",
            ).notna()
        ]
        cosechas_con_detalle = set(
            pd.to_numeric(
                detalles_validos["cosecha_id"],
                errors="coerce",
            ).dropna().astype(int).tolist()
        )

    _agregar(
        filas,
        area,
        None,
        "Info",
        "unidad_destino",
        "Las unidades y destinos de cosecha pueden requerir normalización futura.",
        "Confirmar unidades y destinos oficiales si procede.",
    )

    for _, cosecha in cosechas.iterrows():

        registro_id = cosecha.get("id")

        for columna, etiqueta in [
            ("fecha", "fecha"),
        ]:

            if columna in cosechas.columns and _es_vacio(cosecha.get(columna)):

                _agregar(
                    filas,
                    area,
                    registro_id,
                    "Aviso",
                    columna,
                    f"Cosecha sin {etiqueta}.",
                    f"Completar {etiqueta}.",
                )

        cultivo_id = (
            pd.to_numeric(
                cosecha.get("cultivo_id"),
                errors="coerce",
            )
            if "cultivo_id" in cosechas.columns
            else pd.NA
        )
        tiene_cultivo_id = (
            not pd.isna(cultivo_id)
            or _entero_o_none(registro_id) in cosechas_con_detalle
        )
        cultivo_texto = (
            cosecha.get("cultivo")
            if "cultivo" in cosechas.columns
            else None
        )

        if not tiene_cultivo_id and not _es_vacio(cultivo_texto):

            _agregar(
                filas,
                area,
                registro_id,
                "Info",
                "cultivo",
                "El cultivo de la cosecha está como texto pendiente de estructurar.",
                "Asignar cultivo_id desde el módulo Cosecha cuando proceda.",
            )

        elif not tiene_cultivo_id:

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "cultivo",
                "Cosecha sin cultivo asociado.",
                "Seleccionar un cultivo estructurado o completar el texto de cultivo.",
            )

        cantidad_cosecha = (
            cosecha.get("cantidad")
            if "cantidad" in cosechas.columns
            else cosecha.get("kg")
        )

        if _numero_vacio_o_cero(cantidad_cosecha):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "cantidad",
                "Cosecha sin cantidad válida.",
                "Completar la cantidad cosechada.",
            )

        if "destino" in cosechas.columns and _es_vacio(cosecha.get("destino")):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "destino",
                "Cosecha sin destino informado.",
                "Completar destino si procede.",
            )

    return len(cosechas)


def _revisar_maquinaria(conn, filas):

    area = "Maquinaria"
    revisados = 0
    maquinaria = _leer_tabla(conn, "maquinaria")
    equipos = _leer_tabla(conn, "equipos_aplicacion")

    if not _tabla_existe(conn, "maquinaria") and not _tabla_existe(
        conn,
        "equipos_aplicacion",
    ):

        _agregar(
            filas,
            area,
            None,
            "Aviso",
            "maquinaria",
            "No existen tablas de maquinaria ni equipos de aplicación.",
            "Revisar la instalación antes de preparar exportación asistida.",
        )
        return 0

    if maquinaria.empty and equipos.empty:

        _agregar(
            filas,
            area,
            None,
            "Info",
            "maquinaria",
            "No hay maquinaria ni equipos de aplicación registrados.",
            "No hay datos de maquinaria que revisar.",
        )
        return 0

    for _, item in maquinaria.iterrows():

        revisados += 1
        registro_id = f"MAQ-{item.get('id')}"

        if "numero_roma" in maquinaria.columns and _es_vacio(item.get("numero_roma")):

            _agregar(
                filas,
                area,
                registro_id,
                "Aviso",
                "numero_roma",
                "Maquinaria general sin número ROMA.",
                "Completar número ROMA si procede.",
            )

        for columna in ["marca", "modelo"]:

            if columna in maquinaria.columns and _es_vacio(item.get(columna)):

                _agregar(
                    filas,
                    area,
                    registro_id,
                    "Aviso",
                    columna,
                    f"Maquinaria general sin {columna}.",
                    f"Completar {columna} si procede.",
                )

    for _, item in equipos.iterrows():

        revisados += 1
        registro_id = f"EQ-{item.get('id')}"

        for columna in ["marca", "modelo"]:

            if columna in equipos.columns and _es_vacio(item.get(columna)):

                _agregar(
                    filas,
                    area,
                    registro_id,
                    "Aviso",
                    columna,
                    f"Equipo de aplicación sin {columna}.",
                    f"Completar {columna} si procede.",
                )

    return revisados


def _contar_documentos(conn, tabla, tipo=None):

    datos = _leer_tabla(conn, tabla)

    if datos.empty:

        return 0

    if tipo is not None and "tipo_documento" in datos.columns:

        datos = datos[datos["tipo_documento"].fillna("").astype(str) == tipo]

    return len(datos)


def _revisar_documentos(conn, filas):

    area = "Documentos"
    recetas = _contar_documentos(conn, "tratamientos_documentos", "receta")
    facturas = _contar_documentos(
        conn,
        "movimientos_economicos_documentos",
        "factura",
    )

    if not _tabla_existe(conn, "tratamientos_documentos"):

        _agregar(
            filas,
            area,
            None,
            "Info",
            "tratamientos_documentos",
            "No existe tabla de documentos de tratamientos.",
            "No bloquea la revisión SIEX.",
        )

    else:

        _agregar(
            filas,
            area,
            None,
            "Info",
            "recetas_pdf",
            f"Hay {recetas} recetas PDF asociadas a tratamientos.",
            "Solo se inventarían como anexos en un futuro paquete ZIP asistido.",
        )

    if not _tabla_existe(conn, "movimientos_economicos_documentos"):

        _agregar(
            filas,
            area,
            None,
            "Info",
            "movimientos_economicos_documentos",
            "No existe tabla de documentos contables.",
            "No bloquea la revisión SIEX.",
        )

    else:

        _agregar(
            filas,
            area,
            None,
            "Info",
            "facturas_pdf",
            f"Hay {facturas} facturas PDF asociadas a movimientos contables.",
            "No bloquea la revisión SIEX.",
        )

    return recetas + facturas


def _generar_revision(conn, campana_id):

    filas = []
    registros_revisados = 0

    registros_revisados += _revisar_explotacion(conn, filas)
    registros_revisados += _revisar_parcelas(conn, filas)
    registros_revisados += _revisar_cultivos(conn, filas)
    registros_revisados += _revisar_tratamientos(conn, filas, campana_id)
    registros_revisados += _revisar_fertilizacion(conn, filas, campana_id)
    registros_revisados += _revisar_practicas(conn, filas, campana_id)
    registros_revisados += _revisar_cosecha(conn, filas, campana_id)
    registros_revisados += _revisar_maquinaria(conn, filas)
    registros_revisados += _revisar_documentos(conn, filas)

    dataframe = pd.DataFrame(filas, columns=COLUMNAS_REVISION)

    return dataframe, registros_revisados


def _filtrar_revision(dataframe):

    if dataframe.empty:

        return dataframe

    filtros = st.columns(3)

    with filtros[0]:

        gravedades = ["Todas"] + sorted(dataframe["gravedad"].unique())
        gravedad = st.selectbox(
            "Gravedad",
            gravedades,
            key="revision_siex_filtro_gravedad",
        )

    with filtros[1]:

        areas = ["Todas"] + sorted(dataframe["area"].unique())
        area = st.selectbox(
            "Área",
            areas,
            key="revision_siex_filtro_area",
        )

    with filtros[2]:

        bloqueos = ["Todas"] + sorted(dataframe["bloquea_exportacion"].unique())
        bloqueo = st.selectbox(
            "Bloquea exportación",
            bloqueos,
            key="revision_siex_filtro_bloqueo",
        )

    filtrado = dataframe.copy()

    if gravedad != "Todas":

        filtrado = filtrado[filtrado["gravedad"] == gravedad]

    if area != "Todas":

        filtrado = filtrado[filtrado["area"] == area]

    if bloqueo != "Todas":

        filtrado = filtrado[filtrado["bloquea_exportacion"] == bloqueo]

    return filtrado


def _mostrar_metricas(dataframe, registros_revisados):

    total_avisos = 0
    total_info = 0
    total_areas = len(AREAS_REVISION)

    if not dataframe.empty:

        total_avisos = int((dataframe["gravedad"] == "Aviso").sum())
        total_info = int((dataframe["gravedad"] == "Info").sum())

    columnas = st.columns(4)
    columnas[0].metric("Avisos", total_avisos)
    columnas[1].metric("Información", total_info)
    columnas[2].metric("Áreas revisadas", total_areas)
    columnas[3].metric("Registros revisados", registros_revisados)


def _mostrar_exportacion_excel(campana_id, revision):

    st.subheader("Exportar Excel asistido")
    st.warning(AVISO_NO_OFICIAL)

    try:

        datos_excel, nombre_archivo = generar_excel_asistido_siex(
            campana_id=campana_id,
            revision=revision,
        )

    except Exception as exc:

        st.error(f"No se pudo preparar el Excel asistido: {exc}")
        return

    st.download_button(
        "Exportar Excel asistido",
        data=datos_excel,
        file_name=nombre_archivo,
        mime=MIME_XLSX,
        key=f"revision_siex_exportar_excel_{campana_id or 'general'}",
    )
    st.caption(
        "No genera ZIP, no adjunta PDFs y no envía datos a SIEX/CUE."
    )


def render(CAMPANA=None):

    st.title("Revisión SIEX")

    st.info(
        "Esta revisión no envía datos a SIEX/CUE. Solo ayuda a preparar y "
        "revisar la información para una futura exportación asistida. La "
        "carga oficial deberá realizarla el agricultor, asesor o entidad "
        "autorizada mediante los canales oficiales correspondientes."
    )

    conn = conectar()

    try:

        campana_id = _seleccionar_campana(conn, CAMPANA)
        _mostrar_filtro_cultivo(conn)
        revision, registros_revisados = _generar_revision(conn, campana_id)

    finally:

        conn.close()

    _mostrar_metricas(revision, registros_revisados)
    _mostrar_exportacion_excel(campana_id, revision)

    st.subheader("Resultado de la revisión")

    if revision.empty:

        st.success("No se han detectado avisos en esta revisión.")
        return

    revision_filtrada = _filtrar_revision(revision)

    st.dataframe(
        preparar_dataframe_visual(
            revision_filtrada,
            ocultar_tecnicas=True,
        ),
        hide_index=True,
        use_container_width=True,
    )
