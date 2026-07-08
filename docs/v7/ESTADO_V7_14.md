# Estado v7.14 - Prueba completa pre-v8

## Objetivo

Ejecutar una prueba completa de CuadernoPro sobre base v7 limpia como si un
agricultor empezara desde cero, y dejar una base objetiva para decidir si la
siguiente versión puede ser una candidata v8.0 estable.

## Alcance de la prueba pre-v8

La prueba automatizada cubre:

- configuración inicial y explotación;
- campana 2025/2026 activa;
- cliente, proveedor y persona aplicadora;
- parcela SIGPAC minima;
- cultivo asociado mediante `cultivo_parcelas`;
- maquinaria y equipo de aplicación con campos v7.13;
- producto fitosanitario;
- tratamiento con producto, aplicador, equipo y parcelas;
- fertilización con cultivo y parcelas;
- practica cultural con maquinaria/proveedor;
- cosecha con cliente;
- contabilidad con ingreso, gasto, IVA y totales;
- informes;
- Revisión SIEX;
- Excel SIEX;
- PDF oficial;
- Mapas/SIGPAC sin geometría y sin error.

## Base usada

Automática:

- `runtime/v7/prueba_pre_v8_v7_14.db`

Manual:

- `runtime/v7/prueba_manual_v7_14.db`

Ambas bases se crean con `scripts/crear_base_v7.py` y no tocan
`cuadernopro.db`.

## Script nuevo

- `scripts/probar_pre_v8_v7_14.py`

El script usa solo `runtime/v7/prueba_pre_v8_v7_14.db` y genera salidas en:

- `runtime/v7/exports_pre_v8_v7_14/`
- `runtime/v7/documentos_pre_v8_v7_14/`

## Resultado automatico

Resultado de `scripts/probar_pre_v8_v7_14.py`:

- base v7 limpia: OK;
- diagnóstico de esquema: OK;
- campos v7.13: OK;
- configuración inicial / explotación: OK;
- campana: OK;
- terceros/personas: OK;
- parcelas/cultivos: OK;
- maquinaria/equipos: OK;
- productos fito: OK;
- tratamientos: OK;
- fertilización: OK;
- prácticas culturales: OK;
- cosecha: OK;
- contabilidad: OK;
- informes: OK;
- Revisión SIEX: OK, 11 registros revisados, 0 bloqueos;
- Excel SIEX: OK, 15434 bytes;
- PDF oficial: OK, 28325 bytes;
- Mapas/SIGPAC: OK, sin geometría disponible y sin error.

Resultado global:

- `Resultado: OK`
- `Candidata v8.0: Si`

## Diagnóstico v7

Diagnóstico inicial:

- `runtime/v7/prueba_pre_v8_v7_14.db`: OK;
- `runtime/v7/prueba_manual_v7_14.db`: OK.

Condiciones verificadas:

- `PRAGMA user_version = 7`;
- 25 tablas;
- columnas requeridas presentes;
- sin columnas legacy prohibidas;
- claves foraneas OK;
- salidas v7 OK.

## Fallos detectados

No se han detectado fallos bloqueantes en la prueba automatizada pre-v8.

## Correcciones aplicadas

No se han aplicado correcciones funcionales durante v7.14.

Cambios introducidos:

- script automatizado pre-v8;
- documento de estado v7.14;
- checklist manual pre-v8;
- actualización del plan v7.

## Prueba manual

Checklist creada:

- `docs/v7/PRUEBA_MANUAL_PRE_V8.md`

La prueba manual debe ejecutarse en navegador con:

- base: `runtime/v7/prueba_manual_v7_14.db`;
- URL: `http://192.168.0.13:8517`.

## Pendientes obligatorios antes de v8.0

- Completar la checklist manual pre-v8 en navegador y documentar cualquier
  incidencia real detectada.
- Confirmar que no aparecen artefactos generados en `git status --short`.

## Pendientes opcionales posteriores a v8.0

- Sustituir progresivamente `use_container_width` por `width` en tablas
  Streamlit, porque Streamlit avisa de retirada futura.
- Reducir referencias internas de compatibilidad v6 que ya no afectan al
  esquema limpio v7.
- Mejorar pruebas de interfaz con AppTest para cubrir más flujos de usuario.

## Recomendacion final

CuadernoPro queda recomendado como candidata v8.0 desde el punto de vista de
flujo automatizado, esquema limpio, persistencia, salidas y Mapas/SIGPAC.

La recomendacion final de cierre a v8.0 debe quedar condicionada a completar
la prueba manual pre-v8 en navegador.
