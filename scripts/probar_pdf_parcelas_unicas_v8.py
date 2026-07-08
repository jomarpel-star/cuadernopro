#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import sqlite3
import sys
import types


APP_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = APP_ROOT / "runtime" / "tests"
DB_PRUEBA = RUNTIME_DIR / "prueba_pdf_parcelas_unicas_v8.db"
EXPORTS_PRUEBA = RUNTIME_DIR / "exports_pdf_parcelas_unicas_v8"
DOCS_PRUEBA = RUNTIME_DIR / "documentos_pdf_parcelas_unicas_v8"
BACKUPS_PRUEBA = RUNTIME_DIR / "backups_pdf_parcelas_unicas_v8"

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_PRUEBA)
os.environ["CUADERNOPRO_EXPORTS_DIR"] = str(EXPORTS_PRUEBA)
os.environ["CUADERNOPRO_DOCUMENTOS_DIR"] = str(DOCS_PRUEBA)
os.environ["CUADERNOPRO_BACKUPS_DIR"] = str(BACKUPS_PRUEBA)

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

if "streamlit" not in sys.modules:

    sys.modules["streamlit"] = types.SimpleNamespace()

from core.db import crear_tablas  # noqa: E402
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
        EXPORTS_PRUEBA,
        DOCS_PRUEBA,
        BACKUPS_PRUEBA,
    ):

        _limpiar_ruta(ruta)

    EXPORTS_PRUEBA.mkdir(parents=True, exist_ok=True)
    DOCS_PRUEBA.mkdir(parents=True, exist_ok=True)
    BACKUPS_PRUEBA.mkdir(parents=True, exist_ok=True)
    crear_tablas(DB_PRUEBA)


def _asegurar_columna(conn, tabla, columna, definicion):

    columnas = {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }

    if columna not in columnas:

        conn.execute(
            f'ALTER TABLE "{tabla}" ADD COLUMN "{columna}" {definicion}'
        )


def _insertar_cultivo(
    conn,
    campana_id,
    parcela_id,
    nombre,
    variedad,
    sistema,
    superficie,
    ahora,
):

    cultivo_id = conn.execute(
        """
        INSERT INTO cultivos
        (campana_id, nombre, variedad, codigo_siex, superficie,
         ano_plantacion, marco_plantacion, numero_arboles, sistema, activo,
         created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            nombre,
            variedad,
            "104",
            superficie,
            2018,
            "7X7",
            5627,
            sistema,
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO cultivo_parcelas
        (cultivo_id, parcela_id, superficie, created_at, updated_at)
        VALUES (?,?,?,?,?)
        """,
        (cultivo_id, parcela_id, superficie, ahora, ahora),
    )
    return cultivo_id


def _insertar_datos():

    ahora = "2026-07-08T00:00:00"

    with sqlite3.connect(DB_PRUEBA) as conn:

        conn.execute("PRAGMA foreign_keys=ON")
        _asegurar_columna(conn, "cultivos", "sistema", "TEXT")

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
                "Explotacion parcelas unicas",
                "Titular parcelas unicas",
                "00000000T",
                "Camino de prueba",
                "Jumilla",
                "Murcia",
                "30520",
                "600000000",
                "prueba@example.com",
                "REGEPA-PARCELAS-001",
                "REGEPA",
                "REG-PARCELAS-001",
                "SECANO TRADICIONAL",
                "Almendro",
                "2025-10-01",
                1,
                0,
                "Responsable prueba",
                "Asesor prueba",
                "ASE-001",
                "Prueba de parcelas unicas",
                ahora,
                ahora,
            ),
        )
        campana_anterior_id = conn.execute(
            """
            INSERT INTO campanas
            (nombre, fecha_inicio, fecha_fin, activa, estado,
             observaciones, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                "2024/2025",
                "2024-10-01",
                "2025-09-30",
                0,
                "cerrada",
                "Campana anterior",
                ahora,
                ahora,
            ),
        ).lastrowid
        campana_actual_id = conn.execute(
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
                "Campana actual",
                ahora,
                ahora,
            ),
        ).lastrowid
        parcela_duplicada_id = conn.execute(
            """
            INSERT INTO parcelas
            (nombre, provincia_sigpac, municipio_sigpac, agregado_sigpac,
             zona_sigpac, poligono, parcela, recinto, superficie_sigpac,
             uso_sigpac, activa, observaciones, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "Parcela duplicada por cultivos",
                30,
                "022",
                0,
                0,
                "007",
                "00045",
                "02",
                4.5,
                "TA",
                1,
                "Parcela con relaciones multiples",
                ahora,
                ahora,
            ),
        ).lastrowid
        parcela_fallback_id = conn.execute(
            """
            INSERT INTO parcelas
            (nombre, provincia_sigpac, municipio_sigpac, agregado_sigpac,
             zona_sigpac, poligono, parcela, recinto, superficie_sigpac,
             uso_sigpac, activa, observaciones, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "Parcela fallback sistema",
                30,
                22,
                0,
                0,
                "8",
                "46",
                "1",
                2.25,
                "TA",
                1,
                "Parcela sin sistema en cultivo",
                ahora,
                ahora,
            ),
        ).lastrowid
        parcela_doble_sistema_id = conn.execute(
            """
            INSERT INTO parcelas
            (nombre, provincia_sigpac, municipio_sigpac, agregado_sigpac,
             zona_sigpac, poligono, parcela, recinto, superficie_sigpac,
             uso_sigpac, activa, observaciones, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "Parcela con dos sistemas",
                30,
                23,
                0,
                0,
                "1",
                "1",
                "1",
                3.0,
                "TA",
                1,
                "Parcela con sistemas distintos",
                ahora,
                ahora,
            ),
        ).lastrowid

        _insertar_cultivo(
            conn,
            campana_anterior_id,
            parcela_duplicada_id,
            "OLIVAR",
            "Manzanilla",
            "REGADIO",
            4.5,
            ahora,
        )
        _insertar_cultivo(
            conn,
            campana_actual_id,
            parcela_duplicada_id,
            "ALMENDRO",
            "Guara",
            "Secano",
            4.5,
            ahora,
        )
        _insertar_cultivo(
            conn,
            campana_actual_id,
            parcela_duplicada_id,
            "ALMENDRO",
            "Guara",
            "Secano",
            4.5,
            ahora,
        )
        _insertar_cultivo(
            conn,
            campana_actual_id,
            parcela_fallback_id,
            "ALMENDRO",
            "Lauranne",
            "",
            2.25,
            ahora,
        )
        _insertar_cultivo(
            conn,
            campana_actual_id,
            parcela_doble_sistema_id,
            "ALMENDRO",
            "Guara",
            "Secano",
            1.5,
            ahora,
        )
        _insertar_cultivo(
            conn,
            campana_actual_id,
            parcela_doble_sistema_id,
            "OLIVAR",
            "Arbequina",
            "Regadío",
            1.5,
            ahora,
        )
        conn.commit()

    return {
        "campana_actual_id": campana_actual_id,
        "parcela_duplicada_id": parcela_duplicada_id,
        "parcela_fallback_id": parcela_fallback_id,
        "parcela_doble_sistema_id": parcela_doble_sistema_id,
    }


