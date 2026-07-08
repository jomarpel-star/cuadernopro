from datetime import datetime

import pandas as pd
import streamlit as st

from core.borrado import borrar_registros_seguro
from core.db import conectar, leer
from core.fechas import formatear_columnas_fecha_es, parsear_fecha_es
from core.ui_tablas import (
    mapear_columnas_visuales_a_tecnicas,
    preparar_column_config_visual,
    preparar_dataframe_visual,
)


GRUPOS_EXPLOTACION = {
    "Datos del titular": [
        "titular",
        "nif",
        "direccion",
        "localidad",
        "codigo_postal",
        "provincia",
        "telefono",
        "email"
    ],
    "Datos de la explotación": [
        "nombre_explotacion",
        "identificador_oficial_visual",
        "registro_autonomico",
        "tipo_explotacion",
        "orientacion_productiva",
        "fecha_alta",
        "agricultor_activo",
        "joven_agricultor",
        "observaciones"
    ],
    "Responsable": [
        "responsable_nombre",
        "responsable_nif",
        "responsable_telefono"
    ],
    "Asesor": [
        "asesor_nombre",
        "asesor_nif",
        "asesor_numero_registro",
        "asesor_telefono"
    ]
}

COLUMNAS_EXPLOTACION = [
    "titular",
    "nif",
    "direccion",
    "localidad",
    "codigo_postal",
    "provincia",
    "telefono",
    "email",
    "nombre_explotacion",
    "identificador_oficial_visual",
    "registro_autonomico",
    "codigo_regea",
    "codigo_regepa",
    "tipo_explotacion",
    "orientacion_productiva",
    "fecha_alta",
    "agricultor_activo",
    "joven_agricultor",
    "responsable_nombre",
    "responsable_nif",
    "responsable_telefono",
    "asesor_nombre",
    "asesor_nif",
    "asesor_numero_registro",
    "asesor_telefono",
    "observaciones"
]

COLUMNAS_BOOLEANAS_EXPLOTACION = [
    "agricultor_activo",
    "joven_agricultor"
]

COLUMNAS_OPCIONALES_DATOS_EXPLOTACION = [
    "registro_autonomico",
    "tipo_explotacion",
    "orientacion_productiva",
    "fecha_alta",
    "agricultor_activo",
    "joven_agricultor",
]

ETIQUETAS_EXPLOTACION = {
    "id": "ID",
    "titular": "Titular",
    "nif": "NIF",
    "direccion": "Dirección",
    "localidad": "Municipio",
    "codigo_postal": "Código postal",
    "provincia": "Provincia",
    "telefono": "Teléfono",
    "email": "Email",
    "nombre_explotacion": "Nombre de la explotación",
    "identificador_oficial_visual": (
        "Código REGEPA / identificador oficial"
    ),
    "registro_autonomico": "Registro autonómico",
    "codigo_regea": "Código REGEA / identificador oficial",
    "codigo_regepa": "Código REGEPA / identificador oficial",
    "tipo_explotacion": "Tipo de explotación",
    "orientacion_productiva": "Orientación productiva",
    "fecha_alta": "Fecha de alta",
    "agricultor_activo": "Agricultor activo",
    "joven_agricultor": "Joven agricultor",
    "observaciones": "Observaciones",
    "responsable_nombre": "Responsable",
    "responsable_nif": "NIF responsable",
    "responsable_telefono": "Teléfono responsable",
    "asesor_nombre": "Asesor",
    "asesor_nif": "NIF asesor",
    "asesor_numero_registro": "Número de registro asesor",
    "asesor_telefono": "Teléfono asesor",
}


def _columnas_visuales_datos_explotacion(columnas=None):

    visuales = [
        "nombre_explotacion",
        "identificador_oficial_visual",
    ]
    visuales.extend(COLUMNAS_OPCIONALES_DATOS_EXPLOTACION)
    visuales.append("observaciones")
    return visuales


def _etiqueta_explotacion(columna):

    return ETIQUETAS_EXPLOTACION.get(columna, columna)


def _preparar_dataframe_editor_explotacion(datos_explotacion, columnas):

    columnas_grupo = ["id"] + columnas
    return datos_explotacion[columnas_grupo].rename(
        columns={
            columna: _etiqueta_explotacion(columna)
            for columna in columnas_grupo
        }
    )


def _preparar_dataframe_borrado_explotacion(datos_explotacion):

    columnas = _columnas_visuales_datos_explotacion()
    visual = _preparar_dataframe_editor_explotacion(
        datos_explotacion,
        columnas
    )
    return visual.rename(columns={"ID": "id"})


def _columnas_deshabilitadas_explotacion(columnas):

    columnas_reales = _columnas_tabla("explotacion")
    deshabilitadas = [_etiqueta_explotacion("id")]

    for columna in columnas:

        if columna in (
            "nombre_explotacion",
            "identificador_oficial_visual",
            "observaciones",
        ):

            continue

        if columna not in columnas_reales:

            deshabilitadas.append(_etiqueta_explotacion(columna))

    return deshabilitadas

ROLES_PERSONAS = [
    "Titular",
    "Representante",
    "Aplicador fitosanitario",
    "Asesor",
    "Operario"
]

COLUMNAS_PERSONAS = [
    "id",
    "nombre",
    "nif",
    "telefono",
    "email",
    "rol",
    "carnet_fitosanitario",
    "fecha_caducidad_carnet",
    "numero_asesor",
    "observaciones"
]

ETIQUETAS_PERSONAS = {
    "id": "ID",
    "nombre": "Nombre",
    "nif": "NIF",
    "telefono": "Teléfono",
    "email": "Email",
    "rol": "Rol",
    "carnet_fitosanitario": "Carnet aplicador",
    "fecha_caducidad_carnet": "Fecha caducidad carnet",
    "numero_asesor": "Nº asesor",
    "observaciones": "Observaciones",
}

def _columnas_visuales_personas(columnas=None):

    if columnas is None:

        columnas = _columnas_tabla("personas")

    visuales = [
        "id",
        "nombre",
        "nif",
        "telefono",
        "email",
        "rol",
        "carnet_fitosanitario",
    ]

    if "fecha_caducidad_carnet" in columnas:

        visuales.append("fecha_caducidad_carnet")

    visuales.extend(["numero_asesor", "observaciones"])
    return visuales


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

FECHAS_EQUIPOS = [
    "fecha_adquisicion",
    "fecha_ultima_inspeccion",
    "fecha_proxima_inspeccion"
]

ETIQUETAS_EQUIPOS = {
    "id": "ID",
    "nombre": "Nombre",
    "tipo": "Tipo",
    "marca": "Marca",
    "modelo": "Modelo",
    "matricula": "Matrícula",
    "numero_roma": "Nº ROMA",
    "numero_serie": "Número de serie",
    "fecha_adquisicion": "Fecha de adquisición",
    "fecha_ultima_inspeccion": "Fecha revisión",
    "fecha_proxima_inspeccion": "Próxima revisión",
    "capacidad_litros": "Capacidad litros",
    "observaciones": "Observaciones",
}


def _columnas_visuales_equipos(columnas=None):

    if columnas is None:

        columnas = _columnas_tabla("equipos_aplicacion")

    visuales = ["id", "nombre", "tipo", "marca", "modelo"]

    if "matricula" in columnas:

        visuales.append("matricula")

    if "numero_roma" in columnas:

        visuales.append("numero_roma")

    if "numero_serie" in columnas:

        visuales.append("numero_serie")

    if "fecha_adquisicion" in columnas:

        visuales.append("fecha_adquisicion")

    if (
        "fecha_revision" in columnas
        or "fecha_ultima_inspeccion" in columnas
    ):

        visuales.append("fecha_ultima_inspeccion")

    if (
        "fecha_proxima_revision" in columnas
        or "fecha_proxima_inspeccion" in columnas
    ):

        visuales.append("fecha_proxima_inspeccion")

    if "capacidad_litros" in columnas:

        visuales.append("capacidad_litros")

    visuales.append("observaciones")
    return visuales


