# CuadernoPro v8.4.0

CuadernoPro es una aplicación web para gestionar el cuaderno agrícola de una
explotación: datos de explotación, campañas, parcelas, cultivos, tratamientos,
fertilización, prácticas culturales, cosecha, contabilidad, informes, mapas,
documentos PDF y copias de seguridad.

CuadernoPro no es una aplicación oficial de la administración. Es una
herramienta de apoyo. El usuario debe revisar los datos antes de usarlos en
trámites, inspecciones o comunicaciones oficiales.

## Objetivo de v8

v8.4.0 prepara la publicación inicial de CuadernoPro. Revisa el README
principal, crea textos base para la futura web pública, añade texto recomendado
para la GitHub Release v8.3.3, incorpora checklist de publicación y actualiza
la versión visible para reflejar esta fase. No cambia funcionalidad, modelo de
datos, Docker ni instalador Windows.

v8.0.0 es la primera versión limpia estable de CuadernoPro. Consolida el modelo
de datos limpio validado durante v7, mantiene compatibilidad con bases v7
existentes y evita incluir datos reales, bases, backups, runtime o documentos en
el código distribuible.

v8.0.1 añade multicultivo/multiparcela a tratamientos, fertilización y
prácticas culturales, siguiendo el mismo diseño ya aplicado en cosecha.

v8.0.2 corrige la versión visible de la interfaz y añade control de versión al
proceso de release. No cambia el modelo de datos.

v8.0.3 corrige la asignación de campaña en Contabilidad: los movimientos se
guardan según la fecha del movimiento, no según la campaña activa global.
Permite introducir movimientos antiguos sin cambiar la campaña activa.

v8.1.0 formaliza la distribución libre de CuadernoPro: código GPLv3 o
posterior, documentación CC BY-SA 4.0, marca CuadernoPro controlada, programa
completo gratuito para agricultores y empaquetado Windows sin Docker en
preparación. No genera todavía el instalador Windows final y no cambia el
modelo de datos.

v8.2.0 prepara el build portable Windows con PyInstaller. El objetivo es generar
`dist_windows/CuadernoPro/CuadernoPro.exe` cuando el proceso se ejecute en
Windows. No cambia el modelo de datos y no genera todavía instalador Inno Setup
final.

v8.3.0 genera el instalador Windows con Inno Setup usando el portable
PyInstaller validado. No cambia el modelo de datos y el desinstalador no borra
los datos del usuario en `Documents/CuadernoPro`.

v8.3.3 corrige la portada del PDF oficial para usar `fecha_inicio` de la
campaña como fecha de apertura, `identificador_oficial` como registro nacional
y `registro_autonomico` como registro autonómico. También amplía el backup de
usuario para incluir documentos adjuntos bajo `documentos/`, como facturas y
recetas.

## Licencia y distribución libre

CuadernoPro se distribuye como software libre bajo GNU GPL v3 o posterior
(`GPL-3.0-or-later`). La documentación se licencia bajo Creative Commons
Attribution-ShareAlike 4.0 International.

El programa completo será gratuito para agricultores:

- sin demo capada;
- sin activación;
- sin límites artificiales de parcelas;
- sin licencias anuales obligatorias;
- con datos locales del usuario.

El proyecto puede ofrecer servicios opcionales de pago: instalación, puesta en
marcha, formación, soporte prioritario, importación de datos y adaptaciones
personalizadas. También puede aceptar donativos o aportaciones voluntarias.

Documentos relacionados:

- `LICENSE`
- `DISCLAIMER.md`
- `TRADEMARKS.md`
- `docs/legal/LICENCIA_DOCUMENTACION.md`
- `docs/distribucion/DISTRIBUCION_CUADERNOPRO.md`

## Requisitos

Instalación recomendada:

- Docker
- Docker Compose
- Terminal en Linux, WSL, servidor, NAS o Raspberry compatible

Instalación de desarrollo:

- Python 3.13
- Entorno virtual
- Dependencias de `requirements.txt`

## Build portable e instalador Windows sin Docker

