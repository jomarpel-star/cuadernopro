# Tablas y campos a limpiar para v6

Esta tabla clasifica los principales elementos del modelo actual que conviene mantener, revisar o reestructurar. No implica cambios aplicados.

| Tabla/campo | Estado actual | Problema | Propuesta v6 | Prioridad |
| --- | --- | --- | --- | --- |
| `campanas` | Mantener | Falta estado explícito más allá de `activa` | Mantener y añadir `estado` si aporta valor | Media |
| `explotacion` | Mantener | Responsable/asesor están embebidos aunque existe `personas` | Mantener en v6 inicial; revisar enlace a `personas` más adelante | Baja |
| `parcelas` | Mantener | No tiene `activa`; conviven `geometry` y `sigpac_geojson` | Mantener y añadir estado activo/inactivo; revisar campo de geometría principal | Media |
| `parcelas.superficie_cultivada` | Revisar | Puede solaparse con superficie de cultivo o superficies por actuación | Definir si es dato propio de parcela o cálculo | Media |
| `cultivos.parcela_id` | Reestructurar | Un cultivo queda asociado a una sola parcela y sin campaña | Sustituir por `cultivo_parcelas` | Alta |
| `cultivos.campana_id` | No existe | No se puede modelar cultivo por campaña | Añadir en v6 como campo obligatorio | Alta |
| `cultivos.especie` | Renombrar | En pantalla se usa como cultivo/nombre | Renombrar conceptualmente a `nombre`; mantener alias si se migra | Alta |
| `cultivos.codigo_siex` | No existe | No hay enlace normalizado a catálogo SIEX de cultivos | Añadir y enlazar con catálogo `cultivo` | Alta |
| `cultivos.superficie` | No existe | La superficie se infiere de parcelas o actuaciones | Añadir superficie propia por cultivo/campaña | Alta |
| `cultivo_parcelas` | No existe | Falta relación N:M cultivo-parcela | Crear en v6 | Alta |
| `tratamientos.campana_id` | Mantener | Bien resuelto | Mantener | Alta |
| `tratamientos.cultivo_id` | Mantener | Bien resuelto | Mantener y exigir en flujos nuevos | Alta |
| `tratamientos.fecha` | Revisar | Convive con `fecha_inicio` y `fecha_fin` | Eliminar en base nueva o conservar solo como legacy | Media |
| `tratamientos.aplicador` | Revisar | Convive con `aplicador_id` | Priorizar `aplicador_id`; eliminar texto en base nueva si no se usa | Media |
| `tratamientos.maquinaria_id` | Revisar | Convive con `equipo_id` y `equipo_aplicacion_id` | Definir origen único para equipo de aplicación | Media |
| `tratamientos.equipo_id` | Revisar | Posible compatibilidad histórica | Usar `equipo_aplicacion_id` como campo principal | Media |
| `tratamiento_parcelas` | Mantener | No tiene `id` propio | Mantener; valorar `id` si se necesita edición avanzada | Media |
| `tratamientos_documentos` | Mantener | Tabla específica para recetas | Mantener inicialmente | Media |
| `analisis_fitosanitarios.parcelas` | Reestructurar | Guarda parcelas como texto CSV | Crear tabla puente si este módulo sigue creciendo | Media |
| `fertilizaciones.cultivo` | Reestructurar | Texto, no FK | Sustituir por `cultivo_id` | Alta |
| `fertilizaciones.codigo_actuacion_siex` | No existe | No hay normalización SIEX | Añadir si se confirma catálogo aplicable | Alta |
| `fertilizaciones.unidad_normalizada` | No existe | Las unidades son texto/locales | Añadir o mapear con tabla/catálogo de unidades | Alta |
| `fertilizacion_parcelas` | Mantener | Buena tabla puente | Mantener y enlazar con `cultivo_id` para coherencia | Alta |
| `practicas_culturales.cultivo` | Reestructurar | Texto, no FK | Sustituir por `cultivo_id` | Alta |
| `practicas_culturales.labor` | Revisar | Lista interna no normalizada | Mantener texto visible y añadir `codigo_actuacion_siex` | Alta |
| `practicas_culturales.codigo_actuacion_siex` | No existe | No hay catálogo oficial asociado | Añadir si procede | Alta |
| `practica_parcelas` | Mantener | Buena tabla puente | Mantener | Alta |
| `cosecha.cultivo` | Reestructurar | Texto, no FK | Sustituir por `cultivo_id` | Alta |
| `cosecha.kg` | Renombrar | Unidad implícita | Cambiar a `cantidad` + `unidad` | Alta |
| `cosecha.parcelas` | Revisar | Texto redundante con `cosecha_parcelas` | Eliminar en base nueva o conservar como resumen calculado | Media |
| `cosecha.cliente` | Revisar | Texto, aunque existen `clientes` | Añadir `cliente_id` y mantener texto solo como fallback | Media |
| `cosecha.destino` | Revisar | Texto libre | Añadir destino normalizado si se confirma necesidad SIEX/CUE | Media |
| `cosecha_parcelas` | Mantener | Buena tabla puente | Mantener | Alta |
| `maquinaria` | Mantener | Falta matrícula si se necesita | Mantener como maquinaria general `MAQ`; añadir matrícula si procede | Baja |
| `equipos_aplicacion` | Mantener | Se solapa parcialmente con maquinaria | Mantener como `EQ` y no exigir ROMA si no procede | Baja |
| `mantenimientos` | Mantener | Depende de `maquinaria` | Mantener | Baja |
| `personas` | Revisar | Puede cubrir aplicadores, asesores, responsables | Mantener; decidir si explotación enlaza responsable/asesor | Media |
| `clientes` | Mantener | Bien estructurado | Mantener | Baja |
| `proveedores` | Mantener | Bien estructurado | Mantener | Baja |
| `movimientos_economicos.cultivo` | Revisar | Texto libre | Añadir `cultivo_id` solo si se quiere análisis económico por cultivo | Baja |
| `movimientos_economicos_documentos` | Mantener | Tabla específica para facturas | Mantener inicialmente | Baja |
| `movimientos_economicos_lineas_iva` | Mantener | Estructura contable útil | Mantener | Baja |
| `gastos` | Revisar | Puede solaparse con contabilidad | Revisar si sigue usándose o si queda sustituida por `movimientos_economicos` | Media |
| `diario` | Revisar | Funcionalidad aislada y simple | Mantener si se usa; si no, dejar fuera de base nueva inicial | Baja |
| `siex_catalogos` | Mantener | Infraestructura reciente y útil | Mantener | Alta |
| `siex_catalogos_items` | Mantener | Infraestructura reciente y útil | Mantener | Alta |
| `productos_fito` | Mantener | Producto fitosanitario estructurado | Mantener; valorar más metadatos si se requieren | Alta |
| `numero_roma` en equipos | Revisar | No siempre aplica a equipos de aplicación | No exigir a `EQ-*`; sí revisar en `MAQ-*` | Baja |
| Imports antiguos | Revisar | Puede quedar código defensivo por compatibilidad | Limpiar después de fijar esquema v6 | Media |
| Excel antiguos versionados | Eliminado | `2_Parcelas.xlsx` y `8_Practicas.xlsx` ya se retiraron del repositorio | Mantener `*.xlsx` ignorado salvo plantillas decididas | Baja |
| Referencias antiguas versionadas | Revisado | No se han detectado referencias antiguas versionadas con `git grep` | Mantener vigilancia en backups/ZIPs | Baja |

