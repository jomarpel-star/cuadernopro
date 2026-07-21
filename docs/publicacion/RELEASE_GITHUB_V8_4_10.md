# CuadernoPro v8.4.10

Release pública recomendada para Windows de CuadernoPro.

CuadernoPro es el cuaderno agrícola libre para que ningún agricultor se quede
sin herramienta. Esta versión permite instalar y usar la aplicación en
Windows sin Docker, WSL, Python ni terminal.

La principal novedad es la personalización de colores en el mapa general. Los
colores de almendro, olivar y tierras arables se mantienen como hasta ahora,
mientras que el usuario puede elegir visualmente los colores de los demás
cultivos. Las preferencias quedan guardadas en la base local para reutilizarlas
en campañas posteriores.

## Novedades

- Almendro en verde, olivar en azul y tierras arables en blanco.
- Selector visual para personalizar el resto de cultivos.
- Paleta inicial diferenciada y leyenda dinámica en el mapa.
- Preferencias de color persistentes entre campañas.
- Prioridad de los colores fijos en parcelas con varios cultivos.
- Pruebas ampliadas de persistencia y compatibilidad.

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

- `CuadernoPro-8.4.10-Setup.exe`
- `SHA256SUMS.txt`

## Compatibilidad y datos

- La actualización crea automáticamente una tabla auxiliar para guardar los
  colores del mapa.
- No modifica los registros agronómicos existentes.
- No requiere migración manual.
- Los datos existentes se conservan.
- Se recomienda crear una copia de seguridad antes de actualizar.

## Avisos importantes

- La capa de radar requiere conexión a Internet y muestra observaciones, no
  una predicción meteorológica.
- Revisa siempre los datos antes de presentarlos en trámites, inspecciones o
  comunicaciones oficiales.
- Conserva tus propias copias de seguridad.
- CuadernoPro no es una aplicación oficial de la administración.

## Licencia

CuadernoPro se distribuye como software libre bajo GNU General Public License
versión 3 o posterior (`GPL-3.0-or-later`).
