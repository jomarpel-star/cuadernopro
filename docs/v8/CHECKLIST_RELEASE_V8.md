# Checklist release CuadernoPro v8

## Release v8.4.8

- Versión de producto visible: `8.4.8`.
- Objetivo: añadir radar de lluvia animado al mapa general.
- Modelo de datos: sin cambios.
- Migración manual: no necesaria.
- Documentos reales de usuario: no se versionan.

Cambios previstos:

- [x] Capa de radar opcional y desactivada inicialmente.
- [x] Reproducción, pausa, navegación temporal y hora de observación.
- [x] Funcionamiento seguro sin conexión o sin servicio de radar.
- [x] Atribución visible al proveedor de datos.
- [x] `core/version.py` actualizado a `8.4.8`.
- [x] `scripts/probar_release_v8.py` espera `8.4.8`.

Validaciones antes de publicar:

- [x] Compilación Python desde `.venv`.
- [x] Renderizado de la capa Folium y sus controles.
- [x] `scripts/probar_release_v8.py`.
- [x] `git diff --check` y revisión de artefactos.
- [x] Auditoría de elementos prohibidos seguidos por Git.

## Release v8.4.7

- Versión de producto visible: `8.4.7`.
- Objetivo: heredar provincia y municipio SIGPAC desde la explotación.
- Modelo de datos: sin cambios.
- Migración manual: no necesaria.
- Documentos reales de usuario: no se versionan.

Cambios previstos:

- [x] Eliminados los valores iniciales fijos Murcia/Jumilla de `Nueva parcela`.
- [x] Ubicación de la explotación resuelta contra el catálogo SIGPAC local.
- [x] Selección neutra cuando la ubicación está incompleta o no coincide.
- [x] `core/version.py` actualizado a `8.4.7`.
- [x] `scripts/probar_release_v8.py` espera `8.4.7`.

Validaciones antes de publicar:

- [ ] Compilación Python desde `.venv`.
- [ ] Pruebas específicas de catálogo y ubicación.
- [ ] `scripts/probar_release_v8.py`.
- [ ] `git diff --check` y revisión de artefactos.
- [ ] ZIP de código y ZIP web generados desde la etiqueta correcta.

## Release v8.4.1

- Versión de producto visible: `8.4.0`.
- Objetivo: revisión lingüística de documentación pública.
- Docker: no se toca.
- Base real `cuadernopro.db`: no se toca.
- Modelo de datos: sin cambios.
- Instalador Windows: no se toca.
- Instaladores y binarios generados: no se generan ni versionan.
- Documentos reales de usuario: no se versionan.

Cambios previstos:

- [x] README principal revisado con tildes y redacción más cuidada.
- [x] Textos web y publicación revisados.
- [x] Documentación v8, SIEX y v7 visible revisada.
- [x] `docs/publicacion/GUIA_ESTILO_TEXTOS.md` creada.
- [x] `scripts/auditar_tildes_documentacion.py` creado.
- [x] Checklists actualizadas para exigir revisión lingüística.
- [x] `core/version.py` sin cambios; la versión visible de la app sigue en
  `8.4.0`.

Validaciones antes de publicar:

- [ ] `./venv/bin/python -m py_compile scripts/auditar_tildes_documentacion.py`
- [ ] `./venv/bin/python scripts/auditar_tildes_documentacion.py`
- [ ] grep de referencias a la denominación antigua.
- [ ] búsqueda de artefactos peligrosos.
- [ ] `git diff --check`
- [ ] `git status --short`

## Release v8.4.0

- Versión de producto visible: `8.4.0`.
- Objetivo: preparación de publicación inicial.
- Docker: no se toca.
- Base real `cuadernopro.db`: no se toca.
- Modelo de datos: sin cambios.
- Instalador Windows: no se modifica salvo documentación.
- Instaladores y binarios generados: no se generan ni versionan.
- Documentos reales de usuario: no se versionan.

Cambios previstos:

- [x] `core/version.py` actualizado a `8.4.0`.
- [x] `scripts/probar_release_v8.py` espera `8.4.0`.
- [x] `README.md` revisado para publicación inicial.
- [x] Texto de GitHub Release v8.4.6 creado en
  `docs/publicacion/RELEASE_GITHUB_V8_4_6.md`.
