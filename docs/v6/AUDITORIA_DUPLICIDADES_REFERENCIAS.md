# Auditoría de duplicidades de referencias v6

Fecha de revisión: 2026-06-30.

Esta auditoría revisa duplicidades visibles y lógicas entre campos de texto legacy y referencias estructuradas `*_id`. No elimina columnas, no cambia formularios, no modifica consultas y no propone migraciones automáticas por coincidencia de texto.

## Alcance revisado

Archivos revisados:

- `core/db.py`
- `modules/contabilidad.py`
- `modules/cosecha.py`
- `modules/fertilizacion.py`
- `modules/practicas_culturales.py`
- `modules/tratamientos.py`
- `modules/cultivos.py`
- `modules/parcelas.py`
- `modules/maquinaria.py`
- `modules/explotacion.py`
- `modules/informes.py`
- `modules/revision_siex.py`
- `services/exportacion_siex.py`
- `services/cuadernopro_pdf.py`

Como apoyo, también se revisó `modules/terceros.py` para entender la gestión maestra de `clientes` y `proveedores`.

## Esquema real observado

Tablas maestras principales:

- `clientes(id,nombre,nif,telefono,email,direccion,poblacion,provincia,codigo_postal,observaciones,activo,created_at,updated_at)`
- `proveedores(id,nombre,nif,telefono,email,direccion,poblacion,provincia,codigo_postal,actividad,observaciones,activo,created_at,updated_at)`
- `campanas(id,nombre,fecha_inicio,fecha_fin,activa)`
- `cultivos(id,parcela_id,especie,variedad,ano_plantacion,marco,arboles,sistema,activo,campana_id,codigo_siex,superficie)`
- `cultivo_parcelas(id,cultivo_id,parcela_id,superficie,created_at,updated_at)`
- `parcelas(id,nombre,provincia,municipio,poligono,parcela,recinto,superficie_sigpac,superficie_cultivada,geometry,observaciones,provincia_sigpac,municipio_sigpac,agregado_sigpac,zona_sigpac,sigpac_geojson,...)`
- `productos_fito(id,registro,nombre,materia_activa,dosis,plazo_seguridad,observaciones)`
- `personas(id,nombre,nif,telefono,email,rol,carnet_fitosanitario,fecha_caducidad_carnet,numero_asesor,observaciones)`
- `maquinaria(id,nombre,tipo,marca,modelo,fecha_compra,num_horas,observaciones,numero_roma)`
- `equipos_aplicacion(id,nombre,tipo,marca,modelo,numero_roma,numero_serie,fecha_adquisicion,fecha_ultima_inspeccion,fecha_proxima_inspeccion,capacidad_litros,observaciones)`

Tablas operativas con mezcla texto/ID:

- `fertilizaciones`: `cultivo` y `cultivo_id`, `operario_id`.
- `practicas_culturales`: `cultivo` y `cultivo_id`, `maquinaria_id`, `operario_id`, `proveedor_id`.
- `cosecha`: `cultivo` y `cultivo_id`, `cliente`, `nif_cliente`, `parcelas`; no existe `cliente_id`.
- `movimientos_economicos`: `tercero`, `nif_tercero`, `cultivo`, `cliente_id`, `proveedor_id`.
- `tratamientos`: `producto_id`, `cultivo_id`, `aplicador`, `aplicador_id`, `maquinaria_id`, `equipo_id`, `equipo_aplicacion_id`.
- `explotacion`: `responsable_*` y `asesor_*` como texto; no existen `responsable_id` ni `asesor_id`.

## Tabla de duplicidades

