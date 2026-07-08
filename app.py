# =====================================================
# 🚜 CuadernoPro
# Cuaderno agrícola personal
# Streamlit + SQLite
# =====================================================

import streamlit as st
import pandas as pd
import sqlite3
import os
import shutil
import zipfile
import io

from datetime import datetime, date
from openpyxl.styles import Font
from pathlib import Path

from core.config import APP_DESCRIPTION, APP_NAME, APP_SUBTITLE
from core.version import APP_STAGE, version_text


# =====================================================
# CONFIGURACIÓN
# =====================================================


def _page_icon():
    icono_png = (
        Path(__file__).resolve().parent
        / "assets"
        / "branding"
        / "cuadernopro.png"
    )

    if icono_png.is_file():
        return str(icono_png)

    return "🚜"


st.set_page_config(
    page_title=f"{APP_NAME} - {APP_SUBTITLE}",
    page_icon=_page_icon(),
    layout="wide"
)


from core.borrado import (
    borrar_registros_seguro,
    tabla_y_columna_existen,
)
from core.db import (
    DB,
    conectar,
    crear_tablas,
    ejecutar,
    leer,
)
from core.fechas import (
    hoy,
    obtener_campana_por_intervalo,
    validar_fecha_en_campana,
    validar_intervalo_en_campana,
)
from core.filtros import mostrar_filtros_dataframe
from modules import (
    asistente_inicio,
    backup_page,
    campanas,
    catalogos_siex,
    contabilidad,
    cuaderno_oficial,
    cultivos,
    explotacion,
    cosecha,
    fertilizacion,
    informes,
    inicio,
    mapas,
    maquinaria,
    parcelas,
    practicas_culturales,
    productos_fito,
    revision_siex,
    terceros,
    tratamientos,
)


crear_tablas()
CONFIGURACION_INICIAL_PENDIENTE = (
    asistente_inicio.app_necesita_configuracion_inicial()
)


# =====================================================
# CAMPAÑA ACTIVA
# =====================================================


CAMPANA = asistente_inicio.obtener_campana_actual_si_existe()


# =====================================================
# MENÚ
# =====================================================


st.sidebar.title(f"🚜 {version_text()}")
st.sidebar.caption(f"{APP_SUBTITLE} · {APP_STAGE}")

SECCIONES_MENU = [
    {
        "title": "Inicio / Configuración",
        "items": [
            "Inicio",
            "Inicio / Configuración",
        ],
    },
    {
        "title": "Cuaderno de Campo",
        "items": [
            "Explotación",
            "Campañas",
            "Parcelas",
            "Cultivos",
            "Tratamientos",
            "Fertilización",
            "Prácticas culturales",
            "Cosecha",
            "Cuaderno oficial",
        ],
    },
    {
        "title": "Sección Contable",
        "items": [
            "Contabilidad",
        ],
    },
    {
        "title": "Datos",
        "items": [
            "Productos Fito",
            "Maquinaria",
            "Clientes / Proveedores",
        ],
    },
    {
        "title": "Utilidades",
        "items": [
            "Mapas",
            "Informes",
        ],
    },
    {
        "title": "SIEX",
        "items": [
            "Revisión SIEX",
            "Catálogos SIEX",
        ],
    },
    {
        "title": "Backups",
        "items": [
            "Backup / Restauración",
        ],
    },
]

ETIQUETAS_MENU = {
    "Inicio / Configuración": "Configuración",
    "Prácticas culturales": "Prácticas Culturales",
    "Cosecha": "Cosechas",
    "Cuaderno oficial": "Cuaderno Oficial",
    "Revisión SIEX": "Revisión",
    "Catálogos SIEX": "Importar Catálogos",
    "Backup / Restauración": "Copias de Seguridad",
}


def _opciones_menu(secciones):

    return [
        item
        for seccion in secciones
        for item in seccion["items"]
    ]


opciones_menu = _opciones_menu(SECCIONES_MENU)


def _etiqueta_menu(opcion):

    return ETIQUETAS_MENU.get(opcion, opcion)


def _clave_radio_menu(indice):

    return f"menu_principal_seccion_{indice}"


def _sincronizar_radios_menu():

    menu_actual = st.session_state.get("menu_principal")

    for indice, seccion in enumerate(SECCIONES_MENU):

        clave = _clave_radio_menu(indice)
        items = seccion["items"]
        st.session_state[clave] = menu_actual if menu_actual in items else None


def _actualizar_menu_desde_radio(clave):

    seleccion = st.session_state.get(clave)

    if seleccion:

        st.session_state["menu_principal"] = seleccion
        _sincronizar_radios_menu()


