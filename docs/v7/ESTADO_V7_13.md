# Estado v7.13 - Ampliacion limpia de campos utiles

## Objetivo

Anadir campos reales utiles para una explotación agrícola sin recuperar
columnas legacy duplicadas ni cambiar la versión lógica del esquema v7.

## Campos candidatos

Explotación:

- registro autonómico de explotación
- tipo de explotación
- orientacion productiva
- fecha de alta
- agricultor activo
- joven agricultor

Maquinaria:

- matricula
- número de serie
- fecha de compra
- horas de uso
- número ROMA

Equipos de aplicación:

- matricula
- número de serie
- número ROMA
- fecha de adquisicion
- capacidad en litros
- fecha revisión
- proxima revisión

## Campos que ya existian

En la base v7.12 limpia ya existian:

- `explotacion.identificador_oficial`
- `maquinaria.matricula`
- `maquinaria.numero_roma`
- `equipos_aplicacion.numero_serie`
- `equipos_aplicacion.fecha_revision`
- `equipos_aplicacion.fecha_proxima_revision`

## Campos anadidos

En `explotacion`:

- `registro_autonomico`
- `tipo_explotacion`
- `orientacion_productiva`
- `fecha_alta`
- `agricultor_activo`
- `joven_agricultor`

En `maquinaria`:

- `numero_serie`
- `fecha_compra`
- `horas_uso`

En `equipos_aplicacion`:

- `matricula`
- `numero_roma`
- `fecha_adquisicion`
- `capacidad_litros`

## Compatibilidad

- Las bases nuevas nacen ya con estos campos.
- Las bases v7 existentes se amplian con
  `asegurar_ampliaciones_v7_13(conn)`.
- La ampliacion es idempotente y solo ejecuta `ALTER TABLE ADD COLUMN` para
  columnas ausentes.
- No hay migración automática destructiva desde v6.
- `core/schema_v7.py` mantiene `PRAGMA user_version = 7`.

## Módulos actualizados

- `core/schema_v7.py`: esquema limpio v7.13 y ampliacion idempotente.
- `core/db.py`: aplica la ampliacion al abrir bases v7 existentes.
- `core/ui_tablas.py`: etiquetas limpias para campos nuevos.
- `modules/asistente_inicio.py`: recoge `registro_autonomico`.
- `modules/explotacion.py`: muestra, edita y guarda datos ampliados de
  explotación y matricula de equipos.
- `modules/maquinaria.py`: usa `horas_uso` como canónico y mantiene
  `num_horas` solo como fallback si existe.
- `services/cuadernopro_pdf.py`: incluye campos ampliados en información
  general y equipos.

## Pruebas

Script nuevo:

- `scripts/probar_schema_v7_13.py`

Comprueba:

- base nueva con columnas v7.13;
- simulacion de base v7.12 existente y ampliacion idempotente;
- ejecución doble sin duplicar columnas;
- insercion y lectura de campos ampliados;
- diagnóstico v7 OK y sin legacy prohibido.

También se actualizan:

- `scripts/probar_persistencia_editores_v7.py`
- `scripts/probar_listados_v7.py`
- `scripts/probar_render_modulos_v7.py`
- `scripts/probar_editores_auxiliares_v7.py`
- `scripts/probar_flujo_integral_v7.py`

## Resultado

- `probar_schema_v7_13.py`: OK.
- `diagnostico_schema_v7.py runtime/v7/prueba_schema_v7_13.db`: OK.
- Persistencia de editores: OK.
- Listados: OK.
- Auditor visual: OK, 0 advertencias.
- Render de módulos: OK.
- Editores auxiliares: OK.
- Flujo integral, Revisión SIEX, Excel SIEX y PDF oficial: OK.

## Pendientes

- Prueba manual en navegador sobre `runtime/v7/prueba_manual_v7_13.db`.
- Si se decide en un hito posterior, normalizar las referencias de texto a
  `fecha_ultima_inspeccion` / `fecha_proxima_inspeccion` como etiquetas o
  alias internos, sin cambiar el esquema limpio.