| Módulo | Campo texto legacy | Campo ID estructurado | Tabla maestra | Uso actual | Problema | Criticidad | Propuesta |
|---|---|---|---|---|---|---|---|
| Core DB | `fertilizaciones.cultivo`, `practicas_culturales.cultivo`, `cosecha.cultivo` | `cultivo_id` en las tres tablas | `cultivos` | Compatibilidad de esquema | La base permite dos fuentes para el mismo cultivo. Es intencionado en v6.1-v6.5, pero requiere disciplina de UI | Baja | Mantener columnas legacy ocultas y rellenarlas automáticamente desde `cultivo_id` cuando exista |
| Core DB | `cosecha.cliente`, `cosecha.nif_cliente` | No existe `cosecha.cliente_id` | `clientes` | Cosecha guarda cliente como texto | No hay relación persistente con `clientes`; el selector actual solo rellena texto/NIF | Crítica | Preparar `cliente_id` nullable en una fase controlada o mantener selector sin mostrar campos manuales cuando se use cliente maestro |
| Core DB | `movimientos_economicos.tercero`, `nif_tercero` | `cliente_id`, `proveedor_id` | `clientes`, `proveedores` | Contabilidad guarda ambos | Puede haber tercero textual distinto del cliente/proveedor seleccionado | Crítica | Usar un único selector por tipo y rellenar `tercero`/`nif_tercero` automáticamente como compatibilidad |
| Core DB | `cultivos.parcela_id` | `cultivo_parcelas.cultivo_id`, `cultivo_parcelas.parcela_id` | `parcelas` | Fallback legacy | Consultas antiguas solo ven una parcela por cultivo | Media | Usar `cultivo_parcelas` en listados, exportador, informes y PDF; mantener `parcela_id` solo como fallback |
| Cosecha | `cultivo` | `cultivo_id` | `cultivos` | Alta usa selector v6 y rellena texto; listado muestra `cultivo_id` y cultivo resuelto; edición tabular permite editar `cultivo` | El usuario ve ID técnico y puede editar texto legacy separado del `cultivo_id` | Crítica | En listado mostrar solo cultivo resuelto; ocultar `cultivo_id`; en edición quitar `cultivo` del editor tabular y dejar solo selector estructurado |
| Cosecha | `cliente`, `nif_cliente` | No existe `cliente_id` | `clientes` | Alta y edición permiten selector de cliente, pero siguen mostrando campos editables `Cliente / comprador` y `NIF cliente` | El usuario puede seleccionar un cliente y luego guardar nombre/NIF contradictorios | Crítica | Si se añade `cliente_id`, guardar relación y rellenar texto/NIF ocultos. Si no se añade todavía, convertir texto/NIF en valores automáticos o edición manual explícita de compatibilidad |
| Cosecha | `parcelas` texto | `cosecha_parcelas.cosecha_id`, `parcela_id` | `parcelas` | Alta guarda relación y también texto; exportador/PDF aún pueden usar texto | Puede divergir el texto histórico de las relaciones reales | Media | Mostrar parcelas resueltas desde `cosecha_parcelas`; mantener `parcelas` solo como fallback |
| Fertilización | `cultivo` | `cultivo_id` | `cultivos` | Alta usa selector v6; listado muestra `cultivo_id` y cultivo resuelto; editor tabular permite editar `cultivo` | Se exponen al usuario el ID técnico y el texto legacy editable | Crítica | Ocultar `cultivo_id`; mostrar solo cultivo resuelto; sacar `cultivo` del editor tabular y usar selector estructurado |
| Fertilización | Texto de parcelas no existe en tabla principal | `fertilizacion_parcelas.fertilizacion_id`, `parcela_id` | `parcelas` | Alta y duplicado usan tabla hija | No hay duplicidad fuerte en datos, pero algunos flujos muestran IDs internos en selectores | Baja | Mantener multiselect con etiquetas legibles; evitar mostrar IDs salvo como fallback |
| Fertilización | Sin texto de operario | `operario_id` | `personas` | Alta usa selector; editor muestra `operario_id` numérico y nombre de operario | El usuario edita un ID técnico en vez de seleccionar persona | Media | Sustituir `operario_id` editable por selector de persona o mantenerlo oculto y gestionar con acción específica |
| Prácticas culturales | `cultivo` | `cultivo_id` | `cultivos` | Alta usa selector v6; listado muestra `cultivo_id` y cultivo resuelto; editor tabular permite editar `cultivo` | Se mantiene una vía de edición textual que puede contradecir `cultivo_id` | Crítica | Mostrar solo cultivo resuelto; ocultar `cultivo_id`; dejar la asignación de cultivo en selector seguro |
| Prácticas culturales | Sin texto de proveedor | `proveedor_id` | `proveedores` | Alta usa selector de prestador; editor convierte a etiqueta `prestador` | La parte de prestador está razonablemente estructurada | Baja | Mantener selector de prestador; evitar exponer `proveedor_id` al usuario |
| Prácticas culturales | Sin texto de maquinaria/operario | `maquinaria_id`, `operario_id` | `maquinaria`, `personas` | Alta usa selectores; editor muestra nombres deshabilitados | No hay duplicidad visible fuerte, pero no hay edición estructurada completa desde tabla | Baja | Mantener nombres legibles y añadir selectores seguros solo si se necesita editar maquinaria/operario |
| Contabilidad | `tercero`, `nif_tercero` | `cliente_id`, `proveedor_id` | `clientes`, `proveedores` | Alta muestra `Tercero`, `NIF tercero` y además selector `Cliente` o `Proveedor`; listado muestra `tercero`, `cliente` y `proveedor`; editor permite editar todo | El usuario puede guardar dos terceros contradictorios en el mismo movimiento | Crítica | En alta mostrar selector único según tipo y rellenar `tercero`/`nif_tercero` ocultos. En listado mostrar tercero resuelto. En edición ocultar texto legacy o dejarlo solo para registros sin ID |
| Contabilidad | `cultivo` | No existe `cultivo_id` en `movimientos_economicos` | `cultivos` | Selector usa textos de cultivos disponibles | La relación económica con cultivo no es estructurada y puede perder campaña/parcela | Media | Preparar `cultivo_id` en fase posterior si se quiere imputación económica estructurada por cultivo |
| Tratamientos | No hay `producto` texto en `tratamientos` | `producto_id` | `productos_fito` | Alta usa selector; listado resuelve nombre; editor muestra nombre deshabilitado y `producto_id` editable | El editor obliga a editar un número interno y puede generar confusión | Crítica | Cambiar editor a selector de producto; ocultar `producto_id` |
| Tratamientos | Cultivo resuelto como texto en consultas | `cultivo_id` | `cultivos` | Alta selecciona cultivo agrupado y guarda un `cultivo_id`; editor muestra `cultivo` deshabilitado y `cultivo_id` editable | El selector de alta se basa en agrupación legacy por `cultivos.parcela_id`; editor muestra ID técnico | Crítica | Usar selector v6 de cultivo por campaña y `cultivo_parcelas`; ocultar `cultivo_id` |
| Tratamientos | `aplicador` | `aplicador_id` | `personas` | Alta usa selector y guarda además nombre; listado usa persona o texto legacy; editor muestra nombre deshabilitado e ID editable | Puede quedar texto legacy divergente; el editor expone ID técnico | Crítica | Usar `aplicador_id` como fuente; ocultar `aplicador`; rellenarlo automáticamente solo por compatibilidad |
| Tratamientos | Equipo como nombre resuelto | `equipo_id`, `equipo_aplicacion_id`, `maquinaria_id` | `equipos_aplicacion`, `maquinaria` | Alta usa `equipos_aplicacion`; consultas hacen `COALESCE(equipo_aplicacion_id,equipo_id)` y fallback a `maquinaria_id`; editor expone `equipo_aplicacion_id` | Hay dos columnas para equipo de aplicación y una de maquinaria general; puede haber ambigüedad | Crítica | Decidir columna canónica para equipos de aplicación; ocultar IDs y usar selector con origen claro |
| Tratamientos | Parcelas agrupadas desde cultivo legacy | `tratamiento_parcelas.tratamiento_id`, `parcela_id` | `parcelas`, `cultivo_parcelas` | Alta deriva parcelas desde `cultivos.parcela_id` | No aprovecha `cultivo_parcelas` v6 para cultivos multi-parcela | Media | Usar `cultivo_parcelas` con fallback a `cultivos.parcela_id` |
| Cultivos | `cultivos.parcela_id` | `cultivo_parcelas` | `parcelas` | Alta/edición usan multiselect y actualizan ambas rutas | La UI está bien orientada, pero el fallback legacy puede sesgar consumidores antiguos a la primera parcela | Media | Mantener escritura dual; adaptar consumidores a `cultivo_parcelas` |
| Cultivos | Etiquetas de parcelas incluyen `ID` | `parcelas.id` | `parcelas` | Selectores muestran `ID`, campaña y datos legibles | ID interno visible en selector, aunque ayuda al diagnóstico | Baja | Reducir ID a fallback o formato secundario cuando las referencias SIGPAC sean suficientes |
| Parcelas | `provincia`, `municipio` | `provincia_sigpac`, `municipio_sigpac`, `agregado_sigpac`, `zona_sigpac` | Catálogos SIGPAC locales | Alta usa selectores de provincia/municipio y guarda nombre+código; edición tabular permite editar ambos | En edición se pueden crear incoherencias entre texto y código SIGPAC | Media | En edición usar selectores SIGPAC o bloquear textos derivados cuando se editen códigos |
| Parcelas | `cultivo_asociado` desde `cultivos.parcela_id` | `cultivo_parcelas` | `cultivos`, `cultivo_parcelas` | Listado calcula cultivos asociados con relación legacy | Puede no mostrar cultivos v6 multi-parcela | Media | Calcular asociados desde `cultivo_parcelas` y usar `cultivos.parcela_id` solo como fallback |
| Maquinaria | `id_visual`, `tabla_origen`, `id_real` | IDs de `maquinaria` y `equipos_aplicacion` | `maquinaria`, `equipos_aplicacion` | Listado unifica maquinaria general y equipos | Se exponen IDs técnicos en el maestro, útil para distinguir origen pero no ideal para usuario final | Baja | Mostrar descripción y origen; reservar `id_real`/`tabla_origen` para diagnóstico |
| Explotación | `responsable_nombre`, `responsable_nif`, `asesor_nombre`, `asesor_nif`, `asesor_numero_registro` | No existen `responsable_id` ni `asesor_id` | `personas` | Responsable/asesor se editan como texto; asesor puede copiarse desde `personas` | Puede existir una persona asesor y datos de explotación divergentes tras editar manualmente | Media | Valorar `responsable_id`/`asesor_id` nullable o mantener copia textual con selector y campos derivados no editables |
| Informes | `movimientos_economicos.tercero`, `fertilizaciones.cultivo`, `practicas_culturales.cultivo`, `cosecha.cultivo` | Parcial: `cliente_id`, `proveedor_id`, `tratamientos.cultivo_id`, `producto_id` | Varias | Informes resuelven clientes/proveedores en contabilidad y tratamientos por ID, pero fertilización/prácticas/cosecha usan texto legacy | Los resúmenes pueden agrupar por texto antiguo aunque exista `cultivo_id` | Media | En v6.8 resolver cultivo desde `cultivo_id` con fallback textual |
| Revisión SIEX | Avisos sobre `cultivo` textual | `cultivo_id` | `cultivos` | Ya distingue con `cultivo_id`, texto pendiente o falta de cultivo en fertilización, prácticas y cosecha | El filtro de cultivo sigue desactivado porque el modelo está mezclado | Baja | Mantener prudencia; activar filtro cuando los módulos principales usen IDs de forma uniforme |
| Exportador SIEX | `fertilizaciones.cultivo`, `practicas_culturales.cultivo`, `cosecha.cultivo`, `cosecha.cliente` | Parcial: tratamientos sí usa `cultivo_id`, `producto_id`, `aplicador_id`; cultivos usa `parcela_id` legacy | Varias | Excel asistido mezcla referencias estructuradas y textos legacy | Puede exportar nombres antiguos aunque ya haya IDs, y cultivos-parcelas puede quedar incompleto | Media | En v6.8 resolver por IDs y mantener fallback textual; adaptar parcelas desde `cultivo_parcelas` |
| PDF oficial | `fertilizaciones.cultivo`, `practicas_culturales.cultivo`, `cosecha.cultivo`, `cosecha.cliente`, `movimientos_economicos.tercero` | Parcial: tratamientos usa `cultivo_id`, `producto_id`, `aplicador_id`; movimientos usa cliente/proveedor join | Varias | PDF mezcla resoluciones por ID con campos legacy | Puede mostrar textos antiguos si el usuario ya asignó `cultivo_id` | Media | En v6.8 resolver nombres desde IDs y mantener textos legacy como fallback |

