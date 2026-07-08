from datetime import datetime
import hashlib
from pathlib import Path
import re

import pandas as pd

from core.db import leer
from core.paths import DOCS_DIR, asegurar_directorio


FACTURAS_DIR = DOCS_DIR / "facturas"
MIMES_PDF = {
    "",
    "application/pdf",
    "application/x-pdf",
}


def _texto(valor):

    if valor is None or pd.isna(valor):

        return ""

    return str(valor).strip()


def nombre_archivo_seguro(nombre):

    texto = Path(_texto(nombre) or "factura.pdf").name
    texto = re.sub(r"[^A-Za-z0-9._-]+", "_", texto).strip("._-")

    if not texto:

        texto = "factura.pdf"

    return texto[:120]


def ruta_factura_absoluta(ruta_relativa):

    ruta = (DOCS_DIR / _texto(ruta_relativa)).resolve()
    documentos = DOCS_DIR.resolve()

    if documentos not in ruta.parents and ruta != documentos:

        raise ValueError("La ruta de factura queda fuera de documentos")

    return ruta


def _contenido_archivo(archivo):

    if hasattr(archivo, "getvalue"):

        return archivo.getvalue()

    if hasattr(archivo, "read"):

        posicion = archivo.tell() if hasattr(archivo, "tell") else None
        contenido = archivo.read()

        if posicion is not None and hasattr(archivo, "seek"):

            archivo.seek(posicion)

        return contenido

    return b""


def validar_pdf(nombre_original, mime_type, contenido):

    nombre = _texto(nombre_original)
    mime = _texto(mime_type).lower()

    if Path(nombre).suffix.lower() != ".pdf":

        return False, "Solo se admiten archivos PDF."

    if mime and mime not in MIMES_PDF:

        return False, f"Tipo MIME no admitido: {mime}"

    if not contenido:

        return False, "El PDF está vacío."

    if not contenido.startswith(b"%PDF"):

        return False, "El archivo no tiene cabecera PDF válida."

    return True, ""


def preparar_pdf_subido(archivo):

    nombre_original = nombre_archivo_seguro(
        getattr(archivo, "name", "factura.pdf")
    )
    mime_type = _texto(getattr(archivo, "type", ""))
    contenido = _contenido_archivo(archivo)
    valido, error = validar_pdf(nombre_original, mime_type, contenido)

    return {
        "valido": valido,
        "error": error,
        "nombre_original": nombre_original,
        "mime_type": mime_type,
        "contenido": contenido,
        "size_bytes": len(contenido or b""),
        "sha256": hashlib.sha256(contenido).hexdigest() if contenido else "",
    }


def guardar_facturas_pdf(conn, movimiento_id, archivos):

    archivos = [
        archivo
        for archivo in (archivos or [])
        if archivo is not None
    ]

    if not archivos:

        return {"guardados": [], "errores": []}

    asegurar_directorio(FACTURAS_DIR)
    movimiento_id = int(movimiento_id)
    fila_orden = conn.execute(
        """
        SELECT COALESCE(MAX(orden),0)
        FROM movimientos_economicos_documentos
        WHERE movimiento_id=?
        """,
        (movimiento_id,)
    ).fetchone()
    orden = int(fila_orden[0] or 0)
    guardados = []
    errores = []
    rutas_escritas = []

    try:

        for indice, archivo in enumerate(archivos, start=1):

            preparado = preparar_pdf_subido(archivo)

            if not preparado["valido"]:

                errores.append(
                    f"{preparado['nombre_original']}: {preparado['error']}"
                )
                continue

            orden += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            nombre_guardado = (
                f"movimiento_{movimiento_id}_factura_{timestamp}_{indice}.pdf"
            )
            ruta = FACTURAS_DIR / nombre_guardado

            with ruta.open("wb") as destino:

                destino.write(preparado["contenido"])

            rutas_escritas.append(ruta)
            ruta_relativa = (Path("facturas") / nombre_guardado).as_posix()
            ahora = datetime.now().isoformat()
            conn.execute(
                """
                INSERT INTO movimientos_economicos_documentos
                (movimiento_id,tipo_documento,nombre_original,nombre_guardado,
                ruta_relativa,extension,mime_type,size_bytes,sha256,orden,
                created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    movimiento_id,
                    "factura",
                    preparado["nombre_original"],
                    nombre_guardado,
                    ruta_relativa,
                    "pdf",
                    preparado["mime_type"] or "application/pdf",
                    preparado["size_bytes"],
                    preparado["sha256"],
                    orden,
                    ahora,
                    ahora,
                )
            )
            guardados.append(preparado["nombre_original"])

    except Exception:

        for ruta in rutas_escritas:

            try:

                ruta.unlink(missing_ok=True)

            except OSError:

                pass

        raise

    return {"guardados": guardados, "errores": errores}


def leer_facturas_movimientos():

    return leer(
        """
        SELECT
        movimientos_economicos_documentos.id,
        movimientos_economicos_documentos.movimiento_id,
        movimientos_economicos_documentos.tipo_documento,
        movimientos_economicos_documentos.nombre_original,
        movimientos_economicos_documentos.nombre_guardado,
        movimientos_economicos_documentos.ruta_relativa,
        movimientos_economicos_documentos.extension,
        movimientos_economicos_documentos.mime_type,
        movimientos_economicos_documentos.size_bytes,
        movimientos_economicos_documentos.sha256,
        movimientos_economicos_documentos.orden,
        movimientos_economicos_documentos.created_at,
        movimientos_economicos_documentos.updated_at
        FROM movimientos_economicos_documentos
        ORDER BY movimiento_id,orden,id
        """
    )


def eliminar_archivo_factura(ruta_relativa):

    try:

        ruta = ruta_factura_absoluta(ruta_relativa)

    except ValueError:

        return False

    if not ruta.exists():

        return False

    ruta.unlink()
    return True


def eliminar_documento_factura(conn, documento_id):

    fila = conn.execute(
        """
        SELECT ruta_relativa
        FROM movimientos_economicos_documentos
        WHERE id=?
        """,
        (int(documento_id),)
    ).fetchone()

    if not fila:

        return False

    conn.execute(
        "DELETE FROM movimientos_economicos_documentos WHERE id=?",
        (int(documento_id),)
    )
    return fila[0]
