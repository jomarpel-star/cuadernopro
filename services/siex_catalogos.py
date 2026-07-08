from datetime import date, datetime
from io import BytesIO
import json
from pathlib import Path
import re
import time
import unicodedata
import warnings
from zipfile import ZipFile

import pandas as pd

from core.db import conectar, crear_tablas


CATALOGOS_CONFIG = {
    "cultivo": {
        "nombre": "Cultivo",
        "patrones": [["cultivo"]],
        "descripcion": ["Cultivo"],
    },
    "variedad_especie_tipo": {
        "nombre": "Variedad / Especie / Tipo",
        "patrones": [["variedad", "especie", "tipo"]],
        "codigo": ["Código cultivo"],
        "codigo_secundario": ["Código Variedad/ Especie/ Tipo"],
        "descripcion": ["Cultivo"],
        "descripcion_secundaria": ["Variedad/ Especie/ Tipo"],
    },
    "actividad_agraria": {
        "nombre": "Actividad agraria",
        "patrones": [["actividad", "agraria"]],
        "descripcion": ["Actividad agraria"],
    },
    "actividad_cubierta": {
        "nombre": "Actividad sobre la cubierta",
        "patrones": [["actividad", "cubierta"]],
        "descripcion": ["Actividad sobre la cubierta"],
    },
    "aprovechamiento": {
        "nombre": "Aprovechamiento",
        "patrones": [["aprovechamiento"]],
        "descripcion": ["Aprovechamiento"],
        "descripcion_secundaria": ["Descripción"],
    },
    "certificacion_ecologica": {
        "nombre": "Certificación producción ecológica",
        "patrones": [["certificacion", "produccion", "ecologica"]],
        "descripcion": ["Descripción"],
    },
    "destino_cultivo": {
        "nombre": "Destino del cultivo",
        "patrones": [["destino", "cultivo"]],
        "descripcion": ["Destino del cultivo"],
    },
    "edificaciones_instalaciones": {
        "nombre": "Edificaciones e instalaciones",
        "patrones": [["edificaciones"], ["instalaciones"]],
        "codigo_secundario": ["Código"],
        "descripcion": ["Edificación e instalación"],
        "descripcion_secundaria": ["Tipología"],
    },
    "material_vegetal_reproduccion": {
        "nombre": "Material vegetal de reproducción",
        "patrones": [["material", "vegetal", "reproduccion"]],
        "codigo_secundario": ["Código del tipo"],
        "descripcion": ["Detalle del tipo"],
        "descripcion_secundaria": [
            "Tipo de material vegetal de reproducción",
        ],
    },
    "regimen_tenencia": {
        "nombre": "Régimen de tenencia",
        "patrones": [["regimen", "tenencia"]],
        "descripcion": ["Régimen de tenencia"],
    },
    "regimenes_calidad": {
        "nombre": "Regímenes de calidad",
        "patrones": [["regimenes", "calidad"]],
        "codigo": ["ID_TIPO_IG"],
        "codigo_secundario": ["ID_IIGG"],
        "descripcion": ["IIGG nombre_oficial"],
        "descripcion_secundaria": ["Tipo_IIGG", "Categoría"],
    },
    "sistema_conduccion": {
        "nombre": "Sistema de conducción",
        "patrones": [["sistema", "conduccion"]],
        "descripcion": ["Sistema de conducción"],
        "descripcion_secundaria": ["Definición"],
    },
    "sistema_cultivo": {
        "nombre": "Sistema de cultivo",
        "patrones": [["sistema", "cultivo"]],
        "descripcion": ["Sistema de cultivo"],
        "descripcion_secundaria": ["Observaciones"],
    },
    "sistema_explotacion": {
        "nombre": "Sistema de explotación",
        "patrones": [["sistema", "explotacion"]],
        "descripcion": ["Sistema de explotación"],
    },
    "senp": {
        "nombre": "Superficies y elementos no productivos (SENP)",
        "patrones": [["superficies", "elementos", "productivos"], ["senp"]],
        "codigo_secundario": ["Código"],
        "descripcion": ["Tipo"],
    },
    "tipo_cobertura_suelo": {
        "nombre": "Tipo de cobertura del suelo",
        "patrones": [["tipo", "cobertura", "suelo"]],
        "descripcion": ["Tipo de cobertura del suelo"],
    },
    "tipo_entidad_asociacion": {
        "nombre": "Tipo de entidad - asociación",
        "patrones": [["tipo", "entidad"], ["tipo", "asociacion"]],
        "descripcion": ["Tipo de asociación"],
    },
    "tipo_titular": {
        "nombre": "Tipo de titular",
        "patrones": [["tipo", "titular"]],
        "descripcion": ["Forma jurídica"],
    },
}

