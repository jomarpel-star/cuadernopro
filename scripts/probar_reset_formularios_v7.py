#!/usr/bin/env python3
from pathlib import Path
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = APP_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from auditar_reset_formularios_v7 import (  # noqa: E402
    MODULOS_OBJETIVO,
    analizar_archivo,
)


MODULOS_CON_RESETEO_CRITICO = {
    "modules/asistente_inicio.py",
    "modules/campanas.py",
    "modules/explotacion.py",
    "modules/maquinaria.py",
    "modules/parcelas.py",
    "modules/productos_fito.py",
    "modules/terceros.py",
}


def _acciones_con_reseteo(resumen):
    return [
        accion
        for accion in resumen["acciones"]
        if accion.posible_reseteo
    ]


def main():
    errores = []

    for relativo in MODULOS_OBJETIVO:
        ruta = APP_ROOT / relativo

        if not ruta.exists():
            errores.append(f"No existe {relativo}")
            continue

        resumen = analizar_archivo(ruta)

        if relativo in MODULOS_CON_RESETEO_CRITICO:
            acciones_ok = _acciones_con_reseteo(resumen)

            if not acciones_ok:
                errores.append(
                    f"{relativo}: no se detecta ningun guardado con reseteo"
                )

    borrado = (APP_ROOT / "core" / "borrado.py").read_text(encoding="utf-8")

    for fragmento in (
        "eliminar_ids_",
        "eliminar_confirmar_",
        "eliminar_texto_",
        "st.session_state.pop(clave_widget, None)",
    ):
        if fragmento not in borrado:
            errores.append(
                "core/borrado.py no limpia correctamente "
                f"la clave {fragmento!r}"
            )

    if errores:
        print("Prueba de reset de formularios v7: ERROR")

        for error in errores:
            print(f"- {error}")

        return 1

    print("Prueba de reset de formularios v7: OK")
    print(
        "Modulos criticos con patron de reseteo: "
        + ", ".join(sorted(MODULOS_CON_RESETEO_CRITICO))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
