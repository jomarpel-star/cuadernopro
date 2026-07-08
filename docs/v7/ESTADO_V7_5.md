# Estado v7.5 - Tratamientos limpios sobre esquema v7

## Resumen

La fase v7.5 prepara `modules/tratamientos.py` para trabajar con dos contextos:

- base v6 actual, con columnas legacy;
- base v7 limpia, sin `fecha`, `producto`, `aplicador`, `equipo`, `equipo_id`, `maquinaria_id` ni `problema` en `tratamientos`.

No se activa todavía v7 como base principal y no se modifica `core/db.py`.

## Modelo limpio

En v7, Tratamientos usa:

- `campana_id`
- `cultivo_id`
- `fecha_inicio`
- `fecha_fin`
- `producto_id`
- `aplicador_id`
- `equipo_aplicacion_id`
- `plaga_motivo`
- `dosis`
- `caldo`
- `superficie_tratada`
- `plazo_seguridad`
- `eficacia`
- `observaciones`

Las parcelas se guardan en `tratamiento_parcelas` y las recetas PDF en `tratamientos_documentos`.

## Compatibilidad v6

El módulo detecta las columnas reales de `tratamientos` antes de leer, insertar o actualizar.

En v6 mantiene compatibilidad con columnas existentes como:

- `fecha`
- `plaga`
- `problema`
- `justificacion`
- `aplicador`
- `equipo_id`
- `maquinaria_id`
- `fecha_recoleccion_segura`
- `condiciones`
- `condiciones_meteorologicas`

Estas columnas solo se consultan o escriben si existen. En una base v7 limpia no se intenta leer ni guardar columnas legacy.

## Selectores y resolucion de nombres

El alta mantiene los selectores seguros acordados en v6.11:

- cultivo estructurado;
- producto fitosanitario;
- aplicador;
- equipo de aplicación;
- parcelas;
- eficacia por defecto sin evaluar;
- receta PDF opcional.

El listado y la edición resuelven nombres desde:

- `cultivos`
- `productos_fito`
- `personas`
- `equipos_aplicacion`
- `tratamiento_parcelas`
- `tratamientos_documentos`

No se muestran IDs tecnicos al usuario.

## Recetas PDF y eficacia

Se mantienen:

- subir receta PDF en alta;
- ver y descargar recetas en edición;
- añadir recetas PDF en edición;
- eliminar recetas adjuntas;
- no duplicar recetas automáticamente;
- eficacia `Sin evaluar`, `B`, `R` o `M`.

La prueba v7 inserta una receta simulada en `tratamientos_documentos` sin crear PDF real.

## Script de prueba

Se crea:

`scripts/probar_tratamientos_v7.py`

La prueba usa exclusivamente:

`runtime/v7/cuadernopro_v7_limpia.db`

Valida:

- campana, parcela, cultivo y `cultivo_parcelas`;
- producto fitosanitario;
- persona/aplicador;
- equipo de aplicación;
- insercion de tratamiento con columnas limpias;
- insercion de `tratamiento_parcelas`;
- insercion de documento de receta simulado;
- lectura resolviendo campana, cultivo, parcelas, producto, aplicador, equipo y receta;
- ausencia de columnas legacy en `tratamientos`.

Resultado obtenido:

- tratamiento insertado en base v7 limpia;
- lectura campana/cultivo/parcelas/producto/aplicador/equipo/receta: OK;
- columnas legacy usadas: ninguna;
- resultado: OK.

## Diagnóstico v7

`scripts/diagnostico_schema_v7.py` muestra ahora bloques específicos:

- `Tratamientos limpios - columnas requeridas faltantes`;
- `Tratamientos limpios - legacy detectado`;
- `Tratamientos limpios - tabla tratamiento_parcelas`;
- `Tratamientos limpios - tabla tratamientos_documentos`.

Resultado obtenido:

- columnas requeridas faltantes: ninguna;
- legacy detectado: ninguno;
- tablas de parcelas y documentos: existen;
- resultado: OK.

## Seguridad

- No se toca `cuadernopro.db`.
- No se modifica `core/db.py`.
- No se eliminan columnas de v6.
- No se migra ningún dato real.
- No se modifica Docker ni instaladores.
- No se adapta todavía PDF oficial, exportador SIEX ni informes.

## Pendiente

- Probar manualmente Tratamientos v6 real: listado, alta, selectores, recetas PDF, eficacia, edición, duplicado y borrado.
- En v7.6 adaptar informes, PDF oficial y exportación SIEX para no depender de campos legacy.
