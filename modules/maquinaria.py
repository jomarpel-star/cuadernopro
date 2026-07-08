from datetime import datetime

import pandas as pd
import streamlit as st

from core.borrado import (
    hacer_backup_antes_de_borrar,
    tabla_y_columna_existen,
)
from core.db import conectar, leer
from core.fechas import (
    formatear_fecha_es,
    parsear_fecha_es,
    preparar_columnas_fecha_tabla,
)
from core.filtros import mostrar_filtros_dataframe
from core.ui_tablas import preparar_dataframe_visual


COLUMNAS_EQUIPOS = [
    "id",
    "nombre",
    "tipo",
    "marca",
    "modelo",
    "matricula",
    "numero_roma",
    "numero_serie",
    "fecha_adquisicion",
    "fecha_ultima_inspeccion",
    "fecha_proxima_inspeccion",
    "capacidad_litros",
    "observaciones"
]

COLUMNAS_LISTADO = [
    "id_visual",
    "origen",
    "tabla_origen",
    "id_real",
    "descripcion",
    "nombre",
    "tipo",
    "marca",
    "modelo",
    "matricula",
    "numero_roma",
    "numero_serie",
    "fecha_compra",
    "fecha_ultima_inspeccion",
    "fecha_proxima_inspeccion",
    "capacidad_litros",
    "horas_uso",
    "observaciones"
]

FECHAS_EQUIPOS = [
    "fecha_adquisicion",
    "fecha_ultima_inspeccion",
    "fecha_proxima_inspeccion"
]

FECHAS_LISTADO = [
    "fecha_compra",
    "fecha_ultima_inspeccion",
    "fecha_proxima_inspeccion"
]

TEXTOS_EQUIPOS = [
    "nombre",
    "tipo",
    "marca",
    "modelo",
    "matricula",
    "numero_roma",
    "numero_serie",
    "observaciones"
]

TEXTOS_LISTADO = [
    "id_visual",
    "origen",
    "tabla_origen",
    "descripcion",
    "nombre",
    "tipo",
    "marca",
    "modelo",
    "matricula",
    "numero_roma",
    "numero_serie",
    "observaciones"
]


def _tabla_existe_conn(conn, tabla):

    fila = conn.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (tabla,),
    ).fetchone()
    return fila is not None


def _columnas_tabla_conn(conn, tabla):

    if not _tabla_existe_conn(conn, tabla):

        return set()

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _columnas_tabla(tabla):

    conn = conectar()

    try:

        return _columnas_tabla_conn(conn, tabla)

    finally:

        conn.close()


def _expr_texto(tabla, columna, columnas, defecto="''"):

    if columna in columnas:

        return f"COALESCE({tabla}.{columna},{defecto})"

    return defecto


def _expr_valor(tabla, columna, columnas, defecto="NULL"):

    if columna in columnas:

        return f"{tabla}.{columna}"

    return defecto


def _anadir_si_existe(destino, columnas, columna, valor):

    if columna in columnas:

        destino[columna] = valor


def _ejecutar_insert_dinamico(conn, tabla, valores):

    nombres = list(valores)

    if not nombres:

        return None

    cursor = conn.execute(
        f"""
        INSERT INTO {tabla}
        ({','.join(nombres)})
        VALUES ({','.join(['?'] * len(nombres))})
        """,
        [valores[columna] for columna in nombres],
    )
    return cursor.lastrowid


def _ejecutar_update_dinamico(conn, tabla, registro_id, valores):

    nombres = list(valores)

    if not nombres:

        return

    conn.execute(
        f"""
        UPDATE {tabla}
        SET {','.join(f'{columna}=?' for columna in nombres)}
        WHERE id=?
        """,
        [valores[columna] for columna in nombres] + [int(registro_id)],
    )