## Campos de texto que deberían ser FK

- `fertilizaciones.cultivo -> cultivos.id`.
- `practicas_culturales.cultivo -> cultivos.id`.
- `cosecha.cultivo -> cultivos.id`.
- `movimientos_economicos.cultivo -> cultivos.id`, solo si se decide explotar contabilidad por cultivo.
- `cosecha.cliente -> clientes.id`, con fallback textual.
- `analisis_fitosanitarios.parcelas -> analisis_fitosanitarios_parcelas`, si se mantiene el módulo como entidad relevante.

## Columnas históricas candidatas a desaparecer en base nueva

- `tratamientos.fecha`, si `fecha_inicio` y `fecha_fin` quedan como fuente única.
- `tratamientos.aplicador`, si `aplicador_id` queda completo.
- `tratamientos.equipo_id`, si `equipo_aplicacion_id` queda como campo único.
- `cosecha.parcelas`, si `cosecha_parcelas` se usa siempre.
- `cultivos.parcela_id`, si existe `cultivo_parcelas`.
- `cosecha.kg`, si se sustituye por `cantidad` + `unidad`.

## Tablas solapadas o a revisar

- `gastos` frente a `movimientos_economicos`.
- `maquinaria` frente a `equipos_aplicacion`, no para fusionarlas sino para fijar límites.
- Tablas documentales específicas frente a una posible `documentos` genérica.
- `personas` frente a campos embebidos de asesor/responsable en `explotacion`.