La línea v8.3.0 prepara el build portable Windows y el instalador Inno Setup
sin Docker, sin WSL y sin terminal para el usuario final. En esta fase se
mantiene `packaging/windows/` con launcher, spec de PyInstaller, script de
build portable, script de instalador, prueba portable, prueba de instalador y
plantilla de Inno Setup.

El instalador Windows guarda el programa en el perfil del usuario y deja los
datos reales fuera de la carpeta instalada. La aplicación guarda los datos en
`Documents/CuadernoPro`, arranca Streamlit en `127.0.0.1` y abre la aplicación
en el navegador local. La build real del `.exe` y del instalador debe ejecutarse
y probarse en Windows.

## Instalación recomendada con Docker

La imagen oficial `jomarpel74/cuadernopro` está disponible para Linux `amd64`
y `arm64`. Desde la carpeta descomprimida o clonada:

```bash
docker compose pull cuadernopro
docker compose up -d --no-build
docker compose ps
```

Para fijar una release concreta, configurar `CUADERNOPRO_IMAGE_TAG=8.4.10` en
el archivo `.env`. Para construir desde el código fuente en lugar de descargar
la imagen oficial, usar `docker compose up -d --build`.

Con la configuración actual, la aplicación queda disponible en:

```text
http://localhost:8503
```

Si se necesita acceso desde otro equipo de la red local, configurar en `.env`:

```dotenv
CUADERNOPRO_BIND_ADDRESS=0.0.0.0
```

No exponer directamente Streamlit a Internet. Para acceso exterior revisar la
guía de proxy con Caddy.

## Instalación limpia en WSL

1. Instalar Docker Desktop con integración WSL o Docker dentro de WSL.
2. Descomprimir el ZIP limpio de CuadernoPro.
3. Entrar en la carpeta del proyecto.
4. Ejecutar:

```bash
docker compose pull cuadernopro
docker compose up -d --no-build
```

5. Abrir `http://localhost:8503`.
6. Completar el asistente inicial.

## Primer arranque

En una instalación nueva, CuadernoPro crea automáticamente una base SQLite limpia
en:

```text
runtime/cuadernopro.db
```

El primer uso debe completar:

- datos de explotación;
- campaña inicial;
- parcelas;
- cultivos;
- terceros y personas necesarias.

## Datos persistentes

La carpeta importante es:

```text
runtime/
```

Contiene:

- `runtime/cuadernopro.db`: base principal;
- `runtime/backups/`: copias de seguridad;
- `runtime/exports/`: PDF, Excel y salidas generadas;
- `runtime/documentos/`: facturas, recetas y documentos asociados.

No borrar `runtime/` si se quieren conservar los datos.

### Portainer y Watchtower

Para Portainer debe desplegarse `docker-compose.portainer.yml`. Este archivo
monta el volumen nombrado `cuadernopro_data` en `/app/runtime`; así Watchtower
puede reemplazar la imagen sin reemplazar la base SQLite ni los documentos.

La inspección del contenedor debe mostrar un montaje con destino
`/app/runtime`. Si muestra `Mounts: []`, los datos siguen dentro de la capa
temporal del contenedor y se perderán al recrearlo. La guía completa está en
[INSTALAR_DOCKER.md](../../INSTALAR_DOCKER.md).

## Copias de seguridad

Antes de actualizar:

```bash
cp -a runtime runtime.backup.$(date +%Y%m%d_%H%M%S)
```

También se pueden crear backups desde la pantalla `Backup / Restauracion`.
El ZIP creado desde la app incluye la base SQLite y los documentos adjuntos
permitidos dentro de `runtime/documentos/`, conservando subcarpetas como
`facturas/` y `recetas/`. Esos documentos de usuario no forman parte de los ZIP
de release ni deben versionarse en Git.

## Actualización de código

1. Hacer backup de `runtime/`.
2. Sustituir el código por la nueva versión.
3. Mantener la carpeta `runtime/`.
4. Descargar la imagen actualizada y recrear el contenedor:

```bash
docker compose pull cuadernopro
docker compose up -d --no-build
```

Las bases v7 existentes reciben ampliaciones limpias idempotentes. Una
instalación nueva nace directamente con el esquema limpio actual de CuadernoPro
v8.0.

