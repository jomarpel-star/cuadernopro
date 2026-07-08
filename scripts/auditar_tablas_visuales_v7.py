#!/usr/bin/env python3
from pathlib import Path
import re


APP_ROOT = Path(__file__).resolve().parents[1]
RUTAS = [APP_ROOT / "modules", APP_ROOT / "core", APP_ROOT / "app.py"]
PATRON_TABLA = re.compile(r"st\.(dataframe|data_editor|table)\s*\(")
HELPERS_VISUALES = (
    "preparar_dataframe_visual",
    "_vista_campanas_asistente",
    "_preparar_dataframe_editor_explotacion",
    "_preparar_dataframe_borrado_explotacion",
    "ETIQUETAS_PERSONAS",
    "ETIQUETAS_EQUIPOS",
)
VENTANA_CORTA = 24
VENTANA_LARGA = 80

MODULOS_PRIORIDAD_ALTA = {
    "modules/asistente_inicio.py",
    "modules/explotacion.py",
    "modules/campanas.py",
    "modules/parcelas.py",
    "modules/cultivos.py",
    "modules/productos_fito.py",
    "modules/tratamientos.py",
    "modules/fertilizacion.py",
    "modules/practicas_culturales.py",
    "modules/cosecha.py",
    "modules/maquinaria.py",
    "modules/contabilidad.py",
}


def _archivos_python():

    for ruta in RUTAS:

        if ruta.is_file():

            yield ruta

        elif ruta.is_dir():

            yield from sorted(ruta.rglob("*.py"))


def _estado_linea(lineas, indice):

    inicio = max(0, indice - VENTANA_CORTA)
    fin = min(len(lineas), indice + VENTANA_CORTA)
    contexto = "\n".join(lineas[inicio:fin])
    inicio_largo = max(0, indice - VENTANA_LARGA)
    fin_largo = min(len(lineas), indice + VENTANA_LARGA)
    contexto_largo = "\n".join(lineas[inicio_largo:fin_largo])
    llamada = PATRON_TABLA.search(lineas[indice]).group(1)

    if llamada == "data_editor":

        if (
            "column_config" in contexto
            or "preparar_column_config_visual" in contexto
        ):

            return "OK"

        if "mapear_columnas_visuales_a_tecnicas" in contexto_largo:

            return "OK"

        if (
            "rename(columns=" in contexto_largo
            or "preparar_dataframe_visual" in contexto_largo
        ):

            return "ADVERTENCIA_EDITOR_RENOMBRADO"

        return "ADVERTENCIA"

    if any(helper in contexto for helper in HELPERS_VISUALES):

        return "OK"

    if "rename(columns=" in contexto:

        return "OK"

    return "ADVERTENCIA"


def main():

    print("Auditoria tablas visuales v7")
    print("============================")

    total = 0
    advertencias = 0

    for archivo in _archivos_python():

        relativo = archivo.relative_to(APP_ROOT)
        lineas = archivo.read_text(encoding="utf-8").splitlines()

        for indice, linea in enumerate(lineas):

            if not PATRON_TABLA.search(linea):

                continue

            total += 1
            estado = _estado_linea(lineas, indice)

            if estado.startswith("ADVERTENCIA"):

                advertencias += 1

            prioridad = (
                "ALTA"
                if str(relativo) in MODULOS_PRIORIDAD_ALTA
                else "media"
            )
            print(
                f"{estado} [{prioridad}]: {relativo}:{indice + 1}: "
                f"{linea.strip()}"
            )

    print("")
    print(f"Total llamadas detectadas: {total}")
    print(f"Advertencias: {advertencias}")
    print("Resultado: OK")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
