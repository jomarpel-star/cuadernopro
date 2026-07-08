# Auditoria formularios/listados v7

## Objetivo

Revisar la coherencia entre formulario, guardado, base v7, listado y editor.
No se anaden columnas legacy al esquema v7.

Base auditada:

`runtime/v7/prueba_manual_v7_10.db`

Desde la normalización visual general, la prueba automática de listados queda
separada en:

`runtime/v7/prueba_listados_v7.db`

Antes de la auditoria se creo copia en:

`runtime/v7/backups/`

## Explotación

Incidencia detectada en prueba manual:

- al crear o editar una explotación, el listado posterior no mostraba con
  claridad el nombre de explotación ni el Código REGEPA / identificador
  oficial.
- el asistente inicial pedia Titular / razon social, pero no pedia de forma
  clara Nombre de la explotación, aunque luego el resumen lo mostraba;
- por captura se confirma que la pestaña mostraba `nombre_explotacion = None`;
- el identificador introducido aparecia bajo el alias visual `codigo_regea` y
  `codigo_revacío quedaba vacío.
- el fallo real estaba en el `st.data_editor` de la pestaña Explotación: se le
  entregaba un DataFrame con nombres internos, por lo que la tabla visual no
  quedaba normalizada aunque el guardado ya usara campos v7.
- ademas, el bloque de borrado seguro bajo la misma sección recibia
  `datos_explotacion` crudo y podia volver a pintar las columnas internas en
  pantalla.

Correccion aplicada:

- `nombre_explotacion` se mantiene como campo limpio v7 para el nombre;
- el asistente inicial pide explicitamente Nombre de la explotación y lo
  persiste en `nombre_explotacion`;
- si Nombre de la explotación queda vacío, se usa Titular / razon social como
  fallback guardado;
- `identificador_oficial` se usa como campo limpio v7 para Código REGEPA /
  identificador oficial;
- se crea un unico campo visual normalizado para la pantalla de Explotación,
  alimentado por `identificador_oficial` en v7 y con fallback a `codigo_regepa`
  / `codigo_regea` solo en bases antiguas;
- el DataFrame entregado al editor se renombra antes de pintarse, de modo que
  sus columnas reales en pantalla son `Nombre de la explotacion` y
  `Codigo REGEPA / identificador oficial`;
- los grupos Datos del titular, Datos de la explotación, Responsable y Asesor
  se muestran primero como vista limpia y la edición queda en un desplegable;
- Personas relacionadas y Equipos de aplicación usan etiquetas limpias en sus
  editores;
- al guardar, las etiquetas visuales se mapean de vuelta a columnas internas
  antes del `UPDATE`;
- el bloque `borrar_registros_seguro` recibe ahora una vista visual limpia con
  `id` y etiquetas presentables, no el DataFrame crudo de explotación;
- `core/borrado.py` normaliza también la previsualizacion de borrado general
  para evitar columnas técnicas al seleccionar registros en otros módulos;
- al guardar se prioriza el campo visual normalizado y se escribe en
  `identificador_oficial`, manteniendo escritura compatible en columnas legacy
  si existen en bases antiguas;
- en v7 la pestaña no muestra `codigo_regea` ni `codigo_regepa` como columnas
  separadas;
- el resumen/listado muestra nombre, titular, NIF, identificador oficial,
  municipio y provincia.
- la métrica de datos de explotación no exige `tipo_explotacion` cuando esa
  columna no existe en v7 limpia.

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nombre explotación | `nombre_explotacion` | si | si | si | si | OK | Corregido para quedar visible en resumen/listado. |
| Titular / razon social | `titular` | si | si | si | si | OK | Campo legal/persona, separado de noexplotaciónlotacion. |
| NIF | `nif` | si | si | si | si | OK | Campo limpio. |
| Dirección | `direccion` | si | si | si | si | OK | Campo limpio. |
| Localidad visual | `municipio` | si | si | si | si | OK | Alias visual para compatibilidad. |
| Código REGEPA / identificador oficial | `identificador_oficial` | si | si | si | si | OK | Corregido mapeo guardado/listado/editor; no crea columnas legacy. |
| `codigo_regea` / `codigo_regepa` | no existen en v7 | no aplica | no | no | no aplica | OK | Solo fallback legacy interno si una base antigua trae esas columnas. |
| Tipo explotación | sin columna v7 | no aplica | no aplica | no aplica | no aplica | PENDIENTE | No bloquea la métrica de datos básicos en v7 limpia. |
| Responsable | `responsable` | si | si | si | si | OK | Alias desde campos visuales. |
| Asesor | `asesor`, `numero_asesor` | si | si | si | si | OK | Alias v7. |
| Orientacion productiva | sin columna v7 | no aplica | no aplica | no aplica | no aplica | PENDIENTE | Mejora posterior si se decide ampliar v7 de forma limpia. |
| Fecha alta | sin columna v7 | no aplica | no aplica | no aplica | no aplica | PENDIENTE | Mejora posterior si se decide ampliar v7 de forma limpia. |
| Agricultor activo | sin columna v7 | no aplica | no aplica | no aplica | no aplica | PENDIENTE | Mejora posterior si se decide ampliar v7 de forma limpia. |

## Campanas

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nombre | `nombre` | si | si | si | si | OK | Probado por flujo integral. |
| Fecha inicio | `fecha_inicio` | si | si | si | si | OK | Probado por flujo integral. |
| Fecha fin | `fecha_fin` | si | si | si | si | OK | Probado por flujo integral. |
| Activa | `activa` | si | si | si | si | OK | Probado por flujo integral. |

## Parcelas

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nombre | `nombre` | si | si | si | si | OK | Verificado por `probar_listados_v7.py`. |
| Provincia SIGPAC | `provincia_sigpac` | si | si | si | si | OK | No depende de `provincia` legacy. |
| Municipio SIGPAC | `municipio_sigpac` | si | si | si | si | OK | No depende de `municipio` legacy. |
| Agregado | `agregado_sigpac` | si | si | si | si | OK | Campo limpio. |
| Zona | `zona_sigpac` | si | si | si | si | OK | Campo limpio. |
| Poligono | `poligono` | si | si | si | si | OK | Campo limpio. |
| Parcela | `parcela` | si | si | si | si | OK | Campo limpio. |
| Recinto | `recinto` | si | si | si | si | OK | Campo limpio. |
| Superficie | `superficie_sigpac` | si | si | si | si | OK | Campo limpio. |
| Uso SIGPAC | `uso_sigpac` | si | pendiente UI | pendiente UI | si | PENDIENTE | El script valida persistencia; revisar exposición visual. |
| Observaciones | `observaciones` | si | si | si | si | OK | Campo limpio. |
| Cultivos asociados | `cultivo_parcelas` | si | si | si | si | OK | No usa `cultivos.parcela_id`. |

## Cultivos

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Campana | `campana_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Nombre cultivo | `nombre` | si | si | si | si | OK | No usa `especie` en v7. |
| Código SIEX | `codigo_siex` | si | si | si | si | OK | Verificado por script. |
| Superficie | `superficie` | si | si | si | si | OK | Verificado por script. |
| Parcelas | `cultivo_parcelas` | si | si | si | si | OK | Tabla puente canonica. |
| Sistema | sin columna v7 | no aplica | no aplica | no aplica | no aplica | PENDIENTE | Solo fallback si existe en base legacy. |
| Observaciones | `observaciones` | si | pendiente UI | pendiente UI | si | PENDIENTE | Verificar exposición visual en v7. |

