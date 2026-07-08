# CuadernoPro v6: limpieza y normalización del modelo de datos

Esta carpeta documenta la planificación técnica para una fase v6 orientada a sanear el modelo de datos de CuadernoPro. No se ha modificado código ni base de datos en esta fase. Esta carpeta solo documenta el plan técnico.

## Problema a resolver

CuadernoPro funciona y ya cubre el cuaderno de explotación, pero el modelo ha crecido por fases. Algunas áreas quedaron bien estructuradas, mientras que otras conservan campos de texto o compatibilidad histórica que dificultan la exportación asistida SIEX/CUE y el mantenimiento futuro.

Los problemas principales son:

- `cultivos` no tiene `campana_id`.
- `cultivos` está unido directamente a una sola `parcela_id`, en vez de modelar cultivo-campaña con una tabla puente de parcelas.
- Fertilización, prácticas culturales y cosecha guardan `cultivo` como texto.
- La superficie del cultivo se infiere de parcelas o se repite en actuaciones.
- Hay campos y tablas de compatibilidad histórica que conviene revisar antes de seguir añadiendo capas.
- Los catálogos SIEX ya existen internamente, pero aún no se enlazan con cultivos, labores, unidades o actuaciones.

## Por qué no conviene seguir parcheando indefinidamente

Seguir añadiendo columnas puntuales permite avanzar rápido, pero aumenta el coste de cada módulo nuevo: revisión SIEX, exportador Excel, cuaderno oficial PDF, informes, validaciones y futuras pantallas deben compensar las mismas debilidades estructurales.

La v6 debería convertir el modelo de datos en una base estable para:

- campañas y cultivos por año agrícola;
- parcelas asociadas a cultivos de forma explícita;
- actuaciones agronómicas enlazadas a `cultivo_id`;
- códigos SIEX/CUE normalizados;
- exportación asistida más fiable;
- menos lógica defensiva en exportadores y revisiones.

## Qué significa modelo limpio v6

Un modelo limpio v6 significa:

- `cultivos` pasa a ser entidad central por campaña.
- Las parcelas de cada cultivo se guardan en `cultivo_parcelas`.
- Tratamientos, fertilizaciones, prácticas y cosechas referencian `cultivo_id`.
- Los textos visibles se siguen mostrando al usuario, pero la relación real se guarda por ID.
- Las unidades, labores y cultivos pueden vincularse a catálogos SIEX/CUE.
- Los documentos siguen inventariados, pero se valora una tabla documental genérica futura.

## Módulos afectados

- Cultivos.
- Parcelas.
- Tratamientos.
- Fertilización.
- Prácticas culturales.
- Cosecha.
- Revisión SIEX.
- Exportación Excel asistida SIEX.
- Cuaderno oficial PDF.
- Informes.
- Maquinaria, solo para aclarar maquinaria general frente a equipos de aplicación.

## Qué se mantiene igual

- Filosofía de CuadernoPro como herramienta local.
- Sin conexión directa a SIEX/CUE.
- Sin llamadas externas.
- Catálogos SIEX internos (`siex_catalogos`, `siex_catalogos_items`).
- Gestión de documentos PDF como anexos locales.
- Campañas como contexto principal del cuaderno.
- Tratamientos como área ya razonablemente estructurada.

## Qué se decidirá después

- Si v6 migra la base actual o arranca con base nueva.
- Si se añade una tabla documental genérica.
- Qué catálogos SIEX se aplican primero.
- Si se normalizan unidades con tabla propia o con catálogo interno simple.
- Cómo se migran datos reales ya existentes.
- Qué campos quedan como legacy y cuáles desaparecen en base nueva.

## Recomendación ejecutiva

Para una instalación pequeña o controlada, la opción más limpia para v6 es empezar con base nueva, cargar datos reales revisados y reimportar catálogos SIEX. La migración conservadora solo compensa si hay muchos datos históricos que no se pueden reintroducir manualmente con seguridad.
