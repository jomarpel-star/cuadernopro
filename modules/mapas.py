from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from core.campanas import obtener_campana_activa
from core.db import conectar, leer
from core.ui_tablas import preparar_dataframe_visual
from services.sigpac import (
    buscar_geometria_sigpac,
    calcular_bounds_geojson,
    faltan_codigos_sigpac_numericos as _faltan_codigos_sigpac_numericos,
    normalizar_geojson_sigpac,
)


def _agregar_radar_lluvia(mapa, folium):

    from branca.element import MacroElement, Template

    capa_radar = folium.FeatureGroup(
        name="Radar de lluvia (últimas 2 h)",
        overlay=True,
        control=True,
        show=False,
    ).add_to(mapa)

    class ControlRadarLluvia(MacroElement):

        _template = Template(
            """
            {% macro script(this, kwargs) %}
            (function () {
                const map = {{ this._parent.get_name() }};
                const radarGroup = {{ this.radar_group.get_name() }};
                const apiUrl =
                    "https://api.rainviewer.com/public/weather-maps.json";
                let frames = [];
                let currentFrame = -1;
                let timer = null;
                let radarVisible = false;

                const control = L.control({position: "bottomleft"});
                control.onAdd = function () {
                    const container = L.DomUtil.create(
                        "div",
                        "cuadernopro-radar-control leaflet-bar"
                    );
                    container.style.display = "none";
                    container.style.background = "rgba(255,255,255,0.96)";
                    container.style.padding = "7px 9px";
                    container.style.minWidth = "250px";
                    container.style.boxShadow = "0 1px 5px rgba(0,0,0,0.35)";
                    container.innerHTML = `
                        <div style="font-weight:600;margin-bottom:5px;">
                            Radar de lluvia
                        </div>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <button type="button" data-action="previous"
                                title="Imagen anterior" aria-label="Imagen anterior"
                                style="width:30px;height:28px;">&#9664;</button>
                            <button type="button" data-action="play"
                                title="Reproducir" aria-label="Reproducir"
                                style="width:34px;height:28px;">&#9654;</button>
                            <button type="button" data-action="next"
                                title="Imagen siguiente" aria-label="Imagen siguiente"
                                style="width:30px;height:28px;">&#9654;|</button>
                            <input type="range" min="0" max="0" value="0"
                                aria-label="Momento del radar"
                                style="flex:1;min-width:80px;">
                        </div>
                        <div data-role="time"
                            style="font-size:12px;margin-top:5px;color:#374151;">
                            Cargando radar…
                        </div>`;
                    L.DomEvent.disableClickPropagation(container);
                    L.DomEvent.disableScrollPropagation(container);
                    return container;
                };
                control.addTo(map);

                const container = control.getContainer();
                const slider = container.querySelector("input[type=range]");
                const timeLabel = container.querySelector('[data-role="time"]');
                const playButton = container.querySelector('[data-action="play"]');

                function formatTime(unixTime) {
                    return new Date(unixTime * 1000).toLocaleString("es-ES", {
                        day: "2-digit",
                        month: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit"
                    });
                }

                function showFrame(index) {
                    if (!frames.length) return;
                    const normalized = (index + frames.length) % frames.length;
                    if (currentFrame >= 0) {
                        radarGroup.removeLayer(frames[currentFrame].layer);
                    }
                    currentFrame = normalized;
                    radarGroup.addLayer(frames[currentFrame].layer);
                    slider.value = String(currentFrame);
                    timeLabel.textContent =
                        "Observación: " + formatTime(frames[currentFrame].time);
                }

                function stop() {
                    if (timer !== null) {
                        window.clearInterval(timer);
                        timer = null;
                    }
                    playButton.innerHTML = "&#9654;";
                    playButton.title = "Reproducir";
                }

                function togglePlay() {
                    if (!frames.length) return;
                    if (timer !== null) {
                        stop();
                        return;
                    }
                    playButton.innerHTML = "&#10074;&#10074;";
                    playButton.title = "Pausar";
                    timer = window.setInterval(function () {
                        showFrame(currentFrame + 1);
                    }, 850);
                }

                container.querySelector('[data-action="previous"]')
                    .addEventListener("click", function () {
                        stop();
                        showFrame(currentFrame - 1);
                    });
                playButton.addEventListener("click", togglePlay);
                container.querySelector('[data-action="next"]')
                    .addEventListener("click", function () {
                        stop();
                        showFrame(currentFrame + 1);
                    });
                slider.addEventListener("input", function () {
                    stop();
                    showFrame(Number(slider.value));
                });

                map.on("overlayadd", function (event) {
                    if (event.layer === radarGroup) {
                        radarVisible = true;
                        container.style.display = "block";
                        if (frames.length && currentFrame < 0) {
                            showFrame(frames.length - 1);
                        }
                    }
                });
                map.on("overlayremove", function (event) {
                    if (event.layer === radarGroup) {
                        radarVisible = false;
                        stop();
                        container.style.display = "none";
                    }
                });

                fetch(apiUrl)
                    .then(function (response) {
                        if (!response.ok) {
                            throw new Error("HTTP " + response.status);
                        }
                        return response.json();
                    })
                    .then(function (data) {
                        const available = data.radar && data.radar.past
                            ? data.radar.past
                            : [];
                        frames = available.map(function (frame) {
                            return {
                                time: frame.time,
                                layer: L.tileLayer(
                                    data.host + frame.path +
                                        "/256/{z}/{x}/{y}/2/1_1.png",
                                    {
                                        opacity: 0.62,
                                        maxNativeZoom: 7,
                                        maxZoom: 19,
                                        attribution:
                                            'Radar: <a href="https://www.rainviewer.com/" target="_blank" rel="noopener">RainViewer</a>'
                                    }
                                )
                            };
                        });
                        if (!frames.length) {
                            throw new Error("Sin imágenes disponibles");
                        }
                        slider.max = String(frames.length - 1);
                        timeLabel.textContent = "Radar preparado";
                        if (radarVisible) {
                            showFrame(frames.length - 1);
                        }
                    })
                    .catch(function () {
                        stop();
                        timeLabel.textContent =
                            "Radar no disponible. Comprueba la conexión.";
                    });
            })();
            {% endmacro %}
            """
        )

        def __init__(self, radar_group):

            super().__init__()
            self._name = "ControlRadarLluvia"
            self.radar_group = radar_group

    ControlRadarLluvia(capa_radar).add_to(mapa)

    return capa_radar