def _fechas_visuales_equipos(columnas=None):

    return [
        columna
        for columna in FECHAS_EQUIPOS
        if columna in _columnas_visuales_equipos(columnas)
    ]


def _textos_visuales_equipos(columnas=None):

    return [
        columna
        for columna in (
            "nombre",
            "tipo",
            "marca",
            "modelo",
            "matricula",
            "numero_roma",
            "numero_serie",
            "observaciones",
        )
        if columna in _columnas_visuales_equipos(columnas)
    ]


def _columnas_tabla_conn(conn, tabla):

    tabla_existe = conn.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (tabla,)
    ).fetchone()

    if not tabla_existe:

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


def _expr_fecha(tabla, columna, columnas):

    if columna in columnas:

        return f"{tabla}.{columna}"

    return "NULL"


def _anadir_si_existe(destino, columnas, columna, valor):

    if columna in columnas:

        destino[columna] = valor


def _ejecutar_insert_dinamico(conn, tabla, valores):

    columnas = list(valores)

    if not columnas:

        return None

    marcadores = ",".join("?" for _ in columnas)
    cursor = conn.execute(
        f"""
        INSERT INTO {tabla}
        ({','.join(columnas)})
        VALUES ({marcadores})
        """,
        [valores[columna] for columna in columnas]
    )
    return cursor.lastrowid


def _ejecutar_update_dinamico(conn, tabla, registro_id, valores):

    columnas = list(valores)

    if not columnas:

        return

    asignaciones = ",".join(f"{columna}=?" for columna in columnas)
    conn.execute(
        f"""
        UPDATE {tabla}
        SET {asignaciones}
        WHERE id=?
        """,
        [valores[columna] for columna in columnas] + [int(registro_id)]
    )


def _texto_limpio(valor):

    if pd.isna(valor):

        return ""

    return str(valor).strip()


def _primer_texto(*valores):

    for valor in valores:

        texto = _texto_limpio(valor)

        if texto:

            return texto

    return ""


def _insertar_explotacion_vacia(columnas):

    ahora = datetime.now().isoformat(timespec="seconds")
    valores = {}

    for columna in (
        "titular",
        "nif",
        "direccion",
        "localidad",
        "municipio",
        "codigo_postal",
        "provincia",
        "telefono",
        "email",
        "observaciones",
    ):

        _anadir_si_existe(valores, columnas, columna, "")

    _anadir_si_existe(valores, columnas, "created_at", ahora)
    _anadir_si_existe(valores, columnas, "updated_at", ahora)

    conn = conectar()

    try:

        _ejecutar_insert_dinamico(conn, "explotacion", valores)
        conn.commit()

    finally:

        conn.close()


