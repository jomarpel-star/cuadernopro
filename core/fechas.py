from datetime import date, datetime
import re

import pandas as pd


def hoy():

    return date.today().isoformat()


def fecha_es_a_datetime(valor):

    if valor is None or pd.isna(valor):

        return pd.NaT

    if isinstance(valor, pd.Timestamp):

        return valor

    if isinstance(valor, datetime):

        return pd.Timestamp(valor)

    if isinstance(valor, date):

        return pd.Timestamp(valor)

    texto = str(valor).strip()

    if not texto:

        return pd.NaT

    formatos = []

    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", texto):

        formatos.append("%Y-%m-%d")

    elif re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", texto):

        formatos.append("%d/%m/%Y")

    elif re.fullmatch(r"\d{1,2}-\d{1,2}-\d{4}", texto):

        formatos.append("%d-%m-%Y")

    for formato in formatos:

        try:

            return pd.Timestamp(datetime.strptime(texto, formato))

        except ValueError:

            return pd.NaT

    return pd.to_datetime(texto, errors="coerce", dayfirst=True)


def formatear_fecha_es(valor):

    fecha = fecha_es_a_datetime(valor)

    if pd.isna(fecha):

        return ""

    return fecha.strftime("%d/%m/%Y")


def parsear_fecha_es(valor):

    if valor is None or pd.isna(valor):

        return None

    if isinstance(valor, str) and not valor.strip():

        return None

    fecha = fecha_es_a_datetime(valor)

    if pd.isna(fecha):

        raise ValueError("La fecha debe tener formato DD/MM/AAAA")

    return fecha.date().isoformat()


def formatear_columnas_fecha_es(dataframe, columnas=None):

    if dataframe is None or dataframe.empty:

        return dataframe

    resultado = dataframe.copy()
    columnas_fecha = columnas or [
        columna
        for columna in resultado.columns
        if (
            columna == "fecha"
            or columna.startswith("fecha_")
            or columna.endswith("_fecha")
        )
    ]

    for columna in columnas_fecha:

        if columna in resultado.columns:

            resultado[columna] = resultado[columna].apply(
                formatear_fecha_es
            )

    if "periodo" in resultado.columns:

        def formatear_periodo(valor):

            texto = "" if pd.isna(valor) else str(valor).strip()

            if " a " not in texto:

                return texto

            inicio, fin = texto.split(" a ", 1)
            inicio_es = formatear_fecha_es(inicio)
            fin_es = formatear_fecha_es(fin)

            if inicio_es and fin_es:

                return f"{inicio_es} a {fin_es}"

            return texto

        resultado["periodo"] = resultado["periodo"].apply(formatear_periodo)

    return resultado


def preparar_columnas_fecha_tabla(dataframe, columnas=None):

    if dataframe is None or dataframe.empty:

        return dataframe

    resultado = dataframe.copy()
    columnas_fecha = columnas or [
        columna
        for columna in resultado.columns
        if (
            columna == "fecha"
            or columna.startswith("fecha_")
            or columna.endswith("_fecha")
        )
    ]

    for columna in columnas_fecha:

        if columna in resultado.columns:

            resultado[columna] = resultado[columna].map(
                fecha_es_a_datetime
            )

    return resultado


def _fecha_normalizada(valor):

    fecha = fecha_es_a_datetime(valor)

    if pd.isna(fecha):

        return None

    return fecha.date()


def detectar_campana_por_fecha(fecha, conn=None):

    fecha_normalizada = _fecha_normalizada(fecha)

    if fecha_normalizada is None:

        return None

    if conn is not None:

        filas = conn.execute(
            """
            SELECT id,nombre,fecha_inicio,fecha_fin
            FROM campanas
            ORDER BY fecha_inicio,id
            """
        ).fetchall()

    else:

        from core.db import leer

        campanas = leer(
            """
            SELECT id,nombre,fecha_inicio,fecha_fin
            FROM campanas
            ORDER BY fecha_inicio,id
            """
        )
        filas = campanas.itertuples(index=False, name=None)

    coincidencias = []

    for fila in filas:

        inicio_campana = _fecha_normalizada(fila[2])
        fin_campana = _fecha_normalizada(fila[3])

        if inicio_campana is None or fin_campana is None:

            continue

        if inicio_campana <= fecha_normalizada <= fin_campana:

            coincidencias.append(
                {
                    "id": int(fila[0]),
                    "nombre": fila[1],
                    "fecha_inicio": inicio_campana,
                    "fecha_fin": fin_campana,
                }
            )

    if not coincidencias:

        return None

    coincidencias.sort(
        key=lambda campana: (
            (campana["fecha_fin"] - campana["fecha_inicio"]).days,
            campana["fecha_inicio"],
            campana["id"],
        )
    )
    campana = coincidencias[0].copy()
    campana["coincidencias"] = len(coincidencias)
    campana["solapadas"] = coincidencias

    if len(coincidencias) > 1:

        campana["aviso"] = (
            "La fecha encaja en varias campañas configuradas. "
            "Se ha elegido la campaña con el periodo más específico."
        )

    else:

        campana["aviso"] = ""

    return campana



