# Estado v7.16 - Cosecha multi-cultivo y multi-parcela

## Objetivo

Permitir que una cosecha agrupe varios cultivos y varias parcelas o recintos
por cultivo, manteniendo la compatibilidad con cosechas v7 antiguas que solo
tenian `cosecha.cultivo_id`.

El caso agrícola cubierto es la agrupacion de cultivos por año de plantación,
por ejemplo `Almendro 2010`, `Almendro 2018` y `Almendro 2022`, cuando una
misma cosecha comercializada procede de varios grupos.

## Diseño elegido

Se crea la tabla puente `cosecha_cultivos`:

- `id`
- `cosecha_id`
- `cultivo_id`
- `parcela_id`
- `superficie`
- `observaciones`
- `created_at`
- `updated_at`

Relaciones:

- `cosecha_id -> cosecha.id` con borrado en cascada;
- `cultivo_id -> cultivos.id`;
- `parcela_id -> parcelas.id`.

La cabecera `cosecha.cultivo_id` se mantiene como compatibilidad y se rellena
con el primer cultivo seleccionado. La relación canonica v7.16 para cosechas
nuevas es `cosecha_cultivos`.

`cosecha_parcelas` se sigue rellenando con las parcelas seleccionadas para no
romper listados y consumidores anteriores.

## Módulos revisados

- `core/schema_v7.py`
- `core/db.py`
- `modules/cosecha.py`
- `modules/informes.py`
- `modules/revision_siex.py`
- `services/cuadernopro_pdf.py`
- `services/exportacion_siex.py`
- `scripts/probar_persistencia_editores_v7.py`
- `scripts/probar_pre_v8_v7_14.py`
- `scripts/probar_flujo_integral_v7.py`

## Cambios funcionales

En alta de cosecha:

- selector multiple de cultivos cosechados;
- selector de parcelas por cada cultivo seleccionado;
- seleccion por defecto de todas las parcelas asociadas al cultivo;
- cálculo de superficie total desde las parcelas seleccionadas;
- ajuste manual de superficie total, repartido proporcionalmente por detalle;
- guardado de cabecera en `cosecha`;
- guardado de detalle en `cosecha_cultivos`;
- mantenimiento de `cosecha_parcelas` como compatibilidad.

En listado/editor:

- se muestran cultivos agregados desde `cosecha_cultivos` si existen;
- se muestran parcelas agregadas desde el detalle;
- se muestra superficie agregada;
- el editor permite modificar datos generales y conserva el detalle
  multi-cultivo.

En borrado:

- el borrado seguro limpia `cosecha_cultivos` y `cosecha_parcelas`.

## Informes, PDF y SIEX

- Informes y PDF consumen la lectura agregada de cosecha, por lo que muestran
  cultivos y parcelas del detalle v7.16.
- La sección oficial de cosecha del PDF usa el texto agregado de parcelas
  antes de recurrir a `cosecha_parcelas`.
- La revisión SIEX reconoce `cosecha_cultivos` como cultivo estructurado.
- El Excel SIEX genera una fila por detalle cultivo/parcela cuando existe
  `cosecha_cultivos`; la cantidad queda como cantidad total de cabecera, no
  se reparte automáticamente por superficie.

## Compatibilidad

- Las cosechas antiguas sin `cosecha_cultivos` siguen leyendose mediante
  `cosecha.cultivo_id` y `cosecha_parcelas`.
- Las bases v7 existentes reciben la ampliacion idempotente
  `asegurar_ampliaciones_v7_16(conn)`.
- No se modifica el modelo de datos legacy ni se convierte automáticamente una
  base v6.

## Pruebas realizadas

- Compilacion:
  - `./venv/bin/python -m py_compile app.py core/db.py core/schema_v7.py modules/cosecha.py modules/informes.py modules/revision_siex.py services/cuadernopro_pdf.py services/exportacion_siex.py scripts/probar_cosecha_multicultivo_v7.py scripts/probar_persistencia_editores_v7.py scripts/probar_pre_v8_v7_14.py scripts/probar_flujo_integral_v7.py`: OK.
- `./venv/bin/python scripts/probar_cosecha_multicultivo_v7.py`: OK.
  - tabla puente: OK;
  - listado e informes: OK;
  - revisión SIEX: OK, 9 registros revisados;
  - Excel SIEX: OK, 14172 bytes;
  - PDF oficial: OK, 19770 bytes.
- `./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v7/prueba_cosecha_multicultivo_v7.db`: OK, 26 tablas.
- `./venv/bin/python scripts/probar_pre_v8_v7_14.py`: OK, 26 tablas, Excel SIEX OK, PDF oficial OK.
- `./venv/bin/python scripts/probar_persistencia_editores_v7.py`: OK, cosecha valida `cosecha_parcelas` y `cosecha_cultivos`.
- `./venv/bin/python scripts/probar_schema_v7_13.py`: OK.
- `./venv/bin/python scripts/probar_listados_v7.py`: OK.
- `./venv/bin/python scripts/auditar_tablas_visuales_v7.py`: OK, 48 llamadas, 0 advertencias.
- `./venv/bin/python scripts/probar_render_modulos_v7.py`: OK.
- `./venv/bin/python scripts/probar_editores_auxiliares_v7.py`: OK.
- `./venv/bin/python scripts/probar_flujo_integral_v7.py`: OK, 26 tablas, Excel SIEX OK, PDF oficial OK.

## Prueba manual

Preparada:

- base creada: `runtime/v7/prueba_manual_v7_16.db`;
- servidor arrancado en `http://192.168.0.13:8517`;
- PID guardado en `runtime/v7/streamlit_v7_16.pid`;
- PID real verificado: `129971`.

Pendiente de completar en esta misma preparación:

- comprobacion manual en navegador de alta de varios cultivos, seleccion de
  parcelas por cultivo, listado, edición general, PDF, revisión SIEX y Excel.

## Pendientes para v8.0

- Decidir si el editor debe permitir cambiar cultivos y parcelas de una
  cosecha multi-cultivo de forma transaccional.
- Definir si SIEX debe repartir cantidad por superficie o mantener cantidad
  total en cada fila de detalle asistido.
- Normalizar unidades, destinos y productos de cosecha si se cierra un modelo
  SIEX más estricto.