def _identificador_sql(nombre):

    return '"' + nombre.replace('"', '""') + '"'


def _columnas_tabla_conn(conn, tabla):

    return {
        fila[1]
        for fila in conn.execute(f"PRAGMA table_info({_identificador_sql(tabla)})")
    }


def _tabla_existe_conn(conn, tabla):

    fila = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (tabla,),
    ).fetchone()
    return fila is not None


def _expr_columna(columnas, columna, alias=None, defecto="''"):

    alias = alias or columna

    if columna in columnas:

        expresion = _identificador_sql(columna)

        if alias != columna:

            expresion += f" AS {_identificador_sql(alias)}"

        return expresion

    return f"{defecto} AS {_identificador_sql(alias)}"


def _expr_provincia(columnas):

    if "provincia" in columnas:

        return _expr_columna(columnas, "provincia")

    return _expr_columna(columnas, "provincia_sigpac", alias="provincia")


def _expr_municipio(columnas):

    if "municipio" in columnas:

        return _expr_columna(columnas, "municipio")

    return _expr_columna(columnas, "municipio_sigpac", alias="municipio")


def _expr_estado_geojson(columnas):

    if "sigpac_geojson_estado" in columnas:

        return _expr_columna(columnas, "sigpac_geojson_estado")

    if "sigpac_geojson" in columnas:

        return (
            "CASE WHEN TRIM(COALESCE(sigpac_geojson,''))<>'' "
            "THEN 'Con geometría' ELSE 'Sin geometría' END "
            "AS sigpac_geojson_estado"
        )

    return "'Sin geometría' AS sigpac_geojson_estado"


def _estado_geometria_visual(estado, geojson=None):

    texto = "" if estado is None or pd.isna(estado) else str(estado).strip()
    normalizado = texto.casefold()

    if normalizado in {"ok", "con geometría", "con geometria"}:

        return "Con geometría"

    if normalizado in {"pendiente_actualizacion", "pendiente"}:

        return "Pendiente de actualización"

    if normalizado in {"error", "sin_codigos", "sin códigos", "sin codigos"}:

        return "Error SIGPAC"

    if texto:

        return texto

    texto_geojson = "" if geojson is None or pd.isna(geojson) else str(geojson)
    return "Con geometría" if texto_geojson.strip() else "Sin geometría"


def _texto_mapa(valor):

    try:

        if valor is None or pd.isna(valor):

            return ""

    except (TypeError, ValueError):

        if valor is None:

            return ""

    texto = str(valor).strip()

    if texto.casefold() in {"none", "nan", "null"}:

        return ""

    return texto


def _numero_mapa(valor):

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):

        return None

    return float(numero)


def _formatear_superficie_mapa(valor):

    numero = _numero_mapa(valor)

    if numero is None:

        return ""

    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _normalizar_entero_arboles_tooltip(valor):

    try:

        if valor is None or pd.isna(valor):

            return None

    except (TypeError, ValueError):

        if valor is None:

            return None

    if isinstance(valor, bool):

        return None

    if isinstance(valor, int):

        numero = valor

    elif isinstance(valor, float):

        if not valor.is_integer():

            return None

        numero = int(valor)

    else:

        texto = str(valor).strip().replace(" ", "")

        if not texto or texto.casefold() in {"none", "nan", "null"}:

            return None

        if texto.startswith("+"):

            texto = texto[1:]

        if texto.startswith("-"):

            return None

        if "," in texto:

            if texto.count(",") != 1:

                return None

            parte_entera, parte_decimal = texto.split(",", 1)

            if not parte_decimal.isdigit() or int(parte_decimal) != 0:

                return None

            if "." in parte_entera:

                grupos = parte_entera.split(".")

                if (
                    not grupos
                    or not grupos[0].isdigit()
                    or not all(
                        grupo.isdigit() and len(grupo) == 3
                        for grupo in grupos[1:]
                    )
                ):

                    return None

                parte_entera = "".join(grupos)

            if not parte_entera.isdigit():

                return None

            numero = int(parte_entera)

        elif "." in texto:

            grupos = texto.split(".")

            es_miles_es = (
                grupos[0].isdigit()
                and all(
                    grupo.isdigit() and len(grupo) == 3
                    for grupo in grupos[1:]
                )
            )

            if es_miles_es:

                numero = int("".join(grupos))

            elif (
                len(grupos) == 2
                and grupos[0].isdigit()
                and grupos[1].isdigit()
                and int(grupos[1]) == 0
            ):

                numero = int(grupos[0])

            else:

                return None

        elif texto.isdigit():

            numero = int(texto)

        else:

            return None

    if numero <= 0:

        return None

    return numero