## Maquinaria

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nombre / descripcion | `descripcion` | si | si | si | si | OK | Corregido para v7. |
| Tipo | `tipo` | si | si | si | si | OK | Verificado por script. |
| Marca | `marca` | si | si | si | si | OK | Verificado por script. |
| Modelo | `modelo` | si | si | si | si | OK | Verificado por script. |
| Matricula | `matricula` | si | si | si | si | OK | Corregido en formulario/listado/editor. |
| Número ROMA | `numero_roma` | si | si | si | si | OK | Corregido y verificado. |
| Número de serie | sin columna v7 | no aplica | no aplica | no aplica | no aplica | OK | No se muestra como campo persistible en v7. |
| Fecha de compra | sin columna v7 | no aplica | no aplica | no aplica | no aplica | OK | Ocultada si la columna no existe. |
| Observaciones | `observaciones` | si | si | si | si | OK | Verificado por script. |

## Equipos de aplicación

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nombre | `nombre` | si | si | si | si | OK | Verificado por script. |
| Tipo | `tipo` | si | si | si | si | OK | Verificado por script. |
| Marca | `marca` | si | si | si | si | OK | Verificado por script. |
| Modelo | `modelo` | si | si | si | si | OK | Verificado por script. |
| Número de serie | `numero_serie` | si | si | si | si | OK | Verificado por script. |
| Número ROMA | sin columna v7 | no aplica | no aplica | no aplica | no aplica | OK | Ocultado si no existe. |
| Fecha revisión | `fecha_revision` | si | si | si | si | OK | Corregido alias visual. |
| Fecha proxima revisión | `fecha_proxima_revision` | si | si | si | si | OK | Corregido alias visual. |
| Observaciones | `observaciones` | si | si | si | si | OK | Verificado por script. |