ORDEN_CATALOGOS = [
    "variedad_especie_tipo",
    "actividad_agraria",
    "actividad_cubierta",
    "aprovechamiento",
    "certificacion_ecologica",
    "destino_cultivo",
    "edificaciones_instalaciones",
    "material_vegetal_reproduccion",
    "regimen_tenencia",
    "regimenes_calidad",
    "sistema_conduccion",
    "sistema_cultivo",
    "sistema_explotacion",
    "senp",
    "tipo_cobertura_suelo",
    "tipo_entidad_asociacion",
    "tipo_titular",
    "cultivo",
]

CATALOGOS_OBLIGATORIOS_V8 = (
    "cultivo",
)

CATALOGOS_RECOMENDADOS_V8 = tuple(
    codigo
    for codigo in ORDEN_CATALOGOS
    if codigo not in CATALOGOS_OBLIGATORIOS_V8
)

CODIGOS_CANDIDATOS = [
    "Código SIEX",
    "Código",
    "Código cultivo",
    "ID_TIPO_IG",
    "Código del tipo",
]

DESCRIPCIONES_CANDIDATAS = [
    "Cultivo",
    "Actividad agraria",
    "Actividad sobre la cubierta",
    "Aprovechamiento",
    "Descripción",
    "Destino del cultivo",
    "Edificación e instalación",
    "Detalle del tipo",
    "Tipo de material vegetal de reproducción",
    "Régimen de tenencia",
    "IIGG nombre_oficial",
    "Sistema de conducción",
    "Sistema de cultivo",
    "Sistema de explotación",
    "Tipo",
    "Tipo de cobertura del suelo",
    "Tipo de asociación",
    "Forma jurídica",
]


def _texto(valor):

    if valor is None:

        return ""

    try:

        if pd.isna(valor):

            return ""

    except (TypeError, ValueError):

        pass

    if isinstance(valor, pd.Timestamp):

        return valor.date().isoformat()

    if isinstance(valor, (datetime, date)):

        return valor.isoformat()

    return str(valor).strip()


def _normalizar_texto(texto):

    texto = unicodedata.normalize("NFKD", _texto(texto))
    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _mapa_columnas(fila):

    return {
        _normalizar_texto(columna): columna
        for columna in fila.keys()
    }


def _obtener_valor(fila, columnas):

    mapa = _mapa_columnas(fila)

    for columna in columnas:

        columna_real = mapa.get(_normalizar_texto(columna))

        if columna_real is not None:

            return _texto(fila.get(columna_real))

    return ""


def _serializar_fila(fila):

    datos = {}

    for columna, valor in fila.items():

        datos[str(columna)] = _texto(valor)

    return datos


def _codigo_catalogo_por_nombre(nombre_archivo):

    nombre_normalizado = _normalizar_texto(Path(nombre_archivo).stem)

    for codigo in ORDEN_CATALOGOS:

        config = CATALOGOS_CONFIG[codigo]

        for patron in config["patrones"]:

            if all(token in nombre_normalizado for token in patron):

                return codigo

    return nombre_normalizado.replace(" ", "_") or "catalogo_siex"


def _nombre_catalogo(codigo_catalogo, nombre_archivo):

    config = CATALOGOS_CONFIG.get(codigo_catalogo, {})
    return config.get("nombre") or Path(nombre_archivo).stem


