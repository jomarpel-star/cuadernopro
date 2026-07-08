import pandas as pd
import streamlit as st

from core.borrado import borrar_registros_seguro
from core.db import conectar, ejecutar, leer
from core.filtros import mostrar_filtros_dataframe
from core.ui_tablas import (
    mapear_columnas_visuales_a_tecnicas,
    preparar_column_config_visual,
    preparar_dataframe_visual,
)


def _identificador_sql(nombre):

    return '"' + nombre.replace('"', '""') + '"'


def _columnas_productos_fito():

    datos = leer("PRAGMA table_info(productos_fito)")

    if datos.empty:

        return set()

    return set(datos["name"].tolist())


def _columna_registro_producto(columnas=None):

    columnas = columnas or _columnas_productos_fito()

    if "numero_registro" in columnas:

        return "numero_registro"

    if "registro" in columnas:

        return "registro"

    return None


def _primer_valor(datos, *claves):

    for clave in claves:

        valor = datos.get(clave)

        if valor is not None and not pd.isna(valor):

            texto = str(valor).strip()

            if texto:

                return texto

    return ""


def _bool_producto(valor):

    if valor is None or pd.isna(valor):

        return False

    if isinstance(valor, str):

        return valor.strip().casefold() in {"1", "true", "si", "sí", "yes"}

    return bool(valor)


def _columnas_editables_producto(columnas=None):

    columnas = columnas or _columnas_productos_fito()
    columna_registro = _columna_registro_producto(columnas)
    candidatas = [
        columna_registro,
        "nombre",
        "materia_activa",
        "titular",
        "uso_autorizado",
        "dosis",
        "plazo_seguridad",
        "observaciones",
        "activo",
    ]
    return [
        columna
        for columna in candidatas
        if columna and columna in columnas
    ]


def _valores_producto_fito(datos, columnas=None):

    columnas = columnas or _columnas_productos_fito()
    columna_registro = _columna_registro_producto(columnas)
    valores = {}

    if columna_registro:

        valores[columna_registro] = _primer_valor(
            datos,
            columna_registro,
            "numero_registro",
            "registro",
        )

    for columna in (
        "nombre",
        "materia_activa",
        "titular",
        "uso_autorizado",
        "dosis",
        "plazo_seguridad",
        "observaciones",
    ):

        if columna in columnas:

            valores[columna] = _primer_valor(datos, columna)

    if "activo" in columnas:

        valores["activo"] = int(_bool_producto(datos.get("activo", True)))

    return valores


def _insertar_producto_fito(datos):

    columnas = _columnas_productos_fito()
    valores = _valores_producto_fito(datos, columnas)
    ahora = pd.Timestamp.now().isoformat()

    if "created_at" in columnas:

        valores["created_at"] = ahora

    if "updated_at" in columnas:

        valores["updated_at"] = ahora

    nombres = list(valores)
    marcadores = ",".join(["?"] * len(nombres))

    conn = conectar()

    try:

        cursor = conn.execute(
            f"""
            INSERT INTO productos_fito
            ({','.join(_identificador_sql(nombre) for nombre in nombres)})
            VALUES ({marcadores})
            """,
            [valores[nombre] for nombre in nombres],
        )
        conn.commit()
        return int(cursor.lastrowid)

    finally:

        conn.close()


def _actualizar_producto_fito(producto_id, datos):

    columnas = _columnas_productos_fito()
    valores = _valores_producto_fito(datos, columnas)

    if "updated_at" in columnas:

        valores["updated_at"] = pd.Timestamp.now().isoformat()

    if not valores:

        return

    asignaciones = ",".join(
        f"{_identificador_sql(columna)}=?"
        for columna in valores
    )
    conn = conectar()

    try:

        conn.execute(
            f"UPDATE productos_fito SET {asignaciones} WHERE id=?",
            [valores[columna] for columna in valores] + [int(producto_id)],
        )
        conn.commit()

    finally:

        conn.close()


