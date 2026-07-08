# Auditoría legacy v7

Esta auditoría lista columnas y dependencias reales detectadas en el esquema y
en el código actual. No implica cambios aplicados.

## Tabla de campos legacy y duplicidades

| Módulo | Tabla | Campo legacy | Campo limpio equivalente | Uso actual en código | Riesgo al eliminar | Propuesta v7 |
| --- | --- | --- | --- | --- | --- | --- |
| Cultivos | `cultivos` | `parcela_id` | `cultivo_parcelas.cultivo_id` + `cultivo_parcelas.parcela_id` | `modules/cultivos.py` lo sigue rellenando con la primera parcela; `modules/parcelas.py`, `services/exportacion_siex.py`, `services/cuadernopro_pdf.py` y `modules/revision_siex.py` aún lo usan como relación/fallback. | Alto | Eliminar en esquema v7; adaptar consumidores a `cultivo_parcelas`. |
| Cultivos | `cultivos` | `especie` como nombre visible | `nombre` conceptual o mantener `especie` si se decide nombre técnico | Formularios y consultas usan `especie` para mostrar el cultivo. | Medio | Revisar más adelante: renombrar conceptualmente o mantener como nombre principal documentado. |
| Cultivos | `cultivos` | `superficie` como dato editable paralelo a parcelas | Superficie propia del cultivo/campaña | Ya se usa para sugerir superficies en actuaciones. | Bajo | Mantener como superficie declarada del cultivo; no tratar como legacy. |
| Parcelas | `parcelas` | `superficie_cultivada` | Superficie calculada o dato agronómico definido | Se muestra en parcelas; puede solaparse con `cultivos.superficie`. | Medio | Revisar más adelante; definir si es dato propio o derivado. |
| Fertilización | `fertilizaciones` | `cultivo` | `cultivo_id` | Alta, duplicado, asignación legacy, listados, informes, PDF y exportador SIEX lo leen o escriben como compatibilidad. | Alto | Eliminar en esquema v7; resolver etiqueta desde `cultivo_id`. |
| Fertilización | `fertilizaciones` | `producto` texto | Catálogo futuro de fertilizantes o texto controlado | Es el producto/fertilizante principal; no existe tabla maestra de fertilizantes. | Medio | Mantener, pero revisar normalización futura. |
| Fertilización | `fertilizaciones` | `unidad` texto libre/control interno | Catálogo/unidad normalizada | Revisión SIEX avisa que las unidades pueden requerir normalización; exportador espera `unidad_normalizada` si existe. | Medio | Mantener en v7 inicial y añadir normalización posterior si se confirma catálogo. |
| Fertilización | `fertilizaciones` | `superficie` | Derivada de parcelas/cultivo o superficie aplicada | Se guarda y se usa en informes. | Bajo | Mantener como superficie aplicada, no derivarla automáticamente. |
| Fertilización | `fertilizaciones` | `operario_id` | `personas.id` | Ya es estructurado; el editor aún muestra/valida el ID. | Bajo | Mantener; mejorar UI si procede. |
| Prácticas culturales | `practicas_culturales` | `cultivo` | `cultivo_id` | Alta, duplicado, asignación legacy, listados, informes, PDF y exportador SIEX lo leen o escriben como compatibilidad. | Alto | Eliminar en esquema v7; resolver etiqueta desde `cultivo_id`. |
| Prácticas culturales | `practicas_culturales` | `labor` texto | Código SIEX/CUE de actuación si se confirma catálogo | Es el campo funcional actual; no existe columna `codigo_actuacion_siex` en el esquema base. | Medio | Mantener como texto visible y preparar código normalizado en fase posterior. |
| Prácticas culturales | `practicas_culturales` | `maquinaria_id` | `maquinaria.id` | Ya es estructurado; se usa en listados, revisión y PDF. | Bajo | Mantener. |
| Prácticas culturales | `practicas_culturales` | `proveedor_id` | `proveedores.id` | Ya es estructurado para prestador. | Bajo | Mantener. |
| Cosecha | `cosecha` | `cultivo` | `cultivo_id` | Alta, duplicado, asignación legacy, listados, informes, PDF y exportador SIEX lo leen o escriben. | Alto | Eliminar en esquema v7; resolver etiqueta desde `cultivo_id`. |
| Cosecha | `cosecha` | `kg` | `cantidad` + `unidad` | Es la cantidad principal actual; listados derivan unidad `kg`. | Alto | Sustituir en esquema v7 por `cantidad` y `unidad`; no migrar automáticamente en esta fase. |
| Cosecha | `cosecha` | `cliente` | `cliente_id` propuesto | Se selecciona desde `clientes`, pero se persiste texto. | Alto | Añadir `cliente_id` en esquema v7; eliminar texto si se carga base nueva. |
| Cosecha | `cosecha` | `nif_cliente` | Derivado de `clientes.nif` | Se guarda junto al cliente textual. | Alto | Convertir a campo derivado; no guardar duplicado en v7 limpia. |
| Cosecha | `cosecha` | `parcelas` | `cosecha_parcelas` | Se conserva como texto/fallback en listados, duplicado y exportador. | Medio | Eliminar en esquema v7; usar solo `cosecha_parcelas`. |
| Cosecha | `cosecha` | `producto` | Producto cosechado textual o cultivo/producto comercial normalizado | Campo funcional actual; no existe tabla maestra de productos cosechados. | Medio | Mantener inicialmente como texto de producto/lote comercial. |
| Cosecha | `cosecha` | `albaran`, `factura` | Documentos o referencias comerciales | Son referencias textuales; no hay tabla documental específica de cosecha. | Bajo | Mantener como referencias de gestión o revisar tabla documental futura. |
| Contabilidad | `movimientos_economicos` | `tercero` | `cliente_id` o `proveedor_id` | Alta, listados, informes y PDF lo rellenan o lo usan como fallback. | Alto | Eliminar en esquema v7; resolver tercero desde cliente/proveedor. |
| Contabilidad | `movimientos_economicos` | `nif_tercero` | `clientes.nif` o `proveedores.nif` | Se guarda como compatibilidad y se muestra como NIF resuelto. | Alto | Convertir a campo derivado; no guardar duplicado. |
| Contabilidad | `movimientos_economicos` | `cultivo` | `cultivo_id` opcional, si se decide contabilidad por cultivo | Informes agrupan resultado económico por este texto. | Medio | Revisar más adelante; añadir `cultivo_id` solo si se quiere analítica por cultivo. |
| Contabilidad | `movimientos_economicos` | `iva_porcentaje`, `iva_importe` junto a `movimientos_economicos_lineas_iva` | Líneas IVA como detalle canónico | Sigue habiendo campos resumen y tabla de desglose. | Medio | Mantener resumen calculado o definirlo como caché derivada. |
| Tratamientos | `tratamientos` | `fecha` | `fecha_inicio` + `fecha_fin` | Alta y consultas guardan `fecha` igual a inicio; listados/PDF/exportador hacen fallback. | Alto | Eliminar en esquema v7; usar intervalo obligatorio. |
| Tratamientos | `tratamientos` | `problema` | `plaga` | Alta guarda ambos; PDF/exportador usan `COALESCE(plaga, problema)`. | Medio | Eliminar en esquema v7; usar `plaga` o renombrar a motivo/plaga. |
| Tratamientos | `tratamientos` | `aplicador` | `aplicador_id` -> `personas.id` | Alta lo rellena desde persona; PDF/exportador/listado lo usan como fallback. | Alto | Eliminar en esquema v7; resolver desde `aplicador_id`. |
| Tratamientos | `tratamientos` | `equipo_id` | `equipo_aplicacion_id` | Consultas hacen `COALESCE(equipo_aplicacion_id, equipo_id)`. | Alto | Eliminar en esquema v7; usar `equipo_aplicacion_id`. |
| Tratamientos | `tratamientos` | `maquinaria_id` para equipo aplicado | `equipo_aplicacion_id` o maquinaria general separada | Sigue como fallback en listados, exportador, revisión y maquinaria. | Medio | Revisar: dejar solo si representa maquinaria general distinta del equipo de aplicación. |
| Tratamientos | `tratamientos` | `condiciones` | `condiciones_meteorologicas` | Alta y edición guardan ambas con el mismo valor. | Medio | Eliminar en esquema v7; usar `condiciones_meteorologicas`. |
| Tratamientos | `tratamientos` | `producto_id` | `productos_fito.id` | Ya es estructurado. | Bajo | Mantener; no hay producto texto principal en tratamientos. |
| Tratamientos | `tratamiento_parcelas` | Sin `id` propio | Relación N:M canónica | Tabla puente funciona sin PK; puede limitar edición avanzada. | Bajo | Mantener o añadir `id` si se necesita administración granular. |
| Tratamientos | `tratamientos_documentos` | No legacy | Recetas PDF estructuradas | Se usa para adjuntos y anexos PDF. | Bajo | Mantener. |
| Análisis fitosanitarios | `analisis_fitosanitarios` | `parcelas` texto | Tabla puente futura | Guarda IDs/texto en una columna; el módulo no es eje principal de v7 inicial. | Medio | Revisar más adelante si el módulo crece. |
| Informes | Varias | `cultivo` texto en fertilización/prácticas/cosecha/contabilidad | Resolver por `cultivo_id` o relación decidida | Informes agrupan por texto legacy en varias áreas. | Alto | Adaptar antes de eliminar columnas legacy. |
| PDF oficial | Varias | `fertilizaciones.cultivo`, `practicas_culturales.cultivo`, `cosecha.cultivo`, `cosecha.kg`, `cliente`, `nif_cliente`, `tercero` | Resolver por IDs y campos limpios | PDF lee esos campos directamente o como fallback. | Alto | Adaptar antes de eliminar columnas. |
| Exportación SIEX | Varias | `cultivos.parcela_id`, `fertilizaciones.cultivo`, `practicas_culturales.cultivo`, `cosecha.cultivo`, `cosecha.kg`, `cosecha.cliente` | `cultivo_parcelas`, `cultivo_id`, `cantidad`/`unidad`, `cliente_id` | Excel asistido mezcla estructura y textos legacy. | Alto | Adaptar a esquema v7 antes de retirar columnas. |
| Revisión SIEX | Varias | avisos sobre textos legacy | Reglas contra campos limpios | Todavía distingue texto pendiente de estructurar en fertilización/prácticas/cosecha. | Medio | Actualizar reglas v7 para no esperar texto legacy. |
| Maquinaria | Vista combinada | `id_visual`, `tabla_origen`, `id_real` | No son columnas de DB; son campos UI de combinación | Se usan para mezclar `maquinaria` y `equipos_aplicacion`. | Bajo | Mantener como artefacto de UI o mejorar etiquetas; no afecta esquema. |
| Gastos antiguos | `gastos` | tabla simple solapada | `movimientos_economicos` | Existe en `core/db.py`; no parece el flujo contable principal. | Medio | Revisar si entra en base v7 limpia o queda fuera. |
| Diario | `diario` | funcionalidad simple aislada | Sin equivalente | Existe como tabla separada con `parcela_id`. | Bajo | Mantener solo si se usa; revisar alcance v7 inicial. |

