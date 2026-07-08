# Changelog CuadernoPro v8

## v8.4.6 - Release publica recomendada

### Resumen

Se prepara la release publica recomendada para Windows con correcciones en el
cuaderno oficial, gestion mas segura de campanas activas y mapas mas claros. No
cambia el modelo de datos de usuario y no requiere migracion manual.

### Cambios

- Se corrigen duplicados de parcelas en el cuaderno oficial.
- La seccion de identificacion de parcelas lista cada recinto una sola vez.
- Se corrige el campo Sistema en la tabla de parcelas del cuaderno oficial.
- Se mejora la activacion y desactivacion de campanas activas con confirmacion
  explicita.
- Se evita usar una campana como activa de forma silenciosa cuando no hay
  ninguna activada.
- En mapas, el tooltip de parcelas es mas compacto.
- En mapas, los cultivos del tooltip se filtran por campana activa.
- En mapas, el numero de arboles se formatea correctamente.
- El instalador recomendado pasa a ser `CuadernoPro-8.4.6-Setup.exe`.

### Compatibilidad

- No cambia el modelo de datos de usuario.
- No requiere migracion manual.
- Los datos existentes se conservan.

## v8.4.2 - Web pública estática para Plesk

### Resumen

Se crea una web pública estática inicial para publicar CuadernoPro en Plesk,
orientada al dominio `cuadernopro.es`. No cambia la aplicación.

### Cambios

- Se crea `web_publica/` con páginas HTML estáticas para inicio, descarga,
  primeros pasos, software libre, soporte y privacidad.
- Se añade CSS propio, ligero y responsive, sin dependencias externas.
- Se reutilizan el logo y favicon de `assets/branding/`.
- Se añade `.htaccess` con `Options -Indexes`, `DirectoryIndex index.html`,
  caché básica para assets y reglas opcionales comentadas.
- Se añade `web_publica/README_DEPLOY_PLESK.md` con pasos de despliegue en
  Plesk y alternativa por SCP.

### Compatibilidad

- No cambia funcionalidad.
- No cambia el modelo de datos.
- No toca Docker.
- No toca instalador Windows.
- No genera binarios.
- No toca bases reales ni `cuadernopro.db`.
- No cambia `core/version.py`; la versión visible de la aplicación sigue siendo
  `8.4.0`.

## v8.4.1 - Revisión lingüística de documentación pública

### Resumen

Se revisan tildes, ortografía y redacción de los textos públicos de
CuadernoPro. No cambia la aplicación.

### Cambios

- Se revisan textos visibles en README, notas de versión, documentación web,
  publicación, distribución, documentación legal, documentación v8, SIEX y v7.
- Se crea `docs/publicacion/GUIA_ESTILO_TEXTOS.md` con criterios de tono,
  terminología y revisión antes de publicar.
- Se añade `scripts/auditar_tildes_documentacion.py` para detectar palabras
  frecuentes sin tilde en documentación pública.
- Se actualizan checklists para exigir revisión lingüística y ejecución del
  auditor antes de publicar.
- Se mantiene `core/version.py` sin cambios, porque la versión visible de la
  aplicación no debe cambiar solo por documentación.

### Compatibilidad

- No cambia funcionalidad.
- No cambia el modelo de datos.
- No toca Docker.
- No toca instalador Windows.
- No genera binarios.
- No toca bases reales ni `cuadernopro.db`.
- No cambia `core/version.py`; la versión visible de la aplicación sigue siendo
  `8.4.0`.

## v8.4.0 - Preparación de publicación inicial

### Resumen

Se prepara la primera publicación pública de CuadernoPro con documentación,
textos web, texto recomendado para GitHub Release, checklist pública y
versionado visible actualizado. No cambia funcionalidad.

### Cambios

- `core/version.py` pasa a `8.4.0`.
- `scripts/probar_release_v8.py` espera `8.4.0`.
- `README.md` se revisa para explicar desde el inicio que CuadernoPro es
  software libre, gratuito para agricultores, local, sin cuotas ni activación.
- Se crea `docs/publicacion/RELEASE_GITHUB_V8_4_6.md` con el texto recomendado
  para la release pública v8.4.6.
