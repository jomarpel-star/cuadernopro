from pathlib import Path
import sqlite3


SCHEMA_VERSION = 7


PRINCIPAL_TABLES = (
    "explotacion",
    "campanas",
    "parcelas",
    "cultivos",
    "cultivo_parcelas",
    "tratamientos",
    "fertilizaciones",
    "practicas_culturales",
    "cosecha",
    "movimientos_economicos",
)


TABLE_DEFINITIONS = (
    """
    CREATE TABLE IF NOT EXISTS explotacion(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_explotacion TEXT,
        titular TEXT,
        nif TEXT,
        direccion TEXT,
        municipio TEXT,
        provincia TEXT,
        codigo_postal TEXT,
        telefono TEXT,
        email TEXT,
        identificador_oficial TEXT,
        tipo_identificador_oficial TEXT,
        registro_autonomico TEXT,
        tipo_explotacion TEXT,
        orientacion_productiva TEXT,
        fecha_alta TEXT,
        agricultor_activo INTEGER DEFAULT 0,
        joven_agricultor INTEGER DEFAULT 0,
        responsable TEXT,
        asesor TEXT,
        numero_asesor TEXT,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campanas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        activa INTEGER DEFAULT 0,
        estado TEXT DEFAULT 'abierta',
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS parcelas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        provincia_sigpac INTEGER,
        municipio_sigpac INTEGER,
        agregado_sigpac INTEGER DEFAULT 0,
        zona_sigpac INTEGER DEFAULT 0,
        poligono TEXT,
        parcela TEXT,
        recinto TEXT,
        superficie_sigpac REAL,
        uso_sigpac TEXT,
        sigpac_geojson TEXT,
        activa INTEGER DEFAULT 1,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cultivos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campana_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        variedad TEXT,
        codigo_siex TEXT,
        superficie REAL,
        ano_plantacion INTEGER,
        marco_plantacion TEXT,
        numero_arboles INTEGER,
        activo INTEGER DEFAULT 1,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(campana_id) REFERENCES campanas(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cultivo_parcelas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cultivo_id INTEGER NOT NULL,
        parcela_id INTEGER NOT NULL,
        superficie REAL,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id) ON DELETE CASCADE,
        FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
        UNIQUE(cultivo_id, parcela_id)
    )
    """,
    """
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
    """,
    """
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
    """,
    """
    CREATE TABLE IF NOT EXISTS productos_fito(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        numero_registro TEXT,
        materia_activa TEXT,
        titular TEXT,
        uso_autorizado TEXT,
        plazo_seguridad TEXT,
        observaciones TEXT,
        activo INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS personas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        nif TEXT,
        telefono TEXT,
        email TEXT,
        rol TEXT,
        carnet_aplicador TEXT,
        numero_asesor TEXT,
        observaciones TEXT,
        activo INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS maquinaria(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        marca TEXT,
        modelo TEXT,
        matricula TEXT,
        numero_roma TEXT,
        numero_serie TEXT,
        fecha_compra TEXT,
        horas_uso REAL,
        descripcion TEXT,
        observaciones TEXT,
        activa INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS equipos_aplicacion(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        marca TEXT,
        modelo TEXT,
        tipo TEXT,
        matricula TEXT,
        numero_roma TEXT,
        numero_serie TEXT,
        fecha_adquisicion TEXT,
        capacidad_litros REAL,
        fecha_revision TEXT,
        fecha_proxima_revision TEXT,
        observaciones TEXT,
        activo INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS siex_catalogos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_catalogo TEXT NOT NULL,
        nombre_catalogo TEXT NOT NULL,
        archivo_origen TEXT,
        version TEXT,
        fecha_importacion TEXT,
        observaciones TEXT
    )
    """,
    """
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
        FOREIGN KEY(catalogo_id) REFERENCES siex_catalogos(id)
        ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tratamientos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campana_id INTEGER NOT NULL,
        cultivo_id INTEGER NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL,
        producto_id INTEGER NOT NULL,
        aplicador_id INTEGER,
        equipo_aplicacion_id INTEGER,
        plaga_motivo TEXT,
        dosis TEXT,
        caldo REAL,
        superficie_tratada REAL,
        plazo_seguridad TEXT,
        eficacia TEXT,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(campana_id) REFERENCES campanas(id),
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
        FOREIGN KEY(producto_id) REFERENCES productos_fito(id),
        FOREIGN KEY(aplicador_id) REFERENCES personas(id),
        FOREIGN KEY(equipo_aplicacion_id) REFERENCES equipos_aplicacion(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tratamiento_parcelas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tratamiento_id INTEGER NOT NULL,
        parcela_id INTEGER NOT NULL,
        superficie REAL,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(tratamiento_id) REFERENCES tratamientos(id)
        ON DELETE CASCADE,
        FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
        UNIQUE(tratamiento_id, parcela_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tratamiento_cultivos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tratamiento_id INTEGER NOT NULL,
        cultivo_id INTEGER NOT NULL,
        parcela_id INTEGER,
        superficie REAL,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(tratamiento_id) REFERENCES tratamientos(id)
        ON DELETE CASCADE,
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
        FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
        UNIQUE(tratamiento_id, cultivo_id, parcela_id)
    )
    """,
    """
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
        FOREIGN KEY(tratamiento_id) REFERENCES tratamientos(id)
        ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fertilizaciones(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campana_id INTEGER NOT NULL,
        cultivo_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        producto TEXT NOT NULL,
        tipo_fertilizante TEXT,
        cantidad REAL,
        unidad TEXT,
        unidad_normalizada TEXT,
        superficie REAL,
        codigo_actuacion_siex TEXT,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(campana_id) REFERENCES campanas(id),
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fertilizacion_parcelas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fertilizacion_id INTEGER NOT NULL,
        parcela_id INTEGER NOT NULL,
        superficie REAL,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(fertilizacion_id) REFERENCES fertilizaciones(id)
        ON DELETE CASCADE,
        FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
        UNIQUE(fertilizacion_id, parcela_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fertilizacion_cultivos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fertilizacion_id INTEGER NOT NULL,
        cultivo_id INTEGER NOT NULL,
        parcela_id INTEGER,
        superficie REAL,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(fertilizacion_id) REFERENCES fertilizaciones(id)
        ON DELETE CASCADE,
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
        FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
        UNIQUE(fertilizacion_id, cultivo_id, parcela_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS practicas_culturales(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campana_id INTEGER NOT NULL,
        cultivo_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        labor TEXT NOT NULL,
        codigo_actuacion_siex TEXT,
        superficie REAL,
        maquinaria_id INTEGER,
        proveedor_id INTEGER,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(campana_id) REFERENCES campanas(id),
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
        FOREIGN KEY(maquinaria_id) REFERENCES maquinaria(id),
        FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS practicas_culturales_parcelas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        practica_id INTEGER NOT NULL,
        parcela_id INTEGER NOT NULL,
        superficie REAL,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(practica_id) REFERENCES practicas_culturales(id)
        ON DELETE CASCADE,
        FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
        UNIQUE(practica_id, parcela_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS practicas_culturales_cultivos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        practica_id INTEGER NOT NULL,
        cultivo_id INTEGER NOT NULL,
        parcela_id INTEGER,
        superficie REAL,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(practica_id) REFERENCES practicas_culturales(id)
        ON DELETE CASCADE,
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
        FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
        UNIQUE(practica_id, cultivo_id, parcela_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cosecha(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campana_id INTEGER NOT NULL,
        cultivo_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        cantidad REAL NOT NULL,
        unidad TEXT NOT NULL,
        destino TEXT,
        cliente_id INTEGER,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(campana_id) REFERENCES campanas(id),
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cosecha_parcelas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cosecha_id INTEGER NOT NULL,
        parcela_id INTEGER NOT NULL,
        superficie REAL,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(cosecha_id) REFERENCES cosecha(id) ON DELETE CASCADE,
        FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
        UNIQUE(cosecha_id, parcela_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cosecha_cultivos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cosecha_id INTEGER NOT NULL,
        cultivo_id INTEGER NOT NULL,
        parcela_id INTEGER,
        superficie REAL,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(cosecha_id) REFERENCES cosecha(id) ON DELETE CASCADE,
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
        FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
        UNIQUE(cosecha_id, cultivo_id, parcela_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS movimientos_economicos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campana_id INTEGER NOT NULL,
        cultivo_id INTEGER,
        fecha TEXT NOT NULL,
        tipo TEXT NOT NULL,
        categoria TEXT,
        concepto TEXT,
        numero_factura TEXT,
        cliente_id INTEGER,
        proveedor_id INTEGER,
        base_imponible REAL DEFAULT 0,
        iva REAL DEFAULT 0,
        retencion REAL DEFAULT 0,
        total REAL DEFAULT 0,
        pendiente INTEGER DEFAULT 0,
        fecha_pago TEXT,
        observaciones TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(campana_id) REFERENCES campanas(id),
        FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
    )
    """,
    """
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
        FOREIGN KEY(movimiento_id) REFERENCES movimientos_economicos(id)
        ON DELETE CASCADE
    )
    """,
    """
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
        FOREIGN KEY(movimiento_id) REFERENCES movimientos_economicos(id)
        ON DELETE CASCADE
    )
    """,
)


