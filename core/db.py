from datetime import datetime
import errno
import logging
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile

import pandas as pd

from core.paths import (
    BACKUPS_DIR,
    DB_PATH,
    DOCS_DIR,
    asegurar_directorio,
    asegurar_directorio_padre,
)


DB = str(DB_PATH)
DOCS = str(DOCS_DIR)
LOGGER = logging.getLogger(__name__)

TABLAS_ESQUEMA_MINIMO = {
    "campanas",
    "explotacion",
    "parcelas",
    "cultivos",
}


asegurar_directorio(DOCS_DIR)


# =====================================================
# BASE DE DATOS
# =====================================================

def obtener_ruta_db():
    ruta_db = asegurar_directorio_padre(DB_PATH)

    if ruta_db.exists() and ruta_db.is_dir():
        raise RuntimeError(
            "La ruta configurada para SQLite apunta a un directorio, no a "
            f"un fichero de base de datos: {ruta_db}"
        )

    return str(ruta_db)


def _resolver_ruta_db(ruta_db=None):

    if ruta_db is None:

        return Path(obtener_ruta_db())

    ruta = asegurar_directorio_padre(Path(ruta_db).expanduser())

    if ruta.exists() and ruta.is_dir():
        raise RuntimeError(
            "La ruta configurada para SQLite apunta a un directorio, no a "
            f"un fichero de base de datos: {ruta}"
        )

    return ruta