- Se crean textos base para `cuadernopro.es` en `docs/web/`.
- Se crean textos de difusión en `docs/publicacion/TEXTOS_DIFUSION.md`.
- Se crea checklist de capturas pendientes en
  `docs/publicacion/CAPTURAS_PENDIENTES.md`.
- Se crea checklist de publicación en
  `docs/publicacion/CHECKLIST_PUBLICACION.md`.

### Compatibilidad

- No cambia funcionalidad.
- No cambia el modelo de datos.
- No toca Docker.
- No toca instalador Windows salvo documentación.
- No genera binarios.
- No toca bases reales ni `cuadernopro.db`.

## v8.3.3 - PDF de portada y backup documental completo

### Resumen

Se corrige la portada del PDF oficial del cuaderno para usar los datos reales
de campaña y explotación, y se amplía la copia de seguridad de usuario para
incluir los documentos adjuntos guardados en la aplicación.

### Cambios

- `core/version.py` pasa a `8.3.3`.
- `scripts/probar_release_v8.py` espera `8.3.3`.
- La fecha de apertura de portada sale de `campanas.fecha_inicio` y se muestra
  en formato `DD/MM/AAAA`.
- El registro nacional de explotación se resuelve con prioridad
  `identificador_oficial`, `registro_explotacion`, `codigo_regepa`,
  `codigo_regea`.
- El registro autonómico se resuelve desde `registro_autonomico` y no cae al
  identificador nacional.
- El backup ZIP de usuario incluye la base y `documentos/...`, preservando
  subcarpetas como `facturas/` y `recetas/`.
- La restauración mantiene compatibilidad con backups antiguos y restaura
  documentos de backups nuevos de forma aditiva.
- Se añade `scripts/probar_pdf_portada_y_backup_docs_v8.py`.

### Compatibilidad

- No cambia el modelo de datos.
- No toca Docker.
- No toca instaladores.
- No incluye documentos reales, bases ni ZIPs de backup en Git.

## v8.3.2 - Cierre automatico del portable Windows

### Resumen

Se ajusta el launcher Windows para que el portable y el instalador se comporten
como una app local: abre una ventana dedicada con Microsoft Edge en modo app
cuando está disponible y cierra `CuadernoPro.exe` al cerrar esa ventana.

### Cambios

- `core/version.py` pasa a `8.3.2`.
- `scripts/probar_release_v8.py` espera `8.3.2`.
- `packaging/windows/cuadernopro_launcher.py` busca `msedge.exe` en rutas
  habituales y en `PATH`.
- Edge se lanza con `--app=http://127.0.0.1:<puerto>` y perfil aislado en
  `Documents\CuadernoPro\browser-profile`.
- El launcher monitoriza el proceso de Edge y termina CuadernoPro al detectar
  el cierre de la ventana.
- Se añade `cuadernopro.lock` en la raíz de datos para reutilizar una instancia
  viva y no arrancar dos servidores Streamlit.
- Se anaden `--browser-mode app/default` y `--no-exit-on-browser-close` para
  diagnóstico y desarrollo.
- `packaging/windows/test_portable_windows.ps1` comprueba que no quedan
  procesos `CuadernoPro.exe` vivos tras la prueba HTTP.

### Compatibilidad

- No cambia el modelo de datos.
- No toca Docker.
- No incluye instaladores ni binarios generados en Git.
- No borra datos del usuario al desinstalar.

## v8.3.1 - Pulido del instalador Windows

### Resumen

Se prepara el branding del build Windows para usar un icono personalizado en el
ejecutable, el instalador Inno Setup, los accesos directos y el favicon de la
app cuando existan los recursos oficiales.

### Cambios

- `core/version.py` pasa a `8.3.1`.
- `scripts/probar_release_v8.py` espera `8.3.1`.
- Se crea `assets/branding/README.md` con las rutas esperadas para
  `cuadernopro.ico` y `cuadernopro.png`.
- PyInstaller usa `assets/branding/cuadernopro.ico` como icono del ejecutable
  cuando existe y avisa claramente si falta.
- Inno Setup usa el icono oficial para el instalador cuando existe.
- Los accesos directos de escritorio y menú inicio usan el icono de
  `CuadernoPro.exe`.
- Streamlit usa `assets/branding/cuadernopro.png` como favicon cuando existe y
  mantiene `🚜` como fallback.
