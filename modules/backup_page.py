from dataclasses import dataclass
from datetime import datetime
import errno
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zipfile

import streamlit as st

from core.db import obtener_ruta_db, resetear_base_datos_creando_backup
from core.paths import BACKUPS_DIR, DOCS_DIR, EXPORTS_DIR, asegurar_directorio


EXTENSIONES_DB = {".db", ".sqlite", ".sqlite3"}
EXTENSIONES_PERMITIDAS = EXTENSIONES_DB | {".zip"}
BACKUP_DOCUMENTOS_DIRNAME = "documentos"
DIRECTORIOS_EXCLUIDOS_BACKUP = {
    "__pycache__",
    ".cache",
    "cache",
    "caches",
    "tmp",
    "temp",
    "temporales",
}
SUFIJOS_TEMPORALES_BACKUP = (
    "~",
    ".tmp",
    ".temp",
    ".part",
    ".crdownload",
    ".swp",
)

TABLAS_MINIMAS_CUADERNOPRO = {
    "campanas",
    "explotacion",
    "parcelas",
    "cultivos",
}

TABLAS_RECONOCIBLES_CUADERNOPRO = TABLAS_MINIMAS_CUADERNOPRO | {
    "productos_fito",
    "equipos_aplicacion",
    "personas",
    "tratamientos",
    "tratamiento_parcelas",
    "fertilizaciones",
    "fertilizacion_parcelas",
    "practicas_culturales",
    "practica_parcelas",
    "maquinaria",
    "mantenimientos",
    "gastos",
    "cosecha",
    "cosecha_parcelas",
    "movimientos_economicos",
    "diario",
}


@dataclass
class ArchivoRestauracion:
    ruta_temporal: str
    nombre: str
    tamano: int
    documentos_temporal: str = ""
    documentos_count: int = 0


def render():

    st.title("💾 Backup / Restauración")
    _mostrar_mensaje_restauracion()
    _mostrar_mensaje_reset()

    pestana_copias, pestana_restaurar, pestana_reset = st.tabs(
        [
            "📦 Copias de seguridad",
            "♻️ Restaurar copia",
            "🧨 Resetear base de datos",
        ]
    )

    with pestana_copias:

        _render_copias_seguridad()

    with pestana_restaurar:

        _render_restauracion()

    with pestana_reset:

        _render_reset_base_datos()


def _mostrar_mensaje_restauracion():

    resultado = st.session_state.pop("restauracion_db_resultado", None)

    if not resultado:

        return

    st.success("Base de datos restaurada correctamente.")

    ruta_backup = resultado.get("ruta_backup")

    if ruta_backup:

        st.info(f"Copia automática previa creada: {ruta_backup}")

    else:

        st.warning(
            "La base de datos actual no existía; se restauró sin backup "
            "previo."
        )

    avisos = resultado.get("avisos") or []

    for aviso in avisos:

        st.warning(aviso)

    documentos_restaurados = resultado.get("documentos_restaurados", 0)

    if documentos_restaurados:

        st.info(
            f"Documentos restaurados desde la copia: {documentos_restaurados}"
        )

    st.info(
        "Si algún dato no se actualiza al instante, recarga la página o "
        "reinicia el contenedor/servicio."
    )


def _mostrar_mensaje_reset():

    resultado = st.session_state.pop("reset_db_resultado", None)

    if not resultado:

        return

    st.success("Base de datos reseteada correctamente.")

    ruta_backup = resultado.get("ruta_backup")

    if ruta_backup:

        st.info(f"Copia anterior guardada en: {ruta_backup}")

    else:

        st.warning(
            "La base de datos anterior no existía; se creó una base limpia "
            "sin copia previa."
        )