EXPECTED_COLUMNS = {
    "explotacion": (
        "id", "nombre_explotacion", "titular", "nif", "direccion",
        "municipio", "provincia", "codigo_postal", "telefono", "email",
        "identificador_oficial", "tipo_identificador_oficial",
        "registro_autonomico", "tipo_explotacion",
        "orientacion_productiva", "fecha_alta", "agricultor_activo",
        "joven_agricultor",
        "responsable", "asesor", "numero_asesor", "observaciones",
        "created_at", "updated_at",
    ),
    "campanas": (
        "id", "nombre", "fecha_inicio", "fecha_fin", "activa", "estado",
        "observaciones", "created_at", "updated_at",
    ),
    "parcelas": (
        "id", "nombre", "provincia_sigpac", "municipio_sigpac",
        "agregado_sigpac", "zona_sigpac", "poligono", "parcela", "recinto",
        "superficie_sigpac", "uso_sigpac", "sigpac_geojson", "activa",
        "observaciones", "created_at", "updated_at",
    ),
    "cultivos": (
        "id", "campana_id", "nombre", "variedad", "codigo_siex",
        "superficie", "ano_plantacion", "marco_plantacion",
        "numero_arboles", "activo", "observaciones", "created_at",
        "updated_at",
    ),
    "cultivo_parcelas": (
        "id", "cultivo_id", "parcela_id", "superficie", "created_at",
        "updated_at",
    ),
    "clientes": (
        "id", "nombre", "nif", "telefono", "email", "direccion",
        "poblacion", "provincia", "codigo_postal", "observaciones",
        "activo", "created_at", "updated_at",
    ),
    "proveedores": (
        "id", "nombre", "nif", "telefono", "email", "direccion",
        "poblacion", "provincia", "codigo_postal", "actividad",
        "observaciones", "activo", "created_at", "updated_at",
    ),
    "productos_fito": (
        "id", "nombre", "numero_registro", "materia_activa", "titular",
        "uso_autorizado", "plazo_seguridad", "observaciones", "activo",
        "created_at", "updated_at",
    ),
    "personas": (
        "id", "nombre", "nif", "telefono", "email", "rol",
        "carnet_aplicador", "numero_asesor", "observaciones", "activo",
        "created_at", "updated_at",
    ),
    "maquinaria": (
        "id", "tipo", "marca", "modelo", "matricula", "numero_roma",
        "numero_serie", "fecha_compra", "horas_uso",
        "descripcion", "observaciones", "activa", "created_at",
        "updated_at",
    ),
    "equipos_aplicacion": (
        "id", "nombre", "marca", "modelo", "tipo", "matricula",
        "numero_roma", "numero_serie", "fecha_adquisicion",
        "capacidad_litros",
        "fecha_revision", "fecha_proxima_revision", "observaciones",
        "activo", "created_at", "updated_at",
    ),
    "siex_catalogos": (
        "id", "codigo_catalogo", "nombre_catalogo", "archivo_origen",
        "version", "fecha_importacion", "observaciones",
    ),
    "siex_catalogos_items": (
        "id", "catalogo_id", "codigo", "codigo_secundario", "descripcion",
        "descripcion_secundaria", "fecha_alta", "fecha_baja", "activo",
        "datos_json", "created_at", "updated_at",
    ),
    "tratamientos": (
        "id", "campana_id", "cultivo_id", "fecha_inicio", "fecha_fin",
        "producto_id", "aplicador_id", "equipo_aplicacion_id",
        "plaga_motivo", "dosis", "caldo", "superficie_tratada",
        "plazo_seguridad", "eficacia", "observaciones", "created_at",
        "updated_at",
    ),
    "tratamiento_parcelas": (
        "id", "tratamiento_id", "parcela_id", "superficie", "created_at",
        "updated_at",
    ),
    "tratamiento_cultivos": (
        "id", "tratamiento_id", "cultivo_id", "parcela_id", "superficie",
        "observaciones", "created_at", "updated_at",
    ),
    "tratamientos_documentos": (
        "id", "tratamiento_id", "tipo_documento", "nombre_original",
        "nombre_guardado", "ruta_relativa", "extension", "mime_type",
        "size_bytes", "sha256", "orden", "created_at", "updated_at",
    ),
    "fertilizaciones": (
        "id", "campana_id", "cultivo_id", "fecha", "producto",
        "tipo_fertilizante", "cantidad", "unidad", "unidad_normalizada",
        "superficie", "codigo_actuacion_siex", "observaciones",
        "created_at", "updated_at",
    ),
    "fertilizacion_parcelas": (
        "id", "fertilizacion_id", "parcela_id", "superficie", "created_at",
        "updated_at",
    ),
    "fertilizacion_cultivos": (
        "id", "fertilizacion_id", "cultivo_id", "parcela_id", "superficie",
        "observaciones", "created_at", "updated_at",
    ),
    "practicas_culturales": (
        "id", "campana_id", "cultivo_id", "fecha", "labor",
        "codigo_actuacion_siex", "superficie", "maquinaria_id",
        "proveedor_id", "observaciones", "created_at", "updated_at",
    ),
    "practicas_culturales_parcelas": (
        "id", "practica_id", "parcela_id", "superficie", "created_at",
        "updated_at",
    ),
    "practicas_culturales_cultivos": (
        "id", "practica_id", "cultivo_id", "parcela_id", "superficie",
        "observaciones", "created_at", "updated_at",
    ),
    "cosecha": (
        "id", "campana_id", "cultivo_id", "fecha", "cantidad", "unidad",
        "destino", "cliente_id", "observaciones", "created_at",
        "updated_at",
    ),
    "cosecha_parcelas": (
        "id", "cosecha_id", "parcela_id", "superficie", "created_at",
        "updated_at",
    ),
    "cosecha_cultivos": (
        "id", "cosecha_id", "cultivo_id", "parcela_id", "superficie",
        "observaciones", "created_at", "updated_at",
    ),
    "movimientos_economicos": (
        "id", "campana_id", "cultivo_id", "fecha", "tipo", "categoria",
        "concepto", "numero_factura", "cliente_id", "proveedor_id",
        "base_imponible", "iva", "retencion", "total", "pendiente",
        "fecha_pago", "observaciones", "created_at", "updated_at",
    ),
    "movimientos_economicos_lineas_iva": (
        "id", "movimiento_id", "descripcion", "base_imponible", "tipo_iva",
        "cuota_iva", "total_linea", "created_at", "updated_at",
    ),
    "movimientos_economicos_documentos": (
        "id", "movimiento_id", "tipo_documento", "nombre_original",
        "nombre_guardado", "ruta_relativa", "extension", "mime_type",
        "size_bytes", "sha256", "orden", "created_at", "updated_at",
    ),
}


