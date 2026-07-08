# Estado v7.3 - Fertilización y prácticas limpias sobre esquema v7

## Resumen

La fase v7.3 prepara `modules/fertilizacion.py` y `modules/practicas_culturales.py` para trabajar con dos contextos:

- base v6 actual, con columnas legacy;
- base v7 limpia, sin `fertilizaciones.cultivo` ni `practicas_culturales.cultivo`.

No se activa todavía v7 como base principal y no se modifica `core/db.py`.

## Fertilización

El módulo detecta las columnas reales de `fertilizaciones` antes de leer, insertar o actualizar.

En v7 usa:

- `campana_id`
- `cultivo_id`
- `fecha`
- `producto`
- `tipo_fertilizante`
- `cantidad`
- `unidad`
- `unidad_normalizada`
- `superficie`
- `codigo_actuacion_siex`
- `observaciones`

En v6 mantiene compatibilidad con columnas existentes como:

- `cultivo`
- `tipo`
- `riqueza_npk`
- `metodo_aplicacion`
- `operario_id`

Las parcelas se guardan en `fertilizacion_parcelas` si la tabla existe.

## Prácticas culturales

El módulo detecta las columnas reales de `practicas_culturales` antes de leer, insertar o actualizar.

En v7 usa:

- `campana_id`
- `cultivo_id`
- `fecha`
- `labor`
- `codigo_actuacion_siex`
- `superficie`
- `maquinaria_id`
- `proveedor_id`
- `observaciones`

En v6 mantiene compatibilidad con columnas existentes como:

- `cultivo`
- `operario_id`

Las parcelas se guardan en la tabla puente disponible:

- `practicas_culturales_parcelas` en v7;
- `practica_parcelas` en v6.

La maquinaria se resuelve de forma compatible aunque el esquema v7 no tenga `maquinaria.nombre`.

## Script de prueba

Se crea:

`scripts/probar_fertilizacion_practicas_v7.py`

La prueba usa exclusivamente:

`runtime/v7/cuadernopro_v7_limpia.db`

Valida:

- campana, parcela, cultivo y `cultivo_parcelas`;
- proveedor y maquinaria;
- insercion de fertilización con columnas limpias;
- insercion de relación en `fertilizacion_parcelas`;
- lectura de fertilización resolviendo campana, cultivo y parcelas;
- insercion de practica cultural con columnas limpias;
- insercion de relación en `practicas_culturales_parcelas`;
- lectura de practica resolviendo campana, cultivo, parcelas, maquinaria y proveedor;
- ausencia de uso de columnas legacy.

Resultado obtenido:

- fertilización insertada en base v7 limpia;
- practica cultural insertada en base v7 limpia;
- lectura campana/cultivo/parcelas/maquinaria/proveedor: OK;
- columnas legacy usadas: ninguna;
- resultado: OK.

## Diagnóstico v7

`scripts/diagnostico_schema_v7.py` muestra ahora bloques específicos:

- `Fertilizacion limpia - columnas requeridas faltantes`;
- `Fertilizacion limpia - legacy detectado`;
- `Fertilizacion limpia - tabla fertilizacion_parcelas`;
- `Practicas limpias - columnas requeridas faltantes`;
- `Practicas limpias - legacy detectado`;
- `Practicas limpias - tabla practicas_culturales_parcelas`.

Resultado obtenido:

- columnas requeridas faltantes: ninguna;
- legacy detectado: ninguno;
- tablas puente requeridas: existen;
- resultado: OK.

## Seguridad

- No se toca `cuadernopro.db`.
- No se modifica `core/db.py`.
- No se eliminan columnas de v6.
- No se migra ningún dato real.
- No se modifica Docker ni instaladores.
- No se adapta todavía PDF oficial, exportador SIEX ni informes.

## Pendiente

- Probar manualmente listado, alta, edición y duplicado en Fertilización v6 real.
- Probar manualmente listado, alta, edición, duplicado y maquinaria/prestador en Prácticas culturales v6 real.
- En fases posteriores, adaptar informes, PDF y exportación SIEX para no depender de legacy.