def _leer_equipos():

    columnas = _columnas_tabla("equipos_aplicacion")
    expr_fecha_revision = (
        _expr_valor("equipos_aplicacion", "fecha_revision", columnas)
        if "fecha_revision" in columnas
        else _expr_valor(
            "equipos_aplicacion",
            "fecha_ultima_inspeccion",
            columnas
        )
    )
    expr_fecha_proxima_revision = (
        _expr_valor(
            "equipos_aplicacion",
            "fecha_proxima_revision",
            columnas
        )
        if "fecha_proxima_revision" in columnas
        else _expr_valor(
            "equipos_aplicacion",
            "fecha_proxima_inspeccion",
            columnas
        )
    )

    return leer(
        f"""
        SELECT
            equipos_aplicacion.id,
            {_expr_texto("equipos_aplicacion", "nombre", columnas)}
                AS nombre,
            {_expr_texto("equipos_aplicacion", "tipo", columnas)} AS tipo,
            {_expr_texto("equipos_aplicacion", "marca", columnas)} AS marca,
            {_expr_texto("equipos_aplicacion", "modelo", columnas)}
                AS modelo,
            {_expr_texto("equipos_aplicacion", "matricula", columnas)}
                AS matricula,
            {_expr_texto("equipos_aplicacion", "numero_roma", columnas)}
                AS numero_roma,
            {_expr_texto("equipos_aplicacion", "numero_serie", columnas)}
                AS numero_serie,
            {_expr_valor(
                "equipos_aplicacion",
                "fecha_adquisicion",
                columnas
            )} AS fecha_adquisicion,
            {expr_fecha_revision} AS fecha_ultima_inspeccion,
            {expr_fecha_proxima_revision} AS fecha_proxima_inspeccion,
            {_expr_valor(
                "equipos_aplicacion",
                "capacidad_litros",
                columnas
            )} AS capacidad_litros,
            {_expr_texto("equipos_aplicacion", "observaciones", columnas)}
                AS observaciones
        FROM equipos_aplicacion
        ORDER BY equipos_aplicacion.id
        """
    )


def _leer_maquinaria_general():

    columnas = _columnas_tabla("maquinaria")
    expr_nombre = (
        _expr_texto("maquinaria", "nombre", columnas)
        if "nombre" in columnas
        else _expr_texto("maquinaria", "descripcion", columnas)
    )
    expr_horas = (
        _expr_valor("maquinaria", "horas_uso", columnas)
        if "horas_uso" in columnas
        else _expr_valor("maquinaria", "num_horas", columnas)
    )

    return leer(
        f"""
        SELECT
            maquinaria.id,
            {expr_nombre} AS nombre,
            {_expr_texto("maquinaria", "tipo", columnas)} AS tipo,
            {_expr_texto("maquinaria", "marca", columnas)} AS marca,
            {_expr_texto("maquinaria", "modelo", columnas)} AS modelo,
            {_expr_texto("maquinaria", "matricula", columnas)}
                AS matricula,
            {_expr_texto("maquinaria", "numero_roma", columnas)}
                AS numero_roma,
            {_expr_texto("maquinaria", "numero_serie", columnas)}
                AS numero_serie,
            {_expr_valor("maquinaria", "fecha_compra", columnas)}
                AS fecha_compra,
            {expr_horas} AS horas_uso,
            {_expr_texto("maquinaria", "observaciones", columnas)}
                AS observaciones
        FROM maquinaria
        ORDER BY nombre,maquinaria.id
        """
    )


def _normalizar_columnas_texto(dataframe, columnas):

    datos = dataframe.copy()

    for columna in columnas:

        if columna not in datos:

            datos[columna] = ""

        datos[columna] = datos[columna].fillna("").astype(str)

    return datos


def _texto(valor):

    if valor is None or pd.isna(valor):

        return ""

    return str(valor).strip()


def _numero(valor, defecto=0.0):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return defecto

    return float(numero)


def _descripcion_registro(fila):

    partes = [
        _texto(fila.get("nombre")),
        _texto(fila.get("marca")),
        _texto(fila.get("modelo")),
        _texto(fila.get("tipo")),
    ]
    return " / ".join(parte for parte in partes if parte)


