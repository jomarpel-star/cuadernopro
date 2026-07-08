# Formato preliminar de Excel para exportación asistida SIEX/CUE

Este documento define el primer formato interno de CuadernoPro para un Excel de exportación asistida SIEX/CUE.

No es todavía un formato oficial SIEX/CUE. Es una propuesta preliminar para ordenar la información local, facilitar la revisión por asesor o agricultor autorizado y preparar paquetes de trabajo que puedan adaptarse más adelante a plantillas oficiales, catálogos o formatos autonómicos si se confirman.

CuadernoPro no enviará nada automáticamente a SIEX/CUE. El Excel servirá para revisión y preparación. La tramitación, carga o presentación oficial deberá realizarla el agricultor, asesor o entidad autorizada mediante los canales oficiales.

## Estructura del libro Excel

Pestañas propuestas:

1. `Resumen`
2. `Validación`
3. `Explotación`
4. `Parcelas_SIGPAC`
5. `Cultivos`
6. `Tratamientos`
7. `Fertilización`
8. `Prácticas_Culturales`
9. `Cosecha`
10. `Maquinaria`
11. `Documentos`

## 1. Resumen

Objetivo: ofrecer una vista general del paquete generado para una campaña y una explotación.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `fecha_exportacion` | Fecha de generación local del Excel | Definir formato final | No implica envío telemático. |
| `campaña` | `campanas.nombre` | Confirmar formato de campaña | Se obtiene de la campaña seleccionada. |
| `explotación` | `explotacion.nombre_explotacion` | Confirmar obligatoriedad | Puede estar vacío en instalaciones antiguas. |
| `titular` | `explotacion.titular` | Validar formato | Dato principal de titular. |
| `nif` | `explotacion.nif` | Validar formato | Identificación fiscal local. |
| `número de parcelas` | Conteo de `parcelas.id` | Ninguno inicial | Puede filtrarse en el futuro por campaña si se modela esa relación. |
| `número de cultivos` | Conteo de `cultivos.id` | Relación cultivo/campaña | Actualmente los cultivos no tienen `campana_id`. |
| `número de tratamientos` | Conteo de `tratamientos.id` por `campana_id` | Ninguno inicial | Actuación por campaña. |
| `número de fertilizaciones` | Conteo de `fertilizaciones.id` por `campana_id` | Ninguno inicial | Actuación por campaña. |
| `número de prácticas culturales` | Conteo de `practicas_culturales.id` por `campana_id` | Ninguno inicial | Actuación por campaña. |
| `número de cosechas` | Conteo de `cosecha.id` por `campana_id` | Ninguno inicial | Actuación por campaña. |
| `número de documentos anexos` | Conteo de `tratamientos_documentos` y `movimientos_economicos_documentos` | Definir alcance de anexos | Incluir solo documentos seleccionados para el paquete asistido. |
| `versión de CuadernoPro` | No existe campo/versionado interno estable | Pendiente | Podría informarse manualmente o desde una futura constante de versión. |
| `observaciones` | Campo generado en exportación | Definir contenido | Para avisos generales del paquete. |

## 2. Validación

Objetivo: concentrar errores, avisos e información útil antes de usar el Excel como paquete de revisión.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `área` | Nombre del módulo o pestaña | Normalizar nombres de áreas | Ejemplo: Parcelas, Cultivos, Tratamientos. |
| `registro_id` | `id` de la tabla afectada | Definir formato para registros agregados | Puede quedar vacío para problemas generales. |
| `gravedad` | Resultado de validación futura | Catálogo local: Error, Aviso, Info | `Error` bloquearía la exportación asistida si se decide así. |
| `campo` | Nombre de columna afectada | Ninguno inicial | Debe coincidir con el Excel cuando sea posible. |
| `problema` | Mensaje generado por validación futura | Redacción uniforme | Debe ser entendible por asesor/agricultor. |
| `recomendación` | Mensaje generado por validación futura | Redacción uniforme | Debe indicar una acción concreta. |
| `bloquea_exportación` | Resultado booleano de validación futura | Definir criterio | Valores sugeridos: `sí` / `no`. |

Gravedades:

- `Error`
- `Aviso`
- `Info`

Ejemplos iniciales:

- Parcela sin superficie SIGPAC.
- Tratamiento sin eficacia.
- Cultivo sin código normalizado.
- Fertilización sin unidad normalizada.
- Práctica cultural con cultivo como texto pendiente de normalizar.

## 3. Explotación

Objetivo: exportar los datos principales de titular, explotación, responsable y asesor.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `explotacion_id` | `explotacion.id` | Ninguno inicial | Identificador interno. |
| `nombre_explotacion` | `explotacion.nombre_explotacion` | Confirmar obligatoriedad | Nombre local. |
| `titular` | `explotacion.titular` | Validar formato | Dato principal. |
| `nif` | `explotacion.nif` | Validar formato | Identificación fiscal. |
| `dirección` | `explotacion.direccion` | Normalizar dirección postal | Puede requerir separación en campos oficiales. |
| `municipio` | `explotacion.localidad` | Normalizar municipio | No confundir con municipio SIGPAC de parcelas. |
| `provincia` | `explotacion.provincia` | Normalizar provincia/código | Texto local. |
| `teléfono` | `explotacion.telefono` | Validar formato | Dato de contacto. |
| `email` | `explotacion.email` | Validar formato | Dato de contacto. |
| `identificador_REA_REGEA_REGEPA` | `explotacion.registro_explotacion`, `codigo_regea`, `codigo_regepa` | Pendiente de confirmar | Debe confirmarse qué identificador oficial aplica. |
| `responsable` | `responsable_nombre`, `responsable_nif`, `responsable_telefono` | Definir formato compuesto | Puede separarse en columnas futuras. |
| `asesor` | `asesor_nombre`, `asesor_nif`, `asesor_telefono` | Definir formato compuesto | Puede cruzarse con `personas`. |
| `número_asesor` | `explotacion.asesor_numero_registro` o `personas.numero_asesor` | Resolver fuente preferente | Pendiente de confirmar. |
| `observaciones` | `explotacion.observaciones` | Ninguno inicial | Texto libre. |

## 4. Parcelas_SIGPAC

Objetivo: listar parcelas y recintos con referencia SIGPAC y datos básicos para revisión.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `parcela_id` | `parcelas.id` | Ninguno inicial | Identificador interno. |
| `nombre` | `parcelas.nombre` | Ninguno inicial | Alias local. |
| `campaña` | `campanas.nombre` seleccionada | Relación parcela/campaña no estructurada | Se incluiría como contexto del paquete, no como dato propio de parcela. |
| `provincia_sigpac` | `parcelas.provincia_sigpac` | Confirmar codificación | Código SIGPAC. |
| `municipio_sigpac` | `parcelas.municipio_sigpac` | Confirmar codificación | Código SIGPAC. |
| `agregado` | `parcelas.agregado_sigpac` | Confirmar formato | Valor local por defecto 0. |
| `zona` | `parcelas.zona_sigpac` | Confirmar formato | Valor local por defecto 0. |
| `polígono` | `parcelas.poligono` | Confirmar formato | Texto local. |
| `parcela` | `parcelas.parcela` | Confirmar formato | Texto local. |
| `recinto` | `parcelas.recinto` | Confirmar formato | Texto local. |
| `superficie_sigpac` | `parcelas.superficie_sigpac` | Validar obligatoriedad | Hectáreas. |
| `uso_sigpac` | No existe actualmente | Pendiente si se requiere | No se exportaría inicialmente. |
| `cultivo_asociado` | `cultivos.parcela_id`, `cultivos.especie`, `variedad`, `sistema` | Relación cultivo/campaña | Puede haber varios cultivos por parcela. |
| `geometría_disponible` | `parcelas.geometry`, `sigpac_geojson`, `sigpac_geojson_estado` | Definir criterio | Sugerido: `sí` si existe GeoJSON válido o geometría local. |
| `observaciones` | `parcelas.observaciones` | Ninguno inicial | Texto libre. |

## 5. Cultivos

