# CuadernoPro - Release notes

## v8.4.10 - Personalización de colores de cultivos

- Mantiene los colores existentes de almendro (verde), olivar (azul) y
  tierras arables (blanco).
- Añade en Mapas un selector visual para personalizar el color de los demás
  cultivos de la campaña activa.
- Propone una paleta inicial diferenciada para que el mapa sea legible antes
  de realizar ajustes manuales.
- Guarda las preferencias de color en la base SQLite local y las reutiliza en
  las campañas posteriores.
- Actualiza la leyenda del mapa con los cultivos y colores configurados.
- En parcelas con varios cultivos, conserva la prioridad de los colores fijos.
- Añade una tabla auxiliar idempotente para preferencias visuales; no modifica
  los registros agronómicos existentes.
- No requiere migración manual y conserva los datos del usuario.

## v8.4.9 - Radar y avisos legales completos

- Mantiene la capa opcional de radar de lluvia animado sobre el mapa general.
- Declara `branca` como dependencia directa.
- Regenera el inventario de dependencias y licencias desde el entorno exacto
  usado para construir el instalador.
- Documenta las atribuciones y condiciones de SIGPAC, PNOA/IGN,
  OpenStreetMap y RainViewer.
- Incluye los avisos de terceros y las atribuciones externas dentro del paquete
  Windows.
- No cambia el modelo de datos de usuario.
- No requiere migración manual.
- Los datos existentes se conservan.

## v8.4.8 - Radar de lluvia animado en mapas

- Añade una capa opcional de radar de lluvia sobre el mapa general de la
  explotación.
- Permite reproducir, pausar y recorrer las observaciones de las últimas dos
  horas.
- Muestra la fecha y hora de cada imagen de radar.
- Mantiene visibles las parcelas y los cultivos sobre la capa meteorológica.
- La capa está desactivada al abrir el mapa y se degrada de forma segura cuando
  no hay conexión o el servicio externo no está disponible.
- Declara `branca` como dependencia directa y actualiza el inventario completo
  de licencias del entorno usado para construir el instalador.
- Documenta las atribuciones y condiciones de SIGPAC, PNOA/IGN,
  OpenStreetMap y RainViewer.
- No cambia el modelo de datos de usuario.
- No requiere migración manual.
- Los datos existentes se conservan.

## v8.4.7 - Ubicación SIGPAC desde la explotación

- La pantalla `Nueva parcela` propone la provincia y el municipio configurados
  en la explotación.
- Los nombres se resuelven contra el catálogo SIGPAC local para obtener sus
  códigos oficiales, tolerando mayúsculas, tildes y códigos escritos junto al
  nombre.
- Si la ubicación está vacía o no coincide con el catálogo, no se presupone
  Murcia/Jumilla: se solicita una selección manual.
- No cambia el modelo de datos de usuario.
- No requiere migración manual.
- Los datos existentes se conservan.

## v8.4.6 - Release pública recomendada

- Corrige duplicados de parcelas en el cuaderno oficial.
- La sección de identificación de parcelas lista cada recinto una sola vez.
- Corrige el campo Sistema en la tabla de parcelas del cuaderno oficial.
- Mejora la activación y desactivación de campañas activas con confirmación
  explícita.
- Evita usar una campaña como activa de forma silenciosa cuando no hay ninguna
  activada.
- Mejora los mapas:
  - tooltip más compacto;
  - cultivos filtrados por campaña activa;
  - número de árboles formateado correctamente.
- El instalador recomendado pasa a ser `CuadernoPro-8.4.6-Setup.exe`.
- No cambia el modelo de datos de usuario.
- No requiere migración manual.
- Los datos existentes se conservan.

## v8.4.2 - Web pública estática para Plesk

- Crea `web_publica/` con una web estática inicial lista para subir a Plesk.
- Añade páginas para inicio, descarga, primeros pasos, software libre, soporte
  y privacidad.
- Añade CSS propio, ligero y responsive, sin dependencias externas.
- Reutiliza el logo y favicon oficiales de `assets/branding/`.
- Añade `.htaccess` seguro con caché básica de assets y reglas opcionales
  comentadas.
