#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Windows launcher for CuadernoPro.

This file is intentionally self-contained so it can be used as the PyInstaller
entry point. It prepares user data folders, configures CuadernoPro environment
variables and starts Streamlit bound to localhost.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
from urllib import error as urlerror
from urllib import request as urlrequest
import webbrowser


APP_NAME = "CuadernoPro"
HOST = "127.0.0.1"
PORT_INICIAL = 8501
PORT_INTENTOS = 100
NOMBRE_DB = "cuadernopro.db"
ENV_DATA_ROOT = "CUADERNOPRO_WINDOWS_DATA_ROOT"
LOCK_FILENAME = "cuadernopro.lock"
EDGE_PROFILE_DIRNAME = "browser-profile"
STREAMLIT_READY_TIMEOUT = 90


@dataclass(frozen=True)
class BrowserLaunch:
    mode: str
    process: subprocess.Popen | None = None
    executable: Path | None = None


def _mensaje_usuario(titulo: str, detalle: str) -> None:
    texto = f"{detalle}\n\nRevise el log de {APP_NAME} para mas detalle."
    print(f"{titulo}\n{texto}", file=sys.stderr)

    if os.name != "nt":
        return

    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, texto, titulo, 0x10)
    except Exception:
        pass


def _documentos_windows_api() -> Path | None:
    if os.name != "nt":
        return None

    try:
        import ctypes
        import uuid
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8),
            ]

            def __init__(self, valor: str) -> None:
                identificador = uuid.UUID(valor)
                campos = identificador.fields
                data4 = [campos[3], campos[4]]
                data4.extend(campos[5].to_bytes(6, "big"))
                super().__init__(
                    campos[0],
                    campos[1],
                    campos[2],
                    (ctypes.c_ubyte * 8)(*data4),
                )

        folderid_documents = GUID("FDD39AD0-238F-46AF-ADB4-6C85480369C7")
        ruta_ptr = ctypes.c_wchar_p()

        sh_get_known_folder_path = ctypes.windll.shell32.SHGetKnownFolderPath
        sh_get_known_folder_path.argtypes = [
            ctypes.POINTER(GUID),
            wintypes.DWORD,
            wintypes.HANDLE,
            ctypes.POINTER(ctypes.c_wchar_p),
        ]
        sh_get_known_folder_path.restype = getattr(
            wintypes,
            "HRESULT",
            ctypes.c_long,
        )

        resultado = sh_get_known_folder_path(
            ctypes.byref(folderid_documents),
            0,
            None,
            ctypes.byref(ruta_ptr),
        )

        if resultado != 0 or not ruta_ptr.value:
            return None

        try:
            return Path(ruta_ptr.value)
        finally:
            co_task_mem_free = ctypes.windll.ole32.CoTaskMemFree
            co_task_mem_free.argtypes = [ctypes.c_void_p]
            co_task_mem_free.restype = None
            co_task_mem_free(ruta_ptr)

    except Exception:
        return None


def _carpeta_documentos_usuario() -> Path:
    ruta_api = _documentos_windows_api()

    if ruta_api is not None:
        return ruta_api

    return Path.home() / "Documents"


def _resolver_raiz_datos(data_root: str | None = None) -> Path:
    valor = data_root or os.environ.get(ENV_DATA_ROOT)

    if valor:
        return Path(valor).expanduser().resolve()

    return _carpeta_documentos_usuario() / APP_NAME


def _preparar_directorios(data_root: str | None = None) -> dict[str, Path]:
    raiz = _resolver_raiz_datos(data_root)
    directorios = {
        "raiz": raiz,
        "datos": raiz / "datos",
        "documentos": raiz / "documentos",
        "copias": raiz / "copias",
        "exportaciones": raiz / "exportaciones",
        "logs": raiz / "logs",
    }

    for ruta in directorios.values():
        ruta.mkdir(parents=True, exist_ok=True)

    return directorios


