# Estado v7.2 - Cosecha limpia sobre esquema v7

## Resumen

La fase v7.2 prepara `modules/cosecha.py` para trabajar con dos contextos:

- base v6 actual, con columnas legacy;
- base v7 limpia, sin `cultivo`, `cliente`, `nif_cliente` ni `kg`.

No se activa todavía v7 como base principal y no se modifica `core/db.py`.

## Cambios tecnicos

- El módulo Cosecha detecta las columnas reales de la tabla `cosecha` con `PRAGMA table_info`.
- Los `INSERT` y `UPDATE` de Cosecha solo escriben columnas existentes.
- La lectura del listado construye SQL compatible según el esquema disponible.
- En v7, Cosecha usa `campana_id`, `cultivo_id`, `cliente_id`, `cantidad`, `unidad`, `destino` y `observaciones`.
- En v6, si existen columnas legacy, se siguen rellenando internamente por compatibilidad.
- Los nombres visibles de cultivo y cliente se resuelven desde `cultivos` y `clientes`.
- Los campos manuales de cultivo/cliente legacy solo aparecen si existen las columnas legacy.

## Columnas limpias usadas en v7

La tabla `cosecha` del esquema v7 mantiene:

- `id`
- `campana_id`
- `cultivo_id`
- `fecha`
- `cantidad`
- `unidad`
- `destino`
- `cliente_id`
- `observaciones`
- `created_at`
- `updated_at`

## Columnas legacy no usadas en v7

El diagnóstico marca error si aparecen:

- `cosecha.cultivo`
- `cosecha.cliente`
- `cosecha.nif_cliente`
- `cosecha.kg`

## Script de prueba

Se crea:

`scripts/probar_cosecha_v7.py`

La prueba usa exclusivamente:

`runtime/v7/cuadernopro_v7_limpia.db`

Pasos que valida:

- crea campana, cliente, parcela, cultivo y `cultivo_parcelas`;
- inserta una cosecha con el helper compatible;
- lee la cosecha resolviendo campana, cultivo y cliente;
- confirma que no existen columnas legacy en `cosecha`;
- confirma que no se usan columnas legacy para insertar.

Resultado obtenido:

- cosecha insertada en base v7 limpia;
- lectura campana/cultivo/cliente: OK;
- columnas legacy usadas: ninguna;
- resultado: OK.

## Diagnóstico v7

`scripts/diagnostico_schema_v7.py` muestra ahora un bloque especifico:

- `Cosecha limpia - columnas requeridas faltantes`;
- `Cosecha limpia - legacy detectado`.

Resultado obtenido:

- columnas requeridas faltantes: ninguna;
- legacy detectado: ninguno;
- resultado: OK.

## Seguridad

- No se toca `cuadernopro.db`.
- No se modifica `core/db.py`.
- No se eliminan columnas de v6.
- No se migra ningún dato real.
- No se modifica Docker ni instaladores.
- No se adapta todavía PDF oficial, exportador SIEX ni informes.

## Pendiente

- Probar manualmente alta, listado y edición de Cosecha en la app v6 real.
- En fases posteriores, adaptar informes, PDF y exportación SIEX para leer Cosecha limpia sin legacy.
- Integrar el esquema v7 en el flujo de instalación nueva cuando el resto de módulos este preparado.
