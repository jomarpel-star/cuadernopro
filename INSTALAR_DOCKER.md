# Instalación con Docker

Esta guía explica como levantar CuadernoPro con Docker. Los datos de la
aplicación quedan guardados en la carpeta `runtime/` del proyecto.

Para CuadernoPro v8.0.0, la documentación principal de release está en
`docs/v8/README_V8.md`.

## Requisitos

- Docker
- Docker Compose

## Estructura principal

El despliegue usa estos elementos:

- `docker-compose.yml`: define el servicio `cuadernopro`.
- `runtime/`: carpeta persistente de datos.
- `runtime/cuadernopro.db`: baseaplicaciónSQLite de la aplicación.
- `runtime/backups`: copias de seguridad.
- `runtime/exports`: exportaciones gaplicaciónor la aplicación.
- `runtime/documentos`: documentos y ficheros asociados.

Si `runtime/` o alguna de sus subcarpetas no existe, la aplicación puede crear
las carpetas necesarias al arrancar. Aun así, antes de una instalación de
produccion conviene revisar que la ruta existe y que el usuario que ejecuta
Docker puede escribir en ella.

## Arranque

La imagen oficial se publica en Docker Hub para Linux `amd64` y `arm64`:

```text
jomarpel74/cuadernopro
```

Desde la carpeta del proyecto, descargar y arrancar la release estable:

```bash
docker compose pull cuadernopro
docker compose up -d --no-build
```

Para fijar una version concreta y evitar actualizaciones accidentales, crear
un archivo `.env` a partir de `.env.example` y configurar, por ejemplo:

```dotenv
CUADERNOPRO_IMAGE_TAG=8.4.9
```

Si se quiere construir la imagen localmente desde el codigo fuente, ejecutar:

```bash
docker compose up -d --build
```

Comprobar el estado del contenedor:

```bash
docker compose ps
```

Ver logs de la aplicación:

```bash
docker compose logs -f cuadernopro
```

Detener el servicio:

```bash
docker compose down
```

## Acceso exterior opcional

La instalación normal no activa proxy ni HTTPS. Si se necesita publicar
CuadernoPro hacia Internet, revisa primero:

[GUIA_ACCESO_EXTERNO.md](GUIA_ACCESO_EXTERNO.md)

Esa opción usa Caddy con el perfil `proxy`:

```bash
docker compose pull cuadernopro
docker compose --profile proxy up -d --no-build
```

No abras directamente a Internet el puerto de Streamlit (`8501` o el puerto
configurado en `CUADERNOPRO_PORT`). Para acceso exterior, la entrada pública
debe ser el proxy. En ese caso, configura `CUADERNOPRO_BIND_ADDRESS=127.0.0.1`
en `.env` o usa `./start_proxy.sh`, que lo comprueba antes de arrancar Caddy.

## Varias instalaciones en el mismo servidor

CuadernoPro no usa un `container_name` fijo en `docker-compose.yml`. Docker
Compose generara el nombre real del contenedor a partir del nombre del proyecto,
lo que permite tener varias instalaciones en el mismo servidor.

Para una instalación normal, puede usarse la configuración por defecto:

```bash
docker compose pull cuadernopro
docker compose up -d --no-build
```

Para una segunda instalación en el mismo servidor:

1. Copiar el proyecto en otra carpeta.
2. Crear o editar el archivo `.env` de esa copia.
3. Usar otro nombre de proyecto y otro puerto.

Ejemplo de `.env` para una segunda instalación:

```dotenv
COMPOSE_PROJECT_NAME=cuadernopro_demo
CUADERNOPRO_PORT=8504
```

No debe usarse un `container_name` fijo, porque impediria arrancar dos
instalaciones de CuadernoPro en el mismo servidor.

## URL por defecto

Con la configuración actual, CuadernoPro queda disponible en:

```text
http://localhost:8503
```

Por seguridad, el puerto de Streamlit queda ligado por defecto a `127.0.0.1`.
Si necesitas acceso desde otros equipos de la red local, configura en `.env`:

```dotenv
CUADERNOPRO_BIND_ADDRESS=0.0.0.0
```

Usa esa opción solo si entiendes el riesgo y no expones ese puerto directamente
a Internet. Para acceso exterior, usa el proxy descrito en
[GUIA_ACCESO_EXTERNO.md](GUIA_ACCESO_EXTERNO.md).

## Persistencia de datos

El contenedor monta la carpeta local `runtime/` dentaplicaciónplicacion. Por
eso, la base de datos, backups, exportaciones y documentos deben conservarse
fuera del contenedor.

No borres `runtime/` si quieres conservar los datos.

En una instalación nueva, CuadernoPro crea una base limpia actual. Las bases v7
existentes se abren con ampliaciones idempotentes, sin migraciones
destructivas.

## Backup manual antes de actualizar

Antes de actualizar el proyecto o reconstruir el contenedor, haz una copia
manual de `runtime/`.

Ejemplo:

```bash
cp -a runtime runtime.backup.$(date +%Y%m%d_%H%M%S)
```

Después de crear la copia, comprueba que contiene al menos:

- `runtime/cuadernopro.db`
- `runtime/backups`
- `runtime/exports`
- `runtime/documentos`

Cuando el backup este verificado, ya se puede actualizar el código y volver a
levantar el servicio con:

```bash
docker compose pull cuadernopro
docker compose up -d --no-build
```