def _leer_excel_desde_origen(archivo_excel):

    if isinstance(archivo_excel, (bytes, bytearray)):

        origen = BytesIO(archivo_excel)

    else:

        origen = archivo_excel

    with warnings.catch_warnings():

        warnings.filterwarnings(
            "ignore",
            message="Workbook contains no default style.*",
            category=UserWarning,
        )
        excel = pd.ExcelFile(origen, engine="openpyxl")
        dataframe = pd.read_excel(
            excel,
            sheet_name=excel.sheet_names[0],
            dtype=object,
        )
    dataframe = dataframe.dropna(how="all")
    dataframe.columns = [str(columna).strip() for columna in dataframe.columns]
    return dataframe


def _abrir_zip(origen_zip):

    if isinstance(origen_zip, (bytes, bytearray)):

        return ZipFile(BytesIO(origen_zip))

    if hasattr(origen_zip, "getvalue"):

        return ZipFile(BytesIO(origen_zip.getvalue()))

    if hasattr(origen_zip, "read") and not isinstance(origen_zip, (str, Path)):

        return ZipFile(BytesIO(origen_zip.read()))

    return ZipFile(Path(origen_zip).expanduser())


def _nombre_zip(origen_zip, nombre_archivo=None):

    if nombre_archivo:

        return str(nombre_archivo)

    nombre = getattr(origen_zip, "name", "")

    if nombre:

        return str(nombre)

    if isinstance(origen_zip, (str, Path)):

        return str(Path(origen_zip).expanduser())

    return "catalogos_siex.zip"


def listar_archivos_catalogos_zip(origen_zip):

    archivos = []

    with _abrir_zip(origen_zip) as zip_file:

        for info in zip_file.infolist():

            if info.is_dir() or info.filename.startswith("__MACOSX/"):

                continue

            if not info.filename.lower().endswith((".xlsx", ".xlsm", ".xls")):

                continue

            codigo = _codigo_catalogo_por_nombre(info.filename)
            archivos.append({
                "archivo": info.filename,
                "codigo_catalogo": codigo,
                "nombre_catalogo": _nombre_catalogo(codigo, info.filename),
                "tamano_bytes": info.file_size,
            })

    return archivos


def normalizar_item_catalogo(nombre_catalogo, fila):

    codigo_catalogo = _codigo_catalogo_por_nombre(nombre_catalogo)
    config = CATALOGOS_CONFIG.get(codigo_catalogo, {})
    codigo = _obtener_valor(
        fila,
        config.get("codigo", []) + CODIGOS_CANDIDATOS,
    )
    codigo_secundario = _obtener_valor(
        fila,
        config.get("codigo_secundario", []),
    )
    descripcion = _obtener_valor(
        fila,
        config.get("descripcion", []) + DESCRIPCIONES_CANDIDATAS,
    )
    descripcion_secundaria = _obtener_valor(
        fila,
        config.get("descripcion_secundaria", []),
    )
    fecha_alta = _obtener_valor(fila, ["Fecha de alta"])
    fecha_baja = _obtener_valor(fila, ["Fecha de baja"])

    return {
        "codigo": codigo,
        "codigo_secundario": codigo_secundario,
        "descripcion": descripcion,
        "descripcion_secundaria": descripcion_secundaria,
        "fecha_alta": fecha_alta,
        "fecha_baja": fecha_baja,
        "activo": 0 if fecha_baja else 1,
        "datos_json": json.dumps(
            _serializar_fila(fila),
            ensure_ascii=False,
            sort_keys=True,
        ),
    }


