# Matriz inicial CuadernoPro - SIEX/CUE para exportación asistida

Auditoría interna inicial basada en el código y el esquema SQLite actual. Fuentes revisadas: `core/db.py`, `modules/explotacion.py`, `modules/parcelas.py`, `modules/cultivos.py`, `modules/tratamientos.py`, `modules/fertilizacion.py`, `modules/practicas_culturales.py`, `modules/cosecha.py`, `modules/maquinaria.py`, `modules/informes.py`, `services/cuadernopro_pdf.py` y el esquema real de `cuadernopro.db`.

Esta matriz no es una equivalencia oficial SIEX/CUE. La columna "Posible equivalente SIEX/CUE" se interpreta como campo candidato para preparar exportaciones estructuradas, paquetes de trabajo o revisiones del asesor, no como contrato oficial de integración.

No se presupone conexión directa, llamada HTTP, autenticación, certificado ni envío telemático. Cuando el formato, catálogo o requisito oficial no está documentado en el proyecto se marca como "Falta confirmar" o como uso que requiere catálogo oficial.

Estados usados:

- Cubierto: existe dato estructurado en CuadernoPro.
- Parcial: existe dato útil, pero incompleto, no normalizado o indirecto.
- Falta confirmar: el dato existe o se intuye, pero falta especificación oficial SIEX/CUE.
- No existe: no se ha encontrado campo o estructura actual.
- No aplica: no corresponde como dato estructurado de exportación inicial.

Valores de "Uso en exportación asistida":

- Exportable: puede salir en un Excel/CSV/JSON asistido con la estructura actual.
- Requiere normalización: existe dato, pero necesita formato, relación o unidad más consistente antes de exportar.
- Requiere catálogo oficial: no debería exportarse como texto libre sin confirmar catálogo/código admitido.
- Requiere confirmación: falta confirmar formato, obligatoriedad o criterio administrativo.
- No exportar inicialmente: no se incluiría en una primera exportación asistida.

