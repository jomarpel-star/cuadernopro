from datetime import date

import streamlit as st

from core.config import APP_DESCRIPTION, APP_NAME
from core.db import ejecutar, leer
from core.fechas import formatear_fecha_es, parsear_fecha_es
from core.ui_tablas import preparar_dataframe_visual


def _leer_seguro(sql, params=()):

    try:

        return leer(sql, params)

    except Exception:

        return None


def _tabla_existe(nombre):

    datos = _leer_seguro(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (nombre,)
    )
    return datos is not None and not datos.empty


def _identificador_sql(nombre):

    return '"' + nombre.replace('"', '""') + '"'


def _columnas_tabla(nombre):

    datos = _leer_seguro(f"PRAGMA table_info({_identificador_sql(nombre)})")

    if datos is None or datos.empty:

        return set()

    return set(datos["name"].tolist())


def _valores_existentes(tabla, valores):

    columnas = _columnas_tabla(tabla)

    return {
        columna: valor
        for columna, valor in valores.items()
        if columna in columnas
    }


def _insertar_dinamico(tabla, valores):

    valores = _valores_existentes(tabla, valores)

    if not valores:

        raise ValueError(f"No hay columnas compatibles para insertar en {tabla}")

    columnas_sql = ",".join(_identificador_sql(columna) for columna in valores)
    marcas = ",".join("?" for _ in valores)

    ejecutar(
        f"""
        INSERT INTO {_identificador_sql(tabla)}
        ({columnas_sql})
        VALUES ({marcas})
        """,
        tuple(valores.values())
    )


def _actualizar_dinamico(tabla, valores, fila_id):

    valores = _valores_existentes(tabla, valores)

    if not valores:

        raise ValueError(f"No hay columnas compatibles para actualizar en {tabla}")

    asignaciones = ",".join(
        f"{_identificador_sql(columna)}=?"
        for columna in valores
    )

    ejecutar(
        f"""
        UPDATE {_identificador_sql(tabla)}
        SET {asignaciones}
        WHERE id=?
        """,
        tuple(valores.values()) + (int(fila_id),)
    )


def _contar(tabla):

    if not _tabla_existe(tabla):

        return 0

    datos = _leer_seguro(f"SELECT COUNT(*) total FROM {tabla}")

    if datos is None or datos.empty:

        return 0

    return int(datos.iloc[0]["total"] or 0)


def _obtener_version(clave):

    if clave not in st.session_state:

        st.session_state[clave] = 0

    return st.session_state[clave]


def _hay_explotacion_real():

    if not _tabla_existe("explotacion"):

        return False

    datos = _leer_seguro(
        """
        SELECT COUNT(*) total
        FROM explotacion
        WHERE TRIM(COALESCE(titular,'')) <> ''
        AND TRIM(COALESCE(nif,'')) <> ''
        """
    )

    if datos is None or datos.empty:

        return False

    return int(datos.iloc[0]["total"] or 0) > 0


def estado_configuracion_inicial():

    campanas = _contar("campanas")
    personas = _contar("personas")
    parcelas = _contar("parcelas")
    equipos = _contar("equipos_aplicacion")

    return {
        "campana": {
            "ok": campanas > 0,
            "total": campanas,
            "tipo": "obligatorio"
        },
        "explotacion": {
            "ok": _hay_explotacion_real(),
            "total": 1 if _hay_explotacion_real() else 0,
            "tipo": "obligatorio"
        },
        "personas": {
            "ok": personas > 0,
            "total": personas,
            "tipo": "obligatorio"
        },
        "parcelas": {
            "ok": parcelas > 0,
            "total": parcelas,
            "tipo": "recomendable"
        },
        "equipos": {
            "ok": equipos > 0,
            "total": equipos,
            "tipo": "opcional"
        },
    }


def app_necesita_configuracion_inicial():

    estado = estado_configuracion_inicial()
    return not (
        estado["campana"]["ok"]
        and estado["explotacion"]["ok"]
        and estado["personas"]["ok"]
    )


def hay_campana_configurada():

    return _contar("campanas") > 0