## Personas / aplicadores

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nombre | `nombre` | si | si | si | si | OK | Verificado indirectamente. |
| NIF | `nif` | si | si | si | si | OK | Campo limpio. |
| Rol | `rol` | si | si | si | si | OK | Campo limpio. |
| Carnet aplicador visual | `carnet_aplicador` | si | si | si | si | OK | Alias desde carnet fitosanitario visual. |
| Fecha caducidad carnet | sin columna v7 | no aplica | no aplica | no aplica | no aplica | OK | Ocultada si no existe. |
| Número asesor | `numero_asesor` | si | si | si | si | OK | Campo limpio. |

## Productos fitosanitarios

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nombre | `nombre` | si | si | si | si | OK | Verificado por script. |
| Número registro | `numero_registro` | si | si | si | si | OK | Verificado en tratamiento. |
| Materia activa | `materia_activa` | si | si | si | si | OK | Probado por flujo integral. |
| Plazo seguridad | `plazo_seguridad` | si | si | si | si | OK | Probado por flujo integral. |

## Tratamientos

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Campana | `campana_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Cultivo | `cultivo_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Parcelas | `tratamiento_parcelas` | si | si | si | si | OK | Tabla puente. |
| Fecha inicio | `fecha_inicio` | si | si | si | si | OK | Verificado por script. |
| Fecha fin | `fecha_fin` | si | si | si | si | OK | Verificado por script. |
| Producto | `producto_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Registro producto | `productos_fito.numero_registro` | si | si | si | si | OK | Verificado por script. |
| Aplicador | `aplicador_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Equipo | `equipo_aplicacion_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Eficacia | `eficacia` | si | si | si | si | OK | Campo limpio. |

## Fertilización

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Campana | `campana_id` | si | si | si | si | OK | Verificado por script. |
| Cultivo | `cultivo_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Parcelas | `fertilizacion_parcelas` | si | si | si | si | OK | Tabla puente. |
| Fecha | `fecha` | si | si | si | si | OK | Campo limpio. |
| Producto | `producto` | si | si | si | si | OK | Campo limpio. |
| Tipo fertilizante | `tipo_fertilizante` | si | si | si | si | OK | Campo limpio. |
| Cantidad | `cantidad` | si | si | si | si | OK | Campo limpio. |
| Unidad | `unidad` | si | si | si | si | OK | Campo limpio. |
| Superficie | `superficie` | si | si | si | si | OK | Campo limpio. |

