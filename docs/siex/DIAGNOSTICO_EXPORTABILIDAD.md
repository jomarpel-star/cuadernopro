# Diagnóstico de exportabilidad SIEX/CUE asistida

Este documento resume qué datos de CuadernoPro pueden prepararse hoy para una futura exportación asistida SIEX/CUE y qué falta antes de considerar fiable un archivo estructurado. No define un formato oficial SIEX/CUE, no implementa exportador, no modifica la base de datos y no presupone conexión externa.

Fuentes revisadas:

- `core/db.py`, especialmente `crear_tablas()` y columnas añadidas por migraciones internas.
- Esquema real de `cuadernopro.db`.
- Módulos que guardan datos reales: explotación, campañas, parcelas, cultivos, tratamientos, fertilización, prácticas culturales, cosecha, maquinaria, terceros, contabilidad, recetas y facturas.
- Documentación interna en `docs/siex/`: `README_SIEX.md`, `MATRIZ_CUADERNOPRO_SIEX.md`, `CAMPOS_PENDIENTES_SIEX.md`, `PLAN_INTEGRACION_SIEX.md` y `FORMATO_EXCEL_ASISTIDO.md`.

Nota posterior: ya se ha iniciado infraestructura para importar catálogos SIEX internos mediante `siex_catalogos`, `siex_catalogos_items`, `services/siex_catalogos.py` y `scripts/importar_catalogos_siex.py`. Esta infraestructura es solo local y no implica conexión externa ni uso automático en formularios.

## Lectura del esquema actual

El modelo actual ya separa bien varias entidades principales:

- Explotación: tabla `explotacion`.
- Campañas: tabla `campanas`.
- Parcelas SIGPAC: tabla `parcelas`.
- Cultivos: tabla `cultivos`, vinculada a `parcelas` mediante `parcela_id`.
- Tratamientos: tabla `tratamientos`, vinculada a `campanas`, `productos_fito`, `cultivos`, `personas`, `equipos_aplicacion` y parcelas mediante `tratamiento_parcelas`.
- Recetas PDF: tabla `tratamientos_documentos`.
- Fertilización: tabla `fertilizaciones`, con parcelas mediante `fertilizacion_parcelas`.
- Prácticas culturales: tabla `practicas_culturales`, con parcelas mediante `practica_parcelas`.
- Cosecha: tabla `cosecha`, con parcelas mediante `cosecha_parcelas`.
- Maquinaria: tablas `maquinaria` y `equipos_aplicacion`.
- Terceros: tablas `clientes` y `proveedores`.
- Contabilidad y facturas: `movimientos_economicos`, `movimientos_economicos_lineas_iva` y `movimientos_economicos_documentos`.

Limitaciones estructurales relevantes:

- `cultivos` no tiene `campana_id`.
- `cultivos` no tiene superficie propia por cultivo.
- `fertilizaciones.cultivo`, `practicas_culturales.cultivo` y `cosecha.cultivo` son texto, no `cultivo_id`.
- No existen campos de trazabilidad de exportación asistida como `exportado_siex`, `fecha_exportacion`, `estado_exportacion` o `lote_exportacion`.
- No existen catálogos internos SIEX/CUE de cultivos, actuaciones, unidades, labores, tipos de fertilización o destinos.
- La tabla `parcelas` tiene referencia SIGPAC y GeoJSON cacheado, pero no `uso_sigpac`.

## Estado por área