Objetivo: revisar cultivos declarados en CuadernoPro y preparar su normalización.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `cultivo_id` | `cultivos.id` | Ninguno inicial | Identificador interno. |
| `campaña` | `campanas.nombre` seleccionada | Relación campaña/cultivo pendiente | Actualmente `cultivos` no tiene `campana_id`. |
| `cultivo` | `cultivos.especie` | Código normalizado de cultivo | Requiere catálogo oficial antes de usar códigos SIEX/CUE. |
| `variedad` | `cultivos.variedad` | Confirmar catálogo/formato | Texto libre actual. |
| `año_plantación` | `cultivos.ano_plantacion` | Ninguno inicial | Campo numérico. |
| `superficie` | Inferible desde `parcelas.superficie_sigpac` o `superficie_cultivada` | Superficie propia por cultivo pendiente | No existe campo de superficie en `cultivos`. |
| `parcelas_asociadas` | `cultivos.parcela_id` -> `parcelas` | Formato de listado | Una fila de cultivo apunta a una parcela. |
| `codigo_cultivo_siex` | No existe actualmente | Pendiente crítico | No inventar códigos. |
| `observaciones` | No existe en `cultivos` | Pendiente si se requiere | Podría quedar vacío inicialmente. |

Pendientes específicos:

- Código normalizado de cultivo.
- Relación campaña/cultivo si se requiere histórico por campaña.
- Superficie propia por cultivo si la superficie de parcela no basta.

## 6. Tratamientos

Objetivo: exportar tratamientos fitosanitarios con datos suficientes para revisión técnica.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `tratamiento_id` | `tratamientos.id` | Ninguno inicial | Identificador interno. |
| `campaña` | `tratamientos.campana_id` -> `campanas.nombre` | Ninguno inicial | Actuación por campaña. |
| `fecha_inicio` | `tratamientos.fecha_inicio` | Validar obligatoriedad | Usar `fecha` legacy solo como respaldo. |
| `fecha_fin` | `tratamientos.fecha_fin` | Validar obligatoriedad | Debe ser igual o posterior a inicio. |
| `cultivo` | `tratamientos.cultivo_id` -> `cultivos` | Código de cultivo pendiente | Exportar etiqueta legible para revisión. |
| `parcelas` | `tratamiento_parcelas.parcela_id` -> `parcelas` | Formato de listado | Incluir referencia SIGPAC resumida. |
| `producto` | `tratamientos.producto_id` -> `productos_fito.nombre` | Catálogo/registro oficial | Producto local. |
| `número_registro_producto` | `productos_fito.registro` | Validar formato | Campo clave para fitosanitarios. |
| `materia_activa` | `productos_fito.materia_activa` | Confirmar uso | Campo disponible. |
| `plaga_motivo` | `tratamientos.plaga`, `problema`, `justificacion` | Catálogo de motivos | Texto libre actual. |
| `dosis` | `tratamientos.dosis` | Unidad/formato pendiente | Texto libre actual. |
| `caldo` | `tratamientos.caldo` | Unidad normalizada | Litros de caldo en interfaz. |
| `superficie_tratada` | `tratamientos.superficie_tratada`, `tratamiento_parcelas.superficie` | Confirmar total vs detalle por parcela | Campo total y posible detalle. |
| `aplicador` | `tratamientos.aplicador_id` -> `personas`; `tratamientos.aplicador` | Identificación aplicador | Puede requerir NIF/carnet. |
| `equipo_aplicación` | `equipo_aplicacion_id`, `equipo_id` -> `equipos_aplicacion` | Resolver campo preferente | Conviven campos legacy y actuales. |
| `eficacia` | `tratamientos.eficacia` | Normalizar a B/R/M/vacío | Exportar `B`, `R`, `M` o vacío. |
| `plazo_seguridad` | `tratamientos.plazo_seguridad`; `productos_fito.plazo_seguridad` | Fuente preferente | Priorizar tratamiento si está informado. |
| `receta_pdf` | `tratamientos_documentos` tipo `receta` | Definir si se enlaza o anexa | Podría indicar número de PDFs o ruta relativa. |
| `observaciones` | `tratamientos.observaciones` | Ninguno inicial | Texto libre. |

Regla de eficacia:

- `B`: Buena.
- `R`: Regular.
- `M`: Mala.
- Vacío: sin evaluar.

## 7. Fertilización