def obtener_campana_actual_si_existe():

    if not hay_campana_configurada():

        return None

    activa = _leer_seguro(
        """
        SELECT id
        FROM campanas
        WHERE activa=1
        ORDER BY id DESC
        LIMIT 1
        """
    )

    if activa is not None and not activa.empty:

        return int(activa.iloc[0]["id"])

    ultima = _leer_seguro(
        """
        SELECT id
        FROM campanas
        ORDER BY fecha_inicio DESC,id DESC
        LIMIT 1
        """
    )

    if ultima is None or ultima.empty:

        return None

    return int(ultima.iloc[0]["id"])


def _campana_por_defecto():

    hoy = date.today()

    if hoy.month <= 9:

        inicio_ano = hoy.year - 1
        fin_ano = hoy.year

    else:

        inicio_ano = hoy.year
        fin_ano = hoy.year + 1

    return {
        "nombre": f"{inicio_ano}/{fin_ano}",
        "inicio": date(inicio_ano, 10, 1),
        "fin": date(fin_ano, 9, 30),
    }


def _estado_icono(ok):

    return "✅" if ok else "❌"


def _valor_fila(fila, campo):

    valor = fila.get(campo, "")

    if valor is None:

        return ""

    try:

        if valor != valor:

            return ""

    except TypeError:

        pass

    return str(valor)


def _nombre_explotacion_o_titular(nombre_explotacion, titular):

    nombre = str(nombre_explotacion or "").strip()
    titular = str(titular or "").strip()
    return nombre or titular


def _mostrar_resumen(estado):

    st.subheader("Configuración inicial")

    elementos = [
        ("Campaña", estado["campana"]),
        ("Explotación", estado["explotacion"]),
        ("Personas", estado["personas"]),
        ("Parcelas", estado["parcelas"]),
        ("Equipos", estado["equipos"]),
    ]
    columnas = st.columns(len(elementos))

    for columna, (nombre, datos) in zip(columnas, elementos):

        with columna:

            st.markdown(f"**{nombre}**")
            st.markdown(f"{_estado_icono(datos['ok'])} {datos['tipo']}")

            if datos["total"]:

                st.caption(f"{datos['total']} registro(s)")

            else:

                st.caption("Sin datos")


def _ir_a(seccion):

    st.session_state["menu_principal_pendiente"] = seccion
    st.rerun()


def _vista_campanas_asistente(campanas):

    if campanas is None or campanas.empty:

        return campanas

    campanas_mostrar = campanas.copy()

    for columna in ("fecha_inicio", "fecha_fin"):

        if columna in campanas_mostrar.columns:

            campanas_mostrar[columna] = (
                campanas_mostrar[columna].apply(formatear_fecha_es)
            )

    return preparar_dataframe_visual(
        campanas_mostrar,
        columnas=["nombre", "fecha_inicio", "fecha_fin", "activa"],
        ocultar_tecnicas=True,
        etiquetas_extra={"nombre": "Campaña"}
    )


def _form_campana(estado):

    st.subheader("Campaña")

    if estado["campana"]["ok"]:

        campanas = _leer_seguro(
            """
            SELECT nombre,fecha_inicio,fecha_fin,activa
            FROM campanas
            ORDER BY fecha_inicio DESC,id DESC
            """
        )
        st.success("Ya hay campañas creadas.")

        if campanas is not None and not campanas.empty:

            st.dataframe(
                _vista_campanas_asistente(campanas),
                use_container_width=True,
                hide_index=True
            )

        if st.button("Ir a Campañas", key="asistente_ir_campanas"):

            _ir_a("Campañas")

        return

    defecto = _campana_por_defecto()
    version = _obtener_version("asistente_campana_form_version")

    with st.form(f"asistente_crear_campana_v{version}"):

        nombre = st.text_input(
            "Nombre campaña",
            defecto["nombre"],
            key=f"asistente_campana_nombre_{version}"
        )
        fecha_inicio = st.text_input(
            "Fecha inicio",
            formatear_fecha_es(defecto["inicio"]),
            placeholder="DD/MM/AAAA",
            key=f"asistente_campana_fecha_inicio_{version}"
        )
        fecha_fin = st.text_input(
            "Fecha fin",
            formatear_fecha_es(defecto["fin"]),
            placeholder="DD/MM/AAAA",
            key=f"asistente_campana_fecha_fin_{version}"
        )
        activa = st.checkbox(
            "Activa",
            value=True,
            key=f"asistente_campana_activa_{version}"
        )

        if st.form_submit_button("Crear campaña inicial"):

            nombre = nombre.strip()

            if not nombre:

                st.error("El nombre de la campaña es obligatorio")
                return

            try:

                inicio_iso = parsear_fecha_es(fecha_inicio)
                fin_iso = parsear_fecha_es(fecha_fin)

            except ValueError as exc:

                st.error(str(exc))
                return

            if inicio_iso is None or fin_iso is None:

                st.error("Fecha inicio y fecha fin son obligatorias")
                return

            if inicio_iso > fin_iso:

                st.error("La fecha de inicio no puede ser posterior a la fecha fin")
                return

            existente = _leer_seguro(
                "SELECT id FROM campanas WHERE nombre=?",
                (nombre,)
            )

            if existente is not None and not existente.empty:

                st.warning("Ya existe una campaña con ese nombre")
                return

            if activa:

                ejecutar("UPDATE campanas SET activa=0")

            ejecutar(
                """
                INSERT INTO campanas
                (nombre,fecha_inicio,fecha_fin,activa)
                VALUES (?,?,?,?)
                """,
                (nombre, inicio_iso, fin_iso, int(activa))
            )
            st.success("Campaña inicial creada")
            st.session_state["asistente_campana_form_version"] += 1
            st.rerun()