- [x] Textos web creados en `docs/web/`.
- [x] Textos de difusión creados en
  `docs/publicacion/TEXTOS_DIFUSION.md`.
- [x] Checklist de capturas pendientes creado en
  `docs/publicacion/CAPTURAS_PENDIENTES.md`.
- [x] Checklist pública creado en
  `docs/publicacion/CHECKLIST_PUBLICACION.md`.

Validaciones ejecutadas:

- [x] `./venv/bin/python -m py_compile app.py`
- [x] `./venv/bin/python -m py_compile core/version.py`
- [x] `./venv/bin/python -m py_compile scripts/probar_release_v8.py`
- [x] `./venv/bin/python scripts/probar_release_v8.py`
- [x] grep de referencias a la denominación antigua.
- [x] búsqueda de artefactos peligrosos.
- [x] `git diff --check`
- [x] `git status --short`

## Release v8.3.3

- Versión de producto visible: `8.3.3`.
- Objetivo: corregir portada PDF y backup documental completo.
- Docker: no se toca en esta preparación.
- Base real `cuadernopro.db`: no se toca.
- Modelo de datos: sin cambios.
- Instaladores y binarios generados: no se versionan.
- Documentos reales de usuario: no se versionan.

Cambios previstos:

- [x] `core/version.py` actualizado a `8.3.3`.
- [x] `scripts/probar_release_v8.py` espera `8.3.3`.
- [x] Portada PDF usa `campanas.fecha_inicio` como fecha de apertura.
- [x] Portada PDF usa `explotacion.identificador_oficial` para registro
  nacional con fallback legacy.
- [x] Portada PDF usa `explotacion.registro_autonomico` para registro
  autonómico.
- [x] Backup ZIP de usuario incluye `documentos/` desde `DOCS_DIR`.
- [x] Restauración acepta backups antiguos y nuevos con documentos.
- [x] `scripts/probar_pdf_portada_y_backup_docs_v8.py` creado.
- [x] Documentación v8.3.3 creada.

Validaciones antes de cerrar:

- [x] `./venv/bin/python -m py_compile app.py`
- [x] `./venv/bin/python -m py_compile core/version.py`
- [x] `./venv/bin/python -m py_compile modules/backup_page.py`
- [x] `./venv/bin/python -m py_compile services/cuadernopro_pdf.py`
- [x] `./venv/bin/python -m py_compile scripts/probar_pdf_portada_y_backup_docs_v8.py`
- [x] `./venv/bin/python -m py_compile scripts/probar_release_v8.py`
- [x] `./venv/bin/python scripts/probar_pdf_portada_y_backup_docs_v8.py`
- [x] `./venv/bin/python scripts/probar_release_v8.py`
- [x] `./venv/bin/python scripts/probar_pre_v8_v7_14.py`
- [x] `./venv/bin/python scripts/probar_flujo_integral_v7.py`
- [x] `./venv/bin/python scripts/probar_persistencia_editores_v7.py`
- [x] `git diff --check`
- [x] `git status --short`

## Release v8.3.2

- Versión de producto visible: `8.3.2`.
- Objetivo: cierre automatico del portable Windows al cerrar la ventana de app.
- Docker: no se toca en esta preparación.
- Base real `cuadernopro.db`: no se toca.
- Modelo de datos: sin cambios.
- Instaladores y binarios generados: no se versionan.
- Desinstalacion: no borra `Documents\CuadernoPro`.

Cambios previstos:

- [x] `core/version.py` actualizado a `8.3.2`.
- [x] `scripts/probar_release_v8.py` espera `8.3.2`.
- [x] `packaging/windows/cuadernopro_launcher.py` abre Edge en modo app si
  está disponible.
- [x] `packaging/windows/cuadernopro_launcher.py` monitoriza el proceso del
  navegador y cierra CuadernoPro al detectar cierre.
- [x] `packaging/windows/cuadernopro_launcher.py` usa `cuadernopro.lock` para
  reutilizar una instancia viva y evitar segundo servidor.
- [x] `packaging/windows/test_portable_windows.ps1` comprueba que no quedan
  procesos `CuadernoPro.exe` vivos.
- [x] Documentación Windows actualizada.

Validaciones antes de cerrar:

- [x] `./venv/bin/python -m py_compile app.py`
- [x] `./venv/bin/python -m py_compile core/version.py`
- [x] `./venv/bin/python -m py_compile packaging/windows/cuadernopro_launcher.py`
- [x] `./venv/bin/python -m py_compile scripts/probar_release_v8.py`
- [x] `./venv/bin/python scripts/probar_release_v8.py`
- [x] `git diff --check`
- [x] `git status --short`
- [ ] En Windows: `powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_installer_windows.ps1 -Clean -Release`
- [ ] En Windows: instalar CuadernoPro.
- [ ] En Windows: abrir desde acceso directo y confirmar `CuadernoPro v8.3.2`.
- [ ] En Windows: cerrar ventana y comprobar que
  `Get-Process CuadernoPro -ErrorAction SilentlyContinue` no devuelve procesos.
- [ ] En Windows: volver a abrir desde acceso directo y confirmar arranque.
- [ ] En Windows: desinstalar y confirmar que `Documents\CuadernoPro` no se
  borra.

## Release v8.3.1

- Versión de producto visible: `8.3.1`.
- Objetivo: pulido visual del instalador Windows con icono personalizado.
- Docker: no se toca en esta preparación.
- Base real `cuadernopro.db`: no se toca.
- Modelo de datos: sin cambios.
- Instaladores y binarios generados: no se versionan.
- Desinstalacion: no borra `Documents\CuadernoPro`.

Cambios previstos:

- [x] `core/version.py` actualizado a `8.3.1`.
- [x] `scripts/probar_release_v8.py` espera `8.3.1`.
- [x] `assets/branding/README.md` creado.
- [x] `packaging/windows/CuadernoPro.spec` preparado para
  `assets/branding/cuadernopro.ico`.
- [x] `packaging/windows/CuadernoPro.iss.template` preparado para icono de
  instalador y accesos directos.
- [x] `packaging/windows/build_windows.ps1` avisa si falta el icono y falla en
  modo `-Release`.
- [x] `packaging/windows/build_installer_windows.ps1` avisa si falta el icono y
  falla en modo `-Release`.

Validaciones antes de cerrar:

- [ ] `./venv/bin/python -m py_compile app.py`
- [ ] `./venv/bin/python -m py_compile core/version.py`
- [ ] `./venv/bin/python -m py_compile scripts/probar_release_v8.py`
- [ ] `./venv/bin/python scripts/probar_release_v8.py`
- [ ] `git diff --check`
- [ ] `git status --short`
- [ ] En Windows: `powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_installer_windows.ps1 -Clean`
- [ ] En Windows: comprobar `CuadernoPro.exe` con icono personalizado.
- [ ] En Windows: comprobar `CuadernoPro-8.3.1-Setup.exe` con icono
  personalizado.
- [ ] En Windows: comprobar accesos directos de escritorio y menú inicio con
  icono.
- [ ] En Windows: abrir la app correctamente.
- [ ] En Windows: desinstalar y confirmar que `Documents\CuadernoPro` no se
  borra.

## Release v8.3.0

- Versión de producto visible: `8.3.0`.
- Objetivo: instalador Windows con Inno Setup.
- Portable PyInstaller: se reconstruye y valida antes de compilar el instalador.
- Docker: no se toca en esta preparación.
- Base real `cuadernopro.db`: no se toca.
- Modelo de datos: sin cambios.
- Desinstalacion: no borra `Documents\CuadernoPro`.

Cambios previstos:

- [x] `core/version.py` actualizado a `8.3.0`.
- [x] `scripts/probar_release_v8.py` espera `8.3.0`.
- [x] `packaging/windows/build_installer_windows.ps1` creado.
- [x] `packaging/windows/CuadernoPro.iss.template` preparado.
- [x] `packaging/windows/test_installer_windows.ps1` creado.
- [x] `.gitignore` excluye instaladores, portable y artefactos generados.

Validaciones antes de cerrar:

- [ ] `python -m py_compile app.py`
- [ ] `python -m py_compile core/version.py`
- [ ] `python -m py_compile packaging/windows/cuadernopro_launcher.py`
- [ ] `python -m py_compile scripts/probar_release_v8.py`
- [ ] `python scripts/probar_release_v8.py`
- [ ] En Windows: `powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_installer_windows.ps1 -Clean`
- [ ] En Windows: comprobar `packaging\windows\output\CuadernoPro-8.3.0-Setup.exe`.
- [ ] En Windows: probar instalación, accesos directos, arranque, logs y base local.
- [ ] En Windows: desinstalar y confirmar que `Documents\CuadernoPro` no se borra.