Objetivo: revisar fertilizaciones por campaña, cultivo y parcelas.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `fertilizacion_id` | `fertilizaciones.id` | Ninguno inicial | Identificador interno. |
| `campaña` | `fertilizaciones.campana_id` -> `campanas.nombre` | Ninguno inicial | Actuación por campaña. |
| `fecha` | `fertilizaciones.fecha` | Validar obligatoriedad | Fecha de actuación. |
| `cultivo` | `fertilizaciones.cultivo` | Cultivo estructurado pendiente | Actualmente texto agrupado. |
| `parcelas` | `fertilizacion_parcelas.parcela_id` -> `parcelas` | Formato de listado | Relación estructurada disponible. |
| `producto` | `fertilizaciones.producto` | Catálogo si procede | Texto libre. |
| `tipo_fertilizante` | `fertilizaciones.tipo` | Catálogo oficial pendiente | Opciones locales. |
| `cantidad` | `fertilizaciones.cantidad` | Validar unidad | Campo numérico. |
| `unidad` | `fertilizaciones.unidad` | Unidades normalizadas | Actualmente `kg` o `litros`. |
| `superficie` | `fertilizaciones.superficie` | Confirmar criterio | Hectáreas afectadas. |
| `observaciones` | `fertilizaciones.observaciones` | Ninguno inicial | Texto libre. |
| `codigo_actuacion_siex` | No existe actualmente | Pendiente crítico | No inventar códigos. |
| `unidad_normalizada` | No existe actualmente | Pendiente crítico | Derivar solo cuando haya catálogo confirmado. |

Pendientes específicos:

- Unidades normalizadas.
- Códigos oficiales de actuación.
- Cultivo estructurado si actualmente está como texto.

## 8. Prácticas_Culturales

Objetivo: revisar labores y prácticas culturales por campaña.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `practica_id` | `practicas_culturales.id` | Ninguno inicial | Identificador interno. |
| `campaña` | `practicas_culturales.campana_id` -> `campanas.nombre` | Ninguno inicial | Actuación por campaña. |
| `fecha` | `practicas_culturales.fecha` | Validar obligatoriedad | Fecha de labor. |
| `labor` | `practicas_culturales.labor` | Catálogo oficial de labores/actuaciones | Lista local. |
| `cultivo` | `practicas_culturales.cultivo` | Cultivo estructurado pendiente | Actualmente texto agrupado. |
| `parcelas` | `practica_parcelas.parcela_id` -> `parcelas` | Formato de listado | Relación estructurada disponible. |
| `superficie` | `practicas_culturales.superficie` | Confirmar criterio | Hectáreas afectadas. |
| `maquinaria` | `practicas_culturales.maquinaria_id` -> `maquinaria` | Formato de descripción | Puede usar nombre/tipo/marca/modelo. |
| `prestador` | `practicas_culturales.proveedor_id` -> `proveedores.nombre` | Identificación si procede | Prestador externo opcional. |
| `observaciones` | `practicas_culturales.observaciones` | Ninguno inicial | Texto libre. |
| `codigo_actuacion_siex` | No existe actualmente | Pendiente crítico | No inventar códigos. |

Pendientes específicos:

- Catálogo oficial de labores/actuaciones.
- Cultivo estructurado si actualmente está como texto.

## 9. Cosecha

Objetivo: revisar registros de cosecha por campaña, cultivo y parcelas.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `cosecha_id` | `cosecha.id` | Ninguno inicial | Identificador interno. |
| `campaña` | `cosecha.campana_id` -> `campanas.nombre` | Ninguno inicial | Actuación por campaña. |
| `fecha` | `cosecha.fecha` | Validar obligatoriedad | Fecha de cosecha. |
| `cultivo` | `cosecha.cultivo` | Cultivo estructurado pendiente | Actualmente texto agrupado. |
| `parcelas` | `cosecha_parcelas.parcela_id` -> `parcelas`; `cosecha.parcelas` legacy | Formato de listado | Usar relación estructurada cuando exista. |
| `cantidad` | `cosecha.kg` | Confirmar unidad | Cantidad en kg. |
| `unidad` | Valor derivado `kg` | Unidad normalizada | Añadir aunque no exista campo actual. |
| `destino` | `cosecha.destino` | Destino normalizado si procede | Texto libre. |
| `cliente` | `cosecha.cliente`, `nif_cliente` | Relación con clientes pendiente | Existe como texto, no `cliente_id`. |
| `observaciones` | `cosecha.observaciones` | Ninguno inicial | Texto libre. |

Pendientes específicos:

- Unidades normalizadas.
- Destino normalizado si procede.
- Cultivo estructurado si se requiere trazabilidad por código.

## 10. Maquinaria

