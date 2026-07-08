#!/usr/bin/env python3
from dataclasses import dataclass
from pathlib import Path
import re


APP_ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = APP_ROOT / "modules"

MODULOS_OBJETIVO = [
    "modules/asistente_inicio.py",
    "modules/explotacion.py",
    "modules/campanas.py",
    "modules/terceros.py",
    "modules/parcelas.py",
    "modules/cultivos.py",
    "modules/maquinaria.py",
    "modules/productos_fito.py",
    "modules/tratamientos.py",
    "modules/fertilizacion.py",
    "modules/practicas_culturales.py",
    "modules/cosecha.py",
    "modules/contabilidad.py",
]

PRIORIDAD_MODULOS = {
    "parcelas.py": "alta",
    "cultivos.py": "alta",
    "maquinaria.py": "alta",
    "productos_fito.py": "alta",
    "tratamientos.py": "alta",
    "fertilizacion.py": "alta",
    "practicas_culturales.py": "alta",
    "cosecha.py": "alta",
    "contabilidad.py": "alta",
    "terceros.py": "alta",
    "explotacion.py": "alta",
    "campanas.py": "media",
    "asistente_inicio.py": "media",
}

PALABRAS_ACCION = (
    "guardar",
    "crear",
    "actualizar",
    "anadir",
    "añadir",
    "registrar",
    "desactivar",
    "eliminar",
    "borrar",
)

BOTON_RE = re.compile(r"st\.(form_submit_button|button)\(")


@dataclass
class AccionFormulario:
    linea: int
    tipo: str
    etiqueta: str
    tiene_success: bool
    tiene_rerun: bool
    tiene_version: bool
    tiene_clear_on_submit: bool
    tiene_limpieza_state: bool

    @property
    def posible_reseteo(self):
        return (
            self.tiene_clear_on_submit
            or (self.tiene_version and self.tiene_rerun)
            or (self.tiene_limpieza_state and self.tiene_rerun)
        )

    @property
    def advertencias(self):
        avisos = []

        if not self.tiene_success:
            avisos.append("no se ve mensaje de exito cercano")

        if not self.tiene_rerun and not self.tiene_clear_on_submit:
            avisos.append("no se ve refresco/rerun cercano")

        if not self.posible_reseteo:
            avisos.append("no se ve patron de reseteo cercano")

        return avisos


def _normalizar(texto):
    return texto.casefold().replace("á", "a")


def _es_boton_guardado(fragmento):
    texto = _normalizar(fragmento)
    return any(palabra in texto for palabra in PALABRAS_ACCION)


def _extraer_etiqueta(fragmento):
    coincidencias = re.findall(r"[\"']([^\"']+)[\"']", fragmento)

    if not coincidencias:
        return "(sin etiqueta literal)"

    for etiqueta in coincidencias:
        if _es_boton_guardado(etiqueta):
            return etiqueta

    return coincidencias[0]


def _ventana(lineas, indice, antes=20, despues=460):
    inicio = max(0, indice - antes)
    fin = min(len(lineas), indice + despues)
    return "\n".join(lineas[inicio:fin])


def analizar_archivo(ruta):
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    acciones = []

    for indice, linea in enumerate(lineas):
        if not BOTON_RE.search(linea):
            continue

        fragmento = "\n".join(lineas[indice:indice + 8])

        if not _es_boton_guardado(fragmento):
            continue

        contexto = _ventana(lineas, indice)
        tipo = "st.form_submit_button" if "form_submit_button" in linea else "st.button"
        acciones.append(
            AccionFormulario(
                linea=indice + 1,
                tipo=tipo,
                etiqueta=_extraer_etiqueta(fragmento),
                tiene_success=(
                    "st.success" in contexto
                    or "mensaje_" in contexto
                    or "mensajes_" in contexto
                ),
                tiene_rerun="st.rerun" in contexto,
                tiene_version="_version" in contexto,
                tiene_clear_on_submit="clear_on_submit" in contexto,
                tiene_limpieza_state="st.session_state.pop" in contexto,
            )
        )

    texto_completo = "\n".join(lineas)
    return {
        "ruta": ruta,
        "prioridad": PRIORIDAD_MODULOS.get(ruta.name, "baja"),
        "formularios": texto_completo.count("st.form("),
        "acciones": acciones,
        "success": texto_completo.count("st.success"),
        "rerun": texto_completo.count("st.rerun"),
        "versiones": texto_completo.count("_version"),
        "clear_on_submit": texto_completo.count("clear_on_submit"),
    }


def _imprimir_resumen(resumen):
    ruta = resumen["ruta"]
    print(f"\n== {ruta.relative_to(APP_ROOT)} ==")
    print(f"Prioridad: {resumen['prioridad']}")
    print(f"Formularios st.form detectados: {resumen['formularios']}")
    print(
        "Patrones globales: "
        f"success={resumen['success']} "
        f"rerun={resumen['rerun']} "
        f"_version={resumen['versiones']} "
        f"clear_on_submit={resumen['clear_on_submit']}"
    )

    if not resumen["acciones"]:
        print("Acciones de guardado detectadas: 0")
        return

    print(f"Acciones de guardado detectadas: {len(resumen['acciones'])}")

    for accion in resumen["acciones"]:
        estado = "OK" if accion.posible_reseteo else "REVISAR"
        print(
            f"  L{accion.linea}: {estado} {accion.tipo} "
            f"{accion.etiqueta!r} "
            f"success={accion.tiene_success} "
            f"rerun={accion.tiene_rerun} "
            f"version={accion.tiene_version} "
            f"clear_on_submit={accion.tiene_clear_on_submit} "
            f"limpieza_state={accion.tiene_limpieza_state}"
        )

        for aviso in accion.advertencias:
            print(f"    - aviso: {aviso}")


def main():
    print("Auditoria v7.15 - reseteo de formularios tras guardar")
    print("No se abren bases de datos; solo se inspecciona codigo en modules/.")

    for relativo in MODULOS_OBJETIVO:
        ruta = APP_ROOT / relativo

        if not ruta.exists():
            print(f"\n== {relativo} ==")
            print("ADVERTENCIA: modulo no encontrado")
            continue

        _imprimir_resumen(analizar_archivo(ruta))


if __name__ == "__main__":
    main()
