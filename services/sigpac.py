import requests


SIGPAC_BASE_URL = (
    "https://sigpac-hubcloud.es/servicioconsultassigpac/query"
)


def _coordenadas_geojson(geojson):

    if not isinstance(geojson, dict):

        return []

    if geojson.get("type") == "Feature":

        return _coordenadas_geojson(geojson.get("geometry", {}))

    if geojson.get("type") == "FeatureCollection":

        return [
            punto
            for feature in geojson.get("features", [])
            for punto in _coordenadas_geojson(feature)
        ]

    puntos = []

    def recorrer(coordenadas):

        if (
            isinstance(coordenadas, (list, tuple))
            and len(coordenadas) >= 2
            and isinstance(coordenadas[0], (int, float))
            and isinstance(coordenadas[1], (int, float))
        ):

            puntos.append([coordenadas[0], coordenadas[1]])
            return

        if isinstance(coordenadas, (list, tuple)):

            for elemento in coordenadas:

                recorrer(elemento)

    recorrer(geojson.get("coordinates", []))

    return puntos


def normalizar_geojson_sigpac(datos):

    if not isinstance(datos, dict):

        raise ValueError(
            "SIGPAC devolvio una estructura distinta de GeoJSON"
        )

    tipo = datos.get("type")

    if tipo == "FeatureCollection":

        features = datos.get("features")

        if not isinstance(features, list):

            raise ValueError(
                "El FeatureCollection recibido no contiene una lista "
                "de features"
            )

        normalizado = {
            "type": "FeatureCollection",
            "features": features,
        }

    elif tipo == "Feature":

        normalizado = {
            "type": "FeatureCollection",
            "features": [datos],
        }

    elif tipo in ("Polygon", "MultiPolygon"):

        normalizado = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": datos,
                }
            ],
        }

    else:

        raise ValueError(
            "SIGPAC devolvio un tipo GeoJSON no compatible: "
            f"{tipo or 'sin tipo'}"
        )

    features_validas = []

    for feature in normalizado["features"]:

        if not isinstance(feature, dict):

            continue

        geometria = feature.get("geometry") or {}

        if geometria.get("type") in ("Polygon", "MultiPolygon"):

            feature.setdefault("properties", {})
            features_validas.append(feature)

    normalizado["features"] = features_validas

    if not features_validas:

        raise ValueError(
            "La respuesta SIGPAC no contiene geometrias Polygon o "
            "MultiPolygon validas"
        )

    return normalizado


def calcular_bounds_geojson(geojson):

    puntos = _coordenadas_geojson(geojson)

    if not puntos:

        raise ValueError(
            "No se pudieron calcular los limites de la geometria"
        )

    longitudes = [punto[0] for punto in puntos]
    latitudes = [punto[1] for punto in puntos]

    if (
        any(abs(longitud) > 180 for longitud in longitudes)
        or any(abs(latitud) > 90 for latitud in latitudes)
    ):

        raise ValueError(
            "Las coordenadas recibidas no parecen geograficas"
        )

    lon_min = min(longitudes)
    lon_max = max(longitudes)
    lat_min = min(latitudes)
    lat_max = max(latitudes)

    return {
        "lat_min": lat_min,
        "lat_max": lat_max,
        "lon_min": lon_min,
        "lon_max": lon_max,
        "centro_lat": (lat_min + lat_max) / 2,
        "centro_lon": (lon_min + lon_max) / 2,
    }


def valor_entero_sigpac(valor, campo):

    try:

        texto = str(valor).strip()
        numero = float(texto)

        if not numero.is_integer():

            raise ValueError

        return int(numero)

    except (TypeError, ValueError):

        raise ValueError(
            f"El campo {campo} no contiene un codigo numerico valido"
        )


def _esta_vacio(valor):

    if valor is None:

        return True

    try:

        if valor != valor:

            return True

    except TypeError:

        pass

    return str(valor).strip() == ""


def faltan_codigos_sigpac_numericos(parcela):

    campos_obligatorios = [
        "provincia_sigpac",
        "municipio_sigpac",
        "poligono",
        "parcela",
        "recinto",
    ]

    for campo in campos_obligatorios:

        valor = parcela.get(campo)

        if _esta_vacio(valor):

            return True

        try:

            valor_entero_sigpac(valor, campo)

        except ValueError:

            return True

    for campo in ["agregado_sigpac", "zona_sigpac"]:

        valor = parcela.get(campo)

        if _esta_vacio(valor):

            continue

        try:

            valor_entero_sigpac(valor, campo)

        except ValueError:

            return True

    return False


