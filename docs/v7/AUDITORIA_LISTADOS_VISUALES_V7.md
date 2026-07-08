# Auditoria listados visuales v7

## Objetivo

Evitar que las pantallas principales muestren nombres SQL o columnas técnicas
al agricultor. La interfaz debe hablar con etiquetas comprensibles sin cambiar
el esquema v7.

## Bases separadas

- Base manual navegador: `runtime/v7/prueba_manual_v7_10.db`
- Base automática listados: `runtime/v7/prueba_listados_v7.db`

`scripts/probar_listados_v7.py` usa solo `prueba_listados_v7.db` y ya no
ensucia la base manual.

## Helper comun

Se crea `core/ui_tablas.py` con:

- `MAPA_ETIQUETAS_COLUMNAS`
- `COLUMNAS_TECNICAS_OCULTAS`
- `preparar_dataframe_visual`
- `aplicar_etiquetas_columnas`
- `ocultar_columnas_tecnicas`
- `normalizar_vacios`
- `mapear_columnas_visuales_a_tecnicas`
- `preparar_column_config_visual`

Regla de uso:

- En `st.dataframe` se puede renombrar fisicamente el DataFrame porque es
  solo visual.
- En `st.data_editor` con guardado se deben conservar nombres internos y usar
  `column_config`, o mapear explicitamente visual -> interno antes de guardar.

## Correcciones aplicadas ahora

| Módulo | Tabla/listado | Acción |
| --- | --- | --- |
| Asistente inicial | Configuración inicial / Campaña | Vista visual limpia con `Campaña`, `Fecha inicio`, `Fecha fin`, `Activa`. |
| Asistente inicial | Configuración inicial / Explotación | El formulario recoge `Nombre de la explotacion` y alimenta el resumen/listado. |
| Core borrado | Previsualizacion de borrado | Usa vista visual limpia y mantiene `ID` para confirmar. |
| Explotación | Titular, datos, responsable y asesor | Vista visible limpia; editor queda en desplegable. |
| Explotación | Personas y equipos | Editores con etiquetas visuales y mapeo de guardado. |
| Explotación | Responsable / Asesor | Editor corregido para mantener columnas internas y evitar `KeyError: responsable_nombre`. |
| Contabilidad | Listado | Eliminado `assert` de dtype de fecha; conversion segura con `pd.to_datetime`. |
| Campanas | Listado/editor | Listado visible sin `id`; editor queda en desplegable. |
| Parcelas | Listado | Etiquetas SIGPAC limpias y ocultacion de geometría. |
| Parcelas | Editor | Etiquetas limpias; `geometry` no se muestra. |
| Cultivos | Listado | Etiquetas visuales en campos principales. |
| Maquinaria | Listado | Etiquetas visuales para ROMA, matricula, fechas y descripcion. |
| Maquinaria | Previsualizacion | Etiquetas visuales. |
| Productos fito | Listado | Etiquetas visuales y ocultacion técnica. |
| Tratamientos | Listado | Oculta IDs y muestra campaña, cultivo, producto, registro, fechas y aplicación. |
| Fertilización | Listado | Etiquetas visuales. |
| Prácticas culturales | Listado | Etiquetas visuales. |
| Cosecha | Listado | Etiquetas visuales. |
| Contabilidad | Listado principal | Etiquetas visuales para movimientos. |

## Auditoria automática

Script nuevo:

`scripts/auditar_tablas_visuales_v7.py`

Resultado actual:

- llamadas detectadas: 46
- OK con helper visual, `column_config` o mapeo explicito: 29
- advertencias pendientes: 17

El auditor distingue ahora:

- `st.dataframe` sin `preparar_dataframe_visual`: advertencia.
- `st.data_editor` con `column_config`: OK.
- `st.data_editor` con DataFrame renombrado y sin mapeo visible:
  `ADVERTENCIA_EDITOR_RENOMBRADO`.

## Detalle de llamadas detectadas

