#!/usr/bin/env python3
"""Audita palabras frecuentes sin tilde en documentación pública.

El script solo informa advertencias. No modifica archivos.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SUGERENCIAS = {
    "instalacion": "instalación",
    "configuracion": "configuración",
    "documentacion": "documentación",
    "explotacion": "explotación",
    "informacion": "información",
    "aplicacion": "aplicación",
    "version": "versión",
    "publicacion": "publicación",
    "restauracion": "restauración",
    "validacion": "validación",
    "introduccion": "introducción",
    "actualizacion": "actualización",
    "agricola": "agrícola",
    "practicas": "prácticas",
    "catalogos": "catálogos",
    "exportacion": "exportación",
    "importacion": "importación",
    "generacion": "generación",
    "ejecucion": "ejecución",
    "opcion": "opción",
    "seccion": "sección",
    "funcion": "función",
    "gestion": "gestión",
    "comunicacion": "comunicación",
    "administracion": "administración",
    "tecnico": "técnico",
    "economico": "económico",
    "analisis": "análisis",
    "ningun": "ningún",
    "fertilizacion": "fertilización",
    "revision": "revisión",
    "activacion": "activación",
    "limites": "límites",
    "automaticamente": "automáticamente",
    "codigo": "código",
    "caracteristicas": "características",
    "calculo": "cálculo",
    "arboles": "árboles",
    "plantacion": "plantación",
    "basica": "básica",
    "basico": "básico",
    "publica": "pública",
    "publico": "público",
    "publicos": "públicos",
    "rapida": "rápida",
    "especificos": "específicos",
    "guia": "guía",
    "diagnostico": "diagnóstico",
    "garantia": "garantía",
    "tramites": "trámites",
    "podran": "podrán",
    "formacion": "formación",
    "tambien": "también",
    "sera": "será",
    "habra": "habrá",
    "todavia": "todavía",
    "anade": "añade",
    "diseno": "diseño",
    "segun": "según",
    "raiz": "raíz",
    "politica": "política",
    "menu": "menú",
    "minimo": "mínimo",
    "maximo": "máximo",
    "telefono": "teléfono",
    "direccion": "dirección",
    "util": "útil",
    "suscripcion": "suscripción",
    "adaptacion": "adaptación",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "autonomico": "autonómico",
    "autonomica": "autonómica",
    "autonomicos": "autonómicos",
    "economicos": "económicos",
    "analitica": "analítica",
    "historica": "histórica",
    "historicos": "históricos",
    "fisico": "físico",
    "logica": "lógica",
    "integracion": "integración",
    "automaticas": "automáticas",
    "ultimos": "últimos",
    "despues": "después",
    "debera": "deberá",
    "deberia": "debería",
    "podria": "podría",
    "linea": "línea",
    "pagina": "página",
    "paginas": "páginas",
    "accion": "acción",
    "modulo": "módulo",
    "modulos": "módulos",
    "indices": "índices",
    "generico": "genérico",
    "clasificacion": "clasificación",
    "denominacion": "denominación",
    "ano": "año",
    "numero": "número",
    "automatica": "automática",
    "migracion": "migración",
    "retencion": "retención",
    "edicion": "edición",
    "visualizacion": "visualización",
    "eliminacion": "eliminación",
    "preparacion": "preparación",
    "distribucion": "distribución",
    "difusion": "difusión",
    "verificacion": "verificación",
    "catalogo": "catálogo",
    "canonico": "canónico",
    "decision": "decisión",
    "relacion": "relación",
    "areas": "áreas",
    "minimos": "mínimos",
    "criticos": "críticos",
    "dinamicas": "dinámicas",
    "geometria": "geometría",
    "vacia": "vacía",
    "vacio": "vacío",
    "nacera": "nacerá",
    "seguiran": "seguirán",
}

RUTAS_POR_DEFECTO = [
    "README.md",
    "RELEASE_NOTES.md",
    "CHECKLIST_RELEASE.md",
    "GUIA_INSTALACION_SENCILLA.md",
    "INSTALAR_DOCKER.md",
    "DISCLAIMER.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "TRADEMARKS.md",
    "docs/web",
    "docs/publicacion",
    "docs/distribucion",
    "docs/legal",
    "docs/v8",
    "docs/siex",
    "docs/v7",
    "packaging/windows/README_WINDOWS_BUILD.md",
]

PATRON = re.compile(
    r"(?<![A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_/\\-])("
    + "|".join(re.escape(palabra) for palabra in sorted(SUGERENCIAS, key=len, reverse=True))
    + r")(?![A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_/\\-])",
    re.IGNORECASE,
)

URL_RE = re.compile(r"https?://\S+|www\.\S+")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
MARKDOWN_TARGET_RE = re.compile(r"\]\([^)]*\)")


def iterar_markdown(rutas: list[str]) -> list[Path]:
    archivos: list[Path] = []
    for ruta_texto in rutas:
        ruta = Path(ruta_texto)
        if ruta.is_file() and ruta.suffix.lower() == ".md":
            archivos.append(ruta)
        elif ruta.is_dir():
            archivos.extend(sorted(ruta.rglob("*.md")))
    return sorted(dict.fromkeys(archivos))


def parece_comando(linea: str) -> bool:
    texto = linea.strip()
    if not texto:
        return False
    prefijos = (
        "./",
        "python ",
        "python3 ",
        "docker ",
        "git ",
        "grep ",
        "find ",
        "cp ",
        "scp ",
        "curl ",
        "wget ",
        "tar ",
        "zip ",
        "unzip ",
    )
    return texto.startswith(prefijos)


def preparar_linea(linea: str) -> str:
    linea = URL_RE.sub(" ", linea)
    linea = INLINE_CODE_RE.sub(" ", linea)
    linea = MARKDOWN_TARGET_RE.sub("] ", linea)
    return linea


def parece_ruta_o_archivo(linea: str, inicio: int, fin: int) -> bool:
    izquierda = inicio
    derecha = fin
    while izquierda > 0 and not linea[izquierda - 1].isspace():
        izquierda -= 1
    while derecha < len(linea) and not linea[derecha].isspace():
        derecha += 1

    token = linea[izquierda:derecha].strip("()[]{}<>,:;")
    if "/" in token or "\\" in token:
        return True
    return bool(re.search(r"\.[A-Za-z0-9]{1,8}$", token))


def auditar_archivo(ruta: Path) -> list[tuple[int, str, str]]:
    advertencias: list[tuple[int, str, str]] = []
    en_bloque_codigo = False

    for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), start=1):
        if linea.lstrip().startswith("```"):
            en_bloque_codigo = not en_bloque_codigo
            continue
        if en_bloque_codigo or parece_comando(linea):
            continue

        limpia = preparar_linea(linea)
        for coincidencia in PATRON.finditer(limpia):
            if parece_ruta_o_archivo(limpia, coincidencia.start(1), coincidencia.end(1)):
                continue
            palabra = coincidencia.group(1)
            sugerencia = SUGERENCIAS[palabra.lower()]
            advertencias.append((numero, palabra, sugerencia))

    return advertencias


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detecta palabras frecuentes sin tilde en documentación pública."
    )
    parser.add_argument(
        "rutas",
        nargs="*",
        default=RUTAS_POR_DEFECTO,
        help="Archivos o carpetas Markdown a revisar.",
    )
    args = parser.parse_args()

    total = 0
    for archivo in iterar_markdown(args.rutas):
        for numero, palabra, sugerencia in auditar_archivo(archivo):
            total += 1
            print(f"{archivo}:{numero}: {palabra} -> {sugerencia}")

    if total:
        print(f"\nAdvertencias: {total}")
        return 1

    print("Sin advertencias de tildes frecuentes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
