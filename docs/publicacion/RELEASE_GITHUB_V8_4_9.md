# CuadernoPro v8.4.9

Release pública recomendada para Windows de CuadernoPro.

CuadernoPro es el cuaderno agrícola libre para que ningún agricultor se quede
sin herramienta. Esta versión permite instalar y usar la aplicación en Windows
sin Docker, WSL, Python ni terminal.

Esta versión incorpora una capa opcional de radar de lluvia en el mapa general
de la explotación. Permite reproducir, pausar y recorrer las observaciones de
las últimas dos horas manteniendo visibles las parcelas y los cultivos.

La release incluye también el inventario actualizado de dependencias y
licencias, las atribuciones de las fuentes de datos externas y esos avisos
dentro del paquete Windows.

## Incluye

- Instalador Windows.
- Funcionamiento sin Docker ni WSL.
- Base SQLite local y datos en `Documentos\CuadernoPro`.
- PDF oficial del cuaderno.
- Backup completo con documentos adjuntos.
- Importación de catálogos SIEX y revisión SIEX.
- Mapas/SIGPAC con radar de lluvia animado opcional.
- Inventario de licencias y atribuciones de datos externos.
- Cosecha, tratamientos, fertilización y prácticas multicultivo.

## Descargas

- `CuadernoPro-8.4.9-Setup.exe`
- `SHA256SUMS.txt`

## Avisos importantes

- La capa de radar requiere conexión a Internet y muestra observaciones, no una
  predicción meteorológica.
- Los datos de radar se consultan en RainViewer y conservan su atribución y sus
  condiciones de uso propias; no se incluyen datos de radar en CuadernoPro.
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
