# Estado v7.7 - Activar base limpia v7 para instalaciones nuevas

## Resumen

La fase v7.7 activa el esquema limpio v7 para bases nuevas.

A partir de esta fase, cuando CuadernoPro arranca contra una ruta de base de
datos inexistente, vacía o sin tablas de usuario, la inicializacion real de la
app crea el esquema v7 mediante `core/schema_v7.py`.

No se convierte automáticamente ninguna base existente.

## Decisión de producto

CuadernoPro v7 está pensado para instalaciones nuevas o para usuarios que
acepten empezar con una base limpia y cargar sus datos desde cero.

No se implementa migración automática desde v6 porque podría arrastrar
relaciones ambiguas, campos duplicados y datos legacy históricos.

La versión v6 queda como respaldo estable para bases anteriores.

## Cambio técnico

Se modifica `core/db.py` para que `crear_tablas()` decida antes de ejecutar el
esquema compatible historico:

- si la base no existe, está vacía o no tiene tablas de usuario, crea esquema
  v7 limpio con `core.schema_v7.crear_base_v7`;
- si la base ya es v7 (`PRAGMA user_version >= 7` y contiene tablas), no ejecuta
  el esquema legacy;
- si la base ya existe con tablas y no es v7, mantiene el camino compatible
  anterior.

Esto evita recrear o alterar destructivamente bases v6 existentes.

## Bases existentes

Si `cuadernopro.db` ya existe y contiene tablas, no se borra, no se migra y no
se fuerza a v7.

El comportamiento actual se mantiene en modo compatible durante esta transición.

## Prueba automática

Se crea:

`scripts/probar_arranque_base_v7.py`

La prueba usa:

`runtime/v7/prueba_arranque_v7.db`

El script:

- elimina la base de prueba si existe, conservando copia `.bak`;
- llama a `core.db.crear_tablas()` como mecanismo real de arranque;
- valida `PRAGMA user_version = 7`;
- comprueba ausencia de columnas legacy prohibidas;
- ejecuta `scripts/diagnostico_schema_v7.py`;
- confirma diagnóstico OK.

Resultado obtenido:

- inicializacion real: `core.db.crear_tablas`;
- número de tablas: 25;
- `PRAGMA user_version`: 7;
- columnas legacy detectadas: ninguna;
- diagnóstico schema v7: OK;
- resultado: OK.

## Prueba Streamlit separada

Para probar el arranque con base v7 limpia sin tocar la base real:

```bash
CUADERNOPRO_DB_PATH=runtime/v7/prueba_streamlit_v7.db \
./venv/bin/streamlit run app.py \
  --server.address 0.0.0.0 \
  --server.port 8517 \
  --server.headless true
```

Abrir:

```text
http://192.168.0.13:8517
```

Al terminar la prueba, detener ese proceso. No debe quedar como servicio.

## Docker

`docker-compose.yml` ya apunta a:

`CUADERNOPRO_DB_PATH=/app/runtime/cuadernopro.db`

En una instalación nueva, ese fichero no existe o está vacío; por tanto nacerá
con esquema v7 limpio. No se cambian puertos ni volumenes.

## Conservacion de una base v6

Antes de probar v7 con datos nuevos, conservar copia de la base v6 anterior:

- mantener el ZIP/tag estable v6;
- copiar `cuadernopro.db` a una ubicacion de backup;
- no usar la base v6 como destino de pruebas v7.

## Seguridad

- No se toca destructivamente `cuadernopro.db`.
- No se elimina ninguna columna.
- No se migran datos reales.
- No se modifica Docker ni instaladores.
- No se borra código legacy de módulos.

## Pendiente para v7.8

- Revisar el flujo de primera configuración sobre esquema v7.
- Adaptar pantallas maestras que aún puedan esperar nombres históricos de
  columnas.
- Documentar instalación limpia completa para usuarios nuevos.
- Preparar checklist de prueba funcional con base v7 vacía.