## Duplicidades críticas detectadas

1. Cosecha muestra y/o permite modificar `cultivo_id`/`cultivo` de forma separada en listado y edición, y además no tiene `cliente_id` para persistir el cliente seleccionado.
2. Fertilización muestra `cultivo_id` junto al cultivo resuelto y mantiene `cultivo` editable en la edición tabular.
3. Prácticas culturales muestra `cultivo_id` junto al cultivo resuelto y mantiene `cultivo` editable en la edición tabular.
4. Contabilidad muestra y guarda `tercero`/`nif_tercero` además de `cliente_id` o `proveedor_id`.
5. Tratamientos expone en edición `producto_id`, `cultivo_id`, `aplicador_id` y `equipo_aplicacion_id` como números técnicos junto a nombres resueltos.
6. Tratamientos mantiene `aplicador` texto junto a `aplicador_id` y mezcla `equipo_id`, `equipo_aplicacion_id` y `maquinaria_id`.

## Módulos más afectados

1. `modules/cosecha.py`: impacto directo en `cultivo_id`, cliente, NIF y listado/editor.
2. `modules/contabilidad.py`: impacto directo en terceros, cliente/proveedor y listados económicos.
3. `modules/tratamientos.py`: mayor mezcla de referencias técnicas visibles en editor.
4. `modules/fertilizacion.py`: limpieza acotada de cultivo y operario.
5. `modules/practicas_culturales.py`: limpieza acotada de cultivo; prestador ya está razonablemente resuelto.
6. `modules/informes.py`, `services/exportacion_siex.py` y `services/cuadernopro_pdf.py`: consumidores que aún deben priorizar IDs en v6.8.

