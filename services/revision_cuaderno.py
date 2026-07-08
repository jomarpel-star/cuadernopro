from datetime import datetime, timedelta
import sqlite3

from core.db import conectar
from core.paths import BACKUPS_DIR


def _item(seccion, nivel, mensaje, detalle=""):

    return {
        "seccion": seccion,
        "nivel": nivel,
        "mensaje": mensaje,
        "detalle": detalle,
    }


def _texto(valor):

    if valor is None:

        return ""

    return str(valor).strip()


def _tabla_existe(conn, tabla):

    try:

        fila = conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table'
            AND name=?
            """,
            (tabla,)
        ).fetchone()

    except sqlite3.Error:

        return False

    return fila is not None


def _columnas(conn, tabla):

    if not _tabla_existe(conn, tabla):

        return set()

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _tiene_columnas(conn, tabla, columnas):

    existentes = _columnas(conn, tabla)
    return all(columna in existentes for columna in columnas)


def _scalar(conn, sql, params=(), defecto=0):

    try:

        fila = conn.execute(sql, params).fetchone()

    except sqlite3.Error:

        return defecto

    if fila is None:

        return defecto

    valor = fila[0]
    return defecto if valor is None else valor


def _contar(conn, tabla, where="", params=(), columnas=()):

    if not _tabla_existe(conn, tabla):

        return 0

    if columnas and not _tiene_columnas(conn, tabla, columnas):

        return 0

    sql = f'SELECT COUNT(*) FROM "{tabla}"'

    if where:

        sql += f" WHERE {where}"

    return int(_scalar(conn, sql, params, 0) or 0)


def _sumar(conn, tabla, columna, where="", params=(), columnas=()):

    columnas_necesarias = set(columnas)
    columnas_necesarias.add(columna)

    if not _tabla_existe(conn, tabla):

        return 0.0

    if not _tiene_columnas(conn, tabla, columnas_necesarias):

        return 0.0

    sql = f'SELECT COALESCE(SUM("{columna}"),0) FROM "{tabla}"'

    if where:

        sql += f" WHERE {where}"

    return float(_scalar(conn, sql, params, 0.0) or 0.0)


def _primera_fila(conn, tabla, where="", params=()):

    if not _tabla_existe(conn, tabla):

        return None

    sql = f'SELECT * FROM "{tabla}"'

    if where:

        sql += f" WHERE {where}"

    sql += " ORDER BY id LIMIT 1"

    try:

        conn.row_factory = sqlite3.Row
        fila = conn.execute(sql, params).fetchone()

    except sqlite3.Error:

        return None

    finally:

        conn.row_factory = None

    return dict(fila) if fila is not None else None


def _campana(conn, campana_id):

    if campana_id is None or not _tabla_existe(conn, "campanas"):

        return None

    if not _tiene_columnas(conn, "campanas", ["id"]):

        return None

    try:

        conn.row_factory = sqlite3.Row
        fila = conn.execute(
            """
            SELECT *
            FROM campanas
            WHERE id=?
            """,
            (int(campana_id),)
        ).fetchone()

    except sqlite3.Error:

        return None

    finally:

        conn.row_factory = None

    return dict(fila) if fila is not None else None


def _tabla_fertilizacion(conn):

    if _tabla_existe(conn, "fertilizaciones"):

        return "fertilizaciones"

    if _tabla_existe(conn, "fertilizacion"):

        return "fertilizacion"

    return None


def _contar_por_campana(conn, tabla, campana_id):

    if not tabla:

        return 0

    return _contar(
        conn,
        tabla,
        '"campana_id"=?',
        (int(campana_id),),
        columnas=["campana_id"]
    )


def _contar_cultivos_sin_parcela(conn):

    if not _tabla_existe(conn, "cultivos"):

        return 0

    if not _tiene_columnas(conn, "cultivos", ["parcela_id"]):

        return 0

    if not _tabla_existe(conn, "parcelas"):

        return _contar(conn, "cultivos")

    return int(_scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM cultivos
        LEFT JOIN parcelas
        ON parcelas.id = cultivos.parcela_id
        WHERE cultivos.parcela_id IS NULL
        OR parcelas.id IS NULL
        """,
        defecto=0
    ) or 0)