- Añade `web_publica/README_DEPLOY_PLESK.md` con instrucciones de despliegue.
- No cambia funcionalidad de la aplicación.
- No cambia el modelo de datos.
- No toca Docker ni instalador Windows.
- No cambia `core/version.py`; la versión visible de la app sigue siendo
  `8.4.0`.

## v8.4.1 - Revisión lingüística de documentación pública

- Revisa tildes, ortografía y redacción de README, notas de versión, textos web,
  publicación, distribución, documentación legal y documentación v8 visible.
- Crea `docs/publicacion/GUIA_ESTILO_TEXTOS.md` con criterios de tono,
  terminología y revisión antes de publicar.
- Añade `scripts/auditar_tildes_documentacion.py` para detectar palabras
  frecuentes sin tilde en documentación pública.
- Actualiza checklists para exigir revisión lingüística y ejecución del auditor
  antes de publicar.
- No cambia la aplicación.
- No cambia el modelo de datos.
- No toca Docker ni instalador Windows.
- No cambia `core/version.py`; la versión visible de la app sigue siendo
  `8.4.0`.

## v8.4.0 - Preparación de publicación inicial

- Prepara el repositorio y los textos públicos para la primera publicación de
  CuadernoPro.
- Revisa `README.md` para explicar que CuadernoPro es software libre, gratuito
  para agricultores, local, sin cuotas, sin activación y con datos controlados
  por el usuario.
- Crea textos base para la futura web pública en `docs/web/`.
- Crea texto recomendado para la GitHub Release v8.3.3.
- Crea checklist pública de revisión previa, capturas pendientes y textos de
  difusión.
- Actualiza la versión visible a `8.4.0`.
- No cambia funcionalidad.
- No cambia el modelo de datos.
- No toca Docker ni instalador Windows.

## v8.3.3 - PDF de portada y backup documental completo

- La portada del PDF del cuaderno usa `campanas.fecha_inicio` como fecha de
  apertura, con formato `DD/MM/AAAA`.
- El registro nacional de explotación sale de
  `explotacion.identificador_oficial`, con fallback a campos legacy si existen.
- El registro autonómico sale de `explotacion.registro_autonomico`; no se
  rellena copiando el identificador nacional.
- El backup ZIP creado desde la app incluye la base SQLite y documentos bajo
  `documentos/`, incluyendo facturas y recetas adjuntas.
- La restauración acepta backups antiguos de solo base y backups nuevos con
  documentos, sin borrar documentos actuales.
- No cambia el modelo de datos.
- No toca Docker ni instaladores.

## v8.3.2 - Cierre automatico del portable Windows

- El portable/instalador Windows abre CuadernoPro en Microsoft Edge modo app
  cuando Edge está disponible.
- Al cerrar la ventana de la app, el launcher detecta el cierre del proceso de
  navegador y termina `CuadernoPro.exe`.
- Añade lock de instancia en la raíz de datos para reutilizar una instancia
  viva y evitar servidores Streamlit duplicados.
- Mantiene fallback a navegador por defecto si Edge no existe, con aviso en
  logs porque ese modo no permite detectar el cierre de la ventana.
- No cambia el modelo de datos.
- No toca Docker.

## v8.3.1 - Pulido del instalador Windows

- Prepara `assets/branding/` para los iconos oficiales de CuadernoPro.
- PyInstaller usa `assets/branding/cuadernopro.ico` como icono del ejecutable
  cuando existe.
- Inno Setup usa el icono oficial para el instalador cuando existe.
- Los accesos directos de escritorio y menú inicio usan el icono de
  `CuadernoPro.exe`.
- Streamlit usa `assets/branding/cuadernopro.png` como favicon cuando existe y
  mantiene `🚜` como fallback.
- No cambia el modelo de datos.
- No toca Docker.

## v8.3.0 - Instalador Windows con Inno Setup

- Genera instalador Windows con Inno Setup.
- Usa el portable PyInstaller validado.
- Instala CuadernoPro por usuario, sin pedir permisos de administrador.
- Crea accesos directos en escritorio y menú inicio.
- No requiere Docker, WSL, Python ni terminal para el usuario final.
- No cambia el modelo de datos.
- No borra datos del usuario al desinstalar.

## v8.2.2 - Portable Windows y validación PyInstaller