## Propuesta de limpieza por fases

### v6.6 - Limpieza UI de referencias principales

Módulos prioritarios:

1. Cosecha.
2. Fertilización.
3. Prácticas culturales.
4. Contabilidad.

Objetivo:

- Ocultar `cultivo_id`, `cliente_id`, `proveedor_id` y otros IDs técnicos en listados y editores de usuario.
- Mostrar nombres resueltos desde tablas maestras.
- Evitar edición manual de `cultivo`, `cliente`, `proveedor`, `tercero` y `nif_tercero` cuando exista selector estructurado.
- Mantener campos legacy, pero rellenarlos automáticamente desde la relación estructurada.
- En Cosecha, decidir explícitamente si se prepara `cosecha.cliente_id` nullable para cerrar la relación con `clientes`.

### v6.7 - Limpieza de tratamientos y productos/personas

Objetivo:

- Cambiar la edición de tratamientos para usar selectores de producto, cultivo, aplicador y equipo.
- Ocultar IDs técnicos en el editor.
- Usar `cultivo_parcelas` para sugerir parcelas tratadas.
- Decidir columna canónica para equipo de aplicación: `equipo_aplicacion_id` debería prevalecer sobre `equipo_id`; `maquinaria_id` debe quedar solo para maquinaria general si procede.
- Mantener `tratamientos.aplicador` como copia textual automática, no como fuente principal.