def render():

    st.title("🧪 Productos fitosanitarios")
    mensaje_productos_fito = st.session_state.pop(
        "mensaje_productos_fito",
        None
    )

    if mensaje_productos_fito:

        st.success(mensaje_productos_fito)

    columnas_productos = _columnas_productos_fito()
    columna_registro = _columna_registro_producto(columnas_productos)

    if not columna_registro:

        st.error(
            "La tabla de productos no tiene columna de número de registro."
        )
        return

    def buscar_producto_mapa(registro):

        try:

            import json
            import requests

        except Exception as e:

            return None, f"requests no está disponible: {e}"

        try:

            r = requests.post(
                "https://servicio.mapa.gob.es"
                "/regfiweb/Exportaciones/ExportJsonProductos",
                data={"numRegistro": registro},
                timeout=10
            )

            if r.status_code != 200:

                return None, (
                    "MAPA no responde correctamente "
                    f"(HTTP {r.status_code})"
                )

            respuesta = r.json()

            if isinstance(respuesta, str):

                respuesta = json.loads(respuesta)

            contenido = respuesta.get(
                "Contenido",
                "[]"
            )

            productos = json.loads(contenido)

            if not productos:

                return None, "No se encontró el producto en MAPA"

            producto = productos[0]
            id_producto = producto.get("IdProducto")

            if id_producto:

                detalle = requests.get(
                    "https://servicio.mapa.gob.es"
                    "/regfiweb/Productos/GetProductoById",
                    params={"idProducto": id_producto},
                    timeout=10
                )

                if detalle.status_code == 200:

                    producto.update(
                        detalle.json()
                    )

            observaciones = (
                producto.get("observaciones")
                or producto.get("Observaciones")
                or producto.get("condicionamiento")
                or producto.get("Condicionamiento")
                or ""
            )

            datos = {
                "registro": (
                    producto.get("numRegistro")
                    or producto.get("NumRegistro")
                    or registro
                ),
                "nombre": (
                    producto.get("nombre")
                    or producto.get("Nombre")
                    or ""
                ),
                "materia_activa": (
                    producto.get("formulado")
                    or producto.get("Formulado")
                    or ""
                ),
                "dosis": "",
                "plazo_seguridad": "",
                "observaciones": observaciones
            }

            return datos, None

        except Exception as e:

            return None, f"No se pudo consultar MAPA: {e}"



    seccion = st.radio(
        "Opciones de productos fito",
        [
            "📋 Listado",
            "➕ Nuevo producto",
            "✏️ Editar",
            "🗑️ Borrar"
        ],
        horizontal=True,
        key="productos_fito_seccion"
    )
    if seccion == "➕ Nuevo producto":

        st.subheader("Nuevo producto")
        if "form_producto_fito_version" not in st.session_state:

            st.session_state["form_producto_fito_version"] = 0

        form_producto_fito_version = (
            st.session_state["form_producto_fito_version"]
        )

        registro = st.text_input(
            "Nº Registro MAPA",
            key=f"producto_fito_registro_{form_producto_fito_version}"
        ).strip()

        producto_existente = leer(
            f"""
            SELECT *
            FROM productos_fito
            WHERE {_identificador_sql(columna_registro)}=?
            """,
            (registro,)
        ) if registro else pd.DataFrame()

        if registro:

            clave_busqueda = f"mapa_producto_{registro}"

            if clave_busqueda not in st.session_state:

                with st.spinner("Consultando Registro MAPA"):

                    datos_mapa, error_mapa = buscar_producto_mapa(
                        registro
                    )

                st.session_state[clave_busqueda] = {
                    "datos": datos_mapa,
                    "error": error_mapa
                }

            resultado_mapa = st.session_state[clave_busqueda]

            if resultado_mapa["datos"]:

                st.success(
                    "Producto encontrado en el Registro MAPA"
                )

            elif resultado_mapa["error"]:

                st.warning(
                    resultado_mapa["error"]
                )

        else:

            resultado_mapa = {
                "datos": None,
                "error": None
            }

        if not producto_existente.empty:

            st.warning(
                "Ya existe un producto con ese número de registro"
            )

            datos_iniciales = producto_existente.iloc[0][
                _columnas_editables_producto(columnas_productos)
            ].to_dict()

        elif resultado_mapa["datos"]:

            datos_iniciales = resultado_mapa["datos"]
            datos_iniciales[columna_registro] = _primer_valor(
                datos_iniciales,
                columna_registro,
                "numero_registro",
                "registro",
            )

        else:

            datos_iniciales = {
                columna_registro: registro,
                "nombre": "",
                "materia_activa": "",
                "titular": "",
                "uso_autorizado": "",
                "plazo_seguridad": "",
                "observaciones": "",
                "activo": True,
            }

        columnas_editor_producto = _columnas_editables_producto(
            columnas_productos
        )
        etiquetas_producto = {
            columna_registro: "Nº registro",
        }
        editor_producto_visual = preparar_dataframe_visual(
            pd.DataFrame([datos_iniciales]),
            columnas=columnas_editor_producto,
            ocultar_tecnicas=False,
            etiquetas_extra=etiquetas_producto
        )
        editado_visual = st.data_editor(
            editor_producto_visual,
            num_rows="fixed",
            disabled=["Nº registro"],
            use_container_width=True,
            hide_index=True,
            column_order=list(editor_producto_visual.columns),
            key=f"producto_fito_alta_editor_v7_{form_producto_fito_version}"
        )
        editado = mapear_columnas_visuales_a_tecnicas(
            editado_visual,
            etiquetas_extra=etiquetas_producto
        )

        actualizar = False

        if not producto_existente.empty:

            actualizar = st.checkbox(
                "Actualizar el producto existente con los datos editados",
                key=f"producto_fito_actualizar_{form_producto_fito_version}"
            )

        if st.button(
            "Guardar producto",
            key=f"producto_fito_guardar_{form_producto_fito_version}"
        ):

            datos = editado.iloc[0].fillna("").to_dict()
            registro_guardar = str(
                datos.get(columna_registro, "")
            ).strip()

            if not registro_guardar:

                st.warning(
                    "Introduce un número de registro"
                )

            elif not producto_existente.empty and not actualizar:

                st.warning(
                    "El registro ya existe. Marca la opción de actualizar para guardar cambios."
                )

            elif not producto_existente.empty and actualizar:

                _actualizar_producto_fito(
                    int(producto_existente.iloc[0]["id"]),
                    datos,
                )

                st.session_state["mensaje_productos_fito"] = (
                    "Producto actualizado"
                )
                st.session_state["form_producto_fito_version"] += 1
                st.rerun()

            else:

                existe = leer(
                    f"""
                    SELECT id
                    FROM productos_fito
                    WHERE {_identificador_sql(columna_registro)}=?
                    """,
                    (registro_guardar,)
                )

                if not existe.empty:

                    st.warning(
                        "Ya existe un producto con ese número de registro"
                    )

                else:

                    _insertar_producto_fito(datos)

                    st.session_state["mensaje_productos_fito"] = (
                        "Producto añadido"
                    )
                    st.session_state["form_producto_fito_version"] += 1
                    st.rerun()



    productos_guardados = leer(
        "SELECT * FROM productos_fito ORDER BY id"
    )


    if seccion == "📋 Listado":

        st.subheader("Listado de productos")
        productos_filtrados = mostrar_filtros_dataframe(
            productos_guardados,
            "productos_fito_listado",
            columnas_texto=[
                columna_registro,
                "nombre",
                "materia_activa",
                "observaciones"
            ],
            filtros_select={
                "Registro": columna_registro,
                "Nombre": "nombre",
                "Materia activa": "materia_activa"
            }
        )
        st.dataframe(
            preparar_dataframe_visual(
                productos_filtrados,
                ocultar_tecnicas=True,
                etiquetas_extra={columna_registro: "Nº registro"}
            ),
            hide_index=True,
            use_container_width=True
        )


    if seccion == "✏️ Editar":

        st.subheader("Editar productos")
        if "productos_fito_editor_version" not in st.session_state:

            st.session_state["productos_fito_editor_version"] = 0

        productos_fito_editor_version = st.session_state[
            "productos_fito_editor_version"
        ]

        columnas_editables_fito = _columnas_editables_producto(
            columnas_productos
        )

        productos_editados = st.data_editor(
            productos_guardados,
            num_rows="fixed",
            disabled=["id"],
            use_container_width=True,
            hide_index=True,
            column_order=["id"] + columnas_editables_fito,
            column_config=preparar_column_config_visual(
                productos_guardados,
                etiquetas={columna_registro: "Nº registro"}
            ),
            key=(
                "productos_fito_editar_editor_guardados_"
                f"{productos_fito_editor_version}"
            )
        )

        confirmar_cambios_fito = st.checkbox(
            "Confirmo que quiero guardar los cambios",
            key=(
                "productos_fito_editar_confirmar_cambios_"
                f"{productos_fito_editor_version}"
            )
        )

        if st.button(
            "💾 Guardar cambios",
            key=(
                "productos_fito_editar_guardar_cambios_"
                f"{productos_fito_editor_version}"
            )
        ):

            if productos_guardados.empty:

                st.info(
                    "No hay productos guardados para actualizar"
                )

            elif not confirmar_cambios_fito:

                st.warning(
                    "Marca la confirmación antes de guardar los cambios"
                )

            else:

                productos_para_guardar = productos_editados.copy()
                columnas_texto_fito = [
                    columna
                    for columna in columnas_editables_fito
                    if columna != "activo"
                ]

                for columna in columnas_texto_fito:

                    productos_para_guardar[columna] = (
                        productos_para_guardar[columna]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )

                registros_vacios = productos_para_guardar[columna_registro] == ""

                registros_duplicados = (
                    productos_para_guardar[columna_registro]
                    .duplicated(keep=False)
                )

                if registros_vacios.any():

                    ids_vacios = productos_para_guardar.loc[
                        registros_vacios,
                        "id"
                    ].astype(str).tolist()

                    st.warning(
                        "Todos los productos deben tener registro. "
                        f"Revisa id: {', '.join(ids_vacios)}"
                    )

                elif registros_duplicados.any():

                    registros_repetidos = sorted(
                        productos_para_guardar.loc[
                            registros_duplicados,
                            columna_registro
                        ].unique()
                    )

                    st.warning(
                        "No se pueden guardar registros duplicados: "
                        f"{', '.join(registros_repetidos)}"
                    )

                else:

                    productos_originales = productos_guardados.copy()

                    for columna in columnas_texto_fito:

                        productos_originales[columna] = (
                            productos_originales[columna]
                            .fillna("")
                            .astype(str)
                            .str.strip()
                        )

                    filas_actualizadas = []

                    for _, fila in productos_para_guardar.iterrows():

                        producto_id = int(fila["id"])
                        original = productos_originales[
                            productos_originales["id"] == producto_id
                        ]

                        if original.empty:

                            continue

                        cambios = any(
                            fila[columna] != original.iloc[0][columna]
                            for columna in columnas_editables_fito
                        )

                        if cambios:

                            _actualizar_producto_fito(
                                producto_id,
                                fila.to_dict(),
                            )

                            filas_actualizadas.append(
                                producto_id
                            )

                    if filas_actualizadas:

                        st.session_state["mensaje_productos_fito"] = (
                            "Filas actualizadas: "
                            f"{len(filas_actualizadas)} "
                            f"(id: {', '.join(map(str, filas_actualizadas))})"
                        )
                        st.session_state[
                            "productos_fito_editor_version"
                        ] += 1
                        st.rerun()

                    else:

                        st.info(
                            "No había cambios para guardar"
                        )



    if seccion == "🗑️ Borrar":

        st.subheader("Borrar productos")
        borrar_registros_seguro(
            "productos_fito",
            "id",
            productos_guardados,
            "productos fitosanitarios",
            bloqueos=[
                (
                    "tratamientos",
                    "producto_id",
                    "el producto está usado en tratamientos"
                )
            ],
            campo_descripcion="nombre",
            key="productos_fito_borrar"
        )
