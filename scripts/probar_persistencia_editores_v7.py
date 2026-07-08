#!/usr/bin/env python3
from pathlib import Path
import os
import sqlite3
import sys
import traceback

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
DB_PERSISTENCIA = APP_ROOT / "runtime" / "v7" / "prueba_persistencia_v7.db"
EXPORTS_DIR = APP_ROOT / "runtime" / "v7" / "exports_persistencia"
DOCS_DIR = APP_ROOT / "runtime" / "v7" / "documentos_persistencia"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_PERSISTENCIA)

from core.db import leer  # noqa: E402
from core.schema_v7 import asegurar_ampliaciones_v8_0_1, crear_base_v7  # noqa: E402
import modules.cosecha as cosecha_mod  # noqa: E402
import modules.contabilidad as contabilidad_mod  # noqa: E402
import modules.explotacion as explotacion_mod  # noqa: E402
import modules.fertilizacion as fertilizacion_mod  # noqa: E402
import modules.maquinaria as maquinaria_mod  # noqa: E402
import modules.mapas as mapas_mod  # noqa: E402
import modules.practicas_culturales as practicas_mod  # noqa: E402
import modules.productos_fito as productos_mod  # noqa: E402
import modules.revision_siex as revision_siex  # noqa: E402
import modules.terceros as terceros_mod  # noqa: E402
import modules.tratamientos as tratamientos_mod  # noqa: E402
import services.cuadernopro_pdf as cuadernopro_pdf  # noqa: E402
import services.exportacion_siex as exportacion_siex  # noqa: E402


def _conectar():

    conn = sqlite3.connect(DB_PERSISTENCIA)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _leer_persistencia(sql, params=None):

    with _conectar() as conn:

        return pd.read_sql_query(sql, conn, params=params or ())


def _user_version(conn):

    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _columnas(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f'PRAGMA table_info("{tabla}")')
    }


def _fila(conn, tabla, registro_id):

    fila = conn.execute(
        f'SELECT * FROM "{tabla}" WHERE id=?',
        (int(registro_id),),
    ).fetchone()

    if fila is None:

        raise AssertionError(f"No existe {tabla}.id={registro_id}")

    return dict(fila)


def _filas(conn, sql, params=()):

    return [dict(fila) for fila in conn.execute(sql, params).fetchall()]


def _assert_igual(actual, esperado, campo):

    if actual != esperado:

        raise AssertionError(
            f"{campo}: esperado {esperado!r}, obtenido {actual!r}"
        )


def _assert_float(actual, esperado, campo):

    if abs(float(actual or 0) - float(esperado)) > 0.0001:

        raise AssertionError(
            f"{campo}: esperado {esperado!r}, obtenido {actual!r}"
        )


def _assert_no_vacio(valor, campo):

    if valor is None or str(valor).strip() == "":

        raise AssertionError(f"{campo} queda vacio")


def _limpiar_tablas(conn):

    tablas = [
        "movimientos_economicos_documentos",
        "movimientos_economicos_lineas_iva",
        "movimientos_economicos",
        "tratamientos_documentos",
        "tratamiento_cultivos",
        "tratamiento_parcelas",
        "tratamientos",
        "fertilizacion_cultivos",
        "fertilizacion_parcelas",
        "fertilizaciones",
        "practicas_culturales_cultivos",
        "practicas_culturales_parcelas",
        "practicas_culturales",
        "cosecha_cultivos",
        "cosecha_parcelas",
        "cosecha",
        "cultivo_parcelas",
        "cultivos",
        "parcelas",
        "productos_fito",
        "personas",
        "equipos_aplicacion",
        "maquinaria",
        "clientes",
        "proveedores",
        "campanas",
        "explotacion",
    ]

    for tabla in tablas:

        conn.execute(f'DELETE FROM "{tabla}"')


