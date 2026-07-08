from datetime import datetime
from html import escape
from io import BytesIO
import re
import shutil
import unicodedata

import pandas as pd

from core.config import APP_DESCRIPTION, APP_NAME
from core.db import conectar, leer
from core.fechas import formatear_fecha_es
from core.paths import DOCS_DIR, EXPORTS_DIR
from modules.contabilidad import (
    _leer_movimientos_contabilidad,
    _resolver_tercero_movimiento,
)
from modules.cosecha import (
    _leer_cosechas_guardadas,
    _preparar_cosechas_presentacion,
)
from modules.fertilizacion import (
    _leer_fertilizaciones_guardadas,
    _preparar_fertilizaciones_presentacion,
)
from modules.practicas_culturales import (
    _leer_practicas_guardadas,
    _preparar_practicas_presentacion,
)
from modules.tratamientos import _leer_tratamientos_guardados


CONTENT_WIDTH = 793
COLOR_PRIMARIO = "#3F4A3C"
COLOR_SECUNDARIO = "#6E7A66"
COLOR_CABECERA_TABLA = "#EEF1EE"
COLOR_BORDE = "#B7BDB4"
COLOR_TEXTO = "#202520"
COLOR_MUTED = "#6B7068"


def limpiar_texto_pdf(valor, max_len=None):

    if valor is None:

        return ""

    try:

        if pd.isna(valor):

            return ""

    except (TypeError, ValueError):

        pass

    texto = unicodedata.normalize("NFKC", str(valor))
    texto = "".join(caracter for caracter in texto if ord(caracter) >= 32)
    texto = texto.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    texto = re.sub(r"\s+", " ", texto).strip()

    if max_len is not None and len(texto) > max_len:

        texto = f"{texto[: max_len - 3].rstrip()}..."

    return texto


def fecha_es(valor):

    return formatear_fecha_es(valor)


def numero_es(valor, decimales=2):

    if valor is None:

        return ""

    try:

        if pd.isna(valor):

            return ""

        numero = float(valor)

    except (TypeError, ValueError):

        return limpiar_texto_pdf(valor)

    return f"{numero:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def importe_es(valor):

    texto = numero_es(valor, 2)
    return f"{texto} €" if texto else ""


def abreviar_si_necesario(valor, max_len=80):

    return limpiar_texto_pdf(valor, max_len=max_len)


def _clave_texto(valor):

    texto = limpiar_texto_pdf(valor).upper()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )


def _compactar_numero_unidad(texto):

    texto = limpiar_texto_pdf(texto)
    texto = re.sub(
        r"(?<=\d)\s+(?=(?:L|KG|G|ML|CC|HA|M2|M3|%)\b)",
        "",
        texto,
        flags=re.IGNORECASE
    )
    return texto


def abreviar_texto_largo(valor, max_len=None):

    texto = _compactar_numero_unidad(valor)

    if max_len is not None and len(texto) > max_len:

        texto = f"{texto[: max_len - 3].rstrip()}..."

    return texto


def abreviar_dosis(valor, max_len=42):

    texto = _compactar_numero_unidad(valor).upper()
    texto = re.sub(r"\s*/\s*", "/", texto)
    return abreviar_texto_largo(texto, max_len=max_len)


def abreviar_cultivo(valor, max_len=70):

    texto = limpiar_texto_pdf(valor)

    if not texto:

        return ""

    partes = [
        parte.strip()
        for parte in re.split(r"\s*/\s*", texto)
        if parte.strip()
    ]
    abreviadas = []

    for parte in partes or [texto]:

        clave = _clave_texto(parte)

        if "OLIVAR DE ACEITUNA PARA ACEITE" in clave:

            abreviadas.append("OLIVAR")

        elif "ALMENDROS DULCES" in clave:

            abreviadas.append("ALMENDRO")

        elif clave == "SECANO":

            abreviadas.append("SEC")

        elif clave == "REGADIO":

            abreviadas.append("REG")

        else:

            abreviadas.append(limpiar_texto_pdf(parte).upper())

    return abreviar_texto_largo(" / ".join(abreviadas), max_len=max_len)


def abreviar_persona(valor, max_len=70):

    texto = limpiar_texto_pdf(valor)

    if not texto:

        return ""

    clave = _clave_texto(texto)

    if re.search(r"\b(SL|SA|SAT|SC|CB|COOP|SLL|SLA)\b", clave):

        return abreviar_texto_largo(texto.upper(), max_len=max_len)

    palabras = texto.upper().split()

    if len(palabras) >= 4:

        iniciales = [f"{palabra[0]}." for palabra in palabras[:2] if palabra]
        texto = " ".join(iniciales + [palabras[2]])

    elif len(palabras) == 3:

        texto = f"{palabras[0][0]}. {palabras[1][0]}. {palabras[2]}"

    elif len(palabras) == 2:

        texto = f"{palabras[0][0]}. {palabras[1]}"

    else:

        texto = texto.upper()

    return abreviar_texto_largo(texto, max_len=max_len)


