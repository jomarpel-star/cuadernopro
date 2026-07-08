from datetime import datetime
import re

import streamlit as st

from core.config import APP_DESCRIPTION, APP_NAME, APP_SUBTITLE
from core.db import leer
from core.fechas import formatear_fecha_es
from core.paths import BACKUPS_DIR, EXPORTS_DIR


def _leer_seguro(sql, params=()):

    try:

        return leer(sql, params or ())

    except Exception:

        return None


def _identificador_seguro(nombre):

    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", nombre or ""))


def tabla_existe(nombre_tabla):

    if not _identificador_seguro(nombre_tabla):

        return False

    datos = _leer_seguro(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (nombre_tabla,)
    )
    return datos is not None and not datos.empty


def contar_registros(nombre_tabla, where=None, params=None):

    if not tabla_existe(nombre_tabla):

        return 0

    sql = f"SELECT COUNT(*) total FROM {nombre_tabla}"

    if where:

        sql += f" WHERE {where}"

    datos = _leer_seguro(sql, params or ())

    if datos is None or datos.empty:

        return 0

    return int(datos.iloc[0]["total"] or 0)


def _primera_fila(sql, params=()):

    datos = _leer_seguro(sql, params)

    if datos is None or datos.empty:

        return None

    return datos.iloc[0].to_dict()


def obtener_campana_activa():

    if not tabla_existe("campanas"):

        return None

    activa = _primera_fila(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin,activa
        FROM campanas
        WHERE activa=1
        ORDER BY id DESC
        LIMIT 1
        """
    )

    if activa:

        return activa

    return _primera_fila(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin,activa
        FROM campanas
        ORDER BY fecha_inicio DESC,id DESC
        LIMIT 1
        """
    )


def _tabla_fertilizacion():

    if tabla_existe("fertilizaciones"):

        return "fertilizaciones"

    if tabla_existe("fertilizacion"):

        return "fertilizacion"

    return None


def _explotacion_configurada():

    if not tabla_existe("explotacion"):

        return False

    return contar_registros(
        "explotacion",
        "TRIM(COALESCE(titular,'')) <> '' "
        "AND TRIM(COALESCE(nif,'')) <> ''"
    ) > 0


def _suma_movimientos(campana_id, tipo):

    if campana_id is None or not tabla_existe("movimientos_economicos"):

        return 0.0

    datos = _leer_seguro(
        """
        SELECT COALESCE(SUM(total),0) total
        FROM movimientos_economicos
        WHERE campana_id=?
        AND LOWER(TRIM(COALESCE(tipo,'')))=?
        """,
        (int(campana_id), tipo)
    )

    if datos is None or datos.empty:

        return 0.0

    return float(datos.iloc[0]["total"] or 0)


def _importe(valor):

    return f"{float(valor or 0):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def obtener_resumen_campana(campana_id):

    fertilizacion = _tabla_fertilizacion()
    filtros_campana = "campana_id=?" if campana_id is not None else None
    params_campana = (int(campana_id),) if campana_id is not None else ()

    resumen = {
        "campanas": contar_registros("campanas"),
        "explotacion_configurada": _explotacion_configurada(),
        "personas": contar_registros("personas"),
        "equipos": contar_registros("equipos_aplicacion"),
        "parcelas": contar_registros("parcelas"),
        "cultivos": contar_registros("cultivos"),
        "productos_fito": contar_registros("productos_fito"),
        "tratamientos": contar_registros("tratamientos", filtros_campana, params_campana),
        "analisis_fitosanitarios": contar_registros(
            "analisis_fitosanitarios",
            filtros_campana,
            params_campana
        ),
        "fertilizacion": (
            contar_registros(fertilizacion, filtros_campana, params_campana)
            if fertilizacion
            else 0
        ),
        "practicas": contar_registros(
            "practicas_culturales",
            filtros_campana,
            params_campana
        ),
        "cosecha": contar_registros("cosecha", filtros_campana, params_campana),
        "movimientos": contar_registros(
            "movimientos_economicos",
            filtros_campana,
            params_campana
        ),
        "ingresos": _suma_movimientos(campana_id, "ingreso"),
        "gastos": _suma_movimientos(campana_id, "gasto"),
    }
    resumen["resultado"] = resumen["ingresos"] - resumen["gastos"]
    return resumen


