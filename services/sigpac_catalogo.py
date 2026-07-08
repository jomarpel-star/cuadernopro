import csv
import re
import warnings
from functools import lru_cache
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT_DIR / "data" / "sigpac_provincias_municipios.csv"
COLUMNAS = [
    "provincia_codigo",
    "provincia_nombre",
    "municipio_codigo",
    "municipio_nombre",
    "provincia_label",
    "municipio_label",
]


def _limpiar_texto(valor):

    texto = "" if valor is None else str(valor).strip()
    return re.sub(r"\s+", " ", texto)


def _fallback_catalogo(motivo=None):

    if motivo:

        warnings.warn(
            "No se pudo cargar el catálogo SIGPAC completo; "
            f"se usará Murcia/Jumilla como fallback. Detalle: {motivo}",
            RuntimeWarning,
            stacklevel=2
        )

    return (
        {
            "provincia_codigo": 30,
            "provincia_nombre": "MURCIA",
            "municipio_codigo": 22,
            "municipio_nombre": "Jumilla",
            "provincia_label": "30 - MURCIA",
            "municipio_label": "22 - Jumilla",
        },
    )


def _entero(valor):

    try:

        return int(valor)

    except (TypeError, ValueError):

        return None


def _normalizar_fila(fila):

    provincia_codigo = _entero(fila.get("provincia_codigo"))
    municipio_codigo = _entero(fila.get("municipio_codigo"))

    if provincia_codigo is None or municipio_codigo is None:

        return None

    provincia_nombre = _limpiar_texto(fila.get("provincia_nombre"))
    municipio_nombre = _limpiar_texto(fila.get("municipio_nombre"))

    if not provincia_nombre or not municipio_nombre:

        return None

    return {
        "provincia_codigo": provincia_codigo,
        "provincia_nombre": provincia_nombre,
        "municipio_codigo": municipio_codigo,
        "municipio_nombre": municipio_nombre,
        "provincia_label": f"{provincia_codigo} - {provincia_nombre}",
        "municipio_label": f"{municipio_codigo} - {municipio_nombre}",
    }


@lru_cache(maxsize=1)
def cargar_catalogo():

    if not CSV_PATH.exists():

        return _fallback_catalogo(f"no existe {CSV_PATH}")

    try:

        with CSV_PATH.open(newline="", encoding="utf-8") as archivo:

            lector = csv.DictReader(archivo)
            columnas_faltantes = [
                columna
                for columna in COLUMNAS
                if columna not in (lector.fieldnames or [])
            ]

            if columnas_faltantes:

                return _fallback_catalogo(
                    "faltan columnas: "
                    + ", ".join(columnas_faltantes)
                )

            filas = [
                fila_normalizada
                for fila in lector
                if (fila_normalizada := _normalizar_fila(fila)) is not None
            ]

    except Exception as exc:

        return _fallback_catalogo(exc)

    if not filas:

        return _fallback_catalogo("el CSV no contiene códigos válidos")

    return tuple(
        sorted(
            filas,
            key=lambda fila: (
                fila["provincia_codigo"],
                fila["municipio_codigo"],
                fila["municipio_nombre"],
            )
        )
    )


def obtener_provincias():

    provincias = {}

    for fila in cargar_catalogo():

        codigo = fila["provincia_codigo"]

        if codigo not in provincias:

            provincias[codigo] = {
                "codigo": codigo,
                "nombre": fila["provincia_nombre"],
                "label": fila["provincia_label"],
            }

    return [
        provincias[codigo]
        for codigo in sorted(provincias)
    ]


def obtener_municipios(provincia_codigo):

    codigo = _entero(provincia_codigo)

    if codigo is None:

        return []

    municipios = [
        {
            "codigo": fila["municipio_codigo"],
            "nombre": fila["municipio_nombre"],
            "label": fila["municipio_label"],
        }
        for fila in cargar_catalogo()
        if fila["provincia_codigo"] == codigo
    ]

    return sorted(
        municipios,
        key=lambda municipio: (municipio["codigo"], municipio["nombre"])
    )


def buscar_provincia_por_label(label):

    etiqueta = _limpiar_texto(label)

    for provincia in obtener_provincias():

        if provincia["label"] == etiqueta:

            return provincia

    return None


def buscar_municipio_por_label(provincia_codigo, label):

    etiqueta = _limpiar_texto(label)

    for municipio in obtener_municipios(provincia_codigo):

        if municipio["label"] == etiqueta:

            return municipio

    return None
