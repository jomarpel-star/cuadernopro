# CuadernoPro v7: base limpia sin legacy

Esta carpeta define la preparación técnica de CuadernoPro v7. En esta fase no se modifica código funcional, no se modifica la base de datos y no se eliminan columnas. El objetivo es dejar documentado que debe cambiar antes de crear una base nueva limpia.

## Por qué se crea v7

La fase v6 dejó la aplicación en un punto estable: los formularios principales ya trabajan con referencias estructuradas y ocultan buena parte de los campos históricos. Aun así, el esquema físico conserva columnas duplicadas o legacy para no romper datos anteriores.

v7 se plantea como una versión limpia para instalaciones nuevas, sin arrastrar compatibilidad histórica cuando ya existe una relación estructurada.

## Qué problema resuelve

El problema principal no es visual, sino de modelo de datos:

- varios módulos guardan `cultivo_id` y también `cultivo` textual;
- contabilidad guarda `cliente_id`/`proveedor_id` y también `tercero`/`nif_tercero`;
- cosecha guarda cliente y NIF como texto y no tiene todavía `cliente_id`;
- tratamientos mantiene `fecha` junto a `fecha_inicio`/`fecha_fin`, `problema` junto a `plaga`, `aplicador` junto a `aplicador_id`, y varias columnas para equipo;
- exportadores, informes y PDF todavía leen algunos textos legacy como fallback.

## Diferencia entre v6 y v7

v6 es una versión de transición compatible con bases existentes. Mantiene columnas antiguas y escribe algunos textos duplicados para que los datos históricos sigan siendo visibles.

v7 debe estar pensada para bases nuevas. No debe garantizar una migración automática desde datos ambiguos de v6. La versión v6 queda como referencia estable compatible con datos anteriores.

## Qué significa base limpia

Una base limpia v7 significa:

- relaciones reales por ID cuando exista una entidad maestra;
- tablas puente para relaciones N:M;
- textos derivados calculados desde IDs, no persistidos como duplicados;
- sin campos legacy usados como fuente principal;
- exportaciones, informes y PDF resolviendo nombres desde las relaciones estructuradas;
- datos nuevos obligatoriamente estructurados cuando el módulo lo requiere.

## Que se conserva

- `campanas` como contexto principal.
- `parcelas` y datos SIGPAC.
- `cultivos` como entidad central por campaña.
- `cultivo_parcelas`.
- `clientes`, `proveedores`, `personas`, `productos_fito`, `maquinaria`, `equipos_aplicacion`.
- tablas puente de parcelas por actuacion.
- documentos PDF adjuntos de recetas y facturas.
- `siex_catalogos` y `siex_catalogos_items`.

## Que se elimina o revisa

- columnas textuales que duplican relaciones estructuradas;
- columnas antiguas mantenidas solo para compatibilidad;
- referencias a `cultivos.parcela_id` cuando ya existe `cultivo_parcelas`;
- cantidad de cosecha como `kg` implicito si se adopta `cantidad` + `unidad`;
- fallbacks de exportadores e informes que agrupen por textos antiguos;
- IDs tecnicos visibles en pantallas de usuario.

## Módulos afectados

- Cultivos.
- Parcelas.
- Tratamientos fitosanitarios.
- Fertilización.
- Prácticas culturales.
- Cosecha.
- Contabilidad.
- Maquinaria y equipos de aplicación.
- Informes.
- Cuaderno oficial PDF.
- Exportación asistida SIEX.
- Revisión SIEX.

## Criterio inicial

v7 está pensada para instalaciones nuevas o para usuarios que acepten cargar sus datos de nuevo sobre un modelo limpio. La versión v6 queda como referencia estable compatible con datos anteriores.