def _pdf_disponible():

    exports = EXPORTS_DIR

    if not exports.exists():

        return None

    pdfs = list(exports.glob("*.pdf"))

    if not pdfs:

        return None

    return max(pdfs, key=lambda ruta: ruta.stat().st_mtime)


def _ultimo_backup():

    backups = BACKUPS_DIR

    if not backups.exists():

        return None

    archivos = [
        ruta
        for patron in ("*.db", "*.zip")
        for ruta in backups.glob(patron)
        if ruta.is_file()
    ]

    if not archivos:

        return None

    return max(archivos, key=lambda ruta: ruta.stat().st_mtime)


def _fecha_archivo(ruta):

    return datetime.fromtimestamp(ruta.stat().st_mtime).strftime("%d/%m/%Y %H:%M")


def _estado(ok, severidad="warning"):

    if ok:

        return "✅"

    if severidad == "error":

        return "❌"

    return "⚠️"


def _configuracion_inicial_pendiente():

    try:

        from modules.asistente_inicio import app_necesita_configuracion_inicial

        return app_necesita_configuracion_inicial()

    except Exception:

        return False


def _mostrar_campana(campana):

    st.subheader("Campaña activa")

    if not campana:

        st.warning("Todavía no hay una campaña creada. Empieza por crear una campaña.")
        return

    st.success(f"Campaña activa: {campana.get('nombre')}")
    st.caption(
        "Periodo: "
        f"{formatear_fecha_es(campana.get('fecha_inicio'))} - "
        f"{formatear_fecha_es(campana.get('fecha_fin'))}"
    )


def _mostrar_metricas(resumen):

    st.subheader("Configuración")
    cols = st.columns(4)
    cols[0].metric("Campañas", resumen["campanas"])
    cols[1].metric(
        "Explotación",
        "Sí" if resumen["explotacion_configurada"] else "No"
    )
    cols[2].metric("Personas", resumen["personas"])
    cols[3].metric("Equipos", resumen["equipos"])

    st.subheader("Datos agrícolas")
    cols = st.columns(8)
    cols[0].metric("Parcelas", resumen["parcelas"])
    cols[1].metric("Cultivos", resumen["cultivos"])
    cols[2].metric("Productos fito", resumen["productos_fito"])
    cols[3].metric("Tratamientos", resumen["tratamientos"])
    cols[4].metric(
        "Análisis fitosanitarios",
        resumen["analisis_fitosanitarios"]
    )
    cols[5].metric("Fertilización", resumen["fertilizacion"])
    cols[6].metric("Prácticas", resumen["practicas"])
    cols[7].metric("Cosecha", resumen["cosecha"])

    st.subheader("Economía")
    cols = st.columns(4)
    cols[0].metric("Movimientos", resumen["movimientos"])
    cols[1].metric("Ingresos", _importe(resumen["ingresos"]))
    cols[2].metric("Gastos", _importe(resumen["gastos"]))
    cols[3].metric("Resultado", _importe(resumen["resultado"]))


def _mostrar_checklist(campana, resumen):

    st.subheader("Estado del cuaderno")

    pdf = _pdf_disponible()
    backup = _ultimo_backup()
    filas = [
        ("Campaña activa", bool(campana), "error"),
        ("Datos de explotación", resumen["explotacion_configurada"], "error"),
        ("Personas registradas", resumen["personas"] > 0, "error"),
        ("Parcelas registradas", resumen["parcelas"] > 0, "error"),
        ("Cultivos registrados", resumen["cultivos"] > 0, "error"),
        ("Productos fitosanitarios", resumen["productos_fito"] > 0, "warning"),
        ("Tratamientos fitosanitarios", resumen["tratamientos"] > 0, "warning"),
        ("Fertilización", resumen["fertilizacion"] > 0, "warning"),
        ("Cosecha", resumen["cosecha"] > 0, "warning"),
        ("Contabilidad", resumen["movimientos"] > 0, "warning"),
        ("PDF del cuaderno disponible", pdf is not None, "warning"),
        ("Backup detectado", backup is not None, "warning"),
    ]
    columnas = st.columns(2)

    for indice, (texto, ok, severidad) in enumerate(filas):

        with columnas[indice % 2]:

            st.write(f"{_estado(ok, severidad)} {texto}")

    if pdf:

        st.caption(f"Último PDF detectado: {pdf.name}")