- Los scripts Windows incorporan modo `-Release` para fallar si falta el icono
  oficial.

### Compatibilidad

- No cambia el modelo de datos.
- No toca Docker.
- No incluye instaladores ni binarios generados en Git.
- No borra datos del usuario al desinstalar.

## v8.3.0 - Instalador Windows con Inno Setup

### Resumen

Se prepara el instalador Windows normal de CuadernoPro con Inno Setup a partir
del portable PyInstaller validado.

### Cambios

- `core/version.py` pasa a `8.3.0`.
- `scripts/probar_release_v8.py` espera `8.3.0`.
- Se añade `packaging/windows/build_installer_windows.ps1`.
- Se añade `packaging/windows/test_installer_windows.ps1`.
- Se genera `packaging/windows/CuadernoPro.iss` desde la plantilla Inno Setup.
- El instalador crea accesos directos en escritorio y menú inicio.
- El instalador incluye documentación básica: licencia, avisos, marcas y README.

### Compatibilidad

- No cambia el modelo de datos.
- No toca Docker.
- Usa el portable PyInstaller validado.
- No borra datos del usuario al desinstalar.

## v8.2.2 - Portable Windows y validación PyInstaller

### Resumen

Se corrige el arranque del portable Windows y se ajusta la validación de
artefactos internos del build para no bloquear ficheros legitimos incluidos por
PyInstaller y `pyproj`.

### Cambios

- `core/version.py` pasa a `8.2.2`.
- `scripts/probar_release_v8.py` espera `8.2.2`.
- El launcher Windows configura explicitamente el runtime de Streamlit antes
  de arrancar la app empaquetada.
- La validación del build Windows permite artefactos internos de PyInstaller,
  como `_internal/base_library.zip`, y recursos internos de `pyproj`.
- La validación sigue bloqueando bases, backups, runtime, exports, documentos
  subidos, excels y binarios generados que no deben distribuirse.

### Compatibilidad

- No cambia el modelo de datos.
- No toca Docker.
- No genera instalador Inno Setup final.

## v8.2.0 - Build portable Windows con PyInstaller

### Resumen

Se prepara el build portable Windows de CuadernoPro con PyInstaller. El objetivo
es generar `dist_windows/CuadernoPro/CuadernoPro.exe` desde Windows, sin Docker,
sin WSL y sin terminal para el agricultor.

### Cambios

- `core/version.py` pasa a `8.2.0`.
- `scripts/probar_release_v8.py` espera `8.2.0`.
- Se añade `packaging/windows/CuadernoPro.spec`.
- Se mejora `packaging/windows/build_windows.ps1` para generar
  `dist_windows/CuadernoPro`.
- Se mejora el launcher Windows para modo PyInstaller, argumentos de diagnóstico
  y carpeta de datos temporal para pruebas.
- Se añade `packaging/windows/test_portable_windows.ps1`.
- Se actualiza la documentación Windows.

### Compatibilidad

- No cambia el modelo de datos.
- No toca Docker.
- No genera instalador Inno Setup final.
- Los binarios `dist_windows/`, `dist/`, `build/` y `.exe` quedan fuera de Git.

## v8.1.0 - Distribución libre y preparación Windows sin Docker

### Resumen

Se formaliza CuadernoPro para una nueva línea de distribución libre: programa
completo gratuito para agricultores, licencia GPLv3 o posterior, documentación
CC BY-SA 4.0, marca CuadernoPro controlada y empaquetado Windows sin Docker en
fase preparatoria.

### Cambios

- Se incorpora `LICENSE` con GNU General Public License versión 3.
- Se documenta `GPL-3.0-or-later` ccódigocencia del código.
- Se crea `docs/legal/LICENCIA_DOCUMENTACION.md` para documentación CC BY-SA
  4.0.
- Se crea `TRADEMARKS.md` para aclarar el uso controlado de la marca
  CuadernoPro.
- Se crea `DISCLAIMER.md` con aviso de ausencia de garantía y responsabilidad
  del usuario.
- Se crea `docs/distribucion/DISTRIBUCION_CUADERNOPRO.md` con el modelo de
  descarga libre, servicios opcionales, donativos y dominios previstos.
