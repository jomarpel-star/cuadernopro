# Estado v7.10 - Prueba manual e incidencia de listados

## Objetivo

Preparar y ejecutar la fase de prueba manual completa de interfaz sobre una
base v7 limpia, comprobando que los datos introducidos en formularios se
persisten y vuelven a verse en listados y editores.

Base usada:

`runtime/v7/prueba_manual_v7_10.db`

Desde la normalización general de listados, las bases quedan separadas:

- prueba manual navegador: `runtime/v7/prueba_manual_v7_10.db`;
- pruebas automáticas de listados: `runtime/v7/prueba_listados_v7.db`.

## Problema detectado

Durante la prueba manual se detecto que algunos formularios permitian rellenar
campos que luego aparecian vacios o no se recuperaban en listados.

Ejemplos visuales:

- nombre de explotación;
- Código REGEPA / identificador oficial;
- `nombre_explotacion = None` mostrado literalmente en la pestaña
  Explotación;
- identificador oficial mostrado bajo el alias `codigo_regea` y no como Código
  REGEPA / identificador oficial;
- columnas técnicas visibles en el `data_editor` de la pestaña Explotación;
- número ROMA;
- número de serie;
- fechas;
- campos auxiliares de maquinaria y equipos.
- `KeyError: responsable_nombre` en Responsable / Asesor por usar un
  `data_editor` con columnas renombradas y luego guardar esperando nombres
  internos.
- `AssertionError` en Contabilidad / Listado por un `assert` de desarrollo
  sobre el dtype de `fecha` dentro del render.
- Inicio / Configuración inicial / Campaña mostraba encabezados tecnicos:
  `nombre`, `fecha_inicio`, `fecha_fin`, `activa`.
- Inicio / Configuración inicial / Explotación pedia Titular / razon social,
  pero no pedia de forma explicita Nombre de la explotación; después el
  resumen/listado mostraba ese campo vacío.

La causa principal no era el esquema v7, sino la interfaz: algunas pantallas
seguian mostrando campos de compatibilidad v6 o campos que ya no existen en la
base v7 limpia.

## Módulos auditados

- Explotación
- Campanas
- Parcelas
- Cultivos
- Maquinaria
- Equipos de aplicación
- Personas / aplicadores
- Productos fitosanitarios
- Tratamientos
- Fertilización
- Prácticas culturales
- Cosecha
- Contabilidad
- Informes

Detalle completo:

`docs/v7/AUDITORIA_FORMULARIOS_LISTADOS_V7.md`

## Correcciones aplicadas

### Explotación

- `nombre_explotacion` se confirma como campo limpio v7 para el nombre de la
  explotación.
- `identificador_oficial` se confirma como campo limpio v7 para Código REGEPA /
  identificador oficial.
- La pestaña Explotación deja de mostrar `codigo_regea` y `codigo_regepa` como
  columnas separadas en v7.
- El `data_editor` de Datos de la explotación recibe ahora un DataFrame ya
  renombrado con etiquetas limpias; no depende solo de `column_config`.
- La vista visible de Datos del titular, Datos de la explotación,
  Responsable y Asesor se muestra como tabla limpia; la edición queda en un
  desplegable.
- Personas relacionadas y equipos de aplicación usan etiquetas limpias en sus
  editores y mapean de vuelta a columnas reales al guardar.
- Responsable / Asesor mantiene columnas internas en el editor
  (`responsable_nombre`, `asesor_nombre`, etc.) y usa `column_config` para
  mostrar etiquetas limpias.
- El guardado mapea esas etiquetas visuales a columnas internas antes de
  actualizar la tabla.
- El bloque de borrado seguro de la misma sección recibe una vista visual
  limpia, evitando que vuelva a aparecer `datos_explotacion` crudo.
- Se usa un unico campo visual normalizado para Código REGEPA / identificador
  oficial, alimentado por `identificador_oficial` y con fallback a columnas
  legacy solo si existen en bases antiguas.