def _form_explotacion(estado):

    st.subheader("Explotación")

    if estado["explotacion"]["ok"]:

        st.success("Los datos básicos de explotación ya están guardados.")

        if st.button("Ir a Explotación", key="asistente_ir_explotacion"):

            _ir_a("Explotación")

        return

    datos = _leer_seguro(
        """
        SELECT *
        FROM explotacion
        ORDER BY id
        LIMIT 1
        """
    )
    fila = {} if datos is None or datos.empty else datos.iloc[0].to_dict()
    version = _obtener_version("asistente_explotacion_form_version")

    with st.form(f"asistente_guardar_explotacion_v{version}"):

        nombre_explotacion = st.text_input(
            "Nombre de la explotación",
            (
                _valor_fila(fila, "nombre_explotacion")
                or _valor_fila(fila, "titular")
            ),
            key=f"asistente_explotacion_nombre_{version}"
        )
        titular = st.text_input(
            "Titular / razón social",
            _valor_fila(fila, "titular"),
            key=f"asistente_explotacion_titular_{version}"
        )
        nif = st.text_input(
            "NIF",
            _valor_fila(fila, "nif"),
            key=f"asistente_explotacion_nif_{version}"
        )
        direccion = st.text_input(
            "Dirección",
            _valor_fila(fila, "direccion"),
            key=f"asistente_explotacion_direccion_{version}"
        )
        localidad = st.text_input(
            "Municipio / localidad",
            (
                _valor_fila(fila, "municipio")
                or _valor_fila(fila, "localidad")
            ),
            key=f"asistente_explotacion_localidad_{version}"
        )
        codigo_postal = st.text_input(
            "Código postal",
            _valor_fila(fila, "codigo_postal"),
            key=f"asistente_explotacion_codigo_postal_{version}"
        )
        provincia = st.text_input(
            "Provincia",
            _valor_fila(fila, "provincia"),
            key=f"asistente_explotacion_provincia_{version}"
        )
        telefono = st.text_input(
            "Teléfono",
            _valor_fila(fila, "telefono"),
            key=f"asistente_explotacion_telefono_{version}"
        )
        email = st.text_input(
            "Email",
            _valor_fila(fila, "email"),
            key=f"asistente_explotacion_email_{version}"
        )
        identificador_oficial = st.text_input(
            "Código REGEPA / identificador oficial",
            (
                _valor_fila(fila, "identificador_oficial")
                or _valor_fila(fila, "codigo_regepa")
                or _valor_fila(fila, "registro_explotacion")
                or _valor_fila(fila, "codigo_regea")
            ),
            key=f"asistente_explotacion_identificador_{version}"
        )
        registro_autonomico = st.text_input(
            "Registro autonómico",
            (
                _valor_fila(fila, "registro_autonomico")
                or _valor_fila(fila, "codigo_regepa")
            ),
            key=f"asistente_explotacion_registro_autonomico_{version}"
        )

        if st.form_submit_button("Guardar datos de explotación"):

            titular = titular.strip()
            nif = nif.strip()

            if not titular:

                st.error("El titular o razón social es obligatorio")
                return

            if not nif:

                st.error("El NIF es obligatorio")
                return

            nombre_explotacion = _nombre_explotacion_o_titular(
                nombre_explotacion,
                titular
            )
            identificador_oficial = identificador_oficial.strip()
            registro_autonomico = registro_autonomico.strip()
            tipo_identificador = (
                "REGEPA"
                if identificador_oficial
                else ""
            )
            valores = {
                "nombre_explotacion": nombre_explotacion,
                "titular": titular,
                "nif": nif,
                "direccion": direccion.strip(),
                "municipio": localidad.strip(),
                "localidad": localidad.strip(),
                "codigo_postal": codigo_postal.strip(),
                "provincia": provincia.strip(),
                "telefono": telefono.strip(),
                "email": email.strip(),
                "registro_explotacion": identificador_oficial,
                "codigo_regea": identificador_oficial,
                "codigo_regepa": identificador_oficial,
                "registro_autonomico": registro_autonomico,
                "identificador_oficial": identificador_oficial,
                "tipo_identificador_oficial": tipo_identificador,
            }

            if fila.get("id"):

                _actualizar_dinamico(
                    "explotacion",
                    valores,
                    fila["id"]
                )

            else:

                _insertar_dinamico("explotacion", valores)

            st.success("Datos de explotación guardados")
            st.session_state["asistente_explotacion_form_version"] += 1
            st.rerun()


