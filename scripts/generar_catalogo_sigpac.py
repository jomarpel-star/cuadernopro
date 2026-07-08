#!/usr/bin/env python3
import csv
import json
import re
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


try:

    import requests

except ImportError:

    requests = None


BASE_URL = "https://sigpac-hubcloud.es/codigossigpac"
TIMEOUT = 15
ROOT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT_DIR / "data" / "sigpac_provincias_municipios.csv"


def _limpiar_texto(valor):

    texto = "" if valor is None else str(valor).strip()
    return re.sub(r"\s+", " ", texto)


def _capitalizar_municipio(valor):

    texto = _limpiar_texto(valor)

    if not texto or texto != texto.upper():

        return texto

    texto = texto.title()
    particulas = {
        " De ": " de ",
        " Del ": " del ",
        " La ": " la ",
        " Las ": " las ",
        " Los ": " los ",
        " El ": " el ",
        " Y ": " y ",
        " Da ": " da ",
        " Das ": " das ",
        " Do ": " do ",
        " Dos ": " dos ",
        " D'": " d'",
    }

    for origen, destino in particulas.items():

        texto = texto.replace(origen, destino)

    return texto


def _descargar_json(url):

    if requests is not None:

        respuesta = requests.get(url, timeout=TIMEOUT)
        respuesta.raise_for_status()
        return respuesta.json()

    with urlopen(url, timeout=TIMEOUT) as respuesta:

        contenido = respuesta.read().decode("utf-8")
        return json.loads(contenido)


def _extraer_codigos(datos, normalizar_nombre=None):

    if isinstance(datos, dict):

        registros = (
            datos.get("codigos")
            or datos.get("items")
            or datos.get("data")
            or datos.get("municipios")
            or datos.get("provincias")
            or []
        )

    else:

        registros = datos

    resultado = []

    for registro in registros or []:

        if not isinstance(registro, dict):

            continue

        codigo = (
            registro.get("codigo")
            or registro.get("id")
            or registro.get("cod")
        )
        nombre = (
            registro.get("descripcion")
            or registro.get("nombre")
            or registro.get("label")
        )

        try:

            codigo = int(codigo)

        except (TypeError, ValueError):

            continue

        if normalizar_nombre is None:

            nombre = _limpiar_texto(nombre)

        else:

            nombre = normalizar_nombre(nombre)

        if not nombre:

            continue

        resultado.append(
            {
                "codigo": codigo,
                "nombre": nombre,
            }
        )

    return resultado


def _descargar_provincias():

    datos = _descargar_json(f"{BASE_URL}/provincia.json")
    return _extraer_codigos(datos)


def _descargar_municipios(provincia_codigo):

    datos = _descargar_json(f"{BASE_URL}/municipio{provincia_codigo}.json")
    return _extraer_codigos(
        datos,
        normalizar_nombre=_capitalizar_municipio
    )


def generar_catalogo():

    try:

        provincias = _descargar_provincias()

    except Exception as exc:

        raise RuntimeError(
            f"No se pudo descargar el listado de provincias: {exc}"
        ) from exc

    if not provincias:

        raise RuntimeError("El listado de provincias SIGPAC está vacío.")

    filas = []
    provincias_con_municipios = 0
    provincias_fallidas = []

    for provincia in provincias:

        provincia_codigo = provincia["codigo"]
        provincia_nombre = provincia["nombre"]
        print(
            f"Descargando provincia {provincia_codigo} - "
            f"{provincia_nombre}..."
        )

        try:

            municipios = _descargar_municipios(provincia_codigo)

        except (RuntimeError, ValueError, URLError, OSError) as exc:

            print(
                "Aviso: no se pudieron descargar los municipios de "
                f"{provincia_codigo} - {provincia_nombre}: {exc}",
                file=sys.stderr
            )
            provincias_fallidas.append(provincia_codigo)
            continue

        if not municipios:

            print(
                "Aviso: la provincia "
                f"{provincia_codigo} - {provincia_nombre} no tiene "
                "municipios en la respuesta.",
                file=sys.stderr
            )
            provincias_fallidas.append(provincia_codigo)
            continue

        provincias_con_municipios += 1

        for municipio in municipios:

            municipio_codigo = municipio["codigo"]
            municipio_nombre = municipio["nombre"]
            filas.append(
                {
                    "provincia_codigo": provincia_codigo,
                    "provincia_nombre": provincia_nombre,
                    "municipio_codigo": municipio_codigo,
                    "municipio_nombre": municipio_nombre,
                    "provincia_label": (
                        f"{provincia_codigo} - {provincia_nombre}"
                    ),
                    "municipio_label": (
                        f"{municipio_codigo} - {municipio_nombre}"
                    ),
                }
            )

    if not filas:

        raise RuntimeError("No se descargó ningún municipio SIGPAC.")

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    with CSV_PATH.open("w", newline="", encoding="utf-8") as archivo:

        writer = csv.DictWriter(
            archivo,
            fieldnames=[
                "provincia_codigo",
                "provincia_nombre",
                "municipio_codigo",
                "municipio_nombre",
                "provincia_label",
                "municipio_label",
            ]
        )
        writer.writeheader()
        writer.writerows(filas)

    print(
        "Catálogo guardado en "
        f"{CSV_PATH.relative_to(ROOT_DIR)}: "
        f"{provincias_con_municipios} provincias y "
        f"{len(filas)} municipios."
    )

    if provincias_fallidas:

        print(
            "Provincias con aviso/error: "
            + ", ".join(str(codigo) for codigo in provincias_fallidas),
            file=sys.stderr
        )


def main():

    try:

        generar_catalogo()

    except Exception as exc:

        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":

    raise SystemExit(main())
