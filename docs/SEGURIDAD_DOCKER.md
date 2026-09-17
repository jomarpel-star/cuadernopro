# Mantenimiento de seguridad de Docker

## Cambios preparados el 17 de septiembre de 2026

- Base `python:3.13-slim-trixie` con actualización de los paquetes de Debian
  durante la construcción. Se mantiene Python 3.13.
- Dependencias directas en `requirements.in`; cierre completo de dependencias,
  versiones exactas, marcadores de plataforma y hashes en `requirements.txt`.
- Streamlit 1.64.0, que ya no necesita GitPython. La CI comprueba que GitPython
  no reaparece en la imagen.
- Instalación mediante wheels y hashes obligatorios, seguida de `pip check`.
- Tras instalar y comprobar las dependencias, se retiran `pip` y `ensurepip`
  de la imagen final. La aplicación no los necesita para funcionar. Esto elimina
  las copias internas de msgpack 1.1.2 y setuptools 70.3.0 que Trivy detectó en
  pip 26.2.1 durante la primera construcción. Las dependencias se actualizan
  reconstruyendo la imagen, no instalando paquetes en el contenedor en marcha.
- Exclusión del contexto Docker de `.venv`, herramientas locales, artefactos de
  compilación y catálogos privados, además de los datos ya excluidos.
- Los dos Compose prohíben ganar privilegios y retiran las capacidades Linux
  salvo `DAC_OVERRIDE`, necesaria para conservar acceso a bind mounts que
  pertenecen a otro usuario. Portainer limita el puerto a `127.0.0.1` por defecto.
- Acciones de GitHub fijadas a commits y revisiones semanales con Dependabot.

Se conservan las rutas y los volúmenes existentes. No se cambia el esquema de
datos. La versión de esta actualización es 8.4.11. El cambio de usuario
del contenedor queda pendiente de una migración de permisos probada con volúmenes
existentes; retirar capacidades no equivale a ejecutar como usuario no root.

## Comprobaciones locales

La instalación de prueba utiliza un entorno virtual separado con Python 3.13.
Las pruebas se ejecutan sobre una copia del código y bases sintéticas, sin abrir
las bases ni los documentos de la instalación real.

- Auditoría de PyPI con `pip-audit 2.10.1`: 54 dependencias, ninguna omitida,
  cero vulnerabilidades conocidas el 17 de septiembre de 2026.
- Instalación completa en Windows con verificación de hashes y `pip check`.
- Resolución en seco de 53 dependencias para cada una de las plataformas Linux
  AMD64 y ARM64, utilizando únicamente wheels. La diferencia con Windows es
  `tzdata`, condicionado por plataforma.
- Batería `scripts/probar_release_v8.py`: 22 comprobaciones correctas, incluida
  una prueba de arranque y rerun
  real del código de `app.py` mediante Streamlit AppTest con una base temporal.
- Validación de los workflows con actionlint y de la sintaxis YAML.

Docker y WSL no están instalados en el entorno local utilizado. Estas
comprobaciones no sustituyen la construcción, el arranque ni el escaneo de la
imagen Linux. No se afirma que las 102 alertas de la imagen anterior hayan
desaparecido. Tampoco actualizan una imagen ya publicada ni un contenedor activo.

## Controles antes de publicar

El workflow `security.yml` se ejecuta en pull requests, en cambios de `main`,
manualmente y cada semana. `docker-publish.yml` lo reutiliza para comprobar el
commit exacto de la etiqueta que se va a publicar.

1. Auditar las dependencias fijadas con PyPI tanto en Windows como en Linux.
   Cualquier vulnerabilidad detectada por `pip-audit` bloquea el proceso.
2. Construir imágenes AMD64 y ARM64 en runners nativos, descargando la base
   actualizada y sin reutilizar capas de construcción.
3. Guardar el informe completo de Trivy y un SBOM CycloneDX por arquitectura.
4. Bloquear la publicación si Trivy detecta vulnerabilidades altas o críticas
   para las que exista una corrección. El informe completo también conserva las
   vulnerabilidades sin corrección y las de menor severidad: hay que revisarlas.
5. Verificar dependencias durante la construcción, ausencia de GitPython,
   pip y ensurepip en la imagen final y la batería de pruebas dentro
   de cada imagen, sin red y con las restricciones de capacidades de Compose.
   Comprobar también la escritura en un bind mount con permisos restringidos y
   que sus datos siguen disponibles tras recrear el contenedor.
6. Exportar las imágenes comprobadas. El job de publicación carga esos mismos
   archivos, verifica arquitectura, versión y commit, y los publica sin volver
   a construir. Solo después de superar ambas arquitecturas actualiza las
   etiquetas de versión y `latest`.

Los informes se conservan como artefactos de Actions durante 14 días. Las
imágenes temporales para publicar se conservan durante un día. Si se reintenta
una publicación después de ese plazo, hay que volver a ejecutar todo el workflow.
Las etiquetas `build-<ejecución>-<intento>-<arquitectura>` de Docker Hub identifican
los componentes utilizados para crear el manifiesto multi-arquitectura.

Un fallo al descargar la base de vulnerabilidades o al ejecutar el analizador
bloquea la publicación. No se han añadido excepciones para ocultar los avisos.

## Actualizar las dependencias

Usar Python 3.13 y un entorno dedicado a herramientas. La aplicación solo necesita
instalar `requirements.txt`; no necesita instalar uv ni pip-audit.

```bash
python -m pip install uv==0.12.15 pip-audit==2.10.1
uv pip compile requirements.in --universal --python-version 3.13 --generate-hashes --upgrade --output-file requirements.txt
python -m pip_audit --require-hashes --disable-pip -r requirements.txt
```

Después, instalar en un entorno limpio y ejecutar las pruebas:

```bash
python -m pip install --require-hashes --only-binary=:all: -r requirements.txt
python -m pip check
python -m py_compile app.py
python scripts/probar_release_v8.py
```

Ejecutar las pruebas en una copia de desarrollo con datos sintéticos. Los scripts
existentes crean y sustituyen sus propias bases de prueba bajo `runtime/`.
No generar el lock mediante `pip freeze` de una instalación de usuario: podría
incluir herramientas y dependencias ajenas a la aplicación.

## Construir y comprobar una candidata local

En un equipo con Docker:

```bash
docker build --pull --no-cache -t cuadernopro:security .
docker run --rm --network none --cap-drop ALL --cap-add DAC_OVERRIDE --security-opt no-new-privileges=true cuadernopro:security python scripts/probar_release_v8.py
docker scout quickview cuadernopro:security
docker scout cves cuadernopro:security
```

Antes de actualizar una instalación, comprobar backup y restauración, acceso
HTTP, mapas, PDF/Excel y persistencia después de recrear el contenedor con el
mismo volumen. Las pruebas de Docker pendientes deben superar estos controles
antes de considerar validada la imagen final.

## Cambio de acceso en Portainer

Al actualizar el archivo Compose, una instalación que dependía del valor
implícito `0.0.0.0` dejará de aceptar conexiones desde otros equipos. Para una
red de confianza, definir `CUADERNOPRO_BIND_ADDRESS` con la IP privada del
servidor en las variables del stack. El valor `0.0.0.0` publica en todas las
interfaces y requiere limitar el acceso mediante firewall.

Para Internet, usar HTTPS y autenticación en un proxy o acceder mediante VPN.
No hay autenticación propia de usuarios en CuadernoPro. Ver
[la guía de acceso exterior](../GUIA_ACCESO_EXTERNO.md).