def _formatear_arboles_tooltip(valor):

    numero = _normalizar_entero_arboles_tooltip(valor)

    if numero is None:

        return ""

    return f"{numero:,}".replace(",", ".") + " árboles"


def _formatear_arboles_mapa(valor):

    arboles = _formatear_arboles_tooltip(valor)

    if not arboles:

        return ""

    return arboles.replace(" árboles", "")


def _clave_texto_mapa(valor):

    return _texto_mapa(valor).casefold()


def _obtener_campana_contexto_mapa(conn, campana_id=None):

    if campana_id is not None:

        numero = pd.to_numeric(campana_id, errors="coerce")

        if not pd.isna(numero):

            return int(numero)

    activa = obtener_campana_activa(conn)

    if not activa:

        return None

    return int(activa["id"])


def _resumir_cultivo_mapa(cultivo):

    especie = _texto_mapa(cultivo.get("especie")).upper()
    variedad = _texto_mapa(cultivo.get("variedad")).upper()
    arboles = _formatear_arboles_tooltip(cultivo.get("arboles"))
    partes = []

    for valor in [especie, variedad]:

        if not valor:

            continue

        claves = {_clave_texto_mapa(parte) for parte in partes}

        if _clave_texto_mapa(valor) not in claves:

            partes.append(valor)

    if arboles:

        partes.append(arboles)

    return " · ".join(partes)


def resumir_cultivos_mapa(cultivos, max_cultivos=2):

    vistos = set()
    resumenes = []

    for cultivo in cultivos:

        resumen = _resumir_cultivo_mapa(cultivo)

        if not resumen:

            continue

        clave = _clave_texto_mapa(resumen)

        if clave in vistos:

            continue

        vistos.add(clave)
        resumenes.append(resumen)

    if not resumenes:

        return ""

    if len(resumenes) <= max_cultivos:

        return "<br>".join(escape(resumen) for resumen in resumenes)

    primero = escape(resumenes[0])
    restantes = len(resumenes) - 1
    return f"{primero}<br>y {restantes} más"


def construir_tooltip_parcela_mapa(parcela, cultivos):

    nombre = _texto_mapa(parcela.get("nombre")) or "Sin nombre"
    poligono = _texto_mapa(parcela.get("poligono")) or "—"
    numero_parcela = _texto_mapa(parcela.get("parcela")) or "—"
    recinto = _texto_mapa(parcela.get("recinto")) or "—"
    superficie = _formatear_superficie_mapa(parcela.get("superficie_sigpac"))
    cultivo = resumir_cultivos_mapa(cultivos) or "Sin cultivo en campaña activa"
    superficie_linea = (
        f"<br><b>Sup.:</b> {escape(superficie)} ha"
        if superficie
        else ""
    )
    return (
        '<div style="max-width:360px;font-size:12px;line-height:1.25;'
        'padding:6px 8px;">'
        f"<b>Parcela:</b> {escape(nombre)}<br>"
        f"<b>SIGPAC:</b> Pol. {escape(poligono)} · "
        f"Parc. {escape(numero_parcela)} · Rec. {escape(recinto)}"
        f"{superficie_linea}<br>"
        f"<b>Cultivo:</b> {cultivo}"
        "</div>"
    )


def _actualizar_parcela_sigpac(conn, parcela_id, valores):

    columnas = _columnas_tabla_conn(conn, "parcelas")
    valores = {
        columna: valor
        for columna, valor in valores.items()
        if columna in columnas
    }

    if not valores:

        return

    asignaciones = ",".join(
        f"{_identificador_sql(columna)}=?"
        for columna in valores
    )
    conn.execute(
        f"UPDATE parcelas SET {asignaciones} WHERE id=?",
        [valores[columna] for columna in valores] + [int(parcela_id)],
    )


def _sql_parcela_sigpac(conn):

    columnas = _columnas_tabla_conn(conn, "parcelas")
    select = [
        _expr_columna(columnas, "id"),
        _expr_columna(columnas, "nombre"),
        _expr_provincia(columnas),
        _expr_municipio(columnas),
        _expr_columna(columnas, "poligono"),
        _expr_columna(columnas, "parcela"),
        _expr_columna(columnas, "recinto"),
        _expr_columna(columnas, "superficie_sigpac", defecto="NULL"),
        _expr_columna(columnas, "provincia_sigpac", defecto="NULL"),
        _expr_columna(columnas, "municipio_sigpac", defecto="NULL"),
        _expr_columna(columnas, "agregado_sigpac", defecto="0"),
        _expr_columna(columnas, "zona_sigpac", defecto="0"),
        _expr_columna(columnas, "sigpac_geojson"),
        _expr_columna(
            columnas,
            "sigpac_geojson_actualizado",
            defecto="''",
        ),
        _expr_estado_geojson(columnas),
        _expr_columna(columnas, "sigpac_geojson_error", defecto="''"),
    ]
    return (
        "SELECT "
        + ",".join(select)
        + " FROM parcelas WHERE id=?"
    )