| Estado | Archivo:línea | Acción |
| --- | --- | --- |
| OK | `modules/asistente_inicio.py:354` | Campaña del asistente inicial corregida. |
| ADVERTENCIA | `modules/asistente_inicio.py:570` | Pendiente; tabla de personas del asistente inicial. |
| OK | `modules/campanas.py:55` | Listado visible corregido. |
| OK | `modules/campanas.py:63` | Editor con etiquetas visuales. |
| ADVERTENCIA | `modules/catalogos_siex.técnico| Pendiente; catálogo técnico. |
| ADVERTENCIA | `modules/catalogos_siex.técnico | Pendiente; catálogo técnico. |
| OK | `modules/contabilidad.py:2340` | Listado principal corregido. |
| OK | `modules/contabilidad.py:2420` | Pendientes de pagar corregido. |
| OK | `modules/contabilidad.py:2447` | Pendientes de cobrar corregido. |
| OK | `modules/contabilidad.py:2929` | Detalle de IVA corregido. |
| OK | `modules/contabilidad.py:2981` | Facturas adjuntas corregido. |
| ADVERTENCIA | `modules/contabilidad.py:3139` | Pendiente; editor complejo. |
| OK | `modules/cosecha.py:1729` | Listado corregido. |
| ADVERTENCIA | `modules/cosecha.py:2529` | Pendiente; editor complejo. |
| OK | `modules/cultivos.py:962` | Listado corregido. |
| OK | `modules/explotacion.py:986` | Editor de grupo con etiquetas limpias. |
| ADVERTENCIA | `modules/explotacion.py:1135` | Resumen ya tiene etiquetas limpias, pendiente adaptar al helper comun. |
| OK | `modules/explotacion.py:1685` | Editor personas con etiquetas limpias. |
| OK | `modules/explotacion.py:2190` | Editor equipos con etiquetas limpias. |
| OK | `modules/fertilizacion.py:1500` | Listado corregido. |
| ADVERTENCIA | `modules/fertilizacion.py:2058` | Pendiente; editor complejo. |
| ADVERTENCIA | `modules/informes.py:787` | Pendiente; tablas de informes. |
| ADVERTENCIA | `modules/informes.py:1048` | Pendiente; tablas de informes. |
| ADVERTENCIA | `modules/informes.py:1069` | Pendiente; tablas de informes. |
| ADVERTENCIA | `modules/informes.py:1114` | Pendiente; tablas de informes. |
| ADVERTENCIA | `modules/informes.py:1143` | Pendiente; tablas de informes. |
| ADVERTENCIA | `modules/informes.py:1172` | Pendiente; tablas de informes. |
| ADVERTENCIA | `modules/mapas.py:798` | Pendiente; tabla auxiliar de mapas. |
| OK | `modules/maquinaria.py:523` | Listado corregido. |
| OK | `modules/maquinaria.py:826` | Previsualizacion corregida. |
| OK | `modules/parcelas.py:460` | Listado corregido. |
| OK | `modules/parcelas.py:536` | Editor corregido. |
| OK | `modules/practicas_culturales.py:1669` | Listado corregido. |
| ADVERTENCIA | `modules/practicas_culturales.py:2224` | Pendiente; editor complejo. |
| OK | `modules/productos_fito.py:231` | Alta de producto con etiquetas limpias. |
| OK | `modules/productos_fito.py:375` | Listado corregido. |
| OK | `modules/productos_fito.py:399` | Editor detectado junto a helper; revisar visualmente. |
| ADVERTENCIA | `modules/revision_siex.py:1601` | Pendiente; tabla revisión SIEX. |
| ADVERTENCIA | `modules/terceros.py:226` | Pendiente; listado terceros. |
| ADVERTENCIA | `modules/terceros.py:235` | Pendiente; editor terceros. |
| OK | `modules/tratamientos.py:1582` | Análisis fitosanitarios corregido. |
| OK | `modules/tratamientos.py:3331` | Listado tratamientos corregido. |
| OK | `modules/tratamientos.py:4096` | Recetas adjuntas corregido. |
| ADVERTENCIA | `modules/tratamientos.py:4463` | Pendiente; editor complejo. |

