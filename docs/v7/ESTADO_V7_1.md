# Estado v7.1 - Esquema limpio base nueva

## Resumen

La fase v7.1 crea un generador y un diagnóstico de esquema limpio v7 en una base SQLite separada. No integra todavía el esquema con la aplicación actual y no toca la base real `cuadernopro.db`.

La base de prueba se genera en:

`runtime/v7/cuadernopro_v7_limpia.db`

## Archivos creados

- `core/schema_v7.py`: definicion del esquema limvalidacióndices y validación.
- `scripts/crear_base_v7.py`: crea una bavalidaciónrada y ejecuta validación.
- `scripts/diagnostico_schema_v7.py`: audita una base v7 existente en modo lectura.
- `docs/v7/ESTADO_V7_1.md`: estado técnico de esta fase.

## Seguridad

- No se modifica `core/db.py`.
- No se modifica `app.py`.
- No se modifican módulos funcionales.
- No se toca `cuadernopro.db`.
- No se ejecutan migraciones destructivas.
- No se eliminan columnas de bases existentes.

Si la base de destino ya existe, `scripts/crear_base_v7.py` crea una copia previa con sufijo `.bak-YYYYMMDD_HHMMSS` antes de regenerarla.

## Tablas creadas

El esquema v7.1 crea 25 tablas.

Tablas maestras:

- `explotacion`
- `campanas`
- `parcelas`
- `cultivos`
- `cultivo_parcelas`
- `clientes`
- `proveedores`
- `productos_fito`
- `personas`
- `maquinaria`
- `equipos_aplicacion`
- `siex_catalogos`
- `siex_catalogos_items`

Tablas operativas:

- `tratamientos`
- `tratamiento_parcelas`
- `tratamientos_documentos`
- `fertilizaciones`
- `fertilizacion_parcelas`
- `practicas_culturales`
- `practicas_culturales_parcelas`
- `cosecha`
- `cosecha_parcelas`
- `movimientos_economicos`
- `movimientos_economicos_lineas_iva`
- `movimientos_economicos_documentos`

## Columnas legacy prohibidas

El diagnóstico marca como error que aparezcan estas columnas en el esquema v7 limpio:

- `cultivos.parcela_id`
- `fertilizaciones.cultivo`
- `practicas_culturales.cultivo`
- `cosecha.cultivo`
- `cosecha.cliente`
- `cosecha.nif_cliente`
- `cosecha.kg`
- `movimientos_economicos.tercero`
- `movimientos_economicos.nif_tercero`
- `movimientos_economicos.cultivo`
- `tratamientos.cultivo`
- `tratamientos.producto`
- `tratamientos.aplicador`
- `tratamientos.equipo`
- `tratamientos.fecha`

## Scripts disponibles

Crear una base v7 de prueba:

```bash
./venv/bin/python scripts/crear_base_v7.py runtime/v7/cuadernopro_v7_limpia.db
```

Diagnosticar una base v7:

```bash
./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v7/cuadernopro_v7_limpia.db
```

## Resultado del diagnóstico

Resultado obtenido en `runtime/v7/cuadernopro_v7_limpia.db`:

- versión esperada: 7
- `PRAGMA user_version`: 7
- número de tablas: 25
- tablas faltantes: ninguna
- columnas faltantes: ninguna
- columnas legacy prohibidas detectadas: ninguna
- índices faltantes: ninguno
- errores de claves foraneas: ninguno
- resultado: OK

## Proximos pasos

La siguiente fase debería adaptar el primer módulo funcional sobre el esquema limpio v7, empezando por Cosecha, porque concentra varias duplicidades historicas: `cultivo`, `cliente`, `nif_cliente` y `kg`.

La integración real con `core/db.py` debe hacerse después de validar que el esquema aislado cubre las necesidades de instalación nueva.