def _insertar_base_minima(conn):

    ahora = "2026-07-02T00:00:00"
    conn.execute(
        """
        INSERT INTO explotacion
        (nombre_explotacion,titular,nif,direccion,municipio,provincia,
         codigo_postal,telefono,email,identificador_oficial,
         tipo_identificador_oficial,registro_autonomico,tipo_explotacion,
         orientacion_productiva,fecha_alta,agricultor_activo,
         joven_agricultor,responsable,asesor,numero_asesor,
         observaciones,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Explotacion persistencia v7",
            "Titular Persistencia V7",
            "00000000P",
            "Camino Persistencia 1",
            "Jumilla",
            "Murcia",
            "30520",
            "600100000",
            "persistencia@example.com",
            "REGEPA-PERSIST-V7",
            "REGEPA",
            "REG-AUT-PERSIST-V7",
            "Agraria",
            "Frutos secos",
            "2026-01-01",
            1,
            0,
            "Responsable Persistencia",
            "Asesor Persistencia",
            "ASE-PERSIST-V7",
            "Explotacion base persistencia",
            ahora,
            ahora,
        ),
    )
    campana_anterior_id = conn.execute(
        """
        INSERT INTO campanas
        (nombre,fecha_inicio,fecha_fin,activa,estado,observaciones,
         created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            "2024/2025",
            "2024-10-01",
            "2025-09-30",
            0,
            "abierta",
            "Campana anterior persistencia",
            ahora,
            ahora,
        ),
    ).lastrowid
    campana_id = conn.execute(
        """
        INSERT INTO campanas
        (nombre,fecha_inicio,fecha_fin,activa,estado,observaciones,
         created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            "2025/2026",
            "2025-10-01",
            "2026-09-30",
            1,
            "abierta",
            "Campana persistencia",
            ahora,
            ahora,
        ),
    ).lastrowid
    cliente_id = conn.execute(
        """
        INSERT INTO clientes
        (nombre,nif,telefono,email,direccion,poblacion,provincia,
         codigo_postal,observaciones,activo,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Cliente persistencia",
            "B12000001",
            "600100001",
            "cliente-persistencia@example.com",
            "Calle Cliente 1",
            "Jumilla",
            "Murcia",
            "30520",
            "Cliente base",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    proveedor_id = conn.execute(
        """
        INSERT INTO proveedores
        (nombre,nif,telefono,email,direccion,poblacion,provincia,
         codigo_postal,actividad,observaciones,activo,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Proveedor persistencia",
            "B12000002",
            "600100002",
            "proveedor-persistencia@example.com",
            "Calle Proveedor 2",
            "Jumilla",
            "Murcia",
            "30520",
            "Servicios",
            "Proveedor base",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    parcela_id = conn.execute(
        """
        INSERT INTO parcelas
        (nombre,provincia_sigpac,municipio_sigpac,agregado_sigpac,
         zona_sigpac,poligono,parcela,recinto,superficie_sigpac,
         uso_sigpac,activa,observaciones,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Parcela persistencia",
            30,
            22,
            0,
            0,
            "10",
            "20",
            "30",
            2.5,
            "TA",
            1,
            "Parcela base",
            ahora,
            ahora,
        ),
    ).lastrowid
    cultivo_id = conn.execute(
        """
        INSERT INTO cultivos
        (campana_id,nombre,variedad,codigo_siex,superficie,ano_plantacion,
         marco_plantacion,numero_arboles,activo,observaciones,created_at,
         updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            campana_id,
            "Almendro persistencia",
            "Comuna",
            "104",
            2.5,
            2020,
            "7x7",
            510,
            1,
            "Cultivo base",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO cultivo_parcelas
        (cultivo_id,parcela_id,superficie,created_at,updated_at)
        VALUES (?,?,?,?,?)
        """,
        (cultivo_id, parcela_id, 2.5, ahora, ahora),
    )
    persona_id = conn.execute(
        """
        INSERT INTO personas
        (nombre,nif,telefono,email,rol,carnet_aplicador,observaciones,
         activo,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Aplicador persistencia",
            "12345678A",
            "600100003",
            "aplicador-persistencia@example.com",
            "Aplicador fitosanitario",
            "CAR-PERSIST-V7",
            "Aplicador base",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid

    conn.commit()

    return {
        "ahora": ahora,
        "campana_anterior_id": int(campana_anterior_id),
        "campana_id": int(campana_id),
        "cliente_id": int(cliente_id),
        "proveedor_id": int(proveedor_id),
        "parcela_id": int(parcela_id),
        "cultivo_id": int(cultivo_id),
        "persona_id": int(persona_id),
    }


def _preparar_base():

    with _conectar() as conn:

        asegurar_ampliaciones_v8_0_1(conn)

        if _user_version(conn) != 7:

            raise AssertionError("La base de persistencia no es user_version 7")

        _limpiar_tablas(conn)
        ctx = _insertar_base_minima(conn)
        conn.commit()
        return ctx


def _asegurar_base_prueba():

    if DB_PERSISTENCIA.exists():

        return

    crear_base_v7(DB_PERSISTENCIA, sobrescribir=True)


def _registrar(resultados, modulo, funcion):

    try:

        observaciones = funcion() or ""
        resultados.append((modulo, "OK", "OK", "OK", observaciones, ""))
        return True

    except Exception as exc:

        resultados.append(
            (
                modulo,
                "FALLO",
                "FALLO",
                "FALLO",
                "",
                f"{exc}\n{traceback.format_exc()}",
            )
        )
        return False


def _probar_explotacion(ctx):

    datos = explotacion_mod._leer_datos_explotacion()
    editado = datos.copy()
    editado.loc[0, "titular"] = "Titular Persistencia Editado"
    editado.loc[0, "nombre_explotacion"] = "Finca Persistencia Editada"
    editado.loc[0, "identificador_oficial_visual"] = "REGEPA-PERSIST-EDIT"
    editado.loc[0, "registro_autonomico"] = "REG-AUT-PERSIST-EDIT"
    editado.loc[0, "tipo_explotacion"] = "Agraria editada"
    editado.loc[0, "orientacion_productiva"] = "Almendro secano"
    editado.loc[0, "fecha_alta"] = pd.Timestamp("2026-02-01")
    editado.loc[0, "agricultor_activo"] = True
    editado.loc[0, "joven_agricultor"] = True
    editado.loc[0, "localidad"] = "Yecla"
    editado.loc[0, "provincia"] = "Murcia"
    editado.loc[0, "responsable_nombre"] = "Responsable Editado"
    editado.loc[0, "asesor_nombre"] = "Asesor Editado"
    editado.loc[0, "asesor_numero_registro"] = "ASE-PERSIST-EDIT"

    explotacion_mod._guardar_explotacion(
        datos,
        editado,
        list(editado.columns),
    )

    with _conectar() as conn:

        fila = conn.execute("SELECT * FROM explotacion LIMIT 1").fetchone()
        fila = dict(fila)
        _assert_igual(
            fila["nombre_explotacion"],
            "Finca Persistencia Editada",
            "nombre_explotacion",
        )
        _assert_igual(
            fila["identificador_oficial"],
            "REGEPA-PERSIST-EDIT",
            "identificador_oficial",
        )
        _assert_igual(fila["titular"], "Titular Persistencia Editado", "titular")
        _assert_igual(fila["municipio"], "Yecla", "municipio")
        _assert_igual(
            fila["registro_autonomico"],
            "REG-AUT-PERSIST-EDIT",
            "registro_autonomico",
        )
        _assert_igual(
            fila["tipo_explotacion"],
            "Agraria editada",
            "tipo_explotacion",
        )
        _assert_igual(
            fila["orientacion_productiva"],
            "Almendro secano",
            "orientacion_productiva",
        )
        _assert_igual(fila["fecha_alta"], "2026-02-01", "fecha_alta")
        _assert_igual(int(fila["agricultor_activo"]), 1, "agricultor_activo")
        _assert_igual(int(fila["joven_agricultor"]), 1, "joven_agricultor")
        _assert_igual(fila["responsable"], "Responsable Editado", "responsable")
        _assert_igual(fila["asesor"], "Asesor Editado", "asesor")

    return "Persistencia por helper de Explotacion OK"


def _probar_productos(ctx):

    producto_id = productos_mod._insertar_producto_fito(
        {
            "numero_registro": "REG-PERSIST-V7",
            "nombre": "Producto Persistencia",
            "materia_activa": "Materia inicial",
            "titular": "Titular producto",
            "uso_autorizado": "Almendro",
            "plazo_seguridad": "14",
            "observaciones": "Producto base",
            "activo": True,
        }
    )
    productos_mod._actualizar_producto_fito(
        producto_id,
        {
            "numero_registro": "REG-PERSIST-EDIT",
            "nombre": "Producto Persistencia Editado",
            "materia_activa": "Materia editada",
            "titular": "Titular producto",
            "uso_autorizado": "Almendro",
            "plazo_seguridad": "21",
            "observaciones": "Producto editado",
            "activo": False,
        },
    )

    with _conectar() as conn:

        fila = _fila(conn, "productos_fito", producto_id)
        _assert_igual(fila["numero_registro"], "REG-PERSIST-EDIT", "registro")
        _assert_igual(
            fila["nombre"],
            "Producto Persistencia Editado",
            "nombre producto",
        )
        _assert_igual(fila["materia_activa"], "Materia editada", "materia")
        _assert_igual(str(fila["plazo_seguridad"]), "21", "plazo seguridad")
        _assert_igual(int(fila["activo"]), 0, "activo")

    ctx["producto_id"] = producto_id
    return "Persistencia producto fito v7 OK"


def _probar_maquinaria_y_equipos(ctx):

    maquinaria_mod._insertar_maquinaria(
        {
            "nombre": "Tractor Persistencia",
            "tipo": "Tractor",
            "marca": "Marca inicial",
            "modelo": "Modelo inicial",
            "matricula": "MU-1111-A",
            "numero_roma": "ROMA-PERSIST-V7",
            "numero_serie": "SER-MAQ-PERSIST-V7",
            "fecha_compra": "2025-01-15",
            "horas_uso": 100.0,
            "observaciones": "Maquinaria base",
        }
    )

    with _conectar() as conn:

        maquinaria_id = conn.execute(
            """
            SELECT id
            FROM maquinaria
            WHERE numero_roma='ROMA-PERSIST-V7'
            """
        ).fetchone()[0]

    maquinaria_mod._actualizar_maquinaria(
        maquinaria_id,
        {
            "nombre": "Tractor Persistencia Editado",
            "tipo": "Tractor",
            "marca": "Marca editada",
            "modelo": "Modelo editado",
            "matricula": "MU-2222-B",
            "numero_roma": "ROMA-PERSIST-EDIT",
            "numero_serie": "SER-MAQ-PERSIST-EDIT",
            "fecha_compra": "2025-02-15",
            "horas_uso": 150.5,
            "observaciones": "Maquinaria editada",
        },
    )
    explotacion_mod._insertar_equipo(
        {
            "nombre": "Equipo Persistencia",
            "tipo": "Pulverizador",
            "marca": "Marca equipo",
            "modelo": "Modelo equipo",
            "matricula": "MU-3333-C",
            "numero_roma": "ROMA-EQ-PERSIST-V7",
            "numero_serie": "SER-PERSIST-V7",
            "fecha_adquisicion": "2025-03-01",
            "fecha_ultima_inspeccion": "2026-01-15",
            "fecha_proxima_inspeccion": "2027-01-15",
            "capacidad_litros": 600.0,
            "observaciones": "Equipo base",
        }
    )

    with _conectar() as conn:

        equipo_id = conn.execute(
            """
            SELECT id
            FROM equipos_aplicacion
            WHERE numero_serie='SER-PERSIST-V7'
            """
        ).fetchone()[0]
        explotacion_mod._actualizar_equipo(
            conn,
            {
                "id": equipo_id,
                "nombre": "Equipo Persistencia Editado",
                "tipo": "Pulverizador",
                "marca": "Marca equipo editada",
                "modelo": "Modelo equipo editado",
                "matricula": "MU-4444-D",
                "numero_roma": "ROMA-EQ-PERSIST-EDIT",
                "numero_serie": "SER-PERSIST-EDIT",
                "observaciones": "Equipo editado",
            },
            {
                "fecha_adquisicion": "2025-04-01",
                "fecha_ultima_inspeccion": "2026-02-01",
                "fecha_proxima_inspeccion": "2027-02-01",
            },
            750.0,
        )
        conn.commit()
        maquinaria = _fila(conn, "maquinaria", maquinaria_id)
        equipo = _fila(conn, "equipos_aplicacion", equipo_id)

    _assert_igual(
        maquinaria["descripcion"],
        "Tractor Persistencia Editado",
        "descripcion maquinaria",
    )
    _assert_igual(maquinaria["matricula"], "MU-2222-B", "matricula")
    _assert_igual(maquinaria["numero_roma"], "ROMA-PERSIST-EDIT", "numero_roma")
    _assert_igual(
        maquinaria["numero_serie"],
        "SER-MAQ-PERSIST-EDIT",
        "numero_serie maquinaria",
    )
    _assert_igual(maquinaria["fecha_compra"], "2025-02-15", "fecha_compra")
    _assert_float(maquinaria["horas_uso"], 150.5, "horas_uso")
    _assert_igual(equipo["matricula"], "MU-4444-D", "matricula equipo")
    _assert_igual(
        equipo["numero_roma"],
        "ROMA-EQ-PERSIST-EDIT",
        "numero_roma equipo",
    )
    _assert_igual(equipo["numero_serie"], "SER-PERSIST-EDIT", "numero_serie")
    _assert_igual(
        equipo["fecha_adquisicion"],
        "2025-04-01",
        "fecha_adquisicion",
    )
    _assert_float(equipo["capacidad_litros"], 750.0, "capacidad_litros")
    _assert_igual(equipo["fecha_revision"], "2026-02-01", "fecha_revision")
    _assert_igual(
        equipo["fecha_proxima_revision"],
        "2027-02-01",
        "fecha_proxima_revision",
    )

    ctx["maquinaria_id"] = maquinaria_id
    ctx["equipo_id"] = equipo_id
    return "Maquinaria y equipo persistidos"


def _probar_tratamientos(ctx):

    with _conectar() as conn:

        tratamiento_id = tratamientos_mod._insertar_tratamiento_compatible(
            conn,
            {
                "campana_id": ctx["campana_id"],
                "cultivo_id": ctx["cultivo_id"],
                "fecha_inicio": "2026-03-01",
                "fecha_fin": "2026-03-01",
                "producto_id": ctx["producto_id"],
                "aplicador_id": ctx["persona_id"],
                "equipo_aplicacion_id": ctx["equipo_id"],
                "plaga_motivo": "Repilo",
                "dosis": "1 l/ha",
                "caldo": 250.0,
                "superficie_tratada": 2.5,
                "plazo_seguridad": "21",
                "eficacia": "B",
                "observaciones": "Tratamiento base",
            },
            parcelas=[{"parcela_id": ctx["parcela_id"], "superficie": 2.5}],
        )
        tratamientos_mod._actualizar_tratamiento_compatible(
            conn,
            tratamiento_id,
            {
                "fecha_fin": "2026-03-05",
                "dosis": "1.5 l/ha",
                "eficacia": "R",
                "observaciones": "Tratamiento editado",
            },
        )
        conn.commit()
        fila = _fila(conn, "tratamientos", tratamiento_id)
        parcelas = _filas(
            conn,
            """
            SELECT parcela_id,superficie
            FROM tratamiento_parcelas
            WHERE tratamiento_id=?
            """,
            (tratamiento_id,),
        )

    _assert_igual(fila["fecha_inicio"], "2026-03-01", "fecha_inicio")
    _assert_igual(fila["fecha_fin"], "2026-03-05", "fecha_fin")
    _assert_igual(fila["dosis"], "1.5 l/ha", "dosis")
    _assert_igual(fila["eficacia"], "R", "eficacia")
    _assert_igual(fila["producto_id"], ctx["producto_id"], "producto_id")
    _assert_igual(fila["cultivo_id"], ctx["cultivo_id"], "cultivo_id")
    _assert_igual(fila["aplicador_id"], ctx["persona_id"], "aplicador_id")
    _assert_igual(fila["equipo_aplicacion_id"], ctx["equipo_id"], "equipo_id")
    _assert_igual(len(parcelas), 1, "tratamiento_parcelas")
    _assert_igual(parcelas[0]["parcela_id"], ctx["parcela_id"], "parcela_id")

    ctx["tratamiento_id"] = tratamiento_id
    return "Tratamiento y puente tratamiento_parcelas OK"


def _probar_fertilizacion(ctx):

    with _conectar() as conn:

        fertilizacion_id = fertilizacion_mod._insertar_fertilizacion_compatible(
            conn,
            {
                "campana_id": ctx["campana_id"],
                "cultivo_id": ctx["cultivo_id"],
                "fecha": "2026-02-01",
                "producto": "Abono inicial",
                "tipo_fertilizante": "Mineral",
                "cantidad": 120.0,
                "unidad": "kg",
                "unidad_normalizada": "kg",
                "superficie": 2.5,
                "codigo_actuacion_siex": "FERT-PERSIST",
                "observaciones": "Fertilizacion base",
            },
            parcelas_ids=[ctx["parcela_id"]],
        )
        fertilizacion_mod._actualizar_fertilizacion_compatible(
            conn,
            fertilizacion_id,
            {
                "fecha": "2026-02-10",
                "producto": "Abono editado",
                "tipo_fertilizante": "Organico",
                "cantidad": 150.0,
                "unidad": "kg",
                "unidad_normalizada": "kg",
                "observaciones": "Fertilizacion editada",
            },
        )
        conn.commit()
        fila = _fila(conn, "fertilizaciones", fertilizacion_id)
        parcelas = _filas(
            conn,
            """
            SELECT parcela_id
            FROM fertilizacion_parcelas
            WHERE fertilizacion_id=?
            """,
            (fertilizacion_id,),
        )

    _assert_igual(fila["fecha"], "2026-02-10", "fecha fertilizacion")
    _assert_igual(fila["producto"], "Abono editado", "producto fertilizacion")
    _assert_float(fila["cantidad"], 150.0, "cantidad fertilizacion")
    _assert_igual(fila["cultivo_id"], ctx["cultivo_id"], "cultivo fertilizacion")
    _assert_igual(len(parcelas), 1, "fertilizacion_parcelas")
    _assert_igual(parcelas[0]["parcela_id"], ctx["parcela_id"], "parcela fert")

    ctx["fertilizacion_id"] = fertilizacion_id
    return "Fertilizacion y puente fertilizacion_parcelas OK"


def _probar_practicas(ctx):

    with _conectar() as conn:

        practica_id = practicas_mod._insertar_practica_compatible(
            conn,
            {
                "campana_id": ctx["campana_id"],
                "cultivo_id": ctx["cultivo_id"],
                "fecha": "2026-01-20",
                "labor": "Poda",
                "codigo_actuacion_siex": "PRAC-PERSIST",
                "superficie": 2.5,
                "maquinaria_id": ctx["maquinaria_id"],
                "proveedor_id": ctx["proveedor_id"],
                "observaciones": "Practica base",
            },
            parcelas_ids=[ctx["parcela_id"]],
        )
        practicas_mod._actualizar_practica_compatible(
            conn,
            practica_id,
            {
                "fecha": "2026-01-25",
                "labor": "Poda editada",
                "superficie": 2.25,
                "observaciones": "Practica editada",
            },
        )
        conn.commit()
        fila = _fila(conn, "practicas_culturales", practica_id)
        parcelas = _filas(
            conn,
            """
            SELECT parcela_id
            FROM practicas_culturales_parcelas
            WHERE practica_id=?
            """,
            (practica_id,),
        )

    _assert_igual(fila["fecha"], "2026-01-25", "fecha practica")
    _assert_igual(fila["labor"], "Poda editada", "labor")
    _assert_float(fila["superficie"], 2.25, "superficie practica")
    _assert_igual(fila["cultivo_id"], ctx["cultivo_id"], "cultivo practica")
    _assert_igual(fila["maquinaria_id"], ctx["maquinaria_id"], "maquinaria")
    _assert_igual(fila["proveedor_id"], ctx["proveedor_id"], "proveedor")
    _assert_igual(len(parcelas), 1, "practicas_culturales_parcelas")

    ctx["practica_id"] = practica_id
    return "Practica y puente practicas_culturales_parcelas OK"


def _probar_cosecha(ctx):

    with _conectar() as conn:

        cosecha_id = cosecha_mod._insertar_cosecha_compatible(
            conn,
            {
                "campana_id": ctx["campana_id"],
                "cultivo_id": ctx["cultivo_id"],
                "fecha": "2026-08-20",
                "cantidad": 1000.0,
                "unidad": "kg",
                "destino": "Venta",
                "cliente_id": ctx["cliente_id"],
                "precio": 2.5,
                "observaciones": "Cosecha base",
            },
            parcelas_ids=[ctx["parcela_id"]],
            detalles_cultivos=[
                {
                    "cultivo_id": ctx["cultivo_id"],
                    "parcela_id": ctx["parcela_id"],
                    "superficie": 2.25,
                }
            ],
        )
        cosecha_mod._actualizar_cosecha_compatible(
            conn,
            cosecha_id,
            {
                "fecha": "2026-08-25",
                "cantidad": 1250.0,
                "unidad": "kg",
                "destino": "Venta editada",
                "observaciones": "Cosecha editada",
            },
        )
        conn.commit()
        fila = _fila(conn, "cosecha", cosecha_id)
        parcelas = _filas(
            conn,
            """
            SELECT parcela_id
            FROM cosecha_parcelas
            WHERE cosecha_id=?
            """,
            (cosecha_id,),
        )
        detalles = _filas(
            conn,
            """
            SELECT cultivo_id, parcela_id, superficie
            FROM cosecha_cultivos
            WHERE cosecha_id=?
            """,
            (cosecha_id,),
        )

    _assert_igual(fila["fecha"], "2026-08-25", "fecha cosecha")
    _assert_float(fila["cantidad"], 1250.0, "cantidad cosecha")
    _assert_igual(fila["unidad"], "kg", "unidad cosecha")
    _assert_igual(fila["cultivo_id"], ctx["cultivo_id"], "cultivo cosecha")
    _assert_igual(fila["cliente_id"], ctx["cliente_id"], "cliente cosecha")
    _assert_igual(len(parcelas), 1, "cosecha_parcelas")
    _assert_igual(len(detalles), 1, "cosecha_cultivos")
    _assert_igual(detalles[0]["cultivo_id"], ctx["cultivo_id"], "detalle cultivo")

    ctx["cosecha_id"] = cosecha_id
    return "Cosecha y puentes cosecha_parcelas/cosecha_cultivos OK"


def _probar_contabilidad(ctx):

    with _conectar() as conn:

        ingreso_id = contabilidad_mod._insertar_movimiento_compatible(
            conn,
            {
                "campana_id": ctx["campana_id"],
                "cultivo_id": ctx["cultivo_id"],
                "fecha": "2026-09-01",
                "tipo": "Ingreso",
                "categoria": "Venta de cosecha",
                "concepto": "Ingreso base",
                "numero_factura": "I-PERSIST",
                "cliente_id": ctx["cliente_id"],
                "base_imponible": 1000.0,
                "iva": 100.0,
                "retencion": 0.0,
                "total": 1100.0,
                "pagado": False,
                "observaciones": "Ingreso base",
            },
        )
        gasto_id = contabilidad_mod._insertar_movimiento_compatible(
            conn,
            {
                "campana_id": ctx["campana_id"],
                "cultivo_id": ctx["cultivo_id"],
                "fecha": "2026-04-01",
                "tipo": "Gasto",
                "categoria": "Fitosanitarios",
                "concepto": "Gasto base",
                "numero_factura": "G-PERSIST",
                "proveedor_id": ctx["proveedor_id"],
                "base_imponible": 300.0,
                "iva": 63.0,
                "retencion": 0.0,
                "total": 363.0,
                "pagado": False,
                "observaciones": "Gasto base",
            },
        )
        contabilidad_mod._actualizar_movimiento_compatible(
            conn,
            ingreso_id,
            {
                "tipo": "Ingreso",
                "concepto": "Ingreso editado",
                "cliente_id": ctx["cliente_id"],
                "base_imponible": 1200.0,
                "iva": 120.0,
                "retencion": 0.0,
                "total": 1320.0,
                "pagado": True,
            },
        )
        contabilidad_mod._actualizar_movimiento_compatible(
            conn,
            gasto_id,
            {
                "tipo": "Gasto",
                "concepto": "Gasto editado",
                "proveedor_id": ctx["proveedor_id"],
                "base_imponible": 400.0,
                "iva": 84.0,
                "retencion": 0.0,
                "total": 484.0,
                "pagado": True,
            },
        )
        resolucion_antigua = (
            contabilidad_mod._resolver_campana_movimiento_por_fecha(
                "2025-03-15",
                ctx["campana_id"],
                conn=conn,
            )
        )
        movimiento_antiguo_id = contabilidad_mod._insertar_movimiento_compatible(
            conn,
            {
                "campana_id": resolucion_antigua["campana_id"],
                "cultivo_id": None,
                "fecha": "2025-03-15",
                "tipo": "Ingreso",
                "categoria": "Venta de cosecha",
                "concepto": "Ingreso campaña anterior",
                "numero_factura": "I-PERSIST-ANT",
                "cliente_id": ctx["cliente_id"],
                "base_imponible": 100.0,
                "iva": 0.0,
                "retencion": 0.0,
                "total": 100.0,
                "pagado": True,
                "observaciones": "Movimiento antiguo por fecha",
            },
        )
        conn.commit()
        ingreso = _fila(conn, "movimientos_economicos", ingreso_id)
        gasto = _fila(conn, "movimientos_economicos", gasto_id)
        movimiento_antiguo = _fila(
            conn,
            "movimientos_economicos",
            movimiento_antiguo_id,
        )

    _assert_igual(ingreso["concepto"], "Ingreso editado", "concepto ingreso")
    _assert_float(ingreso["base_imponible"], 1200.0, "base ingreso")
    _assert_float(ingreso["iva"], 120.0, "iva ingreso")
    _assert_float(ingreso["total"], 1320.0, "total ingreso")
    _assert_igual(ingreso["cliente_id"], ctx["cliente_id"], "cliente ingreso")
    _assert_igual(ingreso["cultivo_id"], ctx["cultivo_id"], "cultivo ingreso")
    _assert_igual(ingreso["campana_id"], ctx["campana_id"], "campana ingreso")
    _assert_igual(int(ingreso["pendiente"]), 0, "pendiente ingreso")
    _assert_igual(gasto["concepto"], "Gasto editado", "concepto gasto")
    _assert_igual(gasto["proveedor_id"], ctx["proveedor_id"], "proveedor gasto")
    _assert_float(gasto["total"], 484.0, "total gasto")
    _assert_igual(int(gasto["pendiente"]), 0, "pendiente gasto")
    _assert_igual(
        resolucion_antigua["campana_id"],
        ctx["campana_anterior_id"],
        "resolucion campaña movimiento antiguo",
    )
    _assert_igual(
        movimiento_antiguo["campana_id"],
        ctx["campana_anterior_id"],
        "campaña guardada movimiento antiguo",
    )

    ctx["ingreso_id"] = ingreso_id
    ctx["gasto_id"] = gasto_id
    ctx["movimiento_antiguo_id"] = movimiento_antiguo_id
    return "Movimientos, terceros, IVA, totales y campaña por fecha OK"


def _probar_mapas_sigpac(ctx):

    estado = mapas_mod._leer_estado_geometrias()
    parcelas = mapas_mod._leer_parcelas_mapa()
    cultivos = mapas_mod._leer_cultivos_mapa()

    if estado.empty:

        raise AssertionError("Mapas no recupera parcelas para diagnostico")

    columnas_necesarias = {
        "id",
        "sigpac_geojson",
        "sigpac_geojson_estado",
    }
    faltantes = columnas_necesarias - set(estado.columns)

    if faltantes:

        raise AssertionError(
            "Mapas no devuelve columnas normalizadas: "
            + ", ".join(sorted(faltantes))
        )

    fila = estado[estado["id"].astype(int) == int(ctx["parcela_id"])]

    if fila.empty:

        raise AssertionError("Mapas no recupera la parcela de prueba")

    _assert_igual(
        fila.iloc[0]["sigpac_geojson_estado"],
        "Sin geometría",
        "estado geometria derivado",
    )
    _assert_igual(
        int(parcelas.iloc[0]["id"]),
        int(ctx["parcela_id"]),
        "parcela mapa",
    )
    _assert_igual(
        int(cultivos.iloc[0]["parcela_id"]),
        int(ctx["parcela_id"]),
        "cultivo_parcelas mapa",
    )
    return "Mapas deriva estado SIGPAC sin columna legacy"


def _probar_terceros(ctx):

    terceros_mod._guardar_nuevo(
        "clientes",
        {
            "nombre": "Cliente nuevo persistencia",
            "nif": "B12990001",
            "telefono": "600200001",
            "email": "cliente-nuevo@example.com",
            "direccion": "Calle Nueva 1",
            "poblacion": "Jumilla",
            "provincia": "Murcia",
            "codigo_postal": "30520",
            "observaciones": "Cliente nuevo",
        },
    )
    terceros_mod._guardar_nuevo(
        "proveedores",
        {
            "nombre": "Proveedor nuevo persistencia",
            "nif": "B12990002",
            "telefono": "600200002",
            "email": "proveedor-nuevo@example.com",
            "direccion": "Calle Nueva 2",
            "poblacion": "Jumilla",
            "provincia": "Murcia",
            "codigo_postal": "30520",
            "actividad": "Servicios",
            "observaciones": "Proveedor nuevo",
        },
    )
    clientes = leer(
        "SELECT * FROM clientes WHERE nif=?",
        ("B12990001",),
    )
    proveedores = leer(
        "SELECT * FROM proveedores WHERE nif=?",
        ("B12990002",),
    )
    cliente_id = int(clientes.iloc[0]["id"])
    proveedor_id = int(proveedores.iloc[0]["id"])
    clientes.loc[clientes.index[0], "nombre"] = "Cliente nuevo editado"
    clientes.loc[clientes.index[0], "telefono"] = "600299001"
    proveedores.loc[proveedores.index[0], "nombre"] = "Proveedor nuevo editado"
    proveedores.loc[proveedores.index[0], "email"] = "proveedor-editado@example.com"
    terceros_mod._actualizar_terceros(
        "clientes",
        clientes,
        [campo for campo, _, _ in terceros_mod.CONFIGURACION_TERCEROS["clientes"]["campos"]],
    )
    terceros_mod._actualizar_terceros(
        "proveedores",
        proveedores,
        [campo for campo, _, _ in terceros_mod.CONFIGURACION_TERCEROS["proveedores"]["campos"]],
    )

    with _conectar() as conn:

        cliente = _fila(conn, "clientes", cliente_id)
        proveedor = _fila(conn, "proveedores", proveedor_id)

    _assert_igual(cliente["nombre"], "Cliente nuevo editado", "cliente editado")
    _assert_igual(cliente["telefono"], "600299001", "telefono cliente")
    _assert_igual(
        proveedor["email"],
        "proveedor-editado@example.com",
        "email proveedor",
    )
    return "Clientes y proveedores persistidos"


def _validar_revision_excel_pdf(ctx):

    with _conectar() as conn:

        revision, registros = revision_siex._generar_revision(
            conn,
            ctx["campana_id"],
        )
        bloqueos = (
            0
            if revision.empty
            else int((revision["bloquea_exportacion"] == "Si").sum())
        )

    contenido_excel, nombre_excel = exportacion_siex.generar_excel_asistido_siex(
        campana_id=ctx["campana_id"],
        revision=revision,
    )

    if len(contenido_excel) <= 0:

        raise AssertionError("Excel SIEX sin contenido")

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    original_conectar = cuadernopro_pdf.conectar
    original_leer = cuadernopro_pdf.leer
    original_exports = cuadernopro_pdf.EXPORTS_DIR
    original_docs = cuadernopro_pdf.DOCS_DIR
    cuadernopro_pdf.conectar = _conectar
    cuadernopro_pdf.leer = _leer_persistencia
    cuadernopro_pdf.EXPORTS_DIR = EXPORTS_DIR
    cuadernopro_pdf.DOCS_DIR = DOCS_DIR

    try:

        ruta_pdf = Path(cuadernopro_pdf.generar_cuadernopro_pdf(
            ctx["campana_id"]
        ))

    finally:

        cuadernopro_pdf.conectar = original_conectar
        cuadernopro_pdf.leer = original_leer
        cuadernopro_pdf.EXPORTS_DIR = original_exports
        cuadernopro_pdf.DOCS_DIR = original_docs

    if not ruta_pdf.exists() or ruta_pdf.stat().st_size <= 0:

        raise AssertionError("PDF oficial sin contenido")

    ctx["revision_siex_registros"] = registros
    ctx["revision_siex_filas"] = len(revision)
    ctx["revision_siex_bloqueos"] = bloqueos
    ctx["excel_siex_nombre"] = nombre_excel
    ctx["excel_siex_bytes"] = len(contenido_excel)
    ctx["pdf_oficial"] = str(ruta_pdf)
    ctx["pdf_oficial_bytes"] = ruta_pdf.stat().st_size
    return (
        f"Revision {registros} registros/{bloqueos} bloqueos; "
        f"Excel {len(contenido_excel)} bytes; "
        f"PDF {ruta_pdf.stat().st_size} bytes"
    )


def _imprimir_resultados(resultados, ctx):

    print("Prueba persistencia editores v7")
    print("===============================")
    print(f"Base usada: {DB_PERSISTENCIA}")
    print("")
    print("| Modulo | Crear | Editar | Persistencia | Observaciones |")
    print("| --- | --- | --- | --- | --- |")

    for modulo, crear, editar, persistencia, observaciones, error in resultados:

        detalle = observaciones or error.splitlines()[0]
        print(
            f"| {modulo} | {crear} | {editar} | {persistencia} | {detalle} |"
        )

    print("")
    print("Salidas")
    print(
        "- Revision SIEX: "
        f"OK ({ctx.get('revision_siex_registros')} registros, "
        f"{ctx.get('revision_siex_filas')} avisos/info, "
        f"{ctx.get('revision_siex_bloqueos')} bloqueos)"
    )
    print(
        "- Excel SIEX: "
        f"OK ({ctx.get('excel_siex_nombre')}, "
        f"{ctx.get('excel_siex_bytes')} bytes)"
    )
    print(
        "- PDF oficial: "
        f"OK ({ctx.get('pdf_oficial')}, "
        f"{ctx.get('pdf_oficial_bytes')} bytes)"
    )

    fallos = [fila for fila in resultados if fila[1] != "OK"]
    print("")
    print("Resultado: " + ("FALLO" if fallos else "OK"))

    if fallos:

        print("")
        print("Errores")

        for modulo, _, _, _, _, error in fallos:

            print(f"## {modulo}")
            print(error)


def main():

    resultados = []

    try:

        _asegurar_base_prueba()
        ctx = _preparar_base()

    except Exception:

        print("Prueba persistencia editores v7")
        print("===============================")
        print(f"Base usada: {DB_PERSISTENCIA}")
        print("Preparacion base: FALLO")
        print(traceback.format_exc())
        return 1

    pruebas = [
        ("Explotacion", lambda: _probar_explotacion(ctx)),
        ("Productos fito", lambda: _probar_productos(ctx)),
        ("Maquinaria / equipos", lambda: _probar_maquinaria_y_equipos(ctx)),
        ("Tratamientos", lambda: _probar_tratamientos(ctx)),
        ("Fertilizacion", lambda: _probar_fertilizacion(ctx)),
        ("Practicas culturales", lambda: _probar_practicas(ctx)),
        ("Cosecha", lambda: _probar_cosecha(ctx)),
        ("Contabilidad", lambda: _probar_contabilidad(ctx)),
        ("Mapas / SIGPAC", lambda: _probar_mapas_sigpac(ctx)),
        ("Terceros", lambda: _probar_terceros(ctx)),
        ("Informes / salidas", lambda: _validar_revision_excel_pdf(ctx)),
    ]

    for modulo, funcion in pruebas:

        _registrar(resultados, modulo, funcion)

    _imprimir_resultados(resultados, ctx)
    return 0 if all(fila[1] == "OK" for fila in resultados) else 1


if __name__ == "__main__":

    raise SystemExit(main())