Objetivo: revisar maquinaria general y equipos de aplicación usados en la explotación.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `id_visual` | Construido por `modules/maquinaria.py` | Ninguno inicial | `MAQ-*` para maquinaria general y `EQ-*` para equipos de aplicación. |
| `origen` | Construido por `modules/maquinaria.py` | Ninguno inicial | `Maquinaria` o `Equipo aplicación`. |
| `tipo` | `maquinaria.tipo`, `equipos_aplicacion.tipo` | Catálogo si procede | Texto libre. |
| `marca` | `maquinaria.marca`, `equipos_aplicacion.marca` | Ninguno inicial | Texto libre. |
| `modelo` | `maquinaria.modelo`, `equipos_aplicacion.modelo` | Ninguno inicial | Texto libre. |
| `matrícula` | No existe actualmente | Pendiente si se requiere | No exportar inicialmente salvo alta futura. |
| `numero_roma` | `maquinaria.numero_roma`, `equipos_aplicacion.numero_roma` | Validar formato | Número de inscripción ROMA. |
| `descripción` | Composición local nombre/marca/modelo/tipo | Definir formato | Puede replicar la descripción visual. |
| `observaciones` | `maquinaria.observaciones`, `equipos_aplicacion.observaciones` | Ninguno inicial | Texto libre. |

Distinción de origen:

- `MAQ-*`: maquinaria general de la tabla `maquinaria`.
- `EQ-*`: equipos de aplicación de la tabla `equipos_aplicacion`.

## 11. Documentos

Objetivo: inventariar documentos anexos que podrían incluirse en un paquete ZIP de exportación asistida.

Columnas propuestas:

| Columna | Fuente actual en CuadernoPro | Pendientes / normalización | Observaciones |
| --- | --- | --- | --- |
| `documento_id` | `tratamientos_documentos.id`, `movimientos_economicos_documentos.id` | Prefijar origen si hay colisiones | Ejemplo futuro: `REC-1`, `FAC-1`. |
| `tipo_documento` | `tipo_documento` | Catálogo local | `receta`, `factura` u otros futuros. |
| `área` | Derivado por origen | Definir valores | Tratamientos, Contabilidad, etc. |
| `registro_id` | `tratamiento_id` o `movimiento_id` | Ninguno inicial | Registro relacionado. |
| `nombre_original` | `nombre_original` | Ninguno inicial | Nombre del archivo subido. |
| `ruta_relativa` | `ruta_relativa` | Revisar privacidad | Ruta interna local. |
| `sha256` | `sha256` | Ninguno inicial | Huella para trazabilidad. |
| `tamaño` | `size_bytes` | Formato legible opcional | Guardar bytes o texto formateado. |
| `observaciones` | Campo generado en exportación | Definir contenido | Para incidencias o notas del anexo. |

Incluir inicialmente:

- Recetas PDF de tratamientos desde `tratamientos_documentos`.
- Facturas PDF de movimientos contables desde `movimientos_economicos_documentos`.

Para exportación asistida, los PDFs podrían ir dentro de un ZIP junto al Excel. El Excel debería inventariarlos, pero no implica que estén presentados oficialmente.

## Decisiones iniciales

- El primer formato será Excel por facilidad de revisión.
- Más adelante se podrá generar CSV o JSON.
- Los PDFs se incluirán posteriormente en un paquete ZIP.
- No se enviará nada automáticamente a SIEX.
- El asesor/agricultor revisará y tramitará los datos por los canales oficiales.

## Campos que requieren normalización

- Identificador oficial de explotación: REA, REGEA, REGEPA u otro aplicable.
- Códigos normalizados de cultivo.
- Códigos normalizados de actuaciones.
- Unidades normalizadas para fertilización, tratamientos y cosecha.
- Superficie propia por cultivo y campaña.
- Relación estructurada cultivo/campaña.
- Cultivo estructurado en fertilización, prácticas culturales y cosecha.
- Catálogo de labores, motivos y tipos de fertilizante.
- Fuente preferente para equipos de aplicación en tratamientos.
- Versión de CuadernoPro incluida en el paquete.
- Criterio de inclusión de anexos PDF.

## Siguiente paso técnico propuesto

- Crear módulo interno "Revisión SIEX".
- Generar validaciones por campaña.
- Mantener esta fase todavía sin exportación.
- Después añadir botón "Exportar Excel asistido".