| Área | Exportable ahora | Calidad del dato | Faltan campos | Problemas de estructura | Prioridad |
| --- | --- | --- | --- | --- | --- |
| Explotación | Parcial | Media | Confirmar identificador oficial REA/REGEA/REGEPA/SIEX; posible código de tipo/orientación normalizado | Hay varios campos candidatos de identificación; responsable y asesor están como campos directos y también pueden existir en `personas` | Alta |
| Parcelas SIGPAC | Sí | Alta | `uso_sigpac` si fuera exigido; criterio de geometría exportable | No hay relación parcela-campaña; la campaña sería contexto del paquete | Media |
| Cultivos | Parcial | Media | `codigo_cultivo_siex`, `campana_id`, superficie propia por cultivo/campaña | Cultivo depende de `parcela_id`; no hay histórico por campaña ni superficie específica | Alta |
| Tratamientos | Sí | Alta | Códigos normalizados de motivo/plaga si se exigen; unidades normalizadas de dosis/caldo | Modelo bastante estructurado, pero dosis es texto y conviven campos legacy de equipo/aplicador | Alta |
| Recetas PDF | Parcial | Media | Criterio de obligatoriedad y anexado en ZIP | Tabla preparada, pero puede no haber recetas cargadas en la base actual | Media |
| Fertilización | Parcial | Baja | `cultivo_id`, `codigo_actuacion_siex`, `unidad_normalizada`, posible catálogo de producto fertilizante | El cultivo se guarda como texto; unidades y tipos son locales | Alta |
| Prácticas culturales | Parcial | Media | `cultivo_id`, `codigo_actuacion_siex`, catálogo de labores | El cultivo se guarda como texto; labor es catálogo local no oficial | Alta |
| Cosecha | Parcial | Media | `cultivo_id`, unidad normalizada, destino normalizado si procede | Cultivo y cliente se guardan como texto; unidad kg está implícita en `kg` | Media |
| Maquinaria | Sí | Media | Matrícula si fuera necesaria; normalización de tipo | `maquinaria` y `equipos_aplicacion` son tablas separadas; ROMA existe en ambas | Baja |
| Documentos | Parcial | Media | Criterio de inclusión de anexos, manifest del ZIP, relación documental por área | Recetas y facturas están estructuradas por tablas distintas; falta paquete ZIP y trazabilidad local | Media |
| Contabilidad/facturas | Parcial | Media | Criterio de si entra o no en exportación SIEX/CUE asistida | Es útil como contexto y anexos, pero no parece núcleo agronómico SIEX/CUE | Baja |

## Observación sobre datos actuales

En la base revisada hay datos suficientes para probar una revisión y un Excel preliminar: explotación, campañas, 18 parcelas, 18 cultivos, 6 tratamientos, 18 prácticas culturales, 1 cosecha, maquinaria/equipos, clientes/proveedores y movimientos contables. También existen documentos de facturas en `movimientos_economicos_documentos`.

No hay fertilizaciones registradas actualmente y no hay recetas PDF en `tratamientos_documentos`. Esto no bloquea el diseño del exportador, pero sí limita una prueba real completa de esas pestañas.

## Campos que probablemente faltan para exportación asistida

### A) Campos críticos

- Identificador oficial de explotación: REA, REGEA, REGEPA, SIEX u otro código aplicable según comunidad autónoma.
- `codigo_cultivo_siex` o equivalente interno mapeable para cultivos.
- Códigos normalizados de actuaciones/labores para tratamientos, fertilización y prácticas culturales.
- Unidades normalizadas para dosis, caldo, cantidad fertilizante, superficie y cosecha.
- `campana_id` en `cultivos` si se necesita cultivo por campaña.
- Superficie propia por cultivo/campaña.
- `cultivo_id` estructurado en `fertilizaciones`.
- `cultivo_id` estructurado en `practicas_culturales`.
- `cultivo_id` estructurado en `cosecha`.
- `codigo_actuacion_siex` en fertilización y prácticas culturales, o una tabla de mapeo equivalente.

### B) Campos recomendables

