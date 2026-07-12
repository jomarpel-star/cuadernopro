# CuadernoPro v8.4.7

Release pública recomendada para Windows de CuadernoPro.

CuadernoPro es el cuaderno agrícola libre para que ningún agricultor se quede
sin herramienta. Esta versión permite instalar y usar la aplicación en Windows
sin Docker, WSL, Python ni terminal.

Esta versión mejora el alta de parcelas: la provincia y el municipio se toman
de la explotación y se convierten en sus códigos SIGPAC mediante el catálogo
local. Si la ubicación no está configurada o no coincide, CuadernoPro solicita
una selección manual en lugar de presuponer Murcia/Jumilla.

## Incluye

- Instalador Windows.
- Funcionamiento sin Docker ni WSL.
- Base SQLite local y datos en `Documentos\CuadernoPro`.
- PDF oficial del cuaderno.
- Backup completo con documentos adjuntos.
- Importación de catálogos SIEX y revisión SIEX.
- Mapas/SIGPAC.
- Cosecha, tratamientos, fertilización y prácticas multicultivo.

## Descargas

- `CuadernoPro-8.4.7-Setup.exe`
- `SHA256SUMS.txt`

## Avisos importantes

- No cambia el modelo de datos de usuario.
- No requiere migración manual.
- Los datos existentes se conservan.
- Revisa siempre los datos antes de presentarlos en trámites, inspecciones o
  comunicaciones oficiales.
- Conserva tus propias copias de seguridad.
- CuadernoPro no es una aplicación oficial de la administración.

## Licencia

CuadernoPro se distribuye como software libre bajo GNU General Public License
versión 3 o posterior (`GPL-3.0-or-later`).