def conectar(ruta_db=None):
    conn = sqlite3.connect(str(_resolver_ruta_db(ruta_db)))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _tablas_usuario(conn):

    return {
        fila[0]
        for fila in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            """
        )
    }


def _base_nueva_o_vacia(ruta_db):

    ruta_db = Path(ruta_db)

    if not ruta_db.exists():

        return True

    if ruta_db.stat().st_size == 0:

        return True

    conn = sqlite3.connect(str(ruta_db))

    try:

        return not _tablas_usuario(conn)

    finally:

        conn.close()


def _base_es_v7(ruta_db):

    from core.schema_v7 import SCHEMA_VERSION

    ruta_db = Path(ruta_db)

    if not ruta_db.exists() or ruta_db.stat().st_size == 0:

        return False

    conn = sqlite3.connect(str(ruta_db))

    try:

        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        return user_version >= SCHEMA_VERSION and bool(_tablas_usuario(conn))

    finally:

        conn.close()


def _crear_esquema_v7_base_nueva(ruta_db):

    from core.schema_v7 import crear_base_v7

    ruta_db = Path(ruta_db)
    resultado = crear_base_v7(
        ruta_db,
        sobrescribir=ruta_db.exists(),
    )
    LOGGER.info(
        "Base nueva inicializada con esquema v7 en %s (%s tablas).",
        ruta_db,
        resultado.get("table_count"),
    )
    return resultado



def crear_tablas(ruta_db=None):

    ruta_db_resuelta = _resolver_ruta_db(ruta_db)

    if _base_nueva_o_vacia(ruta_db_resuelta):

        _crear_esquema_v7_base_nueva(ruta_db_resuelta)
        return

    if _base_es_v7(ruta_db_resuelta):

        from core.schema_v7 import asegurar_ampliaciones_v8_0_1

        LOGGER.info(
            "Base v7 existente detectada en %s; se aseguran ampliaciones "
            "limpias v7.17/v8.0.1 y no se ejecuta esquema legacy.",
            ruta_db_resuelta,
        )

        conn = conectar(ruta_db_resuelta)

        try:

            asegurar_ampliaciones_v8_0_1(conn)
            conn.commit()

        finally:

            conn.close()

        return

    LOGGER.info(
        "Base existente detectada en %s; se mantiene modo compatible.",
        ruta_db_resuelta,
    )

    conn = conectar(ruta_db_resuelta)
    c = conn.cursor()


    # ------------------------------
    # CAMPAÑAS AGRÍCOLAS
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS campanas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        activa INTEGER DEFAULT 0
    )
    """)


    # ------------------------------
    # DATOS GENERALES DE EXPLOTACIÓN
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS explotacion(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titular TEXT,
        nif TEXT,
        direccion TEXT,
        localidad TEXT,
        codigo_postal TEXT,
        provincia TEXT,
        telefono TEXT,
        email TEXT,
        registro_explotacion TEXT,
        fecha_apertura TEXT,
        observaciones TEXT
    )
    """)

    columnas_explotacion = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(explotacion)")
    }

    nuevas_columnas_explotacion = {
        "nombre_explotacion": "TEXT",
        "codigo_regea": "TEXT",
        "codigo_regepa": "TEXT",
        "tipo_explotacion": "TEXT",
        "orientacion_productiva": "TEXT",
        "fecha_alta": "TEXT",
        "agricultor_activo": "INTEGER DEFAULT 0",
        "joven_agricultor": "INTEGER DEFAULT 0",
        "responsable_nombre": "TEXT",
        "responsable_nif": "TEXT",
        "responsable_telefono": "TEXT",
        "asesor_nombre": "TEXT",
        "asesor_nif": "TEXT",
        "asesor_numero_registro": "TEXT",
        "asesor_telefono": "TEXT"
    }

    for columna, tipo in nuevas_columnas_explotacion.items():

        if columna not in columnas_explotacion:

            c.execute(
                f"ALTER TABLE explotacion ADD COLUMN {columna} {tipo}"
            )


    # ------------------------------
    # CLIENTES / PROVEEDORES
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        nif TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        poblacion TEXT,
        provincia TEXT,
        codigo_postal TEXT,
        observaciones TEXT,
        activo INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    columnas_clientes = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(clientes)")
    }
    nuevas_columnas_clientes = {
        "nombre": "TEXT",
        "nif": "TEXT",
        "telefono": "TEXT",
        "email": "TEXT",
        "direccion": "TEXT",
        "poblacion": "TEXT",
        "provincia": "TEXT",
        "codigo_postal": "TEXT",
        "observaciones": "TEXT",
        "activo": "INTEGER DEFAULT 1",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    }

    for columna, tipo in nuevas_columnas_clientes.items():

        if columna not in columnas_clientes:

            c.execute(
                f"ALTER TABLE clientes ADD COLUMN {columna} {tipo}"
            )

    c.execute("""
    CREATE TABLE IF NOT EXISTS proveedores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        nif TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        poblacion TEXT,
        provincia TEXT,
        codigo_postal TEXT,
        actividad TEXT,
        observaciones TEXT,
        activo INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    columnas_proveedores = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(proveedores)")
    }
    nuevas_columnas_proveedores = {
        "nombre": "TEXT",
        "nif": "TEXT",
        "telefono": "TEXT",
        "email": "TEXT",
        "direccion": "TEXT",
        "poblacion": "TEXT",
        "provincia": "TEXT",
        "codigo_postal": "TEXT",
        "actividad": "TEXT",
        "observaciones": "TEXT",
        "activo": "INTEGER DEFAULT 1",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    }

    for columna, tipo in nuevas_columnas_proveedores.items():

        if columna not in columnas_proveedores:

            c.execute(
                f"ALTER TABLE proveedores ADD COLUMN {columna} {tipo}"
            )



    # ------------------------------
    # PARCELAS SIGPAC
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS parcelas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT,

        provincia TEXT,
        municipio TEXT,

        provincia_sigpac INTEGER,
        municipio_sigpac INTEGER,
        agregado_sigpac INTEGER DEFAULT 0,
        zona_sigpac INTEGER DEFAULT 0,

        poligono TEXT,
        parcela TEXT,
        recinto TEXT,

        superficie_sigpac REAL,
        superficie_cultivada REAL,

        geometry TEXT,

        sigpac_geojson TEXT,
        sigpac_geojson_actualizado TEXT,
        sigpac_geojson_estado TEXT,
        sigpac_geojson_error TEXT,

        observaciones TEXT
    )
    """)



    # ------------------------------
    # CULTIVOS
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS cultivos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        campana_id INTEGER,

        parcela_id INTEGER,

        especie TEXT,
        variedad TEXT,

        codigo_siex TEXT,
        superficie REAL,

        ano_plantacion INTEGER,
        marco TEXT,
        arboles INTEGER,

        sistema TEXT,

        activo INTEGER DEFAULT 1,

        FOREIGN KEY(campana_id)
        REFERENCES campanas(id),

        FOREIGN KEY(parcela_id)
        REFERENCES parcelas(id)
    )
    """)

    columnas_cultivos = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(cultivos)")
    }
    nuevas_columnas_cultivos = {
        "campana_id": "INTEGER",
        "codigo_siex": "TEXT",
        "superficie": "REAL",
        "activo": "INTEGER DEFAULT 1"
    }

    for columna, tipo in nuevas_columnas_cultivos.items():

        if columna not in columnas_cultivos:

            c.execute(
                f"ALTER TABLE cultivos ADD COLUMN {columna} {tipo}"
            )

    c.execute("""
    CREATE TABLE IF NOT EXISTS cultivo_parcelas(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        cultivo_id INTEGER NOT NULL,
        parcela_id INTEGER NOT NULL,
        superficie REAL,
        created_at TEXT,
        updated_at TEXT,

        FOREIGN KEY(cultivo_id)
        REFERENCES cultivos(id),

        FOREIGN KEY(parcela_id)
        REFERENCES parcelas(id)

    )
    """)

    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_cultivos_campana_id
    ON cultivos(campana_id)
    """)
    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_cultivos_codigo_siex
    ON cultivos(codigo_siex)
    """)
    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_cultivo_parcelas_cultivo_id
    ON cultivo_parcelas(cultivo_id)
    """)
    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_cultivo_parcelas_parcela_id
    ON cultivo_parcelas(parcela_id)
    """)




    # ------------------------------
    # PRODUCTOS FITOSANITARIOS MAPA
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS productos_fito(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        registro TEXT,

        nombre TEXT,

        materia_activa TEXT,

        dosis TEXT,

        plazo_seguridad TEXT,

        observaciones TEXT

    )
    """)

    columnas_parcelas = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(parcelas)")
    }
    nuevas_columnas_parcelas = {
        "provincia_sigpac": "INTEGER",
        "municipio_sigpac": "INTEGER",
        "agregado_sigpac": "INTEGER DEFAULT 0",
        "zona_sigpac": "INTEGER DEFAULT 0",
        "sigpac_geojson": "TEXT",
        "sigpac_geojson_actualizado": "TEXT",
        "sigpac_geojson_estado": "TEXT",
        "sigpac_geojson_error": "TEXT"
    }

    for columna, tipo in nuevas_columnas_parcelas.items():

        if columna not in columnas_parcelas:

            c.execute(
                f"ALTER TABLE parcelas ADD COLUMN {columna} {tipo}"
            )

    c.execute(
        """
        UPDATE parcelas
        SET provincia_sigpac=30,
            municipio_sigpac=22,
            agregado_sigpac=COALESCE(
                NULLIF(agregado_sigpac,''),
                0
            ),
            zona_sigpac=COALESCE(NULLIF(zona_sigpac,''),0)
        WHERE LOWER(TRIM(COALESCE(provincia,'')))='murcia'
        AND LOWER(TRIM(COALESCE(municipio,'')))='jumilla'
        """
    )


    # ------------------------------
    # EQUIPOS DE APLICACIÓN FITOSANITARIA
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS equipos_aplicacion(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT,

        tipo TEXT,

        marca TEXT,

        modelo TEXT,

        numero_roma TEXT,

        numero_serie TEXT,

        fecha_adquisicion TEXT,

        fecha_ultima_inspeccion TEXT,

        fecha_proxima_inspeccion TEXT,

        capacidad_litros REAL,

        observaciones TEXT

    )
    """)


    # ------------------------------
    # PERSONAS RELACIONADAS
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS personas(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT,

        nif TEXT,

        telefono TEXT,

        email TEXT,

        rol TEXT,

        carnet_fitosanitario TEXT,

        fecha_caducidad_carnet TEXT,

        numero_asesor TEXT,

        observaciones TEXT

    )
    """)




    # ------------------------------
    # TRATAMIENTOS
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS tratamientos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        campana_id INTEGER,

        fecha TEXT,

        problema TEXT,

        producto_id INTEGER,

        dosis TEXT,

        caldo REAL,

        aplicador TEXT,

        maquinaria_id INTEGER,

        eficacia TEXT,

        observaciones TEXT,


        FOREIGN KEY(campana_id)
        REFERENCES campanas(id),


        FOREIGN KEY(producto_id)
        REFERENCES productos_fito(id)

    )
    """)

    columnas_tratamientos = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(tratamientos)")
    }

    nuevas_columnas_tratamientos = {
        "fecha_inicio": "TEXT",
        "fecha_fin": "TEXT",
        "cultivo_id": "INTEGER",
        "aplicador_id": "INTEGER",
        "equipo_id": "INTEGER",
        "equipo_aplicacion_id": "INTEGER",
        "plaga": "TEXT",
        "justificacion": "TEXT",
        "superficie_tratada": "REAL",
        "plazo_seguridad": "TEXT",
        "fecha_recoleccion_segura": "TEXT",
        "condiciones": "TEXT",
        "condiciones_meteorologicas": "TEXT",
        "eficacia": "TEXT"
    }

    for columna, tipo in nuevas_columnas_tratamientos.items():

        if columna not in columnas_tratamientos:

            c.execute(
                f"ALTER TABLE tratamientos ADD COLUMN {columna} {tipo}"
            )



    # Relación tratamiento parcelas

    c.execute("""
    CREATE TABLE IF NOT EXISTS tratamiento_parcelas(

        tratamiento_id INTEGER,

        parcela_id INTEGER,

        superficie REAL,


        FOREIGN KEY(tratamiento_id)
        REFERENCES tratamientos(id),


        FOREIGN KEY(parcela_id)
        REFERENCES parcelas(id)

    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS tratamientos_documentos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        tratamiento_id INTEGER NOT NULL,
        tipo_documento TEXT DEFAULT 'receta',
        nombre_original TEXT,
        nombre_guardado TEXT,
        ruta_relativa TEXT NOT NULL,
        extension TEXT DEFAULT 'pdf',
        mime_type TEXT,
        size_bytes INTEGER,
        sha256 TEXT,
        orden INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT,

        FOREIGN KEY(tratamiento_id)
        REFERENCES tratamientos(id)

    )
    """)

    columnas_tratamientos_documentos = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(tratamientos_documentos)")
    }
    nuevas_columnas_tratamientos_documentos = {
        "tratamiento_id": "INTEGER",
        "tipo_documento": "TEXT DEFAULT 'receta'",
        "nombre_original": "TEXT",
        "nombre_guardado": "TEXT",
        "ruta_relativa": "TEXT",
        "extension": "TEXT DEFAULT 'pdf'",
        "mime_type": "TEXT",
        "size_bytes": "INTEGER",
        "sha256": "TEXT",
        "orden": "INTEGER DEFAULT 1",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    }

    for columna, tipo in nuevas_columnas_tratamientos_documentos.items():

        if columna not in columnas_tratamientos_documentos:

            c.execute(
                "ALTER TABLE tratamientos_documentos "
                f"ADD COLUMN {columna} {tipo}"
            )

    # ------------------------------
    # ANÁLISIS FITOSANITARIOS
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS analisis_fitosanitarios(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        campana_id INTEGER,

        fecha TEXT,

        material_analizado TEXT,

        cultivo_id INTEGER,

        parcelas TEXT,

        boletin_numero TEXT,

        laboratorio TEXT,

        sustancias_detectadas TEXT,

        resultado TEXT,

        observaciones TEXT,

        documento TEXT,

        created_at TEXT,

        updated_at TEXT

    )
    """)

    columnas_analisis = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(analisis_fitosanitarios)")
    }

    nuevas_columnas_analisis = {
        "campana_id": "INTEGER",
        "fecha": "TEXT",
        "material_analizado": "TEXT",
        "cultivo_id": "INTEGER",
        "parcelas": "TEXT",
        "boletin_numero": "TEXT",
        "laboratorio": "TEXT",
        "sustancias_detectadas": "TEXT",
        "resultado": "TEXT",
        "observaciones": "TEXT",
        "documento": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT"
    }

    for columna, tipo in nuevas_columnas_analisis.items():

        if columna not in columnas_analisis:

            c.execute(
                f"ALTER TABLE analisis_fitosanitarios ADD COLUMN {columna} {tipo}"
            )



    # ------------------------------
    # FERTILIZACIÓN
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS fertilizaciones(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        campana_id INTEGER,
        cultivo_id INTEGER,
        fecha TEXT,
        cultivo TEXT,
        producto TEXT,
        tipo TEXT,
        riqueza_npk TEXT,
        cantidad REAL,
        unidad TEXT,
        metodo_aplicacion TEXT,
        superficie REAL,
        operario_id INTEGER,
        observaciones TEXT

    )
    """)

    columnas_fertilizaciones = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(fertilizaciones)")
    }
    nuevas_columnas_fertilizaciones = {
        "cultivo_id": "INTEGER"
    }

    for columna, tipo in nuevas_columnas_fertilizaciones.items():

        if columna not in columnas_fertilizaciones:

            c.execute(
                f"ALTER TABLE fertilizaciones ADD COLUMN {columna} {tipo}"
            )

    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_fertilizaciones_cultivo_id
    ON fertilizaciones(cultivo_id)
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS fertilizacion_parcelas(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        fertilizacion_id INTEGER,
        parcela_id INTEGER

    )
    """)



    # ------------------------------
    # PRÁCTICAS CULTURALES
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS practicas_culturales(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        campana_id INTEGER,
        cultivo_id INTEGER,
        fecha TEXT,
        cultivo TEXT,
        labor TEXT,
        superficie REAL,
        maquinaria_id INTEGER,
        operario_id INTEGER,
        proveedor_id INTEGER,
        observaciones TEXT

    )
    """)

    columnas_practicas_culturales = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(practicas_culturales)")
    }
    nuevas_columnas_practicas_culturales = {
        "cultivo_id": "INTEGER",
        "proveedor_id": "INTEGER"
    }

    for columna, tipo in nuevas_columnas_practicas_culturales.items():

        if columna not in columnas_practicas_culturales:

            c.execute(
                f"ALTER TABLE practicas_culturales ADD COLUMN {columna} {tipo}"
            )

    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_practicas_culturales_cultivo_id
    ON practicas_culturales(cultivo_id)
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS practica_parcelas(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        practica_id INTEGER,
        parcela_id INTEGER

    )
    """)



    # ------------------------------
    # MAQUINARIA
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS maquinaria(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT,

        tipo TEXT,

        marca TEXT,

        modelo TEXT,

        numero_roma TEXT,

        fecha_compra TEXT,

        num_horas REAL,

        observaciones TEXT

    )
    """)

    columnas_maquinaria = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(maquinaria)")
    }
    nuevas_columnas_maquinaria = {
        "numero_roma": "TEXT"
    }

    for columna, tipo in nuevas_columnas_maquinaria.items():

        if columna not in columnas_maquinaria:

            c.execute(
                f"ALTER TABLE maquinaria ADD COLUMN {columna} {tipo}"
            )




    # ------------------------------
    # MANTENIMIENTO
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS mantenimientos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        maquinaria_id INTEGER,

        fecha TEXT,

        horas REAL,

        trabajo TEXT,

        coste REAL,


        FOREIGN KEY(maquinaria_id)
        REFERENCES maquinaria(id)

    )
    """)




    # ------------------------------
    # GASTOS
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS gastos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        campana_id INTEGER,

        fecha TEXT,

        categoria TEXT,

        concepto TEXT,

        importe REAL,


        FOREIGN KEY(campana_id)
        REFERENCES campanas(id)

    )
    """)



    # ------------------------------
    # INGRESOS / COSECHA
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS cosecha(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        campana_id INTEGER,

        cultivo_id INTEGER,

        fecha TEXT,

        cultivo TEXT,

        kg REAL,

        precio REAL,

        lote TEXT,

        cliente TEXT,

        observaciones TEXT

    )
    """)



    # ------------------------------
    # CONTABILIDAD AGRÍCOLA
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_economicos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        campana_id INTEGER,
        fecha TEXT,
        tipo TEXT,
        categoria TEXT,
        concepto TEXT,
        tercero TEXT,
        nif_tercero TEXT,
        numero_factura TEXT,
        base_imponible REAL,
        iva_porcentaje REAL,
        iva_importe REAL,
        retencion REAL,
        total REAL,
        forma_pago TEXT,
        pagado INTEGER DEFAULT 0,
        fecha_pago TEXT,
        cultivo TEXT,
        cliente_id INTEGER,
        proveedor_id INTEGER,
        observaciones TEXT

    )
    """)

    columnas_movimientos_economicos = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(movimientos_economicos)")
    }
    nuevas_columnas_movimientos_economicos = {
        "cliente_id": "INTEGER",
        "proveedor_id": "INTEGER"
    }

    for columna, tipo in nuevas_columnas_movimientos_economicos.items():

        if columna not in columnas_movimientos_economicos:

            c.execute(
                f"ALTER TABLE movimientos_economicos ADD COLUMN {columna} {tipo}"
            )

    c.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_economicos_documentos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        movimiento_id INTEGER NOT NULL,
        tipo_documento TEXT DEFAULT 'factura',
        nombre_original TEXT,
        nombre_guardado TEXT,
        ruta_relativa TEXT NOT NULL,
        extension TEXT DEFAULT 'pdf',
        mime_type TEXT,
        size_bytes INTEGER,
        sha256 TEXT,
        orden INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT,

        FOREIGN KEY(movimiento_id)
        REFERENCES movimientos_economicos(id)

    )
    """)

    columnas_movimientos_documentos = {
        fila[1]
        for fila in c.execute(
            "PRAGMA table_info(movimientos_economicos_documentos)"
        )
    }
    nuevas_columnas_movimientos_documentos = {
        "movimiento_id": "INTEGER",
        "tipo_documento": "TEXT DEFAULT 'factura'",
        "nombre_original": "TEXT",
        "nombre_guardado": "TEXT",
        "ruta_relativa": "TEXT",
        "extension": "TEXT DEFAULT 'pdf'",
        "mime_type": "TEXT",
        "size_bytes": "INTEGER",
        "sha256": "TEXT",
        "orden": "INTEGER DEFAULT 1",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    }

    for columna, tipo in nuevas_columnas_movimientos_documentos.items():

        if columna not in columnas_movimientos_documentos:

            c.execute(
                "ALTER TABLE movimientos_economicos_documentos "
                f"ADD COLUMN {columna} {tipo}"
            )

    c.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_economicos_lineas_iva(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        movimiento_id INTEGER NOT NULL,
        descripcion TEXT,
        base_imponible REAL DEFAULT 0,
        tipo_iva REAL DEFAULT 0,
        cuota_iva REAL DEFAULT 0,
        total_linea REAL DEFAULT 0,
        created_at TEXT,
        updated_at TEXT,

        FOREIGN KEY(movimiento_id)
        REFERENCES movimientos_economicos(id)

    )
    """)

    columnas_cosecha = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(cosecha)")
    }

    nuevas_columnas_cosecha = {
        "cultivo": "TEXT",
        "cultivo_id": "INTEGER",
        "producto": "TEXT",
        "parcelas": "TEXT",
        "albaran": "TEXT",
        "factura": "TEXT",
        "lote": "TEXT",
        "cliente": "TEXT",
        "nif_cliente": "TEXT",
        "destino": "TEXT",
        "precio": "REAL",
        "observaciones": "TEXT"
    }

    for columna, tipo in nuevas_columnas_cosecha.items():

        if columna not in columnas_cosecha:

            c.execute(
                f"ALTER TABLE cosecha ADD COLUMN {columna} {tipo}"
            )

    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_cosecha_cultivo_id
    ON cosecha(cultivo_id)
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS cosecha_parcelas(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        cosecha_id INTEGER,
        parcela_id INTEGER

    )
    """)




    # ------------------------------
    # DIARIO DE CAMPO
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS diario(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        fecha TEXT,

        parcela_id INTEGER,

        nota TEXT,

        imagen TEXT

    )
    """)

    # ------------------------------
    # CATALOGOS SIEX / CUE
    # ------------------------------

    c.execute("""
    CREATE TABLE IF NOT EXISTS siex_catalogos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        codigo_catalogo TEXT NOT NULL,
        nombre_catalogo TEXT NOT NULL,
        archivo_origen TEXT,
        version TEXT,
        fecha_importacion TEXT,
        observaciones TEXT

    )
    """)

    columnas_siex_catalogos = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(siex_catalogos)")
    }
    nuevas_columnas_siex_catalogos = {
        "codigo_catalogo": "TEXT",
        "nombre_catalogo": "TEXT",
        "archivo_origen": "TEXT",
        "version": "TEXT",
        "fecha_importacion": "TEXT",
        "observaciones": "TEXT"
    }

    for columna, tipo in nuevas_columnas_siex_catalogos.items():

        if columna not in columnas_siex_catalogos:

            c.execute(
                f"ALTER TABLE siex_catalogos ADD COLUMN {columna} {tipo}"
            )

    c.execute("""
    CREATE TABLE IF NOT EXISTS siex_catalogos_items(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        catalogo_id INTEGER NOT NULL,
        codigo TEXT,
        codigo_secundario TEXT,
        descripcion TEXT,
        descripcion_secundaria TEXT,
        fecha_alta TEXT,
        fecha_baja TEXT,
        activo INTEGER DEFAULT 1,
        datos_json TEXT,
        created_at TEXT,
        updated_at TEXT,

        FOREIGN KEY(catalogo_id)
        REFERENCES siex_catalogos(id)
        ON DELETE CASCADE

    )
    """)

    columnas_siex_items = {
        fila[1]
        for fila in c.execute("PRAGMA table_info(siex_catalogos_items)")
    }
    nuevas_columnas_siex_items = {
        "catalogo_id": "INTEGER",
        "codigo": "TEXT",
        "codigo_secundario": "TEXT",
        "descripcion": "TEXT",
        "descripcion_secundaria": "TEXT",
        "fecha_alta": "TEXT",
        "fecha_baja": "TEXT",
        "activo": "INTEGER DEFAULT 1",
        "datos_json": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT"
    }

    for columna, tipo in nuevas_columnas_siex_items.items():

        if columna not in columnas_siex_items:

            c.execute(
                f"ALTER TABLE siex_catalogos_items ADD COLUMN {columna} {tipo}"
            )

    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_siex_items_catalogo_id
    ON siex_catalogos_items(catalogo_id)
    """)
    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_siex_items_codigo
    ON siex_catalogos_items(codigo)
    """)
    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_siex_items_activo
    ON siex_catalogos_items(activo)
    """)
    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_siex_items_descripcion
    ON siex_catalogos_items(descripcion)
    """)



    conn.commit()
    conn.close()





