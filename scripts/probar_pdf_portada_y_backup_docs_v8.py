#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import sqlite3
import sys
import zipfile


APP_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = APP_ROOT / "runtime" / "v8"
DB_PRUEBA = RUNTIME_DIR / "prueba_pdf_backup_docs_v8.db"
DOCS_PRUEBA = RUNTIME_DIR / "documentos_pdf_backup_docs_v8"
EXPORTS_PRUEBA = RUNTIME_DIR / "exports_pdf_backup_docs_v8"
BACKUPS_PRUEBA = RUNTIME_DIR / "backups_pdf_backup_docs_v8"
DB_RESTAURADA = RUNTIME_DIR / "prueba_pdf_backup_docs_v8_restaurada.db"
DOCS_RESTAURADOS = RUNTIME_DIR / "documentos_pdf_backup_docs_v8_restaurados"

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_PRUEBA)
os.environ["CUADERNOPRO_DOCUMENTOS_DIR"] = str(DOCS_PRUEBA)
os.environ["CUADERNOPRO_BACKUPS_DIR"] = str(BACKUPS_PRUEBA)
os.environ["CUADERNOPRO_EXPORTS_DIR"] = str(EXPORTS_PRUEBA)

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

from core.db import crear_tablas  # noqa: E402
import modules.backup_page as backup_page  # noqa: E402
import services.cuadernopro_pdf as cuadernopro_pdf  # noqa: E402


def _limpiar_ruta(ruta):

    ruta = Path(ruta)

    if ruta.is_dir():

        shutil.rmtree(ruta)

    elif ruta.exists():

        ruta.unlink()


def _preparar_entorno():

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    for ruta in (
        DB_PRUEBA,
        DB_PRUEBA.with_name(f"{DB_PRUEBA.name}-wal"),
        DB_PRUEBA.with_name(f"{DB_PRUEBA.name}-shm"),
        DB_RESTAURADA,
        DB_RESTAURADA.with_name(f"{DB_RESTAURADA.name}-wal"),
        DB_RESTAURADA.with_name(f"{DB_RESTAURADA.name}-shm"),
        DOCS_PRUEBA,
        DOCS_RESTAURADOS,
        EXPORTS_PRUEBA,
        BACKUPS_PRUEBA,
    ):

        _limpiar_ruta(ruta)

    DOCS_PRUEBA.mkdir(parents=True, exist_ok=True)
    EXPORTS_PRUEBA.mkdir(parents=True, exist_ok=True)
    BACKUPS_PRUEBA.mkdir(parents=True, exist_ok=True)
    crear_tablas(DB_PRUEBA)


def _insertar_datos_minimos():

    ahora = "2026-07-07T00:00:00"

    with sqlite3.connect(DB_PRUEBA) as conn:

        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            """
            INSERT INTO explotacion
            (nombre_explotacion, titular, nif, direccion, municipio,
             provincia, codigo_postal, telefono, email,
             identificador_oficial, tipo_identificador_oficial,
             registro_autonomico, tipo_explotacion, orientacion_productiva,
             fecha_alta, agricultor_activo, joven_agricultor, responsable,
             asesor, numero_asesor, observaciones, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "Explotacion prueba PDF backup",
                "Titular prueba PDF backup",
                "00000000T",
                "Camino de Prueba 1",
                "Jumilla",
                "Murcia",
                "30520",
                "600000000",
                "prueba@example.com",
                "REGEPA-PRUEBA-001",
                "REGEPA",
                "REG-AUT-PRUEBA-001",
                "Agraria",
                "Prueba",
                "2025-01-01",
                1,
                0,
                "Responsable prueba",
                "Asesor prueba",
                "ASE-PRUEBA",
                "Datos minimos de prueba",
                ahora,
                ahora,
            ),
        )
        campana_id = conn.execute(
            """
            INSERT INTO campanas
            (nombre, fecha_inicio, fecha_fin, activa, estado,
             observaciones, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                "2025/2026",
                "2025-10-01",
                "2026-09-30",
                1,
                "abierta",
                "Campana de prueba PDF backup",
                ahora,
                ahora,
            ),
        ).lastrowid
        conn.commit()

    return campana_id


def _texto_pdf(ruta_pdf):

    try:

        from pypdf import PdfReader

        lector = PdfReader(str(ruta_pdf))
        return "\n".join(
            pagina.extract_text() or ""
            for pagina in lector.pages
        )

    except Exception:

        return ""


def _validar_pdf(campana_id):

    ruta_pdf = Path(cuadernopro_pdf.generar_cuadernopro_pdf(campana_id))

    if not ruta_pdf.exists():

        raise AssertionError(f"No se genero el PDF: {ruta_pdf}")

    if ruta_pdf.stat().st_size <= 0:

        raise AssertionError(f"PDF sin contenido: {ruta_pdf}")

    campana = cuadernopro_pdf._campana(campana_id)
    explotacion = cuadernopro_pdf._datos_explotacion()
    datos_esperados = {
        "fecha_apertura": cuadernopro_pdf._fecha_apertura_portada(campana),
        "registro_nacional": (
            cuadernopro_pdf._registro_nacional_explotacion(explotacion)
        ),
        "registro_autonomico": (
            cuadernopro_pdf._registro_autonomico_explotacion(explotacion)
        ),
    }

    esperado = {
        "fecha_apertura": "01/10/2025",
        "registro_nacional": "REGEPA-PRUEBA-001",
        "registro_autonomico": "REG-AUT-PRUEBA-001",
    }

    if datos_esperados != esperado:

        raise AssertionError(
            f"Datos de portada inesperados: {datos_esperados!r}"
        )

    texto = _texto_pdf(ruta_pdf)

    if texto.strip():

        for valor in esperado.values():

            if valor not in texto:

                raise AssertionError(
                    f"El texto extraido del PDF no contiene {valor!r}"
                )

        comprobacion_texto = "texto PDF validado"

    else:

        comprobacion_texto = "texto PDF no extraible; helpers validados"

    return ruta_pdf, comprobacion_texto