def _normalizar_alias_explotacion(datos_explotacion):

    if datos_explotacion.empty:

        return datos_explotacion

    if "nombre_explotacion" in datos_explotacion and "titular" in datos_explotacion:

        nombre = (
            datos_explotacion["nombre_explotacion"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        titular = (
            datos_explotacion["titular"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        datos_explotacion["nombre_explotacion"] = nombre.where(
            nombre != "",
            titular
        )

    if "municipio" in datos_explotacion:

        datos_explotacion["localidad"] = (
            datos_explotacion["municipio"]
            .fillna("")
            .astype(str)
        )

    identificador = pd.Series("", index=datos_explotacion.index)

    for columna in (
        "identificador_oficial",
        "codigo_regepa",
        "codigo_regea",
        "registro_explotacion",
    ):

        if columna in datos_explotacion:

            valores = (
                datos_explotacion[columna]
                .fillna("")
                .astype(str)
                .str.strip()
            )
            identificador = identificador.where(
                identificador.str.strip() != "",
                valores
            )

    datos_explotacion["identificador_oficial_visual"] = identificador

    for columna in ("codigo_regepa", "codigo_regea"):

        if columna not in datos_explotacion:

            datos_explotacion[columna] = ""

    if "responsable" in datos_explotacion:

        datos_explotacion["responsable_nombre"] = (
            datos_explotacion["responsable"]
            .fillna("")
            .astype(str)
        )

    if "asesor" in datos_explotacion:

        datos_explotacion["asesor_nombre"] = (
            datos_explotacion["asesor"]
            .fillna("")
            .astype(str)
        )

    if "numero_asesor" in datos_explotacion:

        datos_explotacion["asesor_numero_registro"] = (
            datos_explotacion["numero_asesor"]
            .fillna("")
            .astype(str)
        )

    return datos_explotacion


def _leer_datos_explotacion():

    columnas = _columnas_tabla("explotacion")
    datos_explotacion = leer(
        "SELECT * FROM explotacion ORDER BY id LIMIT 1"
    )

    if datos_explotacion.empty:

        _insertar_explotacion_vacia(columnas)
        datos_explotacion = leer(
            "SELECT * FROM explotacion ORDER BY id LIMIT 1"
        )

    datos_explotacion = _normalizar_alias_explotacion(
        datos_explotacion
    )

    for columna in COLUMNAS_EXPLOTACION:

        if columna not in datos_explotacion.columns:

            datos_explotacion[columna] = (
                0
                if columna in COLUMNAS_BOOLEANAS_EXPLOTACION
                else ""
            )

    datos_explotacion = datos_explotacion[
        ["id"] + COLUMNAS_EXPLOTACION
    ].copy()

    for columna in COLUMNAS_BOOLEANAS_EXPLOTACION:

        datos_explotacion[columna] = (
            datos_explotacion[columna]
            .fillna(0)
            .astype(bool)
        )

    datos_explotacion["fecha_alta"] = pd.to_datetime(
        datos_explotacion["fecha_alta"],
        errors="coerce"
    )

    for columna in COLUMNAS_EXPLOTACION:

        if (
            columna not in COLUMNAS_BOOLEANAS_EXPLOTACION
            and columna != "fecha_alta"
        ):

            datos_explotacion[columna] = (
                datos_explotacion[columna]
                .fillna("")
                .astype(str)
            )

    return datos_explotacion


def _leer_personas():

    columnas = _columnas_tabla("personas")
    expr_carnet = (
        _expr_texto("personas", "carnet_aplicador", columnas)
        if "carnet_aplicador" in columnas
        else _expr_texto("personas", "carnet_fitosanitario", columnas)
    )

    return leer(
        f"""
        SELECT
            personas.id,
            {_expr_texto("personas", "nombre", columnas)} AS nombre,
            {_expr_texto("personas", "nif", columnas)} AS nif,
            {_expr_texto("personas", "telefono", columnas)} AS telefono,
            {_expr_texto("personas", "email", columnas)} AS email,
            {_expr_texto("personas", "rol", columnas)} AS rol,
            {expr_carnet} AS carnet_fitosanitario,
            {_expr_fecha("personas", "fecha_caducidad_carnet", columnas)}
                AS fecha_caducidad_carnet,
            {_expr_texto("personas", "numero_asesor", columnas)}
                AS numero_asesor,
            {_expr_texto("personas", "observaciones", columnas)}
                AS observaciones
        FROM personas
        ORDER BY personas.id
        """
    )


def _leer_equipos():

    columnas = _columnas_tabla("equipos_aplicacion")
    expr_fecha_revision = (
        _expr_fecha("equipos_aplicacion", "fecha_revision", columnas)
        if "fecha_revision" in columnas
        else _expr_fecha(
            "equipos_aplicacion",
            "fecha_ultima_inspeccion",
            columnas
        )
    )
    expr_fecha_proxima_revision = (
        _expr_fecha(
            "equipos_aplicacion",
            "fecha_proxima_revision",
            columnas
        )
        if "fecha_proxima_revision" in columnas
        else _expr_fecha(
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
            {_expr_texto("equipos_aplicacion", "tipo", columnas)}
                AS tipo,
            {_expr_texto("equipos_aplicacion", "marca", columnas)}
                AS marca,
            {_expr_texto("equipos_aplicacion", "modelo", columnas)}
                AS modelo,
            {_expr_texto("equipos_aplicacion", "matricula", columnas)}
                AS matricula,
            {_expr_texto("equipos_aplicacion", "numero_roma", columnas)}
                AS numero_roma,
            {_expr_texto("equipos_aplicacion", "numero_serie", columnas)}
                AS numero_serie,
            {_expr_fecha("equipos_aplicacion", "fecha_adquisicion", columnas)}
                AS fecha_adquisicion,
            {expr_fecha_revision} AS fecha_ultima_inspeccion,
            {expr_fecha_proxima_revision} AS fecha_proxima_inspeccion,
            {_expr_fecha("equipos_aplicacion", "capacidad_litros", columnas)}
                AS capacidad_litros,
            {_expr_texto("equipos_aplicacion", "observaciones", columnas)}
                AS observaciones
        FROM equipos_aplicacion
        ORDER BY equipos_aplicacion.id
        """
    )


def _normalizar_explotacion(dataframe):

    resultado = dataframe.copy()

    for columna in COLUMNAS_EXPLOTACION:

        if columna in COLUMNAS_BOOLEANAS_EXPLOTACION:

            resultado[columna] = (
                resultado[columna]
                .fillna(False)
                .astype(bool)
            )

        elif columna == "fecha_alta":

            resultado[columna] = pd.to_datetime(
                resultado[columna],
                errors="coerce"
            )

        else:

            resultado[columna] = (
                resultado[columna]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    return resultado


def _valores_distintos(valor_nuevo, valor_original):

    if pd.isna(valor_nuevo) and pd.isna(valor_original):

        return False

    return valor_nuevo != valor_original


def _guardar_explotacion(
    datos_explotacion,
    explotacion_editada,
    columnas_revision
):

    explotacion_para_guardar = _normalizar_explotacion(
        explotacion_editada
    )
    explotacion_original = _normalizar_explotacion(
        datos_explotacion
    )

    fila = explotacion_para_guardar.iloc[0]
    original = explotacion_original.iloc[0]

    if not _texto_limpio(fila["nombre_explotacion"]):

        fila["nombre_explotacion"] = _texto_limpio(fila["titular"])

    cambios = any(
        _valores_distintos(fila[columna], original[columna])
        for columna in columnas_revision
    )

    if not cambios:

        st.info("No había cambios para guardar")
        return False

    fecha_alta = None

    if not pd.isna(fila["fecha_alta"]):

        fecha_alta = pd.to_datetime(
            fila["fecha_alta"]
        ).date().isoformat()

    columnas = _columnas_tabla("explotacion")
    valores = {}
    identificador = _primer_texto(
        fila["identificador_oficial_visual"],
        fila["codigo_regepa"],
        fila["codigo_regea"]
    )
    tipo_identificador = ""

    if _texto_limpio(fila["identificador_oficial_visual"]):

        tipo_identificador = "REGEPA"

    elif _texto_limpio(fila["codigo_regepa"]):

        tipo_identificador = "REGEPA"

    elif _texto_limpio(fila["codigo_regea"]):

        tipo_identificador = "REGEA"

    for columna in (
        "titular",
        "nif",
        "direccion",
        "codigo_postal",
        "provincia",
        "telefono",
        "email",
        "nombre_explotacion",
        "registro_autonomico",
        "tipo_explotacion",
        "orientacion_productiva",
        "responsable_nif",
        "responsable_telefono",
        "asesor_nif",
        "asesor_telefono",
        "observaciones",
    ):

        _anadir_si_existe(valores, columnas, columna, fila[columna])

    _anadir_si_existe(valores, columnas, "localidad", fila["localidad"])
    _anadir_si_existe(valores, columnas, "municipio", fila["localidad"])
    _anadir_si_existe(valores, columnas, "codigo_regea", identificador)
    _anadir_si_existe(valores, columnas, "codigo_regepa", identificador)
    _anadir_si_existe(
        valores,
        columnas,
        "registro_explotacion",
        identificador
    )
    _anadir_si_existe(
        valores,
        columnas,
        "identificador_oficial",
        identificador
    )
    _anadir_si_existe(
        valores,
        columnas,
        "tipo_identificador_oficial",
        tipo_identificador
    )
    _anadir_si_existe(valores, columnas, "fecha_alta", fecha_alta)
    _anadir_si_existe(
        valores,
        columnas,
        "agricultor_activo",
        int(bool(fila["agricultor_activo"]))
    )
    _anadir_si_existe(
        valores,
        columnas,
        "joven_agricultor",
        int(bool(fila["joven_agricultor"]))
    )
    _anadir_si_existe(
        valores,
        columnas,
        "responsable_nombre",
        fila["responsable_nombre"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "responsable",
        fila["responsable_nombre"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "asesor_nombre",
        fila["asesor_nombre"]
    )
    _anadir_si_existe(valores, columnas, "asesor", fila["asesor_nombre"])
    _anadir_si_existe(
        valores,
        columnas,
        "asesor_numero_registro",
        fila["asesor_numero_registro"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "numero_asesor",
        fila["asesor_numero_registro"]
    )
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
            "explotacion",
            int(fila["id"]),
            valores
        )
        conn.commit()

    finally:

        conn.close()

    return True


def _config_explotacion():

    return {
        "ID": st.column_config.NumberColumn(
            "ID",
            disabled=True
        ),
        "Titular": st.column_config.TextColumn("Titular"),
        "NIF": st.column_config.TextColumn("NIF"),
        "Dirección": st.column_config.TextColumn("Dirección"),
        "Municipio": st.column_config.TextColumn("Municipio"),
        "Código postal": st.column_config.TextColumn("Código postal"),
        "Provincia": st.column_config.TextColumn("Provincia"),
        "Teléfono": st.column_config.TextColumn("Teléfono"),
        "Email": st.column_config.TextColumn("Email"),
        "Nombre de la explotación": st.column_config.TextColumn(
            "Nombre de la explotación"
        ),
        "Código REGEPA / identificador oficial": st.column_config.TextColumn(
            "Código REGEPA / identificador oficial"
        ),
        "Registro autonómico": st.column_config.TextColumn(
            "Registro autonómico"
        ),
        "Tipo de explotación": st.column_config.TextColumn(
            "Tipo de explotación"
        ),
        "Orientación productiva": st.column_config.TextColumn(
            "Orientación productiva"
        ),
        "Fecha de alta": st.column_config.DateColumn(
            "Fecha de alta",
            format="DD/MM/YYYY"
        ),
        "Agricultor activo": st.column_config.CheckboxColumn(
            "Agricultor activo"
        ),
        "Joven agricultor": st.column_config.CheckboxColumn(
            "Joven agricultor"
        ),
        "Observaciones": st.column_config.TextColumn("Observaciones"),
        "Responsable": st.column_config.TextColumn("Responsable"),
        "NIF responsable": st.column_config.TextColumn("NIF responsable"),
        "Teléfono responsable": st.column_config.TextColumn(
            "Teléfono responsable"
        ),
        "Asesor": st.column_config.TextColumn("Asesor"),
        "NIF asesor": st.column_config.TextColumn("NIF asesor"),
        "Número de registro asesor": st.column_config.TextColumn(
            "Número de registro asesor"
        ),
        "Teléfono asesor": st.column_config.TextColumn("Teléfono asesor"),
    }


def _editar_columnas_explotacion(
    datos_explotacion,
    columnas,
    key_editor
):

    editor = _preparar_dataframe_editor_explotacion(
        datos_explotacion,
        columnas
    )
    columnas_visuales = list(editor.columns)

    return st.data_editor(
        editor,
        num_rows="fixed",
        disabled=_columnas_deshabilitadas_explotacion(columnas),
        hide_index=True,
        use_container_width=True,
        column_order=columnas_visuales,
        column_config=_config_explotacion(),
        key=key_editor
    )


def _editar_columnas_explotacion_interno(
    datos_explotacion,
    columnas,
    key_editor
):

    columnas_editor = [
        columna
        for columna in ["id"] + columnas
        if columna in datos_explotacion.columns
    ]
    editor = datos_explotacion[columnas_editor].copy()

    return st.data_editor(
        editor,
        num_rows="fixed",
        disabled=["id"],
        hide_index=True,
        use_container_width=True,
        column_order=columnas_editor,
        column_config=preparar_column_config_visual(
            editor,
            etiquetas=ETIQUETAS_EXPLOTACION
        ),
        key=key_editor
    )


def _render_editor_explotacion(
    datos_explotacion,
    titulo,
    columnas,
    key_prefix
):

    st.subheader(titulo)

    vista_grupo = _preparar_dataframe_editor_explotacion(
        datos_explotacion,
        columnas
    )
    st.dataframe(
        vista_grupo.drop(columns=["ID"], errors="ignore"),
        hide_index=True,
        use_container_width=True
    )

    explotacion_editada = datos_explotacion.copy()

    with st.expander(f"Editar {titulo.lower()}"):

        version_key = f"{key_prefix}_editor_version"

        if version_key not in st.session_state:

            st.session_state[version_key] = 0

        editor_version = st.session_state[version_key]
        editado_grupo = _editar_columnas_explotacion(
            datos_explotacion,
            columnas,
            f"{key_prefix}_editor_v7_campos_limpios_v2_{editor_version}"
        )

        for columna in columnas:

            explotacion_editada[columna] = editado_grupo[
                _etiqueta_explotacion(columna)
            ]

        confirmar_cambios = st.checkbox(
            "Confirmo que quiero guardar los cambios",
            key=f"{key_prefix}_confirmar_cambios_{editor_version}"
        )

        if st.button(
            "💾 Guardar cambios",
            key=f"{key_prefix}_guardar_cambios_{editor_version}"
        ):

            if not confirmar_cambios:

                st.warning(
                    "Marca la confirmación antes de guardar los cambios"
                )

            else:

                if _guardar_explotacion(
                    datos_explotacion,
                    explotacion_editada,
                    columnas
                ):

                    st.session_state["mensaje_explotacion_guardado"] = (
                        "Filas actualizadas: 1"
                    )
                    st.session_state[version_key] += 1
                    st.rerun()

    return explotacion_editada


def _render_resumen(datos_explotacion, personas, equipos):

    st.subheader("Resumen de explotación")

    fila = datos_explotacion.iloc[0]
    titular_configurado = bool(_texto_limpio(fila["titular"]))
    datos_minimos_explotacion = (
        _texto_limpio(fila["nombre_explotacion"])
        and _texto_limpio(fila["identificador_oficial_visual"])
    )

    if "tipo_explotacion" in _columnas_tabla("explotacion"):

        datos_minimos_explotacion = (
            datos_minimos_explotacion
            and _texto_limpio(fila["tipo_explotacion"])
        )

    datos_explotacion_completos = bool(datos_minimos_explotacion)
    responsable_configurado = bool(
        _texto_limpio(fila["responsable_nombre"])
    )
    asesor_configurado = bool(
        _texto_limpio(fila["asesor_nombre"])
        or _texto_limpio(fila["asesor_nif"])
    )

    total_personas = len(personas)
    total_equipos = len(equipos)

    columnas = st.columns(3)
    columnas[0].metric(
        "Titular configurado",
        "Sí" if titular_configurado else "No"
    )
    columnas[1].metric(
        "Datos explotación",
        "Completos" if datos_explotacion_completos else "Incompletos"
    )
    columnas[2].metric(
        "Responsable",
        "Sí" if responsable_configurado else "No"
    )

    columnas = st.columns(3)
    columnas[0].metric(
        "Asesor",
        "Sí" if asesor_configurado else "No"
    )
    columnas[1].metric(
        "Personas relacionadas",
        total_personas
    )
    columnas[2].metric(
        "Equipos aplicación fito",
        total_equipos
    )

    codigo_oficial = _texto_limpio(fila["identificador_oficial_visual"])
    nombre_explotacion_resumen = (
        _texto_limpio(fila["nombre_explotacion"])
        or _texto_limpio(fila["titular"])
    )
    resumen = pd.DataFrame(
        [
            {
                "Nombre de la explotación": (
                    nombre_explotacion_resumen or "—"
                ),
                "Titular": _texto_limpio(fila["titular"]) or "—",
                "NIF": _texto_limpio(fila["nif"]) or "—",
                "Código REGEPA / identificador oficial": (
                    codigo_oficial or "—"
                ),
                "Municipio": _texto_limpio(fila["localidad"]) or "—",
                "Provincia": _texto_limpio(fila["provincia"]) or "—",
            }
        ]
    )
    st.dataframe(
        preparar_dataframe_visual(resumen, ocultar_tecnicas=False),
        hide_index=True,
        use_container_width=True
    )

    avisos = []

    if not _texto_limpio(fila["nif"]):

        avisos.append("Falta NIF del titular")

    if not _texto_limpio(fila["identificador_oficial_visual"]):

        avisos.append("Falta registro explotación")

    if not asesor_configurado:

        avisos.append("No hay asesor asignado")

    if personas.empty:

        avisos.append("No hay personas relacionadas")

    if equipos.empty:

        avisos.append("No hay equipos de aplicación fito")

    if avisos:

        for aviso in avisos:

            st.warning(aviso)

    else:

        st.success("La explotación tiene los datos principales configurados")


def _render_titular(datos_explotacion):

    _render_editor_explotacion(
        datos_explotacion,
        "Datos del titular",
        GRUPOS_EXPLOTACION["Datos del titular"],
        "explotacion_titular"
    )


def _render_datos_explotacion(datos_explotacion):

    columnas = _columnas_visuales_datos_explotacion()
    _render_editor_explotacion(
        datos_explotacion,
        "Datos de la explotación",
        columnas,
        "explotacion_datos"
    )

    borrar_registros_seguro(
        "explotacion",
        "id",
        _preparar_dataframe_borrado_explotacion(datos_explotacion),
        "datos de explotación",
        campo_descripcion="Nombre de la explotación",
        key="explotacion_datos_limpio"
    )


def _guardar_asesor_explotacion(
    explotacion_id,
    nombre,
    nif,
    numero_asesor,
    telefono
):

    columnas = _columnas_tabla("explotacion")
    valores = {}

    _anadir_si_existe(valores, columnas, "asesor_nombre", nombre)
    _anadir_si_existe(valores, columnas, "asesor_nif", nif)
    _anadir_si_existe(
        valores,
        columnas,
        "asesor_numero_registro",
        numero_asesor
    )
    _anadir_si_existe(valores, columnas, "asesor_telefono", telefono)
    _anadir_si_existe(valores, columnas, "asesor", nombre)
    _anadir_si_existe(valores, columnas, "numero_asesor", numero_asesor)
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
            "explotacion",
            explotacion_id,
            valores
        )
        conn.commit()

    finally:

        conn.close()


def _render_asesor_acciones(datos_explotacion):

    asesores_personas = leer(
        """
        SELECT id,nombre,nif,telefono,numero_asesor
        FROM personas
        WHERE rol = ?
        ORDER BY nombre,id
        """,
        ("Asesor",)
    )

    fila_explotacion = datos_explotacion.iloc[0]
    explotacion_id = int(fila_explotacion["id"])
    asesor_nombre_actual = _texto_limpio(
        fila_explotacion["asesor_nombre"]
    )
    asesor_nif_actual = _texto_limpio(
        fila_explotacion["asesor_nif"]
    )
    asesor_relleno = bool(
        asesor_nombre_actual
        or asesor_nif_actual
    )

    existe_asesor = False

    if asesor_relleno and not asesores_personas.empty:

        if asesor_nif_actual:

            existe_asesor = (
                asesores_personas["nif"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.casefold()
                .eq(asesor_nif_actual.casefold())
                .any()
            )

        elif asesor_nombre_actual:

            existe_asesor = (
                asesores_personas["nombre"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.casefold()
                .eq(asesor_nombre_actual.casefold())
                .any()
            )

    if asesor_relleno and not existe_asesor:

        st.warning(
            "⚠️ El asesor indicado en la explotación no existe en "
            "Personas. Puede haber sido borrado."
        )

    if st.button(
        "Limpiar asesor de la explotación",
        key="explotacion_asesor_limpiar",
        disabled=not asesor_relleno
    ):

        _guardar_asesor_explotacion(
            explotacion_id,
            "",
            "",
            "",
            ""
        )

        st.session_state["mensaje_asesor_explotacion"] = (
            "Asesor de la explotación limpiado."
        )
        st.rerun()

    if asesores_personas.empty:

        st.info("No hay personas con rol Asesor para asignar")
        return

    opciones_asesor = (
        asesores_personas["id"]
        .astype(int)
        .tolist()
    )

    def etiqueta_asesor(asesor_id):

        asesor = asesores_personas[
            asesores_personas["id"].astype(int) == asesor_id
        ].iloc[0]
        nombre = _texto_limpio(asesor["nombre"])
        nif = _texto_limpio(asesor["nif"])

        if nif:

            return f"{nombre} ({nif})"

        return nombre

    asesor_id_seleccionado = st.selectbox(
        "Asignar asesor desde Personas",
        opciones_asesor,
        format_func=etiqueta_asesor,
        key="explotacion_asesor_persona"
    )

    if st.button(
        "Asignar asesor",
        key="explotacion_asesor_asignar"
    ):

        asesor = asesores_personas[
            asesores_personas["id"].astype(int)
            == int(asesor_id_seleccionado)
        ].iloc[0]

        _guardar_asesor_explotacion(
            explotacion_id,
            _texto_limpio(asesor["nombre"]),
            _texto_limpio(asesor["nif"]),
            _texto_limpio(asesor["numero_asesor"]),
            _texto_limpio(asesor["telefono"])
        )

        st.session_state["mensaje_asesor_explotacion"] = (
            "Asesor asignado a la explotación."
        )
        st.rerun()


def _render_responsable_asesor(datos_explotacion):

    st.subheader("Responsable")
    version_key = "explotacion_asesor_editor_version"

    if version_key not in st.session_state:

        st.session_state[version_key] = 0

    editor_version = st.session_state[version_key]

    columnas_responsable = GRUPOS_EXPLOTACION["Responsable"]
    editado_responsable = _editar_columnas_explotacion_interno(
        datos_explotacion,
        columnas_responsable,
        f"explotacion_asesor_responsable_editor_interno_v7_{editor_version}"
    )

    st.subheader("Asesor")

    columnas_asesor = GRUPOS_EXPLOTACION["Asesor"]
    editado_asesor = _editar_columnas_explotacion_interno(
        datos_explotacion,
        columnas_asesor,
        f"explotacion_asesor_editor_interno_v7_{editor_version}"
    )

    explotacion_editada = datos_explotacion.copy()

    for columna in columnas_responsable:

        explotacion_editada[columna] = editado_responsable[columna]

    for columna in columnas_asesor:

        explotacion_editada[columna] = editado_asesor[columna]

    _render_asesor_acciones(datos_explotacion)

    confirmar_cambios = st.checkbox(
        "Confirmo que quiero guardar los cambios",
        key=f"explotacion_asesor_confirmar_cambios_{editor_version}"
    )

    if st.button(
        "💾 Guardar cambios",
        key=f"explotacion_asesor_guardar_cambios_{editor_version}"
    ):

        if not confirmar_cambios:

            st.warning(
                "Marca la confirmación antes de guardar los cambios"
            )

        else:

            if _guardar_explotacion(
                datos_explotacion,
                explotacion_editada,
                columnas_responsable + columnas_asesor
            ):

                st.session_state["mensaje_explotacion_guardado"] = (
                    "Filas actualizadas: 1"
                )
                st.session_state[version_key] += 1
                st.rerun()


def _insertar_persona(datos):

    columnas = _columnas_tabla("personas")
    ahora = datetime.now().isoformat(timespec="seconds")
    valores = {}

    for columna in (
        "nombre",
        "nif",
        "telefono",
        "email",
        "rol",
        "numero_asesor",
        "observaciones",
    ):

        _anadir_si_existe(valores, columnas, columna, datos.get(columna))

    carnet = datos.get("carnet_fitosanitario")
    _anadir_si_existe(valores, columnas, "carnet_fitosanitario", carnet)
    _anadir_si_existe(valores, columnas, "carnet_aplicador", carnet)
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_caducidad_carnet",
        datos.get("fecha_caducidad_carnet")
    )
    _anadir_si_existe(valores, columnas, "created_at", ahora)
    _anadir_si_existe(valores, columnas, "updated_at", ahora)

    conn = conectar()

    try:

        _ejecutar_insert_dinamico(conn, "personas", valores)
        conn.commit()

    finally:

        conn.close()


def _actualizar_persona(conn, fila, fecha_caducidad):

    columnas = _columnas_tabla_conn(conn, "personas")
    valores = {}

    for columna in (
        "nombre",
        "nif",
        "telefono",
        "email",
        "rol",
        "numero_asesor",
        "observaciones",
    ):

        _anadir_si_existe(valores, columnas, columna, fila[columna])

    _anadir_si_existe(
        valores,
        columnas,
        "carnet_fitosanitario",
        fila["carnet_fitosanitario"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "carnet_aplicador",
        fila["carnet_fitosanitario"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_caducidad_carnet",
        fecha_caducidad
    )
    _anadir_si_existe(
        valores,
        columnas,
        "updated_at",
        datetime.now().isoformat(timespec="seconds")
    )

    _ejecutar_update_dinamico(
        conn,
        "personas",
        int(fila["id"]),
        valores
    )


def _render_personas():

    st.subheader("1.2 Personas relacionadas")

    if "explotacion_personas_form_version" not in st.session_state:

        st.session_state["explotacion_personas_form_version"] = 0

    form_persona_version = st.session_state[
        "explotacion_personas_form_version"
    ]
    columnas_personas = _columnas_tabla("personas")

    with st.form(f"explotacion_personas_nueva_v{form_persona_version}"):

        st.markdown("Nueva persona")

        persona_nombre = st.text_input(
            "Nombre",
            key=f"explotacion_personas_nueva_nombre_{form_persona_version}"
        )
        persona_nif = st.text_input(
            "NIF",
            key=f"explotacion_personas_nueva_nif_{form_persona_version}"
        )
        persona_telefono = st.text_input(
            "Teléfono",
            key=f"explotacion_personas_nueva_telefono_{form_persona_version}"
        )
        persona_email = st.text_input(
            "Email",
            key=f"explotacion_personas_nueva_email_{form_persona_version}"
        )
        persona_rol = st.selectbox(
            "Rol",
            ROLES_PERSONAS,
            key=f"explotacion_personas_nueva_rol_{form_persona_version}"
        )
        persona_carnet = st.text_input(
            "Carnet fitosanitario",
            key=f"explotacion_personas_nueva_carnet_{form_persona_version}"
        )
        persona_fecha_caducidad = ""

        if "fecha_caducidad_carnet" in columnas_personas:

            persona_fecha_caducidad = st.text_input(
                "Fecha caducidad carnet",
                placeholder="DD/MM/AAAA",
                key=(
                    "explotacion_personas_nueva_fecha_caducidad_"
                    f"{form_persona_version}"
                )
            )

        persona_numero_asesor = st.text_input(
            "Número de asesor",
            key=f"explotacion_personas_nueva_numero_asesor_{form_persona_version}"
        )
        persona_observaciones = st.text_area(
            "Observaciones",
            key=(
                "explotacion_personas_nueva_observaciones_"
                f"{form_persona_version}"
            )
        )

        if st.form_submit_button("Añadir persona"):

            persona_nombre = persona_nombre.strip()
            persona_rol = persona_rol.strip()
            persona_carnet = persona_carnet.strip()
            persona_numero_asesor = persona_numero_asesor.strip()

            if not persona_nombre or not persona_rol:

                st.error("Nombre y rol son obligatorios")

            else:

                if (
                    persona_rol == "Aplicador fitosanitario"
                    and not persona_carnet
                ):

                    st.warning(
                        "Aplicador fitosanitario sin carnet informado"
                    )

                if persona_rol == "Asesor" and not persona_numero_asesor:

                    st.warning("Asesor sin número de asesor informado")

                try:

                    fecha_caducidad = (
                        parsear_fecha_es(persona_fecha_caducidad)
                        if "fecha_caducidad_carnet" in columnas_personas
                        else None
                    )

                except ValueError:

                    st.error("La fecha debe tener formato DD/MM/AAAA")

                else:

                    _insertar_persona(
                        {
                            "nombre": persona_nombre,
                            "nif": persona_nif.strip(),
                            "telefono": persona_telefono.strip(),
                            "email": persona_email.strip(),
                            "rol": persona_rol,
                            "carnet_fitosanitario": persona_carnet,
                            "fecha_caducidad_carnet": fecha_caducidad,
                            "numero_asesor": persona_numero_asesor,
                            "observaciones": persona_observaciones.strip()
                        }
                    )

                    st.success("Persona añadida")
                    st.session_state[
                        "explotacion_personas_form_version"
                    ] += 1
                    st.rerun()

    personas = _leer_personas()

    if personas.empty:

        st.info("No hay personas relacionadas registradas")

    else:

        if "explotacion_personas_editor_version" not in st.session_state:

            st.session_state["explotacion_personas_editor_version"] = 0

        personas_editor_version = st.session_state[
            "explotacion_personas_editor_version"
        ]
        personas_editor = personas.copy()
        columnas_visuales_personas = _columnas_visuales_personas(
            columnas_personas
        )
        columnas_visuales_personas = [
            columna
            for columna in columnas_visuales_personas
            if columna in personas_editor.columns
        ]

        if "fecha_caducidad_carnet" in columnas_visuales_personas:

            personas_editor["fecha_caducidad_carnet"] = pd.to_datetime(
                personas_editor["fecha_caducidad_carnet"],
                errors="coerce"
            )

        personas_editor_visual = personas_editor[
            columnas_visuales_personas
        ].rename(columns=ETIQUETAS_PERSONAS)
        personas_editadas_visual = st.data_editor(
            personas_editor_visual,
            num_rows="fixed",
            disabled=["ID"],
            hide_index=True,
            use_container_width=True,
            column_order=[
                ETIQUETAS_PERSONAS.get(columna, columna)
                for columna in columnas_visuales_personas
            ],
            column_config={
                "ID": st.column_config.NumberColumn(
                    "ID",
                    disabled=True
                ),
                "Rol": st.column_config.SelectboxColumn(
                    "Rol",
                    options=ROLES_PERSONAS,
                    required=True
                ),
                "Fecha caducidad carnet": st.column_config.DateColumn(
                    "Fecha caducidad carnet",
                    format="DD/MM/YYYY"
                )
            },
            key=f"explotacion_personas_editor_v7_etiquetas_{personas_editor_version}"
        )
        personas_editadas = mapear_columnas_visuales_a_tecnicas(
            personas_editadas_visual,
            etiquetas_extra=ETIQUETAS_PERSONAS
        )

        confirmar_cambios_personas = st.checkbox(
            "Confirmo que quiero guardar los cambios de personas",
            key=(
                "explotacion_personas_confirmar_cambios_"
                f"{personas_editor_version}"
            )
        )

        if st.button(
            "💾 Guardar cambios de personas",
            key=(
                "explotacion_personas_guardar_cambios_"
                f"{personas_editor_version}"
            )
        ):

            errores_personas = []
            personas_guardar = personas_editadas.copy()

            if len(personas_guardar) != len(personas):

                errores_personas.append(
                    "No se permite borrar personas desde el editor"
                )

            for columna in [
                "nombre",
                "nif",
                "telefono",
                "email",
                "rol",
                "carnet_fitosanitario",
                "numero_asesor",
                "observaciones"
            ]:

                personas_guardar[columna] = (
                    personas_guardar[columna]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

            if (personas_guardar["nombre"] == "").any():

                errores_personas.append("El nombre no puede estar vacío")

            if (personas_guardar["rol"] == "").any():

                errores_personas.append("El rol no puede estar vacío")

            roles_invalidos = ~personas_guardar["rol"].isin(ROLES_PERSONAS)

            if roles_invalidos.any():

                errores_personas.append("Hay personas con un rol no válido")

            aplicadores_sin_carnet = (
                (personas_guardar["rol"] == "Aplicador fitosanitario")
                & (personas_guardar["carnet_fitosanitario"] == "")
            )

            if aplicadores_sin_carnet.any():

                st.warning(
                    "Hay aplicadores fitosanitarios sin carnet informado"
                )

            asesores_sin_numero = (
                (personas_guardar["rol"] == "Asesor")
                & (personas_guardar["numero_asesor"] == "")
            )

            if asesores_sin_numero.any():

                st.warning("Hay asesores sin número de asesor informado")

            if not confirmar_cambios_personas:

                errores_personas.append(
                    "Marca la confirmación antes de guardar las personas"
                )

            if errores_personas:

                for error in errores_personas:

                    st.error(error)

            else:

                conn = conectar()

                for _, fila in personas_guardar.iterrows():

                    fecha_caducidad = None

                    if (
                        "fecha_caducidad_carnet" in personas_guardar.columns
                        and not pd.isna(fila["fecha_caducidad_carnet"])
                    ):

                        fecha_caducidad = pd.to_datetime(
                            fila["fecha_caducidad_carnet"]
                        ).date().isoformat()

                    _actualizar_persona(conn, fila, fecha_caducidad)

                conn.commit()
                conn.close()

                st.session_state["mensaje_explotacion_guardado"] = (
                    "Cambios de personas guardados"
                )
                st.session_state[
                    "explotacion_personas_editor_version"
                ] += 1
                st.rerun()

    borrar_registros_seguro(
        "personas",
        "id",
        personas,
        "personas",
        bloqueos=[
            (
                "tratamientos",
                "aplicador_id",
                "la persona está usada en tratamientos"
            ),
            (
                "fertilizaciones",
                "operario_id",
                "la persona está usada en fertilizaciones"
            ),
            (
                "practicas_culturales",
                "operario_id",
                "la persona está usada en prácticas culturales"
            )
        ],
        campo_descripcion="nombre",
        key="explotacion_personas"
    )


def _insertar_equipo(datos):

    columnas = _columnas_tabla("equipos_aplicacion")
    ahora = datetime.now().isoformat(timespec="seconds")
    valores = {}

    for columna in (
        "nombre",
        "tipo",
        "marca",
        "modelo",
        "matricula",
        "numero_roma",
        "numero_serie",
        "fecha_adquisicion",
        "capacidad_litros",
        "observaciones",
    ):

        _anadir_si_existe(valores, columnas, columna, datos.get(columna))

    fecha_revision = datos.get("fecha_ultima_inspeccion")
    fecha_proxima_revision = datos.get("fecha_proxima_inspeccion")
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_ultima_inspeccion",
        fecha_revision
    )
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_revision",
        fecha_revision
    )
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_proxima_inspeccion",
        fecha_proxima_revision
    )
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_proxima_revision",
        fecha_proxima_revision
    )
    _anadir_si_existe(valores, columnas, "created_at", ahora)
    _anadir_si_existe(valores, columnas, "updated_at", ahora)

    conn = conectar()

    try:

        _ejecutar_insert_dinamico(conn, "equipos_aplicacion", valores)
        conn.commit()

    finally:

        conn.close()


def _actualizar_equipo(conn, fila, fechas_guardar, capacidad_litros):

    columnas = _columnas_tabla_conn(conn, "equipos_aplicacion")
    valores = {}

    for columna in (
        "nombre",
        "tipo",
        "marca",
        "modelo",
        "matricula",
        "numero_roma",
        "numero_serie",
        "observaciones",
    ):

        _anadir_si_existe(valores, columnas, columna, fila.get(columna, ""))

    _anadir_si_existe(
        valores,
        columnas,
        "fecha_adquisicion",
        fechas_guardar["fecha_adquisicion"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_ultima_inspeccion",
        fechas_guardar["fecha_ultima_inspeccion"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_revision",
        fechas_guardar["fecha_ultima_inspeccion"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_proxima_inspeccion",
        fechas_guardar["fecha_proxima_inspeccion"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "fecha_proxima_revision",
        fechas_guardar["fecha_proxima_inspeccion"]
    )
    _anadir_si_existe(
        valores,
        columnas,
        "capacidad_litros",
        capacidad_litros
    )
    _anadir_si_existe(
        valores,
        columnas,
        "updated_at",
        datetime.now().isoformat(timespec="seconds")
    )

    _ejecutar_update_dinamico(
        conn,
        "equipos_aplicacion",
        int(fila["id"]),
        valores
    )


def _render_equipos():

    st.subheader(
        "1.3 Equipos de aplicación de productos fitosanitarios"
    )

    if "explotacion_equipos_form_version" not in st.session_state:

        st.session_state["explotacion_equipos_form_version"] = 0

    form_equipo_aplicacion_version = st.session_state[
        "explotacion_equipos_form_version"
    ]
    columnas_equipos = _columnas_tabla("equipos_aplicacion")

    with st.form(
        f"explotacion_equipos_nuevo_v{form_equipo_aplicacion_version}"
    ):

        st.markdown("Nuevo equipo")

        equipo_nombre = st.text_input(
            "Nombre",
            key=f"explotacion_equipos_nuevo_nombre_{form_equipo_aplicacion_version}"
        )
        equipo_tipo = st.text_input(
            "Tipo",
            key=f"explotacion_equipos_nuevo_tipo_{form_equipo_aplicacion_version}"
        )
        equipo_marca = st.text_input(
            "Marca",
            key=f"explotacion_equipos_nuevo_marca_{form_equipo_aplicacion_version}"
        )
        equipo_modelo = st.text_input(
            "Modelo",
            key=f"explotacion_equipos_nuevo_modelo_{form_equipo_aplicacion_version}"
        )
        equipo_matricula = ""

        if "matricula" in columnas_equipos:

            equipo_matricula = st.text_input(
                "Matrícula",
                key=(
                    "explotacion_equipos_nuevo_matricula_"
                    f"{form_equipo_aplicacion_version}"
                )
            )

        equipo_numero_roma = ""

        if "numero_roma" in columnas_equipos:

            equipo_numero_roma = st.text_input(
                "Nº ROMA",
                key=(
                    "explotacion_equipos_nuevo_numero_roma_"
                    f"{form_equipo_aplicacion_version}"
                )
            )

        equipo_numero_serie = ""

        if "numero_serie" in columnas_equipos:

            equipo_numero_serie = st.text_input(
                "Número de serie",
                key=(
                    "explotacion_equipos_nuevo_numero_serie_"
                    f"{form_equipo_aplicacion_version}"
                )
            )

        equipo_fecha_adquisicion = ""

        if "fecha_adquisicion" in columnas_equipos:

            equipo_fecha_adquisicion = st.text_input(
                "Fecha de adquisición",
                placeholder="DD/MM/AAAA",
                key=(
                    "explotacion_equipos_nuevo_fecha_adquisicion_"
                    f"{form_equipo_aplicacion_version}"
                )
            )

        equipo_fecha_ultima_inspeccion = st.text_input(
            "Fecha revisión",
            placeholder="DD/MM/AAAA",
            key=(
                "explotacion_equipos_nuevo_fecha_ultima_inspeccion_"
                f"{form_equipo_aplicacion_version}"
            )
        )
        equipo_fecha_proxima_inspeccion = st.text_input(
            "Fecha próxima revisión",
            placeholder="DD/MM/AAAA",
            key=(
                "explotacion_equipos_nuevo_fecha_proxima_inspeccion_"
                f"{form_equipo_aplicacion_version}"
            )
        )

        equipo_capacidad_litros = 0.0

        if "capacidad_litros" in columnas_equipos:

            equipo_capacidad_litros = st.number_input(
                "Capacidad litros",
                min_value=0.0,
                value=0.0,
                key=(
                    "explotacion_equipos_nuevo_capacidad_litros_"
                    f"{form_equipo_aplicacion_version}"
                )
            )

        equipo_observaciones = st.text_area(
            "Observaciones",
            key=(
                "explotacion_equipos_nuevo_observaciones_"
                f"{form_equipo_aplicacion_version}"
            )
        )

        if st.form_submit_button("Añadir equipo"):

            equipo_nombre = equipo_nombre.strip()
            equipo_tipo = equipo_tipo.strip()

            if not equipo_nombre or not equipo_tipo:

                st.error("Nombre y tipo son obligatorios")

            else:

                try:

                    fechas_nuevo_equipo = {
                        "fecha_adquisicion": (
                            parsear_fecha_es(equipo_fecha_adquisicion)
                            if "fecha_adquisicion" in columnas_equipos
                            else None
                        ),
                        "fecha_ultima_inspeccion": parsear_fecha_es(
                            equipo_fecha_ultima_inspeccion
                        ),
                        "fecha_proxima_inspeccion": parsear_fecha_es(
                            equipo_fecha_proxima_inspeccion
                        )
                    }

                except ValueError:

                    st.error("La fecha debe tener formato DD/MM/AAAA")

                else:

                    _insertar_equipo(
                        {
                            "nombre": equipo_nombre,
                            "tipo": equipo_tipo,
                            "marca": equipo_marca.strip(),
                            "modelo": equipo_modelo.strip(),
                            "matricula": equipo_matricula.strip(),
                            "numero_roma": equipo_numero_roma.strip(),
                            "numero_serie": equipo_numero_serie.strip(),
                            "fecha_adquisicion": (
                                fechas_nuevo_equipo["fecha_adquisicion"]
                            ),
                            "fecha_ultima_inspeccion": (
                                fechas_nuevo_equipo[
                                    "fecha_ultima_inspeccion"
                                ]
                            ),
                            "fecha_proxima_inspeccion": (
                                fechas_nuevo_equipo[
                                    "fecha_proxima_inspeccion"
                                ]
                            ),
                            "capacidad_litros": float(equipo_capacidad_litros),
                            "observaciones": equipo_observaciones.strip()
                        }
                    )

                    st.success("Equipo añadido")
                    st.session_state[
                        "explotacion_equipos_form_version"
                    ] += 1
                    st.rerun()

    equipos = _leer_equipos()

    if equipos.empty:

        st.info("No hay equipos de aplicación registrados")

    else:

        if "explotacion_equipos_editor_version" not in st.session_state:

            st.session_state["explotacion_equipos_editor_version"] = 0

        equipos_editor_version = st.session_state[
            "explotacion_equipos_editor_version"
        ]
        equipos_editor = equipos.copy()
        columnas_visuales_equipos = _columnas_visuales_equipos(
            columnas_equipos
        )
        columnas_visuales_equipos = [
            columna
            for columna in columnas_visuales_equipos
            if columna in equipos_editor.columns
        ]
        fechas_visuales_equipos = _fechas_visuales_equipos(
            columnas_equipos
        )

        for columna in fechas_visuales_equipos:

            equipos_editor[columna] = pd.to_datetime(
                equipos_editor[columna],
                errors="coerce"
            )

        equipos_editor_visual = equipos_editor[
            columnas_visuales_equipos
        ].rename(columns=ETIQUETAS_EQUIPOS)
        equipos_editados_visual = st.data_editor(
            equipos_editor_visual,
            num_rows="fixed",
            disabled=["ID"],
            hide_index=True,
            use_container_width=True,
            column_order=[
                ETIQUETAS_EQUIPOS.get(columna, columna)
                for columna in columnas_visuales_equipos
            ],
            column_config={
                "ID": st.column_config.NumberColumn(
                    "ID",
                    disabled=True
                ),
                "Fecha de adquisición": st.column_config.DateColumn(
                    "Fecha de adquisición",
                    format="DD/MM/YYYY"
                ),
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
                    min_value=0.0
                )
            },
            key=f"explotacion_equipos_editor_v7_etiquetas_{equipos_editor_version}"
        )
        equipos_editados = mapear_columnas_visuales_a_tecnicas(
            equipos_editados_visual,
            etiquetas_extra=ETIQUETAS_EQUIPOS
        )

        confirmar_cambios_equipos = st.checkbox(
            "Confirmo que quiero guardar los cambios de equipos",
            key=(
                "explotacion_equipos_confirmar_cambios_"
                f"{equipos_editor_version}"
            )
        )

        if st.button(
            "💾 Guardar cambios de equipos",
            key=(
                "explotacion_equipos_guardar_cambios_"
                f"{equipos_editor_version}"
            )
        ):

            errores_equipos = []
            equipos_guardar = equipos_editados.copy()

            if len(equipos_guardar) != len(equipos):

                errores_equipos.append(
                    "No se permite borrar equipos desde el editor"
                )

            for columna in _textos_visuales_equipos(columnas_equipos):

                equipos_guardar[columna] = (
                    equipos_guardar[columna]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

            if (equipos_guardar["nombre"] == "").any():

                errores_equipos.append("El nombre no puede estar vacío")

            if (equipos_guardar["tipo"] == "").any():

                errores_equipos.append("El tipo no puede estar vacío")

            if not confirmar_cambios_equipos:

                errores_equipos.append(
                    "Marca la confirmación antes de guardar los equipos"
                )

            if errores_equipos:

                for error in errores_equipos:

                    st.error(error)

            else:

                conn = conectar()

                for _, fila in equipos_guardar.iterrows():

                    fechas_guardar = {}

                    for columna in fechas_visuales_equipos:

                        fechas_guardar[columna] = None

                        if not pd.isna(fila[columna]):

                            fechas_guardar[columna] = pd.to_datetime(
                                fila[columna]
                            ).date().isoformat()

                    for columna in FECHAS_EQUIPOS:

                        fechas_guardar.setdefault(columna, None)

                    capacidad_litros = None

                    if (
                        "capacidad_litros" in equipos_guardar.columns
                        and not pd.isna(fila["capacidad_litros"])
                    ):

                        capacidad_litros = float(fila["capacidad_litros"])

                    _actualizar_equipo(
                        conn,
                        fila,
                        fechas_guardar,
                        capacidad_litros
                    )

                conn.commit()
                conn.close()

                st.session_state["mensaje_explotacion_guardado"] = (
                    "Cambios de equipos guardados"
                )
                st.session_state[
                    "explotacion_equipos_editor_version"
                ] += 1
                st.rerun()

    borrar_registros_seguro(
        "equipos_aplicacion",
        "id",
        formatear_columnas_fecha_es(equipos, FECHAS_EQUIPOS),
        "equipos de aplicación",
        bloqueos=[
            (
                "tratamientos",
                "equipo_aplicacion_id",
                "el equipo está usado en tratamientos"
            ),
            (
                "tratamientos",
                "equipo_id",
                "el equipo está usado en tratamientos"
            )
        ],
        campo_descripcion="nombre",
        key="explotacion_equipos"
    )


def render():

    st.title("🏡 Explotación")

    for clave_mensaje in (
        "mensaje_asesor_explotacion",
        "mensaje_explotacion_guardado",
    ):

        mensaje = st.session_state.pop(clave_mensaje, None)

        if mensaje:

            st.success(mensaje)

    seccion = st.radio(
        "Opciones de explotación",
        [
            "📋 Resumen",
            "👤 Titular",
            "🏡 Explotación",
            "🧑‍🌾 Responsable / Asesor",
            "👥 1.2 Personas relacionadas",
            "🚜 1.3 Equipos aplicación fito",
        ],
        horizontal=True,
        key="explotacion_seccion"
    )

    datos_explotacion = _leer_datos_explotacion()

    if seccion == "📋 Resumen":

        _render_resumen(
            datos_explotacion,
            _leer_personas(),
            _leer_equipos()
        )

    elif seccion == "👤 Titular":

        _render_titular(datos_explotacion)

    elif seccion == "🏡 Explotación":

        _render_datos_explotacion(datos_explotacion)

    elif seccion == "🧑‍🌾 Responsable / Asesor":

        _render_responsable_asesor(datos_explotacion)

    elif seccion == "👥 1.2 Personas relacionadas":

        _render_personas()

    elif seccion == "🚜 1.3 Equipos aplicación fito":

        _render_equipos()