FORBIDDEN_COLUMNS = {
    "cultivos": ("parcela_id",),
    "fertilizaciones": ("cultivo",),
    "practicas_culturales": ("cultivo",),
    "cosecha": ("cultivo", "cliente", "nif_cliente", "kg"),
    "movimientos_economicos": ("tercero", "nif_tercero", "cultivo"),
    "tratamientos": (
        "cultivo", "producto", "aplicador", "equipo", "fecha",
    ),
}


V7_13_COLUMN_ADDITIONS = {
    "explotacion": {
        "registro_autonomico": "TEXT",
        "tipo_explotacion": "TEXT",
        "orientacion_productiva": "TEXT",
        "fecha_alta": "TEXT",
        "agricultor_activo": "INTEGER DEFAULT 0",
        "joven_agricultor": "INTEGER DEFAULT 0",
    },
    "maquinaria": {
        "numero_serie": "TEXT",
        "fecha_compra": "TEXT",
        "horas_uso": "REAL",
    },
    "equipos_aplicacion": {
        "matricula": "TEXT",
        "numero_roma": "TEXT",
        "fecha_adquisicion": "TEXT",
        "capacidad_litros": "REAL",
    },
}


V7_17_COLUMN_ADDITIONS = {
    "cultivos": {
        "marco_plantacion": "TEXT",
        "numero_arboles": "INTEGER",
    },
}


