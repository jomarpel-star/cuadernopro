# Compatibilidad v6 / v7

Este documento compara las opciones para pasar de CuadernoPro v6 a v7.

## Punto de partida

v6 es estable y mantiene compatibilidad con datos históricos. Sus formularios ya favorecen referencias estructuradas, pero la base conserva columnas legacy y muchos consumidores siguen leyendo fallbacks.

v7 busca una base limpia para instalaciones nuevas. No debe bloquearse por una migración automática de datos ambiguos.

## Opción A: migración automática

### Ventajas

- Conserva datos existentes.
- Reduce trabajo manual inicial.
- Mantiene historico operativo dentro de la misma base.
- Puede ser útil si hay muchas campañas ya cargadas.

### Inconvenientes

- Riesgo de relaciones ambiguas entre textos antiguos y IDs.
- `cultivo` textual puede coincidir con varios cultivos/campañas.
- `cliente` y `nif_cliente` de cosecha no garantizan una relación unica con `clientes`.
- `tercero` y `nif_tercero` pueden no coincidir con `cliente_id` o `proveedor_id`.
- Documentos PDF asociados requieren conservar rutas y relaciones.
- Se puede arrastrar basura histórica a la versión limpia.
- Obliga a mantener código de migración, diagnóstico y rollback.

### Cuando tendria sentido

- Instalaciones con mucho historico que no se puede recargar manualmente.
- Necesidad de continuidad exacta de IDs.
- Documentos adjuntos numerosos y críticos.
- Usuario dispuesto a revisar manualmente conflictos detectados por un asistente de migración.

## Opción B: base nueva limpia

### Ventajas

- Esquema claro desde el primer arranque.
- Menos riesgo técnico.
- Ideal para producto y usuarios nuevos.
- Facilita pruebas automatizadas y manuales.
- Evita arrastrar textos contradictorios.
- Hace más fiable el PDF, informes y exportación SIEX.
- Permite cargar solo datos reales revisados.

### Inconvenientes

- Hay que recargar datos.
- Requiere conservar backup de v6 como archivo de consulta.
- Puede requerir reimportar catálogos SIEX.
- Los documentos asociados deben revisarse o volver a adjuntarse si se quieren en v7.

### Cuando es preferible

- Instalaciones nuevas.
- Usuarios que aceptan cargar datos de nuevo.
- Fase de producto donde interesa eliminar deuda histórica.
- Bases v6 con pocos datos reales o datos faciles de revisar.

## Recomendacion inicial

Para CuadernoPro v7, priorizar base nueva limpia.

La migración automática desde v6 puede estudiarse más adelante, pero no debe bloquear el saneamiento. Si se implementa, debería ser opcional, asistida, con diagnóstico de conflictos y sin modificar la base v6 original.

## Estrategia practica

1. Conservar v6 como respaldo estable.
2. Generar backup de base v6 y carpeta `documentos/`.
3. Crear base v7 vacía.
4. Cargar datos maestros revisados.
5. Cargar cultivos por campaña con `cultivo_parcelas`.
6. Cargar actuaciones reales ya estructuradas.
7. Validar PDF, informes y exportación SIEX.
8. Mantener v6 solo como archivo historico si no se migran todos los datos.

## Regla de seguridad

Nunca debe ejecutarse una migración destructiva sobre la base v6 sin backup y confirmacion explicita. v7 debe poder nacer sin depender de una base v6 previa.