- `uso_sigpac` en parcelas si algún formato lo requiere.
- Código normalizado de variedad, sistema de cultivo o secano/regadío si procede.
- Destino normalizado de cosecha.
- Producto fertilizante normalizado o tabla de fertilizantes si se confirma necesidad.
- Catálogo interno de motivos/plagas para tratamientos.
- Fuente única para equipo de aplicación en tratamientos, consolidando `equipo_id`, `equipo_aplicacion_id` y `maquinaria_id`.
- Relación más clara entre asesor/responsable y `personas`, si se quiere evitar duplicar datos en `explotacion`.
- Matrícula en maquinaria si fuera necesaria.
- Versión de CuadernoPro incluida en el paquete exportable.

### C) Campos administrativos

- Confirmación del identificador oficial de explotación que debe usarse por comunidad autónoma.
- Confirmación de plantillas admitidas, si existen.
- Confirmación de catálogos oficiales aplicables.
- Confirmación de si los anexos PDF deben incluirse, referenciarse o excluirse.
- Confirmación de si contabilidad/facturas forman parte de la exportación asistida o solo del contexto documental.
- Procedimiento de revisión por asesor/agricultor autorizado.

### D) Campos técnicos de trazabilidad

Estos campos no existen hoy y no deben confundirse con envío oficial. Si se añaden en el futuro, deberían registrar solo exportaciones locales asistidas:

- `exportado_siex` o mejor `exportado_asistido_siex`.
- `fecha_exportacion`.
- `estado_exportacion`.
- `lote_exportacion`.
- Identificador/hash del Excel generado.
- Identificador/hash del ZIP generado.
- Usuario local o responsable de generación, si CuadernoPro incorpora usuarios.
- Resumen de validación asociado al lote.
- Ruta local del paquete exportable.

## Datos ya razonablemente preparados

- Referencia SIGPAC: `provincia_sigpac`, `municipio_sigpac`, `agregado_sigpac`, `zona_sigpac`, `poligono`, `parcela`, `recinto`, `superficie_sigpac` y cache GeoJSON.
- Campañas: `campanas` permite filtrar tratamientos, fertilizaciones, prácticas, cosecha, contabilidad y análisis.
- Tratamientos fitosanitarios: fechas, campaña, producto, número de registro mediante `productos_fito.registro`, cultivo, parcelas, superficie tratada, aplicador, equipo, eficacia, plazo de seguridad y observaciones.
- Eficacia B/R/M: `tratamientos.eficacia` ya está preparada para valores normalizados locales.
- Relación tratamientos-parcelas: `tratamiento_parcelas`.
- Recetas PDF: `tratamientos_documentos` tiene metadatos útiles (`ruta_relativa`, `sha256`, `size_bytes`, `created_at`, `updated_at`).
- Maquinaria y equipos: `maquinaria.numero_roma` y `equipos_aplicacion.numero_roma` existen.
- Facturas/documentos: `movimientos_economicos_documentos` tiene metadatos y hash.
- Clientes/proveedores: tienen NIF, contacto, dirección, activo y timestamps, útiles para contexto y revisión.
- Prácticas/cosecha/fertilización: tienen `campana_id` y tablas intermedias de parcelas, aunque algunas relaciones de cultivo estén como texto.

## Normalizaciones necesarias antes de exportar

Todo lo siguiente queda pendiente de confirmar con documentación oficial o criterios autonómicos. No se deben inventar códigos.

- Catálogo de cultivos y variedades.
- Catálogo de labores/actuaciones.
- Catálogo de unidades.
- Tipos de fertilización.
- Métodos de aplicación de fertilizantes.
- Motivos/plagas de tratamientos.
- Productos fitosanitarios: confirmar número de registro, materia activa y formato admitido.
- Productos fertilizantes: confirmar si requieren catálogo, composición o códigos.
- Sistema de cultivo y secano/regadío.
- Destinos de cosecha.
- Tipos de maquinaria/equipos si se requieren códigos.
- Formato de superficies y decimales.
- Formato de fechas.
- Identificadores oficiales de explotación, titular, asesor, aplicador y prestador.

## Orden recomendado de desarrollo

