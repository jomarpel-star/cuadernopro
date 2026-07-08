# Estado v7.15 - Reseteo coherente de formularios tras guardar

## Objetivo

Pulir la UX de formularios principales antes de v8.0 para que, tras un
guardado correcto, no queden campos de alta rellenos con datos anteriores, se
refresquen listados y se reduzca el riesgo de duplicar registros por accidente.

## Módulos revisados

Revisados en esta fase:

- `modules/asistente_inicio.py`
- `modules/explotacion.py`
- `modules/campanas.py`
- `modules/terceros.py`
- `modules/parcelas.py`
- `modules/cultivos.py`
- `modules/maquinaria.py`
- `modules/productos_fito.py`
- `modules/tratamientos.py`
- `modules/fertilizacion.py`
- `modules/practicas_culturales.py`
- `modules/cosecha.py`
- `modules/contabilidad.py`

También se reviso el helper compartido:

- `core/borrado.py`

## Formularios corregidos

Cambios aplicados:

- Asistente inicial: versionado de formularios de campana inicial,
  explotación, persona y equipo.
- Campanas: mensaje persistente tras rerun y versionado del editor de
  campanas.
- Terceros: versionado de altas de clientes/proveedores, editor y
  desactivacion.
- Explotación: refresco tras guardar titular, datos de explotación,
  responsable/asesor, personas y equipos; reinicio de confirmaciones de
  editores.
- Parcelas: refresco y reinicio del editor tras guardar cambios reales.
- Maquinaria/equipos: reinicio del editor de maquinaria y limpieza de borrado
  propio.
- Productos fito: reset tras alta y tras actualizar un producto existente desde
  el formulario de alta; refresco del editor masivo.
- Borrado seguro comun: limpieza de seleccion, confirmacion y texto `BORRAR`
  tras borrado correcto.

## Formularios que no deben resetearse

No se resetean por decisión:

- Filtros de busqueda/listado: se mantienen para no romper el contexto de
  revisión.
- Campana activa global: se mantiene salvo cuando el propio formulario de
  campanas cambia la campana activa.
- Editores masivos sin cambios: no fuerzan rerun si no habia diferencias que
  guardar.
- Formularios con error de validación: conservan el contenido para que el
  usuario pueda corregirlo.
- Acciones auxiliares como adjuntar PDF, asignar cultivo/cliente o guardar
  recetas/facturas: mantienen contexto porque no son formularios de alta
  normal.

## Patron usado

Patron principal:

- claves de versión en `st.session_state`, por ejemplo
  `form_<modulo>_version` o `<modulo>_editor_version`;
- keys de widgets dependientes de esa versión;
- incremento de versión solo tras guardado correcto;
- mensaje persistente en `st.session_state` cuando hay `st.rerun()`;
- limpieza puntual de claves auxiliares en borrado seguro.

No se ha hecho borrado agresivo de `st.session_state`.

## Script de auditoria

Creado:

- `scripts/auditar_reset_formularios_v7.py`

El script inspecciona `modules/` y detecta:

- `st.form_submit_button`;
- `st.button` con acciones de guardar/crear/actualizar/registrar/borrar;
- `st.success`;
- `st.rerun`;
- claves `_version`;
- `clear_on_submit`;
- limpiezas explicitas con `st.session_state.pop`.

También se creo:

- `scripts/probar_reset_formularios_v7.py`

Esta prueba estatica valida los módulos críticos modificados y la limpieza del
borrado seguro comun. No toca bases de datos.

## Pruebas realizadas

Ejecutado en v7.15:

- `./venv/bin/python -m py_compile app.py scripts/auditar_reset_formularios_v7.py scripts/probar_reset_formularios_v7.py modules/asistente_inicio.py modules/explotacion.py modules/campanas.py modules/terceros.py modules/parcelas.py modules/cultivos.py modules/maquinaria.py modules/productos_fito.py modules/tratamientos.py modules/fertilizacion.py modules/practicas_culturales.py modules/cosecha.py modules/contabilidad.py core/borrado.py`: OK.
- `./venv/bin/python scripts/crear_base_v7.py runtime/v7/prueba_manual_v7_15.db`: OK, `PRAGMA user_version = 7`, 25 tablas.
- `./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v7/prueba_manual_v7_15.db`: OK.
- `./venv/bin/python scripts/probar_pre_v8_v7_14.py`: OK, candidata v8.0: Si.
- `./venv/bin/python scripts/probar_schema_v7_13.py`: OK.
- `./venv/bin/python scripts/probar_persistencia_editores_v7.py`: OK.
- `./venv/bin/python scripts/probar_listados_v7.py`: OK.
- `./venv/bin/python scripts/auditar_tablas_visuales_v7.py`: OK, 47 llamadas revisadas, 0 advertencias.
- `./venv/bin/python scripts/probar_render_modulos_v7.py`: OK.
- `./venv/bin/python scripts/probar_editores_auxiliares_v7.py`: OK.
- `./venv/bin/python scripts/probar_flujo_integral_v7.py`: OK.
- `./venv/bin/python scripts/auditar_reset_formularios_v7.py`: ejecutado; altas principales OK y avisos en acciones auxiliares/editores sin versionado dedicado.
- `./venv/bin/python scripts/probar_reset_formularios_v7.py`: OK.
- `git diff --check`: OK.

Prueba manual:

- base creada: `runtime/v7/prueba_manual_v7_15.db`;
- servidor arrancado con PID guardado en `runtime/v7/streamlit_v7_15.pid`;
- URL verificada: `http://192.168.0.13:8517`;
- comprobacion visual completa en navegador: pendiente de ejecución manual.

## Pendientes para v8.0

- Completar la prueba manual en navegador con base limpia v7.15.
- Mantener como deuda menor los avisos del auditor en acciones auxiliares que
  no son altas normales, por si se quiere versionarlas en v8.x.
- Si se introduce AppTest más adelante, cubrir de forma real los formularios de
  alta de tratamientos, fertilización, prácticas, cosecha y contabilidad.