def _form_personas(estado):

    st.subheader("Personas")

    if estado["personas"]["ok"]:

        st.success("Ya hay personas registradas.")

        personas = _leer_seguro(
            """
            SELECT nombre,nif,rol,telefono,email
            FROM personas
            ORDER BY id
            """
        )

        if personas is not None and not personas.empty:

            st.dataframe(
                preparar_dataframe_visual(
                    personas,
                    columnas=["nombre", "nif", "rol", "telefono", "email"],
                ),
                hide_index=True,
                use_container_width=True
            )

        if st.button("Ir a Explotación / Personas", key="asistente_ir_personas"):

            _ir_a("Explotación")

        return

    roles = [
        "Titular",
        "Representante",
        "Aplicador fitosanitario",
        "Asesor",
        "Operario"
    ]
    version = _obtener_version("asistente_persona_form_version")

    with st.form(f"asistente_anadir_persona_v{version}"):

        nombre = st.text_input(
            "Nombre",
            key=f"asistente_persona_nombre_{version}"
        )
        nif = st.text_input(
            "NIF",
            key=f"asistente_persona_nif_{version}"
        )
        rol = st.selectbox(
            "Rol",
            roles,
            key=f"asistente_persona_rol_{version}"
        )
        telefono = st.text_input(
            "Teléfono",
            key=f"asistente_persona_telefono_{version}"
        )
        email = st.text_input(
            "Email",
            key=f"asistente_persona_email_{version}"
        )
        carnet = st.text_input(
            "Carnet fitosanitario",
            key=f"asistente_persona_carnet_{version}"
        )

        if st.form_submit_button("Añadir persona"):

            nombre = nombre.strip()
            nif = nif.strip()

            if not nombre:

                st.error("El nombre es obligatorio")
                return

            if not nif:

                st.error("El NIF es obligatorio")
                return

            valores = {
                "nombre": nombre,
                "nif": nif,
                "telefono": telefono.strip(),
                "email": email.strip(),
                "rol": rol,
                "carnet_aplicador": carnet.strip(),
                "carnet_fitosanitario": carnet.strip(),
                "fecha_caducidad_carnet": None,
                "numero_asesor": "",
                "observaciones": "",
                "activo": 1,
            }
            _insertar_dinamico("personas", valores)
            st.success("Persona añadida")
            st.session_state["asistente_persona_form_version"] += 1
            st.rerun()