### Fase 1: Excel preliminar con datos actuales

- Generar Excel asistido con las pestañas definidas en `FORMATO_EXCEL_ASISTIDO.md`.
- Usar los datos existentes sin cambiar el esquema.
- Marcar campos no normalizados como pendientes.
- Incluir pestaña de validación con avisos generados por `Revisión SIEX`.

### Fase 2: Mejorar cultivos

- Añadir o preparar modelo para campaña por cultivo.
- Añadir superficie propia por cultivo/campaña.
- Añadir campo o tabla de mapeo para código normalizado de cultivo.
- Mantener compatibilidad con cultivos actuales vinculados a parcela.

### Fase 3: Estructurar cultivo en actuaciones

- Sustituir o complementar texto de cultivo en `fertilizaciones` por `cultivo_id`.
- Sustituir o complementar texto de cultivo en `practicas_culturales` por `cultivo_id`.
- Sustituir o complementar texto de cultivo en `cosecha` por `cultivo_id`.
- Mantener texto legacy para compatibilidad y migración progresiva.

### Fase 4: Catálogos internos SIEX/CUE

- Crear catálogos internos de cultivos, actuaciones, unidades, labores, tipos de fertilización y destinos.
- Permitir mapeo entre valores actuales y códigos confirmados.
- No activar códigos hasta confirmar documentación oficial.

### Fase 5: Trazabilidad de exportaciones

- Registrar lotes locales de exportación asistida.
- Guardar fecha, campaña, alcance, estado, resumen de validación y hash de archivos.
- Diferenciar claramente exportación local asistida de presentación oficial.

### Fase 6: ZIP asistido

- Generar ZIP con Excel, JSON interno, CSV si procede y PDFs seleccionados.
- Incluir manifest del paquete.
- Incluir resumen de validación.
- No enviar ni conectar con sistemas externos.

## Conclusión

Qué se puede exportar ya:

- Un Excel preliminar de revisión con explotación, campañas, parcelas SIGPAC, tratamientos, prácticas culturales, cosecha, maquinaria, clientes/proveedores, movimientos y documentos.
- Tratamientos fitosanitarios con buen nivel estructural, incluyendo producto, registro, parcelas, cultivo, superficie, eficacia B/R/M y equipo.
- Parcelas SIGPAC con una base sólida de referencia alfanumérica y geometría cacheada si está disponible.
- Documentos como inventario de recetas/facturas si existen en sus tablas.

Qué se puede exportar parcialmente:

- Cultivos, porque faltan campaña propia, superficie propia y código normalizado.
- Fertilización, porque el cultivo es texto, las unidades son locales y no hay datos actuales para probar una exportación completa.
- Prácticas culturales, porque el cultivo es texto y las labores no están en catálogo oficial.
- Cosecha, porque cultivo y cliente son texto, la unidad es implícita y el destino puede requerir normalización.
- Contabilidad/facturas, porque son útiles como contexto/anexos pero no deberían tratarse como núcleo SIEX/CUE sin confirmación.

Qué no debería exportarse todavía como oficial:

- Ningún archivo que se presente como formato SIEX/CUE oficial.
- Códigos de cultivo, labores, actuaciones, unidades o destinos inventados.
- Estados de envío o sincronización con SIEX/CUE.
- Paquetes con apariencia de presentación oficial.
- Conexión directa, servicios web, certificados o comunicación administrativa.

Qué falta antes de decir que CuadernoPro genera un archivo SIEX/CUE fiable:

- Confirmar identificadores oficiales y catálogos aplicables.
- Normalizar cultivos, actuaciones y unidades.
- Resolver campaña/superficie por cultivo.
- Estructurar `cultivo_id` en fertilización, prácticas culturales y cosecha.
- Añadir trazabilidad local de exportaciones asistidas.
- Validar el Excel/ZIP contra una plantilla o criterio oficial confirmado por la administración o el asesor responsable.