def _contar_tratamientos_sin_producto(conn, campana_id):

    if not _tabla_existe(conn, "tratamientos"):

        return 0

    if not _tiene_columnas(conn, "tratamientos", ["campana_id", "producto_id"]):

        return 0

    if not _tabla_existe(conn, "productos_fito"):

        return _contar(
            conn,
            "tratamientos",
            '"campana_id"=?',
            (int(campana_id),),
            columnas=["campana_id"]
        )

    return int(_scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM tratamientos
        LEFT JOIN productos_fito
        ON productos_fito.id = tratamientos.producto_id
        WHERE tratamientos.campana_id=?
        AND (
            tratamientos.producto_id IS NULL
            OR productos_fito.id IS NULL
        )
        """,
        (int(campana_id),),
        0
    ) or 0)


def _contar_tratamientos_sin_fechas(conn, campana_id):

    return _contar(
        conn,
        "tratamientos",
        """
        "campana_id"=?
        AND (
            NULLIF(TRIM(COALESCE("fecha_inicio",'')),'') IS NULL
            OR NULLIF(TRIM(COALESCE("fecha_fin",'')),'') IS NULL
        )
        """,
        (int(campana_id),),
        columnas=["campana_id", "fecha_inicio", "fecha_fin"]
    )


def _contar_tratamientos_fechas_invertidas(conn, campana_id):

    return _contar(
        conn,
        "tratamientos",
        """
        "campana_id"=?
        AND NULLIF(TRIM(COALESCE("fecha_inicio",'')),'') IS NOT NULL
        AND NULLIF(TRIM(COALESCE("fecha_fin",'')),'') IS NOT NULL
        AND date("fecha_inicio") > date("fecha_fin")
        """,
        (int(campana_id),),
        columnas=["campana_id", "fecha_inicio", "fecha_fin"]
    )


def _contar_tratamientos_sin_parcelas(conn, campana_id):

    if not _tabla_existe(conn, "tratamientos"):

        return 0

    if not _tiene_columnas(conn, "tratamientos", ["id", "campana_id"]):

        return 0

    if not _tabla_existe(conn, "tratamiento_parcelas"):

        return _contar(
            conn,
            "tratamientos",
            '"campana_id"=?',
            (int(campana_id),),
            columnas=["campana_id"]
        )

    return int(_scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM tratamientos
        WHERE tratamientos.campana_id=?
        AND NOT EXISTS (
            SELECT 1
            FROM tratamiento_parcelas
            WHERE tratamiento_parcelas.tratamiento_id = tratamientos.id
        )
        """,
        (int(campana_id),),
        0
    ) or 0)


def _contar_tratamientos_sin_superficie(conn, campana_id):

    return _contar(
        conn,
        "tratamientos",
        """
        "campana_id"=?
        AND (
            "superficie_tratada" IS NULL
            OR COALESCE("superficie_tratada",0) <= 0
        )
        """,
        (int(campana_id),),
        columnas=["campana_id", "superficie_tratada"]
    )


def _contar_fuera_periodo(conn, tabla, campana_id, fecha_inicio, fecha_fin, campos):

    if not _tabla_existe(conn, tabla):

        return 0

    columnas = _columnas(conn, tabla)

    if "campana_id" not in columnas:

        return 0

    campos_disponibles = [
        campo
        for campo in campos
        if campo in columnas
    ]

    if not campos_disponibles:

        return 0

    condiciones = []
    params = [int(campana_id)]

    for campo in campos_disponibles:

        valor_fecha = (
            f"date(NULLIF(TRIM(COALESCE(\"{campo}\",'')),''))"
        )
        condiciones.append(
            f"({valor_fecha} < date(?) OR {valor_fecha} > date(?))"
        )
        params.extend([fecha_inicio, fecha_fin])

    columna_id = '"id"' if "id" in columnas else "*"
    distinct = "DISTINCT " if "id" in columnas else ""
    sql = (
        f'SELECT COUNT({distinct}{columna_id}) '
        f'FROM "{tabla}" '
        'WHERE "campana_id"=? '
        f'AND ({" OR ".join(condiciones)})'
    )
    return int(_scalar(conn, sql, tuple(params), 0) or 0)