def _render_menu_lateral():

    st.sidebar.markdown(
        """
        <style>
        section[data-testid="stSidebar"] .menu-section-title {
            font-size: 0.75rem;
            font-weight: 700;
            margin: 1rem 0 0.2rem;
            text-transform: uppercase;
        }

        section[data-testid="stSidebar"] div[data-testid="stRadio"] {
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    for indice, seccion in enumerate(SECCIONES_MENU):

        st.sidebar.markdown(
            f"<div class='menu-section-title'>{seccion['title']}</div>",
            unsafe_allow_html=True,
        )
        st.sidebar.radio(
            seccion["title"],
            seccion["items"],
            index=None,
            format_func=_etiqueta_menu,
            key=_clave_radio_menu(indice),
            label_visibility="collapsed",
            on_change=_actualizar_menu_desde_radio,
            args=(_clave_radio_menu(indice),),
        )

if CONFIGURACION_INICIAL_PENDIENTE:

    st.sidebar.warning(
        f"{APP_NAME} aún no está configurada. Completa los datos iniciales "
        "para empezar."
    )


def _menu_por_defecto():

    if CONFIGURACION_INICIAL_PENDIENTE:

        return "Inicio / Configuración"

    return opciones_menu[0]


if "menu_principal_pendiente" in st.session_state:

    destino = st.session_state.pop("menu_principal_pendiente")

    if destino in opciones_menu:

        st.session_state["menu_principal"] = destino

    else:

        st.session_state["menu_principal"] = _menu_por_defecto()

if st.session_state.get("menu_principal") not in opciones_menu:

    st.session_state["menu_principal"] = _menu_por_defecto()

_sincronizar_radios_menu()
_render_menu_lateral()

menu = st.session_state["menu_principal"]


RESET_SECCIONES_MODULOS = {
    "Explotación": ("explotacion_seccion", "📋 Resumen"),
    "Parcelas": ("parcelas_seccion", "📋 Listado"),
    "Cultivos": ("cultivos_seccion", "📋 Listado"),
    "Tratamientos": ("tratamientos_seccion", "📋 Listado"),
    "Prácticas culturales": ("practicas_seccion", "📋 Listado"),
    "Fertilización": ("fertilizacion_seccion", "📋 Listado"),
    "Cosecha": ("cosecha_seccion", "📋 Listado"),
    "Contabilidad": ("contabilidad_seccion", "📊 Resumen"),
    "Productos Fito": ("productos_fito_seccion", "📋 Listado"),
    "Maquinaria": ("maquinaria_seccion", "📋 Listado"),
}


def _resetear_seccion_modulo(menu_actual):

    configuracion = RESET_SECCIONES_MODULOS.get(menu_actual)

    if not configuracion:

        return

    clave_seccion, valor_inicial = configuracion
    st.session_state[clave_seccion] = valor_inicial


menu_anterior = st.session_state.get("_ultimo_menu_principal")

if menu != menu_anterior:

    st.session_state["_ultimo_menu_principal"] = menu
    _resetear_seccion_modulo(menu)


def _requiere_campana():

    if CAMPANA is not None:

        return False

    st.warning(
        "Activa una campaña para usar esta sección."
    )
    asistente_inicio.render()
    return True

# =====================================================
# INICIO
# =====================================================

if menu == "Inicio / Configuración":

    asistente_inicio.render()


elif menu == "Inicio":

    inicio.render()



# =====================================================
# EXPLOTACIÓN
# =====================================================

elif menu == "Explotación":

    explotacion.render()


# =====================================================
# CAMPAÑAS
# =====================================================

elif menu == "Campañas":

    campanas.render()



# =====================================================
# PARCELAS SIGPAC
# =====================================================


elif menu == "Parcelas":

    parcelas.render()


# =====================================================
# CULTIVOS
# =====================================================


elif menu == "Cultivos":

    cultivos.render()



# =====================================================
# MAQUINARIA
# =====================================================


elif menu == "Maquinaria":

    maquinaria.render()


# =====================================================
# PRODUCTOS FITOSANITARIOS
# =====================================================


elif menu == "Productos Fito":

    productos_fito.render()


# =====================================================
# CLIENTES / PROVEEDORES
# =====================================================


elif menu == "Clientes / Proveedores":

    terceros.render()


# =====================================================
# TRATAMIENTOS
# =====================================================

elif menu == "Tratamientos":

    if not _requiere_campana():

        tratamientos.render(CAMPANA)

# =====================================================
# FERTILIZACIÓN
# =====================================================

elif menu == "Fertilización":

    if not _requiere_campana():

        fertilizacion.render(CAMPANA)

# =====================================================
# PRÁCTICAS CULTURALES
# =====================================================

elif menu == "Prácticas culturales":

    if not _requiere_campana():

        practicas_culturales.render(CAMPANA)

# =====================================================
# CONTABILIDAD
# =====================================================

elif menu == "Contabilidad":

    if not _requiere_campana():

        contabilidad.render(CAMPANA)

# =====================================================
# COSECHA
# =====================================================

elif menu == "Cosecha":

    if not _requiere_campana():

        cosecha.render(CAMPANA)

# =====================================================
# INFORMES
# =====================================================

elif menu == "Informes":

    if not _requiere_campana():

        informes.render(CAMPANA)

# =====================================================
# REVISIÓN SIEX
# =====================================================

elif menu == "Revisión SIEX":

    revision_siex.render(CAMPANA)

# =====================================================
# CATÁLOGOS SIEX
# =====================================================

elif menu == "Catálogos SIEX":

    catalogos_siex.render()

# =====================================================
# CUADERNO OFICIAL
# =====================================================

elif menu == "Cuaderno oficial":

    if not _requiere_campana():

        cuaderno_oficial.render(CAMPANA)

# =====================================================
# BACKUP
# =====================================================

elif menu == "Backup / Restauración":

    backup_page.render()
# =====================================================
# MAPAS SIGPAC
# =====================================================

elif menu == "Mapas":

    mapas.render()