## Release v8.2.0

- Versión de producto visible: `8.2.0`.
- Objetivo: build portable Windows con PyInstaller.
- Docker: no se toca en esta preparación.
- Instalador Inno Setup final: no se genera.
- Base real `cuadernopro.db`: no se toca.
- Modelo de datos: sin cambios.

Cambios previstos:

- [x] `core/version.py` actualizado a `8.2.0`.
- [x] `scripts/probar_release_v8.py` espera `8.2.0`.
- [x] `packaging/windows/CuadernoPro.spec` preparado.
- [x] `packaging/windows/build_windows.ps1` orientado a
  `dist_windows/CuadernoPro`.
- [x] `packaging/windows/cuadernopro_launcher.py` preparado para PyInstaller.
- [x] `packaging/windows/test_portable_windows.ps1` creado.
- [x] `.gitignore` excluye `dist_windows/`, `dist/`, `build/` y binarios.

Validaciones antes de cerrar:

- [ ] `python -m py_compile app.py`
- [ ] `python -m py_compile core/version.py`
- [ ] `python -m py_compile packaging/windows/cuadernopro_launcher.py`
- [ ] `./venv/bin/python scripts/probar_release_v8.py`
- [ ] En Windows: `powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_windows.ps1 -Clean`
- [ ] En Windows: comprobar `dist_windows\CuadernoPro\CuadernoPro.exe`.
- [ ] En Windows: arrancar el portable y comprobar navegador, logs y datos en
  `Documents\CuadernoPro`.

## Release v8.1.0

- Versión de producto visible: `8.1.0`.
- Objetivo: distribución libre, licencia GPLv3 o posterior, documentación
  CC BY-SA 4.0 y preparación Windows sin Docker.
- Docker: no se toca en esta preparación.
- Instaladores: no se generan.
- Base real `cuadernopro.db`: no se toca.
- Modelo de datos: sin cambios.

Cambios previstos:

- [x] `LICENSE` con GNU General Public License versión 3.
- [x] Código documentado como `GPL-3.0-or-later`.
- [x] Documentación bajo CC BY-SA 4.0 en
  `docs/legal/LICENCIA_DOCUMENTACION.md`.
- [x] `TRADEMARKS.md` para marca CuadernoPro controlada.
- [x] `DISCLAIMER.md` pargarantíaia de garantía.
- [x] `docs/distribucion/DISTRIBUCION_CUADERNOPRO.md`.
- [x] `CONTRIBUTING.md`.
- [x] `SECURITY.md`.
- [x] `packaging/windows/` preparado sin binarios.
- [x] `.gitignore` excluye build, dist, instaladores, bases, ZIPs y artefactos.
- [x] `core/version.py` actualizado a `8.1.0`.
- [x] `scripts/probar_release_v8.py` espera `8.1.0`.

Checklist legal antes de publicar:

- [ ] Revisar que no hay claves ni secretos.
- [ ] Revisar que no hay bases de datos reales.
- [ ] Revisar que no hay documentos PDF reales.
- [ ] Revisar que no hay datos personales.
- [ ] Revisar que no hay catálogos ZIP oficiales versionados.
- [ ] Revisar compatibilidad de dependencias con GPLv3.
- [ ] Revisar `LICENSE`.
- [ ] Revisar `DISCLAIMER.md`.
- [ ] Revisar `TRADEMARKS.md`.
- [ ] Revisar `README.md`.
- [ ] Ejecutar grep de referencias antiguas.
- [ ] Ejecutar `./venv/bin/python scripts/probar_release_v8.py`.
- [ ] Generar ZIP limpio desde commit/tag correcto.

## Parche v8.0.3

- Versión: `8.0.3`
- Objetivo: asignar automáticamente la campaña de movimientos contables por la
  fecha del movimiento.
- Tag previsto: `v8.0.3`
- Docker: no se toca en este parche
- Instaladores: no se tocan
- Base real `cuadernopro.db`: no se toca
- Modelo de datos: sin cambios
- Migración automática de movimientos existentes: no incluida