## Dependencias de código a resolver antes de eliminar columnas

- `services/exportacion_siex.py` usa `cultivos.parcela_id` para cultivos asociados a parcelas y lee textos legacy en fertilización, prácticas y cosecha.
- `services/cuadernopro_pdf.py` lee `fertilizaciones.cultivo`, `practicas_culturales.cultivo`, `cosecha.cultivo`, `cosecha.kg`, `cosecha.cliente`, `cosecha.nif_cliente` y `movimientos_economicos.tercero`.
- `modules/informes.py` agrupa por `cultivo` textual en contabilidad, fertilización, prácticas y cosecha.
- `modules/revision_siex.py` todavía trata `cultivo` textual como pendiente de estructurar en fertilización, prácticas y cosecha.
- `modules/parcelas.py` y partes del PDF/exportador calculan cultivo asociado desde `cultivos.parcela_id`.
- `modules/tratamientos.py` conserva fallbacks para `fecha`, `problema`, `aplicador`, `equipo_id`, `maquinaria_id` y `condiciones`.

## Módulos con más riesgo

1. PDF oficial y exportación SIEX, porque son consumidores transversales y aún leen legacy.
2. Cosecha, porque necesita decidir `cliente_id` y sustituir `kg` por `cantidad` + `unidad`.
3. Contabilidad, porque `tercero`/`nif_tercero` se usan en alta, listados, informes, pendientes y facturas.
4. Cultivos/parcelas, porque retirar `cultivos.parcela_id` obliga a adaptar todos los consumidores a `cultivo_parcelas`.
5. Tratamientos, por la unificación de fecha, plaga, aplicador y equipo.
