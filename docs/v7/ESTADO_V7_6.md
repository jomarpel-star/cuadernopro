# Estado v7.6 - Informes, PDF oficial y Excel SIEX limpios

## Resumen

La fase v7.6 prepara las salidas principales de CuadernoPro para leer una base
v7 limpia sin depender de columnas legacy.

Se adaptan:

- `modules/informes.py`
- `modules/revision_siex.py`
- `services/cuadernopro_pdf.py`
- `services/exportacion_siex.py`
- `scripts/diagnostico_schema_v7.py`

No se activa v7 como base principal y no se modifica `core/db.py`.

## Resolucion limpia de datos

Las salidas resuelven datos desde relaciones estructuradas:

- cosecha: `campana_id`, `cultivo_id`, `cliente_id`, `cantidad`, `unidad`;
- fertilización: `campana_id`, `cultivo_id`, `fertilizacion_parcelas`;
- prácticas culturales: `campana_id`, `cultivo_id`, `maquinaria_id`,
  `proveedor_id`, `practicas_culturales_parcelas`;
- contabilidad: `cliente_id`, `proveedor_id`, `cultivo_id`, lineas IVA y
  documentos;
- tratamientos: `cultivo_id`, `producto_id`, `aplicador_id`,
  `equipo_aplicacion_id`, `tratamiento_parcelas` y `tratamientos_documentos`.

Los textos legacy se mantienen solo como fallback v6 si la columna existe.

## Informes

`modules/informes.py` usa los lectores compatibles creados en fases v7.2-v7.5.
El informe mantiene las columnas de presentacion que espera la interfaz, pero
los valores se resuelven desde IDs y tablas puente.

Se evita consultar directamente columnas como:

- `cosecha.kg`
- `cosecha.cliente`
- `movimientos_economicos.tercero`
- `fertilizaciones.cultivo`
- `practicas_culturales.cultivo`
- `tratamientos.fecha`

## PDF oficial

`services/cuadernopro_pdf.py` mantiene el diseño y la estructura del cuaderno,
pero las secciones principales usan lecturas compatibles con v6/v7:

- tratamientos y recetas;
- fertilizaciones;
- prácticas culturales;
- cosecha;
- movimientos económicos y facturas;
- parcelas y cultivos asociados.

Las recetas y facturas PDF siguen siendo anexos documentales. En la prueba v7
se usan documentos simulados para validar el recorrido sin tocar documentos
reales.

## Excel asistido SIEX

`services/exportacion_siex.py` resuelve:

- cultivo desde `cultivo_id` y `cultivo_parcelas`;
- producto fitosanitario desde `productos_fito.numero_registro`;
- cosecha desde `cantidad` y `unidad`;
- cliente/proveedor desde tablas maestras;
- prácticas desde `practicas_culturales_parcelas`;
- documentos desde tablas documentales limpias.

## Revisión SIEX

`modules/revision_siex.py` reconoce nombres limpios de v7:

- `cultivos.nombre`;
- `productos_fito.numero_registro`;
- `cosecha.cantidad`.

La revisión mantiene el criterio prudente de avisos y no convierte estas
comprobaciones en bloqueos duros.

## Script de prueba

Se crea:

`scripts/probar_salidas_v7.py`

La prueba:

- regenera `runtime/v7/cuadernopro_v7_limpia.db`;
- inserta datos mínimos completos;
- valida ausencia de columnas legacy prohibidas;
- ejecuta carga de datos de Informes;
- genera Excel asistido SIEX en memoria;
- genera PDF oficial en `runtime/v7/exports` usando la base v7 aislada.

## Diagnóstico v7

`scripts/diagnostico_schema_v7.py` incorpora un bloque de salidas v7 para
comprobar tablas y columnas requeridas por Informes, PDF y Excel SIEX:

- tablas puente;
- tablas documentales;
- maestros de cultivos, clientes, proveedores, productos, personas y equipos.

## Seguridad

- No se toca `cuadernopro.db`.
- No se modifica `core/db.py`.
- No se eliminan columnas de v6.
- No se migra ningún dato real.
- No se modifica Docker ni instaladores.
- v7 sigue aislado en `runtime/v7`.

## Resultado esperado de validación

Comandos previstos:

- `py_compile` de Informes, Revisión SIEX, PDF, Excel SIEX, prueba y diagnóstico;
- creacion de base v7 limpia;
- diagnóstico v7 OK;
- prueba `scripts/probar_salidas_v7.py` OK;
- `py_compile app.py`;
- `git diff --check`.

## Pendiente

- Prueba manual v6 real en la aplicación: Informes, PDF oficial, Revisión SIEX y
  descarga de Excel asistido.
- v7.7 debería centrarse en instalación limpia y flujo de primera configuración.