## Prácticas culturales

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Campana | `campana_id` | si | si | si | si | OK | Verificado por script. |
| Cultivo | `cultivo_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Parcelas | `practicas_culturales_parcelas` | si | si | si | si | OK | Tabla puente v7. |
| Fecha | `fecha` | si | si | si | si | OK | Campo limpio. |
| Labor | `labor` | si | si | si | si | OK | Campo limpio. |
| Superficie | `superficie` | si | si | si | si | OK | Campo limpio. |
| Maquinaria | `maquinaria_id` | si | si | si | si | OK | Resuelto desde `descripcion`. |
| Proveedor | `proveedor_id` | si | si | si | si | OK | Resuelto por JOIN. |

## Cosecha

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Campana | `campana_id` | si | si | si | si | OK | Verificado por script. |
| Cultivo | `cultivo_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Parcelas | `cosecha_parcelas` | si | si | si | si | OK | Tabla puente. |
| Fecha | `fecha` | si | si | si | si | OK | Campo limpio. |
| Cantidad | `cantidad` | si | si | si | si | OK | Sustituye `kg`. |
| Unidad | `unidad` | si | si | si | si | OK | Campo limpio. |
| Cliente | `cliente_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Precio | sin columna v7 | no aplica | no aplica | no aplica | no aplica | OK | Solo fallback si existe en base legacy. |

## Contabilidad

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fecha | `fecha` | si | si | si | si | OK | Verificado por script. |
| Tipo | `tipo` | si | si | si | si | OK | Ingreso/gasto. |
| Concepto | `concepto` | si | si | si | si | OK | Campo limpio. |
| Campana | `campana_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Cultivo | `cultivo_id` | si | si | si | si | OK | Resuelto por JOIN. |
| Cliente | `cliente_id` | si | si | si | si | OK | Ingresos. |
| Proveedor | `proveedor_id` | si | si | si | si | OK | Gastos. |
| Base imponible | `base_imponible` | si | si | si | si | OK | Campo limpio. |
| IVA | `iva` | si | si | si | si | OK | Campo limpio. |
| Total | `total` | si | si | si | si | OK | Campo limpio. |
| Pendiente | `pendiente` | si | si | si | si | OK | Campo limpio. |
| Factura/documento | `movimientos_economicos_documentos` | si | si | si | si | OK | Probado por flujo integral. |

## Informes

| Campo visible | Columna real v7 | Guarda | Listado | Editor | Informe/exportacion | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Resumen general | varias v7 | no aplica | si | no aplica | si | OK | Probado por flujo integral. |
| Tratamientos | IDs y tablas puente | no aplica | si | no aplica | si | OK | Probado por flujo integral. |
| Fertilización | IDs y tablas puente | no aplica | si | no aplica | si | OK | Probado por flujo integral. |
| Prácticas | IDs y tablas puente | no aplica | si | no aplica | si | OK | Probado por flujo integral. |
| Cosecha | `cantidad`, `unidad`, IDs | no aplica | si | no aplica | si | OK | Probado por flujo integral. |
| Contabilidad | IDs y lineas IVA | no aplica | si | no aplica | si | OK | Probado por flujo integral. |

## Resultado de `scripts/probar_listados_v7.py`

Resultado: OK.

Base usada por el script:

`runtime/v7/prueba_listados_v7.db`

Módulos comprobados:

- Explotación
- Maquinaria
- Equipo de aplicación
- Parcela
- Cultivo
- Tratamiento
- Fertilización
- Practica cultural
- Cosecha
- Contabilidad ingreso
- Contabilidad gasto

Campos no aplicables en v7 limpia:

- maquinaria general: `numero_serie`, `fecha_compra`, `num_horas`;
- equipos de aplicación: `numero_roma`, `fecha_adquisicion`,
  `capacidad_litros`;
- cultivos: `cultivos.parcela_id`, `cultivos.especie`;
- cosecha: `kg`, `precio`.