def _configurar_logging(logs_dir: Path, debug: bool = False) -> Path:
    marca = time.strftime("%Y%m%d_%H%M%S")
    ruta_log = logs_dir / f"cuadernopro_launcher_{marca}.log"

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(ruta_log, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )
    logging.info("Log iniciado en %s", ruta_log)
    return ruta_log


def _configurar_entorno(directorios: dict[str, Path]) -> None:
    variables = {
        "CUADERNOPRO_DB_PATH": directorios["datos"] / NOMBRE_DB,
        "CUADERNOPRO_DOCUMENTOS_DIR": directorios["documentos"],
        "CUADERNOPRO_BACKUPS_DIR": directorios["copias"],
        "CUADERNOPRO_EXPORTS_DIR": directorios["exportaciones"],
    }

    for nombre, ruta in variables.items():
        os.environ[nombre] = str(ruta)
        logging.info("%s=%s", nombre, ruta)

    os.environ.setdefault("PYTHONUNBUFFERED", "1")


def _configurar_streamlit_runtime(puerto: int) -> None:
    variables = {
        "STREAMLIT_GLOBAL_DEVELOPMENT_MODE": "false",
        "STREAMLIT_SERVER_HEADLESS": "true",
        "STREAMLIT_SERVER_ADDRESS": HOST,
        "STREAMLIT_SERVER_PORT": str(puerto),
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
    }

    for nombre, valor in variables.items():
        os.environ[nombre] = valor

    from streamlit import config as st_config

    st_config.set_option("global.developmentMode", False, "launcher")
    st_config.set_option("server.headless", True, "launcher")
    st_config.set_option("server.address", HOST, "launcher")
    st_config.set_option("server.port", puerto, "launcher")
    st_config.set_option("browser.gatherUsageStats", False, "launcher")

    logging.info("STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false")
    logging.info("STREAMLIT_SERVER_HEADLESS=true")
    logging.info("STREAMLIT_SERVER_ADDRESS=%s", HOST)
    logging.info("STREAMLIT_SERVER_PORT=%s", puerto)
    logging.info("STREAMLIT_BROWSER_GATHER_USAGE_STATS=false")


def _candidatos_app_py() -> list[Path]:
    candidatos: list[Path] = []
    app_env = os.environ.get("CUADERNOPRO_APP_PATH")

    if app_env:
        candidatos.append(Path(app_env).expanduser())

    meipass = getattr(sys, "_MEIPASS", None)

    if meipass:
        candidatos.append(Path(meipass) / "app.py")
        candidatos.append(Path(meipass) / "_internal" / "app.py")

    ejecutable_dir = Path(sys.executable).resolve().parent
    candidatos.append(ejecutable_dir / "app.py")
    candidatos.append(ejecutable_dir / "_internal" / "app.py")

    archivo_actual = Path(__file__).resolve()
    candidatos.append(archivo_actual.parent / "app.py")

    for padre in archivo_actual.parents:
        candidatos.append(padre / "app.py")

    candidatos.append(Path.cwd() / "app.py")
    return candidatos


def _localizar_app_py() -> Path:
    revisadas: list[str] = []

    for candidato in _candidatos_app_py():
        try:
            ruta = candidato.resolve()
        except OSError:
            ruta = candidato.absolute()

        revisadas.append(str(ruta))

        if ruta.is_file():
            return ruta

    detalle = "\n".join(f"- {ruta}" for ruta in revisadas)
    raise FileNotFoundError(
        "No se encontro app.py. Rutas revisadas:\n" + detalle
    )


