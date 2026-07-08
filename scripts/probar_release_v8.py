#!/usr/bin/env python3
from pathlib import Path
import importlib
import os
import subprocess
import sys
import time


APP_ROOT = Path(__file__).resolve().parents[1]
DB_RELEASE_V8 = APP_ROOT / "runtime" / "v8" / "prueba_release_v8.db"
VERSION_ESPERADA = "8.4.5"


PRUEBAS = [
    (
        "Crear base limpia v8",
        ["scripts/crear_base_v7.py", str(DB_RELEASE_V8.relative_to(APP_ROOT))],
    ),
    (
        "Diagnostico base limpia v8",
        [
            "scripts/diagnostico_schema_v7.py",
            str(DB_RELEASE_V8.relative_to(APP_ROOT)),
        ],
    ),
    ("Importacion catalogos SIEX", ["scripts/probar_importacion_catalogos_siex_v8.py"]),
    ("Esquema v7.13/idempotencia", ["scripts/probar_schema_v7_13.py"]),
    ("Cultivos arboles", ["scripts/probar_cultivos_arboles_v7.py"]),
    ("Cosecha multicultivo", ["scripts/probar_cosecha_multicultivo_v7.py"]),
    (
        "Actuaciones multicultivo v8.0.1",
        ["scripts/probar_actuaciones_multicultivo_v8.py"],
    ),
    (
        "Contabilidad campana por fecha v8.0.3",
        ["scripts/probar_contabilidad_campana_por_fecha_v8.py"],
    ),
    (
        "PDF portada y backup documental v8.3.3",
        ["scripts/probar_pdf_portada_y_backup_docs_v8.py"],
    ),
    (
        "PDF parcelas unicas v8.4.4",
        ["scripts/probar_pdf_parcelas_unicas_v8.py"],
    ),
    (
        "Campanas activacion v8.4.5",
        ["scripts/probar_campanas_activacion_v8.py"],
    ),
    ("Persistencia editores", ["scripts/probar_persistencia_editores_v7.py"]),
    ("Pre-v8 completo", ["scripts/probar_pre_v8_v7_14.py"]),
    ("Listados", ["scripts/probar_listados_v7.py"]),
    ("Auditoria visual", ["scripts/auditar_tablas_visuales_v7.py"]),
    ("Render modulos", ["scripts/probar_render_modulos_v7.py"]),
    ("Editores auxiliares", ["scripts/probar_editores_auxiliares_v7.py"]),
    ("Flujo integral", ["scripts/probar_flujo_integral_v7.py"]),
]


def _resultado(nombre, codigo, duracion, salida=""):

    return {
        "nombre": nombre,
        "comando": "validacion interna",
        "codigo": codigo,
        "duracion": duracion,
        "salida": salida,
    }


def _validar_version_visible():

    inicio = time.monotonic()
    nombre = "Version visible"

    if str(APP_ROOT) not in sys.path:

        sys.path.insert(0, str(APP_ROOT))

    try:

        version = importlib.import_module("core.version")
        app_name = getattr(version, "APP_NAME", "")
        app_version = getattr(version, "APP_VERSION", "")
        texto_version = version.version_text()

        errores = []

        if app_name != "CuadernoPro":

            errores.append(f"APP_NAME inesperado: {app_name!r}")

        if not app_version:

            errores.append("APP_VERSION vacio")

        if app_version != VERSION_ESPERADA:

            errores.append(
                f"APP_VERSION={app_version!r}; esperado {VERSION_ESPERADA!r}"
            )

        if "8.0.0" == app_version:

            errores.append("APP_VERSION conserva 8.0.0")

        if app_version not in texto_version:

            errores.append(
                f"version_text() no contiene APP_VERSION: {texto_version!r}"
            )

        if errores:

            return _resultado(
                nombre,
                1,
                time.monotonic() - inicio,
                "\n".join(errores),
            )

        salida = (
            f"APP_NAME={app_name}; APP_VERSION={app_version}; "
            f"version_text={texto_version}"
        )
        return _resultado(nombre, 0, time.monotonic() - inicio, salida)

    except Exception as exc:

        return _resultado(nombre, 1, time.monotonic() - inicio, repr(exc))


def _ejecutar(nombre, args):

    inicio = time.monotonic()
    comando = [sys.executable, *args]
    entorno = os.environ.copy()
    entorno.setdefault("PYTHONUNBUFFERED", "1")
    resultado = subprocess.run(
        comando,
        cwd=APP_ROOT,
        env=entorno,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    duracion = time.monotonic() - inicio
    return {
        "nombre": nombre,
        "comando": " ".join(args),
        "codigo": resultado.returncode,
        "duracion": duracion,
        "salida": resultado.stdout,
    }


def _imprimir_resumen(resultados):

    print("Prueba release v8")
    print("=================")
    print(f"Base limpia v8: {DB_RELEASE_V8}")
    print("")
    print("| Prueba | Resultado | Segundos |")
    print("| --- | --- | ---: |")

    for resultado in resultados:

        estado = "OK" if resultado["codigo"] == 0 else "FALLO"
        print(
            f"| {resultado['nombre']} | {estado} | "
            f"{resultado['duracion']:.1f} |"
        )


def _imprimir_fallos(resultados):

    fallos = [
        resultado
        for resultado in resultados
        if resultado["codigo"] != 0
    ]

    if not fallos:

        return

    print("")
    print("Errores")

    for fallo in fallos:

        print("")
        print(f"## {fallo['nombre']}")
        print(f"Comando: {fallo['comando']}")
        print(f"Codigo: {fallo['codigo']}")
        print(fallo["salida"].rstrip())


def main():

    DB_RELEASE_V8.parent.mkdir(parents=True, exist_ok=True)
    resultados = []

    print("Ejecutando: Version visible")
    resultado_version = _validar_version_visible()
    resultados.append(resultado_version)
    estado_version = "OK" if resultado_version["codigo"] == 0 else "FALLO"
    print(f"- {estado_version} ({resultado_version['duracion']:.1f}s)")

    if resultado_version["codigo"] != 0:

        print("")
        _imprimir_resumen(resultados)
        _imprimir_fallos(resultados)
        print("")
        print("Conclusion: release v8 no validada")
        return 1

    for nombre, args in PRUEBAS:

        print(f"Ejecutando: {nombre}")
        resultado = _ejecutar(nombre, args)
        resultados.append(resultado)
        estado = "OK" if resultado["codigo"] == 0 else "FALLO"
        print(f"- {estado} ({resultado['duracion']:.1f}s)")

        if resultado["codigo"] != 0:

            break

    print("")
    _imprimir_resumen(resultados)
    _imprimir_fallos(resultados)

    if any(resultado["codigo"] != 0 for resultado in resultados):

        print("")
        print("Conclusion: release v8 no validada")
        return 1

    if len(resultados) != len(PRUEBAS) + 1:

        print("")
        print("Conclusion: release v8 no validada")
        return 1

    print("")
    print("Conclusion: release v8 validada")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