def resetear_base_datos_creando_backup():

    ruta_db = _resolver_ruta_db()
    ruta_backup = _crear_backup_antes_resetear(ruta_db)
    ruta_temporal = _crear_base_limpia_temporal(ruta_db.parent)

    try:

        _aplicar_permisos_db(ruta_db, ruta_temporal)
        _reemplazar_base_datos(ruta_temporal, ruta_db)
        _eliminar_auxiliares_sqlite(ruta_db)
        _validar_base_inicializada(ruta_db)

    except Exception as error:

        _eliminar_temporal(ruta_temporal)

        if ruta_backup:

            try:

                _restaurar_backup_reset(ruta_backup, ruta_db)

            except Exception as error_restauracion:

                raise RuntimeError(
                    "No se pudo completar el reset y tampoco se pudo "
                    "restaurar automáticamente la copia previa. "
                    f"Error del reset: {error}. "
                    f"Error al restaurar: {error_restauracion}"
                ) from error

        raise

    return ruta_backup


def _crear_backup_antes_resetear(ruta_db):

    if not ruta_db.exists():

        return None

    if ruta_db.is_dir():
        raise RuntimeError(
            "La ruta configurada para SQLite apunta a un directorio, no a "
            f"un fichero de base de datos: {ruta_db}"
        )

    if ruta_db.stat().st_size <= 0:
        raise RuntimeError(
            "La base de datos actual existe, pero está vacía. No se puede "
            "crear una copia automática válida."
        )

    _sincronizar_sqlite_si_es_posible(ruta_db)
    asegurar_directorio(BACKUPS_DIR)
    marca_tiempo = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ruta_backup = BACKUPS_DIR / f"antes_resetear_{marca_tiempo}.db"
    contador = 1

    while ruta_backup.exists():

        ruta_backup = (
            BACKUPS_DIR / f"antes_resetear_{marca_tiempo}_{contador}.db"
        )
        contador += 1

    shutil.copy2(ruta_db, ruta_backup)

    if not ruta_backup.exists() or ruta_backup.stat().st_size <= 0:
        raise RuntimeError(
            "No se pudo validar la copia automática previa al reset."
        )

    return str(ruta_backup.resolve())