INDEX_DEFINITIONS = {
    "idx_campanas_activa": "CREATE INDEX IF NOT EXISTS idx_campanas_activa ON campanas(activa)",
    "idx_campanas_estado": "CREATE INDEX IF NOT EXISTS idx_campanas_estado ON campanas(estado)",
    "idx_parcelas_sigpac": "CREATE INDEX IF NOT EXISTS idx_parcelas_sigpac ON parcelas(provincia_sigpac, municipio_sigpac, agregado_sigpac, zona_sigpac, poligono, parcela, recinto)",
    "idx_parcelas_activa": "CREATE INDEX IF NOT EXISTS idx_parcelas_activa ON parcelas(activa)",
    "idx_cultivos_campana_id": "CREATE INDEX IF NOT EXISTS idx_cultivos_campana_id ON cultivos(campana_id)",
    "idx_cultivos_codigo_siex": "CREATE INDEX IF NOT EXISTS idx_cultivos_codigo_siex ON cultivos(codigo_siex)",
    "idx_cultivos_activo": "CREATE INDEX IF NOT EXISTS idx_cultivos_activo ON cultivos(activo)",
    "idx_cultivo_parcelas_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_cultivo_parcelas_cultivo_id ON cultivo_parcelas(cultivo_id)",
    "idx_cultivo_parcelas_parcela_id": "CREATE INDEX IF NOT EXISTS idx_cultivo_parcelas_parcela_id ON cultivo_parcelas(parcela_id)",
    "idx_clientes_nif": "CREATE INDEX IF NOT EXISTS idx_clientes_nif ON clientes(nif)",
    "idx_clientes_activo": "CREATE INDEX IF NOT EXISTS idx_clientes_activo ON clientes(activo)",
    "idx_proveedores_nif": "CREATE INDEX IF NOT EXISTS idx_proveedores_nif ON proveedores(nif)",
    "idx_proveedores_activo": "CREATE INDEX IF NOT EXISTS idx_proveedores_activo ON proveedores(activo)",
    "idx_productos_fito_numero_registro": "CREATE INDEX IF NOT EXISTS idx_productos_fito_numero_registro ON productos_fito(numero_registro)",
    "idx_productos_fito_activo": "CREATE INDEX IF NOT EXISTS idx_productos_fito_activo ON productos_fito(activo)",
    "idx_personas_nif": "CREATE INDEX IF NOT EXISTS idx_personas_nif ON personas(nif)",
    "idx_personas_rol": "CREATE INDEX IF NOT EXISTS idx_personas_rol ON personas(rol)",
    "idx_personas_activo": "CREATE INDEX IF NOT EXISTS idx_personas_activo ON personas(activo)",
    "idx_maquinaria_numero_roma": "CREATE INDEX IF NOT EXISTS idx_maquinaria_numero_roma ON maquinaria(numero_roma)",
    "idx_maquinaria_activa": "CREATE INDEX IF NOT EXISTS idx_maquinaria_activa ON maquinaria(activa)",
    "idx_equipos_aplicacion_activo": "CREATE INDEX IF NOT EXISTS idx_equipos_aplicacion_activo ON equipos_aplicacion(activo)",
    "idx_siex_items_catalogo_id": "CREATE INDEX IF NOT EXISTS idx_siex_items_catalogo_id ON siex_catalogos_items(catalogo_id)",
    "idx_siex_items_codigo": "CREATE INDEX IF NOT EXISTS idx_siex_items_codigo ON siex_catalogos_items(codigo)",
    "idx_siex_items_activo": "CREATE INDEX IF NOT EXISTS idx_siex_items_activo ON siex_catalogos_items(activo)",
    "idx_tratamientos_campana_id": "CREATE INDEX IF NOT EXISTS idx_tratamientos_campana_id ON tratamientos(campana_id)",
    "idx_tratamientos_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_tratamientos_cultivo_id ON tratamientos(cultivo_id)",
    "idx_tratamientos_producto_id": "CREATE INDEX IF NOT EXISTS idx_tratamientos_producto_id ON tratamientos(producto_id)",
    "idx_tratamientos_aplicador_id": "CREATE INDEX IF NOT EXISTS idx_tratamientos_aplicador_id ON tratamientos(aplicador_id)",
    "idx_tratamientos_equipo_aplicacion_id": "CREATE INDEX IF NOT EXISTS idx_tratamientos_equipo_aplicacion_id ON tratamientos(equipo_aplicacion_id)",
    "idx_tratamientos_fechas": "CREATE INDEX IF NOT EXISTS idx_tratamientos_fechas ON tratamientos(fecha_inicio, fecha_fin)",
    "idx_tratamiento_parcelas_tratamiento_id": "CREATE INDEX IF NOT EXISTS idx_tratamiento_parcelas_tratamiento_id ON tratamiento_parcelas(tratamiento_id)",
    "idx_tratamiento_parcelas_parcela_id": "CREATE INDEX IF NOT EXISTS idx_tratamiento_parcelas_parcela_id ON tratamiento_parcelas(parcela_id)",
    "idx_tratamiento_cultivos_tratamiento_id": "CREATE INDEX IF NOT EXISTS idx_tratamiento_cultivos_tratamiento_id ON tratamiento_cultivos(tratamiento_id)",
    "idx_tratamiento_cultivos_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_tratamiento_cultivos_cultivo_id ON tratamiento_cultivos(cultivo_id)",
    "idx_tratamiento_cultivos_parcela_id": "CREATE INDEX IF NOT EXISTS idx_tratamiento_cultivos_parcela_id ON tratamiento_cultivos(parcela_id)",
    "idx_tratamientos_documentos_tratamiento_id": "CREATE INDEX IF NOT EXISTS idx_tratamientos_documentos_tratamiento_id ON tratamientos_documentos(tratamiento_id)",
    "idx_fertilizaciones_campana_id": "CREATE INDEX IF NOT EXISTS idx_fertilizaciones_campana_id ON fertilizaciones(campana_id)",
    "idx_fertilizaciones_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_fertilizaciones_cultivo_id ON fertilizaciones(cultivo_id)",
    "idx_fertilizaciones_fecha": "CREATE INDEX IF NOT EXISTS idx_fertilizaciones_fecha ON fertilizaciones(fecha)",
    "idx_fertilizacion_parcelas_fertilizacion_id": "CREATE INDEX IF NOT EXISTS idx_fertilizacion_parcelas_fertilizacion_id ON fertilizacion_parcelas(fertilizacion_id)",
    "idx_fertilizacion_parcelas_parcela_id": "CREATE INDEX IF NOT EXISTS idx_fertilizacion_parcelas_parcela_id ON fertilizacion_parcelas(parcela_id)",
    "idx_fertilizacion_cultivos_fertilizacion_id": "CREATE INDEX IF NOT EXISTS idx_fertilizacion_cultivos_fertilizacion_id ON fertilizacion_cultivos(fertilizacion_id)",
    "idx_fertilizacion_cultivos_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_fertilizacion_cultivos_cultivo_id ON fertilizacion_cultivos(cultivo_id)",
    "idx_fertilizacion_cultivos_parcela_id": "CREATE INDEX IF NOT EXISTS idx_fertilizacion_cultivos_parcela_id ON fertilizacion_cultivos(parcela_id)",
    "idx_practicas_culturales_campana_id": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_campana_id ON practicas_culturales(campana_id)",
    "idx_practicas_culturales_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_cultivo_id ON practicas_culturales(cultivo_id)",
    "idx_practicas_culturales_fecha": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_fecha ON practicas_culturales(fecha)",
    "idx_practicas_culturales_maquinaria_id": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_maquinaria_id ON practicas_culturales(maquinaria_id)",
    "idx_practicas_culturales_proveedor_id": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_proveedor_id ON practicas_culturales(proveedor_id)",
    "idx_practicas_culturales_parcelas_practica_id": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_parcelas_practica_id ON practicas_culturales_parcelas(practica_id)",
    "idx_practicas_culturales_parcelas_parcela_id": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_parcelas_parcela_id ON practicas_culturales_parcelas(parcela_id)",
    "idx_practicas_culturales_cultivos_practica_id": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_cultivos_practica_id ON practicas_culturales_cultivos(practica_id)",
    "idx_practicas_culturales_cultivos_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_cultivos_cultivo_id ON practicas_culturales_cultivos(cultivo_id)",
    "idx_practicas_culturales_cultivos_parcela_id": "CREATE INDEX IF NOT EXISTS idx_practicas_culturales_cultivos_parcela_id ON practicas_culturales_cultivos(parcela_id)",
    "idx_cosecha_campana_id": "CREATE INDEX IF NOT EXISTS idx_cosecha_campana_id ON cosecha(campana_id)",
    "idx_cosecha_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_cosecha_cultivo_id ON cosecha(cultivo_id)",
    "idx_cosecha_cliente_id": "CREATE INDEX IF NOT EXISTS idx_cosecha_cliente_id ON cosecha(cliente_id)",
    "idx_cosecha_fecha": "CREATE INDEX IF NOT EXISTS idx_cosecha_fecha ON cosecha(fecha)",
    "idx_cosecha_parcelas_cosecha_id": "CREATE INDEX IF NOT EXISTS idx_cosecha_parcelas_cosecha_id ON cosecha_parcelas(cosecha_id)",
    "idx_cosecha_parcelas_parcela_id": "CREATE INDEX IF NOT EXISTS idx_cosecha_parcelas_parcela_id ON cosecha_parcelas(parcela_id)",
    "idx_cosecha_cultivos_cosecha_id": "CREATE INDEX IF NOT EXISTS idx_cosecha_cultivos_cosecha_id ON cosecha_cultivos(cosecha_id)",
    "idx_cosecha_cultivos_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_cosecha_cultivos_cultivo_id ON cosecha_cultivos(cultivo_id)",
    "idx_cosecha_cultivos_parcela_id": "CREATE INDEX IF NOT EXISTS idx_cosecha_cultivos_parcela_id ON cosecha_cultivos(parcela_id)",
    "idx_movimientos_economicos_campana_id": "CREATE INDEX IF NOT EXISTS idx_movimientos_economicos_campana_id ON movimientos_economicos(campana_id)",
    "idx_movimientos_economicos_cultivo_id": "CREATE INDEX IF NOT EXISTS idx_movimientos_economicos_cultivo_id ON movimientos_economicos(cultivo_id)",
    "idx_movimientos_economicos_cliente_id": "CREATE INDEX IF NOT EXISTS idx_movimientos_economicos_cliente_id ON movimientos_economicos(cliente_id)",
    "idx_movimientos_economicos_proveedor_id": "CREATE INDEX IF NOT EXISTS idx_movimientos_economicos_proveedor_id ON movimientos_economicos(proveedor_id)",
    "idx_movimientos_economicos_fecha": "CREATE INDEX IF NOT EXISTS idx_movimientos_economicos_fecha ON movimientos_economicos(fecha)",
    "idx_movimientos_economicos_pendiente": "CREATE INDEX IF NOT EXISTS idx_movimientos_economicos_pendiente ON movimientos_economicos(pendiente)",
    "idx_movimientos_lineas_iva_movimiento_id": "CREATE INDEX IF NOT EXISTS idx_movimientos_lineas_iva_movimiento_id ON movimientos_economicos_lineas_iva(movimiento_id)",
    "idx_movimientos_documentos_movimiento_id": "CREATE INDEX IF NOT EXISTS idx_movimientos_documentos_movimiento_id ON movimientos_economicos_documentos(movimiento_id)",
}