### v6.8 - Limpieza de listados, informes y exportador SIEX

Objetivo:

- Adaptar listados, informes, Excel asistido SIEX/CUE y PDF oficial para resolver nombres desde IDs.
- Usar `cultivo_id` en fertilización, prácticas y cosecha con fallback a texto legacy.
- Usar `cultivo_parcelas` para cultivos-parcelas con fallback a `cultivos.parcela_id`.
- Mantener prudencia en `Revisión SIEX` y activar filtros estructurados solo cuando los módulos afectados estén normalizados.

### v6.9 - Decisión sobre columnas legacy

Objetivo:

- Decidir si las columnas legacy se eliminan en base nueva o si quedan ocultas por compatibilidad.
- Documentar reglas de relleno automático para cada texto legacy conservado.
- Diseñar migraciones revisables, no automáticas por coincidencia de texto, para datos históricos.

## Recomendación de inicio

Recomiendo empezar v6.6 por `Cosecha`.

Motivos:

- Es el módulo adaptado más recientemente y el contexto está fresco.
- Tiene duplicidad crítica de `cultivo_id`/`cultivo` visible en listado y edición.
- Tiene el problema visible de cliente: selector desde `clientes`, pero persistencia solo en `cliente` y `nif_cliente`.
- Es un flujo más acotado que Contabilidad y menos denso que Tratamientos.

Después seguiría con `Fertilización` y `Prácticas culturales`, porque la limpieza de `cultivo_id`/`cultivo` es muy parecida y debería resolverse con el mismo patrón. `Contabilidad` debería entrar al final de v6.6, porque el esquema ya tiene `cliente_id` y `proveedor_id`, pero el cambio afecta a ingresos, gastos, listados, pendientes, facturas adjuntas y edición tabular.