def _ultimo_backup_reciente():

    try:

        if not BACKUPS_DIR.exists():

            return None

        archivos = [
            ruta
            for patron in ("*.db", "*.zip")
            for ruta in BACKUPS_DIR.glob(patron)
            if ruta.is_file()
        ]

    except OSError:

        return None

    if not archivos:

        return None

    ultimo = max(archivos, key=lambda ruta: ruta.stat().st_mtime)
    fecha = datetime.fromtimestamp(ultimo.stat().st_mtime)

    if fecha < datetime.now() - timedelta(days=7):

        return None

    return ultimo, fecha


def _resumen_base(conn, campana_id):

    tabla_fertilizacion = _tabla_fertilizacion(conn)
    ingresos = 0.0
    gastos = 0.0

    if _tiene_columnas(
        conn,
        "movimientos_economicos",
        ["campana_id", "tipo", "total"]
    ):

        ingresos = float(_scalar(
            conn,
            """
            SELECT COALESCE(SUM(total),0)
            FROM movimientos_economicos
            WHERE campana_id=?
            AND tipo='Ingreso'
            """,
            (int(campana_id),),
            0.0
        ) or 0.0)
        gastos = float(_scalar(
            conn,
            """
            SELECT COALESCE(SUM(total),0)
            FROM movimientos_economicos
            WHERE campana_id=?
            AND tipo='Gasto'
            """,
            (int(campana_id),),
            0.0
        ) or 0.0)

    return {
        "parcelas": _contar(conn, "parcelas"),
        "cultivos": _contar(conn, "cultivos"),
        "tratamientos": _contar_por_campana(conn, "tratamientos", campana_id),
        "fertilizaciones": _contar_por_campana(
            conn,
            tabla_fertilizacion,
            campana_id
        ),
        "practicas_culturales": _contar_por_campana(
            conn,
            "practicas_culturales",
            campana_id
        ),
        "cosechas": _contar_por_campana(conn, "cosecha", campana_id),
        "analisis_fitosanitarios": _contar_por_campana(
            conn,
            "analisis_fitosanitarios",
            campana_id
        ),
        "movimientos_economicos": _contar_por_campana(
            conn,
            "movimientos_economicos",
            campana_id
        ),
        "superficie_sigpac_total": _sumar(
            conn,
            "parcelas",
            "superficie_sigpac"
        ),
        "ingresos": ingresos,
        "gastos": gastos,
    }


