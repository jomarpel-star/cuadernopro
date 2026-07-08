# Prueba integral v7.8 - Base v7 limpia

## Fecha

2026-07-01

## Base usada

`runtime/v7/prueba_integral_v7.db`

La prueba automatizada `scripts/probar_flujo_integral_v7.py` regenera esta
base usando `core.db.crear_tablas(ruta_db)`, para validar el mecanismo real de
arranque de CuadernoPro sobre una ruta de base nueva.

No se toca `cuadernopro.db`.

## Diagnóstico de esquema

- `PRAGMA user_version`: 7
- número de tablas: 25
- columnas faltantes: ninguna
- columnas legacy prohibidas detectadas en el esquema: ninguna
- índices faltantes: ninguno
- claves foraneas: sin errores
- resultado diagnóstico: OK

## Datos insertados

La prueba crea un flujo mínimo de agricultor nuevo:

- explotación con titular, NIF, nombre de explotación, municipio, provincia,
  responsable y asesor;
- campana `2025/2026` activa;
- cliente y proveedor;
- parcela SIGPAC minima;
- cultivo `ALMENDRO` con `codigo_siex=104`;
- relación `cultivo_parcelas`;
- maquinaria general y equipo de aplicación fitosanitaria;
- producto fitosanitario con número de registro;
- persona aplicadora;
- tratamiento completo con `eficacia=B`, parcela asociada y receta simulada;
- fertilización con `cultivo_id` y `fertilizacion_parcelas`;
- practica cultural con `cultivo_id`, maquinaria, proveedor y parcelas;
- cosecha con `cultivo_id` y `cliente_id`;
- ingreso y gasto contable, lineas IVA y factura simulada.

## Resultado por módulo

| Módulo | Resultado | Observaciones |
| --- | --- | --- |
| Base v7 limpia | OK | Creada con `core.db.crear_tablas`. |
| Diagnóstico esquema | OK | `user_version=7`, 25 tablas. |
| Explotación | OK | Insercion directa sobre columnas v7 limpias. |
| Campana | OK | `2025/2026` activa. |
| Cliente y proveedor | OK | Insercion en tablas limpias. |
| Parcela | OK | Parcela SIGPAC minima. |
| Cultivo | OK | `ALMENDRO`, `codigo_siex=104`, relación `cultivo_parcelas`. |
| Maquinaria y equipo aplicación | OK | Maquinaria general y equipo fito v7. |
| Producto fitosanitario y persona | OK | Producto con registro y aplicador. |
| Tratamiento | OK | Tratamiento, parcela asociada y documento receta simulado. |
| Fertilización | OK | Usa `cultivo_id` y `fertilizacion_parcelas`. |
| Practica cultural | OK | Usa `cultivo_id`, `maquinaria_id`, `proveedor_id` y parcelas. |
| Cosecha | OK | Usa `cultivo_id`, `cliente_id` y `cosecha_parcelas`. |
| Contabilidad | OK | Ingreso, gasto, lineas IVA y factura simulada. |
| Conteos relacionales | OK | Todos los mínimos esperados presentes. |
| Informes | OK | Lee movimientos, tratamientos, fertilizaciones, prácticas y cosecha. |
| Revisión SIEX | OK | 11 registros revisados, 8 avisos/info, 0 bloqueos. |
| Excel asistido SIEX | OK | Excel generado correctamente. |
| PDF oficial | OK | PDF generado correctamente. |

## Salidas generadas

- Excel SIEX asistido:
  `cuadernopro_exportacion_asistida_siex_2025_2026_2026-07-01.xlsx`
- Tamano Excel: 15423 bytes
- PDF oficial:
  `runtime/v7/exports_integral/cuadernopro_cuaderno_2025_2026.pdf`
- Tamano PDF: 27833 bytes

## Prueba de render Streamlit

Ademas del script integral de datos, se ha ejecutado una comprobacion con
`streamlit.testing.v1.AppTest` usando `CUADERNOPRO_DB_PATH` contra
`runtime/v7/prueba_integral_v7.db`. No arranca servidor ni sustituye a la
prueba manual en navegador, pero detecta errores de render de las secciones.

| Sección | Resultado | Error |
| --- | --- | --- |
| Inicio | OK | - |
| Explotación | Fallo | `no such column: carnet_fitosanitario` en consulta de `personas`. |
| Cultivos | Fallo | `no such column: municipio` en consulta de `parcelas`. |
| Tratamientos | OK | - |
| Fertilización | OK | - |
| Prácticas culturales | OK | - |
| Cosecha | OK | - |
| Contabilidad | OK | - |
| Informes | OK | - |
| Cuaderno oficial | OK | - |
| Revisión SIEX | OK | - |

## Errores encontrados

La prueba automatizada de datos no encuentra errores bloqueantes en inserciones,
relaciones, informes ni salidas.

La comprobacion de render Streamlit detecta dos fallos de interfaz sobre v7
limpio:

- `modules/explotacion.py` consulta `personas.carnet_fitosanitario`, columna
  que no existe en v7 limpio.
- `modules/cultivos.py` consulta `parcelas.municipio`, columna que no existe
  en v7 limpio; v7 usa codigos SIGPAC (`municipio_sigpac`) y no el campo texto
  legacy.

## Campos o tablas faltantes

No se detectan campos ni tablas faltantes en el esquema v7 limpio.

## Dependencias legacy pendientes

El esquema está limpio, pero queda código de interfaz que todavía contiene
referencias directas a columnas legacy o nombres históricos. No se modifica en
v7.8; se documenta para la fase siguiente.

- `modules/explotacion.py`: `localidad`, `carnet_fitosanitario`,
  `fecha_adquisicion`, `fecha_ultima_inspeccion`,
  `fecha_proxima_inspeccion`.
- `modules/cultivos.py`: `parcelas.municipio`, `cultivos.parcela_id`,
  `cultivos.especie`.
- `modules/parcelas.py`: `cultivos.parcela_id`, `cultivos.especie`.
- `modules/maquinaria.py`: `fecha_adquisicion`,
  `fecha_ultima_inspeccion`, `fecha_proxima_inspeccion`.

Algunas referencias legacy de otros módulos son compatibilidad controlada y no
bloquean esta prueba automatizada porque se comprueba la existencia de columnas
antes de usarlas.

## Prueba Streamlit manual

Arrancar la app con la base integral:

```bash
CUADERNOPRO_DB_PATH=runtime/v7/prueba_integral_v7.db \
./venv/bin/streamlit run app.py \
  --server.address 0.0.0.0 \
  --server.port 8517 \
  --server.headless true
```

Abrir:

```text
http://192.168.0.13:8517
```

Checklist manual:

- Inicio.
- Asistente inicial.
- Explotación.
- Cultivos.
- Tratamientos.
- Fertilización.
- Prácticas culturales.
- Cosecha.
- Contabilidad.
- Informes.
- Cuaderno oficial.
- Revisión SIEX.
- Exportación Excel.

Al terminar, detener el proceso temporal de Streamlit. No debe quedar como
servicio.

## Siguiente acción recomendada

Para v7.9, adaptar las pantallas que aún tienen referencias directas a columnas
legacy, empezando por:

1. `modules/explotacion.py`
2. `modules/cultivos.py`
3. `modules/parcelas.py`
4. `modules/maquinaria.py`

El objetivo de v7.9 debería ser que esas pantallas puedan leer y guardar sobre
v7 limpio sin depender de `localidad`, `cultivos.parcela_id`,
`cultivos.especie`, `parcelas.municipio`, `carnet_fitosanitario` ni las fechas
legacy de equipos.