def _por_id(filas):

    return {
        int(fila["id"]): fila
        for fila in filas
    }


def _clave_sigpac(fila):

    return (
        str(fila.get("provincia_sigpac")),
        str(fila.get("municipio_sigpac")),
        str(fila.get("agregado_sigpac")),
        str(fila.get("zona_sigpac")),
        str(fila.get("poligono")),
        str(fila.get("parcela")),
        str(fila.get("recinto")),
    )


def _validar_filas(ctx):

    filas, orden_parcelas = cuadernopro_pdf.obtener_parcelas_unicas_para_cuaderno(
        ctx["campana_actual_id"]
    )

    if len(filas) != 3:

        raise AssertionError(f"Se esperaban 3 parcelas unicas y hay {len(filas)}")

    claves_sigpac = [_clave_sigpac(fila) for fila in filas]

    if len(set(claves_sigpac)) != len(claves_sigpac):

        raise AssertionError(f"Hay claves SIGPAC repetidas: {claves_sigpac!r}")

    if sum(cuadernopro_pdf._numero(fila.get("superficie_sigpac")) for fila in filas) != 9.75:

        raise AssertionError("La superficie SIGPAC no suma una sola vez")

    if sum(cuadernopro_pdf._numero(fila.get("superficie_cultivada")) for fila in filas) != 9.75:

        raise AssertionError("La superficie cultivada no suma una sola vez")

    por_id = _por_id(filas)
    duplicada = por_id[ctx["parcela_duplicada_id"]]

    if duplicada["sistema"] != "SECANO":

        raise AssertionError(
            f"Sistema duplicado inesperado: {duplicada['sistema']!r}"
        )

    if "SECANO / SECANO" in duplicada["sistema"]:

        raise AssertionError("El sistema se ha repetido como SECANO / SECANO")

    if cuadernopro_pdf._numero(duplicada["superficie_cultivada"]) != 4.5:

        raise AssertionError("La parcela duplicada cuenta superficie mas de una vez")

    if duplicada["especie"] != "ALMENDRO":

        raise AssertionError(
            f"No se prioriza la campana actual: {duplicada['especie']!r}"
        )

    fallback = por_id[ctx["parcela_fallback_id"]]

    if fallback["sistema"] != "SECANO TRADICIONAL":

        raise AssertionError(
            f"No se aplica fallback de explotacion: {fallback['sistema']!r}"
        )

    doble_sistema = por_id[ctx["parcela_doble_sistema_id"]]

    if doble_sistema["sistema"] != "SECANO / REGADÍO":

        raise AssertionError(
            f"No se agrupan sistemas unicos: {doble_sistema['sistema']!r}"
        )

    if orden_parcelas[ctx["parcela_duplicada_id"]] != 1:

        raise AssertionError(f"Orden SIGPAC inesperado: {orden_parcelas!r}")

    return filas


def _validar_pdf(campana_id):

    ruta_pdf = Path(cuadernopro_pdf.generar_cuadernopro_pdf(campana_id))

    if not ruta_pdf.exists():

        raise AssertionError(f"No se genero el PDF: {ruta_pdf}")

    if ruta_pdf.stat().st_size <= 0:

        raise AssertionError(f"PDF vacio: {ruta_pdf}")

    return ruta_pdf


def main():

    _preparar_entorno()
    ctx = _insertar_datos()
    filas = _validar_filas(ctx)
    ruta_pdf = _validar_pdf(ctx["campana_actual_id"])

    print("PDF parcelas unicas v8.4.4: OK")
    print(f"Parcelas unicas: {len(filas)}")
    print(f"PDF generado: {ruta_pdf}")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