- Se crean `CONTRIBUTING.md` y `SECURITY.md`.
- Se prepara `packaging/windows/` con launcher, script PyInstaller y plantilla
  Inno Setup sin generar binarios ni instalador.
- Se actualiza la versión visible a la versión 8.1.0.

### Compatibilidad

- No cambia el modelo de datos.
- No toca Docker.
- No genera `.exe`, instaladores, `dist/` ni `build/`.
- No modifica bases reales ni documentos del usuario.

## v8.0.3 - Asignacion automática de campaña en contabilidad por fecha

### Resumen

Contabilidad deja de guardar movimientos nuevos usando ciegamente la campaña
activa. La campaña del movimiento se resuelve por la fecha del movimiento.

### Cambios

- Nuevo helper `detectar_campana_por_fecha(fecha, conn=None)` en
  `core/fechas.py`.
- Alta de movimientos: si la fecha pertenece a otra campaña configurada, se
  guarda esa `campana_id`.
- Edición de movimientos: cambiar la fecha recalcula campaña; cambiar
  concepto, importe u otros campos conserva la campaña existente.
- Si la fecha no encaja en ninguna campaña, se usa la campaña activa como
  fallback y se muestra aviso claro.
- Si hay campañas solapadas, se avisa y se elige la campaña con periodo más
  específico.
- Nuevo diagnóstico sin cambios de datos:
  `scripts/diagnosticar_contabilidad_campanas_v8.py`.
- Nueva prueba especifica:
  `scripts/probar_contabilidad_campana_por_fecha_v8.py`.
- `scripts/probar_release_v8.py` valida la versión 8.0.3 e incluye la
  prueba especifica.

### Compatibilidad

- No cambia el modelo de datos.
- No se migran automáticamente movimientos existentes.
- Listados, balances e informes usan el `campana_id` real guardado en cada
  movimiento.

## v8.0.2 - Versión visible y control de release

### Resumen

Se corrige la versión visible de la interfaz para mostrar la versión 8.0.2
y se añade una comprobacion de versionado a la prueba de release.

### Cambios

- `core/version.py` queda como fuente de verdad para la versión visible.
- La barra lateral usa `version_text()` en lugar de componer la versión en
  `app.py`.
- `scripts/probar_release_v8.py` valida que `APP_VERSION` coincida con la
  versión esperada del release.
- No cambia el modelo de datos.

## v8.0.1 - Multicultivo en tratamientos, fertilización y prácticas

### Resumen

Se extiende a tratamientos, fertilización y prácticas culturales el mismo
criterio multicultivo/multiparcela incorporado previamente en cosecha.

### Motivo agrícola

Permite registrar una actuacion sobre varios cultivos del mismo producto
separados por año de plantación, por ejemplo Almendro 2010, Almendro 2018 y
Almendro 2022.

### Esquema

- Nueva tabla `tratamiento_cultivos`.
- Nueva tabla `fertilizacion_cultivos`.
- Nueva tabla `practicas_culturales_cultivos`.
- `cultivo_id` en cabecera se conserva como primer cultivo seleccionado.
- Las tablas antiguas de parcelas se siguen rellenando por compatibilidad.

### Salidas

- Listados e informes muestran cultivos y parcelas agregados desde el detalle.
- PDF oficial prefiere el texto agregado de cultivos/parcelas.
- Revisión SIEX reconoce el detalle multicultivo.
- Excel SIEX genera filas por detalle cultivo/parcela cuando existe.

### Compatibilidad

- Registros antiguos de cultivo unico siguen funcionando con fallback.
- No hay migración destructiva.
- No se convierten bases v6 legacy automáticamente.

## v8.0.0 - Primera versión limpia estable

## Resumen

La versión 8.0.0 consolida la primera versión limpia estable del proyecto.
Recoge el trabajo de estabilizacion de v7 y deja una base lista para uso real
con instalación limpia, Docker, persistencia SQLite y salidas principales.

## Base limpia v7/v8

- Base SQLite limpia para instalaciones nuevas.
- Ampliaciones idempotentes para bases v7 existentes.
- Diagnóstico de esquema sin columnas legacy prohibidas.
- Validaciones automatizadas sobre bases aisladas en `runtime/`.

## Explotación

- Datos generales de titular y explotación.
- Registro autonómico, tipo de explotación, orientacion productiva y fechas.
- Responsable y asesor.
- Persistencia validada.