def _leer_listado_maquinaria():

    maquinaria = _leer_maquinaria_general()
    equipos = _leer_equipos()
    filas = []

    if not maquinaria.empty:

        maquinaria = _normalizar_columnas_texto(
            maquinaria,
            [
                "nombre",
                "tipo",
                "marca",
                "modelo",
                "matricula",
                "numero_roma",
                "numero_serie",
                "observaciones"
            ]
        )

        for _, fila in maquinaria.iterrows():

            id_real = int(fila["id"])
            id_visual = f"MAQ-{id_real}"
            filas.append({
                "id_visual": id_visual,
                "origen": "Maquinaria",
                "tabla_origen": "maquinaria",
                "id_real": id_real,
                "descripcion": _descripcion_registro(fila),
                "nombre": fila["nombre"],
                "tipo": fila["tipo"],
                "marca": fila["marca"],
                "modelo": fila["modelo"],
                "matricula": fila["matricula"],
                "numero_roma": fila["numero_roma"],
                "numero_serie": fila["numero_serie"],
                "fecha_compra": fila["fecha_compra"],
                "fecha_ultima_inspeccion": "",
                "fecha_proxima_inspeccion": "",
                "capacidad_litros": None,
                "horas_uso": fila["horas_uso"],
                "observaciones": fila["observaciones"]
            })

    if not equipos.empty:

        equipos = _normalizar_columnas_texto(
            equipos,
            [
                "nombre",
                "tipo",
                "marca",
                "modelo",
                "matricula",
                "numero_roma",
                "numero_serie",
                "observaciones"
            ]
        )

        for _, fila in equipos.iterrows():

            id_real = int(fila["id"])
            id_visual = f"EQ-{id_real}"
            filas.append({
                "id_visual": id_visual,
                "origen": "Equipo aplicación",
                "tabla_origen": "equipos_aplicacion",
                "id_real": id_real,
                "descripcion": _descripcion_registro(fila),
                "nombre": fila["nombre"],
                "tipo": fila["tipo"],
                "marca": fila["marca"],
                "modelo": fila["modelo"],
                "matricula": fila["matricula"],
                "numero_roma": fila["numero_roma"],
                "numero_serie": fila["numero_serie"],
                "fecha_compra": fila["fecha_adquisicion"],
                "fecha_ultima_inspeccion": fila["fecha_ultima_inspeccion"],
                "fecha_proxima_inspeccion": fila["fecha_proxima_inspeccion"],
                "capacidad_litros": fila["capacidad_litros"],
                "horas_uso": None,
                "observaciones": fila["observaciones"]
            })

    return pd.DataFrame(filas, columns=COLUMNAS_LISTADO)