def _leer_estado_geometrias():

    with conectar() as conn:

        columnas = _columnas_tabla_conn(conn, "parcelas")
        sql = (
            "SELECT "
            + ",".join(
                [
                    _expr_columna(columnas, "id"),
                    _expr_columna(columnas, "sigpac_geojson"),
                    _expr_estado_geojson(columnas),
                ]
            )
            + " FROM parcelas ORDER BY id"
        )
        return pd.read_sql_query(sql, conn)


def _leer_parcelas_mapa():

    with conectar() as conn:

        columnas = _columnas_tabla_conn(conn, "parcelas")
        select = [
            _expr_columna(columnas, "id"),
            _expr_columna(columnas, "nombre"),
            _expr_provincia(columnas),
            _expr_municipio(columnas),
            _expr_columna(columnas, "poligono"),
            _expr_columna(columnas, "parcela"),
            _expr_columna(columnas, "recinto"),
            _expr_columna(columnas, "superficie_sigpac", defecto="NULL"),
            _expr_columna(columnas, "provincia_sigpac", defecto="NULL"),
            _expr_columna(columnas, "municipio_sigpac", defecto="NULL"),
            _expr_columna(columnas, "agregado_sigpac", defecto="0"),
            _expr_columna(columnas, "zona_sigpac", defecto="0"),
            _expr_columna(columnas, "sigpac_geojson"),
            _expr_columna(
                columnas,
                "sigpac_geojson_actualizado",
                defecto="''",
            ),
            _expr_estado_geojson(columnas),
            _expr_columna(columnas, "sigpac_geojson_error", defecto="''"),
        ]
        sql = (
            "SELECT "
            + ",".join(select)
            + " FROM parcelas "
            + "ORDER BY municipio,poligono,parcela,recinto,id"
        )
        return pd.read_sql_query(sql, conn)


def _dataframe_cultivos_mapa_vacio():

    return pd.DataFrame(
        columns=["parcela_id", "especie", "variedad", "sistema", "arboles"]
    )


def _leer_cultivos_mapa(campana_id=None):

    with conectar() as conn:

        if not _tabla_existe_conn(conn, "cultivos"):

            return _dataframe_cultivos_mapa_vacio()

        columnas_cultivos = _columnas_tabla_conn(conn, "cultivos")

        if "campana_id" not in columnas_cultivos:

            return _dataframe_cultivos_mapa_vacio()

        campana_contexto_id = _obtener_campana_contexto_mapa(conn, campana_id)

        if campana_contexto_id is None:

            return _dataframe_cultivos_mapa_vacio()

        expr_especie = (
            "c.especie AS especie"
            if "especie" in columnas_cultivos
            else "c.nombre AS especie"
        )
        expr_variedad = (
            "c.variedad AS variedad"
            if "variedad" in columnas_cultivos
            else "'' AS variedad"
        )
        expr_sistema = (
            "c.sistema AS sistema"
            if "sistema" in columnas_cultivos
            else "'' AS sistema"
        )
        expr_arboles = (
            "c.numero_arboles AS arboles"
            if "numero_arboles" in columnas_cultivos
            else (
                "c.arboles AS arboles"
                if "arboles" in columnas_cultivos
                else "NULL AS arboles"
            )
        )

        if (
            _tabla_existe_conn(conn, "cultivo_parcelas")
            and "id" in columnas_cultivos
        ):

            sql = f"""
            SELECT cp.parcela_id,{expr_especie},{expr_variedad},
                   {expr_sistema},{expr_arboles}
            FROM cultivo_parcelas cp
            JOIN cultivos c ON c.id=cp.cultivo_id
            WHERE c.campana_id=?
            ORDER BY cp.parcela_id,c.id
            """
            return pd.read_sql_query(sql, conn, params=(campana_contexto_id,))

        if "parcela_id" in columnas_cultivos:

            sql = f"""
            SELECT c.parcela_id,{expr_especie},{expr_variedad},
                   {expr_sistema},{expr_arboles}
            FROM cultivos c
            WHERE c.campana_id=?
            ORDER BY c.parcela_id,c.id
            """
            return pd.read_sql_query(sql, conn, params=(campana_contexto_id,))

    return _dataframe_cultivos_mapa_vacio()


