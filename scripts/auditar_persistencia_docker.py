#!/usr/bin/env python3
"""Impide publicar una imagen Docker sin persistencia para los datos reales."""

from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]

RUTAS_PERSISTENTES = (
    "CUADERNOPRO_DATA_DIR=/app/runtime",
    "CUADERNOPRO_DB_PATH=/app/runtime/cuadernopro.db",
    "CUADERNOPRO_BACKUPS_DIR=/app/runtime/backups",
    "CUADERNOPRO_EXPORTS_DIR=/app/runtime/exports",
    "CUADERNOPRO_DOCUMENTOS_DIR=/app/runtime/documentos",
)


def _leer(nombre):
    return (APP_ROOT / nombre).read_text(encoding="utf-8")


def _exigir(condicion, mensaje, errores):
    if not condicion:
        errores.append(mensaje)


def main():
    errores = []
    dockerfile = _leer("Dockerfile")
    compose = _leer("docker-compose.yml")
    compose_portainer = _leer("docker-compose.portainer.yml")

    for ruta in RUTAS_PERSISTENTES:
        _exigir(
            ruta in dockerfile,
            f"Dockerfile no fija {ruta}",
            errores,
        )
        _exigir(
            ruta in compose_portainer,
            f"Compose de Portainer no fija {ruta}",
            errores,
        )

    _exigir(
        'VOLUME ["/app/runtime"]' in dockerfile,
        "Dockerfile no declara /app/runtime como volumen",
        errores,
    )
    _exigir(
        "./runtime:/app/runtime" in compose,
        "Compose tradicional no conserva el bind mount de runtime",
        errores,
    )
    _exigir(
        "cuadernopro_data:/app/runtime" in compose_portainer,
        "Compose de Portainer no monta el volumen de datos",
        errores,
    )
    _exigir(
        "name: ${CUADERNOPRO_DATA_VOLUME:-cuadernopro_data}"
        in compose_portainer,
        "El volumen de Portainer no tiene un nombre estable",
        errores,
    )

    if errores:
        print("Persistencia Docker: FALLO")
        for error in errores:
            print(f"- {error}")
        return 1

    print("Persistencia Docker: OK")
    print("- Imagen: todos los datos se dirigen a /app/runtime")
    print("- Imagen: /app/runtime esta declarado como volumen")
    print("- Compose tradicional: conserva ./runtime")
    print("- Portainer: usa el volumen nombrado cuadernopro_data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