def crear_tablas_v7(conn):

    conn.execute("PRAGMA foreign_keys=ON")

    for sql in TABLE_DEFINITIONS:

        conn.execute(sql)

    asegurar_ampliaciones_v8_0_1(conn)
    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")


def crear_indices_v7(conn):

    conn.execute("PRAGMA foreign_keys=ON")

    for sql in INDEX_DEFINITIONS.values():

        conn.execute(sql)


def _nombres_tablas(conn):

    filas = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return {fila[0] for fila in filas}


def _nombres_indices(conn):

    filas = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='index'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return {fila[0] for fila in filas}


def _columnas(conn, tabla):

    if tabla not in _nombres_tablas(conn):

        return set()

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def asegurar_ampliaciones_v7_13(conn):

    conn.execute("PRAGMA foreign_keys=ON")

    for tabla, columnas_nuevas in V7_13_COLUMN_ADDITIONS.items():

        if tabla not in _nombres_tablas(conn):

            continue

        columnas_reales = _columnas(conn, tabla)

        for columna, definicion in columnas_nuevas.items():

            if columna in columnas_reales:

                continue

            conn.execute(
                f'ALTER TABLE "{tabla}" ADD COLUMN "{columna}" {definicion}'
            )
            columnas_reales.add(columna)

    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")