def _render_listado(maquinaria):

    st.subheader("Listado de maquinaria y equipos")
    st.caption(
        "MAQ-* corresponde a maquinaria general. EQ-* corresponde a equipos "
        "de aplicación fitosanitaria gestionados desde Explotación."
    )

    if maquinaria.empty:

        st.info("No hay maquinaria ni equipos registrados")
        return

    maquinaria_filtrada = mostrar_filtros_dataframe(
        maquinaria,
        "maquinaria_listado",
        columnas_texto=TEXTOS_LISTADO,
        columna_fecha="fecha_proxima_inspeccion",
        filtros_select={
            "Origen": "origen",
            "Tipo": "tipo",
            "Marca": "marca",
            "Modelo": "modelo",
            "Matrícula": "matricula"
        }
    )

    columnas_maquinaria = _columnas_tabla("maquinaria")
    columnas_equipos = _columnas_tabla("equipos_aplicacion")
    maquinaria_filtrada = maquinaria_filtrada.copy()
    if "descripcion" in maquinaria_filtrada.columns:

        maquinaria_filtrada["nombre_visual"] = (
            maquinaria_filtrada["descripcion"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    else:

        maquinaria_filtrada["nombre_visual"] = ""

    if "nombre" in maquinaria_filtrada.columns:

        nombre_origen = (
            maquinaria_filtrada["nombre"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        maquinaria_filtrada["nombre_visual"] = (
            maquinaria_filtrada["nombre_visual"].where(
                maquinaria_filtrada["nombre_visual"] != "",
                nombre_origen
            )
        )

    columnas_visibles = [
        "id_visual",
        "origen",
        "tabla_origen",
        "id_real",
        "nombre_visual",
        "tipo",
        "marca",
        "modelo",
    ]

    if "matricula" in columnas_maquinaria or "matricula" in columnas_equipos:

        columnas_visibles.append("matricula")

    columnas_visibles.append("numero_roma")

    if "numero_serie" in columnas_maquinaria or "numero_serie" in columnas_equipos:

        columnas_visibles.append("numero_serie")

    if (
        "fecha_compra" in columnas_maquinaria
        or "fecha_adquisicion" in columnas_equipos
    ):

        columnas_visibles.append("fecha_compra")

    if (
        "fecha_revision" in columnas_equipos
        or "fecha_ultima_inspeccion" in columnas_equipos
    ):

        columnas_visibles.append("fecha_ultima_inspeccion")

    if (
        "fecha_proxima_revision" in columnas_equipos
        or "fecha_proxima_inspeccion" in columnas_equipos
    ):

        columnas_visibles.append("fecha_proxima_inspeccion")

    if "capacidad_litros" in columnas_equipos:

        columnas_visibles.append("capacidad_litros")

    if "horas_uso" in columnas_maquinaria or "num_horas" in columnas_maquinaria:

        columnas_visibles.append("horas_uso")

    columnas_visibles.append("observaciones")

    maquinaria_visual = preparar_dataframe_visual(
        preparar_columnas_fecha_tabla(
            maquinaria_filtrada,
            FECHAS_LISTADO
        ),
        columnas=columnas_visibles,
        ocultar_tecnicas=False,
        etiquetas_extra={
            "id_visual": "ID",
            "origen": "Origen",
            "nombre_visual": "Nombre / descripción",
            "fecha_ultima_inspeccion": "Fecha revisión",
            "fecha_proxima_inspeccion": "Próxima revisión",
            "capacidad_litros": "Capacidad litros",
            "horas_uso": "Horas de uso",
        },
    )
    st.dataframe(
        maquinaria_visual,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Fecha de compra": st.column_config.DateColumn(
                "Fecha de compra",
                format="DD/MM/YYYY"
            ),
            "Nombre / descripción": st.column_config.TextColumn(
                "Nombre / descripción"
            ),
            "Matrícula": st.column_config.TextColumn("Matrícula"),
            "Nº ROMA": st.column_config.TextColumn("Nº ROMA"),
            "Fecha revisión": st.column_config.DateColumn(
                "Fecha revisión",
                format="DD/MM/YYYY"
            ),
            "Próxima revisión": st.column_config.DateColumn(
                "Próxima revisión",
                format="DD/MM/YYYY"
            ),
            "Capacidad litros": st.column_config.NumberColumn(
                "Capacidad litros",
                format="%.2f"
            ),
            "Horas de uso": st.column_config.NumberColumn(
                "Horas de uso",
                format="%.2f"
            )
        }
    )


def _insertar_maquinaria(datos):

    columnas = _columnas_tabla("maquinaria")
    ahora = datetime.now().isoformat(timespec="seconds")
    valores = {}
    nombre = datos.get("nombre", "")

    _anadir_si_existe(valores, columnas, "nombre", nombre)
    _anadir_si_existe(valores, columnas, "descripcion", nombre)

    for columna in (
        "tipo",
        "marca",
        "modelo",
        "matricula",
        "numero_roma",
        "numero_serie",
        "fecha_compra",
        "horas_uso",
        "num_horas",
        "observaciones",
    ):

        _anadir_si_existe(valores, columnas, columna, datos.get(columna))

    _anadir_si_existe(valores, columnas, "activa", 1)
    _anadir_si_existe(valores, columnas, "created_at", ahora)
    _anadir_si_existe(valores, columnas, "updated_at", ahora)

    conn = conectar()

    try:

        _ejecutar_insert_dinamico(conn, "maquinaria", valores)
        conn.commit()

    finally:

        conn.close()


def _actualizar_maquinaria(registro_id, datos):

    columnas = _columnas_tabla("maquinaria")
    valores = {}
    nombre = datos.get("nombre", "")

    _anadir_si_existe(valores, columnas, "nombre", nombre)
    _anadir_si_existe(valores, columnas, "descripcion", nombre)

    for columna in (
        "tipo",
        "marca",
        "modelo",
        "matricula",
        "numero_roma",
        "numero_serie",
        "fecha_compra",
        "horas_uso",
        "num_horas",
        "observaciones",
    ):

        _anadir_si_existe(valores, columnas, columna, datos.get(columna))

    _anadir_si_existe(
        valores,
        columnas,
        "updated_at",
        datetime.now().isoformat(timespec="seconds")
    )

    conn = conectar()

    try:

        _ejecutar_update_dinamico(
            conn,
            "maquinaria",
            registro_id,
            valores
        )
        conn.commit()

    finally:

        conn.close()


def _render_nuevo():

    st.subheader("Nueva maquinaria")
    st.info(
        "Los equipos de aplicación fitosanitaria se dan de alta desde "
        "Explotación → Equipos de aplicación."
    )

    if "form_maquinaria_version" not in st.session_state:

        st.session_state["form_maquinaria_version"] = 0

    form_maquinaria_version = st.session_state["form_maquinaria_version"]
    columnas_maquinaria = _columnas_tabla("maquinaria")

    with st.form(f"maquinaria_nuevo_form_v{form_maquinaria_version}"):

        maquinaria_nombre = st.text_input(
            "Nombre / descripción",
            key=f"maquinaria_nuevo_nombre_{form_maquinaria_version}"
        )
        maquinaria_tipo = st.text_input(
            "Tipo",
            key=f"maquinaria_nuevo_tipo_{form_maquinaria_version}"
        )
        maquinaria_marca = st.text_input(
            "Marca",
            key=f"maquinaria_nuevo_marca_{form_maquinaria_version}"
        )
        maquinaria_modelo = st.text_input(
            "Modelo",
            key=f"maquinaria_nuevo_modelo_{form_maquinaria_version}"
        )
        maquinaria_matricula = ""

        if "matricula" in columnas_maquinaria:

            maquinaria_matricula = st.text_input(
                "Matrícula",
                key=f"maquinaria_nuevo_matricula_{form_maquinaria_version}"
            )

        maquinaria_numero_roma = st.text_input(
            "Nº ROMA",
            key=f"maquinaria_nuevo_numero_roma_{form_maquinaria_version}"
        )
        maquinaria_numero_serie = ""

        if "numero_serie" in columnas_maquinaria:

            maquinaria_numero_serie = st.text_input(
                "Número de serie",
                key=(
                    "maquinaria_nuevo_numero_serie_"
                    f"{form_maquinaria_version}"
                )
            )

        maquinaria_fecha_compra = ""

        if "fecha_compra" in columnas_maquinaria:

            maquinaria_fecha_compra = st.text_input(
                "Fecha de compra",
                placeholder="DD/MM/AAAA",
                key=(
                    "maquinaria_nuevo_fecha_compra_"
                    f"{form_maquinaria_version}"
                )
            )

        maquinaria_horas_uso = 0.0

        if "horas_uso" in columnas_maquinaria or "num_horas" in columnas_maquinaria:

            maquinaria_horas_uso = st.number_input(
                "Horas de uso",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key=f"maquinaria_nuevo_horas_uso_{form_maquinaria_version}"
            )

        maquinaria_observaciones = st.text_area(
            "Observaciones",
            key=f"maquinaria_nuevo_observaciones_{form_maquinaria_version}"
        )

        if st.form_submit_button("Añadir maquinaria"):

            maquinaria_nombre = maquinaria_nombre.strip()
            maquinaria_tipo = maquinaria_tipo.strip()

            if not maquinaria_nombre or not maquinaria_tipo:

                st.error("Nombre y tipo son obligatorios")

            else:

                try:

                    fecha_compra = (
                        parsear_fecha_es(maquinaria_fecha_compra)
                        if "fecha_compra" in columnas_maquinaria
                        else None
                    )

                except ValueError:

                    st.error("La fecha debe tener formato DD/MM/AAAA")

                else:

                    _insertar_maquinaria(
                        {
                            "nombre": maquinaria_nombre,
                            "tipo": maquinaria_tipo,
                            "marca": maquinaria_marca.strip(),
                            "modelo": maquinaria_modelo.strip(),
                            "matricula": maquinaria_matricula.strip(),
                            "numero_roma": maquinaria_numero_roma.strip(),
                            "numero_serie": maquinaria_numero_serie.strip(),
                            "fecha_compra": fecha_compra,
                            "horas_uso": float(maquinaria_horas_uso),
                            "num_horas": float(maquinaria_horas_uso),
                            "observaciones": (
                                maquinaria_observaciones.strip()
                            )
                        }
                    )

                    st.success("Maquinaria añadida")
                    st.session_state["form_maquinaria_version"] += 1
                    st.rerun()


def _formatear_opcion_registro(registros, id_visual):

    fila = registros[registros["id_visual"] == id_visual]

    if fila.empty:

        return id_visual

    fila = fila.iloc[0]
    descripcion = _texto(fila.get("descripcion")) or _texto(
        fila.get("nombre")
    )
    return f"{fila['id_visual']} — {fila['origen']} — {descripcion}"


def _seleccionar_registro(registros, key):

    opciones = registros["id_visual"].astype(str).tolist()
    id_visual = st.selectbox(
        "Registro",
        opciones,
        format_func=lambda valor: _formatear_opcion_registro(
            registros,
            valor
        ),
        key=key
    )
    fila = registros[registros["id_visual"] == id_visual].iloc[0]
    return id_visual, fila


def _leer_registro_tabla(tabla, registro_id):

    datos = leer(
        f'SELECT * FROM "{tabla}" WHERE id=?',
        (int(registro_id),)
    )

    if datos.empty:

        return {}

    return datos.iloc[0].to_dict()


def _previsualizar_registro(fila):

    st.dataframe(
        preparar_dataframe_visual(
            pd.DataFrame([
                {
                    "id_visual": fila["id_visual"],
                    "origen": fila["origen"],
                    "nombre": fila["nombre"],
                    "marca": fila["marca"],
                    "modelo": fila["modelo"],
                    "matricula": fila["matricula"],
                    "numero_roma": fila["numero_roma"],
                    "numero_serie": fila["numero_serie"],
                    "tipo": fila["tipo"],
                    "tabla_origen": fila["tabla_origen"],
                    "id_real": fila["id_real"],
                }
            ]),
            ocultar_tecnicas=False,
            etiquetas_extra={
                "id_visual": "ID",
                "origen": "Origen",
                "nombre": "Nombre / descripción",
                "tabla_origen": "Tabla origen",
                "id_real": "ID real",
            },
        ),
        hide_index=True,
        use_container_width=True
    )


def _render_edicion_maquinaria(registro_id, id_visual):

    datos = _leer_registro_tabla("maquinaria", registro_id)
    columnas_maquinaria = _columnas_tabla("maquinaria")

    if not datos:

        st.error("No se encontró el registro de maquinaria seleccionado")
        return

    version_key = f"maquinaria_editar_version_{id_visual}"

    if version_key not in st.session_state:

        st.session_state[version_key] = 0

    editar_version = st.session_state[version_key]

    with st.form(f"maquinaria_editar_form_{id_visual}_v{editar_version}"):

        nombre = st.text_input(
            "Nombre / descripción",
            value=_texto(datos.get("nombre") or datos.get("descripcion"))
        )
        tipo = st.text_input("Tipo", value=_texto(datos.get("tipo")))
        marca = st.text_input("Marca", value=_texto(datos.get("marca")))
        modelo = st.text_input("Modelo", value=_texto(datos.get("modelo")))
        matricula = ""

        if "matricula" in columnas_maquinaria:

            matricula = st.text_input(
                "Matrícula",
                value=_texto(datos.get("matricula"))
            )

        numero_roma = st.text_input(
            "Nº ROMA",
            value=_texto(datos.get("numero_roma"))
        )
        numero_serie = ""

        if "numero_serie" in columnas_maquinaria:

            numero_serie = st.text_input(
                "Número de serie",
                value=_texto(datos.get("numero_serie"))
            )

        fecha_compra = ""

        if "fecha_compra" in columnas_maquinaria:

            fecha_compra = st.text_input(
                "Fecha de compra",
                value=formatear_fecha_es(datos.get("fecha_compra")),
                placeholder="DD/MM/AAAA"
            )

        horas_uso = 0.0

        if "horas_uso" in columnas_maquinaria or "num_horas" in columnas_maquinaria:

            horas_uso = st.number_input(
                "Horas de uso",
                min_value=0.0,
                value=_numero(
                    datos.get("horas_uso", datos.get("num_horas"))
                ),
                step=1.0
            )

        observaciones = st.text_area(
            "Observaciones",
            value=_texto(datos.get("observaciones"))
        )
        confirmar = st.checkbox(
            "Confirmo que quiero guardar los cambios",
            key=f"maquinaria_confirmar_editar_{id_visual}_{editar_version}"
        )
        guardar = st.form_submit_button("Guardar cambios")

    if not guardar:

        return

    errores = []

    if not nombre.strip():

        errores.append("El nombre no puede estar vacío")

    if not tipo.strip():

        errores.append("El tipo no puede estar vacío")

    try:

        fecha_compra_iso = (
            parsear_fecha_es(fecha_compra)
            if "fecha_compra" in columnas_maquinaria
            else None
        )

    except ValueError:

        errores.append("La fecha de compra debe tener formato DD/MM/AAAA")
        fecha_compra_iso = None

    if not confirmar:

        errores.append("Marca la confirmación antes de guardar")

    if errores:

        for error in errores:

            st.error(error)

        return

    _actualizar_maquinaria(
        registro_id,
        {
            "nombre": nombre.strip(),
            "tipo": tipo.strip(),
            "marca": marca.strip(),
            "modelo": modelo.strip(),
            "matricula": matricula.strip(),
            "numero_roma": numero_roma.strip(),
            "numero_serie": numero_serie.strip(),
            "fecha_compra": fecha_compra_iso,
            "horas_uso": float(horas_uso),
            "num_horas": float(horas_uso),
            "observaciones": observaciones.strip()
        }
    )
    st.session_state["mensaje_maquinaria"] = "Maquinaria actualizada"
    st.session_state[version_key] += 1
    st.rerun()


def _render_edicion_equipo(_registro_id, _id_visual):

    st.info(
        "Este equipo de aplicación se gestiona desde Explotación."
    )


def _render_edicion(registros):

    st.subheader("Edición segura")

    if registros.empty:

        st.info("No hay maquinaria ni equipos registrados")
        return

    id_visual, fila = _seleccionar_registro(
        registros,
        "maquinaria_editar_registro"
    )
    _previsualizar_registro(fila)
    tabla = fila["tabla_origen"]
    registro_id = int(fila["id_real"])

    if tabla == "maquinaria":

        _render_edicion_maquinaria(registro_id, id_visual)

    elif tabla == "equipos_aplicacion":

        _render_edicion_equipo(registro_id, id_visual)

    else:

        st.error("Origen de registro no reconocido")


def _contar_usos(conn, tabla, columna, registro_id):

    if not tabla_y_columna_existen(conn, tabla, columna):

        return 0

    fila = conn.execute(
        f'SELECT COUNT(*) FROM "{tabla}" WHERE "{columna}"=?',
        (int(registro_id),)
    ).fetchone()
    return int(fila[0] or 0)


def _bloqueos_borrado(tabla, registro_id):

    conn = conectar()
    bloqueos = []

    try:

        if tabla == "maquinaria":

            usos_practicas = _contar_usos(
                conn,
                "practicas_culturales",
                "maquinaria_id",
                registro_id
            )

            if usos_practicas:

                bloqueos.append(
                    "No se puede borrar porque está usado en prácticas "
                    f"culturales ({usos_practicas})."
                )

            usos_tratamientos = _contar_usos(
                conn,
                "tratamientos",
                "maquinaria_id",
                registro_id
            )

            if usos_tratamientos:

                bloqueos.append(
                    "No se puede borrar porque está usado en tratamientos "
                    f"fitosanitarios ({usos_tratamientos})."
                )

        elif tabla == "equipos_aplicacion":

            columnas_equipo = [
                columna
                for columna in ["equipo_id", "equipo_aplicacion_id"]
                if tabla_y_columna_existen(conn, "tratamientos", columna)
            ]
            total_usos = 0

            if columnas_equipo:

                condiciones = " OR ".join(
                    f'"{columna}"=?'
                    for columna in columnas_equipo
                )
                fila = conn.execute(
                    "SELECT COUNT(DISTINCT id) FROM tratamientos "
                    f"WHERE {condiciones}",
                    tuple(int(registro_id) for _ in columnas_equipo)
                ).fetchone()
                total_usos = int(fila[0] or 0)

            if total_usos:

                bloqueos.append(
                    "No se puede borrar porque está usado en tratamientos "
                    f"fitosanitarios ({total_usos})."
                )

    finally:

        conn.close()

    return bloqueos


def _render_borrado(registros):

    st.subheader("Borrar maquinaria / equipos")

    if registros.empty:

        st.info("No hay maquinaria ni equipos registrados")
        return

    id_visual, fila = _seleccionar_registro(
        registros,
        "maquinaria_borrar_registro"
    )
    _previsualizar_registro(fila)
    tabla = fila["tabla_origen"]
    registro_id = int(fila["id_real"])

    if tabla == "equipos_aplicacion":

        st.info(
            "Los equipos de aplicación se gestionan desde Explotación."
        )
        return

    bloqueos = _bloqueos_borrado(tabla, registro_id)

    if bloqueos:

        for bloqueo in bloqueos:

            st.error(bloqueo)

    st.warning(
        "Esta acción borra definitivamente el registro seleccionado. "
        "Se hará una copia automática antes de borrar."
    )
    confirmar = st.checkbox(
        "Confirmo que quiero eliminar este registro",
        key=f"maquinaria_confirmar_borrar_{id_visual}"
    )
    texto_confirmacion = st.text_input(
        "Escribe BORRAR para confirmar",
        key=f"maquinaria_texto_borrar_{id_visual}"
    )

    if st.button(
        "Eliminar registro seleccionado",
        key=f"maquinaria_boton_borrar_{id_visual}"
    ):

        if bloqueos:

            st.error("El registro está en uso y no se puede borrar")
            return

        if not confirmar:

            st.warning("Marca la casilla de confirmación")
            return

        if texto_confirmacion != "BORRAR":

            st.warning("Escribe BORRAR exactamente para confirmar")
            return

        ruta_backup = hacer_backup_antes_de_borrar()
        conn = conectar()

        try:

            conn.execute(
                f'DELETE FROM "{tabla}" WHERE id=?',
                (registro_id,)
            )
            conn.commit()

        except Exception:

            conn.rollback()
            raise

        finally:

            conn.close()

        st.session_state["mensaje_maquinaria"] = (
            "Registro eliminado. Copia previa creada en "
            f"{ruta_backup}"
        )
        for clave_widget in (
            "maquinaria_borrar_registro",
            f"maquinaria_confirmar_borrar_{id_visual}",
            f"maquinaria_texto_borrar_{id_visual}",
        ):

            st.session_state.pop(clave_widget, None)

        st.rerun()


def render():

    st.title("🚜 Maquinaria / Equipos")
    mensaje_maquinaria = st.session_state.pop("mensaje_maquinaria", None)

    if mensaje_maquinaria:

        st.success(mensaje_maquinaria)

    seccion = st.radio(
        "Opciones de maquinaria/equipos",
        [
            "📋 Listado",
            "➕ Nueva maquinaria",
            "✏️ Editar",
            "🗑️ Borrar"
        ],
        horizontal=True,
        key="maquinaria_seccion"
    )

    maquinaria = _leer_listado_maquinaria()

    if seccion == "📋 Listado":

        _render_listado(maquinaria)

    elif seccion == "➕ Nueva maquinaria":

        _render_nuevo()

    elif seccion == "✏️ Editar":

        _render_edicion(maquinaria)

    elif seccion == "🗑️ Borrar":

        _render_borrado(maquinaria)