def _puerto_disponible(puerto: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind((HOST, puerto))
        except OSError:
            return False

    return True


def _buscar_puerto_libre(inicial: int = PORT_INICIAL) -> int:
    for puerto in range(inicial, inicial + PORT_INTENTOS):
        if _puerto_disponible(puerto):
            return puerto

    raise RuntimeError(
        f"No se encontro un puerto libre entre {inicial} "
        f"y {inicial + PORT_INTENTOS - 1}."
    )


def _puerto_escuchando(puerto: int) -> bool:
    try:
        with socket.create_connection((HOST, puerto), timeout=0.5):
            return True
    except OSError:
        return False


def _http_responde(url: str, timeout: float = 1.0) -> bool:
    try:
        with urlrequest.urlopen(url, timeout=timeout) as respuesta:
            codigo = respuesta.getcode()
            return 200 <= codigo < 500
    except urlerror.HTTPError as error:
        return 200 <= error.code < 500
    except (OSError, ValueError, urlerror.URLError):
        return False


def _pid_vivo_windows(pid: int) -> bool:
    try:
        import ctypes

        synchronize = 0x00100000
        wait_timeout = 0x00000102
        handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, pid)

        if not handle:
            return False

        try:
            resultado = ctypes.windll.kernel32.WaitForSingleObject(handle, 0)
            return resultado == wait_timeout
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        return False


def _pid_vivo(pid: object) -> bool:
    try:
        pid_entero = int(pid)
    except (TypeError, ValueError):
        return False

    if pid_entero <= 0:
        return False

    if pid_entero == os.getpid():
        return True

    if os.name == "nt":
        return _pid_vivo_windows(pid_entero)

    try:
        os.kill(pid_entero, 0)
    except PermissionError:
        return True
    except OSError:
        return False

    return True


def _ruta_lock(directorios: dict[str, Path]) -> Path:
    return directorios["raiz"] / LOCK_FILENAME


def _leer_lock(lock_path: Path) -> dict[str, object] | None:
    try:
        contenido = lock_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as error:
        logging.warning("No se pudo leer lock %s: %s", lock_path, error)
        return None

    for intento in range(3):
        try:
            datos = json.loads(contenido)
            break
        except json.JSONDecodeError as error:
            if intento < 2:
                time.sleep(0.1)
                try:
                    contenido = lock_path.read_text(encoding="utf-8")
                except OSError:
                    return None
                continue

            logging.warning("Lock invalido %s: %s", lock_path, error)
            return None

    if not isinstance(datos, dict):
        logging.warning("Lock invalido %s: contenido no es objeto JSON", lock_path)
        return None

    return datos


def _datos_instancia_desde_lock(
    lock: dict[str, object],
) -> tuple[int, str] | None:
    try:
        puerto = int(lock.get("port", 0))
    except (TypeError, ValueError):
        return None

    if puerto <= 0:
        return None

    url = str(lock.get("url") or f"http://{HOST}:{puerto}")
    return puerto, url


def _eliminar_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except FileNotFoundError:
        return
    except OSError as error:
        logging.warning("No se pudo eliminar lock %s: %s", lock_path, error)


def _eliminar_lock_si_propietario(lock_path: Path, pid: int) -> None:
    lock = _leer_lock(lock_path)

    if lock is None:
        return

    try:
        pid_lock = int(lock.get("pid", 0))
    except (TypeError, ValueError):
        pid_lock = 0

    if pid_lock == pid:
        _eliminar_lock(lock_path)
        logging.info("Lock eliminado: %s", lock_path)


def _crear_lock(lock_path: Path, datos: dict[str, object]) -> bool:
    contenido = json.dumps(datos, indent=2, sort_keys=True) + "\n"

    try:
        descriptor = os.open(
            str(lock_path),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        )
    except FileExistsError:
        return False

    with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)

    logging.info("Lock creado: %s", lock_path)
    return True


