# CuadernoPro

CuadernoPro es el cuaderno agrícola libre para que ningún agricultor se quede
sin herramienta.

Es una aplicación para gestionar el cuaderno de explotación desde el ordenador:
explotación, campañas, parcelas, cultivos, tratamientos, fertilización,
prácticas culturales, cosecha, contabilidad, mapas, informes, PDF del cuaderno,
revisión SIEX, exportación Excel asistida y copias de seguridad.

CuadernoPro es software libre y gratuito para agricultores. No tiene cuotas,
activación, demo capada, límites artificiales de parcelas ni licencias anuales
obligatorias. Funciona en local, guarda los datos en una base SQLite del usuario
y no sube información automáticamente a ningún servidor.

El código fuente de CuadernoPro está publicado bajo GNU GPL v3 o posterior
(`GPL-3.0-or-later`). La documentación se distribuye bajo Creative Commons
Attribution-ShareAlike 4.0 International.

## Características principales

- Aplicación local para Windows mediante instalador, sin Docker ni WSL para el
  usuario final.
- Base SQLite local con datos controlados por el usuario.
- Datos de explotación, campañas, parcelas SIGPAC y cultivos.
- Cálculo de árboles por marco de plantación.
- Tratamientos, fertilización y prácticas culturales con soporte multicultivo y
  multiparcela.
- Cosecha multicultivo y multiparcela.
- Contabilidad agrícola básica.
- Mapas y apoyo SIGPAC.
- PDF oficial del cuaderno.
- Revisión SIEX/CUE y exportación Excel asistida para revisar información.
- Importación local de catálogos SIEX desde ZIP oficial.
- Copia de seguridad completa con base SQLite y documentos adjuntos.

## Capturas pendientes

Las capturas recomendadas para la publicación inicial están recogidas en
[docs/publicacion/CAPTURAS_PENDIENTES.md](docs/publicacion/CAPTURAS_PENDIENTES.md).

## Descarga

La versión recomendada para instalar en Windows es CuadernoPro v8.4.7. La
release pública debe ofrecer:

- `CuadernoPro-8.4.7-Setup.exe`
- `SHA256SUMS.txt`

El instalador Windows deja los datos del usuario en:

```text
Documentos\CuadernoPro
```

CuadernoPro v8.4.7 prepara la descarga pública recomendada. No requiere
migración manual y conserva los datos existentes.

## Instalación rápida

1. Descargar `CuadernoPro-8.4.7-Setup.exe` desde la release publicada.
2. Ejecutar el instalador.
3. Abrir CuadernoPro desde el acceso directo creado.
4. Completar los datos iniciales de la explotación.
5. Importar los catálogos SIEX si se van a usar las funciones de revisión.
6. Crear una primera copia de seguridad desde la pantalla `Backup /
   Restauración`.

Para detalles específicos de Windows, consulta
[packaging/windows/README_WINDOWS_BUILD.md](packaging/windows/README_WINDOWS_BUILD.md).

## Primeros pasos

Un flujo inicial recomendado:

1. Crear o revisar los datos de la explotación.
2. Crear la campaña agrícola.
3. Dar de alta parcelas y referencias SIGPAC.
4. Crear los cultivos asociados a parcelas.
5. Importar catálogos SIEX desde el ZIP oficial, si procede.
6. Registrar el primer tratamiento, fertilización, práctica cultural o cosecha.
7. Generar el PDF del cuaderno y revisar los avisos SIEX.
8. Crear una copia de seguridad completa y conservarla fuera del ordenador si
   es posible.

La guía básica para agricultores está en [USO_BASICO.md](USO_BASICO.md).

## Catálogos SIEX

CuadernoPro puede importar catálogos SIEX/CUE desde un ZIP oficial descargado
por el usuario. El ZIP oficial no se incluye en el código, en el instalador ni
en los archivos de release.

Desde la aplicación:

1. Abrir `Catalogos SIEX`.
2. Seleccionar el ZIP oficial.
3. Importar los catálogos.
4. Revisar el diagnóstico mostrado.

Por consola, en entornos de desarrollo:

```bash
./venv/bin/python scripts/importar_catalogos_siex.py \
  /ruta/al/zip_catalogos_siex.zip \
  --db runtime/cuadernopro.db
```

## Copias de seguridad

La pantalla `Backup / Restauracion` permite crear un ZIP con la base SQLite y
los documentos adjuntos guardados por la aplicación, como facturas o recetas.

El usuario debe conservar sus propias copias de seguridad. Es recomendable
guardarlas en otra unidad, memoria USB o almacenamiento externo, y hacer una
copia antes de actualizar CuadernoPro.

En instalaciones Docker o de desarrollo, la carpeta importante es:

```text
runtime/
```

En Windows instalado, la carpeta de datos está en:

```text
Documentos\CuadernoPro
```

## Licencia

- Código fuente: GNU General Public License versión 3 o posterior
  (`GPL-3.0-or-later`).
- Documentación: Creative Commons Attribution-ShareAlike 4.0 International.
- Marca CuadernoPro: uso controlado para evitar confusión con versiones no
  oficiales.

Documentos relacionados:

- [LICENSE](LICENSE)
- [docs/legal/LICENCIA_DOCUMENTACION.md](docs/legal/LICENCIA_DOCUMENTACION.md)
- [TRADEMARKS.md](TRADEMARKS.md)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

## Aviso de ausencia de garantía

CuadernoPro se ofrece sin garantía. No es una aplicación oficial de la
administración y no sustituye el criterio técnico, legal, fiscal o
administrativo que corresponda en cada caso.

El usuario debe revisar siempre los datos antes de presentarlos en trámites,
inspecciones, comunicaciones oficiales o declaraciones. Consulta
[DISCLAIMER.md](DISCLAIMER.md) y [AVISO_RESPONSABILIDAD.md](AVISO_RESPONSABILIDAD.md).

## Soporte y servicios opcionales

El programa completo es gratuito para agricultores. Se podrán ofrecer servicios
opcionales de pago como instalación, puesta en marcha, formación, soporte
prioritario, importación de datos y adaptaciones personalizadas.

El soporte comunitario, reporte de errores y contribuciones se canalizan desde
el repositorio. Consulta [CONTRIBUTING.md](CONTRIBUTING.md) y
[SECURITY.md](SECURITY.md).

## Contribuir

Las contribuciones son bienvenidas dentro del marco de la licencia GPLv3 o
posterior y respetando la marca CuadernoPro.

Antes de publicar cambios o preparar una release, revisa:

- [docs/publicacion/CHECKLIST_PUBLICACION.md](docs/publicacion/CHECKLIST_PUBLICACION.md)
- [docs/v8/CHECKLIST_RELEASE_V8.md](docs/v8/CHECKLIST_RELEASE_V8.md)
- [RELEASE_NOTES.md](RELEASE_NOTES.md)

## Documentación principal

- [docs/v8/README_V8.md](docs/v8/README_V8.md)
- [docs/v8/CHANGELOG_V8.md](docs/v8/CHANGELOG_V8.md)
- [docs/siex/README_SIEX.md](docs/siex/README_SIEX.md)
- [docs/web/index.md](docs/web/index.md)
- [docs/publicacion/RELEASE_GITHUB_V8_4_7.md](docs/publicacion/RELEASE_GITHUB_V8_4_7.md)
