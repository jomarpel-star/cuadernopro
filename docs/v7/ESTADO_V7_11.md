# Estado v7.11 - Limpieza de editores complejos y pantallas auxiliares

## Objetivo

Reducir o eliminar advertencias del auditor visual sin romper guardados en
editores complejos. La regla se mantiene:

- `st.dataframe`: vista solo visual con `preparar_dataframe_visual`.
- `st.data_editor`: columnas internas intactas y etiquetas mediante
  `column_config`, o mapeo explicito visual -> interno antes de guardar.
- Tablas técnicas o de diagnóstico: ocultas o documentadas si aportan valor.

## Situacion inicial

Auditor inicial:

- llamadas detectadas: 46
- advertencias: 17
- prioridad alta afectada: asistente inicial, explotación, contabilidad,
  parcelas, productos fitosanitarios y tratamientos
- prioridad media afectada: catálogos SIEX, informes, mapas, revisión SIEX y
  terceros

Bases separadas creadas para esta fase:

- `runtime/v7/prueba_manual_v7_11.db`
- `runtime/v7/prueba_editores_v7.db`
- `runtime/v7/prueba_auxiliares_v7.db`

Las tres nacen con `PRAGMA user_version = 7`, 25 tablas, sin columnas legacy y
diagnóstico OK.

## Cambios aplicados

| Módulo | Cambio |
| --- | --- |
| `core/ui_tablas.py` | Ampliado mapa de etiquetas para catálogos, informes, revisión SIEX, mapas, terceros y editores contables. `preparar_column_config_visual` reconoce columnas numericas. |
| `modules/asistente_inicio.py` | Tabla de personas del asistente pasa por vista visual limpia. |
| `modules/catalogos_siex.py` | Catálogos e items SIEX usan etiquetas vitécnicas ocultan columnas técnicas. |
| `modules/explotacion.py` | Resumen de explotación pasa por helper comun, eliminando falso positivo. |
| `modules/contabilidad.py` | Editor complejo mantiene columnas internas y usa `column_config` completo con etiquetas limpias. |
| `modules/tratamientos.py` | Editor complejo mantiene columnas internas y usa `column_config` completo con etiquetas limpias. |
| `modules/informes.py` | Tablas de resumen y detalle pasan por helper visual comun. |
| `modules/mapas.py` | Tabla auxiliar de errores SIGPAC usa etiquetas visuales ytécnicascolumnas técnicas. |
| `modules/revision_siex.py` | Resultado de revisión usa etiquetas comprensibles. |
| `modules/terceros.py` | Listado visual limpio y editor con `column_config` sin renombrar columnas internas. |
| `modules/productos_fito.py` | Editor de productos guardados con `column_config` y columnas internas. |
| `scripts/auditar_tablas_visuales_v7.py` | Auditor cubre `core/`, distingue mejor editores con `column_config`, mapeo explicito y DataFrame crudo. |
| `scripts/probar_editores_auxiliares_v7.py` | Nuevo script AppTest para pantallas auxiliares y editores complejos sobre `prueba_editores_v7.db`. |

## Auditor final

Resultado tras los cambios:

- llamadas detectadas: 47
- advertencias: 0
- advertencias de prioridad alta: 0
- advertencias medias: 0

No quedan advertencias justificadas pendientes en el auditor actual.

## Pruebas ejecutadas

Ejecutado durante el desarrollo:

- `scripts/auditar_tablas_visuales_v7.py`: OK, 0 advertencias.
- `scripts/probar_editores_auxiliares_v7.py`: OK.
- `scripts/probar_listados_v7.py`: OK.
- `scripts/probar_render_modulos_v7.py`: OK.
- `scripts/probar_flujo_integral_v7.py`: OK.
- Diagnóstico de `prueba_manual_v7_11.db`, `prueba_editores_v7.db` y
  `prueba_auxiliares_v7.db`: OK.
- Streamlit sobre `prueba_manual_v7_11.db`: arranque verificado en
  `http://192.168.0.13:8517`; endpoint de salud `ok`.

`probar_editores_auxiliares_v7.py` comprueba:

- Explotación / Responsable-Asesor.
- Contabilidad / Listado vacío.
- Informes con base minima.
- Revisión SIEX con base minima.
- Mapas sin geometría.
- Tratamientos / Editar.
- Fertilización / Editar.
- Prácticas culturales / Editar.
- Cosecha / Editar.
- Contabilidad / Editar.

## Pendiente antes de cerrar

- Revisar visualmente en navegador las pantallas indicadas usando
  `http://192.168.0.13:8517`.
- Confirmar que no aparecen columnas técnicas crudas en flujo normal.

## Recomendacion v7.12

Entrar en una pasada funcional de edición real: guardar cambios desde cada
editor complejo, verificar persistencia en base v7 limpia y revisar impacto en
PDF oficial, Excel SIEX e informes.
