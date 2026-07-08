# Estado v7.12 - Prueba real de guardado y persistencia

## Objetivo

Comprobar que los formularios y editores complejos guardan, recargan y no
pierden campos sobre una base v7 limpia. El hito no busca nuevas etiquetas
visuales; busca persistencia real.

## Bases usadas

- `runtime/v7/prueba_persistencia_v7.db`
- `runtime/v7/prueba_manual_v7_12.db`

Ambas bases se crean con `scripts/crear_base_v7.py` y diagnóstico OK:

- `PRAGMA user_version = 7`
- 25 tablas
- sin columnas legacy prohibidas
- sin errores de claves foraneas

## Criterio de aceptacion

Para cada módulo probado:

- crear registro
- leer desde base
- editar usando helper o flujo equivalente al editor de la app
- guardar
- leer de nuevo
- comprobar que el campo cambiado se actualiza
- comprobar que relaciones e IDs no se pierden
- comprobar que fechas quedan en formato SQLite correcto
- comprobar que salidas SIEX/PDF no rompen tras las ediciones

## Módulos probados

| Módulo | Persistencia |
| --- | --- |
| Explotación | OK |
| Productos fitosanitarios | OK |
| Maquinaria / equipos | OK |
| Tratamientos | OK |
| Fertilización | OK |
| Prácticas culturales | OK |
| Cosecha | OK |
| Contabilidad | OK |
| Mapas / SIGPAC | OK |
| Terceros / clientes / proveedores | OK |
| Revisión SIEX / Excel SIEX / PDF oficial | OK |

## Fallos detectados

### Productos fitosanitarios

El módulo seguia usando nombres legacy en varios puntos del alta, listado y
editor:

- `registro`
- `dosis`

La tabla v7 limpia usa:

- `numero_registro`
- no tiene `dosis`

Impacto:

- el alta/listado/editor podia fallar sobre v7 limpia o no persistir el número
  de registro correctamente.
- el editor podia intentar actualizar columnas inexistentes.

Correccion:

- se anaden helpers dinamicos en `modules/productos_fito.py`.
- se resuelve `numero_registro` como campo canónico v7 y `registro` como
  fallback v6.
- INSERT/UPDATE solo escriben columnas existentes.
- el editor incluye `activo` sin convertirlo a texto antes de guardar.
- `scripts/probar_editores_auxiliares_v7.py` y
  `scripts/probar_render_modulos_v7.py` pasan a cubrir Productos fito.

### Mapas / SIGPAC

La prueba manual detecto un fallo al abrir "Mapa general de la explotación":

```text
no such column: sigpac_geojson_estado
```

Causa:

- `modules/mapas.py` consultaba de forma fija
  `parcelas.sigpac_geojson_estado`.
- la tabla `parcelas` del esquema v7 limpio no contiene esa columna.
- en v7 limpio las columnas SIGPAC disponibles son:
  `provincia_sigpac`, `municipio_sigpac`, `agregado_sigpac`,
  `zona_sigpac`, `superficie_sigpac`, `uso_sigpac` y `sigpac_geojson`.

Correccion:

- no se añade `sigpac_geojson_estado` a `core/schema_v7.py`.
- `modules/mapas.py` detecta columnas reales con `PRAGMA table_info`.
- si existe `sigpac_geojson_estado` en bases antiguas, se respeta.
- si no existe, el estado visual se deriva de `sigpac_geojson`:
  `Con geometria` cuando tiene valor y `Sin geometria` cuando está vacío.
- las columnas opcionales `sigpac_geojson_actualizado` y
  `sigpac_geojson_error` se leen como valores vacios si no existen.
- el mapa abre con base v7 limpia sin parcelas y con parcelas sin geometría,
  mostrando un aviso amable en lugar de romper.
- los cultivos del mapa se resuelven con `cultivo_parcelas` en v7 y con
  `cultivos.parcela_id` solo como fallback legacy.

## Script principal

Script nuevo:

`scripts/probar_persistencia_editores_v7.py`

Resultado:

- Explotación: OK
- Productos fito: OK
- Maquinaria / equipos: OK
- Tratamientos: OK
- Fertilización: OK
- Prácticas culturales: OK
- Cosecha: OK
- Contabilidad: OK
- Mapas / SIGPAC: OK
- Terceros: OK
- Informes / salidas: OK

Salidas generadas por el script:

- Revisión SIEX: OK, 9 registros, 0 bloqueos
- Excel SIEX: OK, tamaño valido
- PDF oficial: OK, tamaño valido

## Pendiente manual

Streamlit queda arrancado para prueba manual con:

```bash
CUADERNOPRO_DB_PATH=runtime/v7/prueba_manual_v7_12.db ./venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8517 --server.headless true
```

URL:

- `http://192.168.0.13:8517`

PID:

- `runtime/v7/streamlit_v7_12.pid`

Health check:

- `ok`

Revisar en navegador:

- crear/listar/editar/recargar Explotación
- Maquinaria/equipo
- Producto fito
- Tratamiento
- Fertilización
- Practica cultural
- Cosecha
- Contabilidad
- Mapas / SIGPAC

## Recomendacion v7.13

Pasar de persistencia por helpers a prueba UI más profunda con AppTest o prueba
manual guiada por capturas: editar celdas reales de `st.data_editor`, pulsar
botones de guardar y verificar recarga en navegador.
