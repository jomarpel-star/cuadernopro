#!/usr/bin/env python3
from pathlib import Path
import os
import sqlite3
import sys
import tempfile
import traceback


APP_ROOT = Path(__file__).resolve().parents[1]
DB_EDITORES = APP_ROOT / "runtime" / "v7" / "prueba_editores_v7.db"

if str(APP_ROOT) not in sys.path:

    sys.path.insert(0, str(APP_ROOT))

os.environ["CUADERNOPRO_DB_PATH"] = str(DB_EDITORES)

from core.schema_v7 import asegurar_ampliaciones_v8_0_1  # noqa: E402


def _conectar():

    conn = sqlite3.connect(DB_EDITORES)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _user_version(conn):

    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _limpiar_tablas_prueba(conn):

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


def _insertar_datos_base(conn):

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
            "Explotacion editores v7",
            "Titular editores v7",
            "00000000E",
            "Camino Editores 1",
            "Jumilla",
            "Murcia",
            "30520",
            "600000001",
            "editores-v7@example.com",
            "REGEPA-EDITORES-V7",
            "REGEPA",
            "REG-AUT-EDITORES-V7",
            "Agraria",
            "Frutos secos",
            "2026-01-01",
            1,
            0,
            "Responsable editores v7",
            "Asesor editores v7",
            "ASE-EDITORES-V7",
            "Datos auxiliares v7",
            ahora,
            ahora,
        ),
    )
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
            "Campana editores v7",
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
            "Parcela editores v7",
            30,
            22,
            0,
            0,
            "1",
            "2",
            "3",
            1.75,
            "TA",
            1,
            "Parcela auxiliar v7",
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
            "Almendro",
            "Comuna",
            "104",
            1.75,
            2020,
            "7x6",
            417,
            1,
            "Cultivo auxiliar v7",
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
        (cultivo_id, parcela_id, 1.75, ahora, ahora),
    )
    producto_id = conn.execute(
        """
        INSERT INTO productos_fito
        (nombre,numero_registro,materia_activa,titular,uso_autorizado,
         plazo_seguridad,observaciones,activo,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Producto editores v7",
            "REG-EDIT-V7",
            "Materia activa",
            "Titular producto",
            "Almendro",
            "15",
            "Producto auxiliar v7",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    aplicador_id = conn.execute(
        """
        INSERT INTO personas
        (nombre,nif,telefono,email,rol,carnet_aplicador,observaciones,
         activo,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Aplicador editores v7",
            "11111111A",
            "600000002",
            "aplicador@example.com",
            "Aplicador fitosanitario",
            "CAR-EDIT-V7",
            "Persona auxiliar v7",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    equipo_id = conn.execute(
        """
        INSERT INTO equipos_aplicacion
        (nombre,marca,modelo,tipo,matricula,numero_roma,numero_serie,
         fecha_adquisicion,capacidad_litros,fecha_revision,
         fecha_proxima_revision,observaciones,activo,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Equipo editores v7",
            "Marca equipo",
            "Modelo equipo",
            "Pulverizador",
            "EQ-MAT-EDIT-V7",
            "ROMA-EQ-EDIT-V7",
            "EQ-EDIT-V7",
            "2025-01-15",
            500.0,
            "2026-01-15",
            "2027-01-15",
            "Equipo auxiliar v7",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid
    maquinaria_id = conn.execute(
        """
        INSERT INTO maquinaria
        (tipo,marca,modelo,matricula,numero_roma,numero_serie,
         fecha_compra,horas_uso,descripcion,observaciones,activa,
         created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "Tractor",
            "Marca maquinaria",
            "Modelo maquinaria",
            "MU-0000-A",
            "ROMA-EDIT-V7",
            "SER-MAQ-EDIT-V7",
            "2025-02-15",
            50.0,
            "Tractor editores v7",
            "Maquinaria auxiliar v7",
            1,
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
            "Cliente editores v7",
            "22222222B",
            "600000003",
            "cliente@example.com",
            "Calle Cliente 1",
            "Jumilla",
            "Murcia",
            "30520",
            "Cliente auxiliar v7",
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
            "Proveedor editores v7",
            "33333333C",
            "600000004",
            "proveedor@example.com",
            "Calle Proveedor 1",
            "Jumilla",
            "Murcia",
            "30520",
            "Servicios",
            "Proveedor auxiliar v7",
            1,
            ahora,
            ahora,
        ),
    ).lastrowid

    return {
        "campana_id": int(campana_id),
        "parcela_id": int(parcela_id),
        "cultivo_id": int(cultivo_id),
        "producto_id": int(producto_id),
        "aplicador_id": int(aplicador_id),
        "equipo_id": int(equipo_id),
        "maquinaria_id": int(maquinaria_id),
        "cliente_id": int(cliente_id),
        "proveedor_id": int(proveedor_id),
        "ahora": ahora,
    }


def _insertar_registros_editables(conn, ids):

    ahora = ids["ahora"]
    tratamiento_id = conn.execute(
        """
        INSERT INTO tratamientos
        (campana_id,cultivo_id,fecha_inicio,fecha_fin,producto_id,
         aplicador_id,equipo_aplicacion_id,plaga_motivo,dosis,caldo,
         superficie_tratada,plazo_seguridad,eficacia,observaciones,
         created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ids["campana_id"],
            ids["cultivo_id"],
            "2026-03-10",
            "2026-03-10",
            ids["producto_id"],
            ids["aplicador_id"],
            ids["equipo_id"],
            "Repilo",
            "1 l/ha",
            500.0,
            1.75,
            "15",
            "B",
            "Tratamiento auxiliar v7",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO tratamiento_parcelas
        (tratamiento_id,parcela_id,superficie,created_at,updated_at)
        VALUES (?,?,?,?,?)
        """,
        (tratamiento_id, ids["parcela_id"], 1.75, ahora, ahora),
    )
    fertilizacion_id = conn.execute(
        """
        INSERT INTO fertilizaciones
        (campana_id,cultivo_id,fecha,producto,tipo_fertilizante,cantidad,
         unidad,unidad_normalizada,superficie,codigo_actuacion_siex,
         observaciones,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ids["campana_id"],
            ids["cultivo_id"],
            "2026-02-01",
            "Abono complejo",
            "Mineral",
            200.0,
            "kg",
            "kg",
            1.75,
            "FERT-EDIT-V7",
            "Fertilizacion auxiliar v7",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO fertilizacion_parcelas
        (fertilizacion_id,parcela_id,superficie,created_at,updated_at)
        VALUES (?,?,?,?,?)
        """,
        (fertilizacion_id, ids["parcela_id"], 1.75, ahora, ahora),
    )
    practica_id = conn.execute(
        """
        INSERT INTO practicas_culturales
        (campana_id,cultivo_id,fecha,labor,codigo_actuacion_siex,
         superficie,maquinaria_id,proveedor_id,observaciones,
         created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ids["campana_id"],
            ids["cultivo_id"],
            "2026-01-20",
            "Poda",
            "PRAC-EDIT-V7",
            1.75,
            ids["maquinaria_id"],
            ids["proveedor_id"],
            "Practica auxiliar v7",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO practicas_culturales_parcelas
        (practica_id,parcela_id,superficie,created_at,updated_at)
        VALUES (?,?,?,?,?)
        """,
        (practica_id, ids["parcela_id"], 1.75, ahora, ahora),
    )
    cosecha_id = conn.execute(
        """
        INSERT INTO cosecha
        (campana_id,cultivo_id,fecha,cantidad,unidad,destino,cliente_id,
         observaciones,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ids["campana_id"],
            ids["cultivo_id"],
            "2026-08-15",
            1500.0,
            "kg",
            "Venta",
            ids["cliente_id"],
            "Cosecha auxiliar v7",
            ahora,
            ahora,
        ),
    ).lastrowid
    conn.execute(
        """
        INSERT INTO cosecha_parcelas
        (cosecha_id,parcela_id,superficie,created_at,updated_at)
        VALUES (?,?,?,?,?)
        """,
        (cosecha_id, ids["parcela_id"], 1.75, ahora, ahora),
    )
    conn.execute(
        """
        INSERT INTO movimientos_economicos
        (campana_id,cultivo_id,fecha,tipo,categoria,concepto,
         numero_factura,cliente_id,proveedor_id,base_imponible,iva,
         retencion,total,pendiente,fecha_pago,observaciones,
         created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ids["campana_id"],
            ids["cultivo_id"],
            "2026-08-16",
            "Ingreso",
            "Venta de cosecha",
            "Venta almendra",
            "F-EDIT-V7",
            ids["cliente_id"],
            None,
            1000.0,
            10.0,
            0.0,
            1100.0,
            0,
            "2026-08-20",
            "Movimiento auxiliar v7",
            ahora,
            ahora,
        ),
    )


def _preparar_datos():

    with _conectar() as conn:

        _limpiar_tablas_prueba(conn)
        ids = _insertar_datos_base(conn)
        conn.commit()

    return ids


def _insertar_datos_editables(ids):

    with _conectar() as conn:

        _insertar_registros_editables(conn, ids)
        conn.commit()


def _crear_app_temporal(nombre, codigo):

    contenido = f"""
from pathlib import Path
import os
import sys

APP_ROOT = Path({str(APP_ROOT)!r})
DB_EDITORES = Path({str(DB_EDITORES)!r})
os.environ["CUADERNOPRO_DB_PATH"] = str(DB_EDITORES)

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

{codigo}
"""
    temporal = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".py",
        prefix=f"editores_auxiliares_{nombre.lower().replace(' ', '_')}_",
        dir=DB_EDITORES.parent,
        delete=False,
    )

    with temporal:

        temporal.write(contenido)

    return Path(temporal.name)


def _descripcion_excepcion(excepcion):

    for atributo in ("value", "message", "exception"):

        valor = getattr(excepcion, atributo, None)

        if valor:

            return str(valor)

    return str(excepcion)


def _renderizar(nombre, codigo):

    from streamlit.testing.v1 import AppTest

    app_temporal = _crear_app_temporal(nombre, codigo)

    try:

        prueba = AppTest.from_file(app_temporal, default_timeout=15)
        prueba.run(timeout=15)
        excepciones = list(prueba.exception)
        errores_streamlit = list(getattr(prueba, "error", []))

        if excepciones:

            return False, "\n".join(
                _descripcion_excepcion(excepcion)
                for excepcion in excepciones
            )

        if errores_streamlit:

            return False, "\n".join(
                _descripcion_excepcion(error)
                for error in errores_streamlit
            )

        return True, ""

    except Exception:

        return False, traceback.format_exc()

    finally:

        try:

            app_temporal.unlink()

        except OSError:

            pass


def _codigo_campana(seccion, modulo, clave_estado):

    return (
        "import sqlite3\n"
        "import streamlit as st\n"
        f"import {modulo} as modulo\n"
        f"st.session_state[{clave_estado!r}] = {seccion!r}\n"
        f"conn = sqlite3.connect({str(DB_EDITORES)!r})\n"
        "campana_id = conn.execute("
        "'SELECT id FROM campanas ORDER BY id LIMIT 1'"
        ").fetchone()[0]\n"
        "conn.close()\n"
        "modulo.render(campana_id)\n"
    )


def main():

    print("Prueba editores y auxiliares v7")
    print("===============================")
    print(f"Base usada: {DB_EDITORES}")

    if not DB_EDITORES.exists():

        print("FALLO: la base de prueba no existe")
        return 1

    with _conectar() as conn:

        version = _user_version(conn)

    print(f"PRAGMA user_version: {version}")

    if version != 7:

        print("FALLO: la base no tiene user_version 7")
        return 1

    resultados = []

    try:

        with _conectar() as conn:

            asegurar_ampliaciones_v8_0_1(conn)
            _limpiar_tablas_prueba(conn)
            conn.commit()

        ok, error = _renderizar(
            "Mapas parcelas vacias",
            "import modules.mapas as modulo\n"
            "modulo.render()\n",
        )
        resultados.append(("Mapas parcelas vacias", ok, error))
        print(f"Mapas parcelas vacias: {'OK' if ok else 'FALLO'}")

        if error:

            print(error)

    except Exception:

        print("Mapas parcelas vacias: FALLO")
        print(traceback.format_exc())
        return 1

    try:

        ids = _preparar_datos()
        print("Datos base editores: OK")

    except Exception:

        print("Datos base editores: FALLO")
        print(traceback.format_exc())
        return 1

    pruebas = [
        (
            "Explotacion Responsable Asesor",
            "import modules.explotacion as modulo\n"
            "datos = modulo._leer_datos_explotacion()\n"
            "modulo._render_responsable_asesor(datos)\n",
        ),
        (
            "Contabilidad listado vacio",
            _codigo_campana(
                "📋 Listado",
                "modules.contabilidad",
                "contabilidad_seccion",
            ),
        ),
        (
            "Informes base minima",
            _codigo_campana(
                "Resumen",
                "modules.informes",
                "informes_seccion",
            ),
        ),
        (
            "Revision SIEX base minima",
            "import modules.revision_siex as modulo\n"
            "modulo.render()\n",
        ),
        (
            "Mapas sin geometria",
            "import modules.mapas as modulo\n"
            "modulo.render()\n",
        ),
        (
            "Productos fito listado",
            "import streamlit as st\n"
            "import modules.productos_fito as modulo\n"
            "st.session_state['productos_fito_seccion'] = '📋 Listado'\n"
            "modulo.render()\n",
        ),
    ]

    for nombre, codigo in pruebas:

        ok, error = _renderizar(nombre, codigo)
        resultados.append((nombre, ok, error))
        print(f"{nombre}: {'OK' if ok else 'FALLO'}")

        if error:

            print(error)

    try:

        _insertar_datos_editables(ids)
        print("Datos editables auxiliares: OK")

    except Exception:

        print("Datos editables auxiliares: FALLO")
        print(traceback.format_exc())
        return 1

    pruebas_editables = [
        (
            "Tratamientos editar",
            _codigo_campana(
                "✏️ Editar",
                "modules.tratamientos",
                "tratamientos_seccion",
            ),
        ),
        (
            "Fertilizacion editar",
            _codigo_campana(
                "✏️ Editar",
                "modules.fertilizacion",
                "fertilizacion_seccion",
            ),
        ),
        (
            "Practicas editar",
            _codigo_campana(
                "✏️ Editar",
                "modules.practicas_culturales",
                "practicas_seccion",
            ),
        ),
        (
            "Cosecha editar",
            _codigo_campana(
                "✏️ Editar",
                "modules.cosecha",
                "cosecha_seccion",
            ),
        ),
        (
            "Contabilidad editar",
            _codigo_campana(
                "✏️ Editar",
                "modules.contabilidad",
                "contabilidad_seccion",
            ),
        ),
        (
            "Productos fito editar",
            "import streamlit as st\n"
            "import modules.productos_fito as modulo\n"
            "st.session_state['productos_fito_seccion'] = '✏️ Editar'\n"
            "modulo.render()\n",
        ),
    ]

    for nombre, codigo in pruebas_editables:

        ok, error = _renderizar(nombre, codigo)
        resultados.append((nombre, ok, error))
        print(f"{nombre}: {'OK' if ok else 'FALLO'}")

        if error:

            print(error)

    if all(ok for _, ok, _ in resultados):

        print("Resultado: OK")
        return 0

    print("Resultado: FALLO")
    return 1


if __name__ == "__main__":

    raise SystemExit(main())
