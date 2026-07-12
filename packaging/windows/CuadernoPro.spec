# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules


block_cipher = None
SPEC_DIR = Path(SPECPATH).resolve()
REPO_ROOT = SPEC_DIR.parents[1]
BRANDING_ICON = REPO_ROOT / "assets" / "branding" / "cuadernopro.ico"
BRANDING_PNG = REPO_ROOT / "assets" / "branding" / "cuadernopro.png"
EXE_ICON = str(BRANDING_ICON) if BRANDING_ICON.exists() else None

if EXE_ICON:
    print(f"Icono Windows: {BRANDING_ICON}")
else:
    print(
        "AVISO: no se encontro assets/branding/cuadernopro.ico; "
        "CuadernoPro.exe se generara con el icono por defecto."
    )

EXE_OPTIONS = {"icon": EXE_ICON} if EXE_ICON else {}

EXCLUDED_NAMES = {
    ".git",
    ".venv-windows",
    "__pycache__",
    "backups",
    "build",
    "dist",
    "dist_windows",
    "exports",
    "runtime",
    "venv",
}
EXCLUDED_SUFFIXES = {
    ".db",
    ".db-shm",
    ".db-wal",
    ".exe",
    ".msi",
    ".msix",
    ".pyc",
    ".sqlite",
    ".sqlite3",
    ".xlsx",
    ".zip",
}


def _incluido(path):
    partes = set(path.parts)

    if partes & EXCLUDED_NAMES:
        return False

    nombre = path.name.lower()

    if nombre.endswith(".spec.bak"):
        return False

    return path.suffix.lower() not in EXCLUDED_SUFFIXES


def _tree(origen, destino):
    raiz = REPO_ROOT / origen
    datos = []

    if not raiz.exists():
        return datos

    for ruta in raiz.rglob("*"):
        if not ruta.is_file() or not _incluido(ruta):
            continue

        relativo = ruta.relative_to(raiz)
        datos.append((str(ruta), str(Path(destino) / relativo.parent)))

    return datos


def _data_file(origen, destino):
    ruta = REPO_ROOT / origen

    if ruta.exists() and ruta.is_file() and _incluido(ruta):
        return [(str(ruta), destino)]

    return []


binaries = []
datas = [
    (str(REPO_ROOT / "app.py"), "."),
]
datas += _tree("core", "core")
datas += _tree("modules", "modules")
datas += _tree("services", "services")
datas += _tree("data", "data")
datas += _tree("docs", "docs")
datas += _data_file(
    BRANDING_PNG,
    str(Path("assets") / "branding"),
)

for nombre in (
    "LICENSE",
    "DISCLAIMER.md",
    "TRADEMARKS.md",
    "README.md",
    "USO_BASICO.md",
    "GUIA_INSTALACION_SENCILLA.md",
    "AVISO_RESPONSABILIDAD.md",
    "THIRD_PARTY_NOTICES.md",
    "ATRIBUCIONES_DATOS.md",
):
    ruta = REPO_ROOT / nombre

    if ruta.exists() and _incluido(ruta):
        datas.append((str(ruta), "."))

hiddenimports = []

for paquete in (
    "core",
    "modules",
    "services",
    "streamlit",
    "pandas",
    "openpyxl",
    "requests",
    "folium",
    "streamlit_folium",
    "docx",
    "xlrd",
    "geopandas",
    "shapely",
    "owslib",
    "reportlab",
    "pypdf",
):
    hiddenimports += collect_submodules(paquete)

for paquete in (
    "streamlit",
    "folium",
    "streamlit_folium",
    "pandas",
    "openpyxl",
    "geopandas",
    "shapely",
    "owslib",
    "reportlab",
    "pypdf",
):
    paquete_datas, paquete_binaries, paquete_hiddenimports = collect_all(
        paquete
    )
    datas += paquete_datas
    binaries += paquete_binaries
    hiddenimports += paquete_hiddenimports


a = Analysis(
    [str(REPO_ROOT / "packaging" / "windows" / "cuadernopro_launcher.py")],
    pathex=[str(REPO_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CuadernoPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    **EXE_OPTIONS,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CuadernoPro",
)