## Parcelas SIGPAC

- Alta y gestión de parcelas.
- Referencias SIGPAC estructuradas.
- Superficies y observaciones.
- Integración con mapas y relaciones de cultivo.

## Cultivos

- Cultivos asociados a campaña y parcelas mediante `cultivo_parcelas`.
- Listados normalizados.
- Editores validados.
- Persistencia validada.

## Cálculo de árboles

- Campo `marco_plantacion`.
- Campo `numero_arboles`.
- Cálculo por superficie en hectareas y marco en metros.
- Formatos aceptados: `7x7`, `7X7`, `7 x 7`, `7×7`, `7*7`, `6,5x5`,
  `6.5x5`.
- Número de árboles editable manualmente.

## Cosecha multicultivo

- Tabla puente `cosecha_cultivos`.
- Una cosecha puede incluir varios cultivos.
- Cada cultivo puede aportar una o varias parcelas.
- Superficie calculada desde el detalle seleccionado.
- Compatibilidad con cosechas antiguas de un solo cultivo mediante fallback.

## Maquinaria y equipos

- Maquinaria general.
- Equipos de aplicación.
- Numeros ROMA, matriculas, numeros de serie, fechas, capacidad y horas.
- Listados y editores validados.

## Productos fito

- Productos fitosanitarios con número de registro.
- Materia activa, titular, uso autorizado, plazo de seguridad y observaciones.
- Altas, listados y editores validados.

## Tratamientos

- Tratamientos fitosanitarios estructurados.
- Producto, aplicador, equipo, cultivo, parcelas y fechas.
- Recetas/documentos asociados.
- Listados, editores, PDF, revisión y Excel validados.

## Fertilización

- Fertilizaciones asociadas a campaña, cultivo y parcelas.
- Producto/tipo, cantidad, unidad, superficie y observaciones.
- Persistencia y listados validados.

## Prácticas culturales

- Labores por fecha, cultivo y parcelas.
- Maquinaria y proveedor/prestador.
- Persistencia y listados validados.

## Cosecha

- Cantidad, unidad, cliente, destino y observaciones.
- Detalle multicultivo/multiparcela.
- Listado, editor, informes, PDF y Excel SIEX validados.

## Contabilidad

- Movimientos económicos de ingreso y gasto.
- Clientes/proveedores estructurados.
- IVA, bases, totales, facturas y estado de pago/cobro.
- Persistencia validada.

## Informes

- Informes internos por campaña.
- Resumen de actuaciones, cosecha y economia.
- Sección de cultivos con marco de plantación y número de árboles.

## PDF oficial

- Generación de PDF de cuaderno.
- Datos estructurados desde relaciones limpias.
- Cultivos y parcelas, tratamientos, fertilizaciones, prácticas, cosecha y
  contabilidad.

## Excel SIEX

- Excel asistido para revisión y preparación de datos.
- No es formato oficial SIEX/CUE.
- No envia datos a administraciones.

## Catálogos SIEX

- Pantalla `Catalogos SIEX` con estado,diagnósticon y diagnóstico.
- Importación desde ZIP oficial de catálogos SIEX/CUE.
- CLI `scripts/importar_catalogos_siex.py` con `--db` o
  `CUADERNOPRO_DB_PATH`.
- Reimportacion idempotente sin duplicar items.
- El ZIP oficial no se versiona ni se incluye en el release.

## Revisión SIEX

- Revisión interna de completitud y coherencia.
- Avisos e información sin bloqueo cuando procede.
- Compatible con cosecha multicultivo.

## Mapas

- Visualización de parcelas y estado SIGPAC.
- Integración con cultivos y número de árboles si existe.
- Comportamiento validado sin geometría disponible.

## Docker / WSL

- Docker Compose con puerto configurable.
- Puerto por defecto: `8503`.
- Datos persistentes en `runtime/`.
- Instalación limpia probada en WSL.

## Documentación y release

- Documentación principal v8 en `docs/v8/`.
- Checklist de release v8.
- Script de validación `scripts/probar_release_v8.py`.
- Prueba `scripts/probar_importacion_catalogos_siex_v8.py`.
- ZIP limpio previsto con `git archive` desde el commit/tag de release.