def asegurar_ampliaciones_v7_16(conn):

    asegurar_ampliaciones_v7_13(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cosecha_cultivos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cosecha_id INTEGER NOT NULL,
            cultivo_id INTEGER NOT NULL,
            parcela_id INTEGER,
            superficie REAL,
            observaciones TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(cosecha_id) REFERENCES cosecha(id) ON DELETE CASCADE,
            FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
            FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
            UNIQUE(cosecha_id, cultivo_id, parcela_id)
        )
        """
    )

    for indice in (
        "idx_cosecha_cultivos_cosecha_id",
        "idx_cosecha_cultivos_cultivo_id",
        "idx_cosecha_cultivos_parcela_id",
    ):

        conn.execute(INDEX_DEFINITIONS[indice])

    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")


def asegurar_ampliaciones_v7_17(conn):

    asegurar_ampliaciones_v7_16(conn)
    conn.execute("PRAGMA foreign_keys=ON")

    for tabla, columnas_nuevas in V7_17_COLUMN_ADDITIONS.items():

        if tabla not in _nombres_tablas(conn):

            continue

        columnas_reales = _columnas(conn, tabla)

        for columna, definicion in columnas_nuevas.items():

            if columna in columnas_reales:

                continue

            conn.execute(
                f'ALTER TABLE "{tabla}" ADD COLUMN "{columna}" {definicion}'
            )
            columnas_reales.add(columna)

    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")


def asegurar_ampliaciones_v8_0_1(conn):

    """Asegura las tablas puente multicultivo añadidas sobre la base v7 limpia.

    CuadernoPro v8 sigue usando internamente el esquema base v7 limpio; esta
    funcion solo añade las tablas idempotentes necesarias para actuaciones
    multicultivo en v8.0.1.
    """

    asegurar_ampliaciones_v7_17(conn)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tratamiento_cultivos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tratamiento_id INTEGER NOT NULL,
            cultivo_id INTEGER NOT NULL,
            parcela_id INTEGER,
            superficie REAL,
            observaciones TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(tratamiento_id) REFERENCES tratamientos(id)
            ON DELETE CASCADE,
            FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
            FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
            UNIQUE(tratamiento_id, cultivo_id, parcela_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fertilizacion_cultivos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fertilizacion_id INTEGER NOT NULL,
            cultivo_id INTEGER NOT NULL,
            parcela_id INTEGER,
            superficie REAL,
            observaciones TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(fertilizacion_id) REFERENCES fertilizaciones(id)
            ON DELETE CASCADE,
            FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
            FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
            UNIQUE(fertilizacion_id, cultivo_id, parcela_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS practicas_culturales_cultivos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            practica_id INTEGER NOT NULL,
            cultivo_id INTEGER NOT NULL,
            parcela_id INTEGER,
            superficie REAL,
            observaciones TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(practica_id) REFERENCES practicas_culturales(id)
            ON DELETE CASCADE,
            FOREIGN KEY(cultivo_id) REFERENCES cultivos(id),
            FOREIGN KEY(parcela_id) REFERENCES parcelas(id),
            UNIQUE(practica_id, cultivo_id, parcela_id)
        )
        """
    )

    for indice in (
        "idx_tratamiento_cultivos_tratamiento_id",
        "idx_tratamiento_cultivos_cultivo_id",
        "idx_tratamiento_cultivos_parcela_id",
        "idx_fertilizacion_cultivos_fertilizacion_id",
        "idx_fertilizacion_cultivos_cultivo_id",
        "idx_fertilizacion_cultivos_parcela_id",
        "idx_practicas_culturales_cultivos_practica_id",
        "idx_practicas_culturales_cultivos_cultivo_id",
        "idx_practicas_culturales_cultivos_parcela_id",
    ):

        conn.execute(INDEX_DEFINITIONS[indice])

    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")