def abreviar_maquinaria(valor, max_len=70):

    texto = limpiar_texto_pdf(valor).upper()

    if not texto:

        return ""

    texto = re.sub(r"\s*/\s*", " ", texto)
    texto = re.sub(r"\bATOMIZADOR ARRASTRADO\b", "ATOMIZADOR", texto)
    texto = re.sub(r"\bATASA TURBO\s*2000\b", "ATASA T2000", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    john_deere = re.search(r"\bJOHN DEERE\s+[A-Z0-9-]+", texto)

    if john_deere:

        texto = john_deere.group(0)

    texto = re.sub(r"\b(\w+)\s+\1\b", r"\1", texto)
    return abreviar_texto_largo(texto, max_len=max_len)


def _rangos_numeros(numeros):

    if not numeros:

        return ""

    rangos = []
    inicio = numeros[0]
    anterior = numeros[0]

    for numero in numeros[1:]:

        if numero == anterior + 1:

            anterior = numero
            continue

        rangos.append(
            f"{inicio}-{anterior}"
            if inicio != anterior
            else str(inicio)
        )
        inicio = numero
        anterior = numero

    rangos.append(
        f"{inicio}-{anterior}"
        if inicio != anterior
        else str(inicio)
    )
    return ", ".join(rangos)


def abreviar_parcelas(ids_parcelas, orden_parcelas, max_directas=8):

    ordenes = sorted({
        int(orden_parcelas[parcela_id])
        for parcela_id in ids_parcelas
        if parcela_id in orden_parcelas
    })

    if not ordenes:

        return ""

    if len(ordenes) <= max_directas:

        return ", ".join(str(orden) for orden in ordenes)

    return f"VARIAS ({_rangos_numeros(ordenes)})"


def _numero(valor):

    try:

        if valor is None or pd.isna(valor):

            return 0.0

        if isinstance(valor, str):

            valor = limpiar_texto_pdf(valor)

            if "," in valor:

                valor = valor.replace(".", "").replace(",", ".")

        return float(valor)

    except (TypeError, ValueError):

        return 0.0


def _numero_es_sin_ceros(valor):

    numero = _numero(valor)

    if numero == 0:

        return "0"

    if numero.is_integer():

        return f"{int(numero):,}".replace(",", ".")

    return numero_es(numero, 2)


def _cantidad_con_unidad(cantidad, unidad):

    cantidad_texto = limpiar_texto_pdf(cantidad)
    unidad_limpia = limpiar_texto_pdf(unidad).upper()

    if not cantidad_texto:

        return unidad_limpia

    try:

        float(cantidad_texto.replace(",", "."))

    except ValueError:

        cantidad_limpia = cantidad_texto

    else:

        cantidad_limpia = _numero_es_sin_ceros(cantidad)

    if cantidad_limpia and unidad_limpia:

        return f"{cantidad_limpia}{unidad_limpia}"

    return cantidad_limpia or unidad_limpia


def _campana(campana_id):

    datos = leer(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin
        FROM campanas
        WHERE id=?
        """,
        (int(campana_id),)
    )

    if datos.empty:

        return {
            "id": int(campana_id),
            "nombre": f"campana_{campana_id}",
            "fecha_inicio": "",
            "fecha_fin": ""
        }

    return datos.iloc[0].to_dict()


def _nombre_archivo_seguro(valor):

    nombre = limpiar_texto_pdf(valor) or "campana"
    nombre = re.sub(r"[^A-Za-z0-9_-]+", "_", nombre)
    nombre = re.sub(r"_+", "_", nombre).strip("_")
    return nombre or "campana"


def _primera_fila(dataframe):

    if dataframe.empty:

        return {}

    return dataframe.iloc[0].to_dict()


def _valor(fila, *campos):

    for campo in campos:

        valor = fila.get(campo, "")

        if limpiar_texto_pdf(valor):

            return limpiar_texto_pdf(valor)

    return ""


def _fecha_apertura_portada(campana):

    return fecha_es(campana.get("fecha_inicio"))


def _registro_nacional_explotacion(explotacion):

    return _valor(
        explotacion,
        "identificador_oficial",
        "registro_explotacion",
        "codigo_regepa",
        "codigo_regea",
    )


def _registro_autonomico_explotacion(explotacion):

    return _valor(
        explotacion,
        "registro_autonomico",
        "registro_autonomico_explotacion",
        "codigo_registro_autonomico",
    )


def _eficacia_pdf(valor):

    texto = limpiar_texto_pdf(valor).upper()

    if texto in {"BUENA", "BUENO"}:

        return "B"

    if texto == "REGULAR":

        return "R"

    if texto in {"MALA", "MALO"}:

        return "M"

    return texto if texto in {"B", "R", "M"} else ""


def _datos_explotacion():

    return _primera_fila(leer("SELECT * FROM explotacion ORDER BY id LIMIT 1"))


def _ids_parcelas(tabla_relacion, campo_id, registro_id):

    conn = conectar()

    try:

        tabla = tabla_relacion

        if not _tabla_existe_conn_pdf(conn, tabla):

            if tabla_relacion == "practica_parcelas":

                tabla = "practicas_culturales_parcelas"

            if not _tabla_existe_conn_pdf(conn, tabla):

                return []

        datos = pd.read_sql_query(
            f"""
            SELECT parcela_id
            FROM {tabla}
            WHERE {campo_id}=?
            ORDER BY parcela_id
            """,
            conn,
            params=(int(registro_id),),
        )

    finally:

        conn.close()

    if datos.empty:

        return []

    return [
        int(parcela_id)
        for parcela_id in datos["parcela_id"].dropna().tolist()
    ]


def _ordenes_parcelas(ids_parcelas, orden_parcelas):

    ordenes = [
        str(orden_parcelas[parcela_id])
        for parcela_id in ids_parcelas
        if parcela_id in orden_parcelas
    ]
    return ", ".join(ordenes)


def _texto_pagado(valor, tipo=""):

    return "Sí" if int(_numero(valor)) else "No"


def _parrafo(texto, estilo):

    from reportlab.platypus import Paragraph

    return Paragraph(escape(limpiar_texto_pdf(texto)), estilo)


def _celda(valor, estilo, max_len=None):

    from reportlab.platypus import Paragraph

    return Paragraph(escape(limpiar_texto_pdf(valor, max_len=max_len)), estilo)


def _descripcion_equipo(fila):

    nombre = limpiar_texto_pdf(fila.get("nombre"))

    if nombre:

        return nombre

    partes = [
        limpiar_texto_pdf(fila.get("tipo")),
        limpiar_texto_pdf(fila.get("marca")),
        limpiar_texto_pdf(fila.get("modelo"))
    ]
    return " / ".join(parte for parte in partes if parte)


def _cultivo_texto(especie, variedad, sistema):

    partes = [
        limpiar_texto_pdf(especie),
        limpiar_texto_pdf(variedad),
        limpiar_texto_pdf(sistema)
    ]
    return " / ".join(parte for parte in partes if parte)


def _filtrar_campana_pdf(dataframe, campana_id):

    if dataframe is None or dataframe.empty:

        return pd.DataFrame()

    if "campana_id" not in dataframe.columns:

        return dataframe.iloc[0:0].copy()

    return dataframe[
        pd.to_numeric(dataframe["campana_id"], errors="coerce")
        == int(campana_id)
    ].copy()


def _tabla_existe_conn_pdf(conn, tabla):

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

    except Exception:

        return False

    return fila is not None


def _leer_tabla_conn_pdf(conn, tabla):

    if not _tabla_existe_conn_pdf(conn, tabla):

        return pd.DataFrame()

    try:

        return pd.read_sql_query(f'SELECT * FROM "{tabla}"', conn)

    except Exception:

        return pd.DataFrame()


def _mapa_por_id_pdf(dataframe):

    if dataframe.empty or "id" not in dataframe.columns:

        return {}

    resultado = {}

    for _, fila in dataframe.iterrows():

        try:

            fila_id = int(pd.to_numeric(fila.get("id"), errors="coerce"))

        except (TypeError, ValueError):

            continue

        resultado[fila_id] = fila.to_dict()

    return resultado


def _entero_orden_pdf(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return 0

    return int(numero)


def _entero_o_none_pdf(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return None

    return int(numero)


def _normalizar_clave_sigpac(valor):

    texto = limpiar_texto_pdf(valor)

    if not texto:

        return ""

    numero = pd.to_numeric(texto, errors="coerce")

    if not pd.isna(numero) and float(numero).is_integer():

        return str(int(numero))

    texto = unicodedata.normalize("NFKD", texto).upper()
    return "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )


def _clave_sigpac_fila(fila):

    return tuple(
        _normalizar_clave_sigpac(fila.get(campo))
        for campo in [
            "provincia_sigpac",
            "municipio_sigpac",
            "agregado_sigpac",
            "zona_sigpac",
            "poligono",
            "parcela",
            "recinto",
        ]
    )


def _clave_deduplicacion_parcela(fila):

    parcela_id = _entero_o_none_pdf(fila.get("id"))

    if parcela_id is not None:

        return ("id", parcela_id)

    return ("sigpac", _clave_sigpac_fila(fila))


def _valor_agronomico(valor, mayusculas=False):

    texto = limpiar_texto_pdf(valor)

    if not texto:

        return ""

    if texto.casefold() in {"none", "nan", "null"}:

        return ""

    if mayusculas:

        texto = texto.upper()

    return texto


def _combinar_valores_unicos(valores, mayusculas=False):

    vistos = set()
    resultado = []

    for valor in valores:

        texto = _valor_agronomico(valor, mayusculas=mayusculas)

        if not texto:

            continue

        clave = _clave_texto(texto)

        if clave in vistos:

            continue

        vistos.add(clave)
        resultado.append(texto)

    return " / ".join(resultado)


def _primer_valor_campos(fila, campos, mayusculas=False):

    for campo in campos:

        texto = _valor_agronomico(fila.get(campo), mayusculas=mayusculas)

        if texto:

            return texto

    return ""


def _entradas_relevantes_campana(entradas, campana_id):

    if campana_id is None:

        return entradas

    actuales = []

    for entrada in entradas:

        cultivo = entrada.get("cultivo") or {}
        cultivo_campana_id = _entero_o_none_pdf(cultivo.get("campana_id"))

        if cultivo_campana_id == int(campana_id):

            actuales.append(entrada)

    return actuales or entradas


def _superficie_cultivada_parcela(parcela, entradas):

    superficie_parcela = _numero(parcela.get("superficie_cultivada"))

    if superficie_parcela:

        return superficie_parcela

    superficies = []
    vistos = set()

    for entrada in entradas:

        relacion = entrada.get("relacion") or {}
        cultivo = entrada.get("cultivo") or {}
        superficie = _numero(
            relacion.get("superficie")
            or cultivo.get("superficie")
        )

        if not superficie:

            continue

        clave = (
            _entero_o_none_pdf(cultivo.get("id")),
            round(superficie, 6),
        )

        if clave in vistos:

            continue

        vistos.add(clave)
        superficies.append(superficie)

    if superficies:

        total = sum(superficies)
        superficie_sigpac = _numero(parcela.get("superficie_sigpac"))

        if superficie_sigpac and total > superficie_sigpac:

            return superficie_sigpac

        return total

    return parcela.get("superficie_sigpac", "")


def _etiqueta_cultivo_pdf(fila):

    if not fila:

        return ""

    return _cultivo_texto(
        limpiar_texto_pdf(fila.get("especie")) or fila.get("nombre"),
        fila.get("variedad"),
        fila.get("sistema"),
    )


def obtener_parcelas_unicas_para_cuaderno(campana_id=None):

    conn = conectar()

    try:

        parcelas = _leer_tabla_conn_pdf(conn, "parcelas")
        cultivos = _leer_tabla_conn_pdf(conn, "cultivos")
        cultivo_parcelas = _leer_tabla_conn_pdf(conn, "cultivo_parcelas")
        explotacion = _leer_tabla_conn_pdf(conn, "explotacion")

    finally:

        conn.close()

    if parcelas.empty:

        return [], {}

    cultivos_por_id = _mapa_por_id_pdf(cultivos)
    entradas_por_parcela = {}

    if not cultivos.empty and "parcela_id" in cultivos.columns:

        for _, cultivo in cultivos.iterrows():

            parcela_id = _entero_o_none_pdf(cultivo.get("parcela_id"))

            if parcela_id is not None:

                entradas_por_parcela.setdefault(
                    parcela_id,
                    [],
                ).append({
                    "cultivo": cultivo.to_dict(),
                    "relacion": {},
                })

    if (
        not cultivo_parcelas.empty
        and "parcela_id" in cultivo_parcelas.columns
        and "cultivo_id" in cultivo_parcelas.columns
    ):

        for _, relacion in cultivo_parcelas.iterrows():

            parcela_id = _entero_o_none_pdf(relacion.get("parcela_id"))
            cultivo_id = _entero_o_none_pdf(relacion.get("cultivo_id"))

            if parcela_id is None or cultivo_id is None:

                continue

            cultivo = cultivos_por_id.get(cultivo_id)

            if cultivo:

                entradas_por_parcela.setdefault(
                    parcela_id,
                    [],
                ).append({
                    "cultivo": cultivo,
                    "relacion": relacion.to_dict(),
                })

    explotacion_fila = (
        explotacion.iloc[0].to_dict()
        if not explotacion.empty
        else {}
    )
    sistema_explotacion = _primer_valor_campos(
        explotacion_fila,
        ["tipo_explotacion", "sistema", "sistema_explotacion"],
        mayusculas=True,
    )
    parcelas_unicas = {}

    for _, parcela in parcelas.iterrows():

        parcela_id = _entero_o_none_pdf(parcela.get("id"))

        if parcela_id is None:

            continue

        entradas = _entradas_relevantes_campana(
            entradas_por_parcela.get(parcela_id, []),
            campana_id,
        )
        fila = parcela.to_dict()
        fila["provincia"] = fila.get("provincia") or fila.get(
            "provincia_sigpac",
            "",
        )
        fila["municipio"] = fila.get("municipio") or fila.get(
            "municipio_sigpac",
            "",
        )
        fila["superficie_cultivada"] = _superficie_cultivada_parcela(
            fila,
            entradas,
        )

        cultivos_parcela = [
            entrada.get("cultivo") or {}
            for entrada in entradas
        ]
        relaciones_parcela = [
            entrada.get("relacion") or {}
            for entrada in entradas
        ]
        sistema_parcela = _primer_valor_campos(
            fila,
            [
                "sistema",
                "sistema_cultivo",
                "sistema_explotacion",
                "tipo_explotacion",
            ],
            mayusculas=True,
        )
        sistemas_cultivo = _combinar_valores_unicos(
            [
                _primer_valor_campos(
                    cultivo,
                    [
                        "sistema",
                        "sistema_cultivo",
                        "sistema_explotacion",
                        "tipo_explotacion",
                    ],
                    mayusculas=True,
                )
                for cultivo in cultivos_parcela
            ],
            mayusculas=True,
        )
        sistemas_relacion = _combinar_valores_unicos(
            [
                _primer_valor_campos(
                    relacion,
                    [
                        "sistema",
                        "sistema_cultivo",
                        "sistema_explotacion",
                        "tipo_explotacion",
                    ],
                    mayusculas=True,
                )
                for relacion in relaciones_parcela
            ],
            mayusculas=True,
        )

        fila["especie"] = _combinar_valores_unicos(
            [
                cultivo.get("especie") or cultivo.get("nombre")
                for cultivo in cultivos_parcela
            ]
        )
        fila["variedad"] = _combinar_valores_unicos(
            [cultivo.get("variedad") for cultivo in cultivos_parcela]
        )
        fila["sistema"] = (
            sistema_parcela
            or sistemas_cultivo
            or sistemas_relacion
            or sistema_explotacion
        )
        fila["marco_plantacion"] = _combinar_valores_unicos(
            [
                cultivo.get("marco_plantacion") or cultivo.get("marco")
                for cultivo in cultivos_parcela
            ]
        )
        fila["numero_arboles"] = _combinar_valores_unicos(
            [
                cultivo.get("numero_arboles") or cultivo.get("arboles")
                for cultivo in cultivos_parcela
                if _numero(cultivo.get("numero_arboles") or cultivo.get("arboles"))
            ]
        )
        parcelas_unicas.setdefault(_clave_deduplicacion_parcela(fila), fila)

    orden_parcelas = {}
    filas = sorted(
        parcelas_unicas.values(),
        key=lambda fila: (
            _clave_sigpac_fila(fila),
            _entero_o_none_pdf(fila.get("id")) or 0,
        ),
    )

    for indice, fila in enumerate(filas, start=1):

        fila["_orden"] = indice

        parcela_id = _entero_o_none_pdf(fila.get("id"))

        if parcela_id is not None:

            orden_parcelas.setdefault(parcela_id, indice)

    return filas, orden_parcelas


def _parcelas_y_orden(campana_id=None):

    return obtener_parcelas_unicas_para_cuaderno(campana_id)


def _personas():

    conn = conectar()

    try:

        datos = _leer_tabla_conn_pdf(conn, "personas")

    finally:

        conn.close()

    if datos.empty:

        return []

    if "carnet_fitosanitario" not in datos.columns:

        datos["carnet_fitosanitario"] = datos.get("carnet_aplicador", "")

    for columna in [
        "id",
        "nombre",
        "nif",
        "telefono",
        "email",
        "rol",
        "numero_asesor",
        "observaciones",
    ]:

        if columna not in datos.columns:

            datos[columna] = ""

    orden_rol = {
        "Titular": 1,
        "Representante": 2,
        "Asesor": 3,
        "Aplicador fitosanitario": 4,
        "Operario": 5,
    }
    datos["_orden_rol"] = datos["rol"].map(orden_rol).fillna(6)
    return datos.sort_values(
        ["_orden_rol", "nombre", "id"],
        na_position="last",
    ).drop(columns=["_orden_rol"]).to_dict("records")


def _equipos():

    conn = conectar()

    try:

        datos = _leer_tabla_conn_pdf(conn, "equipos_aplicacion")

    finally:

        conn.close()

    if datos.empty:

        return []

    equivalencias = {
        "matricula": "",
        "numero_roma": "",
        "numero_serie": "",
        "fecha_adquisicion": "",
        "capacidad_litros": "",
        "fecha_ultima_inspeccion": "fecha_revision",
        "fecha_proxima_inspeccion": "fecha_proxima_revision",
    }

    for columna, alternativa in equivalencias.items():

        if columna not in datos.columns:

            datos[columna] = datos.get(alternativa, "")

    for columna in ["id", "nombre", "tipo", "marca", "modelo"]:

        if columna not in datos.columns:

            datos[columna] = ""

    return datos.sort_values(["nombre", "id"], na_position="last").to_dict(
        "records"
    )


def _tratamientos(campana_id):

    conn = conectar()

    try:

        datos = _filtrar_campana_pdf(
            _leer_tratamientos_guardados(conn=conn),
            campana_id,
        )

    finally:

        conn.close()

    if datos.empty:

        return []

    datos = datos.copy()
    datos["registro"] = datos.get("registro_producto", "")
    return datos.sort_values(
        ["fecha_inicio", "id"],
        na_position="last",
    ).to_dict("records")


def _ids_desde_texto(valor):

    texto = limpiar_texto_pdf(valor)

    if not texto:

        return []

    ids = []

    for parte in texto.split(","):

        parte = parte.strip()

        if parte.isdigit():

            ids.append(int(parte))

    return ids


def _analisis_fitosanitarios(campana_id):

    conn = conectar()

    try:

        datos = _filtrar_campana_pdf(
            _leer_tabla_conn_pdf(conn, "analisis_fitosanitarios"),
            campana_id,
        )
        cultivos = _mapa_por_id_pdf(_leer_tabla_conn_pdf(conn, "cultivos"))

    finally:

        conn.close()

    if datos.empty:

        return []

    datos = datos.copy()

    if "cultivo_id" in datos.columns:

        datos["cultivo"] = datos["cultivo_id"].map(
            lambda valor: _etiqueta_cultivo_pdf(
                cultivos.get(_entero_orden_pdf(valor))
            )
        )

    elif "cultivo" not in datos.columns:

        datos["cultivo"] = ""

    return datos.sort_values(["fecha", "id"], na_position="last").to_dict(
        "records"
    )


def _fertilizaciones(campana_id):

    conn = conectar()

    try:

        datos = _filtrar_campana_pdf(
            _preparar_fertilizaciones_presentacion(
                _leer_fertilizaciones_guardadas(conn=conn)
            ),
            campana_id,
        )

    finally:

        conn.close()

    if datos.empty:

        return []

    datos = datos.copy()
    datos["cultivo"] = datos.get("cultivo_mostrado", datos.get("cultivo", ""))
    datos["tipo"] = datos.get(
        "tipo",
        datos.get("tipo_fertilizante", ""),
    )

    for columna in ["riqueza_npk", "metodo_aplicacion", "operario"]:

        if columna not in datos.columns:

            datos[columna] = ""

    return datos.sort_values(["fecha", "id"], na_position="last").to_dict(
        "records"
    )


def _cosechas(campana_id):

    conn = conectar()

    try:

        datos = _filtrar_campana_pdf(
            _preparar_cosechas_presentacion(
                _leer_cosechas_guardadas(conn=conn)
            ),
            campana_id,
        )

    finally:

        conn.close()

    if datos.empty:

        return []

    datos = datos.copy()
    datos["cultivo"] = datos.get("cultivo_mostrado", datos.get("cultivo", ""))
    datos["kg"] = datos.get("cantidad", datos.get("kg", 0))

    for columna in ["producto", "albaran", "factura", "lote", "nif_cliente"]:

        if columna not in datos.columns:

            datos[columna] = ""

    return datos.sort_values(["fecha", "id"], na_position="last").to_dict(
        "records"
    )


def _movimientos(campana_id):

    conn = conectar()

    try:

        datos = _filtrar_campana_pdf(
            _leer_movimientos_contabilidad(conn=conn),
            campana_id,
        )

    finally:

        conn.close()

    if datos.empty:

        return []

    datos = datos.copy()
    terceros = datos.apply(_resolver_tercero_movimiento, axis=1)
    datos = pd.concat([datos, terceros], axis=1)
    datos["tercero"] = datos["tercero_resuelto"].fillna("")
    datos["facturas"] = datos.get("facturas_count", 0)
    return datos.sort_values(["fecha", "id"], na_position="last").to_dict(
        "records"
    )


def _facturas_movimientos(campana_id):

    conn = conectar()

    try:

        movimientos = _filtrar_campana_pdf(
            _leer_movimientos_contabilidad(conn=conn),
            campana_id,
        )
        documentos = _leer_tabla_conn_pdf(
            conn,
            "movimientos_economicos_documentos",
        )

    finally:

        conn.close()

    if movimientos.empty or documentos.empty:

        return []

    terceros = movimientos.apply(_resolver_tercero_movimiento, axis=1)
    movimientos = pd.concat([movimientos, terceros], axis=1)
    movimientos["tercero"] = movimientos["tercero_resuelto"].fillna("")
    movimientos_por_id = {
        int(fila["id"]): fila
        for fila in movimientos.to_dict("records")
        if str(fila.get("id", "")).isdigit()
    }
    filas = []

    if "tipo_documento" in documentos.columns:

        documentos = documentos[
            documentos["tipo_documento"].fillna("").astype(str) == "factura"
        ].copy()

    for _, documento in documentos.iterrows():

        movimiento_id = pd.to_numeric(
            documento.get("movimiento_id"),
            errors="coerce",
        )

        if pd.isna(movimiento_id):

            continue

        movimiento = movimientos_por_id.get(int(movimiento_id))

        if not movimiento:

            continue

        fila = documento.to_dict()
        fila.update({
            "documento_id": fila.get("id"),
            "fecha": movimiento.get("fecha"),
            "tipo": movimiento.get("tipo"),
            "categoria": movimiento.get("categoria"),
            "concepto": movimiento.get("concepto"),
            "tercero": movimiento.get("tercero"),
            "numero_factura": movimiento.get("numero_factura"),
            "total": movimiento.get("total"),
            "cliente": movimiento.get("cliente"),
            "proveedor": movimiento.get("proveedor"),
        })
        filas.append(fila)

    return sorted(
        filas,
        key=lambda fila: (
            limpiar_texto_pdf(fila.get("fecha")),
            _entero_orden_pdf(fila.get("orden")),
            _entero_orden_pdf(fila.get("documento_id")),
        ),
    )


def _recetas_tratamientos(campana_id):

    conn = conectar()

    try:

        tratamientos = _filtrar_campana_pdf(
            _leer_tratamientos_guardados(conn=conn),
            campana_id,
        )
        documentos = _leer_tabla_conn_pdf(conn, "tratamientos_documentos")

    finally:

        conn.close()

    if tratamientos.empty or documentos.empty:

        return []

    tratamientos_por_id = {
        int(fila["id"]): fila
        for fila in tratamientos.to_dict("records")
        if str(fila.get("id", "")).isdigit()
    }

    if "tipo_documento" in documentos.columns:

        documentos = documentos[
            documentos["tipo_documento"].fillna("").astype(str) == "receta"
        ].copy()

    filas = []

    for _, documento in documentos.iterrows():

        tratamiento_id = pd.to_numeric(
            documento.get("tratamiento_id"),
            errors="coerce",
        )

        if pd.isna(tratamiento_id):

            continue

        tratamiento = tratamientos_por_id.get(int(tratamiento_id))

        if not tratamiento:

            continue

        fila = documento.to_dict()
        fila.update({
            "documento_id": fila.get("id"),
            "fecha_inicio": tratamiento.get("fecha_inicio"),
            "fecha_fin": tratamiento.get("fecha_fin"),
            "campana": tratamiento.get("campana"),
            "cultivo": tratamiento.get("cultivo"),
            "producto": tratamiento.get("producto"),
            "registro": tratamiento.get("registro_producto"),
            "plaga": tratamiento.get("plaga"),
            "dosis": tratamiento.get("dosis"),
            "caldo": tratamiento.get("caldo"),
            "superficie_tratada": tratamiento.get("superficie_tratada"),
            "plazo_seguridad": tratamiento.get("plazo_seguridad"),
            "aplicador": tratamiento.get("aplicador"),
            "parcelas": tratamiento.get("parcelas"),
        })
        filas.append(fila)

    return sorted(
        filas,
        key=lambda fila: (
            limpiar_texto_pdf(fila.get("fecha_inicio")),
            _entero_orden_pdf(fila.get("tratamiento_id")),
            _entero_orden_pdf(fila.get("orden")),
            _entero_orden_pdf(fila.get("documento_id")),
        ),
    )


def _ruta_factura(ruta_relativa):

    ruta = (DOCS_DIR / limpiar_texto_pdf(ruta_relativa)).resolve()
    documentos = DOCS_DIR.resolve()

    if documentos not in ruta.parents and ruta != documentos:

        raise ValueError("Ruta de factura fuera de documentos")

    return ruta


def _ruta_receta(ruta_relativa):

    ruta = (DOCS_DIR / limpiar_texto_pdf(ruta_relativa)).resolve()
    documentos = DOCS_DIR.resolve()

    if documentos not in ruta.parents and ruta != documentos:

        raise ValueError("Ruta de receta fuera de documentos")

    return ruta


def _practicas(campana_id):

    conn = conectar()

    try:

        datos = _filtrar_campana_pdf(
            _preparar_practicas_presentacion(
                _leer_practicas_guardadas(conn=conn)
            ),
            campana_id,
        )

    finally:

        conn.close()

    if datos.empty:

        return []

    datos = datos.copy()
    datos["cultivo"] = datos.get("cultivo_mostrado", datos.get("cultivo", ""))
    datos["operario"] = datos.get("proveedor", datos.get("prestador", ""))

    for columna in ["maquinaria", "superficie", "observaciones"]:

        if columna not in datos.columns:

            datos[columna] = ""

    return datos.sort_values(["fecha", "id"], na_position="last").to_dict(
        "records"
    )


def _styles():

    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    estilos = getSampleStyleSheet()
    color_primario = colors.HexColor(COLOR_PRIMARIO)
    color_secundario = colors.HexColor(COLOR_SECUNDARIO)
    color_texto = colors.HexColor(COLOR_TEXTO)
    color_muted = colors.HexColor(COLOR_MUTED)
    estilo_normal = ParagraphStyle(
        "CuadernoProNormal",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=color_texto,
        spaceAfter=3
    )
    cover_label = ParagraphStyle(
        "CuadernoProCoverLabel",
        parent=estilo_normal,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
        textColor=color_primario
    )
    cover_value = ParagraphStyle(
        "CuadernoProCoverValue",
        parent=estilo_normal,
        fontSize=9,
        leading=12
    )
    estilo_tabla_pequeno = ParagraphStyle(
        "CuadernoProTablaPequeno",
        parent=estilo_normal,
        fontSize=7,
        leading=8.4
    )
    estilo_tabla = ParagraphStyle(
        "CuadernoProTabla",
        parent=estilo_tabla_pequeno,
        fontSize=7.2,
        leading=8.8
    )
    header = ParagraphStyle(
        "CuadernoProHeader",
        parent=estilo_tabla_pequeno,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        textColor=color_primario
    )
    estilo_titulo_portada = ParagraphStyle(
        "CuadernoProTituloPortada",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=29,
        alignment=TA_CENTER,
        textColor=color_primario,
        spaceAfter=10
    )
    index_title = ParagraphStyle(
        "CuadernoProIndexTitle",
        parent=estilo_titulo_portada,
        fontSize=16,
        leading=20,
        spaceAfter=18
    )
    estilo_subtitulo = ParagraphStyle(
        "CuadernoProSubtitulo",
        parent=estilos["Normal"],
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        textColor=color_secundario,
        spaceAfter=8
    )
    section = ParagraphStyle(
        "CuadernoProSection",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=color_primario,
        spaceBefore=10,
        spaceAfter=6
    )
    estilo_titulo_seccion = ParagraphStyle(
        "CuadernoProTituloSeccion",
        parent=estilo_normal,
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        textColor=color_primario
    )
    estilo_subseccion = ParagraphStyle(
        "CuadernoProSubseccion",
        parent=estilo_normal,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=color_primario,
        spaceBefore=8,
        spaceAfter=5
    )
    summary_label = ParagraphStyle(
        "CuadernoProSummaryLabel",
        parent=estilo_tabla_pequeno,
        fontName="Helvetica-Bold",
        textColor=color_muted
    )
    summary_value = ParagraphStyle(
        "CuadernoProSummaryValue",
        parent=estilo_normal,
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=color_primario
    )
    estilo_muted = ParagraphStyle(
        "CuadernoProMuted",
        parent=estilo_normal,
        fontSize=7.5,
        leading=9.5,
        textColor=color_muted
    )
    cover_note = ParagraphStyle(
        "CuadernoProCoverNote",
        parent=estilo_muted,
        alignment=TA_CENTER
    )
    right = ParagraphStyle(
        "CuadernoProRight",
        parent=estilo_tabla_pequeno,
        alignment=TA_RIGHT
    )
    return {
        "normal": estilo_normal,
        "small": estilo_tabla_pequeno,
        "tabla": estilo_tabla,
        "header": header,
        "title": estilo_titulo_portada,
        "index_title": index_title,
        "subtitle": estilo_subtitulo,
        "section": section,
        "section_banner": estilo_titulo_seccion,
        "subsection": estilo_subseccion,
        "summary_label": summary_label,
        "summary_value": summary_value,
        "cover_label": cover_label,
        "cover_value": cover_value,
        "cover_note": cover_note,
        "muted": estilo_muted,
        "right": right,
        "estilo_titulo_portada": estilo_titulo_portada,
        "estilo_subtitulo": estilo_subtitulo,
        "estilo_titulo_seccion": estilo_titulo_seccion,
        "estilo_subseccion": estilo_subseccion,
        "estilo_normal": estilo_normal,
        "estilo_tabla": estilo_tabla,
        "estilo_tabla_pequeno": estilo_tabla_pequeno,
        "estilo_muted": estilo_muted,
    }


def _tabla(data, col_widths=None, font_size=7, right_align=None):

    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    right_align = right_align or []
    tabla = Table(
        data,
        colWidths=col_widths,
        repeatRows=1,
        splitByRow=True
    )
    reglas = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_CABECERA_TABLA)),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 1.4),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(COLOR_TEXTO)),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor(COLOR_BORDE)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    for columna in right_align:

        reglas.append(("ALIGN", (columna, 1), (columna, -1), "RIGHT"))

    tabla.setStyle(TableStyle(reglas))
    return tabla


def _sin_registros_box(texto, styles):

    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    tabla = Table(
        [[Paragraph(escape(texto), styles["muted"])]],
        colWidths=[CONTENT_WIDTH],
        hAlign="LEFT"
    )
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAF8")),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor(COLOR_BORDE)),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return tabla


def crear_tabla_pdf(
    titulo,
    columnas,
    filas,
    anchos=None,
    styles=None,
    font_size=7,
    right_align=None
):

    from reportlab.platypus import Paragraph, Spacer

    styles = styles or _styles()
    story = [
        Paragraph(escape(titulo), styles["subsection"])
    ]

    if not filas:

        story.append(_sin_registros_box("Sin registros", styles))
        story.append(Spacer(1, 8))
        return story

    data = [
        [
            Paragraph(escape(abreviar_texto_largo(columna)), styles["header"])
            for columna in columnas
        ]
    ]

    for fila in filas:

        data.append([
            Paragraph(
                escape(abreviar_texto_largo(valor)),
                styles["right"] if indice in (right_align or []) else styles["tabla"]
            )
            for indice, valor in enumerate(fila)
        ])

    story.append(
        _tabla(
            data,
            col_widths=anchos,
            font_size=font_size,
            right_align=right_align
        )
    )
    story.append(Spacer(1, 8))
    return story


def _encabezado_seccion(titulo, styles):

    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    tabla = Table(
        [[Paragraph(escape(titulo), styles["section_banner"])]],
        colWidths=[CONTENT_WIDTH],
        hAlign="LEFT"
    )
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COLOR_CABECERA_TABLA)),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor(COLOR_BORDE)),
        ("LINEBELOW", (0, 0), (-1, -1), 0.6, colors.HexColor(COLOR_SECUNDARIO)),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [tabla, Spacer(1, 8)]


def _resumen_linea(texto, styles):

    from reportlab.platypus import Paragraph, Spacer

    return [
        Paragraph(escape(texto), styles["muted"]),
        Spacer(1, 6),
    ]


def _tarjeta_metricas(titulo, metricas, styles, width=250):

    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    data = [
        [Paragraph(escape(titulo), styles["subsection"]), ""]
    ]
    data.extend([
        [
            Paragraph(escape(etiqueta), styles["summary_label"]),
            Paragraph(escape(valor), styles["summary_value"]),
        ]
        for etiqueta, valor in metricas
    ])
    tabla = Table(data, colWidths=[width * 0.58, width * 0.42])
    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_CABECERA_TABLA)),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor(COLOR_BORDE)),
        ("INNERGRID", (0, 1), (-1, -1), 0.25, colors.HexColor("#D7DCD4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]))
    return tabla


def _fila_tarjetas(tarjetas):

    from reportlab.platypus import Spacer, Table, TableStyle

    tabla = Table(
        [tarjetas],
        colWidths=[(CONTENT_WIDTH - 24) / len(tarjetas)] * len(tarjetas),
        hAlign="LEFT"
    )
    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [tabla, Spacer(1, 8)]


def _indice_story(styles):

    from reportlab.platypus import Paragraph, Spacer

    secciones = [
        "Información general",
        "Identificación de parcelas",
        "Tratamientos fitosanitarios",
        "Análisis de productos fitosanitarios",
        "Cosecha comercializada",
        "Fertilización",
        "Ayudas / compromisos",
        "Contabilidad agrícola",
        "Prácticas culturales y labores agrícolas",
        "Documentación a conservar",
    ]
    izquierda = list(enumerate(secciones[:5], start=1))
    derecha = list(enumerate(secciones[5:], start=6))
    data = [
        [_celda("Nº", styles["header"]), _celda("Contenido", styles["header"]), _celda("Nº", styles["header"]), _celda("Contenido", styles["header"])]
    ]

    for (numero_1, titulo_1), (numero_2, titulo_2) in zip(izquierda, derecha):

        data.append([
            _celda(str(numero_1), styles["small"]),
            _celda(titulo_1, styles["small"]),
            _celda(str(numero_2), styles["small"]),
            _celda(titulo_2, styles["small"]),
        ])

    return [
        Spacer(1, 30),
        Paragraph("ÍNDICE DEL CUADERNO", styles["index_title"]),
        Paragraph(
            "Secciones principales del cuaderno de explotación.",
            styles["cover_note"]
        ),
        Spacer(1, 10),
        _tabla(data, col_widths=[38, 335, 38, 335], font_size=8),
    ]


def _parcelas_unicas(parcelas):

    unicas = {}

    for fila in parcelas:

        parcela_id = _clave_deduplicacion_parcela(fila)

        if parcela_id not in unicas:

            unicas[parcela_id] = fila

    return list(unicas.values())


def _resumen_economico(movimientos):

    ingresos = [
        fila for fila in movimientos
        if limpiar_texto_pdf(fila.get("tipo")).lower() == "ingreso"
    ]
    gastos = [
        fila for fila in movimientos
        if limpiar_texto_pdf(fila.get("tipo")).lower() == "gasto"
    ]
    total_ingresos = sum(_numero(fila.get("total")) for fila in ingresos)
    total_gastos = sum(_numero(fila.get("total")) for fila in gastos)
    iva_repercutido = sum(_numero(fila.get("iva_importe")) for fila in ingresos)
    iva_soportado = sum(_numero(fila.get("iva_importe")) for fila in gastos)
    pendiente_cobrar = sum(
        _numero(fila.get("total"))
        for fila in ingresos
        if not int(_numero(fila.get("pagado")))
    )
    pendiente_pagar = sum(
        _numero(fila.get("total"))
        for fila in gastos
        if not int(_numero(fila.get("pagado")))
    )
    return {
        "ingresos": total_ingresos,
        "gastos": total_gastos,
        "resultado": total_ingresos - total_gastos,
        "iva_repercutido": iva_repercutido,
        "iva_soportado": iva_soportado,
        "pendiente_cobrar": pendiente_cobrar,
        "pendiente_pagar": pendiente_pagar,
    }


def _resumen_general_story(
    styles,
    parcelas,
    tratamientos,
    fertilizaciones,
    cosechas,
    movimientos,
    practicas
):

    from reportlab.platypus import Paragraph, Spacer

    parcelas_unicas = _parcelas_unicas(parcelas)
    economia = _resumen_economico(movimientos)
    superficie_sigpac = sum(
        _numero(fila.get("superficie_sigpac"))
        for fila in parcelas_unicas
    )
    superficie_cultivada = sum(
        _numero(fila.get("superficie_cultivada"))
        for fila in parcelas_unicas
    )
    kg_cosechados = sum(_numero(fila.get("kg")) for fila in cosechas)
    ancho_tarjeta = (CONTENT_WIDTH - 24) / 3
    tarjetas = [
        _tarjeta_metricas(
            "Explotación",
            [
                ("Nº parcelas", str(len(parcelas_unicas))),
                ("Sup. SIGPAC", f"{numero_es(superficie_sigpac)} ha"),
                ("Sup. cultivada", f"{numero_es(superficie_cultivada)} ha"),
            ],
            styles,
            width=ancho_tarjeta
        ),
        _tarjeta_metricas(
            "Actividad",
            [
                ("Tratamientos", str(len(tratamientos))),
                ("Prácticas", str(len(practicas))),
                ("Fertilizaciones", str(len(fertilizaciones))),
                ("Kg cosechados", f"{numero_es(kg_cosechados)} kg"),
            ],
            styles,
            width=ancho_tarjeta
        ),
        _tarjeta_metricas(
            "Economía",
            [
                ("Ingresos", importe_es(economia["ingresos"])),
                ("Gastos", importe_es(economia["gastos"])),
                ("Resultado", importe_es(economia["resultado"])),
                ("Pte. cobrar", importe_es(economia["pendiente_cobrar"])),
                ("Pte. pagar", importe_es(economia["pendiente_pagar"])),
            ],
            styles,
            width=ancho_tarjeta
        ),
    ]
    story = _encabezado_seccion("RESUMEN GENERAL DE CAMPAÑA", styles)
    story.extend([
        Paragraph(
            "Resumen calculado con los registros disponibles para la campaña seleccionada.",
            styles["muted"]
        ),
        Spacer(1, 8),
    ])
    story.extend(_fila_tarjetas(tarjetas))
    return story


def _datos_generales_story(styles, explotacion, campana):

    from reportlab.platypus import Paragraph, Spacer

    campos = [
        ("Titular", _valor(explotacion, "titular", "nombre_explotacion")),
        ("NIF", explotacion.get("nif")),
        (
            "Código REGEPA / identificador oficial",
            _registro_nacional_explotacion(explotacion),
        ),
        (
            "Registro autonómico",
            _registro_autonomico_explotacion(explotacion),
        ),
        ("Dirección", explotacion.get("direccion")),
        ("Municipio", _valor(explotacion, "municipio", "localidad")),
        ("Código postal", explotacion.get("codigo_postal")),
        ("Provincia", explotacion.get("provincia")),
        ("Teléfono", explotacion.get("telefono")),
        ("Email", explotacion.get("email")),
        ("Campaña", campana.get("nombre")),
        ("Fecha de apertura", _fecha_apertura_portada(campana)),
        ("Responsable", _valor(explotacion, "responsable_nombre", "titular")),
        ("Asesor", _valor(explotacion, "asesor_nombre")),
        ("Tipo explotación", explotacion.get("tipo_explotacion")),
        ("Orientación productiva", explotacion.get("orientacion_productiva")),
        (
            "Agricultor activo",
            _texto_pagado(explotacion.get("agricultor_activo")),
        ),
        (
            "Joven agricultor",
            _texto_pagado(explotacion.get("joven_agricultor")),
        ),
    ]

    data = [
        [
            _celda("Campo", styles["header"]),
            _celda("Valor", styles["header"]),
            _celda("Campo", styles["header"]),
            _celda("Valor", styles["header"]),
        ]
    ]

    for indice in range(0, len(campos), 2):

        campo_1, valor_1 = campos[indice]
        campo_2, valor_2 = campos[indice + 1] if indice + 1 < len(campos) else ("", "")
        data.append([
            _celda(campo_1, styles["small"]),
            _celda(valor_1, styles["small"]),
            _celda(campo_2, styles["small"]),
            _celda(valor_2, styles["small"]),
        ])

    story = _encabezado_seccion("1. INFORMACIÓN GENERAL", styles)
    story.extend([
        Paragraph("1.1 Datos generales de la explotación", styles["subsection"]),
        _tabla(data, col_widths=[95, 285, 95, 285], font_size=8),
        Spacer(1, 8),
    ])

    asesor = _valor(explotacion, "asesor_nombre", "asesor_nif", "asesor_numero_registro")
    story.append(Paragraph("1.4 Asesor / entidad de asesoramiento", styles["subsection"]))

    if asesor:

        asesor_data = [
            [_celda("Nombre", styles["header"]), _celda("NIF", styles["header"]), _celda("Nº registro", styles["header"]), _celda("Teléfono", styles["header"])],
            [
                _celda(explotacion.get("asesor_nombre"), styles["small"]),
                _celda(explotacion.get("asesor_nif"), styles["small"]),
                _celda(explotacion.get("asesor_numero_registro"), styles["small"]),
                _celda(explotacion.get("asesor_telefono"), styles["small"]),
            ]
        ]
        story.append(_tabla(asesor_data, col_widths=[260, 120, 180, 120], font_size=8))

    else:

        story.append(Paragraph("Sin asesor registrado", styles["normal"]))

    story.append(Spacer(1, 8))
    return story


def _portada(styles, explotacion, campana):

    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    titular = _valor(explotacion, "titular", "nombre_explotacion")
    localidad_provincia = " / ".join(
        parte
        for parte in [
            _valor(explotacion, "municipio", "localidad"),
            limpiar_texto_pdf(explotacion.get("provincia")),
        ]
        if parte
    )
    campos = [
        ("Titular:", titular),
        ("NIF:", explotacion.get("nif")),
        ("Campaña:", campana.get("nombre")),
        ("Fecha de apertura:", _fecha_apertura_portada(campana)),
        (
            "Registro explotación nacional:",
            _registro_nacional_explotacion(explotacion)
        ),
        ("Registro autonómico:", _registro_autonomico_explotacion(explotacion)),
        ("Localidad / Provincia:", localidad_provincia),
    ]
    data = [
        [
            Paragraph(escape(etiqueta), styles["cover_label"]),
            Paragraph(escape(limpiar_texto_pdf(valor) or "Sin datos"), styles["cover_value"]),
        ]
        for etiqueta, valor in campos
    ]
    ficha = Table(
        data,
        colWidths=[210, 390],
        hAlign="CENTER"
    )
    ficha.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(COLOR_CABECERA_TABLA)),
        ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor(COLOR_BORDE)),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7DCD4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    fecha_generacion = fecha_es(datetime.now().date())
    return [
        Spacer(1, 58),
        Paragraph("CUADERNO DE EXPLOTACIÓN AGRÍCOLA", styles["title"]),
        Paragraph(f"Generado por {APP_NAME}", styles["subtitle"]),
        Spacer(1, 22),
        ficha,
        Spacer(1, 26),
        Paragraph(APP_DESCRIPTION, styles["subtitle"]),
        Paragraph(
            f"Fecha de generación: {escape(fecha_generacion)}",
            styles["cover_note"]
        ),
    ]


def _on_page(titular, campana_nombre):

    def draw(canvas, doc):
        from reportlab.lib import colors

        if doc.page == 1:

            return

        canvas.saveState()
        width, height = doc.pagesize
        canvas.setFillColor(colors.HexColor(COLOR_MUTED))
        canvas.setFont("Helvetica", 8)
        canvas.drawString(doc.leftMargin, height - 20, APP_NAME)
        canvas.drawCentredString(width / 2, height - 20, limpiar_texto_pdf(titular, 70))
        canvas.drawRightString(width - doc.rightMargin, height - 20, f"Campaña: {limpiar_texto_pdf(campana_nombre, 40)}")
        canvas.setStrokeColor(colors.HexColor(COLOR_BORDE))
        canvas.setLineWidth(0.3)
        canvas.line(doc.leftMargin, height - 29, width - doc.rightMargin, height - 29)
        canvas.line(doc.leftMargin, 26, width - doc.rightMargin, 26)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(doc.leftMargin, 14, f"Generado por {APP_NAME}")
        canvas.drawRightString(width - doc.rightMargin, 14, f"Página {doc.page}")
        canvas.restoreState()

    return draw


def _documentacion_story(styles):

    from reportlab.platypus import Paragraph, Spacer

    documentos = [
        "Facturas o documentos de adquisición de productos fitosanitarios.",
        "Contratos o justificantes de servicios realizados por terceros.",
        "Certificados de inspección de equipos de aplicación.",
        "Justificantes de entrega de envases vacíos.",
        "Boletines de análisis, si los hubiera.",
        "Documentación relativa al asesoramiento recibido.",
        "Albaranes o facturas de venta de cosecha.",
        "Justificantes de fertilizantes, semillas, labores y otros insumos.",
    ]
    story = _encabezado_seccion("10. DOCUMENTACIÓN A CONSERVAR", styles)
    story.append(Paragraph(
        "Se recomienda conservar junto al cuaderno, durante al menos 3 años, "
        "la documentación justificativa que proceda.",
        styles["normal"]
    ))
    story.append(Spacer(1, 6))
    story.extend([
        Paragraph(f"- {escape(documento)}", styles["normal"])
        for documento in documentos
    ])
    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            f"Documento generado automáticamente por {APP_NAME}.",
            styles["muted"]
        )
    )
    return story


def _balance(movimientos):

    economia = _resumen_economico(movimientos)

    return [
        ("Ingresos totales", importe_es(economia["ingresos"])),
        ("Gastos totales", importe_es(economia["gastos"])),
        ("Resultado", importe_es(economia["resultado"])),
        ("IVA soportado", importe_es(economia["iva_soportado"])),
        ("IVA repercutido", importe_es(economia["iva_repercutido"])),
        ("Pendiente de cobrar", importe_es(economia["pendiente_cobrar"])),
        ("Pendiente de pagar", importe_es(economia["pendiente_pagar"])),
    ]


def _tercero_movimiento(fila):

    return (
        limpiar_texto_pdf(fila.get("cliente"))
        or limpiar_texto_pdf(fila.get("proveedor"))
        or limpiar_texto_pdf(fila.get("tercero"))
    )


def _factura_separador_story(styles, factura):

    from reportlab.platypus import Paragraph, Spacer

    movimiento_id = int(factura.get("movimiento_id") or 0)
    documento_id = int(factura.get("documento_id") or 0)
    tercero = _tercero_movimiento(factura)
    referencia = f"DOC-{documento_id}"
    story = _encabezado_seccion("ANEXOS DE FACTURAS", styles)
    story.append(Paragraph(
        f"Factura anexa al movimiento contable #{movimiento_id}",
        styles["subsection"]
    ))
    story.append(Spacer(1, 8))
    filas = [
        ("ID del movimiento", f"#{movimiento_id}"),
        ("Fecha", fecha_es(factura.get("fecha"))),
        ("Tipo", limpiar_texto_pdf(factura.get("tipo"))),
        ("Número de factura", limpiar_texto_pdf(factura.get("numero_factura"))),
        ("Cliente / proveedor", tercero),
        ("Categoría", limpiar_texto_pdf(factura.get("categoria"))),
        ("Concepto", limpiar_texto_pdf(factura.get("concepto"))),
        ("Total", importe_es(factura.get("total"))),
        ("Archivo original", limpiar_texto_pdf(factura.get("nombre_original"))),
        ("Referencia interna", referencia),
    ]
    story.append(_tabla(
        [
            [
                Paragraph("Campo", styles["header"]),
                Paragraph("Valor", styles["header"]),
            ],
            *[
                [
                    Paragraph(escape(etiqueta), styles["tabla"]),
                    Paragraph(escape(valor), styles["tabla"]),
                ]
                for etiqueta, valor in filas
            ],
        ],
        col_widths=[180, CONTENT_WIDTH - 180],
        font_size=8
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "La factura PDF se inserta a continuación de esta página.",
        styles["muted"]
    ))
    return story


def _anexos_facturas_story(styles, facturas):

    from reportlab.platypus import PageBreak

    if not facturas:

        return []

    story = []

    for indice, factura in enumerate(facturas):

        story.append(PageBreak())
        story.extend(_factura_separador_story(styles, factura))

    return story


def _asesor_receta(explotacion):

    partes = [
        _valor(explotacion, "asesor_nombre"),
        _valor(explotacion, "asesor_numero_registro"),
        _valor(explotacion, "asesor_nif"),
    ]
    return " · ".join(parte for parte in partes if parte)


def _receta_separador_story(styles, receta, explotacion):

    from reportlab.platypus import Paragraph, Spacer

    tratamiento_id = int(receta.get("tratamiento_id") or 0)
    documento_id = int(receta.get("documento_id") or 0)
    referencia = f"RECETA-{documento_id}"
    caldo = _numero(receta.get("caldo"))
    dosis_caldo = limpiar_texto_pdf(receta.get("dosis"))

    if caldo:

        dosis_caldo = " / ".join(
            parte
            for parte in [dosis_caldo, f"{numero_es(caldo)} L caldo"]
            if parte
        )

    superficie = numero_es(receta.get("superficie_tratada"))

    if superficie:

        superficie = f"{superficie} ha"

    story = _encabezado_seccion(
        "ANEXOS DE RECETAS FITOSANITARIAS",
        styles
    )
    story.append(Paragraph(
        f"Receta anexa al tratamiento fitosanitario #{tratamiento_id}",
        styles["subsection"]
    ))
    story.append(Spacer(1, 8))
    filas = [
        ("ID del tratamiento", f"#{tratamiento_id}"),
        ("Fecha inicio", fecha_es(receta.get("fecha_inicio"))),
        ("Fecha fin", fecha_es(receta.get("fecha_fin"))),
        ("Campaña", limpiar_texto_pdf(receta.get("campana"))),
        ("Cultivo", limpiar_texto_pdf(receta.get("cultivo"))),
        ("Parcelas", limpiar_texto_pdf(receta.get("parcelas"))),
        ("Producto fitosanitario", limpiar_texto_pdf(receta.get("producto"))),
        ("Número de registro", limpiar_texto_pdf(receta.get("registro"))),
        ("Plaga / motivo", limpiar_texto_pdf(receta.get("plaga"))),
        ("Dosis / caldo", dosis_caldo),
        ("Superficie tratada", superficie),
        ("Plazo de seguridad", limpiar_texto_pdf(receta.get("plazo_seguridad"))),
        ("Aplicador", limpiar_texto_pdf(receta.get("aplicador"))),
        ("Asesor", _asesor_receta(explotacion)),
        ("Archivo original", limpiar_texto_pdf(receta.get("nombre_original"))),
        ("Referencia interna", referencia),
    ]
    story.append(_tabla(
        [
            [
                Paragraph("Campo", styles["header"]),
                Paragraph("Valor", styles["header"]),
            ],
            *[
                [
                    Paragraph(escape(etiqueta), styles["tabla"]),
                    Paragraph(escape(valor), styles["tabla"]),
                ]
                for etiqueta, valor in filas
            ],
        ],
        col_widths=[180, CONTENT_WIDTH - 180],
        font_size=8
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "La receta PDF se inserta a continuación de esta página.",
        styles["muted"]
    ))
    return story


def _anexos_recetas_story(styles, recetas, explotacion):

    from reportlab.platypus import PageBreak

    if not recetas:

        return []

    story = []

    for indice, receta in enumerate(recetas):

        story.append(PageBreak())
        story.extend(_receta_separador_story(styles, receta, explotacion))

    return story


def _pdf_aviso_factura(factura, mensaje):

    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pagina = landscape(A4)
    lienzo = canvas.Canvas(buffer, pagesize=pagina)
    ancho, alto = pagina
    movimiento_id = int(factura.get("movimiento_id") or 0)

    lienzo.setFont("Helvetica-Bold", 18)
    lienzo.drawString(48, alto - 70, "Factura no anexada")
    lienzo.setFont("Helvetica", 11)
    lineas = [
        f"Movimiento contable: #{movimiento_id}",
        f"Archivo: {limpiar_texto_pdf(factura.get('nombre_original'))}",
        f"Motivo: {limpiar_texto_pdf(mensaje, 180)}",
        "",
        (
            "El cuaderno se ha generado igualmente y continúa con el resto "
            "de anexos disponibles."
        ),
    ]
    y = alto - 110

    for linea in lineas:

        lienzo.drawString(48, y, linea)
        y -= 18

    lienzo.showPage()
    lienzo.save()
    buffer.seek(0)
    return buffer


def _pdf_aviso_receta(receta, mensaje):

    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pagina = landscape(A4)
    lienzo = canvas.Canvas(buffer, pagesize=pagina)
    ancho, alto = pagina
    tratamiento_id = int(receta.get("tratamiento_id") or 0)

    lienzo.setFont("Helvetica-Bold", 18)
    lienzo.drawString(48, alto - 70, "Receta no anexada")
    lienzo.setFont("Helvetica", 11)
    lineas = [
        f"Tratamiento fitosanitario: #{tratamiento_id}",
        f"Archivo: {limpiar_texto_pdf(receta.get('nombre_original'))}",
        f"Motivo: {limpiar_texto_pdf(mensaje, 180)}",
        "",
        (
            "El cuaderno se ha generado igualmente y continúa con el resto "
            "de anexos disponibles."
        ),
    ]
    y = alto - 110

    for linea in lineas:

        lienzo.drawString(48, y, linea)
        y -= 18

    lienzo.showPage()
    lienzo.save()
    buffer.seek(0)
    return buffer


def _insertar_anexos_en_pdf(
    pdf_base,
    pdf_salida,
    documentos,
    prefijo_referencia,
    resolver_ruta,
    crear_aviso
):

    if not documentos:

        shutil.move(str(pdf_base), str(pdf_salida))
        return

    from pypdf import PdfReader, PdfWriter

    documentos_por_referencia = {
        f"{prefijo_referencia}-{int(documento.get('documento_id') or 0)}":
        documento
        for documento in documentos
    }
    lector_base = PdfReader(str(pdf_base))
    escritor = PdfWriter()

    for pagina in lector_base.pages:

        escritor.add_page(pagina)
        texto = pagina.extract_text() or ""
        referencias = [
            referencia
            for referencia in documentos_por_referencia
            if referencia in texto
        ]

        for referencia in referencias:

            documento = documentos_por_referencia[referencia]

            try:

                ruta_documento = resolver_ruta(documento.get("ruta_relativa"))
                lector_documento = PdfReader(str(ruta_documento))

                for pagina_documento in lector_documento.pages:

                    escritor.add_page(pagina_documento)

            except Exception as error:

                aviso = crear_aviso(documento, str(error))
                lector_aviso = PdfReader(aviso)

                for pagina_aviso in lector_aviso.pages:

                    escritor.add_page(pagina_aviso)

    with open(pdf_salida, "wb") as destino:

        escritor.write(destino)

    try:

        pdf_base.unlink()

    except OSError:

        pass


def _insertar_facturas_en_pdf(pdf_base, pdf_salida, facturas):

    _insertar_anexos_en_pdf(
        pdf_base,
        pdf_salida,
        facturas,
        "DOC",
        _ruta_factura,
        _pdf_aviso_factura
    )


def _insertar_recetas_en_pdf(pdf_base, pdf_salida, recetas):

    _insertar_anexos_en_pdf(
        pdf_base,
        pdf_salida,
        recetas,
        "RECETA",
        _ruta_receta,
        _pdf_aviso_receta
    )


def generar_cuadernopro_pdf(campana_id):

    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph
    from reportlab.platypus import Spacer

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    campana = _campana(campana_id)
    explotacion = _datos_explotacion()
    titular = _valor(explotacion, "titular", "nombre_explotacion")
    parcelas, orden_parcelas = _parcelas_y_orden(campana_id)
    personas = _personas()
    equipos = _equipos()
    tratamientos = _tratamientos(campana_id)
    recetas_tratamientos = _recetas_tratamientos(campana_id)
    analisis_fitosanitarios = _analisis_fitosanitarios(campana_id)
    fertilizaciones = _fertilizaciones(campana_id)
    cosechas = _cosechas(campana_id)
    movimientos = _movimientos(campana_id)
    facturas_movimientos = _facturas_movimientos(campana_id)
    practicas = _practicas(campana_id)

    salida = EXPORTS_DIR / f"cuadernopro_cuaderno_{_nombre_archivo_seguro(campana['nombre'])}.pdf"
    pdf_base = EXPORTS_DIR / (
        f".{salida.stem}_base_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
    )
    landscape_size = landscape(A4)
    doc = BaseDocTemplate(
        str(pdf_base),
        pagesize=landscape_size,
        leftMargin=24,
        rightMargin=24,
        topMargin=44,
        bottomMargin=36
    )
    landscape_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="landscape"
    )
    on_page = _on_page(titular, campana.get("nombre"))
    doc.addPageTemplates([
        PageTemplate(id="Landscape", pagesize=landscape_size, frames=[landscape_frame], onPage=on_page),
    ])

    story = []
    story.extend(_portada(styles, explotacion, campana))
    story.append(PageBreak())
    story.extend(_indice_story(styles))
    story.append(PageBreak())
    story.extend(_resumen_general_story(
        styles,
        parcelas,
        tratamientos,
        fertilizaciones,
        cosechas,
        movimientos,
        practicas
    ))
    story.append(PageBreak())
    story.extend(_datos_generales_story(styles, explotacion, campana))

    personas_filas = [
        [
            indice,
            abreviar_persona(fila.get("nombre")),
            fila.get("nif"),
            fila.get("rol"),
            fila.get("carnet_fitosanitario"),
            fila.get("numero_asesor"),
            fila.get("telefono"),
            abreviar_texto_largo(fila.get("observaciones"), 90),
        ]
        for indice, fila in enumerate(personas, start=1)
    ]
    story.extend(crear_tabla_pdf(
        "1.2 Personas relacionadas con tratamientos fitosanitarios",
        ["Orden", "Nombre", "NIF", "Rol", "Carnet", "Nº asesor", "Teléfono", "Observaciones"],
        personas_filas,
        anchos=[38, 170, 80, 90, 90, 75, 80, 170],
        styles=styles,
        font_size=7
    ))

    equipos_filas = [
        [
            indice,
            abreviar_maquinaria(_descripcion_equipo(fila)),
            abreviar_maquinaria(fila.get("tipo"), 55),
            abreviar_maquinaria(" / ".join(part for part in [limpiar_texto_pdf(fila.get("marca")), limpiar_texto_pdf(fila.get("modelo"))] if part), 70),
            fila.get("matricula"),
            fila.get("numero_roma"),
            fila.get("numero_serie"),
            fecha_es(fila.get("fecha_adquisicion")),
            fecha_es(fila.get("fecha_ultima_inspeccion")),
            fecha_es(fila.get("fecha_proxima_inspeccion")),
            numero_es(fila.get("capacidad_litros")),
        ]
        for indice, fila in enumerate(equipos, start=1)
    ]
    story.extend(crear_tabla_pdf(
        "1.3 Equipos de aplicación fitosanitaria",
        [
            "Orden",
            "Descripción",
            "Tipo",
            "Marca/modelo",
            "Matrícula",
            "ROMA",
            "Serie",
            "F. adquisición",
            "Última revisión",
            "Próxima revisión",
            "Cap. l",
        ],
        equipos_filas,
        anchos=[32, 140, 75, 90, 60, 60, 70, 70, 75, 75, 45],
        styles=styles,
        font_size=6.4
    ))

    story.append(PageBreak())
    story.extend(_encabezado_seccion("2. IDENTIFICACIÓN DE PARCELAS", styles))
    parcelas_unicas = _parcelas_unicas(parcelas)
    superficie_sigpac = sum(
        _numero(fila.get("superficie_sigpac"))
        for fila in parcelas_unicas
    )
    superficie_cultivada = sum(
        _numero(fila.get("superficie_cultivada"))
        for fila in parcelas_unicas
    )
    story.extend(_resumen_linea(
        "Total parcelas: "
        f"{len(parcelas_unicas)} · Superficie SIGPAC: "
        f"{numero_es(superficie_sigpac)} ha · Superficie cultivada: "
        f"{numero_es(superficie_cultivada)} ha",
        styles
    ))

    parcelas_filas = [
        [
            fila.get("_orden"),
            fila.get("provincia_sigpac"),
            abreviar_texto_largo(" ".join(part for part in [limpiar_texto_pdf(fila.get("municipio_sigpac")), limpiar_texto_pdf(fila.get("municipio"))] if part), 55),
            fila.get("agregado_sigpac"),
            fila.get("zona_sigpac"),
            fila.get("poligono"),
            fila.get("parcela"),
            fila.get("recinto"),
            numero_es(fila.get("superficie_sigpac")),
            numero_es(fila.get("superficie_cultivada")),
            abreviar_cultivo(fila.get("especie"), 50),
            abreviar_texto_largo(fila.get("variedad"), 55),
            abreviar_texto_largo(fila.get("sistema"), 35),
            abreviar_texto_largo(
                " / ".join(
                    parte
                    for parte in [
                        limpiar_texto_pdf(fila.get("marco_plantacion")),
                        limpiar_texto_pdf(fila.get("numero_arboles")),
                    ]
                    if parte
                ),
                42,
            ),
            abreviar_texto_largo(fila.get("observaciones"), 90),
        ]
        for fila in parcelas
    ]
    story.extend(crear_tabla_pdf(
        "2.1 Parcelas y datos agronómicos",
        ["Orden", "Prov.", "Municipio", "Agr.", "Zona", "Políg.", "Parcela", "Recinto", "Sup. SIGPAC", "Sup. cult.", "Especie", "Variedad", "Sistema", "Marco/árb.", "Observaciones"],
        parcelas_filas,
        anchos=[28, 30, 85, 24, 24, 34, 38, 34, 50, 50, 85, 75, 40, 55, 85],
        styles=styles,
        font_size=6.8,
        right_align=[8, 9]
    ))

    story.append(PageBreak())
    story.extend(_encabezado_seccion("3. TRATAMIENTOS FITOSANITARIOS", styles))
    productos_distintos = {
        limpiar_texto_pdf(fila.get("producto")).casefold()
        for fila in tratamientos
        if limpiar_texto_pdf(fila.get("producto"))
    }
    superficie_tratada_total = sum(
        _numero(fila.get("superficie_tratada"))
        for fila in tratamientos
    )
    story.extend(_resumen_linea(
        "Tratamientos registrados: "
        f"{len(tratamientos)} · Superficie tratada total: "
        f"{numero_es(superficie_tratada_total)} ha · Productos distintos: "
        f"{len(productos_distintos)}",
        styles
    ))
    tratamientos_filas = []

    for fila in tratamientos:

        parcelas_texto = limpiar_texto_pdf(fila.get("parcelas"))

        if not parcelas_texto:

            ids = _ids_parcelas(
                "tratamiento_parcelas",
                "tratamiento_id",
                fila["id"],
            )
            parcelas_texto = abreviar_parcelas(ids, orden_parcelas)

        tratamientos_filas.append([
            abreviar_texto_largo(parcelas_texto, 70),
            abreviar_cultivo(fila.get("cultivo"), 60),
            fecha_es(fila.get("fecha_inicio")),
            fecha_es(fila.get("fecha_fin")),
            numero_es(fila.get("superficie_tratada")),
            abreviar_texto_largo(fila.get("plaga"), 65),
            abreviar_persona(fila.get("aplicador"), 55),
            abreviar_maquinaria(fila.get("equipo"), 55),
            abreviar_texto_largo(fila.get("producto"), 65),
            fila.get("registro"),
            abreviar_dosis(fila.get("dosis"), 42),
            fila.get("plazo_seguridad"),
            _eficacia_pdf(fila.get("eficacia")),
            abreviar_texto_largo(fila.get("observaciones"), 90),
        ])

    story.extend(crear_tabla_pdf(
        "3.1 Registro de actuaciones fitosanitarias",
        ["Parcelas", "Cultivo", "Inicio", "Fin", "Superf.", "Plaga/problema", "Aplicador", "Equipo", "Producto", "Registro", "Dosis", "P. seg.", "Ef.", "Observaciones"],
        tratamientos_filas,
        anchos=[56, 76, 50, 50, 38, 74, 64, 50, 76, 38, 62, 32, 27, 100],
        styles=styles,
        font_size=6.4,
        right_align=[4]
    ))

    story.extend(
        _anexos_recetas_story(styles, recetas_tratamientos, explotacion)
    )

    story.append(PageBreak())
    story.extend(_encabezado_seccion("4. ANÁLISIS DE PRODUCTOS FITOSANITARIOS", styles))
    analisis_filas = []

    for fila in analisis_fitosanitarios:

        ids_parcelas = _ids_desde_texto(fila.get("parcelas"))
        parcelas_texto = abreviar_parcelas(ids_parcelas, orden_parcelas)
        cultivo_parcelas = " / ".join(
            parte
            for parte in [
                abreviar_cultivo(fila.get("cultivo"), 70),
                parcelas_texto,
            ]
            if parte
        )
        resultado_observaciones = " / ".join(
            parte
            for parte in [
                limpiar_texto_pdf(fila.get("resultado")),
                limpiar_texto_pdf(fila.get("observaciones")),
            ]
            if parte
        )
        analisis_filas.append([
            fecha_es(fila.get("fecha")),
            abreviar_texto_largo(fila.get("material_analizado"), 70),
            cultivo_parcelas,
            abreviar_texto_largo(fila.get("boletin_numero"), 45),
            abreviar_texto_largo(fila.get("laboratorio"), 70),
            abreviar_texto_largo(fila.get("sustancias_detectadas"), 125),
            abreviar_texto_largo(resultado_observaciones, 160),
        ])

    story.extend(crear_tabla_pdf(
        "4.1 Registro de análisis realizados",
        [
            "Fecha",
            "Material analizado",
            "Cultivo / parcelas",
            "Nº boletín",
            "Laboratorio",
            "Sustancias detectadas",
            "Resultado / observaciones",
        ],
        analisis_filas,
        anchos=[54, 80, 125, 58, 90, 170, 216],
        styles=styles,
        font_size=6.6
    ))

    story.append(PageBreak())
    story.extend(_encabezado_seccion("5. COSECHA COMERCIALIZADA", styles))
    kg_cosechados = sum(_numero(fila.get("kg")) for fila in cosechas)
    story.extend(_resumen_linea(
        f"Kg cosechados: {numero_es(kg_cosechados)} · Operaciones: {len(cosechas)}",
        styles
    ))
    cosecha_filas = []

    for fila in cosechas:

        parcelas_texto = limpiar_texto_pdf(fila.get("parcelas"))

        if not parcelas_texto:

            ids = _ids_parcelas("cosecha_parcelas", "cosecha_id", fila["id"])
            parcelas_texto = abreviar_parcelas(ids, orden_parcelas)

        cosecha_filas.append([
            fecha_es(fila.get("fecha")),
            abreviar_cultivo(_valor(fila, "producto", "cultivo"), 75),
            numero_es(fila.get("kg")),
            abreviar_texto_largo(parcelas_texto, 72),
            fila.get("albaran"),
            fila.get("factura"),
            fila.get("lote"),
            abreviar_texto_largo(fila.get("cliente"), 80),
            fila.get("nif_cliente"),
            fila.get("destino"),
            abreviar_texto_largo(fila.get("observaciones"), 90),
        ])

    story.extend(crear_tabla_pdf(
        "5.1 Registro de cosecha comercializada",
        ["Fecha", "Producto", "Kg", "Parcelas", "Albarán", "Factura", "Lote", "Cliente", "NIF", "Destino", "Observaciones"],
        cosecha_filas,
        anchos=[48, 98, 52, 72, 55, 55, 50, 145, 65, 60, 93],
        styles=styles,
        font_size=7,
        right_align=[2]
    ))

    story.append(PageBreak())
    story.extend(_encabezado_seccion("6. FERTILIZACIÓN", styles))
    fertilizacion_filas = []

    for fila in fertilizaciones:

        parcelas_texto = limpiar_texto_pdf(fila.get("parcelas"))

        if not parcelas_texto:

            ids = _ids_parcelas(
                "fertilizacion_parcelas",
                "fertilizacion_id",
                fila["id"],
            )
            parcelas_texto = abreviar_parcelas(ids, orden_parcelas)

        fertilizacion_filas.append([
            fecha_es(fila.get("fecha")),
            abreviar_texto_largo(parcelas_texto, 70),
            abreviar_cultivo(fila.get("cultivo"), 70),
            abreviar_texto_largo(fila.get("producto"), 70),
            fila.get("tipo"),
            fila.get("riqueza_npk"),
            _cantidad_con_unidad(fila.get("cantidad"), fila.get("unidad")),
            numero_es(fila.get("superficie")),
            abreviar_texto_largo(fila.get("metodo_aplicacion"), 55),
            abreviar_persona(fila.get("operario"), 60),
            abreviar_texto_largo(fila.get("observaciones"), 95),
        ])

    story.extend(crear_tabla_pdf(
        "6.1 Registro de fertilizaciones",
        ["Fecha", "Parcelas", "Cultivo", "Producto", "Tipo", "NPK", "Cantidad", "Superf.", "Método", "Operario", "Observaciones"],
        fertilizacion_filas,
        anchos=[48, 60, 90, 105, 55, 48, 58, 55, 78, 75, 121],
        styles=styles,
        font_size=7
    ))

    story.append(PageBreak())
    story.extend(_encabezado_seccion("7. AYUDAS / COMPROMISOS", styles))
    story.append(Paragraph("Sin registros / no aplica.", styles["normal"]))
    story.append(Spacer(1, 8))

    story.append(PageBreak())
    story.extend(_encabezado_seccion("8. CONTABILIDAD AGRÍCOLA", styles))
    gastos = [
        fila for fila in movimientos
        if limpiar_texto_pdf(fila.get("tipo")).lower() == "gasto"
    ]
    ingresos = [
        fila for fila in movimientos
        if limpiar_texto_pdf(fila.get("tipo")).lower() == "ingreso"
    ]
    economia = _resumen_economico(movimientos)
    story.extend(_fila_tarjetas([
        _tarjeta_metricas(
            "Balance",
            [
                ("Ingresos", importe_es(economia["ingresos"])),
                ("Gastos", importe_es(economia["gastos"])),
                ("Resultado", importe_es(economia["resultado"])),
            ],
            styles,
            width=(CONTENT_WIDTH - 24) / 2
        ),
        _tarjeta_metricas(
            "IVA y pendientes",
            [
                ("IVA soportado", importe_es(economia["iva_soportado"])),
                ("IVA repercutido", importe_es(economia["iva_repercutido"])),
                ("Pte. cobrar", importe_es(economia["pendiente_cobrar"])),
                ("Pte. pagar", importe_es(economia["pendiente_pagar"])),
            ],
            styles,
            width=(CONTENT_WIDTH - 24) / 2
        ),
    ]))

    def movimiento_filas(datos):

        return [
            [
                fecha_es(fila.get("fecha")),
                fila.get("categoria"),
                abreviar_texto_largo(fila.get("concepto"), 90),
                abreviar_texto_largo(fila.get("tercero"), 80),
                fila.get("numero_factura"),
                importe_es(fila.get("base_imponible")),
                importe_es(fila.get("iva_importe")),
                importe_es(fila.get("total")),
                _texto_pagado(fila.get("pagado")),
                abreviar_texto_largo(fila.get("observaciones"), 110),
            ]
            for fila in datos
        ]

    columnas_mov = ["Fecha", "Categoría", "Concepto", "Tercero", "Factura", "Base", "IVA", "Total", "Pagado", "Observaciones"]
    anchos_mov = [48, 60, 150, 125, 54, 58, 50, 58, 42, 148]
    story.extend(crear_tabla_pdf("8.1 Gastos", columnas_mov, movimiento_filas(gastos), anchos=anchos_mov, styles=styles, font_size=7, right_align=[5, 6, 7]))
    story.extend(crear_tabla_pdf("8.2 Ingresos", columnas_mov, movimiento_filas(ingresos), anchos=anchos_mov, styles=styles, font_size=7, right_align=[5, 6, 7]))

    story.extend(_anexos_facturas_story(styles, facturas_movimientos))

    story.append(PageBreak())
    story.extend(_encabezado_seccion("9. PRÁCTICAS CULTURALES Y LABORES AGRÍCOLAS", styles))
    superficie_practicas = sum(
        _numero(fila.get("superficie"))
        for fila in practicas
    )
    story.extend(_resumen_linea(
        "Prácticas registradas: "
        f"{len(practicas)} · Superficie trabajada: "
        f"{numero_es(superficie_practicas)} ha",
        styles
    ))
    practicas_filas = []

    for fila in practicas:

        parcelas_texto = limpiar_texto_pdf(fila.get("parcelas"))

        if not parcelas_texto:

            ids = _ids_parcelas("practica_parcelas", "practica_id", fila["id"])
            parcelas_texto = abreviar_parcelas(ids, orden_parcelas)

        practicas_filas.append([
            fecha_es(fila.get("fecha")),
            abreviar_texto_largo(parcelas_texto, 70),
            abreviar_cultivo(fila.get("cultivo"), 75),
            abreviar_texto_largo(fila.get("labor"), 65),
            numero_es(fila.get("superficie")),
            abreviar_maquinaria(fila.get("maquinaria"), 95),
            abreviar_persona(fila.get("operario"), 70),
            abreviar_texto_largo(fila.get("observaciones"), 120),
        ])

    story.extend(crear_tabla_pdf(
        "9.1 Registro de prácticas culturales",
        ["Fecha", "Parcelas", "Cultivo", "Labor", "Superficie", "Maquinaria", "Operario", "Observaciones"],
        practicas_filas,
        anchos=[48, 60, 105, 110, 60, 160, 90, 160],
        styles=styles,
        font_size=7,
        right_align=[4]
    ))

    story.append(PageBreak())
    story.extend(_documentacion_story(styles))

    doc.build(story)
    if recetas_tratamientos:

        pdf_facturas = EXPORTS_DIR / (
            f".{salida.stem}_facturas_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
        )
        _insertar_facturas_en_pdf(
            pdf_base,
            pdf_facturas,
            facturas_movimientos
        )
        _insertar_recetas_en_pdf(pdf_facturas, salida, recetas_tratamientos)

    else:

        _insertar_facturas_en_pdf(pdf_base, salida, facturas_movimientos)

    return str(salida)