def _form_equipo():

    st.subheader("Equipo de aplicación")
    st.caption("Opcional. Puedes añadirlo ahora o más adelante.")

    total_equipos = _contar("equipos_aplicacion")

    if total_equipos:

        st.success(f"Ya hay {total_equipos} equipo(s) registrado(s).")

    version = _obtener_version("asistente_equipo_form_version")

    with st.form(f"asistente_anadir_equipo_v{version}"):

        nombre = st.text_input(
            "Descripción / nombre",
            key=f"asistente_equipo_nombre_{version}"
        )
        tipo = st.text_input(
            "Tipo",
            key=f"asistente_equipo_tipo_{version}"
        )
        marca = st.text_input(
            "Marca",
            key=f"asistente_equipo_marca_{version}"
        )
        modelo = st.text_input(
            "Modelo",
            key=f"asistente_equipo_modelo_{version}"
        )
        numero_roma = st.text_input(
            "ROMA",
            key=f"asistente_equipo_roma_{version}"
        )
        fecha_adquisicion = st.text_input(
            "Fecha adquisición",
            placeholder="DD/MM/AAAA",
            key=f"asistente_equipo_fecha_adquisicion_{version}"
        )
        fecha_ultima_inspeccion = st.text_input(
            "Fecha última inspección",
            placeholder="DD/MM/AAAA",
            key=f"asistente_equipo_fecha_ultima_{version}"
        )
        fecha_proxima_inspeccion = st.text_input(
            "Próxima inspección",
            placeholder="DD/MM/AAAA",
            key=f"asistente_equipo_fecha_proxima_{version}"
        )

        if st.form_submit_button("Añadir equipo"):

            nombre = nombre.strip()
            tipo = tipo.strip()

            if not nombre or not tipo:

                st.error("Descripción/nombre y tipo son obligatorios para añadir equipo")
                return

            try:

                fecha_adquisicion_iso = parsear_fecha_es(fecha_adquisicion)
                fecha_ultima_iso = parsear_fecha_es(fecha_ultima_inspeccion)
                fecha_proxima_iso = parsear_fecha_es(fecha_proxima_inspeccion)

            except ValueError as exc:

                st.error(str(exc))
                return

            numero_roma = numero_roma.strip()
            columnas_equipos = _columnas_tabla("equipos_aplicacion")
            valores = {
                "nombre": nombre,
                "tipo": tipo,
                "marca": marca.strip(),
                "modelo": modelo.strip(),
                "numero_roma": numero_roma,
                "numero_serie": (
                    ""
                    if "numero_roma" in columnas_equipos
                    else numero_roma
                ),
                "fecha_adquisicion": fecha_adquisicion_iso,
                "fecha_ultima_inspeccion": fecha_ultima_iso,
                "fecha_proxima_inspeccion": fecha_proxima_iso,
                "fecha_revision": fecha_ultima_iso,
                "fecha_proxima_revision": fecha_proxima_iso,
                "capacidad_litros": 0,
                "observaciones": "",
                "activo": 1,
            }
            _insertar_dinamico("equipos_aplicacion", valores)
            st.success("Equipo añadido")
            st.session_state["asistente_equipo_form_version"] += 1
            st.rerun()


def _siguientes_pasos():

    st.subheader("Siguientes pasos")
    st.write("Continúa cargando la información agrícola cuando la tengas preparada.")

    acciones = [
        ("Ir a Parcelas", "Parcelas"),
        ("Ir a Cultivos", "Cultivos"),
        ("Ir a Productos fito", "Productos Fito"),
        ("Ir a Cuaderno oficial / PDF", "Cuaderno oficial"),
    ]
    columnas = st.columns(4)

    for columna, (etiqueta, seccion) in zip(columnas, acciones):

        with columna:

            if st.button(etiqueta, use_container_width=True):

                _ir_a(seccion)


def render():

    estado = estado_configuracion_inicial()

    st.title(f"🌱 Bienvenido a {APP_NAME}")
    st.write(
        "Vamos a preparar los datos mínimos para empezar a trabajar con "
        "tu cuaderno de explotación."
    )
    st.caption(APP_DESCRIPTION)

    _mostrar_resumen(estado)

    tabs = st.tabs([
        "Campaña",
        "Explotación",
        "Personas",
        "Equipo de aplicación",
        "Siguientes pasos",
    ])

    with tabs[0]:

        _form_campana(estado)

    with tabs[1]:

        _form_explotacion(estado)

    with tabs[2]:

        _form_personas(estado)

    with tabs[3]:

        _form_equipo()

    with tabs[4]:

        _siguientes_pasos()