def revisar_cuaderno(campana_id):

    resultado = {
        "errores": [],
        "avisos": [],
        "correctos": [],
        "resumen": {},
    }

    def error(seccion, mensaje, detalle=""):

        resultado["errores"].append(_item(seccion, "error", mensaje, detalle))

    def aviso(seccion, mensaje, detalle=""):

        resultado["avisos"].append(_item(seccion, "aviso", mensaje, detalle))

    def ok(seccion, mensaje, detalle=""):

        resultado["correctos"].append(_item(seccion, "ok", mensaje, detalle))

    if campana_id is None:

        error("Campaña", "No hay campaña seleccionada.")
        return resultado

    try:

        campana_id = int(campana_id)

    except (TypeError, ValueError):

        error("Campaña", "No hay campaña seleccionada.")
        return resultado

    try:

        conn = conectar()

    except Exception as exc:

        error(
            "Base de datos",
            "No se pudo abrir la base de datos para revisar el cuaderno.",
            str(exc)
        )
        return resultado

    try:

        campana = _campana(conn, campana_id)

        if not campana:

            error("Campaña", "No se encontró la campaña seleccionada.")
            return resultado

        resultado["resumen"] = _resumen_base(conn, campana_id)
        ok(
            "Campaña",
            "Campaña activa/seleccionada correcta.",
            _texto(campana.get("nombre"))
        )

        explotacion = _primera_fila(conn, "explotacion")

        if not explotacion:

            error("Explotación", "No hay datos de explotación.")

        else:

            titular = _texto(explotacion.get("titular"))
            nif = _texto(explotacion.get("nif"))

            if not titular:

                error("Explotación", "Falta titular de la explotación.")

            if not nif:

                error("Explotación", "Falta NIF de la explotación.")

            if titular and nif:

                ok("Explotación", "Explotación configurada.")

        parcelas = resultado["resumen"].get("parcelas", 0)
        cultivos = resultado["resumen"].get("cultivos", 0)
        tratamientos = resultado["resumen"].get("tratamientos", 0)

        if parcelas <= 0:

            error("Parcelas", "No hay parcelas registradas.")

        else:

            ok("Parcelas", "Parcelas registradas.", f"{parcelas} parcelas")

        if cultivos <= 0:

            error("Cultivos", "No hay cultivos registrados.")

        else:

            ok("Cultivos", "Cultivos registrados.", f"{cultivos} cultivos")

        cultivos_sin_parcela = _contar_cultivos_sin_parcela(conn)

        if cultivos_sin_parcela:

            error(
                "Cultivos",
                "Hay cultivos sin parcela asociada.",
                f"{cultivos_sin_parcela} cultivos"
            )

        if tratamientos <= 0:

            aviso("Tratamientos", "No hay tratamientos en la campaña.")

        else:

            ok(
                "Tratamientos",
                "Tratamientos registrados.",
                f"{tratamientos} tratamientos"
            )

        comprobaciones_tratamientos = [
            (
                _contar_tratamientos_sin_producto(conn, campana_id),
                "Hay tratamientos sin producto asociado.",
                "Tratamientos"
            ),
            (
                _contar_tratamientos_sin_fechas(conn, campana_id),
                "Hay tratamientos sin fecha de inicio o fecha de fin.",
                "Tratamientos"
            ),
            (
                _contar_tratamientos_fechas_invertidas(conn, campana_id),
                "Hay tratamientos con fecha de inicio posterior a la fecha de fin.",
                "Tratamientos"
            ),
            (
                _contar_tratamientos_sin_parcelas(conn, campana_id),
                "Hay tratamientos sin parcelas asociadas.",
                "Tratamientos"
            ),
            (
                _contar_tratamientos_sin_superficie(conn, campana_id),
                "Hay tratamientos sin superficie tratada.",
                "Tratamientos"
            ),
        ]

        for cantidad, mensaje, seccion in comprobaciones_tratamientos:

            if cantidad:

                error(seccion, mensaje, f"{cantidad} registros")

        asesores = _contar(
            conn,
            "personas",
            """
            LOWER(TRIM(COALESCE("rol",'')))='asesor'
            OR NULLIF(TRIM(COALESCE("numero_asesor",'')),'') IS NOT NULL
            """,
            columnas=["rol", "numero_asesor"]
        )

        if asesores <= 0:

            aviso("Asesoramiento", "No hay asesor registrado.")

        equipos = _contar(conn, "equipos_aplicacion")

        if equipos <= 0:

            aviso(
                "Equipos",
                "No hay equipos de aplicación fitosanitaria registrados."
            )

        productos = _contar(conn, "productos_fito")

        if productos <= 0:

            aviso(
                "Productos fitosanitarios",
                "No hay productos fitosanitarios registrados."
            )

        else:

            sin_plazo = _contar(
                conn,
                "productos_fito",
                "NULLIF(TRIM(COALESCE(\"plazo_seguridad\",'')),'') IS NULL",
                columnas=["plazo_seguridad"]
            )
            sin_registro = _contar(
                conn,
                "productos_fito",
                "NULLIF(TRIM(COALESCE(\"registro\",'')),'') IS NULL",
                columnas=["registro"]
            )

            if sin_plazo:

                aviso(
                    "Productos fitosanitarios",
                    "Hay productos sin plazo de seguridad.",
                    f"{sin_plazo} productos"
                )

            if sin_registro:

                aviso(
                    "Productos fitosanitarios",
                    "Hay productos sin número de registro.",
                    f"{sin_registro} productos"
                )

        if resultado["resumen"].get("fertilizaciones", 0) <= 0:

            aviso("Fertilización", "No hay fertilización registrada.")

        if resultado["resumen"].get("cosechas", 0) <= 0:

            aviso("Cosecha", "No hay cosecha registrada.")

        if resultado["resumen"].get("movimientos_economicos", 0) <= 0:

            aviso("Economía", "No hay movimientos económicos.")

        if resultado["resumen"].get("analisis_fitosanitarios", 0) <= 0:

            aviso(
                "Análisis fitosanitarios",
                "No hay análisis fitosanitarios registrados."
            )

        tratamientos_sin_eficacia = _contar(
            conn,
            "tratamientos",
            """
            campana_id=?
            AND NULLIF(TRIM(COALESCE("eficacia",'')),'') IS NULL
            """,
            (int(campana_id),),
            columnas=["campana_id", "eficacia"]
        )

        if tratamientos_sin_eficacia:

            aviso(
                "Tratamientos fitosanitarios",
                "Hay tratamientos fitosanitarios sin eficacia registrada.",
                f"{tratamientos_sin_eficacia} tratamientos"
            )

        parcelas_sin_superficie = _contar(
            conn,
            "parcelas",
            """
            "superficie_sigpac" IS NULL
            OR COALESCE("superficie_sigpac",0) <= 0
            """,
            columnas=["superficie_sigpac"]
        )

        if parcelas_sin_superficie:

            aviso(
                "Parcelas",
                "Hay parcelas sin superficie SIGPAC.",
                f"{parcelas_sin_superficie} parcelas"
            )

        parcelas_sigpac_error = _contar(
            conn,
            "parcelas",
            """
            LOWER(TRIM(COALESCE("sigpac_geojson_estado",''))) LIKE '%pendiente%'
            OR LOWER(TRIM(COALESCE("sigpac_geojson_estado",''))) LIKE '%error%'
            OR NULLIF(TRIM(COALESCE("sigpac_geojson_error",'')),'') IS NOT NULL
            """,
            columnas=["sigpac_geojson_estado", "sigpac_geojson_error"]
        )

        if parcelas_sigpac_error:

            aviso(
                "SIGPAC",
                "Hay parcelas con geometría SIGPAC pendiente o error.",
                f"{parcelas_sigpac_error} parcelas"
            )

        inicio = _texto(campana.get("fecha_inicio"))
        fin = _texto(campana.get("fecha_fin"))

        if inicio and fin:

            fuera_periodo = 0

            for tabla, campos in [
                ("tratamientos", ["fecha_inicio", "fecha_fin", "fecha"]),
                ("fertilizaciones", ["fecha"]),
                ("practicas_culturales", ["fecha"]),
                ("cosecha", ["fecha"]),
                ("analisis_fitosanitarios", ["fecha"]),
                ("movimientos_economicos", ["fecha"]),
            ]:

                fuera_periodo += _contar_fuera_periodo(
                    conn,
                    tabla,
                    campana_id,
                    inicio,
                    fin,
                    campos
                )

            if fuera_periodo:

                aviso(
                    "Fechas",
                    "Hay registros fuera del periodo oficial de campaña.",
                    f"{fuera_periodo} registros"
                )

        backup = _ultimo_backup_reciente()

        if backup:

            ruta, fecha = backup
            ok(
                "Backup",
                "Backup reciente detectado.",
                f"{ruta.name} · {fecha.strftime('%d/%m/%Y %H:%M')}"
            )

        ok(
            "PDF",
            "PDF puede generarse.",
            "La generación no se bloquea salvo que no haya campaña."
        )

    finally:

        conn.close()

    return resultado
