"""Identidad del ejecutable Windows, derivada de la version de la aplicacion."""

import ast
from pathlib import Path
import re


def app_version(repo_root):
    tree = ast.parse((Path(repo_root) / "core" / "version.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "APP_VERSION"
            for target in node.targets
        ):
            version = ast.literal_eval(node.value)
            if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
                raise ValueError("APP_VERSION debe tener formato X.Y.Z")
            if any(int(part) > 65535 for part in version.split(".")):
                raise ValueError("La version excede el limite de los recursos Windows")
            return version
    raise ValueError("No se encontro APP_VERSION")


def windows_version_info(repo_root):
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo, StringFileInfo, StringStruct, StringTable,
        VarFileInfo, VarStruct, VSVersionInfo,
    )

    version = app_version(repo_root)
    numeric = tuple(int(part) for part in version.split(".")) + (0,)
    fields = {
        "CompanyName": "CuadernoPro",
        "FileDescription": "CuadernoPro - Cuaderno agricola",
        "FileVersion": version,
        "InternalName": "CuadernoPro",
        "LegalCopyright": "CuadernoPro contributors. GPL-3.0.",
        "OriginalFilename": "CuadernoPro.exe",
        "ProductName": "CuadernoPro",
        "ProductVersion": version,
    }
    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=numeric, prodvers=numeric, mask=0x3F,
                          flags=0, OS=0x40004, fileType=1, subtype=0, date=(0, 0)),
        kids=[
            StringFileInfo([StringTable("040904B0", [
                StringStruct(key, value) for key, value in fields.items()
            ])]),
            VarFileInfo([VarStruct("Translation", [1033, 1200])]),
        ],
    )
