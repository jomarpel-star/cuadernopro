# Estado v7.9 - Adaptar pantallas con dependencias legacy

## Objetivo

La fase v7.9 adapta pantallas Streamlit que todavía rompían al renderizar
contra una base v7 limpia.

La prioridad es mantener `core/schema_v7.py` limpio, sin reintroducir columnas
legacy para compensar código de interfaz.

Base de prueba usada:

`runtime/v7/prueba_render_v7.db`

## Errores detectados en v7.8

La prueba integral de v7.8 confirmo que el flujo de datos funcionaba sobre
esquema v7 limpio, pero AppTest detecto dependencias directas a columnas
historicas:

- `modules/explotacion.py`: `localidad`, `carnet_fitosanitario`,
  `fecha_adquisicion`, `fecha_ultima_inspeccion`,
  `fecha_proxima_inspeccion`.
- `modules/cultivos.py`: `parcelas.municipio`, `cultivos.parcela_id`,
  `cultivos.especie`.
- `modules/parcelas.py`: `cultivos.parcela_id`, `cultivos.especie`.
- `modules/maquinaria.py`: `fecha_adquisicion`,
  `fecha_ultima_inspeccion`, `fecha_proxima_inspeccion`.

Durante v7.9 también se neutralizaron lecturas/escrituras relacionadas que
aparecian al revisar las pantallas:

- `parcelas.provincia`, `parcelas.municipio`, `superficie_cultivada`,
  `geometry`, `sigpac_geojson_actualizado`, `sigpac_geojson_estado` y
  `sigpac_geojson_error`;
- `maquinaria.nombre`, `maquinaria.fecha_compra` y `maquinaria.num_horas`;
- campos legacy separados de responsable y asesor de explotación.

## Cambios por módulo

### Explotación

`modules/explotacion.py` usa ahora lecturas y escrituras dinámicas según
`PRAGMA table_info`.

Mapeos principales:

- `localidad` visual lee/escribe `municipio` si existe;
- `codigo_regea` y `codigo_regepa` se mapean a `identificador_oficial`;
- `responsable_nombre` se mapea a `responsable`;
- `asesor_nombre` se mapea a `asesor`;
- `asesor_numero_registro` se mapea a `numero_asesor`;
- `carnet_fitosanitario` visual se mapea a `carnet_aplicador`;
- `fecha_ultima_inspeccion` se mapea a `fecha_revision`;
- `fecha_proxima_inspeccion` se mapea a `fecha_proxima_revision`.

Si una base antigua conserva columnas legacy, se siguen rellenando cuando
existen.

### Cultivos

`modules/cultivos.py` deja de depender de `cultivos.parcela_id` y
`cultivos.especie` para v7.

Cambios principales:

- `cultivos.nombre` es el nombre canónico cuando existe;
- `cultivos.especie` queda como fallback legacy;
- la relación cultivo-parcela usa `cultivo_parcelas`;
- `cultivos.parcela_id` solo se lee o escribe si existe;
- `parcelas.municipio` se sustituye por `municipio_sigpac` cuando no existe
  municipio textual;
- altas y ediciones de cultivo construyen `INSERT` y `UPDATE` con las columnas
  disponibles.

### Parcelas

`modules/parcelas.py` calcula cultivos asociados desde
`cultivo_parcelas -> cultivos` en v7.

Cambios principales:

- el listado de parcelas usa columnas opcionales;
- `provincia` y `municipio` se muestran desde columnas legacy si existen o
  desde codigos SIGPAC si no existen;
- los resumenes de cultivos asociados usan `cultivo_parcelas`;
- `cultivos.parcela_id` queda como fallback condicionado;
- la edición e insercion de parcelas solo escribe columnas existentes;
- el borrado seguro comprueba también `cultivo_parcelas.parcela_id`.

### Maquinaria

`modules/maquinaria.py` lee equipos de aplicación con alias compatibles.

Mapeos principales:

- `fecha_ultima_inspeccion` visual lee/escribe `fecha_revision`;
- `fecha_proxima_inspeccion` visual lee/escribe `fecha_proxima_revision`;
- `maquinaria.nombre` visual usa `descripcion` en v7 limpia;
- `fecha_compra` y `num_horas` solo se escriben si existen.

## Campos legacy neutralizados

No se han anadido columnas legacy a v7.

Quedan neutralizados por deteccion dinamica o alias:

- `explotacion.localidad`;
- `personas.carnet_fitosanitario`;
- `equipos_aplicacion.fecha_adquisicion`;
- `equipos_aplicacion.fecha_ultima_inspeccion`;
- `equipos_aplicacion.fecha_proxima_inspeccion`;
- `parcelas.municipio`;
- `parcelas.provincia`;
- `parcelas.superficie_cultivada`;
- `parcelas.geometry`;
- `parcelas.sigpac_geojson_actualizado`;
- `parcelas.sigpac_geojson_estado`;
- `parcelas.sigpac_geojson_error`;
- `cultivos.parcela_id`;
- `cultivos.especie`;
- `maquinaria.nombre`;
- `maquinaria.fecha_compra`;
- `maquinaria.num_horas`.

## Pruebas

Comandos ejecutados durante la validación de v7.9:

```bash
./venv/bin/python -m py_compile app.py
./venv/bin/python -m py_compile modules/explotacion.py
./venv/bin/python -m py_compile modules/cultivos.py
./venv/bin/python -m py_compile modules/parcelas.py
./venv/bin/python -m py_compile modules/maquinaria.py
./venv/bin/python -m py_compile scripts/probar_render_modulos_v7.py

./venv/bin/python scripts/crear_base_v7.py runtime/v7/prueba_render_v7.db
./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v7/prueba_render_v7.db
./venv/bin/python scripts/probar_render_modulos_v7.py
```

Resultado de diagnóstico:

- `PRAGMA user_version`: 7;
- número de tablas: 25;
- columnas faltantes: ninguna;
- columnas legacy prohibidas: ninguna;
- claves foraneas: sin errores;
- resultado: OK.

Resultado de `scripts/probar_render_modulos_v7.py`:

| Módulo | Resultado |
| --- | --- |
| Explotación | OK |
| Cultivos | OK |
| Parcelas | OK |
| Maquinaria | OK |

El script usa `streamlit.testing.v1.AppTest`, configura
`CUADERNOPRO_DB_PATH` contra `runtime/v7/prueba_render_v7.db` y prepara datos
mínimos dentro de `runtime/v7`.

## Pendiente

- Ejecutar prueba manual en navegador sobre base v7 limpia.
- Revisar otras pantallas maestras no incluidas en el alcance de v7.9:
  asistente inicial, mapas/SIGPAC y cualquier vista secundaria que aún use
  columnas historicas sin deteccion previa.
- Reducir progresivamente nombres visuales legacy cuando se disene la interfaz
  definitiva de v7.

## Recomendacion v7.10

El siguiente hito debería centrarse en una prueba completa de interfaz sobre
base v7 limpia:

- navegar manualmente todas las secciones principales;
- revisar formularios no cubiertos por AppTest;
- probar asistente inicial y mapas/SIGPAC;
- documentar cualquier deuda visual restante antes de preparar una instalación
  v7 nueva para uso real.
