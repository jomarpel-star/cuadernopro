#!/usr/bin/env python3
"""Comprueba el arranque y el rerun de la app con una base temporal vacia."""

import os
from pathlib import Path
import sys
import tempfile


APP_ROOT = Path(__file__).resolve().parents[1]


def main():
    # Configurar las rutas antes de importar Streamlit o cualquier modulo propio.
    with tempfile.TemporaryDirectory(prefix="cuadernopro-arranque-") as directory:
        data = Path(directory)
        os.environ.update(
            CUADERNOPRO_DATA_DIR=str(data),
            CUADERNOPRO_DB_PATH=str(data / "prueba.db"),
            CUADERNOPRO_BACKUPS_DIR=str(data / "backups"),
            CUADERNOPRO_EXPORTS_DIR=str(data / "exports"),
            CUADERNOPRO_DOCUMENTOS_DIR=str(data / "documentos"),
        )
        sys.path.insert(0, str(APP_ROOT))
        from streamlit.testing.v1 import AppTest
        from core.version import version_text

        app = AppTest.from_file(str(APP_ROOT / "app.py"), default_timeout=30)
        for _ in range(2):
            app.run()
            assert not app.exception, [error.message for error in app.exception]
            assert any(version_text() in title.value for title in app.sidebar.title)
        assert (data / "prueba.db").is_file(), "No se ha creado la base temporal"
    print("Arranque y rerun de Streamlit con datos temporales: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
