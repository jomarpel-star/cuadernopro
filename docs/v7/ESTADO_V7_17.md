# Estado v7.17 - Cálculo de árboles por marco de plantación

## Objetivo

Anadir en Cultivos un cálculo practico para cultivos lenosos agrupados por año
de plantación. El usuario puede introducir superficie y marco de plantación,
aceptar el número estimado de árboles o ajustarlo manualmente antes de guardar.

## Formula usada

La superficie se interpreta en hectareas.

```text
numero_arboles = round((superficie_ha * 10000) / (distancia_1_m * distancia_2_m))
```

Ejemplo validado:

- superficie: `2.5 ha`
- marco: `7x7`
- cálculo: `round((2.5 * 10000) / (7 * 7)) = 510`

## Campos anadidos

En `cultivos`:

- `marco_plantacion TEXT`
- `numero_arboles INTEGER`

`marco_plantacion` guarda el texto original introducido por el usuario.
`numero_arboles` guarda el resultado redondeado y editable.

## Módulos modificados

- `core/schema_v7.py`
- `core/db.py`
- `core/ui_tablas.py`
- `modules/cultivos.py`
- `modules/informes.py`
- `modules/mapas.py`
- `services/cuadernopro_pdf.py`
- `scripts/diagnostico_schema_v7.py`
- pruebas v7 que crean cultivos de base

## Comportamiento

- Alta de cultivo: calcula árboles si hay superficie y marco valido.
- Edición de cultivo: recalcula si cambia superficie o marco, pero permite
  mantener o ajustar manualmente el número final.
- Listado de cultivos: muestra marco de plantación y número de árboles.
- Informes internos: anaden sección de cultivos con marco y árboles.
- PDF oficial: muestra marco/arboles en la sección de parcelas y datos
  agronomicos cuando existen.
- Excel SIEX: no añade columnas nuevas porque no forman parte del formato
  asistido actual.

## Incidencia corregida tras prueba manual

Durante la prueba manual se detecto que el formulario real de Cultivos podia
mostrar:

```text
Marco de plantación no válido. Usa formatos como 7x7 o 6,5x5.
```

La causa no estaba en el parser para `7x7`: el helper ya aceptaba el formato
ASCII. El fallo estaba en el formulario, que usaba el resultado de
`calcular_numero_arboles()` para decidir si el marco era valido. Cuando la
superficie era 0 o aún no era calculable, la función devolvía `None` y el
formulario interpretaba ese `None` como marco invalido.

Correccion aplicada:

- el formulario valida el marco con `parsear_marco_plantacion()`;
- solo calcula árboles si el marco es valido y hay superficie positiva;
- si el marco está vacío, no muestra aviso;
- si el marco tiene texto y el parser lo rechaza, muestra aviso;
- se amplian formatos aceptados: `7x7`, `7X7`, `7 x 7`, `7×7`, `7*7`,
  `6,5x5`, `6.5x5` y espacios delante/detras.

## Pruebas realizadas

- `./venv/bin/python -m py_compile ...`: OK.
- `./venv/bin/python scripts/probar_cultivos_arboles_v7.py`: OK.
  - Parseo validado: `7x7`, `7X7`, `7 x 7`, `7×7`, `7*7`, `6x5`,
    `6 x 5`, `6X5`, `6*5`, `6,5x5`, `6.5x5`, `7.5x6`.
  - Marcos invalidos rechazados: vacío, `abc`, `7`, `7x`, `x7`, `7x0`,
    `0x7`, `-7x7`.
  - Calculos validados: 400, 204, 510 y 1000 árboles.
  - AppTest de formulario real de Cultivos: OK para `7x7`, `6x5`,
    `6,5x5` y `7×7`.
  - Informes, revisión SIEX, Excel SIEX y PDF oficial: OK.
- `./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v7/prueba_cultivos_arboles_v7.db`: OK.
- `./venv/bin/python scripts/probar_cosecha_multicultivo_v7.py`: OK.
- `./venv/bin/python scripts/probar_pre_v8_v7_14.py`: OK.
- `./venv/bin/python scripts/probar_persistencia_editores_v7.py`: OK.
- `./venv/bin/python scripts/probar_schema_v7_13.py`: OK.
- `./venv/bin/python scripts/probar_listados_v7.py`: OK.
- `./venv/bin/python scripts/auditar_tablas_visuales_v7.py`: OK, 0 advertencias.
- `./venv/bin/python scripts/probar_render_modulos_v7.py`: OK.
- `./venv/bin/python scripts/probar_editores_auxiliares_v7.py`: OK.
- `./venv/bin/python scripts/probar_flujo_integral_v7.py`: OK.
- `git diff --check`: OK.
- `git status --short`: solo código, scripts y documentación; no aparecen
  `runtime/`, bases de datos ni caches.
- Base manual creada con `scripts/crear_base_v7.py runtime/v7/prueba_manual_v7_17.db`: OK.
- Streamlit manual arrancado con PID `runtime/v7/streamlit_v7_17.pid`: OK.
  - URL usada: `http://192.168.0.13:8518`.
  - Se uso el puerto 8518 porque el 8517 ya estaba ocupado por otro
    `streamlit`.

Pendiente:

- comprobacion visual completa en navegador del formulario de Cultivos.

## Pendientes para v8

- decidir si el número de árboles debe participar en analiticas por hectarea o
  por arbol;
- valorar si conviene una densidad calculada visible;
- revisar si SIEX/CUE oficial requiere algun campo equivalente en futuras
  exportaciones.