## Pendiente

- Normalizar editores complejos con guardado acoplado:
  contabilidad, cosecha, fertilización, prácticas y tratamientos.
- Revisar tablas de informes, revisión SIEX, terceros, mapas y asistente.
- Convertir advertencias criticas en pruebas visuales automatizadas.

## Actualización v7.11

La limpieza de v7.11 revisa las advertencias pendientes del auditor y aplica
la regla definitiva:

- Los listados `st.dataframe` pasan por `preparar_dataframe_visual`.
- Los editores `st.data_editor` conservan columnas internas y usan
  `column_config`, salvo editores visuales con mapeo explicito de vuelta a
  columnas técnicas.
- El auditor amplio su ventana de contexto para reconocer mapeos explicitos y
  ahora también revisa `core/`.

Cambios añadidos:

| Módulo | Resultado |
| --- | --- |
| Asistente inicial | Personas del asistente con etiquetas limpias. |
| Catálogos SIEX | Catálogos e items con etiquetas visuales. |
| Explotación | Resumen de explotación por helper comun. |
| Contabilidad | Editor complejo con `column_config` completo y columnas internas. |
| Tratamientos | Editor complejo con `column_config` completo y columnas internas. |
| Informes | Resumenes y detalles por helper visual. |
| Mapas | Errores SIGPAC con etiquetas limpias. |
| Revisión SIEX | Resultado de revisión con etiquetas limpias. |
| Terceros | Listado visual limpio y editor con `column_config`. |
| Productos fito | Editor de productos guardados con `column_config`. |

Resultado final del auditor v7.11:

- llamadas detectadas: 47
- advertencias: 0
- advertencias de prioridad alta: 0

No quedan pendientes justificados en el auditor actual. La siguiente pasada
debe centrarse en guardar cambios reales desde los editores complejos y validar
persistencia.

## Actualización v7.12

La prueba de persistencia detecta que Productos fitosanitarios todavía asumía
campos legacy (`registro`, `dosis`) en alta/listado/editor. En v7 limpia el
número de registro es `numero_registro` y `dosis` no existe.

Regla añadida:

- Los editores deben resolver la columna real antes de construir el DataFrame.
- `numero_registro` es canónico en v7.
- `registro` queda como fallback para bases antiguas.
- No se deben incluir en `column_order`, filtros ni UPDATE columnas ausentes en
  la tabla real.

Se cubre con:

- `scripts/probar_persistencia_editores_v7.py`
- `scripts/probar_editores_auxiliares_v7.py`
- `scripts/probar_render_modulos_v7.py`

Mapas / SIGPAC también queda cubierto en v7.12:

- no consulta de forma fija `sigpac_geojson_estado`.
- en v7 limpia deriva el estado visual desde `sigpac_geojson`.
- las columnas opcionales de estado, fecha y error se usan solo si existen.
- las pruebas cubren base sin parcelas y parcelas sin geometría.

## Actualización v7.13

La ampliacion limpia del esquema incorpora nuevos campos visibles en
Explotación, Maquinaria y Equipos de aplicación:

- `registro_autoautonómico Registro autonómico.
- `horas_uso` -> Horas de uso.
- `fecha_adquisicion` -> Fecha de adquisicion.
- `capacidad_litros` -> Capacidad litros.
- `numero_roma` -> Nº ROMA.

Los listados y editores mantienen la regla:

- `st.dataframe` usa vistas visuales con etiquetas limpias.
- `st.data_editor` conserva columnas internas y muestra etiquetas con
  `column_config` o mapeo controlado.

Resultado del auditor tras v7.13:

- advertencias: 0.
- advertencias de prioridad alta: 0.