def _pdf_ficticio(titulo):

    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 200 200] /Contents 4 0 R >> endobj\n"
        b"4 0 obj << /Length 0 >> stream\nendstream endobj\n"
        b"trailer << /Root 1 0 R >>\n%%EOF\n"
        + f"% {titulo}\n".encode("utf-8")
    )


def _crear_documentos_ficticios():

    factura = DOCS_PRUEBA / "facturas" / "factura_prueba.pdf"
    receta = DOCS_PRUEBA / "recetas" / "receta_prueba.pdf"
    factura.parent.mkdir(parents=True, exist_ok=True)
    receta.parent.mkdir(parents=True, exist_ok=True)
    factura.write_bytes(_pdf_ficticio("factura prueba"))
    receta.write_bytes(_pdf_ficticio("receta prueba"))
    return factura, receta


def _validar_backup():

    ruta_zip = BACKUPS_PRUEBA / "backup_pdf_docs_v8.zip"
    resultado = backup_page._crear_backup_zip(
        ruta_zip,
        ruta_db=DB_PRUEBA,
        documentos_dir=DOCS_PRUEBA,
    )

    if resultado["documentos_count"] != 2:

        raise AssertionError(
            "El backup no contabilizo los dos documentos ficticios"
        )

    with zipfile.ZipFile(ruta_zip) as z:

        nombres = set(z.namelist())

    esperados = {
        DB_PRUEBA.name,
        "documentos/facturas/factura_prueba.pdf",
        "documentos/recetas/receta_prueba.pdf",
    }
    faltantes = esperados - nombres

    if faltantes:

        raise AssertionError(f"Faltan entradas en el ZIP: {sorted(faltantes)}")

    for nombre in nombres:

        partes = nombre.split("/")

        if nombre.startswith("/") or "\\" in nombre or ".." in partes:

            raise AssertionError(f"Ruta insegura en ZIP: {nombre!r}")

        if nombre.startswith(("runtime/", "backups/", "exports/")):

            raise AssertionError(f"Entrada no permitida en ZIP: {nombre!r}")

        if "__pycache__" in partes or ".cache" in partes:

            raise AssertionError(f"Cache no permitida en ZIP: {nombre!r}")

        if nombre != ruta_zip.name and nombre.endswith(".zip"):

            raise AssertionError(f"ZIP anidado no permitido: {nombre!r}")

    return ruta_zip, nombres


def _validar_restauracion(ruta_zip):

    DB_RESTAURADA.parent.mkdir(parents=True, exist_ok=True)
    DOCS_RESTAURADOS.mkdir(parents=True, exist_ok=True)
    original_obtener_ruta_db = backup_page.obtener_ruta_db
    original_docs_dir = backup_page.DOCS_DIR
    backup_page.obtener_ruta_db = lambda: str(DB_RESTAURADA)
    backup_page.DOCS_DIR = DOCS_RESTAURADOS

    archivo_restauracion = None

    try:

        with open(ruta_zip, "rb") as archivo:

            archivo_restauracion = (
                backup_page._preparar_archivo_restauracion(archivo)
            )
            resultado = backup_page._restaurar_base_datos(
                archivo_restauracion.ruta_temporal,
                archivo_restauracion.documentos_temporal,
            )

    finally:

        backup_page.obtener_ruta_db = original_obtener_ruta_db
        backup_page.DOCS_DIR = original_docs_dir

        if archivo_restauracion is not None:

            backup_page._eliminar_archivo_restauracion(archivo_restauracion)

    if resultado["documentos_restaurados"] != 2:

        raise AssertionError(
            "La restauracion no informo de dos documentos restaurados"
        )

    if not DB_RESTAURADA.exists() or DB_RESTAURADA.stat().st_size <= 0:

        raise AssertionError("La base restaurada no existe o esta vacia")

    for relativa in (
        Path("facturas") / "factura_prueba.pdf",
        Path("recetas") / "receta_prueba.pdf",
    ):

        ruta = DOCS_RESTAURADOS / relativa

        if not ruta.exists() or ruta.stat().st_size <= 0:

            raise AssertionError(f"Documento no restaurado: {ruta}")

    with sqlite3.connect(DB_RESTAURADA) as conn:

        fila = conn.execute(
            """
            SELECT identificador_oficial, registro_autonomico
            FROM explotacion
            ORDER BY id
            LIMIT 1
            """
        ).fetchone()

    if tuple(fila) != ("REGEPA-PRUEBA-001", "REG-AUT-PRUEBA-001"):

        raise AssertionError("La base restaurada no contiene la explotacion")

    return resultado


def main():

    _preparar_entorno()
    campana_id = _insertar_datos_minimos()
    ruta_pdf, comprobacion_texto = _validar_pdf(campana_id)
    _crear_documentos_ficticios()
    ruta_zip, nombres_zip = _validar_backup()
    resultado_restauracion = _validar_restauracion(ruta_zip)

    print("Prueba PDF portada y backup documental v8")
    print("=========================================")
    print(f"PDF: OK ({ruta_pdf}, {ruta_pdf.stat().st_size} bytes)")
    print(f"Portada: OK ({comprobacion_texto})")
    print(f"Backup: OK ({ruta_zip}, {len(nombres_zip)} entradas)")
    print(
        "Restauracion documental: OK "
        f"({resultado_restauracion['documentos_restaurados']} documentos)"
    )
    print("Conclusion: PDF portada y backup documental validados")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