def _instancia_activa_desde_lock(lock_path: Path) -> dict[str, object] | None:
    lock = _leer_lock(lock_path)

    if lock is None:
        if lock_path.exists():
            logging.info("Eliminando lock no utilizable: %s", lock_path)
            _eliminar_lock(lock_path)
        return None

    datos_instancia = _datos_instancia_desde_lock(lock)

    if datos_instancia is None:
        logging.info("Eliminando lock sin puerto valido: %s", lock_path)
        _eliminar_lock(lock_path)
        return None

    puerto, url = datos_instancia

    if _http_responde(url):
        logging.info(
            "Instancia existente responde: pid=%s puerto=%s url=%s",
            lock.get("pid"),
            puerto,
            url,
        )
        return lock

    if _pid_vivo(lock.get("pid")):
        logging.info(
            "Instancia existente aun arrancando: pid=%s puerto=%s url=%s",
            lock.get("pid"),
            puerto,
            url,
        )
        limite = time.monotonic() + STREAMLIT_READY_TIMEOUT

        while time.monotonic() < limite and _pid_vivo(lock.get("pid")):
            if _http_responde(url):
                logging.info("Instancia existente lista en %s", url)
                return lock

            time.sleep(1.0)

    logging.info("Eliminando lock antiguo o sin respuesta: %s", lock_path)
    _eliminar_lock(lock_path)
    return None


def _candidatos_msedge() -> list[Path]:
    bases = [
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("ProgramFiles", r"C:\Program Files"),
    ]
    candidatos = [
        Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
        for base in bases
        if base
    ]

    for comando in ("msedge.exe", "msedge"):
        ruta = shutil.which(comando)

        if ruta:
            candidatos.append(Path(ruta))

    return candidatos


def _buscar_msedge() -> Path | None:
    for candidato in _candidatos_msedge():
        try:
            ruta = candidato.resolve()
        except OSError:
            ruta = candidato

        if ruta.is_file():
            return ruta

    return None


