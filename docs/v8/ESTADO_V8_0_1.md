# Estado v8.0.1

## Objetivo del parche

Extender el criterio multicultivo/multiparcela ya aplicado en Cosecha a:

- Tratamientos
- Fertilización
- Prácticas culturales

Versión preparada: `v8.0.1 - Multicultivo en tratamientos, fertilizacion y practicas`.

## Motivo agrícola

Una explotación puede tener varios cultivos del mismo producto separados por
año de plantación, por ejemplo:

- Almendro 2010
- Almendro 2018
- Almendro 2022

Una misma actuacion agrícola puede afectar a varios de esos cultivos y, dentro
de cada cultivo, a una o varias parcelas.

## Diseño elegido

- Se mantiene la cabecera existente de cada actuacion.
- `cultivo_id` sigue guardando el primer cultivo seleccionado como
  compatibilidad.
- Se añade una tabla puente por módulo con detalle `cultivo_id` +
  `parcela_id`.
- Las tablas antiguas de parcelas se siguen rellenando para consumidores
  anteriores.
- Las lecturas nuevas prefieren la tabla puente multicultivo.
- Si no hay detalle en la tabla nueva, se usa fallback a `cultivo_id` y la
  tabla antigua de parcelas.

Internamente el esquema sigue llamandose v7 porque es la base limpia consolidada
que usa CuadernoPro v8. La ampliacion v8.0.1 es idempotente y no convierte bases
v6 legacy automáticamente.

## Tablas anadidas

- `tratamiento_cultivos`
- `fertilizacion_cultivos`
- `practicas_culturales_cultivos`

Campos principales:

- `id`
- campo de cabecera (`tratamiento_id`, `fertilizacion_id` o `practica_id`)
- `cultivo_id`
- `parcela_id`
- `superficie`
- `observaciones`
- `created_at`
- `updated_at`

## Compatibilidad

- Registros antiguos con un solo cultivo siguen funcionando.
- `tratamientos.cultivo_id`, `fertilizaciones.cultivo_id` y
  `practicas_culturales.cultivo_id` no se eliminan.
- `tratamiento_parcelas`, `fertilizacion_parcelas` y
  `practicas_culturales_parcelas` siguen rellenandose.
- Informes, PDF, revisión SIEX y Excel SIEX usan detalle nuevo si existe y
  fallback si no existe.

## Módulos modificados

- `core/schema_v7.py`
- `core/db.py`
- `core/actuaciones_multicultivo.py`
- `modules/tratamientos.py`
- `modules/fertilizacion.py`
- `modules/practicas_culturales.py`
- `modules/informes.py`
- `modules/revision_siex.py`
- `services/cuadernopro_pdf.py`
- `services/exportacion_siex.py`
- `scripts/diagnostico_schema_v7.py`
- `scripts/probar_actuaciones_multicultivo_v8.py`
- `scripts/probar_release_v8.py`
- scripts de prueba v7 que aseguran esquema limpio o flujo integral

## Pruebas realizadas

Ejecutado:

```bash
./venv/bin/python -m py_compile app.py core/db.py core/schema_v7.py core/actuaciones_multicultivo.py modules/tratamientos.py modules/fertilizacion.py modules/practicas_culturales.py modules/informes.py modules/revision_siex.py services/cuadernopro_pdf.py services/exportacion_siex.py scripts/probar_actuaciones_multicultivo_v8.py
./venv/bin/python scripts/probar_actuaciones_multicultivo_v8.py
./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v8/prueba_actuaciones_multicultivo_v8.db
./venv/bin/python scripts/probar_release_v8.py
./venv/bin/python scripts/probar_cosecha_multicultivo_v7.py
./venv/bin/python scripts/probar_cultivos_arboles_v7.py
./venv/bin/python scripts/probar_persistencia_editores_v7.py
./venv/bin/python scripts/probar_listados_v7.py
./venv/bin/python scripts/auditar_tablas_visuales_v7.py
./venv/bin/python scripts/probar_render_modulos_v7.py
./venv/bin/python scripts/probar_editores_auxiliares_v7.py
./venv/bin/python scripts/probar_flujo_integral_v7.py
git diff --check
```

Resultado especifico:

- tablas puente: OK
- compatibilidad con tablas antiguas de parcelas: OK
- listados e informes: OK
- revisión SIEX: OK
- Excel SIEX: OK, filas por detalle cultivo/parcela
- PDF oficial: OK
- edición de datos generales sin borrar detalle: OK
- borrado con limpieza de detalle: OK
- fallback antiguo de cultivo unico sin detalle: OK
- bateria automatizada v8.0.1: OK
- base manual creada: `runtime/v8/prueba_manual_v8_0_1.db`
- Streamlit para prueba manual: `http://192.168.0.13:8518`

## Pendientes

- Completar comprobacion visual en navegador con la base limpia manual.
- El puerto solicitado `8517` estaba ocupado; se uso `8518`.
- No se ha hecho commit.
- No se ha tocado Docker, instaladores ni `cuadernopro.db` real.