- El guardado escribe el identificador en `identificador_oficial` como campo
  canónico v7.
- Si una base antigua contiene `codigo_regepa` o `codigo_regea`, se mantiene la
  escritura compatible sin anadir esas columnas a v7.
- El resumen/listado muestra nombre de explotación, titular, NIF, Código
  REGEPA / identificador oficial, municipio y provincia.
- La métrica de datos de explotación ya no exige `tipo_explotacion` cuando esa
  columna no existe en v7 limpia.
- Quedan como mejora posterior orientacion productiva, fecha alta y agricultor
  activo, porque no forman parte del formulario prioritario revisado.

### Maquinaria

- El campo visible pasa a ser `Nombre / descripcion` cuando la tabla v7 usa
  `descripcion`.
- Se incorpora `matricula` a formulario, listado, previsualizacion y editor.
- `numero_roma` se mantiene y se valida como campo v7.
- `numero_serie`, `fecha_compra` y `num_horas` solo se muestran si existen en
  la tabla.

### Equipos de aplicación

- El formulario deja de pedir `numero_roma`, `fecha_adquisicion` y
  `capacidad_litros` cuando no existen en v7.
- Las fechas se presentan como `fecha_revision` y
  `fecha_proxima_revision`.
- `numero_serie` se mantiene como campo v7.

### Personas

- `fecha_caducidad_carnet` se oculta si la columna no existe.
- El carnet visual sigue mapeando a `carnet_aplicador` en v7.

### Contabilidad

- Se elimina el `assert` de desarrollo que podia tumbar el listado.
- `fecha` y `fecha_pago` se convierten con `pd.to_datetime(...,
  errors="coerce")` antes de ordenar o mostrar.
- El listado queda estable aunque no haya movimientos o existan fechas vacias.

### Asistente inicial

- La pestaña Inicio / Configuración inicial / Campaña usa una vista visual
  limpia.
- La tabla muestra `Campaña`, `Fecha inicio`, `Fecha fin` y `Activa`.
- Ya no muestra `nombre`, `fecha_inicio`, `fecha_fin` ni `activa` como
  encabezados tecnicos.
- La pestaña Inicio / Configuración inicial / Explotación incluye ahora
  `Nombre de la explotacion`.
- Si se deja vacío, se guarda el valor de `Titular / razon social` como
  fallback en `nombre_explotacion`.
- `Codigo REGEPA / identificador oficial` se guarda en
  `identificador_oficial`.

## Script nuevo

Se crea:

`scripts/probar_listados_v7.py`

La prueba usa solo:

`runtime/v7/prueba_listados_v7.db`

El script inserta registros de auditoria y verifica por consultas directas que
los campos principales se recuperan para listados:

- explotación con `nombre_explotacion`, `identificador_oficial`, titular, NIF,
  municipio y provincia;
- maquinaria con `descripcion`, `matricula` y `numero_roma`;
- equipo de aplicación con `numero_serie`, `fecha_revision` y
  `fecha_proxima_revision`;
- parcela SIGPAC;
- cultivo asociado a parcela mediante `cultivo_parcelas`;
- tratamiento con producto, aplicador, equipo y parcelas;
- fertilización;
- practica cultural;
- cosecha;
- movimiento contable de ingreso;
- movimiento contable de gasto.

Resultado obtenido:

- `scripts/probar_listados_v7.py`: OK.

## Normalizacion visual de listados

Se crea:

`core/ui_tablas.py`

Objetivo:

- centralizar etiquetas visibles;
- ocultar columnas técnicas en listados de usuario;
- normalizar valores vacios;
- permitir mapeo visual -> técnico en editores sencillos.

Regla definitiva:

- `st.dataframe` y listados solo visuales pueden usar
  `preparar_dataframe_visual()` y renombrar/ocultar columnas.
- `st.data_editor` con guardado debe mantener columnas internas y usar
  `column_config`, o mapear explicitamente visual -> interno antes de guardar.

