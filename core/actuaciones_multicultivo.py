from datetime import datetime

import pandas as pd


COLUMNAS_DETALLE = [
    "registro_id",
    "cultivo_id",
    "parcela_id",
    "superficie",
    "observaciones",
    "cultivo",
    "parcela",
]


def texto(valor):

    if valor is None:

        return ""

    try:

        if pd.isna(valor):

            return ""

    except (TypeError, ValueError):

        pass

    return str(valor).strip()


def entero_o_none(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return None

    return int(numero)


def numero_o_none(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return None

    return float(numero)


def tabla_existe(conn, tabla):

    fila = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (tabla,),
    ).fetchone()
    return fila is not None


def columnas_tabla(conn, tabla):

    if not tabla_existe(conn, tabla):

        return set()

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def normalizar_detalles(detalles):

    normalizados = []
    vistos = set()

    for detalle in detalles or []:

        cultivo_id = entero_o_none(detalle.get("cultivo_id"))
        parcela_id = entero_o_none(detalle.get("parcela_id"))

        if cultivo_id is None:

            continue

        clave = (cultivo_id, parcela_id)

        if clave in vistos:

            continue

        normalizados.append(
            {
                "cultivo_id": cultivo_id,
                "parcela_id": parcela_id,
                "superficie": numero_o_none(detalle.get("superficie")),
                "observaciones": texto(detalle.get("observaciones")),
            }
        )
        vistos.add(clave)

    return normalizados


def parcelas_compatibilidad(detalles):

    parcelas = []
    vistos = set()

    for detalle in normalizar_detalles(detalles):

        parcela_id = entero_o_none(detalle.get("parcela_id"))

        if parcela_id is None or parcela_id in vistos:

            continue

        parcelas.append(
            {
                "parcela_id": parcela_id,
                "superficie": detalle.get("superficie"),
            }
        )
        vistos.add(parcela_id)

    return parcelas


def insertar_detalles(conn, tabla, campo_registro, registro_id, detalles):

    if not tabla_existe(conn, tabla):

        return

    columnas = columnas_tabla(conn, tabla)

    if not {campo_registro, "cultivo_id"}.issubset(columnas):

        return

    ahora = datetime.now().isoformat(timespec="seconds")

    for detalle in normalizar_detalles(detalles):

        valores = {
            campo_registro: int(registro_id),
            "cultivo_id": int(detalle["cultivo_id"]),
        }

        if "parcela_id" in columnas:

            valores["parcela_id"] = detalle.get("parcela_id")

        if "superficie" in columnas:

            valores["superficie"] = detalle.get("superficie")

        if "observaciones" in columnas:

            valores["observaciones"] = detalle.get("observaciones")

        if "created_at" in columnas:

            valores["created_at"] = ahora

        if "updated_at" in columnas:

            valores["updated_at"] = ahora

        nombres = list(valores)
        conn.execute(
            f"""
            INSERT INTO {tabla}
            ({','.join(nombres)})
            VALUES ({','.join(['?'] * len(nombres))})
            """,
            [valores[columna] for columna in nombres],
        )


def reemplazar_detalles(conn, tabla, campo_registro, registro_id, detalles):

    if not tabla_existe(conn, tabla):

        return

    conn.execute(
        f"DELETE FROM {tabla} WHERE {campo_registro}=?",
        (int(registro_id),),
    )
    insertar_detalles(conn, tabla, campo_registro, registro_id, detalles)


def _expr_columna(tabla, columna, columnas, defecto="''"):

    if columna in columnas:

        return f"COALESCE({tabla}.{columna},{defecto})"

    return defecto


def _expr_cultivo(columnas_cultivos):

    if "nombre" in columnas_cultivos:

        nombre = "COALESCE(cultivos.nombre,'')"

    elif "especie" in columnas_cultivos:

        nombre = "COALESCE(cultivos.especie,'')"

    else:

        nombre = "''"

    partes = [nombre]

    if "variedad" in columnas_cultivos:

        partes.append("COALESCE(NULLIF(cultivos.variedad,''),'')")

    if "sistema" in columnas_cultivos:

        partes.append("COALESCE(NULLIF(cultivos.sistema,''),'')")

    if "ano_plantacion" in columnas_cultivos:

        partes.append(
            """
            CASE
                WHEN cultivos.ano_plantacion IS NULL THEN ''
                ELSE 'Plant. ' || cultivos.ano_plantacion
            END
            """
        )

    if "codigo_siex" in columnas_cultivos:

        partes.append(
            """
            CASE
                WHEN IFNULL(cultivos.codigo_siex,'') = '' THEN ''
                ELSE 'SIEX ' || cultivos.codigo_siex
            END
            """
        )

    expresion = " || ' / ' || ".join(partes)
    return f"TRIM({expresion})"


def _expr_parcela(columnas_parcelas):

    nombre = _expr_columna("parcelas", "nombre", columnas_parcelas)
    poligono = _expr_columna("parcelas", "poligono", columnas_parcelas)
    parcela = _expr_columna("parcelas", "parcela", columnas_parcelas)
    recinto = _expr_columna("parcelas", "recinto", columnas_parcelas)
    return f"""
        TRIM(
            CASE
                WHEN IFNULL({nombre},'') != '' THEN {nombre}
                ELSE {poligono} || '-' || {parcela} || '-' || {recinto}
            END
        )
    """


def leer_detalles(conn, tabla, campo_registro, registros_ids=None):

    if not tabla_existe(conn, tabla):

        return pd.DataFrame(columns=COLUMNAS_DETALLE)

    columnas = columnas_tabla(conn, tabla)

    if not {campo_registro, "cultivo_id"}.issubset(columnas):

        return pd.DataFrame(columns=COLUMNAS_DETALLE)

    columnas_cultivos = columnas_tabla(conn, "cultivos")
    columnas_parcelas = columnas_tabla(conn, "parcelas")
    expr_cultivo = _expr_cultivo(columnas_cultivos)
    expr_parcela = _expr_parcela(columnas_parcelas)
    expr_parcela_id = (
        f"{tabla}.parcela_id"
        if "parcela_id" in columnas
        else "NULL"
    )
    expr_superficie = (
        f"{tabla}.superficie"
        if "superficie" in columnas
        else "NULL"
    )
    expr_observaciones = _expr_columna(tabla, "observaciones", columnas)
    where = ""
    params = []

    if registros_ids is not None:

        ids = [
            int(valor)
            for valor in registros_ids
            if entero_o_none(valor) is not None
        ]

        if not ids:

            return pd.DataFrame(columns=COLUMNAS_DETALLE)

        marcadores = ",".join(["?"] * len(ids))
        where = f"WHERE {tabla}.{campo_registro} IN ({marcadores})"
        params = ids

    detalles = pd.read_sql_query(
        f"""
        SELECT
            {tabla}.{campo_registro} AS registro_id,
            {tabla}.cultivo_id,
            {expr_parcela_id} AS parcela_id,
            {expr_superficie} AS superficie,
            {expr_observaciones} AS observaciones,
            {expr_cultivo} AS cultivo,
            {expr_parcela} AS parcela
        FROM {tabla}
        LEFT JOIN cultivos ON cultivos.id = {tabla}.cultivo_id
        LEFT JOIN parcelas ON parcelas.id = {expr_parcela_id}
        {where}
        ORDER BY {tabla}.{campo_registro}, {tabla}.id
        """,
        conn,
        params=params,
    )

    for columna in COLUMNAS_DETALLE:

        if columna not in detalles.columns:

            detalles[columna] = ""

    return detalles[COLUMNAS_DETALLE]


def detalles_registro(conn, tabla, campo_registro, registro_id):

    detalles = leer_detalles(conn, tabla, campo_registro, [registro_id])

    if detalles.empty:

        return []

    return [
        {
            "cultivo_id": entero_o_none(fila.get("cultivo_id")),
            "parcela_id": entero_o_none(fila.get("parcela_id")),
            "superficie": numero_o_none(fila.get("superficie")),
            "observaciones": texto(fila.get("observaciones")),
        }
        for fila in detalles.to_dict("records")
    ]


def agregar_detalles(dataframe, conn, tabla, campo_registro, columna_id="id"):

    datos = dataframe.copy() if dataframe is not None else pd.DataFrame()

    for columna, defecto in (
        ("cultivos_detalle", ""),
        ("parcelas_detalle", ""),
        ("superficie_detalle", 0.0),
        ("tiene_detalle_multicultivo", False),
    ):

        if columna not in datos.columns:

            datos[columna] = defecto

    if datos.empty or columna_id not in datos.columns:

        return datos

    ids = (
        pd.to_numeric(datos[columna_id], errors="coerce")
        .dropna()
        .astype(int)
        .tolist()
    )
    detalles = leer_detalles(conn, tabla, campo_registro, ids)

    if detalles.empty:

        return datos

    detalles["registro_id"] = pd.to_numeric(
        detalles["registro_id"],
        errors="coerce",
    )

    for registro_id, grupo in detalles.dropna(
        subset=["registro_id"]
    ).groupby("registro_id", sort=False):

        cultivo_textos = [
            texto(valor)
            for valor in grupo["cultivo"].tolist()
            if texto(valor)
        ]
        parcela_textos = [
            texto(valor)
            for valor in grupo["parcela"].tolist()
            if texto(valor)
        ]
        cultivos = ", ".join(dict.fromkeys(cultivo_textos))
        parcelas = ", ".join(dict.fromkeys(parcela_textos))
        superficie = (
            pd.to_numeric(grupo["superficie"], errors="coerce")
            .fillna(0)
            .sum()
        )
        mascara = (
            pd.to_numeric(datos[columna_id], errors="coerce")
            == int(registro_id)
        )
        datos.loc[mascara, "cultivos_detalle"] = cultivos
        datos.loc[mascara, "parcelas_detalle"] = parcelas
        datos.loc[mascara, "superficie_detalle"] = float(superficie)
        datos.loc[mascara, "tiene_detalle_multicultivo"] = True

    return datos