Cambios:

- `core/version.py` actualizado para mostrar la versión 8.0.3.
- `core/fechas.py` incorpora `detectar_campana_por_fecha(fecha, conn=None)`.
- `modules/contabilidad.py` usa la fecha del movimiento para guardar
  `campana_id`.
- Si la fecha no pertenece a ninguna campaña, se usa la campaña activa como
  fallback y se avisa.
- Nuevo diagnóstico:
  `scripts/diagnosticar_contabilidad_campanas_v8.py --db RUTA`.
- Nueva prueba especifica:
  `scripts/probar_contabilidad_campana_por_fecha_v8.py`.
- `scripts/probar_release_v8.py` esperaba 8.0.3 e incluye la prueba especifica.

Validaciones ejecutadas el 2026-07-05:

- [x] `./venv/bin/python -m py_compile app.py core/version.py core/fechas.py modules/contabilidad.py modules/informes.py scripts/probar_contabilidad_campana_por_fecha_v8.py scripts/diagnosticar_contabilidad_campanas_v8.py scripts/probar_release_v8.py`
- [x] `./venv/bin/python scripts/probar_contabilidad_campana_por_fecha_v8.py`
- [x] `./venv/bin/python scripts/diagnosticar_contabilidad_campanas_v8.py --db runtime/v8/prueba_contabilidad_campana_fecha_v8.db`
- [x] `./venv/bin/python scripts/probar_release_v8.py`
- [x] bateria principal v7/v8 indicada para el parche
- [x] `git diff --check`
- [x] `git status --short`

Prueba manual preparada:

- Base: `runtime/v8/prueba_manual_v8_0_3.db`
- URL: `http://192.168.0.13:8517`
- PID: `runtime/v8/streamlit_v8_0_3.pid`
- Comprobar en Contabilidad que un movimiento de `2024/2025` se asigna a esa
  campaña aunque la activa sea `2025/2026`.

## Parche v8.0.2

- Versión: `8.0.2`
- Objetivo: actualizar versión visible y anadir control de release.
- Tag previsto: `v8.0.2`
- Docker: no se toca en este parche
- Instaladores: no se tocan salvo documentacion/checklist
- Base real `cuadernopro.db`: no se toca
- Modelo de datos: sin cambios

Cambios:

- `core/version.py` actualizado para mostrar la versión 8.0.2.
- La barra lateral usa `version_text()` desde `core/version.py`.
- `scripts/probar_release_v8.py` valida `APP_VERSION` contra
  `VERSION_ESPERADA`.

## Control obligatorio de versionado

- [ ] Actualizar `core/version.py`.
- [ ] Verificar que la barra lateral muestra la versión correcta.
- [ ] Ejecutar `./venv/bin/python scripts/probar_release_v8.py`.
- [ ] Comprobar que `APP_VERSION` coincide con el tag a generar.

## Parche v8.0.1

- Versión: `8.0.1`
- Objetivo: multicultivo/multiparcela en tratamientos, fertilización y
  prácticas culturales.
- Tag previsto: `v8.0.1`
- Commit: pendiente
- Docker: no se toca en este parche
- Instaladores: no se tocan en este parche
- Base real `cuadernopro.db`: no se toca

Pruebas especificas ejecutadas el 2026-07-03:

- [x] `./venv/bin/python -m py_compile core/schema_v7.py core/db.py core/actuaciones_multicultivo.py modules/tratamientos.py modules/fertilizacion.py modules/practicas_culturales.py modules/informes.py modules/revision_siex.py services/cuadernopro_pdf.py services/exportacion_siex.py scripts/probar_actuaciones_multicultivo_v8.py`
- [x] `./venv/bin/python scripts/probar_actuaciones_multicultivo_v8.py`
- [x] `./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v8/prueba_actuaciones_multicultivo_v8.db`
- [x] `./venv/bin/python scripts/probar_release_v8.py`
- [x] bateria v7/v8 indicada para el parche
- [x] `git diff --check`
- [x] `git status --short`

Pendiente antes de cerrar v8.0.1:

- [ ] Comprobacion visual en navegador con `runtime/v8/prueba_manual_v8_0_1.db`.

Tablas nuevas:

- `tratamiento_cultivos`
- `fertilizacion_cultivos`
- `practicas_culturales_cultivos`

Compatibilidad:

- `cultivo_id` de cabecera conserva el primer cultivo seleccionado.
- `tratamiento_parcelas`, `fertilizacion_parcelas` y
  `practicas_culturales_parcelas` siguen rellenandose.
- Lecturas y salidas hacen fallback a datos antiguos si no hay detalle nuevo.

## Estado

- Versión: `8.0.0`
- Estado: `estable`
- Tag previsto: `v8.0.0`
- Commit: pendiente
- ZIP: pendiente hasta tener commit/tag v8.0

## Pruebas automatizadas

Ejecutadas el 2026-07-03: OK.

- [x] `./venv/bin/python -m py_compile app.py`
- [x] `./venv/bin/python -m py_compile core/db.py`
- [x] `./venv/bin/python -m py_compile core/schema_v7.py`
- [x] `./venv/bin/python -m py_compile core/ui_tablas.py`
- [x] `./venv/bin/python -m py_compile core/version.py`
- [x] `./venv/bin/python -m py_compile modules/catalogos_siex.py`
- [x] `./venv/bin/python -m py_compile services/siex_catalogos.py`
- [x] `./venv/bin/python -m py_compile services/catalogos_siex_importer.py`
- [x] `./venv/bin/python -m py_compile scripts/importar_catalogos_siex.py`
- [x] `./venv/bin/python -m py_compile scripts/probar_importacion_catalogos_siex_v8.py`
- [x] `./venv/bin/python -m py_compile scripts/probar_release_v8.py`
- [x] `./venv/bin/python scripts/probar_importacion_catalogos_siex_v8.py`
- [x] `./venv/bin/python scripts/probar_release_v8.py`
- [x] `./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v8/prueba_release_v8.db`
- [x] `git diff --check`
- [x] `git status --short`

Resultado: `scripts/probar_release_v8.py` concluye `release v8 validada`.

Pruebas incluidas en `scripts/probar_release_v8.py`:

- [x] diagnóstico de esquema sobre base limpia v8
- [x] `scripts/probar_importacion_catalogos_siex_v8.py`
- [x] `scripts/probar_schema_v7_13.py`
- [x] `scripts/probar_cultivos_arboles_v7.py`
- [x] `scripts/probar_cosecha_multicultivo_v7.py`
- [x] `scripts/probar_actuaciones_multicultivo_v8.py`
- [x] `scripts/probar_persistencia_editores_v7.py`
- [x] `scripts/probar_pre_v8_v7_14.py`
- [x] `scripts/probar_listados_v7.py`
- [x] `scripts/auditar_tablas_visuales_v7.py`
- [x] `scripts/probar_render_modulos_v7.py`
- [x] `scripts/probar_editores_auxiliares_v7.py`
- [x] `scripts/probar_flujo_integral_v7.py`

## Base limpia v8

- [x] Crear `runtime/v8/prueba_release_v8.db`.
- [x] Ejecutar diagnóstico sobre `runtime/v8/prueba_release_v8.db`.
- [x] Confirmar `PRAGMA user_version = 7`.
- [x] Confirmar que el esquema limpio actual es valido para CuadernoPro v8.0.

Nota: el generador se llama `scripts/crear_base_v7.py` porque el esquema limpio
se consolido durante v7. En v8.0 se mantiene el nombre para evitar renombrados
de riesgo.

## Docker

- [ ] `docker compose up -d --build --remove-orphans`
- [ ] `docker compose ps`
- [ ] Aplicación disponible en `http://localhost:8503` o puerto configurado.
- [ ] Datos persistentes en `runtime/`.

Nota: Docker venia validado de v7.17. En este hito no se reconstruye antes del
commit/tag v8.0.

## Catálogos SIEX

- [x] Pantalla `Catalogos SIEX` con estado,diagnósticon y diagnóstico.
- [x] Servicio reutilizable para importar ZIP oficial.
- [x] CLI `scripts/importar_catalogos_siex.py` con `--db`.
- [x] Prueba con ZIP sintetico en `runtime/v8/`.
- [x] Segunda importación sin duplicar catálogos ni items.
- [x] Revisión SIEX y Excel asistido no rompen tras importar catálogos.
- [ ] Prueba manual con ZIP oficial real descargado por el usuario.