Modelo funcional:

- Titular / razon social identifica a la persona fisica o juridica:
  `titular`, `nif`, dirección, municipio, provincia, código postal, teléfono y
  email.
- Nombre de la explotación identifica la explotación agraria y se persiste en
  `nombre_explotacion`.

Listados corregidos en esta pasada:

- Borrado seguro comun: previsualizacion con etiquetas limpias.
- Explotación: titular, datos de explotación, responsable, asesor, personas y
  equipos.
- Campanas: listado visible sin `id`; editor en desplegable.
- Parcelas: listado y editor sin `geometry`.
- Cultivos: listado principal.
- Maquinaria: listado y previsualizacion.
- Productos fitosanitarios: alta, listado principal y editor.
- Tratamientos: listado principal sin IDs tecnicos, análisis y recetas
  adjuntas.
- Fertilización: listado principal.
- Prácticas culturales: listado principal.
- Cosecha: listado principal.
- Contabilidad: listado principal, pendientes, detalle IVA y facturas adjuntas.

Se crea también:

`scripts/auditar_tablas_visuales_v7.py`

Resultado actual:

- llamadas detectadas: 45;
- OK con helper visual cercano o renombrado explicito: 25;
- advertencias pendientes: 20.
- tras corregir los editores/listados detectados: 46 llamadas detectadas, 28 OK
  y 18 advertencias pendientes.
- tras corregir Campaña del asistente inicial: 46 llamadas detectadas, 29 OK y
  17 advertencias pendientes.

Detalle:

`docs/v7/AUDITORIA_LISTADOS_VISUALES_V7.md`

## Resultados de validación

Validaciones ejecutadas:

```bash
./venv/bin/python -m py_compile app.py
./venv/bin/python -m py_compile modules/explotacion.py
./venv/bin/python -m py_compile modules/parcelas.py
./venv/bin/python -m py_compile modules/cultivos.py
./venv/bin/python -m py_compile modules/maquinaria.py
./venv/bin/python -m py_compile modules/tratamientos.py
./venv/bin/python -m py_compile modules/fertilizacion.py
./venv/bin/python -m py_compile modules/practicas_culturales.py
./venv/bin/python -m py_compile modules/cosecha.py
./venv/bin/python -m py_compile modules/contabilidad.py
./venv/bin/python -m py_compile scripts/probar_listados_v7.py
```

También ejecutadas:

```bash
./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v7/prueba_manual_v7_10.db
./venv/bin/python scripts/probar_listados_v7.py
./venv/bin/python scripts/probar_flujo_integral_v7.py
./venv/bin/python scripts/probar_render_modulos_v7.py
```

Resultado:

- diagnóstico schema v7 de la base manual: OK;
- `scripts/probar_listados_v7.py`: OK;
- flujo integral v7: OK;
- render AppTest de Explotación, Responsable / Asesor, Cultivos, Parcelas,
  Maquinaria, Contabilidad / Listado vacío y vista visual de Campaña del
  asistente inicial: OK.
- `scripts/probar_listados_v7.py` comprueba explotación con nombre explicito y
  explotación con nombre vacío usando titular como fallback persistido: OK.
- `scripts/probar_render_modulos_v7.py` comprueba el fallback del asistente:
  OK.

## Schema v7

No se modifica `core/schema_v7.py`.

No se anaden columnas legacy.

Los campos no presentes en v7 se tratan como no aplicables o como candidatos a
una futura ampliacion limpia del esquema, no como campos legacy a reintroducir.

## Pendiente para v7.11

- Repetir la prueba manual visual completa tras las correcciones.
- Decidir si v7 necesita ampliar de forma limpia la tabla `maquinaria` para
  `fecha_compra`, `num_horas` o `numero_serie`.
- Revisar exposición visual de `uso_sigpac` y `cultivos.observaciones`.
- Convertir avisos manuales restantes en pruebas automatizadas si afectan a
  listados, editores o exportaciones.