def validar_fecha_en_campana(campana_id, fecha_registro):

    from core.db import leer

    campana = leer(
        """
        SELECT nombre,fecha_inicio,fecha_fin
        FROM campanas
        WHERE id=?
        """,
        (int(campana_id),)
    )

    if campana.empty:

        return {
            "es_valida": True,
            "requiere_confirmacion": False,
            "mensaje": "No se encontró la campaña asociada al registro."
        }

    fila = campana.iloc[0]
    fecha = pd.to_datetime(fecha_registro, errors="coerce")

    if pd.isna(fecha):

        return {
            "es_valida": True,
            "requiere_confirmacion": False,
            "mensaje": ""
        }

    fecha_inicio = pd.to_datetime(fila["fecha_inicio"], errors="coerce")
    fecha_fin = pd.to_datetime(fila["fecha_fin"], errors="coerce")

    if pd.isna(fecha_inicio) or pd.isna(fecha_fin):

        return {
            "es_valida": True,
            "requiere_confirmacion": False,
            "mensaje": (
                f"La campaña {fila['nombre']} no tiene definido un periodo "
                "oficial completo. La fecha no se puede comprobar."
            )
        }

    fecha_normalizada = fecha.date()
    inicio_normalizado = fecha_inicio.date()
    fin_normalizado = fecha_fin.date()

    if inicio_normalizado <= fecha_normalizada <= fin_normalizado:

        return {
            "es_valida": True,
            "requiere_confirmacion": False,
            "mensaje": ""
        }

    return {
        "es_valida": False,
        "requiere_confirmacion": True,
        "mensaje": (
            f"⚠️ La fecha {formatear_fecha_es(fecha_normalizada)} está fuera "
            "del "
            f"periodo oficial de la campaña {fila['nombre']} "
            f"({formatear_fecha_es(inicio_normalizado)} a "
            f"{formatear_fecha_es(fin_normalizado)})."
        )
    }



def validar_intervalo_en_campana(campana_id, fecha_inicio, fecha_fin):

    from core.db import leer

    campana = leer(
        """
        SELECT nombre,fecha_inicio,fecha_fin
        FROM campanas
        WHERE id=?
        """,
        (int(campana_id),)
    )

    if campana.empty:

        return {
            "requiere_confirmacion": False,
            "mensaje": "No se encontró la campaña asociada al registro."
        }

    fila = campana.iloc[0]
    inicio = pd.to_datetime(fecha_inicio, errors="coerce")
    fin = pd.to_datetime(fecha_fin, errors="coerce")
    inicio_campana = pd.to_datetime(fila["fecha_inicio"], errors="coerce")
    fin_campana = pd.to_datetime(fila["fecha_fin"], errors="coerce")

    if pd.isna(inicio) or pd.isna(fin):

        return {"requiere_confirmacion": False, "mensaje": ""}

    if pd.isna(inicio_campana) or pd.isna(fin_campana):

        return {
            "requiere_confirmacion": False,
            "mensaje": (
                f"La campaña {fila['nombre']} no tiene definido un periodo "
                "oficial completo. Las fechas no se pueden comprobar."
            )
        }

    fuera_periodo = (
        inicio.date() < inicio_campana.date()
        or inicio.date() > fin_campana.date()
        or fin.date() < inicio_campana.date()
        or fin.date() > fin_campana.date()
    )

    if not fuera_periodo:

        return {"requiere_confirmacion": False, "mensaje": ""}

    return {
        "requiere_confirmacion": True,
        "mensaje": (
            "⚠️ El tratamiento tiene fechas fuera del periodo oficial de "
            f"la campaña {fila['nombre']} "
            f"({formatear_fecha_es(inicio_campana)} a "
            f"{formatear_fecha_es(fin_campana)})."
        )
    }



def obtener_campana_por_intervalo(conn, fecha_inicio, fecha_fin=None):

    inicio = pd.to_datetime(fecha_inicio, errors="coerce")
    fin = pd.to_datetime(fecha_fin, errors="coerce")

    if pd.isna(inicio) and pd.isna(fin):

        return {
            "campana": None,
            "estado": "sin_campana",
            "mensaje": (
                "No se ha encontrado una campaña cuyo periodo incluya "
                "estas fechas."
            )
        }

    if pd.isna(inicio):

        inicio = fin

    if pd.isna(fin):

        fin = inicio

    campanas = []

    for fila in conn.execute(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin
        FROM campanas
        ORDER BY fecha_inicio,id
        """
    ).fetchall():

        inicio_campana = pd.to_datetime(fila[2], errors="coerce")
        fin_campana = pd.to_datetime(fila[3], errors="coerce")

        if pd.isna(inicio_campana) or pd.isna(fin_campana):

            continue

        campanas.append(
            {
                "id": int(fila[0]),
                "nombre": fila[1],
                "fecha_inicio": inicio_campana.date(),
                "fecha_fin": fin_campana.date()
            }
        )

    campanas_inicio = [
        campana
        for campana in campanas
        if campana["fecha_inicio"] <= inicio.date() <= campana["fecha_fin"]
    ]
    campanas_fin = [
        campana
        for campana in campanas
        if campana["fecha_inicio"] <= fin.date() <= campana["fecha_fin"]
    ]
    ids_fin = {campana["id"] for campana in campanas_fin}
    campanas_comunes = [
        campana
        for campana in campanas_inicio
        if campana["id"] in ids_fin
    ]

    if len(campanas_comunes) == 1:

        return {
            "campana": campanas_comunes[0],
            "estado": "encontrada",
            "mensaje": ""
        }

    if campanas_inicio and campanas_fin and not campanas_comunes:

        return {
            "campana": None,
            "estado": "cruza_campanas",
            "mensaje": (
                "El tratamiento cruza dos campañas. Se recomienda "
                "dividirlo en dos tratamientos."
            )
        }

    return {
        "campana": None,
        "estado": "sin_campana",
        "mensaje": (
            "No se ha encontrado una campaña cuyo periodo incluya estas "
            "fechas."
        )
    }
