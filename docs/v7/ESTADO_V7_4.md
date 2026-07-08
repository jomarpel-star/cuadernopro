# Estado v7.4 - Contabilidad limpia sobre esquema v7

## Resumen

La fase v7.4 prepara `modules/contabilidad.py` para trabajar con dos contextos:

- base v6 actual, con columnas legacy;
- base v7 limpia, sin `tercero`, `nif_tercero` ni `cultivo` texto en `movimientos_economicos`.

No se activa todavía v7 como base principal y no se modifica `core/db.py`.

## Modelo limpio

En v7, Contabilidad usa:

- `campana_id`
- `cultivo_id`
- `cliente_id`
- `proveedor_id`
- `fecha`
- `tipo`
- `categoria`
- `concepto`
- `numero_factura`
- `base_imponible`
- `iva`
- `retencion`
- `total`
- `pendiente`
- `fecha_pago`
- `observaciones`

Los importes mantienen la lógica actual de base imponible, IVA, retención y total.

## Compatibilidad v6

El módulo detecta las columnas reales de `movimientos_economicos` antes de leer, insertar o actualizar.

En v6 mantiene compatibilidad con columnas existentes como:

- `tercero`
- `nif_tercero`
- `cultivo`
- `iva_porcentaje`
- `iva_importe`
- `forma_pago`
- `pagado`

Estas columnas solo se consultan o escriben si existen. En una base v7 limpia no se intenta leer ni guardar `tercero`, `nif_tercero` ni `cultivo` texto.

## Cliente, proveedor y cultivo

Los ingresos se estructuran con `cliente_id` y dejan `proveedor_id` a `NULL`.

Los gastos se estructuran con `proveedor_id` y dejan `cliente_id` a `NULL`.

El cultivo se asigna mediante selector estructurado y se guarda como `cultivo_id` cuando la columna existe. En v6 se rellena el texto legacy `cultivo` solo si la columna sigue existiendo.

El listado y pendientes resuelven nombres desde:

- `clientes`
- `proveedores`
- `cultivos`

Los textos legacy quedan solo como fallback v6 para registros antiguos.

## IVA y facturas

Se mantienen:

- `movimientos_economicos_lineas_iva`
- `movimientos_economicos_documentos`
- adjuntar facturas PDF desde la interfaz actual
- ver y descargar facturas en edición
- eliminar facturas adjuntas

La prueba v7 inserta facturas simuladas en la tabla de documentos sin crear PDF real.

## Script de prueba

Se crea:

`scripts/probar_contabilidad_v7.py`

La prueba usa exclusivamente:

`runtime/v7/cuadernopro_v7_limpia.db`

Valida:

- campana, cultivo, cliente y proveedor;
- insercion de un ingreso limpio con `cliente_id`;
- insercion de un gasto limpio con `proveedor_id`;
- insercion de lineas IVA;
- insercion de documentos de factura simulados;
- lectura resolviendo cliente/proveedor, NIF, cultivo, IVA y facturas;
- ausencia de columnas legacy en `movimientos_economicos`.

Resultado obtenido:

- ingreso insertado en base v7 limpia;
- gasto insertado en base v7 limpia;
- lectura cliente/proveedor/cultivo/IVA/facturas: OK;
- columnas legacy usadas: ninguna;
- resultado: OK.

## Diagnóstico v7

`scripts/diagnostico_schema_v7.py` muestra ahora bloques específicos:

- `Contabilidad limpia - columnas requeridas faltantes`;
- `Contabilidad limpia - legacy detectado`;
- `Contabilidad limpia - tabla movimientos_economicos_lineas_iva`;
- `Contabilidad limpia - tabla movimientos_economicos_documentos`.

Resultado obtenido:

- columnas requeridas faltantes: ninguna;
- legacy detectado: ninguno;
- tablas de IVA y documentos: existen;
- resultado: OK.

## Seguridad

- No se toca `cuadernopro.db`.
- No se modifica `core/db.py`.
- No se eliminan columnas de v6.
- No se migra ningún dato real.
- No se modifica Docker ni instaladores.
- No se adapta todavía PDF oficial, exportador SIEX ni informes.

## Pendiente

- Probar manualmente Contabilidad v6 real: listado, nuevo ingreso, nuevo gasto, desglose IVA, facturas PDF, pendientes, edición segura y borrado.
- En v7.5 preparar Tratamientos para el esquema limpio.
- En v7.6 adaptar informes, PDF oficial y exportación SIEX para no depender de campos legacy.
