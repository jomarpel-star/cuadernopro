# Esquema limpio objetivo v7

Este documento define el esquema objetivo para una base nueva v7. No describe una migración automática desde v6.

## Principios

- Un dato estructurado se guarda por ID, no como texto duplicado.
- Los nombres visibles se resuelven con `JOIN` desde tablas maestras.
- Las relaciones N:M se modelan con tablas puente.
- Los textos de compatibilidad de v6 no forman parte del esquema limpio, salvo decisión explicita.
- Las columnas derivadas solo se guardan si se decide que son cache controlada.

## Tablas maestras

### `campanas`

Mantener:

- `id`
- `nombre`
- `fecha_inicio`
- `fecha_fin`
- `activa`

Revisar futuro:

- `estado`, si se quiere diferenciar abierta/cerrada/archivada.

### `explotacion`

Mantener:

- `id`
- `nombre_explotacion`
- `titular`
- `nif`
- datos de dirección y contacto
- `identificador_oficial`
- `tipo_identificador_oficial`
- `registro_autonomico`
- `tipo_explotacion`
- `orientacion_productiva`
- `fecha_alta`
- `agricultor_activo`
- `joven_agricultor`
- responsable y asesor
- `observaciones`

`identificador_oficial` es el campo canónico para el código REGEPA /
identificador oficial principal. `registro_autonomico` es independiente.

Revisar futuro:

- enlazar responsable y asesor a `personas` si compensa funcionalmente.

### `parcelas`

Mantener:

- identificacion SIGPAC;
- superficies SIGPAC;
- geometría o GeoJSON;
- observaciones.

Revisar:

- `superficie_cultivada`, porque puede solaparse con `cultivos.superficie`.
- campo principal de geometría: `geometry` frente a `sigpac_geojson`.

### `cultivos`

Esquema limpio recomendado:

- `id`
- `campana_id`
- `nombre` o `especie` como nombre canónico decidido
- `variedad`
- `codigo_siex`
- `superficie` en hectareas
- `ano_plantacion`
- `marco_plantacion`
- `numero_arboles`
- `activo`
- `observaciones`
- `created_at`
- `updated_at`

Nota v7.17:

- `marco_plantacion` conserva el texto introducido por el usuario
  (`6x5`, `6,5x5`, `8 x 6`, etc.);
- `numero_arboles` guarda el resultado redondeado y editable;
- formula usada: `round((superficie_ha * 10000) / (distancia_1_m * distancia_2_m))`;
- `marco` y `arboles` quedan solo como compatibilidad si ya existen en una
  base previa, pero no se crean como columnas canonicas v7 limpias.

Eliminar en v7:

- `parcela_id`

Relaciones:

- `cultivos.campana_id -> campanas.id`
- `cultivo_parcelas.cultivo_id -> cultivos.id`

### `cultivo_parcelas`

Mantener como relación N:M:

- `id`
- `cultivo_id`
- `parcela_id`
- `superficie`
- `created_at`
- `updated_at`

Relaciones:

- `cultivo_id -> cultivos.id`
- `parcela_id -> parcelas.id`

### `clientes` y `proveedores`

Mantener:

- `id`
- `nombre`
- `nif`
- datos de contacto y dirección
- `activo`
- `created_at`
- `updated_at`

### `productos_fito`

Mantener:

- `id`
- `numero_registro`
- `nombre`
- `materia_activa`
- `titular`
- `uso_autorizado`
- `plazo_seguridad`
- `observaciones`
- `activo`

No recuperar como canonicos:

- `registro`
- `dosis`

### `maquinaria`

Mantener como maquinaria general:

- `id`
- `descripcion`
- `tipo`
- `marca`
- `modelo`
- `matricula`
- `numero_roma`
- `numero_serie`
- `fecha_compra`
- `horas_uso`
- `observaciones`
- `activa`

### `equipos_aplicacion`

Mantener como equipos fitosanitarios:

- `id`
- `nombre`
- `tipo`
- `marca`
- `modelo`
- `matricula`
- `numero_roma`
- `numero_serie`
- `fecha_adquisicion`
- `fecha_revision`
- `fecha_proxima_revision`
- `capacidad_litros`
- `observaciones`
- `activo`

### `personas`

Mantener:

- `id`
- `nombre`
- `nif`
- contacto
- `rol`
- `carnet_fitosanitario`
- `fecha_caducidad_carnet`
- `numero_asesor`
- `observaciones`

### `siex_catalogos` y `siex_catalogos_items`

Mantener como infraestructura interna de catálogos.

Revisar:

- enlaces desde cultivos, labores, unidades y actuaciones cuando se decida el catálogo aplicable.

## Tablas operativas

### `tratamientos`

Campos que deberian quedarse:

- `id`
- `campana_id`
- `fecha_inicio`
- `fecha_fin`
- `cultivo_id`
- `producto_id`
- `plaga`
- `justificacion`
- `dosis`
- `caldo`
- `superficie_tratada`
- `aplicador_id`
- `equipo_aplicacion_id`
- `plazo_seguridad`
- `fecha_recoleccion_segura`
- `condiciones_meteorologicas`
- `eficacia`
- `observaciones`
- `created_at`
- `updated_at`

Eliminar en v7:

- `fecha`
- `problema`
- `aplicador`
- `equipo_id`
- `maquinaria_id`, salvo que se redefina como maquinaria general adicional
- `condiciones`

Claves foraneas:

- `campana_id -> campanas.id`
- `cultivo_id -> cultivos.id`
- `producto_id -> productos_fito.id`
- `aplicador_id -> personas.id`
- `equipo_aplicacion_id -> equipos_aplicacion.id`

Campos derivados:

- nombre de cultivo, producto, aplicador y equipo.

### `tratamiento_parcelas`

Campos:

- `id`, si se decide anadir PK propia
- `tratamiento_id`
- `parcela_id`
- `superficie`

Eliminar:

- nada funcional; es tabla puente canonica.

Uso v8.0.1:

- se mantiene para compatibilidad con consumidores anteriores;
- las altas multicultivo la rellenan con las parcelas seleccionadas.

### `tratamiento_cultivos`

Tabla puente v8.0.1 para representar tratamientos sobre varios cultivos y
parcelas por cultivo.

Campos:

- `id`
- `tratamiento_id`
- `cultivo_id`
- `parcela_id`
- `superficie`
- `observaciones`
- `created_at`
- `updated_at`

Regla de lectura:

- informes, PDF y SIEX deben leer primero `tratamiento_cultivos`;
- si no hay detalle, deben hacer fallback a `tratamientos.cultivo_id` y
  `tratamiento_parcelas`.

### `tratamientos_documentos`

Mantener:

- campos actuales de documento (`tratamiento_id`, `tipo_documento`, `ruta_relativa`, `sha256`, `orden`, fechas).

### `fertilizaciones`

Campos que deberian quedarse:

- `id`
- `campana_id`
- `cultivo_id`
- `fecha`
- `producto`
- `tipo`
- `riqueza_npk`
- `cantidad`
- `unidad`
- `metodo_aplicacion`
- `superficie`
- `operario_id`
- `observaciones`
- `created_at`
- `updated_at`

Eliminar en v7:

- `cultivo`

Revisar/anadir si se confirma SIEX:

- `codigo_actuacion_siex`
- `unidad_normalizada`

Claves foraneas:

- `campana_id -> campanas.id`
- `cultivo_id -> cultivos.id`
- `operario_id -> personas.id`

Campos derivados:

- nombre del cultivo.

### `fertilizacion_parcelas`

Campos:

- `id`
- `fertilizacion_id`
- `parcela_id`

Relaciones:

- `fertilizacion_id -> fertilizaciones.id`
- `parcela_id -> parcelas.id`

Uso v8.0.1:

- se mantiene como compatibilidad;
- las altas multicultivo la rellenan con las parcelas fertilizadas.

### `fertilizacion_cultivos`

Tabla puente v8.0.1 para fertilizaciones sobre varios cultivos y parcelas por
cultivo.

Campos:

- `id`
- `fertilizacion_id`
- `cultivo_id`
- `parcela_id`
- `superficie`
- `observaciones`
- `created_at`
- `updated_at`

Regla de lectura:

- informes, PDF y SIEX deben leer primero `fertilizacion_cultivos`;
- si no hay detalle, deben hacer fallback a `fertilizaciones.cultivo_id` y
  `fertilizacion_parcelas`.

### `practicas_culturales`

Campos que deberian quedarse:

- `id`
- `campana_id`
- `cultivo_id`
- `fecha`
- `labor`
- `superficie`
- `maquinaria_id`
- `operario_id`
- `proveedor_id`
- `observaciones`
- `created_at`
- `updated_at`

Eliminar en v7:

- `cultivo`

Revisar/anadir si se confirma SIEX:

- `codigo_actuacion_siex`

Claves foraneas:

- `campana_id -> campanas.id`
- `cultivo_id -> cultivos.id`
- `maquinaria_id -> maquinaria.id`
- `operario_id -> personas.id`
- `proveedor_id -> proveedores.id`

### `practicas_culturales_parcelas`

Mantener:

- `id`
- `practica_id`
- `parcela_id`

Relaciones:

- `practica_id -> practicas_culturales.id`
- `parcela_id -> parcelas.id`

Uso v8.0.1:

- se mantiene como compatibilidad;
- las altas multicultivo la rellenan con las parcelas afectadas.

### `practicas_culturales_cultivos`

Tabla puente v8.0.1 para prácticas culturales sobre varios cultivos y parcelas
por cultivo.

Campos:

- `id`
- `practica_id`
- `cultivo_id`
- `parcela_id`
- `superficie`
- `observaciones`
- `created_at`
- `updated_at`

Regla de lectura:

- informes, PDF y SIEX deben leer primero `practicas_culturales_cultivos`;
- si no hay detalle, deben hacer fallback a `practicas_culturales.cultivo_id`
  y `practicas_culturales_parcelas` o `practica_parcelas` si se trata de una
  base compatible antigua.

### `cosecha`

Campos limpios recomendados:

- `id`
- `campana_id`
- `cultivo_id`
- `fecha`
- `producto`
- `cantidad`
- `unidad`
- `precio`
- `lote`
- `destino`
- `cliente_id`, si se decide cerrar la relación con `clientes`
- `albaran`
- `factura`
- `observaciones`
- `created_at`
- `updated_at`

Eliminar en v7:

- `cultivo`
- `kg`
- `parcelas`
- `cliente`
- `nif_cliente`

Condicion:

- Eliminar `cliente` y `nif_cliente` solo si v7 incorpora `cliente_id`.

Claves foraneas:

- `campana_id -> campanas.id`
- `cultivo_id -> cultivos.id`
- `cliente_id -> clientes.id`, si se añade.

Campos derivados:

- nombre y NIF de cliente;
- cultivos y parcelas desde `cosecha_cultivos` si existe detalle v7.16;
- parcelas desde `cosecha_parcelas` como compatibilidad;
- unidad textual si se normaliza más adelante.

Nota v7.16:

- `cultivo_id` permanece como cultivo principal de compatibilidad;
- en cosechas multi-cultivo se rellena con el primer cultivo seleccionado;
- la relación canonica nueva es `cosecha_cultivos`.

### `cosecha_parcelas`

Mantener:

- `id`
- `cosecha_id`
- `parcela_id`

Relaciones:

- `cosecha_id -> cosecha.id`
- `parcela_id -> parcelas.id`

Uso v7.16:

- se mantiene para compatibilidad con cosechas antiguas y consumidores
  anteriores;
- las cosechas nuevas multi-cultivo también la rellenan con las parcelas
  seleccionadas.

### `cosecha_cultivos`

Tabla puente v7.16 para representar la procedencia real de una cosecha:

- varios cultivos en una misma cosecha;
- varias parcelas o recintos por cultivo;
- superficie por línea de cultivo/parcela.

Campos:

- `id`
- `cosecha_id`
- `cultivo_id`
- `parcela_id`
- `superficie`
- `observaciones`
- `created_at`
- `updated_at`

Relaciones:

- `cosecha_id -> cosecha.id`
- `cultivo_id -> cultivos.id`
- `parcela_id -> parcelas.id`

Regla de lectura:

- informes, PDF y SIEX deben leer primero `cosecha_cultivos`;
- si no hay detalle, deben hacer fallback a `cosecha.cultivo_id` y
  `cosecha_parcelas`.

### `movimientos_economicos`

Campos que deberian quedarse:

- `id`
- `campana_id`
- `fecha`
- `tipo`
- `categoria`
- `concepto`
- `numero_factura`
- `base_imponible`
- `iva_porcentaje`, si se mantiene resumen
- `iva_importe`, si se mantiene resumen
- `retencion`
- `total`
- `forma_pago`
- `pagado`
- `fecha_pago`
- `cliente_id`
- `proveedor_id`
- `observaciones`
- `created_at`
- `updated_at`

Eliminar en v7:

- `tercero`
- `nif_tercero`
- `cultivo`, salvo decisión de analítica por cultivo.

Revisar/anadir:

- `cultivo_id`, solo si se quiere contabilidad por cultivo.

Claves foraneas:

- `campana_id -> campanas.id`
- `cliente_id -> clientes.id`
- `proveedor_id -> proveedores.id`
- `cultivo_id -> cultivos.id`, si se añade.

Campos derivados:

- nombre y NIF de cliente/proveedor.

### `movimientos_economicos_lineas_iva`

Mantener:

- `id`
- `movimiento_id`
- `descripcion`
- `base_imponible`
- `tipo_iva`
- `cuota_iva`
- `total_linea`
- `created_at`
- `updated_at`

Relaciones:

- `movimiento_id -> movimientos_economicos.id`

### `movimientos_economicos_documentos`

Mantener:

- campos actuales de factura/documento.

### `analisis_fitosanitarios`

Campos actuales utiles:

- `id`
- `campana_id`
- `fecha`
- `material_analizado`
- `cultivo_id`
- `boletin_numero`
- `laboratorio`
- `sustancias_detectadas`
- `resultado`
- `observaciones`
- `documento`
- `created_at`
- `updated_at`

Revisar:

- `parcelas` texto. Si el módulo pasa a ser relevante, crear tabla puente.

### `gastos`

Tabla simple solapada con `movimientos_economicos`.

Propuesta v7:

- dejar fuera de la base limpia inicial si no hay flujo funcional activo;
- conservar solo si se confirma uso real.

### `diario`

Tabla simple de notas con `parcela_id`.

Propuesta v7:

- mantener si se quiere diario de campo;
- revisar si debe relacionarse con campaña o cultivo.