def validar_esquema_v7(conn):

    conn.execute("PRAGMA foreign_keys=ON")

    tablas = _nombres_tablas(conn)
    indices = _nombres_indices(conn)
    tablas_esperadas = set(EXPECTED_COLUMNS)
    indices_esperados = set(INDEX_DEFINITIONS)
    faltan_tablas = sorted(tablas_esperadas - tablas)
    tablas_no_esperadas = sorted(tablas - tablas_esperadas)
    faltan_columnas = []
    legacy_detectadas = []

    for tabla, columnas_esperadas in EXPECTED_COLUMNS.items():

        columnas_reales = _columnas(conn, tabla)

        if not columnas_reales:

            continue

        for columna in columnas_esperadas:

            if columna not in columnas_reales:

                faltan_columnas.append(f"{tabla}.{columna}")

        for columna in FORBIDDEN_COLUMNS.get(tabla, ()):

            if columna in columnas_reales:

                legacy_detectadas.append(f"{tabla}.{columna}")

    faltan_indices = sorted(indices_esperados - indices)
    errores_fk = [
        ".".join(str(valor) for valor in fila)
        for fila in conn.execute("PRAGMA foreign_key_check").fetchall()
    ]
    user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    errores = []

    for tabla in faltan_tablas:

        errores.append(f"Falta tabla {tabla}")

    for columna in faltan_columnas:

        errores.append(f"Falta columna {columna}")

    for columna in legacy_detectadas:

        errores.append(f"Columna legacy prohibida {columna}")

    for indice in faltan_indices:

        errores.append(f"Falta indice {indice}")

    for error_fk in errores_fk:

        errores.append(f"Error de clave foranea {error_fk}")

    if user_version != SCHEMA_VERSION:

        errores.append(
            f"PRAGMA user_version={user_version}; esperado {SCHEMA_VERSION}"
        )

    return {
        "ok": not errores,
        "schema_version": SCHEMA_VERSION,
        "user_version": user_version,
        "table_count": len(tablas),
        "tables": sorted(tablas),
        "principal_tables": list(PRINCIPAL_TABLES),
        "missing_tables": faltan_tablas,
        "unexpected_tables": tablas_no_esperadas,
        "missing_columns": sorted(faltan_columnas),
        "legacy_columns": sorted(legacy_detectadas),
        "missing_indexes": faltan_indices,
        "foreign_key_errors": errores_fk,
        "errors": errores,
    }


def crear_base_v7(ruta_db, sobrescribir=False):

    ruta = Path(ruta_db).expanduser().resolve()
    ruta.parent.mkdir(parents=True, exist_ok=True)

    if ruta.exists():

        if not sobrescribir:

            raise FileExistsError(f"La base ya existe: {ruta}")

        ruta.unlink()

    conn = sqlite3.connect(ruta)

    try:

        crear_tablas_v7(conn)
        crear_indices_v7(conn)
        conn.commit()
        resultado = validar_esquema_v7(conn)

        if not resultado["ok"]:

            raise RuntimeError("; ".join(resultado["errors"]))

        return resultado

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()