Notas:

- `scripts/probar_importacion_catalogos_siex_v8.py`: OK. El diagnóstico queda
  en `ADVERTENCIAS` con el ZIP sintetico porque solo incluye catálogos mínimos
  de prueba.
- El ZIP oficial no se guarda en la base ni en Git.
- `*.zip` y `*.xlsx` están excluidos por `.gitignore`.
- El CLI no usa `cuadernopro.db` por defecto si no se indica `--db` o
  `CUADERNOPRO_DB_PATH`.

## ZIP limpio

Comandos previstos tras commit/tag v8.0:

```bash
git archive \
  --format=zip \
  --prefix=cuadernopro-v8.0/ \
  -o backups/cuadernopro_codigo_v8_0.zip \
  HEAD

zipinfo -1 backups/cuadernopro_codigo_v8_0.zip | grep -i "a[g]rogex" \
  || echo "ZIP limpio: sin referencias antiguas"

zipinfo -1 backups/cuadernopro_codigo_v8_0.zip | grep -E '\.db|^.*backups/|runtime/|exports/|venv/|__pycache__|app_backup_ok|\.save|documentos/facturas|documentos/recetas|facturas/.*\.pdf|recetas/.*\.pdf|data/.*\.zip|Catalogos_SIEX.*\.zip|\.xlsx$' \
  || echo "ZIP limpio: sin bases, backups, runtime, caches, temporales, documentos subidos, catalogos originales ni excels"
```

Debe cumplirse:

- [ ] Sin referencias antiguas de denominación previa.
- [ ] Sin bases `.db`.
- [ ] Sin `runtime/`.
- [ ] Sin `backups/`.
- [ ] Sin `exports/`.
- [ ] Sin `venv/`.
- [ ] Sin `__pycache__/`.
- [ ] Sin PDFs, excels, documentos subidos ni catálogos originales.

## Prueba manual final

Base:

- `runtime/v8/prueba_manual_v8.db`

URL:

- `http://192.168.0.13:8517`

Checklist manual:

- [ ] Inicio / configuración inicial
- [ ] Explotación
- [ ] Campañas
- [ ] Parcelas
- [ ] Cultivos con cálculo de árboles
- [ ] Cosecha multicultivo
- [ ] Maquinaria/equipos
- [ ] Productos fito
- [ ] Tratamientos
- [ ] Fertilización
- [ ] Prácticas culturales
- [ ] Cosecha
- [ ] Contabilidad
- [ ] Informes
- [ ] PDF oficial
- [ ] Revisión SIEX
- [ ] Excel SIEX
- [ ] Catálogos SIEX / importación ZIP oficial
- [ ] Mapas/SIGPAC
- [ ] Backup

Resultado manual:

- Base limpia manual creada: `runtime/v8/prueba_manual_v8.db`.
- Streamlit arrancado en `http://192.168.0.13:8517`.
- PID guardado en `runtime/v8/streamlit_v8.pid`.
- Pendiente de comprobacion visual en navegador.

## Prueba manual v8.0.1

Base:

- `runtime/v8/prueba_manual_v8_0_1.db`

URL:

- `http://192.168.0.13:8518`

Notas:

- El puerto solicitado `8517` estaba ocupado.
- PID guardado en `runtime/v8/streamlit_v8_0_1.pid`.
- Pendiente de comprobacion visual en navegador.

## Instalación limpia

- [ ] Descomprimir ZIP limpio.
- [ ] Ejecutar Docker Compose.
- [ ] Completar asistente inicial.
- [ ] Crear datos mínimos.
- [ ] Generar backup.
- [ ] Verificar que no se toca `cuadernopro.db` real de desarrollo.

## Exclusiones obligatorias

No deben aparecer en el ZIP ni en `git status --short`:

- `runtime/`
- bases `.db`
- `exports/`
- PDFs
- Excels
- `backups/`
- temporales
- `venv/`
- `__pycache__/`

## Pendientes conocidos

- No hay conexion directa oficial con SIEX/CUE.
- Los scripts internos conservan nombres v7 para evitar renombrados de riesgo.
- La revisión legal, comercial y de licencias debe repetirse antes de una
  distribución pública.
- Para publicar en Internet se debe usar proxy, HTTPS y control de acceso.