def render():

    st.title("🗺️ Mapa general de la explotación")

    try:

        import folium
        from streamlit_folium import st_folium
        import json


        def obtener_color_cultivo(cultivos_texto):

            texto = str(cultivos_texto or "").casefold()

            if "almend" in texto:

                return {
                    "fillColor": "green",
                    "color": "darkgreen",
                    "fillOpacity": 0.45,
                    "weight": 2
                }

            if "oliv" in texto:

                return {
                    "fillColor": "blue",
                    "color": "darkblue",
                    "fillOpacity": 0.45,
                    "weight": 2
                }

            if any(
                termino in texto
                for termino in [
                    "arable",
                    "herbace",
                    "herbáce",
                    "cereal",
                    "barbecho"
                ]
            ):

                return {
                    "fillColor": "white",
                    "color": "black",
                    "fillOpacity": 0.55,
                    "weight": 2
                }

            return {
                "fillColor": "lightgray",
                "color": "gray",
                "fillOpacity": 0.35,
                "weight": 1
            }


        def crear_mapa_parcela(geojson, etiqueta):

            bounds = calcular_bounds_geojson(geojson)
            centro = [
                bounds["centro_lat"],
                bounds["centro_lon"]
            ]
            mapa = folium.Map(
                location=centro,
                tiles="OpenStreetMap",
                zoom_start=18,
                control_scale=True
            )
            folium.GeoJson(
                geojson,
                name="Parcela SIGPAC",
                tooltip=etiqueta,
                style_function=lambda _feature: {
                    "color": "#dc2626",
                    "weight": 4,
                    "fillColor": "#facc15",
                    "fillOpacity": 0.45
                }
            ).add_to(mapa)
            folium.Marker(
                centro,
                tooltip="Centro del recinto",
                popup=etiqueta
            ).add_to(mapa)
            mapa.fit_bounds(
                [
                    [bounds["lat_min"], bounds["lon_min"]],
                    [bounds["lat_max"], bounds["lon_max"]]
                ],
                padding=(20, 20)
            )

            return mapa, bounds, centro


        def _parcela_sigpac_desde_conn(conn, parcela_id):

            cursor = conn.execute(_sql_parcela_sigpac(conn), (int(parcela_id),))
            fila = cursor.fetchone()

            if fila is None:

                return None

            columnas = [descripcion[0] for descripcion in cursor.description]

            return dict(zip(columnas, fila))


        def guardar_geometria_sigpac_parcela(conn, parcela_id):

            parcela = _parcela_sigpac_desde_conn(conn, parcela_id)

            if parcela is None:

                return None, {
                    "estado": "error",
                    "error": "No se encontró la parcela indicada"
                }

            sin_codigos = _faltan_codigos_sigpac_numericos(parcela)

            if sin_codigos:

                mensaje = "Faltan códigos SIGPAC numéricos."
                _actualizar_parcela_sigpac(
                    conn,
                    parcela_id,
                    {
                        "sigpac_geojson_estado": "error",
                        "sigpac_geojson_error": mensaje,
                    },
                )
                conn.commit()

                return None, {"estado": "error", "error": mensaje}

            geojson, diagnostico = buscar_geometria_sigpac(parcela)

            if geojson is not None:

                actualizado = datetime.now().isoformat(timespec="seconds")
                _actualizar_parcela_sigpac(
                    conn,
                    parcela_id,
                    {
                        "sigpac_geojson": json.dumps(
                            geojson,
                            ensure_ascii=False,
                        ),
                        "sigpac_geojson_actualizado": actualizado,
                        "sigpac_geojson_estado": "ok",
                        "sigpac_geojson_error": None,
                    },
                )
                conn.commit()

                return geojson, {
                    "estado": "ok",
                    "actualizado": actualizado,
                    "diagnostico": diagnostico
                }

            mensaje = "; ".join(
                diagnostico.get("errores", [])
            ) or "No se encontró geometría SIGPAC"
            _actualizar_parcela_sigpac(
                conn,
                parcela_id,
                {
                    "sigpac_geojson_estado": "error",
                    "sigpac_geojson_error": mensaje,
                },
            )
            conn.commit()

            return None, {"estado": "error", "error": mensaje}


        def obtener_geojson_parcela_desde_cache_o_sigpac(
            conn,
            parcela_id,
            forzar=False
        ):

            parcela = _parcela_sigpac_desde_conn(conn, parcela_id)

            if parcela is None:

                return None, {
                    "estado": "error",
                    "error": "No se encontró la parcela indicada"
                }

            texto_geojson = parcela.get("sigpac_geojson")
            estado_geojson = str(
                parcela.get("sigpac_geojson_estado") or ""
            ).strip()
            pendiente_actualizacion = (
                estado_geojson == "pendiente_actualizacion"
            )

            if texto_geojson and not forzar and not pendiente_actualizacion:

                try:

                    geojson = normalizar_geojson_sigpac(
                        json.loads(texto_geojson)
                    )

                    return geojson, {
                        "estado": parcela.get(
                            "sigpac_geojson_estado"
                        ) or "Con geometría",
                        "actualizado": parcela.get(
                            "sigpac_geojson_actualizado"
                        ),
                        "desde_cache": True
                    }

                except (ValueError, TypeError, json.JSONDecodeError):

                    pass

            return guardar_geometria_sigpac_parcela(conn, parcela_id)


        def actualizar_geometrias_sigpac(ids_parcelas, forzar=False):

            ids = [int(valor) for valor in ids_parcelas]

            if not ids:

                return {"ok": 0, "error": 0, "sin_codigos": 0}

            progreso = st.progress(0, text="Preparando consulta SIGPAC...")
            resultados = {"ok": 0, "error": 0, "sin_codigos": 0}
            conn_actualizacion = conectar()

            try:

                for indice, parcela_id in enumerate(ids, start=1):

                    progreso.progress(
                        (indice - 1) / len(ids),
                        text=(
                            f"Consultando parcela {indice} de {len(ids)} "
                            f"(ID {parcela_id})"
                        )
                    )
                    _, resultado = (
                        obtener_geojson_parcela_desde_cache_o_sigpac(
                            conn_actualizacion,
                            parcela_id,
                            forzar=forzar
                        )
                    )
                    estado = resultado.get("estado", "error")
                    resultados[estado] = resultados.get(estado, 0) + 1

                progreso.progress(1.0, text="Actualización SIGPAC terminada")

            finally:

                conn_actualizacion.close()

            return resultados


        estado_inicial = _leer_estado_geometrias()

        if estado_inicial.empty:

            st.warning("No hay parcelas registradas para mostrar")
            st.stop()

        geojson_vacio_inicial = (
            estado_inicial["sigpac_geojson"].fillna("").astype(str) == ""
        )
        estado_geojson_inicial = (
            estado_inicial["sigpac_geojson_estado"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        ids_automaticos = estado_inicial.loc[
            estado_geojson_inicial == "pendiente_actualizacion",
            "id"
        ].tolist()

        if ids_automaticos:

            st.info(
                f"Se consultarán {len(ids_automaticos)} parcelas sin "
                "geometría almacenada o pendientes de actualización."
            )
            actualizar_geometrias_sigpac(ids_automaticos)

        estado_botones = _leer_estado_geometrias()
        geojson_vacio_botones = (
            estado_botones["sigpac_geojson"].fillna("").astype(str) == ""
        )
        estado_geojson_botones = (
            estado_botones["sigpac_geojson_estado"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        ids_pendientes = estado_botones.loc[
            geojson_vacio_botones
            | (estado_geojson_botones == "pendiente_actualizacion"),
            "id"
        ].tolist()
        columna_pendientes, columna_reconsulta = st.columns(2)

        with columna_pendientes:

            actualizar_pendientes = st.button(
                "Actualizar geometrías SIGPAC pendientes",
                disabled=not ids_pendientes,
                use_container_width=True
            )

        with columna_reconsulta:

            confirmar_reconsulta = st.checkbox(
                "Confirmo que quiero reconsultar todas las geometrías",
                key="confirmar_reconsulta_sigpac"
            )
            reconsultar_todas = st.button(
                "Reconsultar todas las geometrías",
                disabled=not confirmar_reconsulta,
                use_container_width=True
            )

        if actualizar_pendientes:

            resultado_actualizacion = actualizar_geometrias_sigpac(
                ids_pendientes,
                forzar=True
            )
            st.success(
                "Actualización terminada: "
                f"{resultado_actualizacion.get('ok', 0)} correctas, "
                f"{resultado_actualizacion.get('error', 0)} con error y "
                f"{resultado_actualizacion.get('sin_codigos', 0)} sin "
                "códigos."
            )

        if reconsultar_todas:

            resultado_actualizacion = actualizar_geometrias_sigpac(
                estado_botones["id"].tolist(),
                forzar=True
            )
            st.success(
                "Reconsulta terminada: "
                f"{resultado_actualizacion.get('ok', 0)} correctas, "
                f"{resultado_actualizacion.get('error', 0)} con error y "
                f"{resultado_actualizacion.get('sin_codigos', 0)} sin "
                "códigos."
            )

        parcelas_mapa = _leer_parcelas_mapa()

        with conectar() as conn_contexto:

            campana_contexto_id = _obtener_campana_contexto_mapa(conn_contexto)

        if campana_contexto_id is None:

            st.warning(
                "No hay campaña activa. El mapa mostrará parcelas sin "
                "mezclar cultivos de campañas históricas."
            )

        cultivos_mapa = _leer_cultivos_mapa(campana_contexto_id)
        cultivos_por_parcela = {}

        for _, cultivo in cultivos_mapa.iterrows():

            parcela_id = int(cultivo["parcela_id"])
            especie = _texto_mapa(cultivo["especie"]).upper()
            variedad = _texto_mapa(cultivo["variedad"]).upper()
            sistema = _texto_mapa(cultivo["sistema"]).upper()
            arboles = _formatear_arboles_mapa(cultivo["arboles"])

            cultivos_por_parcela.setdefault(parcela_id, []).append(
                {
                    "texto": _resumir_cultivo_mapa(cultivo) or "Sin detalle",
                    "especie": especie,
                    "variedad": variedad,
                    "sistema": sistema,
                    "arboles": arboles
                }
            )

        features_mapa = []
        errores_cache = []

        for _, parcela in parcelas_mapa.iterrows():

            texto_geojson = parcela["sigpac_geojson"]

            if pd.isna(texto_geojson) or not str(texto_geojson).strip():

                continue

            try:

                geojson = normalizar_geojson_sigpac(
                    json.loads(str(texto_geojson))
                )

            except (ValueError, TypeError, json.JSONDecodeError) as error:

                errores_cache.append(
                    {
                        "id": int(parcela["id"]),
                        "nombre": parcela["nombre"],
                        "provincia": parcela["provincia"],
                        "municipio": parcela["municipio"],
                        "poligono": parcela["poligono"],
                        "parcela": parcela["parcela"],
                        "recinto": parcela["recinto"],
                        "sigpac_geojson_estado": "cache_invalida",
                        "sigpac_geojson_error": str(error),
                    }
                )

                continue

            parcela_id = int(parcela["id"])
            cultivos = cultivos_por_parcela.get(parcela_id, [])
            cultivos_texto = ", ".join(
                dict.fromkeys(
                    cultivo["texto"]
                    for cultivo in cultivos
                    if cultivo["texto"]
                )
            ) or "Sin cultivo en campaña activa"
            especies = "; ".join(
                dict.fromkeys(
                    cultivo["especie"]
                    for cultivo in cultivos
                    if cultivo["especie"]
                )
            ) or "—"
            variedades = "; ".join(
                dict.fromkeys(
                    cultivo["variedad"]
                    for cultivo in cultivos
                    if cultivo["variedad"]
                )
            ) or "—"
            sistemas = "; ".join(
                dict.fromkeys(
                    cultivo["sistema"]
                    for cultivo in cultivos
                    if cultivo["sistema"]
                )
            ) or "—"
            arboles = "; ".join(
                cultivo["arboles"]
                for cultivo in cultivos
                if cultivo["arboles"]
            ) or "—"
            referencia = (
                f"Pol. {parcela['poligono']} "
                f"Parc. {parcela['parcela']} Rec. {parcela['recinto']}"
            )
            referencia_compacta = (
                f"Pol. {parcela['poligono']} · "
                f"Parc. {parcela['parcela']} · Rec. {parcela['recinto']}"
            )
            superficie_sigpac = (
                None
                if pd.isna(parcela["superficie_sigpac"])
                else float(parcela["superficie_sigpac"])
            )
            nombre_parcela = (
                referencia
                if pd.isna(parcela["nombre"])
                or not str(parcela["nombre"]).strip()
                else str(parcela["nombre"]).strip()
            )
            estilo_cultivo = obtener_color_cultivo(cultivos_texto)
            tooltip_html = construir_tooltip_parcela_mapa(
                {
                    **parcela.to_dict(),
                    "nombre": nombre_parcela,
                },
                cultivos,
            )

            for feature in geojson["features"]:

                feature_mapa = json.loads(json.dumps(feature))
                feature_mapa["properties"] = {
                    **feature_mapa.get("properties", {}),
                    "id_parcela": parcela_id,
                    "nombre": nombre_parcela,
                    "provincia": parcela["provincia"] or "—",
                    "municipio": parcela["municipio"] or "—",
                    "poligono": parcela["poligono"],
                    "parcela": parcela["parcela"],
                    "recinto": parcela["recinto"],
                    "referencia_sigpac": referencia,
                    "referencia_sigpac_compacta": referencia_compacta,
                    "superficie_sigpac": superficie_sigpac,
                    "superficie_mapa": (
                        f"{_formatear_superficie_mapa(superficie_sigpac)} ha"
                        if superficie_sigpac is not None
                        else "—"
                    ),
                    "cultivos_texto": cultivos_texto,
                    "tooltip_html": tooltip_html,
                    "especie": especies,
                    "variedad": variedades,
                    "sistema": sistemas,
                    "arboles": arboles,
                    "color_relleno": estilo_cultivo["fillColor"],
                    "color_borde": estilo_cultivo["color"],
                    "opacidad_relleno": estilo_cultivo["fillOpacity"],
                    "grosor_borde": estilo_cultivo["weight"],
                    "estado_geometria": (
                        _estado_geometria_visual(
                            parcela["sigpac_geojson_estado"],
                            parcela["sigpac_geojson"],
                        )
                    )
                }
                features_mapa.append(feature_mapa)

        feature_collection = {
            "type": "FeatureCollection",
            "features": features_mapa
        }
        mapa_general = folium.Map(
            location=[38.48, -1.32],
            tiles=None,
            zoom_start=12,
            control_scale=True
        )
        folium.raster_layers.WmsTileLayer(
            url="https://www.ign.es/wms-inspire/pnoa-ma",
            layers="OI.OrthoimageCoverage",
            name="Ortofoto PNOA",
            fmt="image/jpeg",
            transparent=False,
            overlay=False,
            control=True,
            show=True,
            attr="PNOA © IGN/SCNE, CC BY 4.0"
        ).add_to(mapa_general)
        folium.TileLayer(
            "OpenStreetMap",
            name="OpenStreetMap",
            overlay=False,
            control=True,
            show=False
        ).add_to(mapa_general)

        _agregar_radar_lluvia(mapa_general, folium)

        if features_mapa:

            folium.GeoJson(
                feature_collection,
                name="Parcelas de la explotación",
                style_function=lambda feature: {
                    "color": feature["properties"]["color_borde"],
                    "weight": feature["properties"]["grosor_borde"],
                    "fillColor": feature["properties"]["color_relleno"],
                    "fillOpacity": feature["properties"][
                        "opacidad_relleno"
                    ]
                },
                highlight_function=lambda _feature: {
                    "color": "#ffffff",
                    "weight": 5,
                    "fillOpacity": 0.45
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["tooltip_html"],
                    aliases=[""],
                    labels=False,
                    sticky=True,
                    max_width=420,
                    style=(
                        "max-width:360px;font-size:12px;line-height:1.25;"
                        "padding:6px 8px;"
                    ),
                ),
                popup=folium.GeoJsonPopup(
                    fields=[
                        "nombre",
                        "referencia_sigpac",
                        "superficie_sigpac",
                        "cultivos_texto",
                        "variedad",
                        "sistema",
                        "arboles",
                        "estado_geometria"
                    ],
                    aliases=[
                        "Parcela:",
                        "SIGPAC:",
                        "Superficie (ha):",
                        "Cultivo:",
                        "Variedad:",
                        "Sistema:",
                        "Árboles:",
                        "Estado geometría:"
                    ],
                    localize=True
                )
            ).add_to(mapa_general)
            bounds_globales = calcular_bounds_geojson(feature_collection)
            mapa_general.fit_bounds(
                [
                    [
                        bounds_globales["lat_min"],
                        bounds_globales["lon_min"]
                    ],
                    [
                        bounds_globales["lat_max"],
                        bounds_globales["lon_max"]
                    ]
                ],
                padding=(20, 20)
            )

        else:

            st.warning(
                "No hay geometrías SIGPAC disponibles todavía. El mapa se "
                "centra provisionalmente en Jumilla."
            )

        folium.LayerControl(collapsed=False).add_to(mapa_general)
        st.markdown(
            """
            <div style="margin: 0.5rem 0 0.75rem 0;">
              <strong>Colores por cultivo</strong>&nbsp;&nbsp;
              <span style="display:inline-block;width:14px;height:14px;
                    background:green;border:1px solid darkgreen;"></span>
              Verde: Almendro&nbsp;&nbsp;
              <span style="display:inline-block;width:14px;height:14px;
                    background:blue;border:1px solid darkblue;"></span>
              Azul: Olivar&nbsp;&nbsp;
              <span style="display:inline-block;width:14px;height:14px;
                    background:white;border:1px solid black;"></span>
              Blanco: Tierra arable&nbsp;&nbsp;
              <span style="display:inline-block;width:14px;height:14px;
                    background:lightgray;border:1px solid gray;"></span>
              Gris: Sin cultivo / otro
            </div>
            """,
            unsafe_allow_html=True
        )
        st.caption(
            "La capa opcional **Radar de lluvia** muestra observaciones de las "
            "últimas dos horas y requiere conexión a Internet. No es una "
            "predicción. Datos de [RainViewer](https://www.rainviewer.com/)."
        )
        st_folium(
            mapa_general,
            height=700,
            use_container_width=True,
            key="mapa_general_sigpac"
        )

        diagnostico_mapa = _leer_parcelas_mapa()
        total_parcelas = len(diagnostico_mapa)
        con_geometria = int(
            (
                diagnostico_mapa["sigpac_geojson"]
                .fillna("")
                .astype(str)
                .str.strip() != ""
            ).sum()
        )
        pendientes = total_parcelas - con_geometria
        ids_con_error = set(
            diagnostico_mapa.loc[
                diagnostico_mapa["sigpac_geojson_estado"]
                .fillna("")
                .isin(["error", "sin_codigos"]),
                "id"
            ].astype(int).tolist()
        )
        ids_con_error.update(
            int(error["id"])
            for error in errores_cache
        )
        con_error = len(ids_con_error)
        fechas_actualizacion = pd.to_datetime(
            diagnostico_mapa["sigpac_geojson_actualizado"],
            errors="coerce"
        ).dropna()
        ultima_actualizacion = (
            fechas_actualizacion.max().strftime("%Y-%m-%d %H:%M:%S")
            if not fechas_actualizacion.empty
            else "Sin actualizaciones"
        )
        st.subheader("Diagnóstico de geometrías SIGPAC")
        metrica_total, metrica_geo, metrica_pendientes, metrica_error = (
            st.columns(4)
        )
        metrica_total.metric("Parcelas", total_parcelas)
        metrica_geo.metric("Con geometría", con_geometria)
        metrica_pendientes.metric("Pendientes", pendientes)
        metrica_error.metric("Con error", con_error)
        st.caption(f"Última actualización: {ultima_actualizacion}")
        tabla_errores = diagnostico_mapa[
            diagnostico_mapa["sigpac_geojson_estado"]
            .fillna("")
            .isin(["error", "sin_codigos"])
        ][
            [
                "id",
                "nombre",
                "provincia",
                "municipio",
                "poligono",
                "parcela",
                "recinto",
                "sigpac_geojson_estado",
                "sigpac_geojson_error"
            ]
        ].copy()

        if errores_cache:

            tabla_errores = pd.concat(
                [tabla_errores, pd.DataFrame(errores_cache)],
                ignore_index=True,
                sort=False
            )

        if not tabla_errores.empty and "id" in tabla_errores.columns:

            tabla_errores = tabla_errores.drop_duplicates(
                subset=["id"],
                keep="last"
            )

        if not tabla_errores.empty:

            st.dataframe(
                preparar_dataframe_visual(
                    tabla_errores,
                    ocultar_tecnicas=True,
                ),
                hide_index=True,
                use_container_width=True
            )

    except Exception as error:

        st.error(f"Error al mostrar Mapas / SIGPAC: {error}")