## Qué incluye v8.0

- Base SQLite limpia validada.
- Explotación y campañas.
- Parcelas SIGPAC.
- Cultivos asociados a parcelas.
- Cálculo de árboles por marco de plantación.
- Cosecha multicultivo y multiparcela.
- Tratamientos multicultivo y multiparcela.
- Fertilización multicultivo y multiparcela.
- Prácticas culturales multicultivo y multiparcela.
- Clientes, proveedores y personas.
- Maquinaria y equipos de aplicación.
- Productos fitosanitarios.
- Tratamientos fitosanitarios.
- Fertilización.
- Prácticas culturales.
- Cosecha y ventas.
- Contabilidad básica con asignacion de campaña por fecha del movimiento.
- Informes.
- PDF oficial de cuaderno.
- Excel asistido SIEX/CUE.
- Revisión SIEX/CUE.
- Importación de catálogos SIEX desde ZIP oficial.
- Mapas/SIGPAC.
- Backup y restauración.
- Docker Compose.

## Exportación asistida SIEX/CUE

CuadernoPro genera un Excel asistido para revisar y preparar datos. Este Excel no
es un formato oficial SIEX/CUE y no envia información a ningún sistema externo.

La carga oficial, si procede, debe realizarse por los canales oficiales
correspondientes.

## Importar catálogos SIEX

CuadernoPro puede importar catálogos SIEX/CUE desde un ZIP oficial, por ejemplo
el ZIP de catálogos publicado con la Circular PAC correspondiente.

CuadernoPro no incluye necesariamente ese ZIP oficial. El usuario debe
descargarlo de la fuente administrativa vigente y conservarlo fuera de Git y
fuera del ZIP de release.

Desde la aplicación:

1. Abrir `Catalogos SIEX`.
2. Subir el ZIP oficial en `Importar catalogos`.
3. Pulsar `Importar catalogos SIEX`.
4. Revisar el resumen y el diagnóstico.

Por consola, indicando siempre una base destino:

```bash
./venv/bin/python scripts/importar_catalogos_siex.py \
  /ruta/al/zip_catalogos_siex.zip \
  --db runtime/cuadernopro.db
```

También puede usarse `CUADERNOPRO_DB_PATH` como ruta destino. El script no
importa sobre `cuadernopro.db` por defecto si no se indica una base.

La importación es idempotente: se puede repetir cuando haya catálogos
actualizados. Para cada catálogo se reemplazan sus items anteriores por los del
ZIP importado, sin duplicar elementos y sin guardar el ZIP original en la base.

El ZIP oficial de catálogos no debe versionarse ni incluirse en el ZIP de
release, builds portables o instaladores.

## Estructura de datos limpia

v8.0 usa como base el esquema limpio consolidado durante v7:

- datos estructurados por ID;
- relaciones N:M mediante tablas puente;
- cosecha multicultivo mediante `cosecha_cultivos`;
- actuaciones multicultivo mediante `tratamiento_cultivos`,
  `fertilizacion_cultivos` y `practicas_culturales_cultivos`;
- parcelas de actuaciones mediante tablas puente;
- cultivos con `marco_plantacion` y `numero_arboles`;
- ampliaciones idempotentes para bases v7 existentes.

Los nombres internos de algunos scripts siguen usando `v7` para evitar cambios
de riesgo antes de v8.0. Esto no afecta al uso de CuadernoPro v8.0.

## Limitaciones conocidas

- No hay conexion directa oficial con SIEX/CUE.
- La validez administrativa de los datos debe revisarla el usuario o su asesor.
- Los catálogos y codigos oficiales pueden requerir revisión y actualización
  cuando cambien las fuentes oficiales.
- La instalación pública en Internet requiere proxy, HTTPS y control de acceso.
- Los scripts internos conservan nombres v7 por compatibilidad histórica.
- Los movimientos contables existentes no se migran automáticamente; se puede
  revisar la coherencia con
  `scripts/diagnosticar_contabilidad_campanas_v8.py`.

## Versión

- Producto: CuadernoPro
- Versión: 8.4.0
- Estado: estable