| Area | Dato CuadernoPro | Tabla/Campo actual | Posible equivalente SIEX/CUE | Uso en exportación asistida | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- |
| Explotación / titular | Titular | `explotacion.titular` | Identificacion del titular de explotación | Exportable | Cubierto | Revisar formato y obligatoriedad antes de generar el paquete exportable. |
| Explotación / titular | NIF | `explotacion.nif` | Identificador fiscal del titular | Exportable | Cubierto | Dato estructurado. |
| Explotación / titular | Dirección | `explotacion.direccion`, `localidad`, `codigo_postal`, `provincia` | Domicilio o datos de contacto del titular/explotacion | Requiere normalización | Parcial | Existe dirección postal, pero falta confirmar si SIEX separa domicilio fiscal, explotación o notificaciones. |
| Explotación / titular | Telefono/email | `explotacion.telefono`, `explotacion.email` | Datos de contacto | Exportable | Cubierto | Revisar obligatoriedad y validaciones antes de exportar. |
| Explotación / titular | REA / identificador explotación | `explotacion.registro_explotacion`, `codigo_regea`, `codigo_regepa` | Identificador oficial de explotacion/registro agrario | Requiere normalización | Parcial | Hay varios campos candidatos. Debe confirmarse cuál usar en la exportación asistida para Murcia u otra comunidad. |
| Explotación / titular | Nombre de explotación | `explotacion.nombre_explotacion` | Nombre o denominación de explotación | Requiere confirmación | Falta confirmar | Dato disponible; formato de exportación pendiente de confirmar. |
| Explotación / titular | Tipo/orientacion productiva | `explotacion.tipo_explotacion`, `orientacion_productiva` | Clasificación de explotación | Requiere catálogo oficial | Falta confirmar | Campos libres; requieren catálogo oficial antes de exportar como códigos. |
| Explotación / titular | Asesor | `explotacion.asesor_nombre`, `asesor_nif`, `asesor_numero_registro`, `asesor_telefono`; `personas.rol='Asesor'`, `personas.numero_asesor` | Asesor o técnico vinculado al cuaderno | Requiere confirmación | Parcial | Existe información, pero conviene normalizar la referencia al asesor antes de exportar. |
| Explotación / titular | Responsable | `explotacion.responsable_nombre`, `responsable_nif`, `responsable_telefono`; `personas.rol` | Responsable o representante | Requiere confirmación | Parcial | Falta confirmar rol y formato de identificación para el paquete exportable. |
| Explotación / titular | Personas relacionadas | `personas.nombre`, `nif`, `telefono`, `email`, `rol`, `carnet_fitosanitario`, `fecha_caducidad_carnet`, `numero_asesor` | Personas vinculadas, aplicadores, asesores u operarios | Requiere confirmación | Parcial | Roles locales; revisar contra catálogo o criterio admitido antes de exportar. |
| Campanas | Campana agrícola | `campanas.id`, `nombre`, `fecha_inicio`, `fecha_fin`, `activa` | Periodo/campana declarativa | Exportable | Cubierto | Se usa como eje en tratamientos, fertilización, prácticas, cosecha e informes. |
| Parcelas / SIGPAC | Provincia | `parcelas.provincia`, `provincia_sigpac` | Provincia SIGPAC | Expcódigoe | Cubierto | Existe texto y código. Revisar codificación exacta requerida para el archivo exportable. |
| Parcelas / SIGPAC | Municipio | `parcelas.municipio`, `municipio_sigpac` | Municipio SIGPAC | Expcódigoe | Cubierto | Existe texto y código. |
| Parcelas / SIGPAC | Agregado | `parcelas.agregado_sigpac` | Agregado SIGPAC | Exportable | Cubierto | Campo entero con valor por defecto 0. |
| Parcelas / SIGPAC | Zona | `parcelas.zona_sigpac` | Zona SIGPAC | Exportable | Cubierto | Campo entero con valor por defecto 0. |
| Parcelas / SIGPAC | Poligono | `parcelas.poligono` | Poligono SIGPAC | Exportable | Cubierto | Campo de texto exportable si el formato admitido lo permite. |
| Parcelas / SIGPAC | Parcela | `parcelas.parcela` | Parcela SIGPAC | Exportable | Cubierto | Campo de texto exportable si el formato admitido lo permite. |
| Parcelas / SIGPAC | Recinto | `parcelas.recinto` | Recinto SIGPAC | Exportable | Cubierto | Campo de texto exportable si el formato admitido lo permite. |
| Parcelas / SIGPAC | Superficie SIGPAC | `parcelas.superficie_sigpac` | Superficie oficial de recinto/parcela | Requiere normalización | Cubierto | Campo numerico. |
| Parcelas / SIGPAC | Superficie cultivada | `parcelas.superficie_cultivada` | Superficie declarada/cultivada | Requiere normalización | Falta confirmar | Existe campo, pero su uso en exportación asistida requiere confirmación. |
| Parcelas / SIGPAC | Geometría | `parcelas.geometry`, `sigpac_geojson`, `sigpac_geojson_actualizado`, `sigpac_geojson_estado`, `sigpac_geojson_error` | Geometría SIGPAC o referencia grafica | Requiere normalización | Parcial | Hay caché GeoJSON y estado interno. Falta confirmar si el paquete debe incluir geometría o solo referencia SIGPAC. |
| Parcelas / SIGPAC | Cultivo asociado | `cultivos.parcela_id`; listado por `GROUP_CONCAT` en `modules/parcelas.py` | Cultivo declarado sobre parcela/recinto | Requiere normalización | Parcial | Relación directa con cultivo, pero sin periodo/campaña en `cultivos`; revisar antes de exportar por campaña. |
| Parcelas / SIGPAC | Campana | Sin `campana_id` en `parcelas` | Vinculacion parcela-campana | No exportar inicialmente | No existe | La campaña se aplica a actuaciones, no a la parcela base; no exportar como relación parcela-campaña inicial. |
| Cultivos | Cultivo/especie | `cultivos.especie` | Cultivo declarado | Requiere catálogo oficial | Parcial | Campo libre; requiere código normalizado o catálogo oficial antes de exportar. |
| Cultivos | Variedad | `cultivos.variedad` | Variedad | Requiere catálogo oficial | Cubierto | Campo libre; falta confirmar catálogo o codificación para exportación. |
| Cultivos | Superficie | Sin campo propio en `cultivos`; inferible por `parcelas.superficie_sigpac` o `superficie_cultivada` | Superficie de cultivo | Requiere normalización | Parcial | No hay superficie específica por cultivo. En multicultivo o cambios por campaña sería insuficiente para exportar con precisión. |
| Cultivos | Año plantación | `cultivos.ano_plantacion` | Año de plantación | Exportable | Cubierto | Campo numerico. |
| Cultivos | Campana | Sin `cultivos.campana_id` | Cultivo por campana | No exportar inicialmente | No existe | Los cultivos son maestros por parcela, no histórico por campaña; requiere normalización futura. |
| Cultivos | Parcelas asociadas | `cultivos.parcela_id` | Relación cultivo-parcela/recinto | Exportable | Cubierto | Una fila de cultivo apunta a una parcela. No hay tabla intermedia cultivo-parcelas. |
| Cultivos | Sistema | `cultivos.sistema` | Sistema de cultivo, secano/regadio u otro | Requiere catálogo oficial | Falta confirmar | Campo local usado en etiquetas; requiere catálogo o normalización antes de exportar. |
| Tratamientos fitosanitarios | Campana | `tratamientos.campana_id` | Campana de actuacion fitosanitaria | Exportable | Cubierto | Relación con `campanas`. |
| Tratamientos fitosanitarios | Fecha inicio | `tratamientos.fecha_inicio` | Fecha inicio tratamiento | Exportable | Cubierto | También existe `fecha` legacy. |
| Tratamientos fitosanitarios | Fecha fin | `tratamientos.fecha_fin` | Fecha fin tratamiento | Exportable | Cubierto | Validada frente a campana en interfaz. |
| Tratamientos fitosanitarios | Producto | `tratamientos.producto_id` -> `productos_fito.nombre` | Producto fitosanitario | Requiere catálogo oficial | Cubierto | Producto estructurado en catálogo local; revisar equivalencia oficial antes de exportar. |
| Tratamientos fitosanitarios | Número registro | `productos_fito.registro` | Número de registro de producto fitosanitario | Exportable | Cubierto | Campo disponible en producto. |
| Tratamientos fitosanitarios | Materia activa | `productos_fito.materia_activa` | Materia activa | Requiere confirmación | Cubierto | No estaba en la lista minima, pero existe. |
| Tratamientos fitosanitarios | Dosis | `tratamientos.dosis`; `productos_fito.dosis` como referencia | Dosis aplicada | Requiere normalización | Cubierto | Campo de texto; unidades no normalizadas para exportación. |
| Tratamientos fitosanitarios | Caldo | `tratamientos.caldo` | Volumen de caldo | Requiere normalización | Cubierto | Campo numérico; falta confirmar unidad oficial o formato admitido. |
| Tratamientos fitosanitarios | Plaga/motivo | `tratamientos.plaga`, `problema`, `justificacion` | Motivo/plaga/justificacion de tratamiento | Requiere catálogo oficial | Cubierto | Existen campos, pero requieren catálogo oficial o criterio admitido antes de exportar. |
| Tratamientos fitosanitarios | Superficie tratada | `tratamientos.superficie_tratada`; `tratamiento_parcelas.superficie` | Superficie tratada total o por parcela | Requiere normalización | Parcial | Hay total y tabla relación, pero debe confirmarse criterio por recinto/parcela para el archivo exportable. |
| Tratamientos fitosanitarios | Parcelas tratadas | `tratamiento_parcelas.tratamiento_id`, `parcela_id` | Recintos/parcelas afectados | Exportable | Cubierto | Relación estructurada. |
| Tratamientos fitosanitarios | Cultivo tratado | `tratamientos.cultivo_id` -> `cultivos` | Cultivo afectado | Requiere normalización | Cubierto | Relación estructurada. |
| Tratamientos fitosanitarios | Aplicador | `tratamientos.aplicador_id` -> `personas`; `tratamientos.aplicador` legacy | Aplicador | Requiere normalización | Parcial | Persona tiene NIF y carnet, pero formato y obligatoriedad deben confirmarse antes de exportar. |
| Tratamientos fitosanitarios | Equipo aplicación | `tratamientos.equipo_aplicacion_id`, `equipo_id` -> `equipos_aplicacion`; `maquinaria_id` legacy | Equipo o maquinaria de aplicación | Requiere normalización | Parcial | Conviven campos legacy y actuales; conviene consolidar el origen antes de exportar. |
| Tratamientos fitosanitarios | Eficacia B/R/M | `tratamientos.eficacia` | Evaluacion de eficacia | Exportable | Cubierto | La interfavacíomaliza a B/R/M o vacío. |
| Tratamientos fitosanitarios | Plazo seguridad | `tratamientos.plazo_seguridad`; `productos_fito.plazo_seguridad` | Plazo de seguridad | Exportable | Cubierto | Campo disponible en tratamiento y producto; revisar fuente preferente para exportación. |
| Tratamientos fitosanitarios | Fecha recoleccion segura | `tratamientos.fecha_recoleccion_segura` | Fecha calculada o restriccion de recoleccion | Requiere confirmación | Falta confirmar | Campo existe; uso en exportación asistida pendiente de confirmar. |
| Tratamientos fitosanitarios | Receta PDF | `tratamientos_documentos.tipo_documento='receta'`, `ruta_relativa`, `sha256`, `created_at`, `updated_at` | Anexo documental receta | Exportable | Cubierto | Gestionado por `services/recetas.py`; incluir solo si el paquete asistido requiere anexos. |
| Fertilización | Campana | `fertilizaciones.campana_id` | Campana de actuacion | Exportable | Cubierto | Relación con `campanas`. |
| Fertilización | Fecha | `fertilizaciones.fecha` | Fecha de fertilización | Exportable | Cubierto | Validada frente a campana. |
| Fertilización | Producto/fertilizante | `fertilizaciones.producto` | Producto fertilizante | Requiere catálogo oficial | Cubierto | Campo libre; requiere catálogo oficial o normalización antes de exportar. |
| Fertilización | Tipo | `fertilizaciones.tipo` | Tipo de fertilizante/aplicacion | Requiere catálogo oficial | Parcial | Opciones locales; requieren catálogo oficial o mapeo antes de exportar. |
| Fertilización | Riqueza NPK | `fertilizaciones.riqueza_npk` | Composicion/riqueza | Requiere confirmación | Falta confirmar | Existe; formato de exportación pendiente de confirmar. |
| Fertilización | Dosis/cantidad | `fertilizaciones.cantidad` | Cantidad aplicada | Requiere normalización | Cubierto | Campo numerico. |
| Fertilización | Unidades | `fertilizaciones.unidad` | Unidad de medida | Requiere catálogo oficial | Parcial | Opciones locales `kg` y `litros`; falta catálogo normalizado de unidades. |
| Fertilización | Metodo de aplicación | `fertilizaciones.metodo_aplicacion` | Metodo de aplicación | Requiere catálogo oficial | Falta confirmar | Campo libre; revisar formato antes de exportar. |
| Fertilización | Superficie | `fertilizaciones.superficie` | Superficie fertilizada | Requiere normalización | Cubierto | Campo numerico. |
| Fertilización | Parcelas/cultivo | `fertilizaciones.cultivo`; `fertilizacion_parcelas.fertilizacion_id`, `parcela_id` | Cultivo y recintos afectados | Requiere normalización | Parcial | Cultivo se guarda como texto agrupado; conviene usar referencia estructurada antes de exportar. |
| Fertilización | Operario | `fertilizaciones.operario_id` -> `personas` | Operario/aplicador | Requiere confirmación | Falta confirmar | Relación disponible, uso oficial no documentado. |
| Prácticas culturales | Campana | `practicas_culturales.campana_id` | Campana de actuacion | Exportable | Cubierto | Relación con `campanas`. |
| Prácticas culturales | Fecha | `practicas_culturales.fecha` | Fecha de labor | Exportable | Cubierto | Validada frente a campana. |
| Prácticas culturales | Labor | `practicas_culturales.labor` | Tipo de practica/labor cultural | Requiere catálogo oficial | Parcial | Lista local; requiere catálogo oficial o mapeo antes de exportar. |
| Prácticas culturales | Maquinaria | `practicas_culturales.maquinaria_id` -> `maquinaria` | Maquinaria usada | Exportable | Cubierto | Relación estructurada. |
| Prácticas culturales | Prestador/proveedor | `practicas_culturales.proveedor_id` -> `proveedores` | Prestador externo | Requiere confirmación | Parcial | Proveedor tiene NIF/contacto, pero su uso en exportación asistida requiere confirmación. |
| Prácticas culturales | Operario | `practicas_culturales.operario_id` -> `personas` | Operario | Requiere confirmación | Falta confirmar | Dato disponible. |
| Prácticas culturales | Superficie | `practicas_culturales.superficie` | Superficie afectada | Requiere normalización | Cubierto | Campo numerico. |
| Prácticas culturales | Parcelas/cultivo | `practicas_culturales.cultivo`; `practica_parcelas.practica_id`, `parcela_id` | Cultivo y recintos afectados | Requiere normalización | Parcial | Cultivo como texto; parcelas normalizadas por relación. Conviene estructurar cultivo antes de exportar. |
| Cosecha | Campana | `cosecha.campana_id` | Campana de cosecha | Exportable | Cubierto | Relación con `campanas`. |
| Cosecha | Fecha | `cosecha.fecha` | Fecha de recoleccion/cosecha | Exportable | Cubierto | Validada frente a campana. |
| Cosecha | Cultivo | `cosecha.cultivo` | Cultivo cosechado | Requiere normalización | Parcial | Texto agrupado, no `cultivo_id`; requiere normalización para exportación robusta. |
| Cosecha | Producto | `cosecha.producto` | Producto cosechado | Requiere confirmación | Cubierto | Campo libre; revisar formato antes de exportar. |
| Cosecha | Cantidad | `cosecha.kg` | Cantidad cosechada | Exportable | Cubierto | Unidad local fija: kg; confirmar unidad admitida en el formato exportable. |
| Cosecha | Destino | `cosecha.destino` | Destino/comercializacion | Requiere confirmación | Cubierto | Campo libre; revisar formato antes de exportar. |
| Cosecha | Parcelas | `cosecha_parcelas.cosecha_id`, `parcela_id`; `cosecha.parcelas` texto | Parcelas/recintos de origen | Requiere normalización | Parcial | Existe relación normalizada y texto histórico; usar la relación en exportaciones nuevas. |
| Cosecha | Cliente/comprador | `cosecha.cliente`, `nif_cliente` | Destinatario/comprador | Requiere normalización | Falta confirmar | No enlaza con `clientes`; se guarda como texto y requiere revisión antes de exportar. |
| Cosecha | Lote/albaran/factura | `cosecha.lote`, `albaran`, `factura` | Trazabilidad comercial/anexos | Requiere normalización | Falta confirmar | Datos disponibles como texto; revisar si deben salir en el paquete asistido. |
| Maquinaria | Tipo | `maquinaria.tipo`; `equipos_aplicacion.tipo` | Tipo de maquinaria/equipo | Requiere catálogo oficial | Cubierto | Campo libre; revisar formato antes de exportar. |
| Maquinaria | Marca/modelo | `maquinaria.marca`, `modelo`; `equipos_aplicacion.marca`, `modelo` | Identificacion de equipo | Exportable | Cubierto | Campos disponibles. |
| Maquinaria | Matricula | Sin campo especifico | Matricula de maquinaria, si procede | No exportar inicialmente | No existe | No se encontró campo `matricula`; no exportar inicialmente. |
| Maquinaria | Número ROMA | `maquinaria.numero_roma`; `equipos_aplicacion.numero_roma` | Inscripcion ROMA | Exportable | Cubierto | Disponible en maquinaria general y equipos de aplicación; exportable tras revisar formato. |
| Maquinaria | Número de serie | `equipos_aplicacion.numero_serie` | Identificador técnico de equipo | Requiere normalización | Parcial | Solo en equipos de aplicación, no en maquinaria general; revisar alcance antes de exportar. |
| Maquinaria | Equipos de aplicación | `equipos_aplicacion` | Equipos de aplicación fitosanitaria | Exportable | Cubierto | Incluye inspecciones, capacidad y ROMA; revisar campos requeridos por plantilla. |
| Maquinaria | Inspecciones | `equipos_aplicacion.fecha_ultima_inspeccion`, `fecha_proxima_inspeccion` | Inspeccion/revision de equipo | Requiere confirmación | Falta confirmar | Existe para equipos, no para maquinaria general; confirmar si debe exportarse. |
| Documentos/anexos | Recetas PDF | `tratamientos_documentos` con `tipo_documento='receta'` | Anexo receta de tratamiento | Exportable | Cubierto | Incluye ruta, extensión, MIME, tamaño, hash y timestamps; anexar solo si procede. |
| Documentos/anexos | Facturas PDF | `movimientos_economicos_documentos` con `tipo_documento='factura'` | Anexo factura | No exportar inicialmente | Cubierto | Asociado a movimientos económicos; no incluir inicialmente salvo necesidad documental. |
| Documentos/anexos | Cuaderno oficial PDF | `services/cuadernopro_pdf.py::generar_cuadernopro_pdf(campana_id)` | Documento resumen/cuaderno generado | No exportar inicialmente | Parcial | Se genera fichero local; no incluir inicialmente como dato estructurado. |
| Documentos/anexos | Informes | `modules/informes.py`; consultas por campana | Informes internos | No exportar inicialmente | No aplica | Son vistas internas; no exportar inicialmente como estructura SIEX/CUE. |
| Trazabilidad | Identificador interno | `id` en tablas principales | Identificador técnico interno | No exportar inicialmente | Cubierto | No equivale a identificador oficial; no exportar inicialmente salvo como referencia local. |
| Trazabilidad | created_at | `clientes`, `proveedores`, `tratamientos_documentos`, `analisis_fitosanitarios`, `movimientos_economicos_documentos`, `movimientos_economicos_lineas_iva` | Fecha de creacion/auditoria | Requiere normalización | Parcial | No existe en parcelas, cultivos, tratamientos, fertilizaciones, prácticas, cosecha ni maquinaria. |
| Trazabilidad | updated_at | `clientes`, `proveedores`, `tratamientos_documentos`, `analisis_fitosanitarios`, `movimientos_economicos_documentos`, `movimientos_economicos_lineas_iva` | Fecha de modificacion/auditoria | Requiere normalización | Parcial | Cobertura incompleta en tablas agronómicas principales; útil solo para trazabilidad local. |
| Trazabilidad | Usuario | Sin campo encontrado | Usuario autor de alta/modificacion/preparación | No exportar inicialmente | No existe | No hay modelo de usuarios ni auditoría por usuario; no exportar inicialmente. |
| Trazabilidad | Preparado para paquete SIEX/CUE | Sin campo `exportado_a_siex` | Estado de paquete preparado/exportado localmente | No exportar inicialmente | No existe | No exportar inicialmente; si se añade, debería ser trazabilidad local de paquetes asistidos. |
| Trazabilidad | Fecha de exportación local | Sin campo `fecha_exportacion` | Fecha/hora de preparación o exportación | No exportar inicialmente | No existe | Pendiente para una fase futura de trazabilidad local. |
| Trazabilidad | Estado de preparación local | Sin tabla de sincronizacion | Estado de validación y preparación local | No exportar inicialmente | No existe | Requeriría diseño específico para trazabilidad local, no para envío directo. |
| Trazabilidad | Historial de paquetes locales | Sin tabla de historial SIEX/CUE | Registro local de paquetes, validaciones y entrega al asesor | No exportar inicialmente | No existe | Requeriría logs técnicos y auditoría funcional local. |


