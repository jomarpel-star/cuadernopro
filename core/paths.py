import os
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]


def _resolver_directorio(nombre_variable, valor_por_defecto):
    ruta = Path(os.getenv(nombre_variable, valor_por_defecto)).expanduser()

    if not ruta.is_absolute():
        ruta = APP_ROOT / ruta

    return ruta.resolve()


DATA_DIR = _resolver_directorio("CUADERNOPRO_DATA_DIR", str(APP_ROOT))


def _resolver_ruta_datos(nombre_variable, valor_por_defecto):
    ruta = Path(os.getenv(nombre_variable, valor_por_defecto)).expanduser()

    if not ruta.is_absolute():
        ruta = DATA_DIR / ruta

    return ruta.resolve()


def _resolver_ruta_documentos():
    valor = os.getenv("CUADERNOPRO_DOCUMENTOS_DIR")

    if valor is None:
        valor = os.getenv("CUADERNOPRO_DOCS_DIR", "documentos")

    ruta = Path(valor).expanduser()

    if not ruta.is_absolute():
        ruta = DATA_DIR / ruta

    return ruta.resolve()


DB_PATH = _resolver_ruta_datos("CUADERNOPRO_DB_PATH", "cuadernopro.db")
DOCS_DIR = _resolver_ruta_documentos()
BACKUPS_DIR = _resolver_ruta_datos("CUADERNOPRO_BACKUPS_DIR", "backups")
EXPORTS_DIR = _resolver_ruta_datos("CUADERNOPRO_EXPORTS_DIR", "exports")


def asegurar_directorio(ruta):
    ruta = Path(ruta)
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def asegurar_directorio_padre(ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


asegurar_directorio(DATA_DIR)
asegurar_directorio(BACKUPS_DIR)
asegurar_directorio(EXPORTS_DIR)
asegurar_directorio(DOCS_DIR)
