import argparse
from importlib import metadata
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PACKAGES = {"pip", "setuptools"}

LICENSE_OVERRIDES = {
    "altair": "BSD-3-Clause",
    "blinker": "MIT",
    "colorama": "BSD-3-Clause",
    "gitdb": "BSD-3-Clause",
    "itsdangerous": "BSD-3-Clause",
    "jinja2": "BSD-3-Clause",
    "pandas": "BSD-3-Clause",
    "pyinstaller": "GPL-2.0-or-later con excepción de distribución",
    "pyinstaller-hooks-contrib": (
        "GPL-2.0-or-later; runtime hooks Apache-2.0"
    ),
    "pyogrio": "MIT",
    "python-dateutil": "Apache-2.0 OR BSD-3-Clause",
    "reportlab": "BSD-3-Clause",
    "shapely": "BSD-3-Clause",
    "streamlit-folium": "MIT",
}

URL_OVERRIDES = {
    "blinker": "https://github.com/pallets-eco/blinker",
    "colorama": "https://github.com/tartley/colorama",
    "itsdangerous": "https://github.com/pallets/itsdangerous",
    "pyinstaller-hooks-contrib": (
        "https://github.com/pyinstaller/pyinstaller-hooks-contrib"
    ),
    "streamlit-folium": "https://github.com/randyzwitch/streamlit-folium",
}

LICENSE_ALIASES = {
    "3-Clause BSD License": "BSD-3-Clause",
    "Apache License 2.0": "Apache-2.0",
    "Apache Software License": "Apache-2.0",
    "BSD License": "BSD",
    "MIT License": "MIT",
    "Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "Python Software Foundation License": "PSF-2.0",
}


def _normalizar_nombre(nombre):
    return re.sub(r"[-_.]+", "-", nombre).casefold()


def _licencia(distribucion, clave):
    if clave in LICENSE_OVERRIDES:
        return LICENSE_OVERRIDES[clave]

    valor = (
        distribucion.metadata.get("License-Expression")
        or distribucion.metadata.get("License")
        or ""
    ).strip()
    valor = re.sub(r"\s+", " ", valor)

    if valor and len(valor) <= 120 and not valor.casefold().startswith(
        "copyright"
    ):
        return LICENSE_ALIASES.get(valor, valor)

    clasificadores = distribucion.metadata.get_all("Classifier") or []
    for clasificador in clasificadores:
        prefijo = "License :: OSI Approved :: "
        if clasificador.startswith(prefijo):
            nombre = clasificador.removeprefix(prefijo)
            return LICENSE_ALIASES.get(nombre, nombre)

    raise RuntimeError(
        f"Licencia sin identificar para {distribucion.metadata.get('Name')}"
    )


def _url(distribucion, clave, nombre):
    if clave in URL_OVERRIDES:
        return URL_OVERRIDES[clave]

    urls = []
    for valor in distribucion.metadata.get_all("Project-URL") or []:
        if "," in valor:
            etiqueta, url = valor.split(",", 1)
            urls.append((etiqueta.strip().casefold(), url.strip()))

    for etiqueta_buscada in (
        "source",
        "homepage",
        "repository",
        "documentation",
    ):
        for etiqueta, url in urls:
            if etiqueta == etiqueta_buscada:
                return url

    return (
        distribucion.metadata.get("Home-page")
        or f"https://pypi.org/project/{nombre}/"
    )


def _escapar_tabla(valor):
    return str(valor).replace("|", "/").replace("\n", " ")


def generar(version, fecha_revision):
    filas = []
    for distribucion in metadata.distributions():
        nombre = distribucion.metadata.get("Name")
        if not nombre:
            continue

        clave = _normalizar_nombre(nombre)
        if clave in EXCLUDED_PACKAGES:
            continue

        filas.append(
            (
                nombre,
                distribucion.version,
                _licencia(distribucion, clave),
                _url(distribucion, clave, nombre),
            )
        )

    filas.sort(key=lambda fila: fila[0].casefold())

    lineas = [
        "# Avisos de terceros",
        "",
        f"Inventario generado desde el entorno de build de CuadernoPro {version}.",
        "Incluye dependencias directas, transitivas y herramientas cuyos",
        "componentes se incorporan al ejecutable Windows. `pip` y `setuptools`",
        "se excluyen porque solo preparan el entorno y no se distribuyen.",
        "",
        "Las licencias pertenecen a sus respectivos titulares. Este inventario",
        "no sustituye los textos de licencia originales incluidos por cada",
        "proyecto ni cambia la licencia GPL-3.0-or-later de CuadernoPro.",
        "",
        "## Paquetes Python y de empaquetado",
        "",
        "| Paquete | Versión | Licencia | Fuente |",
        "| --- | ---: | --- | --- |",
    ]
    for fila in filas:
        lineas.append(
            "| " + " | ".join(_escapar_tabla(valor) for valor in fila) + " |"
        )

    lineas.extend(
        [
            "",
            "## Servicios y datos externos no incluidos",
            "",
            "RainViewer no es una biblioteca incorporada al ejecutable. Sus",
            "teselas se consultan opcionalmente en tiempo de ejecución y están",
            "sujetas a condiciones propias. La atribución visible es obligatoria",
            "y la API pública se describe para uso personal, educativo y",
            "comunitario a pequeña escala, sin SLA. Condiciones verificadas el",
            f"{fecha_revision}: https://www.rainviewer.com/api.html",
            "",
            "Las atribuciones de SIGPAC, PNOA/IGN, OpenStreetMap y RainViewer se",
            "detallan en `ATRIBUCIONES_DATOS.md`.",
            "",
        ]
    )
    return "\n".join(lineas)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--fecha-revision", required=True)
    parser.add_argument(
        "--salida",
        type=Path,
        default=ROOT / "THIRD_PARTY_NOTICES.md",
    )
    args = parser.parse_args()
    contenido = generar(args.version, args.fecha_revision)
    args.salida.write_text(contenido, encoding="utf-8", newline="\n")
    print(f"Avisos generados: {args.salida}")


if __name__ == "__main__":
    main()