def _sincronizar_sqlite_si_es_posible(ruta_db):

    conn = None

    try:

        conn = sqlite3.connect(str(ruta_db))
        conn.execute("PRAGMA wal_checkpoint(FULL)")

    except sqlite3.Error:

        pass

    finally:

        if conn is not None:

            conn.close()


def _crear_base_limpia_temporal(directorio_db):

    descriptor, ruta_temporal = tempfile.mkstemp(
        prefix=".cuadernopro_reset_",
        suffix=".db",
        dir=str(directorio_db)
    )
    os.close(descriptor)

    try:

        crear_tablas(ruta_temporal)
        _validar_base_inicializada(Path(ruta_temporal))

    except Exception:

        _eliminar_temporal(ruta_temporal)
        raise

    return ruta_temporal


def _aplicar_permisos_db(ruta_db, ruta_intermedia):

    if ruta_db.exists():

        modo = ruta_db.stat().st_mode & 0o777

    else:

        modo = 0o644

    os.chmod(ruta_intermedia, modo)


def _reemplazar_base_datos(ruta_origen, ruta_destino):

    try:

        os.replace(ruta_origen, ruta_destino)

    except OSError as error:

        if error.errno != errno.EBUSY:

            raise

        _sobrescribir_fichero_montado(ruta_origen, ruta_destino)


