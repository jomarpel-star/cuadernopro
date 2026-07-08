from datetime import datetime
import shutil
import sqlite3

import pandas as pd
import streamlit as st

from core.db import DB, conectar
from core.paths import BACKUPS_DIR, asegurar_directorio
from core.ui_tablas import preparar_dataframe_visual


def hacer_backup_antes_de_borrar():

    asegurar_directorio(BACKUPS_DIR)

    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_backup = BACKUPS_DIR / f"cuadernopro_antes_borrado_{marca_tiempo}.db"

    shutil.copy2(DB, ruta_backup)

    return str(ruta_backup)



def tabla_y_columna_existen(conn, tabla, columna=None):

    tabla_encontrada = conn.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (tabla,)
    ).fetchone()

    if not tabla_encontrada:

        return False

    if columna is None:

        return True

    columnas = {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }

    return columna in columnas



def borrar_registros_seguro(
    tabla,
    id_columna,
    dataframe,
    titulo,
    tablas_hijas=None,
    bloqueos=None,
    campo_descripcion=None,
    advertencia=None,
    key=None,
    post_borrar=None
):

    clave = key or tabla
    clave_mensaje = f"resultado_borrado_{clave}"

    if clave_mensaje in st.session_state:

        st.success(st.session_state.pop(clave_mensaje))

    if dataframe is None or dataframe.empty or id_columna not in dataframe:

        return

    tablas_hijas = tablas_hijas or []
    bloqueos = bloqueos or []
    filas_visibles = dataframe.drop_duplicates(subset=[id_columna]).copy()
    ids_disponibles = (
        pd.to_numeric(filas_visibles[id_columna], errors="coerce")
        .dropna()
        .astype(int)
        .tolist()
    )

    if not ids_disponibles:

        return

    descripciones = {}

    if campo_descripcion and campo_descripcion in filas_visibles:

        for _, fila in filas_visibles.iterrows():

            valor_id = pd.to_numeric(fila[id_columna], errors="coerce")

            if not pd.isna(valor_id):

                descripcion = fila[campo_descripcion]
                descripcion = "" if pd.isna(descripcion) else str(descripcion)
                descripciones[int(valor_id)] = descripcion

    with st.expander(f"⚠️ Eliminar registros: {titulo}"):

        st.warning(
            "Esta acción borra definitivamente registros de la base de "
            "datos. Se hará una copia automática antes de borrar."
        )

        if advertencia:

            st.info(advertencia)

        ids_seleccionados = st.multiselect(
            "IDs que se eliminarán",
            ids_disponibles,
            format_func=lambda valor: (
                f"{valor} — {descripciones[valor]}"
                if descripciones.get(valor)
                else str(valor)
            ),
            key=f"eliminar_ids_{clave}"
        )

        if ids_seleccionados:

            seleccion = filas_visibles[
                filas_visibles[id_columna].isin(ids_seleccionados)
            ]
            st.dataframe(
                preparar_dataframe_visual(
                    seleccion,
                    mostrar_id=True
                ),
                hide_index=True,
                use_container_width=True
            )

        confirmar = st.checkbox(
            "Confirmo que quiero eliminar estos registros",
            key=f"eliminar_confirmar_{clave}"
        )
        texto_confirmacion = st.text_input(
            "Escribe BORRAR para confirmar",
            key=f"eliminar_texto_{clave}"
        )

        if st.button(
            "Eliminar registros seleccionados",
            key=f"eliminar_boton_{clave}"
        ):

            if not ids_seleccionados:

                st.warning("Selecciona al menos un registro")

                return

            if not confirmar:

                st.warning("Marca la casilla de confirmación")

                return

            if texto_confirmacion != "BORRAR":

                st.warning("Escribe BORRAR exactamente para confirmar")

                return

            conn = conectar()

            try:

                registros_bloqueados = []

                for registro_id in ids_seleccionados:

                    for bloqueo in bloqueos:

                        tabla_bloqueo = bloqueo[0]
                        columna_bloqueo = bloqueo[1]
                        mensaje_bloqueo = bloqueo[2]

                        if not tabla_y_columna_existen(
                            conn,
                            tabla_bloqueo,
                            columna_bloqueo
                        ):

                            continue

                        usado = conn.execute(
                            f'SELECT 1 FROM "{tabla_bloqueo}" '
                            f'WHERE "{columna_bloqueo}"=? LIMIT 1',
                            (int(registro_id),)
                        ).fetchone()

                        if usado:

                            registros_bloqueados.append(
                                f"ID {registro_id}: {mensaje_bloqueo}"
                            )

                if registros_bloqueados:

                    for mensaje in dict.fromkeys(registros_bloqueados):

                        st.error(mensaje)

                    return

                ruta_backup = hacer_backup_antes_de_borrar()

                for tabla_hija, columna_hija in tablas_hijas:

                    if not tabla_y_columna_existen(
                        conn,
                        tabla_hija,
                        columna_hija
                    ):

                        continue

                    marcadores = ",".join("?" for _ in ids_seleccionados)
                    conn.execute(
                        f'DELETE FROM "{tabla_hija}" '
                        f'WHERE "{columna_hija}" IN ({marcadores})',
                        tuple(int(valor) for valor in ids_seleccionados)
                    )

                marcadores = ",".join("?" for _ in ids_seleccionados)
                conn.execute(
                    f'DELETE FROM "{tabla}" '
                    f'WHERE "{id_columna}" IN ({marcadores})',
                    tuple(int(valor) for valor in ids_seleccionados)
                )
                conn.commit()

            except (sqlite3.Error, OSError) as error:

                conn.rollback()
                st.error(f"No se pudo completar el borrado: {error}")

                return

            finally:

                conn.close()

            if post_borrar:

                try:

                    post_borrar([
                        int(valor)
                        for valor in ids_seleccionados
                    ])

                except OSError as error:

                    st.warning(
                        "Los registros se han eliminado, pero no se pudieron "
                        f"borrar todos los archivos asociados: {error}"
                    )

            st.session_state[clave_mensaje] = (
                "Registros eliminados. Copia creada: "
                f"{ruta_backup}"
            )
            for clave_widget in (
                f"eliminar_ids_{clave}",
                f"eliminar_confirmar_{clave}",
                f"eliminar_texto_{clave}",
            ):

                st.session_state.pop(clave_widget, None)

            st.rerun()