def _abrir_edge_app(url: str, directorios: dict[str, Path]) -> BrowserLaunch | None:
    edge_path = _buscar_msedge()

    if edge_path is None:
        logging.warning(
            "Microsoft Edge no encontrado; se usara navegador por defecto."
        )
        return None

    perfil = directorios["raiz"] / EDGE_PROFILE_DIRNAME
    perfil.mkdir(parents=True, exist_ok=True)
    comando = [
        str(edge_path),
        f"--app={url}",
        f"--user-data-dir={perfil}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-mode",
    ]

    creationflags = 0

    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    try:
        proceso = subprocess.Popen(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
    except OSError as error:
        logging.warning("No se pudo abrir Microsoft Edge: %s", error)
        return None
    logging.info("Modo navegador usado: edge app")
    logging.info("Ruta Edge: %s", edge_path)
    logging.info("Perfil navegador: %s", perfil)
    logging.info("PID navegador=%s", proceso.pid)
    logging.info("Navegador abierto en %s", url)
    return BrowserLaunch(mode="edge app", process=proceso, executable=edge_path)


def _abrir_navegador_defecto(url: str) -> BrowserLaunch:
    abierto = webbrowser.open(url, new=2)

    if abierto:
        logging.info("Navegador por defecto abierto en %s", url)
    else:
        logging.warning("No se pudo abrir automaticamente el navegador en %s", url)

    logging.info("Modo navegador usado: default browser")
    logging.warning(
        "El navegador por defecto no permite detectar el cierre de la ventana."
    )
    return BrowserLaunch(mode="default browser")


def _abrir_navegador(
    url: str,
    directorios: dict[str, Path],
    browser_mode: str,
) -> BrowserLaunch:
    if browser_mode == "app":
        lanzamiento = _abrir_edge_app(url, directorios)

        if lanzamiento is not None:
            return lanzamiento

    return _abrir_navegador_defecto(url)


def _cerrar_por_cierre_navegador(
    proceso: subprocess.Popen,
    lock_path: Path,
) -> None:
    codigo = proceso.wait()
    logging.info(
        "Cierre detectado del navegador: pid=%s codigo=%s",
        proceso.pid,
        codigo,
    )
    logging.info("Cerrando CuadernoPro por cierre de ventana de app.")
    _eliminar_lock_si_propietario(lock_path, os.getpid())
    logging.shutdown()
    os._exit(0)


def _abrir_navegador_cuando_listo(
    url: str,
    puerto: int,
    directorios: dict[str, Path],
    browser_mode: str,
    exit_on_browser_close: bool,
    lock_path: Path,
) -> None:
    limite = time.monotonic() + STREAMLIT_READY_TIMEOUT

    while time.monotonic() < limite:
        if _puerto_escuchando(puerto):
            time.sleep(0.8)
            lanzamiento = _abrir_navegador(url, directorios, browser_mode)

            if lanzamiento.process is None:
                logging.info(
                    "No hay proceso de navegador monitorizable para %s.",
                    lanzamiento.mode,
                )
                return

            if not exit_on_browser_close:
                logging.info("Cierre por navegador desactivado por argumento.")
                return

            logging.info(
                "Monitorizando navegador: modo=%s pid=%s",
                lanzamiento.mode,
                lanzamiento.process.pid,
            )
            _cerrar_por_cierre_navegador(lanzamiento.process, lock_path)
            return

        time.sleep(0.5)

    logging.warning("No se pudo confirmar el arranque de Streamlit en %s", url)
    _mensaje_usuario(
        "CuadernoPro tarda en arrancar",
        "No se pudo confirmar automaticamente que Streamlit este listo. "
        f"Si la ventana no se ha abierto, pruebe a abrir {url}.",
    )


def _ejecutar_streamlit(app_path: Path, puerto: int) -> int:
    _configurar_streamlit_runtime(puerto)

    try:
        from streamlit.web import cli as streamlit_cli
    except Exception as error:
        raise RuntimeError(
            "No se pudo importar Streamlit. Revise que las dependencias "
            "esten instaladas o incluidas en el paquete."
        ) from error

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        HOST,
        "--server.port",
        str(puerto),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]

    try:
        streamlit_cli.main()
    except SystemExit as salida:
        codigo = salida.code

        if codigo in (None, 0):
            return 0

        raise RuntimeError(f"Streamlit termino con codigo {codigo}") from salida

    return 0


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Launcher Windows de CuadernoPro",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Arranca CuadernoPro sin abrir automaticamente el navegador.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=PORT_INICIAL,
        help="Puerto inicial para buscar un puerto libre.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activa logs mas detallados del launcher.",
    )
    parser.add_argument(
        "--print-paths",
        action="store_true",
        help="Muestra rutas resueltas y termina sin arrancar Streamlit.",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help=(
            "Carpeta raiz de datos. Si no se indica, se usa "
            f"{ENV_DATA_ROOT} o Documents\\CuadernoPro."
        ),
    )
    parser.add_argument(
        "--browser-mode",
        choices=("app", "default"),
        default="app",
        help=(
            "Modo de navegador. app usa Microsoft Edge en modo aplicacion "
            "si esta disponible; default usa el navegador predeterminado."
        ),
    )
    parser.add_argument(
        "--no-exit-on-browser-close",
        action="store_true",
        help=(
            "Mantiene Streamlit vivo aunque se cierre la ventana del "
            "navegador. Util para desarrollo."
        ),
    )
    return parser


def _imprimir_rutas(
    directorios: dict[str, Path],
    app_path: Path | None,
    ruta_log: Path,
) -> None:
    print(f"APP_NAME={APP_NAME}")
    print(f"frozen={bool(getattr(sys, 'frozen', False))}")
    print(f"executable={Path(sys.executable).resolve()}")
    print(f"meipass={getattr(sys, '_MEIPASS', '')}")
    print(f"app_path={app_path or ''}")
    print(f"log={ruta_log}")
    print(f"lock={_ruta_lock(directorios)}")

    for nombre, ruta in directorios.items():
        print(f"{nombre}={ruta}")

    for nombre in (
        "CUADERNOPRO_DB_PATH",
        "CUADERNOPRO_DOCUMENTOS_DIR",
        "CUADERNOPRO_BACKUPS_DIR",
        "CUADERNOPRO_EXPORTS_DIR",
    ):
        print(f"{nombre}={os.environ.get(nombre, '')}")