def _reemplazar_catalogo(
    conn,
    codigo_catalogo,
    nombre_catalogo,
    archivo_origen,
    version,
    filas,
):

    ahora = datetime.now().isoformat(timespec="seconds")
    catalogos_previos = conn.execute(
        "SELECT id FROM siex_catalogos WHERE codigo_catalogo=?",
        (codigo_catalogo,),
    ).fetchall()
    ids_previos = [fila[0] for fila in catalogos_previos]

    for catalogo_id in ids_previos:

        conn.execute(
            "DELETE FROM siex_catalogos_items WHERE catalogo_id=?",
            (catalogo_id,),
        )

    conn.execute(
        "DELETE FROM siex_catalogos WHERE codigo_catalogo=?",
        (codigo_catalogo,),
    )
    cursor = conn.execute(
        """
        INSERT INTO siex_catalogos
        (codigo_catalogo,nombre_catalogo,archivo_origen,version,
         fecha_importacion,observaciones)
        VALUES (?,?,?,?,?,?)
        """,
        (
            codigo_catalogo,
            nombre_catalogo,
            archivo_origen,
            version,
            ahora,
            "Importado desde catálogo Excel SIEX.",
        ),
    )
    catalogo_id = cursor.lastrowid

    for item in filas:

        conn.execute(
            """
            INSERT INTO siex_catalogos_items
            (catalogo_id,codigo,codigo_secundario,descripcion,
             descripcion_secundaria,fecha_alta,fecha_baja,activo,datos_json,
             created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                catalogo_id,
                item["codigo"],
                item["codigo_secundario"],
                item["descripcion"],
                item["descripcion_secundaria"],
                item["fecha_alta"],
                item["fecha_baja"],
                item["activo"],
                item["datos_json"],
                ahora,
                ahora,
            ),
        )

    return catalogo_id


def importar_catalogo_excel(
    nombre_catalogo,
    archivo_excel,
    archivo_origen=None,
    version=None,
    conn=None,
    ruta_db=None,
):

    codigo_catalogo = _codigo_catalogo_por_nombre(nombre_catalogo)
    nombre_visible = _nombre_catalogo(codigo_catalogo, nombre_catalogo)
    dataframe = _leer_excel_desde_origen(archivo_excel)
    filas = []

    for _, fila in dataframe.iterrows():

        item = normalizar_item_catalogo(nombre_catalogo, fila.to_dict())

        if not item["codigo"] and not item["descripcion"]:

            continue

        filas.append(item)

    cerrar_conn = conn is None

    if conn is None:

        crear_tablas(ruta_db)
        conn = conectar(ruta_db)

    try:

        with conn:

            catalogo_id = _reemplazar_catalogo(
                conn,
                codigo_catalogo,
                nombre_visible,
                archivo_origen or str(nombre_catalogo),
                version or "",
                filas,
            )

    finally:

        if cerrar_conn:

            conn.close()

    return {
        "catalogo_id": catalogo_id,
        "codigo_catalogo": codigo_catalogo,
        "nombre_catalogo": nombre_visible,
        "archivo_origen": archivo_origen or str(nombre_catalogo),
        "items": len(filas),
        "columnas": list(dataframe.columns),
    }


def importar_catalogos_siex_desde_zip(
    origen_zip,
    conn=None,
    ruta_db=None,
    nombre_archivo=None,
):

    inicio = time.monotonic()
    nombre_zip = _nombre_zip(origen_zip, nombre_archivo=nombre_archivo)
    resumen = {
        "ruta_zip": nombre_zip,
        "catalogos": [],
        "errores": [],
        "ignorados": [],
        "total_catalogos": 0,
        "total_items": 0,
        "duracion_segundos": 0.0,
    }
    cerrar_conn = conn is None

    if conn is None:

        crear_tablas(ruta_db)
        conn = conectar(ruta_db)

    try:

        with _abrir_zip(origen_zip) as zip_file:

            for info in zip_file.infolist():

                if info.is_dir() or info.filename.startswith("__MACOSX/"):

                    continue

                if not info.filename.lower().endswith(
                    (".xlsx", ".xlsm", ".xls")
                ):

                    resumen["ignorados"].append({
                        "archivo": info.filename,
                        "motivo": "No es un Excel de catálogo.",
                    })
                    continue

                try:

                    resultado = importar_catalogo_excel(
                        info.filename,
                        zip_file.read(info),
                        archivo_origen=info.filename,
                        version=Path(nombre_zip).stem,
                        conn=conn,
                    )
                    resumen["catalogos"].append(resultado)

                except Exception as exc:

                    resumen["errores"].append({
                        "archivo": info.filename,
                        "error": str(exc),
                    })

    finally:

        if cerrar_conn:

            conn.close()

    resumen["total_catalogos"] = len(resumen["catalogos"])
    resumen["total_items"] = sum(
        int(catalogo.get("items") or 0)
        for catalogo in resumen["catalogos"]
    )
    resumen["duracion_segundos"] = round(time.monotonic() - inicio, 3)

    return resumen


def resumen_catalogos_siex(conn=None, ruta_db=None):

    cerrar_conn = conn is None

    if conn is None:

        crear_tablas(ruta_db)
        conn = conectar(ruta_db)

    try:

        fila = conn.execute(
            """
            SELECT
                COUNT(DISTINCT c.id),
                COUNT(i.id),
                COALESCE(SUM(CASE WHEN i.activo=1 THEN 1 ELSE 0 END), 0),
                MAX(c.fecha_importacion)
            FROM siex_catalogos c
            LEFT JOIN siex_catalogos_items i ON i.catalogo_id=c.id
            """
        ).fetchone()
        principales = conn.execute(
            """
            SELECT
                c.codigo_catalogo,
                c.nombre_catalogo,
                COUNT(i.id) AS total_items
            FROM siex_catalogos c
            LEFT JOIN siex_catalogos_items i ON i.catalogo_id=c.id
            GROUP BY c.id
            ORDER BY total_items DESC,c.nombre_catalogo
            LIMIT 10
            """
        ).fetchall()

        return {
            "total_catalogos": int(fila[0] or 0),
            "total_items": int(fila[1] or 0),
            "items_activos": int(fila[2] or 0),
            "ultima_importacion": fila[3] or "",
            "catalogos_principales": [
                {
                    "codigo_catalogo": item[0],
                    "nombre_catalogo": item[1],
                    "total_items": int(item[2] or 0),
                }
                for item in principales
            ],
        }

    finally:

        if cerrar_conn:

            conn.close()


def diagnosticar_catalogos_siex(conn=None, ruta_db=None):

    cerrar_conn = conn is None

    if conn is None:

        crear_tablas(ruta_db)
        conn = conectar(ruta_db)

    try:

        resumen = resumen_catalogos_siex(conn=conn)
        presentes = {
            fila[0]
            for fila in conn.execute(
                "SELECT codigo_catalogo FROM siex_catalogos"
            ).fetchall()
        }
        faltan_obligatorios = [
            codigo
            for codigo in CATALOGOS_OBLIGATORIOS_V8
            if codigo not in presentes
        ]
        faltan_recomendados = [
            codigo
            for codigo in CATALOGOS_RECOMENDADOS_V8
            if codigo not in presentes
        ]
        errores = []
        advertencias = []

        if resumen["total_catalogos"] == 0:

            errores.append(
                "No hay catálogos SIEX cargados. Importa el ZIP oficial."
            )

        for codigo in faltan_obligatorios:

            nombre = CATALOGOS_CONFIG.get(codigo, {}).get("nombre", codigo)
            errores.append(f"Falta catálogo obligatorio: {nombre}.")

        if faltan_recomendados:

            nombres = [
                CATALOGOS_CONFIG.get(codigo, {}).get("nombre", codigo)
                for codigo in faltan_recomendados
            ]
            advertencias.append(
                "Catálogos recomendados no cargados: "
                + ", ".join(nombres)
                + "."
            )

        if errores:

            estado = "ERROR"

        elif advertencias:

            estado = "ADVERTENCIAS"

        else:

            estado = "OK"

        return {
            "ok": not errores,
            "estado": estado,
            "errores": errores,
            "advertencias": advertencias,
            "catalogos_presentes": sorted(presentes),
            "catalogos_obligatorios_faltantes": faltan_obligatorios,
            "catalogos_recomendados_faltantes": faltan_recomendados,
            "resumen": resumen,
        }

    finally:

        if cerrar_conn:

            conn.close()


def listar_catalogos(conn=None, ruta_db=None):

    cerrar_conn = conn is None

    if conn is None:

        crear_tablas(ruta_db)
        conn = conectar(ruta_db)

    try:

        return pd.read_sql_query(
            """
            SELECT
                c.id,
                c.codigo_catalogo,
                c.nombre_catalogo,
                c.archivo_origen,
                c.version,
                c.fecha_importacion,
                c.observaciones,
                COUNT(i.id) AS total_items,
                SUM(CASE WHEN i.activo=1 THEN 1 ELSE 0 END) AS items_activos
            FROM siex_catalogos c
            LEFT JOIN siex_catalogos_items i ON i.catalogo_id=c.id
            GROUP BY c.id
            ORDER BY c.nombre_catalogo
            """,
            conn,
        )

    finally:

        if cerrar_conn:

            conn.close()


def buscar_items_catalogo(
    codigo_catalogo,
    texto="",
    solo_activos=True,
    conn=None,
    ruta_db=None,
):

    filtros = ["c.codigo_catalogo=?"]
    params = [codigo_catalogo]

    if solo_activos:

        filtros.append("i.activo=1")

    if _texto(texto):

        filtros.append(
            """
            (
                i.codigo LIKE ?
                OR i.codigo_secundario LIKE ?
                OR i.descripcion LIKE ?
                OR i.descripcion_secundaria LIKE ?
            )
            """
        )
        patron = f"%{_texto(texto)}%"
        params.extend([patron, patron, patron, patron])

    cerrar_conn = conn is None

    if conn is None:

        crear_tablas(ruta_db)
        conn = conectar(ruta_db)

    try:

        return pd.read_sql_query(
            f"""
            SELECT
                i.id,
                c.codigo_catalogo,
                c.nombre_catalogo,
                i.codigo,
                i.codigo_secundario,
                i.descripcion,
                i.descripcion_secundaria,
                i.fecha_alta,
                i.fecha_baja,
                i.activo,
                i.datos_json
            FROM siex_catalogos_items i
            JOIN siex_catalogos c ON c.id=i.catalogo_id
            WHERE {' AND '.join(filtros)}
            ORDER BY i.descripcion,i.codigo
            LIMIT 1000
            """,
            conn,
            params=params,
        )

    finally:

        if cerrar_conn:

            conn.close()


def obtener_item_por_codigo(codigo_catalogo, codigo, conn=None, ruta_db=None):

    cerrar_conn = conn is None

    if conn is None:

        crear_tablas(ruta_db)
        conn = conectar(ruta_db)

    try:

        fila = conn.execute(
            """
            SELECT
                i.id,
                c.codigo_catalogo,
                c.nombre_catalogo,
                i.codigo,
                i.codigo_secundario,
                i.descripcion,
                i.descripcion_secundaria,
                i.fecha_alta,
                i.fecha_baja,
                i.activo,
                i.datos_json
            FROM siex_catalogos_items i
            JOIN siex_catalogos c ON c.id=i.catalogo_id
            WHERE c.codigo_catalogo=?
            AND (i.codigo=? OR i.codigo_secundario=?)
            ORDER BY i.activo DESC,i.id
            LIMIT 1
            """,
            (codigo_catalogo, _texto(codigo), _texto(codigo)),
        ).fetchone()

        if fila is None:

            return None

        columnas = [
            "id",
            "codigo_catalogo",
            "nombre_catalogo",
            "codigo",
            "codigo_secundario",
            "descripcion",
            "descripcion_secundaria",
            "fecha_alta",
            "fecha_baja",
            "activo",
            "datos_json",
        ]
        return dict(zip(columnas, fila))

    finally:

        if cerrar_conn:

            conn.close()