def _sobrescribir_fichero_montado(ruta_origen, ruta_destino):

    with open(ruta_origen, "rb") as origen:

        with open(ruta_destino, "wb") as destino:

            shutil.copyfileobj(origen, destino)
            destino.flush()
            os.fsync(destino.fileno())

    _eliminar_temporal(ruta_origen)


def _eliminar_auxiliares_sqlite(ruta_db):

    for sufijo in ("-wal", "-shm", "-journal"):

        ruta_auxiliar = Path(str(ruta_db) + sufijo)

        if ruta_auxiliar.exists():

            ruta_auxiliar.unlink()


def _validar_base_inicializada(ruta_db):

    ruta_db = Path(ruta_db)

    if not ruta_db.exists() or ruta_db.stat().st_size <= 0:
        raise RuntimeError("La base de datos generada está vacía o no existe.")

    conn = sqlite3.connect(str(ruta_db))

    try:

        integridad = conn.execute("PRAGMA integrity_check").fetchone()

        if (
            not integridad
            or str(integridad[0]).lower() != "ok"
        ):
            raise RuntimeError(
                "La base de datos generada no pasa la comprobación de "
                "integridad."
            )

        tablas = {
            fila[0]
            for fila in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                """
            )
        }

    finally:

        conn.close()

    tablas_faltantes = sorted(TABLAS_ESQUEMA_MINIMO - tablas)

    if tablas_faltantes:
        raise RuntimeError(
            "La base de datos generada no contiene todas las tablas mínimas: "
            + ", ".join(tablas_faltantes)
        )


def _restaurar_backup_reset(ruta_backup, ruta_db):

    ruta_backup = Path(ruta_backup)
    descriptor, ruta_intermedia = tempfile.mkstemp(
        prefix=".cuadernopro_restaurando_reset_",
        suffix=".db",
        dir=str(ruta_db.parent)
    )
    os.close(descriptor)

    try:

        shutil.copy2(ruta_backup, ruta_intermedia)
        _aplicar_permisos_db(ruta_db, ruta_intermedia)
        _reemplazar_base_datos(ruta_intermedia, ruta_db)

    except Exception:

        _eliminar_temporal(ruta_intermedia)
        raise


def _eliminar_temporal(ruta):

    try:

        if ruta and os.path.exists(ruta):

            os.remove(ruta)

    except OSError:

        pass


def leer(sql, params=()):

    conn = conectar()

    df = pd.read_sql_query(
        sql,
        conn,
        params=params
    )

    conn.close()

    return df




def ejecutar(sql, params=()):

    conn = conectar()

    conn.execute(
        sql,
        params
    )

    conn.commit()

    conn.close()





def obtener_campana():

    from core.fechas import hoy

    df = leer(
        "SELECT * FROM campanas WHERE activa=1"
    )

    if df.empty:

        existente = leer(
            "SELECT id FROM campanas WHERE nombre=?",
            ("2025/2026",)
        )

        if not existente.empty:

            ejecutar(
                "UPDATE campanas SET activa=1 WHERE nombre=?",
                ("2025/2026",)
            )

            return int(existente.iloc[0]["id"])

        ejecutar(
            """
            INSERT INTO campanas
            (nombre,fecha_inicio,activa)

            VALUES (?,?,1)
            """,

            (
                "2025/2026",
                hoy()
            )
        )

        return obtener_campana()

    return int(df.iloc[0]["id"])