def _numero_desde_valor(valor):

    if valor is None:

        return None

    if isinstance(valor, bool):

        return None

    try:

        if isinstance(valor, str):

            texto = valor.strip()

            if not texto:

                return None

            texto = texto.replace(" ", "")

            if "," in texto and "." in texto:

                texto = texto.replace(".", "").replace(",", ".")

            elif "," in texto:

                texto = texto.replace(",", ".")

            numero = float(texto)

        else:

            numero = float(valor)

    except (TypeError, ValueError):

        return None

    if numero < 0:

        return None

    return numero


def _clave_normalizada(clave):

    return (
        str(clave or "")
        .strip()
        .casefold()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


def extraer_superficie_ha(propiedades):

    if not isinstance(propiedades, dict):

        return None

    prioridad = [
        "superficie",
        "superficieha",
        "sup",
        "supha",
        "area",
        "areaha",
        "dnsurface",
        "cdsurface",
    ]
    propiedades_normalizadas = {
        _clave_normalizada(clave): valor
        for clave, valor in propiedades.items()
    }

    for clave in prioridad:

        numero = _numero_desde_valor(propiedades_normalizadas.get(clave))

        if numero is not None:

            return numero

    indicadores = ["superficie", "sup", "area", "surface"]

    for clave, valor in propiedades.items():

        clave_normalizada = _clave_normalizada(clave)

        if not any(indicador in clave_normalizada for indicador in indicadores):

            continue

        numero = _numero_desde_valor(valor)

        if numero is None:

            continue

        if clave_normalizada.endswith("m2"):

            return numero / 10000

        return numero

    return None


def obtener_recinto_sigpac_por_codigo(
    provincia,
    municipio,
    agregado,
    zona,
    poligono,
    parcela,
    recinto,
):

    url = (
        f"{SIGPAC_BASE_URL}/recinfo/"
        f"{provincia}/{municipio}/{agregado}/{zona}/"
        f"{poligono}/{parcela}/{recinto}.geojson"
    )
    status_code = None

    try:

        respuesta = requests.get(url, timeout=25)
        status_code = respuesta.status_code

        if status_code != 200:

            return None, (
                f"SIGPAC respondio con HTTP {status_code} al "
                "consultar el recinto"
            ), url, status_code

        return respuesta.json(), None, url, status_code

    except requests.RequestException as error:

        return None, (
            f"No se pudo consultar el recinto SIGPAC: {error}"
        ), url, None

    except ValueError as error:

        return None, (
            f"SIGPAC no devolvio JSON valido: {error}"
        ), url, status_code


def obtener_recintos_parcela_sigpac(
    provincia,
    municipio,
    agregado,
    zona,
    poligono,
    parcela,
    recinto_solicitado=None,
):

    url = (
        f"{SIGPAC_BASE_URL}/recinfoparc/"
        f"{provincia}/{municipio}/{agregado}/{zona}/"
        f"{poligono}/{parcela}.geojson"
    )
    status_code = None

    try:

        respuesta = requests.get(url, timeout=25)
        status_code = respuesta.status_code

        if status_code != 200:

            return None, (
                f"SIGPAC respondio con HTTP {status_code} al "
                "consultar la parcela"
            ), url, status_code, None, 0

        datos = normalizar_geojson_sigpac(respuesta.json())
        features = datos["features"]
        feature_elegida = None

        if recinto_solicitado is not None:

            for feature in features:

                propiedades = feature.get("properties", {})

                try:

                    if int(propiedades.get("recinto")) == int(
                        recinto_solicitado
                    ):

                        feature_elegida = feature
                        break

                except (TypeError, ValueError):

                    continue

        aviso = None

        if feature_elegida is None:

            feature_elegida = features[0]
            aviso = (
                "No se encontro el recinto solicitado dentro de la "
                "parcela; se muestra la primera feature como diagnostico."
            )

        seleccionado = {
            "type": "FeatureCollection",
            "features": [feature_elegida],
        }

        return (
            seleccionado,
            None,
            url,
            status_code,
            aviso,
            len(features),
        )

    except requests.RequestException as error:

        return None, (
            f"No se pudo consultar la parcela SIGPAC: {error}"
        ), url, None, None, 0

    except (ValueError, IndexError) as error:

        return None, str(error), url, status_code, None, 0


def buscar_geometria_sigpac(parcela):

    diagnostico = {
        "provincia_texto": parcela.get("provincia"),
        "municipio_texto": parcela.get("municipio"),
        "provincia_sigpac": parcela.get("provincia_sigpac"),
        "municipio_sigpac": parcela.get("municipio_sigpac"),
        "agregado_sigpac": parcela.get("agregado_sigpac"),
        "zona_sigpac": parcela.get("zona_sigpac"),
        "poligono": parcela.get("poligono"),
        "parcela": parcela.get("parcela"),
        "recinto": parcela.get("recinto"),
        "url_recinfo": "",
        "url_recinfoparc": "",
        "status_code_recinfo": None,
        "status_code_recinfoparc": None,
        "numero_features": 0,
        "tipo_geometria": "",
        "propiedades_recibidas": {},
        "superficie_sigpac": None,
        "uso_sigpac": None,
        "bounds": None,
        "centro": None,
        "avisos": [],
        "errores": [],
    }

    try:

        provincia_sigpac = parcela.get("provincia_sigpac")
        municipio_sigpac = parcela.get("municipio_sigpac")

        if faltan_codigos_sigpac_numericos(parcela):

            raise ValueError("Faltan codigos SIGPAC numericos.")

        provincia = valor_entero_sigpac(
            provincia_sigpac,
            "provincia_sigpac",
        )
        municipio = valor_entero_sigpac(
            municipio_sigpac,
            "municipio_sigpac",
        )
        agregado = valor_entero_sigpac(
            (
                0
                if _esta_vacio(parcela.get("agregado_sigpac"))
                else parcela.get("agregado_sigpac")
            ),
            "agregado_sigpac",
        )
        zona = valor_entero_sigpac(
            (
                0
                if _esta_vacio(parcela.get("zona_sigpac"))
                else parcela.get("zona_sigpac")
            ),
            "zona_sigpac",
        )
        poligono = valor_entero_sigpac(
            parcela.get("poligono"),
            "poligono",
        )
        numero_parcela = valor_entero_sigpac(
            parcela.get("parcela"),
            "parcela",
        )
        recinto = valor_entero_sigpac(
            parcela.get("recinto"),
            "recinto",
        )

        datos, error_recinto, url_recinto, status_recinto = (
            obtener_recinto_sigpac_por_codigo(
                provincia,
                municipio,
                agregado,
                zona,
                poligono,
                numero_parcela,
                recinto,
            )
        )
        diagnostico["url_recinfo"] = url_recinto
        diagnostico["status_code_recinfo"] = status_recinto
        geojson = None

        if datos is not None:

            try:

                geojson = normalizar_geojson_sigpac(datos)

            except ValueError as error:

                error_recinto = str(error)

        if geojson is None:

            if error_recinto:

                diagnostico["avisos"].append(
                    f"Consulta de recinto: {error_recinto}. Se usa "
                    "la consulta de parcela como alternativa."
                )

            (
                geojson,
                error_parcela,
                url_parcela,
                status_parcela,
                aviso_fallback,
                numero_features,
            ) = obtener_recintos_parcela_sigpac(
                provincia,
                municipio,
                agregado,
                zona,
                poligono,
                numero_parcela,
                recinto,
            )
            diagnostico["url_recinfoparc"] = url_parcela
            diagnostico["status_code_recinfoparc"] = status_parcela
            diagnostico["numero_features"] = numero_features

            if aviso_fallback:

                diagnostico["avisos"].append(aviso_fallback)

            if geojson is None:

                raise LookupError(
                    error_parcela
                    or "No se encontro geometria SIGPAC"
                )

        else:

            diagnostico["numero_features"] = len(geojson["features"])

        feature = geojson["features"][0]
        geometria = feature.get("geometry", {})
        propiedades = feature.get("properties", {})
        bounds = calcular_bounds_geojson(geojson)
        superficie = extraer_superficie_ha(propiedades)

        if superficie is None:

            diagnostico["avisos"].append(
                "SIGPAC devolvio geometria, pero no se encontro superficie "
                "en las propiedades."
            )

        diagnostico.update(
            {
                "tipo_geometria": geometria.get("type", ""),
                "propiedades_recibidas": propiedades,
                "superficie_sigpac": superficie,
                "uso_sigpac": propiedades.get("uso_sigpac"),
                "bounds": bounds,
                "centro": {
                    "lat": bounds["centro_lat"],
                    "lon": bounds["centro_lon"],
                },
            }
        )

        return geojson, diagnostico

    except Exception as error:

        diagnostico["errores"].append(str(error))

        return None, diagnostico


def consultar_recinto_sigpac(
    provincia,
    municipio,
    agregado,
    zona,
    poligono,
    parcela,
    recinto,
):

    geojson, diagnostico = buscar_geometria_sigpac(
        {
            "provincia_sigpac": provincia,
            "municipio_sigpac": municipio,
            "agregado_sigpac": agregado,
            "zona_sigpac": zona,
            "poligono": poligono,
            "parcela": parcela,
            "recinto": recinto,
        }
    )

    if geojson is None:

        return {
            "ok": False,
            "geojson": None,
            "superficie_ha": None,
            "error": "; ".join(diagnostico.get("errores", []))
            or "SIGPAC no devolvio informacion para ese recinto.",
            "diagnostico": diagnostico,
        }

    return {
        "ok": True,
        "geojson": geojson,
        "superficie_ha": diagnostico.get("superficie_sigpac"),
        "error": "",
        "diagnostico": diagnostico,
    }