def _mostrar_avisos(campana, resumen):

    avisos = []

    if not campana:

        avisos.append("Todavía no hay una campaña creada. Empieza por crear una campaña.")

    if not resumen["explotacion_configurada"]:

        avisos.append("Faltan los datos de la explotación.")

    if resumen["parcelas"] == 0:

        avisos.append("Todavía no hay parcelas registradas.")

    if resumen["cultivos"] == 0:

        avisos.append("Faltan cultivos asociados a parcelas.")

    if resumen["productos_fito"] == 0:

        avisos.append("Puedes registrar productos fitosanitarios antes de añadir tratamientos.")

    if campana and resumen["tratamientos"] == 0:

        avisos.append("No hay tratamientos fitosanitarios registrados para la campaña activa.")

    if not avisos:

        st.success("Los datos principales del cuaderno están en buen estado.")
        return

    for aviso in avisos:

        st.warning(aviso)


def _ir_a(seccion):

    st.session_state["menu_principal_pendiente"] = seccion
    st.rerun()


def _mostrar_accesos():

    st.subheader("Accesos rápidos")

    accesos = [
        ("Campañas", "Campañas"),
        ("Explotación", "Explotación"),
        ("Personas", "Explotación"),
        ("Parcelas", "Parcelas"),
        ("Cultivos", "Cultivos"),
        ("Productos fito", "Productos Fito"),
        ("Tratamientos", "Tratamientos"),
        ("Fertilización", "Fertilización"),
        ("Prácticas culturales", "Prácticas culturales"),
        ("Cosecha", "Cosecha"),
        ("Contabilidad", "Contabilidad"),
        ("Cuaderno oficial / PDF", "Cuaderno oficial"),
        ("Backup / Restauración", "Backup / Restauración"),
    ]

    for fila_inicio in range(0, len(accesos), 4):

        columnas = st.columns(4)

        for columna, (etiqueta, seccion) in zip(columnas, accesos[fila_inicio:fila_inicio + 4]):

            with columna:

                if st.button(etiqueta, use_container_width=True, key=f"inicio_ir_{etiqueta}"):

                    _ir_a(seccion)


def _mostrar_backups():

    st.subheader("Backups")

    ultimo = _ultimo_backup()

    if not ultimo:

        st.info("No se han detectado backups en la carpeta backups/.")
        return

    st.info(
        "Última copia detectada: "
        f"{ultimo.name} · {_fecha_archivo(ultimo)}"
    )


def render():

    campana = obtener_campana_activa()
    campana_id = int(campana["id"]) if campana else None
    resumen = obtener_resumen_campana(campana_id)

    st.title(f"🌾 {APP_NAME}")
    st.caption(APP_SUBTITLE)
    st.write("Panel de estado de tu cuaderno de explotación.")
    st.caption(APP_DESCRIPTION)

    if _configuracion_inicial_pendiente():

        st.info(
            "Si estás empezando, abre Inicio / Configuración en el menú lateral "
            "para completar los datos mínimos."
        )

    _mostrar_campana(campana)

    st.divider()
    _mostrar_metricas(resumen)

    st.divider()
    _mostrar_checklist(campana, resumen)

    st.divider()
    st.subheader("Avisos")
    _mostrar_avisos(campana, resumen)

    st.divider()
    _mostrar_accesos()

    st.divider()
    _mostrar_backups()