## Hallazgos principales

- El núcleo agronómico está bastante estructurado por campaña para tratamientos, fertilización, prácticas culturales y cosecha.
- La referencia SIGPAC está bien representada en parcelas, con códigos de provincia/municipio, agregado, zona, polígono, parcela, recinto, superficie y caché GeoJSON.
- Explotación ya contiene campos candidatos para REGEA/REGEPA, responsable y asesor, pero falta confirmar el identificador oficial aplicable a cada territorio.
- Tratamientos fitosanitarios son el área más completa: producto, registro, fechas, parcelas, cultivo, aplicador, equipo, dosis, caldo, superficie, eficacia, plazo de seguridad y recetas PDF.
- Cultivos no tienen campaña propia ni superficie propia por cultivo. La superficie se infiere desde parcelas o actuaciones, lo que limita una exportación asistida fina por campaña.
- Fertilización y prácticas guardan `cultivo` como texto agrupado, aunque las parcelas se relacionan mediante tablas intermedias.
- Cosecha guarda cultivo y cliente como texto, aunque parcelas sí tienen tabla intermedia.
- La trazabilidad de creación/modificación es parcial y no existe trazabilidad local específica de paquetes SIEX/CUE asistidos.

## Lectura para exportación asistida

- Una primera exportación debería priorizar Excel/CSV/JSON de revisión, no comunicación con sistemas administrativos.
- Los campos marcados como "Requiere catálogo oficial" no deberían salir como códigos hasta confirmar catálogo o mapeo admitido.
- Los anexos PDF pueden formar parte de un paquete ZIP de trabajo, pero no deben considerarse una presentación oficial.
- El Interfaz Único queda documentado solo como posibilidad futura, no como objetivo inmediato.