def _render_copias_seguridad():

    ruta_db = obtener_ruta_db()

    if not os.path.exists(ruta_db):

        st.warning("No se ha encontrado la base de datos actual.")
        return

    if st.button("Crear copia ZIP"):

        nombre = (
            "cuadernopro_backup_"
            + datetime.now().strftime("%Y%m%d_%H%M")
            + ".zip"
        )

        try:

            asegurar_directorio(BACKUPS_DIR)
            ruta_zip = BACKUPS_DIR / nombre
            contador = 1

            while ruta_zip.exists():

                ruta_zip = BACKUPS_DIR / (
                    f"{Path(nombre).stem}_{contador}{Path(nombre).suffix}"
                )
                contador += 1

            resultado_backup = _crear_backup_zip(ruta_zip, ruta_db)

            with open(ruta_zip, "rb") as f:

                st.download_button(
                    "Descargar copia",
                    f,
                    ruta_zip.name
                )

            st.info(f"Copia guardada en: {ruta_zip.resolve()}")
            st.caption(
                "Incluye base SQLite y "
                f"{resultado_backup['documentos_count']} documentos adjuntos."
            )

        except OSError as error:

            st.error(f"No se pudo crear la copia de seguridad: {error}")


def _crear_backup_zip(ruta_zip, ruta_db=None, documentos_dir=None):

    ruta_zip = Path(ruta_zip).expanduser()
    ruta_db = Path(ruta_db or obtener_ruta_db()).expanduser().resolve()
    documentos_dir = Path(documentos_dir or DOCS_DIR).expanduser().resolve()
    documentos = _documentos_para_backup(
        documentos_dir,
        ruta_zip.resolve(),
        ruta_db,
    )

    with zipfile.ZipFile(
        ruta_zip,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as z:

        z.write(
            ruta_db,
            arcname=ruta_db.name,
        )

        for ruta_documento, arcname in documentos:

            z.write(ruta_documento, arcname=arcname)

    return {
        "ruta_zip": str(ruta_zip.resolve()),
        "documentos_count": len(documentos),
    }


def _documentos_para_backup(documentos_dir, ruta_zip, ruta_db):

    documentos_dir = Path(documentos_dir).resolve()

    if not documentos_dir.exists():

        return []

    documentos = []

    for ruta in sorted(documentos_dir.rglob("*")):

        if not ruta.is_file():

            continue

        if _excluir_documento_backup(ruta, documentos_dir, ruta_zip, ruta_db):

            continue

        relativa = ruta.relative_to(documentos_dir)
        arcname = (
            Path(BACKUP_DOCUMENTOS_DIRNAME) / relativa
        ).as_posix()

        if not _ruta_zip_segura(arcname):

            continue

        documentos.append((ruta, arcname))

    return documentos


def _excluir_documento_backup(ruta, documentos_dir, ruta_zip, ruta_db):

    if ruta.is_symlink():

        return True

    try:

        ruta_resuelta = ruta.resolve()
        relativa = ruta.relative_to(documentos_dir)

    except (OSError, ValueError):

        return True

    if not _ruta_dentro_de(ruta_resuelta, documentos_dir):

        return True

    if ruta_resuelta == Path(ruta_zip).resolve():

        return True

    if ruta_resuelta == Path(ruta_db).resolve():

        return True

    for directorio_excluido in (BACKUPS_DIR, EXPORTS_DIR):

        if _ruta_dentro_de(ruta_resuelta, directorio_excluido):

            return True

    partes = [parte.lower() for parte in relativa.parts]

    if any(parte in DIRECTORIOS_EXCLUIDOS_BACKUP for parte in partes):

        return True

    nombre = ruta.name.lower()
    return nombre.endswith(SUFIJOS_TEMPORALES_BACKUP)


def _render_restauracion():

    st.warning(
        "Esta operación sustituirá los datos actuales por los de la copia "
        "subida. Se creará una copia automática de seguridad antes de "
        "restaurar."
    )

    archivo_subido = st.file_uploader(
        "Sube una copia de base de datos de CuadernoPro. Puede ser un "
        "archivo .db/.sqlite o un .zip que contenga la base de datos y, "
        "si procede, documentos adjuntos.",
        type=["db", "sqlite", "sqlite3", "zip"],
        key="backup_restore_uploader"
    )

    if archivo_subido is None:

        return

    archivo_restauracion = None

    try:

        archivo_restauracion = _preparar_archivo_restauracion(archivo_subido)
        validacion = _validar_base_datos(archivo_restauracion.ruta_temporal)
        _mostrar_resumen_validacion(archivo_restauracion, validacion)

        if not validacion["valida"]:

            st.error(validacion["error"])
            return

        _render_confirmacion_restauracion(archivo_restauracion)

    except ValueError as error:

        st.error(str(error))

    except (OSError, sqlite3.Error) as error:

        st.error(f"No se pudo leer la copia subida: {error}")

    finally:

        if archivo_restauracion is not None:

            _eliminar_archivo_restauracion(archivo_restauracion)


def _render_reset_base_datos():

    st.error(
        "Esta operación dejará CuadernoPro como una instalación nueva. "
        "Se eliminarán campañas, parcelas, cultivos, tratamientos, "
        "cosechas, movimientos económicos y el resto de datos actuales."
    )
    st.warning(
        "Antes de resetear se creará automáticamente una copia de seguridad "
        "de la base actual."
    )

    try:

        ruta_db = obtener_ruta_db()

    except RuntimeError as error:

        st.error(str(error))
        return

    if not os.path.exists(ruta_db):

        st.warning(
            "No se ha encontrado la base de datos actual. Se permitirá crear "
            "una base limpia sin copia previa."
        )

    entiende_borrado = st.checkbox(
        "Entiendo que se borrarán los datos actuales y se creará una base "
        "vacía.",
        key="reset_db_entendido"
    )
    acepta_backup = st.checkbox(
        "He creado o acepto crear una copia automática antes del reset.",
        key="reset_db_backup"
    )
    texto_reset = st.text_input(
        "Escribe exactamente RESET CUADERNOPRO",
        key="reset_db_texto_reset"
    )
    texto_borrar = st.text_input(
        "Escribe exactamente BORRAR DATOS",
        key="reset_db_texto_borrar"
    )
    puede_resetear = (
        entiende_borrado
        and acepta_backup
        and texto_reset == "RESET CUADERNOPRO"
        and texto_borrar == "BORRAR DATOS"
    )

    st.error("Operación peligrosa.")

    if st.button(
        "Resetear base de datos",
        disabled=not puede_resetear,
        type="primary",
        key="reset_db_boton"
    ):

        try:

            ruta_backup = resetear_base_datos_creando_backup()

        except Exception as error:

            st.error(f"No se pudo resetear la base de datos: {error}")
            return

        _limpiar_cache_streamlit()
        st.session_state["reset_db_resultado"] = {
            "ruta_backup": ruta_backup,
        }
        _rerun_seguro()


def _preparar_archivo_restauracion(archivo_subido):

    nombre = Path(archivo_subido.name).name
    extension = Path(nombre).suffix.lower()

    if extension not in EXTENSIONES_PERMITIDAS:

        raise ValueError(
            "Formato no permitido. Sube un archivo .db, .sqlite, .sqlite3 "
            "o .zip."
        )

    tamano = getattr(archivo_subido, "size", None)

    if tamano == 0:

        raise ValueError("El archivo subido está vacío.")

    if extension == ".zip":

        return _preparar_desde_zip(archivo_subido)

    return _guardar_upload_temporal(archivo_subido, nombre, extension)


def _preparar_desde_zip(archivo_subido):

    try:

        archivo_subido.seek(0)

        with zipfile.ZipFile(archivo_subido) as z:

            entradas = z.infolist()
            rutas_peligrosas = [
                info.filename
                for info in entradas
                if not _ruta_zip_segura(info.filename)
            ]

            if rutas_peligrosas:

                raise ValueError(
                    "El ZIP contiene rutas internas no permitidas."
                )

            candidatas = [
                info
                for info in entradas
                if (
                    not info.is_dir()
                    and Path(_normalizar_ruta_zip(info.filename))
                    .suffix.lower() in EXTENSIONES_DB
                )
            ]

            if not candidatas:

                raise ValueError(
                    "El ZIP no contiene ninguna base de datos .db, .sqlite "
                    "o .sqlite3."
                )

            if len(candidatas) == 1:

                indice = 0

            else:

                indice = st.selectbox(
                    "Base de datos dentro del ZIP",
                    list(range(len(candidatas))),
                    format_func=lambda i: (
                        f"{candidatas[i].filename} "
                        f"({_formatear_tamano(candidatas[i].file_size)})"
                    )
                )

            seleccionada = candidatas[indice]

            if seleccionada.file_size <= 0:

                raise ValueError(
                    "La base de datos seleccionada dentro del ZIP está vacía."
                )

            suffix = Path(seleccionada.filename).suffix.lower()
            ruta_temporal = _crear_temporal(suffix)
            documentos_temporal = ""

            try:

                with z.open(seleccionada) as origen:

                    with open(ruta_temporal, "wb") as destino:

                        shutil.copyfileobj(origen, destino)

                tamano = os.path.getsize(ruta_temporal)

                if tamano <= 0:

                    raise ValueError(
                        "La base de datos seleccionada dentro del ZIP está "
                        "vacía."
                    )

                documentos_temporal, documentos_count = _extraer_documentos_zip(
                    z,
                    entradas,
                )

                return ArchivoRestauracion(
                    ruta_temporal=ruta_temporal,
                    nombre=seleccionada.filename,
                    tamano=tamano,
                    documentos_temporal=documentos_temporal,
                    documentos_count=documentos_count,
                )

            except Exception:

                _eliminar_temporal(ruta_temporal)
                _eliminar_directorio_temporal(documentos_temporal)
                raise

    except zipfile.BadZipFile as error:

        raise ValueError("El ZIP no se puede leer o está dañado.") from error


def _guardar_upload_temporal(archivo_subido, nombre, extension):

    ruta_temporal = _crear_temporal(extension)

    try:

        archivo_subido.seek(0)

        with open(ruta_temporal, "wb") as destino:

            shutil.copyfileobj(archivo_subido, destino)

        tamano = os.path.getsize(ruta_temporal)

        if tamano <= 0:

            raise ValueError("El archivo subido está vacío.")

        return ArchivoRestauracion(
            ruta_temporal=ruta_temporal,
            nombre=nombre,
            tamano=tamano
        )

    except Exception:

        _eliminar_temporal(ruta_temporal)
        raise


def _crear_temporal(extension):

    with tempfile.NamedTemporaryFile(
        prefix="cuadernopro_restaurar_",
        suffix=extension,
        delete=False
    ) as temporal:

        return temporal.name


def _ruta_zip_segura(nombre):

    if not nombre or "\x00" in nombre:

        return False

    if "\\" in nombre:

        return False

    normalizada = nombre

    if normalizada.startswith("/"):

        return False

    if len(normalizada) >= 2 and normalizada[1] == ":":

        return False

    if normalizada.endswith("/"):

        normalizada = normalizada[:-1]

    partes = normalizada.split("/")

    if not partes:

        return False

    return all(parte not in {"", ".", ".."} for parte in partes)


def _ruta_dentro_de(ruta, directorio):

    try:

        Path(ruta).resolve().relative_to(Path(directorio).resolve())
        return True

    except ValueError:

        return False


def _normalizar_ruta_zip(nombre):

    if nombre.endswith("/"):

        return nombre[:-1]

    return nombre


def _extraer_documentos_zip(z, entradas):

    documentos = [
        info
        for info in entradas
        if _es_entrada_documento_zip(info)
    ]

    if not documentos:

        return "", 0

    temporal = tempfile.mkdtemp(prefix="cuadernopro_documentos_restaurar_")
    base_temporal = Path(temporal).resolve()
    count = 0

    try:

        for info in documentos:

            ruta_normalizada = _normalizar_ruta_zip(info.filename)
            partes = ruta_normalizada.split("/")[1:]

            if not partes:

                continue

            destino = (base_temporal / Path(*partes)).resolve()

            if not _ruta_dentro_de(destino, base_temporal):

                raise ValueError(
                    "El ZIP contiene rutas de documentos no permitidas."
                )

            destino.parent.mkdir(parents=True, exist_ok=True)

            with z.open(info) as origen:

                with open(destino, "wb") as archivo_destino:

                    shutil.copyfileobj(origen, archivo_destino)

            count += 1

        return temporal, count

    except Exception:

        _eliminar_directorio_temporal(temporal)
        raise


def _es_entrada_documento_zip(info):

    if info.is_dir():

        return False

    ruta_normalizada = _normalizar_ruta_zip(info.filename)
    return ruta_normalizada.startswith(f"{BACKUP_DOCUMENTOS_DIRNAME}/")


def _validar_base_datos(ruta_temporal):

    try:

        conn = sqlite3.connect(
            f"file:{ruta_temporal}?mode=ro",
            uri=True
        )

        try:

            filas_integridad = conn.execute(
                "PRAGMA integrity_check"
            ).fetchmany(20)
            resultado_integridad = [
                str(fila[0])
                for fila in filas_integridad
            ]
            tablas = [
                fila[0]
                for fila in conn.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table'
                    AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                    """
                )
            ]

        finally:

            conn.close()

    except sqlite3.Error as error:

        raise ValueError(
            "El archivo no se puede abrir como base de datos SQLite válida."
        ) from error

    tablas_detectadas = set(tablas)
    tablas_minimas_detectadas = sorted(
        tablas_detectadas & TABLAS_MINIMAS_CUADERNOPRO
    )
    tablas_reconocibles = sorted(
        tablas_detectadas & TABLAS_RECONOCIBLES_CUADERNOPRO
    )
    integridad_ok = (
        len(resultado_integridad) == 1
        and resultado_integridad[0].lower() == "ok"
    )

    validacion = {
        "valida": False,
        "error": "",
        "integrity_check": (
            "; ".join(resultado_integridad)
            if resultado_integridad
            else "sin resultado"
        ),
        "numero_tablas": len(tablas),
        "tablas": tablas,
        "tablas_reconocibles": tablas_reconocibles,
        "tablas_minimas_detectadas": tablas_minimas_detectadas,
    }

    if not integridad_ok:

        validacion["error"] = (
            "La base de datos no pasa la comprobación de integridad."
        )
        return validacion

    if len(tablas_minimas_detectadas) < 3:

        validacion["error"] = (
            "La base de datos no parece una copia de CuadernoPro. Debe "
            "contener varias tablas reconocibles como campanas, explotacion, "
            "parcelas o cultivos."
        )
        return validacion

    validacion["valida"] = True

    return validacion


def _mostrar_resumen_validacion(archivo_restauracion, validacion):

    st.subheader("Resumen de la copia subida")

    st.write(f"**Archivo:** {archivo_restauracion.nombre}")
    st.write(f"**Tamaño:** {_formatear_tamano(archivo_restauracion.tamano)}")
    st.write(
        "**Documentos adjuntos en ZIP:** "
        f"{archivo_restauracion.documentos_count}"
    )
    st.write(f"**Número de tablas:** {validacion['numero_tablas']}")
    st.write(
        "**Resultado integrity_check:** "
        f"{validacion['integrity_check']}"
    )

    tablas = validacion["tablas"]

    if tablas:

        st.write("**Tablas detectadas:** " + ", ".join(tablas))

    else:

        st.write("**Tablas detectadas:** ninguna")

    if validacion["valida"]:

        st.success("La base de datos subida es válida.")


def _render_confirmacion_restauracion(archivo_restauracion):

    entiende = st.checkbox(
        "Entiendo que se reemplazará la base de datos actual y, si el ZIP "
        "incluye documentos, se copiarán dentro de la carpeta de documentos."
    )
    texto_confirmacion = st.text_input(
        "Escribe RESTAURAR para confirmar"
    )
    puede_restaurar = entiende and texto_confirmacion == "RESTAURAR"

    if st.button(
        "Restaurar base de datos",
        disabled=not puede_restaurar,
        type="primary"
    ):

        try:

            resultado = _restaurar_base_datos(
                archivo_restauracion.ruta_temporal,
                archivo_restauracion.documentos_temporal,
            )

        except (OSError, ValueError) as error:

            st.error(f"No se pudo restaurar la base de datos: {error}")
            return

        _limpiar_cache_streamlit()
        st.session_state["restauracion_db_resultado"] = resultado
        _rerun_seguro()


def _restaurar_base_datos(ruta_temporal, documentos_temporal=""):

    ruta_db = obtener_ruta_db()
    directorio_db = os.path.dirname(ruta_db)

    if not directorio_db:

        raise ValueError("No se pudo resolver la carpeta de la base de datos.")

    ruta_backup = _crear_backup_antes_de_restaurar(ruta_db)
    descriptor, ruta_intermedia = tempfile.mkstemp(
        prefix=".cuadernopro_restaurando_",
        suffix=".db",
        dir=directorio_db
    )
    os.close(descriptor)

    try:

        shutil.copyfile(ruta_temporal, ruta_intermedia)
        _aplicar_permisos_db(ruta_db, ruta_intermedia)

        try:

            os.replace(ruta_intermedia, ruta_db)

        except OSError as error:

            if error.errno != errno.EBUSY:

                raise

            # Docker puede rechazar rename sobre una ruta montada como fichero.
            _sobrescribir_fichero_montado(ruta_intermedia, ruta_db)

        avisos = _eliminar_auxiliares_sqlite(ruta_db)
        resultado_documentos = _restaurar_documentos_backup(
            documentos_temporal
        )

        if resultado_documentos["backup_documentos"]:

            avisos.append(
                "Se respaldaron documentos existentes antes de "
                "sobrescribirlos en: "
                f"{resultado_documentos['backup_documentos']}"
            )

    except Exception:

        _eliminar_temporal(ruta_intermedia)
        raise

    return {
        "ruta_backup": ruta_backup,
        "avisos": avisos,
        "documentos_restaurados": (
            resultado_documentos["documentos_restaurados"]
        ),
    }


def _restaurar_documentos_backup(documentos_temporal):

    if not documentos_temporal:

        return {
            "documentos_restaurados": 0,
            "backup_documentos": "",
        }

    origen_base = Path(documentos_temporal).resolve()

    if not origen_base.exists():

        return {
            "documentos_restaurados": 0,
            "backup_documentos": "",
        }

    destino_base = Path(DOCS_DIR).resolve()
    asegurar_directorio(destino_base)
    archivos = [
        ruta
        for ruta in sorted(origen_base.rglob("*"))
        if ruta.is_file()
    ]
    backup_documentos = None
    documentos_restaurados = 0

    for origen in archivos:

        if origen.is_symlink():

            continue

        origen_resuelto = origen.resolve()

        if not _ruta_dentro_de(origen_resuelto, origen_base):

            raise ValueError(
                "La copia contiene documentos fuera de la carpeta temporal."
            )

        relativa = origen.relative_to(origen_base)
        destino = (destino_base / relativa).resolve()

        if not _ruta_dentro_de(destino, destino_base):

            raise ValueError(
                "La copia contiene rutas de documentos no permitidas."
            )

        if destino.exists() and destino.is_dir():

            raise ValueError(
                "No se puede restaurar un documento sobre una carpeta "
                f"existente: {relativa.as_posix()}"
            )

        if destino.exists():

            if backup_documentos is None:

                backup_documentos = _crear_backup_documentos_restauracion()

            destino_backup = (backup_documentos / relativa).resolve()

            if not _ruta_dentro_de(destino_backup, backup_documentos):

                raise ValueError(
                    "No se pudo preparar el backup previo de documentos."
                )

            destino_backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destino, destino_backup)

        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, destino)
        documentos_restaurados += 1

    return {
        "documentos_restaurados": documentos_restaurados,
        "backup_documentos": (
            str(backup_documentos.resolve())
            if backup_documentos is not None
            else ""
        ),
    }


def _crear_backup_documentos_restauracion():

    asegurar_directorio(BACKUPS_DIR)
    marca_tiempo = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ruta_backup = BACKUPS_DIR / (
        f"documentos_antes_restaurar_{marca_tiempo}"
    )
    contador = 1

    while ruta_backup.exists():

        ruta_backup = BACKUPS_DIR / (
            f"documentos_antes_restaurar_{marca_tiempo}_{contador}"
        )
        contador += 1

    ruta_backup.mkdir(parents=True, exist_ok=False)
    return ruta_backup


def _crear_backup_antes_de_restaurar(ruta_db):

    if not os.path.exists(ruta_db):

        return None

    asegurar_directorio(BACKUPS_DIR)
    marca_tiempo = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ruta_backup = BACKUPS_DIR / f"antes_restaurar_{marca_tiempo}.db"
    shutil.copy2(ruta_db, ruta_backup)

    return str(ruta_backup.resolve())


def _aplicar_permisos_db(ruta_db, ruta_intermedia):

    if os.path.exists(ruta_db):

        modo = os.stat(ruta_db).st_mode & 0o777

    else:

        modo = 0o644

    os.chmod(ruta_intermedia, modo)


def _sobrescribir_fichero_montado(ruta_origen, ruta_destino):

    with open(ruta_origen, "rb") as origen:

        with open(ruta_destino, "wb") as destino:

            shutil.copyfileobj(origen, destino)
            destino.flush()
            os.fsync(destino.fileno())

    _eliminar_temporal(ruta_origen)


def _eliminar_auxiliares_sqlite(ruta_db):

    avisos = []

    for sufijo in ("-wal", "-shm", "-journal"):

        ruta_auxiliar = ruta_db + sufijo

        if not os.path.exists(ruta_auxiliar):

            continue

        try:

            os.remove(ruta_auxiliar)

        except OSError as error:

            avisos.append(
                "No se pudo eliminar el archivo auxiliar de SQLite "
                f"{os.path.basename(ruta_auxiliar)}: {error}"
            )

    return avisos


def _limpiar_cache_streamlit():

    try:

        st.cache_data.clear()

    except Exception:

        pass

    try:

        st.cache_resource.clear()

    except Exception:

        pass


def _rerun_seguro():

    if hasattr(st, "rerun"):

        st.rerun()
        return

    if hasattr(st, "experimental_rerun"):

        st.experimental_rerun()


def _eliminar_temporal(ruta):

    try:

        if ruta and os.path.exists(ruta):

            os.remove(ruta)

    except OSError:

        pass


def _eliminar_directorio_temporal(ruta):

    try:

        if ruta and os.path.exists(ruta):

            shutil.rmtree(ruta)

    except OSError:

        pass


def _eliminar_archivo_restauracion(archivo_restauracion):

    _eliminar_temporal(archivo_restauracion.ruta_temporal)
    _eliminar_directorio_temporal(
        archivo_restauracion.documentos_temporal
    )


def _formatear_tamano(tamano):

    valor = float(tamano)

    for unidad in ("B", "KB", "MB", "GB"):

        if valor < 1024 or unidad == "GB":

            if unidad == "B":

                return f"{int(valor)} {unidad}"

            return f"{valor:.1f} {unidad}"

        valor = valor / 1024

    return f"{valor:.1f} GB"