def main(argv: list[str] | None = None) -> int:
    args = _crear_parser().parse_args(argv)
    lock_path: Path | None = None

    try:
        directorios = _preparar_directorios(args.data_root)
    except Exception as error:
        _mensaje_usuario(
            "No se pudo preparar CuadernoPro",
            "No se pudieron crear las carpetas de datos en Documentos. "
            f"Detalle: {error}",
        )
        return 1

    ruta_log = _configurar_logging(directorios["logs"], debug=args.debug)

    try:
        logging.info("Data root=%s", directorios["raiz"])
        logging.info("PID launcher=%s", os.getpid())
        logging.info("Browser mode solicitado=%s", args.browser_mode)
        logging.info(
            "Salir al cerrar navegador=%s",
            not args.no_exit_on_browser_close,
        )
        _configurar_entorno(directorios)
        app_path = _localizar_app_py()
        lock_path = _ruta_lock(directorios)

        if args.print_paths:
            _imprimir_rutas(directorios, app_path, ruta_log)
            return 0

        app_root = app_path.parent

        if str(app_root) not in sys.path:
            sys.path.insert(0, str(app_root))

        os.chdir(app_root)
        instancia = _instancia_activa_desde_lock(lock_path)

        if instancia is not None:
            datos_instancia = _datos_instancia_desde_lock(instancia)

            if datos_instancia is None:
                raise RuntimeError("Lock de instancia activa sin puerto valido.")

            puerto_existente, url_existente = datos_instancia
            logging.info(
                "Reutilizando instancia viva: pid=%s puerto=%s url=%s",
                instancia.get("pid"),
                puerto_existente,
                url_existente,
            )

            if args.no_browser:
                logging.info(
                    "No se abre navegador para instancia existente por --no-browser."
                )
            else:
                _abrir_navegador(
                    url_existente,
                    directorios,
                    args.browser_mode,
                )

            logging.info("No se arranca un segundo servidor Streamlit.")
            return 0

        puerto = _buscar_puerto_libre(args.port)
        url = f"http://{HOST}:{puerto}"
        lock_datos = {
            "app": APP_NAME,
            "pid": os.getpid(),
            "port": puerto,
            "url": url,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "data_root": str(directorios["raiz"]),
        }

        if not _crear_lock(lock_path, lock_datos):
            instancia = _instancia_activa_desde_lock(lock_path)

            if instancia is not None:
                datos_instancia = _datos_instancia_desde_lock(instancia)

                if datos_instancia is not None:
                    _, url_existente = datos_instancia
                    logging.info(
                        "Lock creado por otra instancia; abriendo %s",
                        url_existente,
                    )

                    if not args.no_browser:
                        _abrir_navegador(
                            url_existente,
                            directorios,
                            args.browser_mode,
                        )

                    return 0

            raise RuntimeError(f"No se pudo crear el lock de instancia: {lock_path}")

        logging.info("Puerto elegido=%s", puerto)
        logging.info("app.py localizado en %s", app_path)
        logging.info("Directorio de trabajo: %s", app_root)
        logging.info("Arrancando CuadernoPro en %s", url)

        if not args.no_browser:
            threading.Thread(
                target=_abrir_navegador_cuando_listo,
                args=(
                    url,
                    puerto,
                    directorios,
                    args.browser_mode,
                    not args.no_exit_on_browser_close,
                    lock_path,
                ),
                daemon=True,
            ).start()
        else:
            logging.info("Apertura automatica de navegador desactivada.")

        return _ejecutar_streamlit(app_path, puerto)

    except Exception as error:
        logging.error("No se pudo iniciar CuadernoPro:\n%s", traceback.format_exc())
        _mensaje_usuario(
            "No se pudo iniciar CuadernoPro",
            "CuadernoPro no pudo arrancar. "
            f"Detalle: {error}\n\nLog: {ruta_log}",
        )
        return 1
    finally:
        if lock_path is not None:
            _eliminar_lock_si_propietario(lock_path, os.getpid())


if __name__ == "__main__":
    raise SystemExit(main())
