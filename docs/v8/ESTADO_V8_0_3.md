# Estado v8.0.3

## Objetivo del parche

Corregir la asignacion de campaña en Contabilidad para que los movimientos se
guarden según la fecha del movimiento y no según la campaña activa global.

Versión preparada: `v8.0.3 - Asignacion automática de campaña en contabilidad
por fecha`.

## Problema corregido

Antes del parche, al crear un movimiento económico se guardaba `campana_id` con
la campaña activa. Esto podia asignar movimientos antiguos a la campaña actual,
por ejemplo un movimiento de marzo de 2025 dentro de `2024/2025` quedaba en
`2025/2026` si esa era la activa.

## Regla implementada

- Si la fecha del movimiento cae dentro de una campaña configurada, se guarda
  esa `campana_id`.
- Si la fecha encaja en varias campañas por solape, se elige la campaña con el
  periodo más específico y se muestra aviso.
- Si la fecha no pertenece a ninguna campaña, se usa la campaña activa como
  fallback y se avisa: `La fecha no pertenece a ninguna campaña configurada. Se
  usará la campaña activa.`
- En edición, cambiar importe/concepto no recalcula campaña si la fecha no
  cambia.
- En edición, cambiar la fecha recalcula `campana_id` según la nueva fecha.

## Implementacion

- Helper central `detectar_campana_por_fecha(fecha, conn=None)` en
  `core/fechas.py`.
- Contabilidad resuelve campaña por fecha antes de insertar movimientos.
- El formulario muestra la campaña detectada y avisa cuando difiere de la
  activa o cuando aplica fallback.
- El editor mantiene la campaña existente salvo que cambie la fecha.
- Los listados e informes siguen usando el `campana_id` real guardado en el
  movimiento.

No cambia el modelo de datos y no migra movimientos existentes.

## Diagnóstico opcional

Nuevo script:

```bash
./venv/bin/python scripts/diagnosticar_contabilidad_campanas_v8.py \
  --db runtime/cuadernopro.db
```

El script no modifica datos. Informa movimientos cuya fecha pertenece a una
campaña distinta de la guardada en `campana_id`.

## Prueba especifica

Nuevo script:

```bash
./venv/bin/python scripts/probar_contabilidad_campana_por_fecha_v8.py
```

Cubre:

- movimiento de `2025-03-15` asignado a `2024/2025` aunque la activa sea
  `2025/2026`;
- movimiento de `2026-02-10` asignado a `2025/2026`;
- fecha fuera de campañas con fallback a activa y mensaje comprobable;
- balances por campaña;
- informes de contabilidad por campaña;
- edición de importe/concepto sin cambio accidental de campaña;
- edición de fecha con recalculo de campaña.

## Archivos principales

- `core/fechas.py`
- `modules/contabilidad.py`
- `modules/informes.py` revisado: filtra movimientos por `campana_id` guardado.
- `scripts/probar_contabilidad_campana_por_fecha_v8.py`
- `scripts/diagnosticar_contabilidad_campanas_v8.py`
- `scripts/probar_persistencia_editores_v7.py`
- `scripts/probar_release_v8.py`

## Restricciones respetadas

- No se toca Docker.
- No se tocan instaladores.
- No se toca `runtime/cuadernopro.db` real.
- No se cambia el modelo de datos.
- No se migran automáticamente movimientos existentes.
- No se hace commit.
