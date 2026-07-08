# Modelo de datos objetivo para CuadernoPro v6

Este documento propone el modelo limpio objetivo para CuadernoPro v6. Es una propuesta técnica, no una migración aplicada.

## Principios

- `campanas`, `parcelas` y `cultivos` deben formar el núcleo agronómico.
- `cultivos` debe representar un cultivo de una campaña concreta.
- Las actuaciones deben apuntar a `cultivo_id` y, si procede, a parcelas concretas mediante tablas puente.
- Los catálogos SIEX/CUE se consultan localmente y solo se usan para normalizar datos.
- Los textos descriptivos pueden mantenerse como campos calculados o auxiliares, pero no deben ser la relación principal.

## A) Explotación

Entidad: `explotacion`.

Campos objetivo:

- `id`
- `nombre_explotacion`
- `titular`
- `nif`
- `direccion`
- `localidad`
- `codigo_postal`
- `provincia`
- `telefono`
- `email`
- `registro_explotacion`
- `codigo_regea`
- `codigo_regepa`
- `tipo_explotacion`
- `orientacion_productiva`
- `responsable_nombre`
- `responsable_nif`
- `responsable_telefono`
- `asesor_nombre`
- `asesor_nif`
- `asesor_numero_registro`
- `asesor_telefono`
- `observaciones`

Comentario: el modelo actual es suficiente como base. Para v6 conviene decidir si responsable y asesor se mantienen embebidos o se enlazan a `personas`.

## B) Campañas

Entidad: `campanas`.

Campos objetivo:

- `id`
- `nombre`
- `fecha_inicio`
- `fecha_fin`
- `activa`
- `estado`
- `observaciones`

Comentario: hoy `campanas` ya existe con `nombre`, fechas y `activa`. `estado` puede ayudar a distinguir borrador, activa, cerrada o archivada.

## C) Parcelas

Entidad: `parcelas`.

Campos objetivo:

- `id`
- `nombre`
- `provincia`
- `municipio`
- `provincia_sigpac`
- `municipio_sigpac`
- `agregado_sigpac`
- `zona_sigpac`
- `poligono`
- `parcela`
- `recinto`
- `superficie_sigpac`
- `superficie_cultivada`
- `geometry`
- `sigpac_geojson`
- `sigpac_geojson_actualizado`
- `sigpac_geojson_estado`
- `sigpac_geojson_error`
- `activa`
- `observaciones`

Comentario: parcelas está razonablemente bien resuelta. Falta estado activo/inactivo y confirmar si `geometry` y `sigpac_geojson` deben convivir.

## D) Cultivos

Entidad central: `cultivos`.

Campos objetivo:

- `id`
- `campana_id`
- `nombre`
- `variedad`
- `codigo_siex`
- `superficie`
- `ano_plantacion`
- `marco`
- `arboles`
- `sistema`
- `sistema_cultivo_siex`
- `sistema_conduccion_siex`
- `observaciones`
- `activo`

Tabla puente: `cultivo_parcelas`.

Campos objetivo:

- `id`
- `cultivo_id`
- `parcela_id`
- `superficie`
- `observaciones`

Relaciones:

- `cultivos.campana_id -> campanas.id`
- `cultivo_parcelas.cultivo_id -> cultivos.id`
- `cultivo_parcelas.parcela_id -> parcelas.id`
- `tratamientos.cultivo_id -> cultivos.id`
- `fertilizaciones.cultivo_id -> cultivos.id`
- `practicas_culturales.cultivo_id -> cultivos.id`
- `cosecha.cultivo_id -> cultivos.id`

Comentario: este es el cambio principal de v6. El campo actual `cultivos.parcela_id` debe desaparecer en base nueva o quedar solo como legacy durante una migración conservadora.

## E) Tratamientos

Entidad: `tratamientos`.

Campos objetivo:

- `id`
- `campana_id`
- `cultivo_id`
- `fecha_inicio`
- `fecha_fin`
- `producto_id`
- `problema`
- `plaga`
- `justificacion`
- `dosis`
- `caldo`
- `superficie_tratada`
- `aplicador_id`
- `equipo_aplicacion_id`
- `eficacia`
- `plazo_seguridad`
- `fecha_recoleccion_segura`
- `condiciones`
- `condiciones_meteorologicas`
- `observaciones`

Tablas relacionadas:

- `tratamiento_parcelas`
- `tratamientos_documentos`
- `productos_fito`
- `personas`
- `equipos_aplicacion`

Comentario: tratamientos está bien encaminado porque ya usa `cultivo_id`, `campana_id`, producto estructurado y tabla puente de parcelas. En v6 conviene retirar o unificar campos legacy como `fecha`, `aplicador`, `maquinaria_id`, `equipo_id` si ya no se necesitan.

## F) Fertilización

Entidad: `fertilizaciones`.

Campos objetivo:

- `id`
- `campana_id`
- `cultivo_id`
- `fecha`
- `producto`
- `tipo`
- `riqueza_npk`
- `cantidad`
- `unidad`
- `unidad_normalizada`
- `metodo_aplicacion`
- `superficie`
- `operario_id`
- `codigo_actuacion_siex`
- `observaciones`

Tabla relacionada:

- `fertilizacion_parcelas`

Comentario: actualmente `fertilizaciones.cultivo` es texto. En v6 debe ser `cultivo_id`. Puede mantenerse un campo textual temporal solo durante migración.

## G) Prácticas culturales

Entidad: `practicas_culturales`.

Campos objetivo:

- `id`
- `campana_id`
- `cultivo_id`
- `fecha`
- `labor`
- `codigo_actuacion_siex`
- `superficie`
- `maquinaria_id`
- `operario_id`
- `proveedor_id`
- `observaciones`

Tabla relacionada:

- `practica_parcelas`

Comentario: actualmente `practicas_culturales.cultivo` es texto. Las labores son una lista interna en el módulo; en v6 deberían poder mapearse a catálogo/actuación normalizada.

## H) Cosecha

Entidad: `cosecha`.

Campos objetivo:

- `id`
- `campana_id`
- `cultivo_id`
- `fecha`
- `producto`
- `cantidad`
- `unidad`
- `precio_unitario`
- `lote`
- `cliente_id`
- `cliente_texto`
- `nif_cliente`
- `albaran`
- `factura`
- `destino`
- `destino_normalizado`
- `observaciones`

Tabla relacionada:

- `cosecha_parcelas`

Comentario: actualmente la cantidad está en `kg` y el cultivo en texto. Para v6 conviene usar `cantidad` + `unidad`, con `kg` como migración o vista de compatibilidad si se conserva la base actual.

## I) Maquinaria

Entidades:

- `maquinaria` para maquinaria general (`MAQ-*`).
- `equipos_aplicacion` para equipos fitosanitarios (`EQ-*`).

Campos de maquinaria general:

- `id`
- `nombre`
- `tipo`
- `marca`
- `modelo`
- `numero_roma`
- `matricula`
- `fecha_compra`
- `num_horas`
- `observaciones`

Campos de equipos de aplicación:

- `id`
- `nombre`
- `tipo`
- `marca`
- `modelo`
- `numero_roma`
- `numero_serie`
- `fecha_adquisicion`
- `fecha_ultima_inspeccion`
- `fecha_proxima_inspeccion`
- `capacidad_litros`
- `observaciones`

Comentario: mantener tablas separadas es razonable. La interfaz y exportadores deben distinguir origen `MAQ` y `EQ`. No conviene exigir ROMA a todos los equipos si no procede.

## J) Catálogos SIEX

Mantener:

- `siex_catalogos`
- `siex_catalogos_items`

Enlaces objetivo:

- `cultivos.codigo_siex -> siex_catalogos_items.codigo` para catálogo `cultivo`.
- `cultivos.sistema_cultivo_siex` para catálogo `sistema_cultivo`.
- `cultivos.sistema_conduccion_siex` para catálogo `sistema_conduccion`, si procede.
- `fertilizaciones.codigo_actuacion_siex` para actuaciones si se confirma catálogo aplicable.
- `practicas_culturales.codigo_actuacion_siex` para labores/actuaciones.
- Unidades normalizadas mediante catálogo interno o tabla local pendiente de definir.

Comentario: no se deben inventar códigos. Los catálogos importados son infraestructura local; su aplicación funcional debe ser progresiva.

## K) Documentos

Estado actual:

- `tratamientos_documentos` para recetas PDF.
- `movimientos_economicos_documentos` para facturas PDF.

Opción v6 conservadora:

- Mantener ambas tablas, porque están bien enfocadas y evitan mezclar ámbitos.

Opción v6 futura:

- Crear `documentos` genérica con:
  - `id`
  - `area`
  - `registro_id`
  - `tipo_documento`
  - `nombre_original`
  - `nombre_guardado`
  - `ruta_relativa`
  - `extension`
  - `mime_type`
  - `size_bytes`
  - `sha256`
  - `orden`
  - `created_at`
  - `updated_at`

Comentario: no es imprescindible para el primer v6. La prioridad real está en cultivos/campañas/actuaciones.

## Relaciones bien resueltas hoy

- `tratamientos.campana_id`.
- `tratamientos.cultivo_id`.
- `tratamiento_parcelas`.
- `fertilizacion_parcelas`.
- `practica_parcelas`.
- `cosecha_parcelas`.
- `tratamientos_documentos`.
- `movimientos_economicos_documentos`.
- `siex_catalogos` y `siex_catalogos_items`.

## Relaciones débiles a resolver

- `cultivos.parcela_id` como relación directa única.
- Ausencia de `cultivos.campana_id`.
- `fertilizaciones.cultivo` como texto.
- `practicas_culturales.cultivo` como texto.
- `cosecha.cultivo` como texto.
- `movimientos_economicos.cultivo` como texto, si se quiere análisis económico por cultivo.
- `analisis_fitosanitarios.parcelas` como texto.