- Corrige el arranque del portable Windows.
- Ajusta la validación del build Windows para permitir artefactos internos
  legitimos de PyInstaller y `pyproj`.
- Mantiene el bloqueo de bases, backups, runtime, exports, documentos subidos,
  excels y binarios generados dentro del paquete distribuible.
- No cambia el modelo de datos.
- No genera todavía instalador Inno Setup final.

## v8.2.0 - Build portable Windows con PyInstaller

- Prepara el build portable Windows con PyInstaller.
- Añade spec de PyInstaller para empaquetar `app.py`, `core/`, `modules/`,
  `services/`, `data/`, documentación legal y avisos.
- Mejora el launcher Windows para uso congelado con PyInstaller, argumentos de
  diagnóstico y pruebas con carpeta de datos temporal.
- Actualiza `build_windows.ps1` para generar `dist_windows\CuadernoPro`.
- Añade prueba PowerShell inicial del portable.
- No cambia el modelo de datos.
- No genera todavía instalador Inno Setup final.

## v8.1.0 - Distribución libre y Windows sin Docker

- Formaliza CuadernoPro como software libre con licencia GNU GPL v3 o
  posterior.
- Añade documentación legal y de distribución bajo CC BY-SA 4.0.
- Se aclara que el programa completo será gratuito para agricultores.
- Se documenta que no habrá demo capada, activación, límites de parcelas ni
  licencias anuales obligatorias.
- Se documenta el modelo de servicios opcionales: instalación, puesta en
  marcha, formación, soporte prioritario, importación de datos y adaptaciones.
- Se crea política de marca CuadernoPro controlada para evitar confusion con
  versiones modificadas no oficiales.
- Se prepara `packaging/windows/` para un futuro empaquetado Windows sin Docker,
  sin generar todavía `.exe` ni instalador.
- Actualiza la versión visible a la versión 8.1.0.

No cambia el modelo de datos.

## v8.0.3 - Asignacion de campaña contable por fecha

- Los movimientos nuevos de Contabilidad se asignan a la campaña que corresponde
  a la fecha del movimiento.
- Permite introducir movimientos antiguos sin cambiar la campaña activa global.
- No cambia el modelo de datos.

## v8.0.2 - Versión visible y control de release

- Corrige la versión visible en la interfaz.
- Añade comprobacion de versionado a `scripts/probar_release_v8.py`.
- No cambia el modelo de datos.

## v8.0.1 - Actuaciones multicultivo

- Añade multicultivo/multiparcela en tratamientos, fertilización y prácticas
  culturales.
- Mantiene compatibilidad con registros antiguos de cultivo unico.

## v8.0.0 - Primera versión limpia estable

La versión 8.0.0 consolida la primera versión limpia estable del proyecto.
Incluye el esquema limpio validado durante v7, la instalación Docker/WSL, la
persistencia SQLite, los editores principales, las salidas PDF/Excel y la
revisión asistida SIEX/CUE.

Documentación principal:

- [docs/v8/README_V8.md](docs/v8/README_V8.md)
- [docs/v8/CHANGELOG_V8.md](docs/v8/CHANGELOG_V8.md)
- [docs/v8/CHECKLIST_RELEASE_V8.md](docs/v8/CHECKLIST_RELEASE_V8.md)

## Incluye

- Explotación, campañas, parcelas SIGPAC y cultivos.
- Cálculo de árboles por marco de plantación.
- Cosecha multicultivo y multiparcela.
- Maquinaria, equipos y productos fitosanitarios.
- Tratamientos, fertilización y prácticas culturales.
- Contabilidad básica.
- Informes, PDF oficial y Excel asistido SIEX/CUE.
- Revisión SIEX/CUE.
- Mapas/SIGPAC.
- Backup y restauración.
- Docker Compose con datos persistentes en `runtime/`.

## Avisos

- CuadernoPro no es una aplicación oficial de la administración.
- El Excel SIEX/CUE es asistido y no sustituye los canales oficiales.
- No hay conexion directa oficial con SIEX/CUE.
- La carpeta `runtime/` contiene los datos reales y no debe borrarse al
  actualizar.
- El ZIP de código no debe incluir bases, backups, runtime, exports, documentos
  subidos ni temporales.
