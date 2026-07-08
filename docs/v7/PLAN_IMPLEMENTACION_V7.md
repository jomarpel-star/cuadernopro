# Plan de implementacion v7

Este plan propone un orden de trabajo para pasar de v6 estable a una base v7 limpia. No ejecuta migraciones ni modifica el esquema actual.

## Criterios generales

- Trabajar en rama propia v7.
- Mantener v6 como respaldo estable.
- Priorizar base nueva limpia frente a migración automática.
- No eliminar columnas en v6.
- Adaptar primero consumidores transversales antes de retirar columnas legacy del esquema v7.
- Crear comprobaciones de esquema para evitar que una base nueva nazca con columnas antiguas.

## v7.1 - Esquema limpio base nueva

Objetivo:

- crear `core/schema_v7.py` como definicion aislada del esquema limpio;
- crear `scripts/crear_base_v7.py` para generar una base v7 de prueba separada;
- crear `scripts/diagnostico_schema_v7.py` para validar ausencia de legacy;
- fijar `SCHEMA_VERSION = 7` en el generador aislado;
- validar una base vacía en `runtime/v7/cuadernopro_v7_limpia.db`;
- no modificar todavía `core/db.py` ni el arranque actual;
- no garantizar migración automática desde v6.

Decisiones previas:

- nombre canónico de `cultivos.especie` frente a `cultivos.nombre`;
- si `cosecha.cliente_id` entra ya en v7.1;
- si `cosecha.cantidad` + `unidad` sustituyen inmediatamente a `kg`;
- si `tratamientos.maquinaria_id` desaparece o queda como maquinaria auxiliar.

Entregable:

- base nueva de prueba creada con esquema v7 limpio;
- diagnóstico que confirme ausencia de columnas legacy;
- documento `docs/v7/ESTADO_V7_1.md` con resultado de la validación;
- integración con `core/db.py` aplazada a una fase posterior.

## v7.2 - Cosecha limpia

Objetivo:

- preparar `modules/cosecha.py` para funcionar con v6 y v7;
- detectar columnas disponibles de `cosecha` antes de leer o escribir;
- usar `cliente_id` cuando exista la relación con `clientes`;
- usar `cultivo_id` como unica relación de cultivo;
- sustituir `kg` por `cantidad` + `unidad`;
- usar `cosecha_parcelas` como unica fuente de parcelas;
- eliminar uso funcional de `cliente`, `nif_cliente`, `cultivo` y `kg` en base v7;
- mantener relleno legacy en v6 solo si esas columnas existen.

Consumidores a adaptar:

- `modules/cosecha.py`;
- `scripts/probar_cosecha_v7.py`;
- `scripts/diagnostico_schema_v7.py`.

Consumidores pendientes para fases posteriores:

- `modules/informes.py`;
- `services/cuadernopro_pdf.py`;
- `services/exportacion_siex.py`;
- `modules/revision_siex.py`.

Entregable:

- Cosecha compatible con tabla v6 y tabla v7 limpia;
- prueba aislada contra `runtime/v7/cuadernopro_v7_limpia.db`;
- documento `docs/v7/ESTADO_V7_validaciónresultado de validación.

## v7.3 - Fertilización y prácticas limpias

Objetivo:

- preparar `modules/fertilizacion.py` y `modules/practicas_culturales.py`
  para funcionar con v6 y v7;
- detectar columnas disponibles antes de leer o escribir;
- eliminar uso funcional de `fertilizaciones.cultivo` en base v7;
- eliminar uso funcional de `practicas_culturales.cultivo` en base v7;
- resolver nombres desde `cultivo_id`;
- asegurar que `fertilizacion_parcelas` es fuente canonica de parcelas;
- usar `practicas_culturales_parcelas` en v7 y mantener `practica_parcelas`
  como compatibilidad v6;
- usar `codigo_actuacion_siex` y `unidad_normalizada` cuando existan en el
  esquema limpio.

Consumidores a adaptar:

- `modules/fertilizacion.py`;
- `modules/practicas_culturales.py`;
- `scripts/probar_fertilizacion_practicas_v7.py`;
- `scripts/diagnostico_schema_v7.py`.

Consumidores pendientes para fases posteriores:

- informes;
- PDF oficial;
- exportación SIEX;
- revisión SIEX.

Entregable:

- Fertilización compatible con tabla v6 y tabla v7 limpia;
- Prácticas culturales compatible con tabla v6 y tabla v7 limpia;
- prueba aislada contra `runtime/v7/cuadernopro_v7_limpia.db`;
- documento `docs/v7/ESTADO_V7_validaciónresultado de validación.

## v7.4 - Contabilidad limpia

Objetivo:

- usar solo `cliente_id` para ingresos con cliente;
- usar solo `proveedor_id` para gastos con proveedor;
- usar `cultivo_id` para analítica economica por cultivo;
- eliminar uso funcional de `tercero`, `nif_tercero` y `cultivo` texto en
  base v7;
- mantener compatibilidad v6 leyendo/escribiendo legacy solo si la columna
  existe;
- mantener facturas PDF y lineas IVA;
- resolver nombres desde `clientes`, `proveedores` y `cultivos`.

Consumidores a adaptar:

- `modules/contabilidad.py`;
- `scripts/probar_contabilidad_v7.py`;
- `scripts/diagnostico_schema_v7.py`.

Consumidores pendientes para fases posteriores:

- `modules/informes.py`;
- `services/cuadernopro_pdf.py`;
- exportación SIEX si consume contabilidad.

Entregable:

- Contabilidad compatible con tabla v6 y tabla v7 limpia;
- ingresos con `cliente_id` y gastos con `proveedor_id`;
- cultivo asociado mediante `cultivo_id`;
- lineas IVA y facturas PDF mantenidas;
- prueba aislada contra `runtime/v7/cuadernopro_v7_limpia.db`;
- documento `docs/v7/ESTADO_V7_validaciónresultado de validación.

## v7.5 - Tratamientos limpios

Objetivo:

- usar siempre `fecha_inicio` y `fecha_fin`;
- usar `plaga_motivo` como campo limpio de motivo;
- eliminar uso funcional de `fecha`, `producto`, `aplicador`, `equipo`,
  `equipo_id`, `maquinaria_id` y `problema` en base v7;
- mantener compatibilidad v6 leyendo/escribiendo legacy solo si la columna
  existe;
- resolver producto desde `producto_id`;
- resolver aplicador desde `aplicador_id`;
- usar `equipo_aplicacion_id` como columna canonica de equipo;
- mantener `tratamiento_parcelas`, recetas PDF y eficacia.

Consumidores a adaptar:

- `modules/tratamientos.py`;
- `scripts/probar_tratamientos_v7.py`;
- `scripts/diagnostico_schema_v7.py`.

Consumidores pendientes para fases posteriores:

- `modules/revision_siex.py`;
- `services/exportacion_siex.py`;
- `services/cuadernopro_pdf.py`;
- `modules/maquinaria.py` si quedan dependencias de borrado.

Entregable:

- Tratamientos compatible con tabla v6 y tabla v7 limpia;
- alta, listado, duplicado, edición y borrado sin consultas fijas a legacy;
- prueba aislada contra `runtime/v7/cuadernopro_v7_limpia.db`;
- documento `docs/v7/ESTADO_V7_validaciónresultado de validación.

## v7.6 - Informes, PDF y Excel SIEX limpios

Objetivo:

- resolver nombres desde IDs en todos los informes;
- no depender de campos legacy en esquema v7;
- adaptar exportación SIEX a `cultivo_parcelas`;
- adaptar cosecha a `cantidad` + `unidad`;
- adaptar contabilidad a cliente/proveedor estructurado;
- adaptar revisión SIEX para no esperar textos legacy.

Regla:

- ningún informe o exportador debe depender de `cultivo`, `tercero`, `nif_tercero`, `kg`, `cliente`, `nif_cliente`, `fecha`, `problema`, `aplicador` o `equipo_id` si esos campos desaparecen del esquema v7.

Consumidores adaptados:

- `modules/informes.py`;
- `modules/revision_siex.py`;
- `services/cuadernopro_pdf.py`;
- `services/exportacion_siex.py`;
- `scripts/diagnostico_schema_v7.py`;
- `scripts/probar_salidas_v7.py`.

Entregable:

- Informes compatibles con base v6 y base v7 limpia;
- PDF oficial con lecturas estructuradas para tratamientos, fertilización,
  prácticas, cosecha, contabilidad, recetas y facturas;
- Excel asistido SIEX resolviendo nombres desde IDs y tablas puente;
- Revisión SIEX compatible con `cultivos.nombre`,
  `productos_fito.numero_registro` y `cosecha.cantidad`;
- prueba aislada contra `runtime/v7/cuadernopro_v7_limpia.db`;
- documento `docs/v7/ESTADO_V7_validaciónresultado de validación.

## v7.7 - Instalación limpia / base inicial

Objetivo:

- generar base vacía v7;
- cargar o importar catálogos SIEX;
- crear flujo de primera configuración;
- documentar carga inicial de explotación, campanas, parcelas, cultivos, clientes/proveedores, personas, productos y equipos;
- preparar checklist de instalación nueva.

Estado v7.7:

- `core/db.py` crea esquema v7 cuando la base no existe, está vacía o no tiene
  tablas de usuario;
- las bases existentes no se convierten ni se destruyen automáticamente;
- una base con `PRAGMA user_version >= 7` no ejecuta el bloque legacy de
  `crear_tablas()`;
- se crea `scripts/probar_arranque_base_v7.py` para validar que el mecanismo
  real de arranque genera una base v7 limpia;
- se documenta la prueba de Streamlit con `CUADERNOPRO_DB_PATH` separado en
  `docs/v7/ESTADO_V7_7.md`.

Entregable:

- bases nuevas nacen como v7 limpio;
- compatibilidad de arranque con bases v6 existentes;
- prueba aislada contra `runtime/v7/prueba_arranque_v7.db`;
- documento `docs/v7/ESTADO_V7_validaciónresultado de validación.

## v7.8 - Prueba integral sobre base v7 limpia

Objetivo:

- validar el flujo integral de datos sobre una base v7 limpia;
- comprobar explotación, campana, cliente/proveedor, parcela, cultivo,
  maquinaria/equipo, producto fito/persona, tratamiento, fertilización,
  practica cultural, cosecha, contabilidad, informes, revisión SIEX, Excel
  SIEX y PDF oficial;
- ejecutar render Streamlit con AppTest para detectar dependencias legacy de
  interfaz.

Estado v7.8:

- `scripts/probar_flujo_integral_v7.py` confirma flujo integral OK;
- `docs/v7/PRUEBA_INTEGRAL_V7.md` documenta resultados;
- AppTest detecta dependencias legacy pendientes en Explotación, Cultivos,
  Parcelas y Maquinaria.

Entregable:

- prueba integral OK contra `runtime/v7/prueba_integral_v7.db`;
- diagnóstico v7 OK;
- lista documentada de pantallas pendientes para v7.9.

## v7.9 - Adaptar pantallas con dependencias legacy

Objetivo:

- adaptar pantallas que aún rompían al renderizar sobre base v7 limpia;
- no anadir columnas legacy a `core/schema_v7.py`;
- mantener compatibilidad v6 con fallback condicionado por existencia de
  columnas;
- validar Explotación, Cultivos, Parcelas y Maquinaria con AppTest contra
  `runtime/v7/prueba_render_v7.db`.

Estado v7.9:

- `modules/explotacion.py` mapea campos visuales legacy a columnas v7 como
  `municipio`, `identificador_oficial`, `carnet_aplicador`,
  `fecha_revision` y `fecha_proxima_revision`;
- `modules/cultivos.py` usa `cultivos.nombre` y `cultivo_parcelas` como ruta
  principal;
- `modules/parcelas.py` muestra cultivos asociados mediante
  `cultivo_parcelas -> cultivos`;
- `modules/maquinaria.py` adapta fechas de revisión de equipos y usa
  `descripcion` como nombre visual de maquinaria v7;
- `scripts/probar_render_modulosmódulos valida render de los cuatro módulos.

Entregable:

- render OK de Explotación, Cultivos, Parcelas y Maquinaria sobre v7 limpio;
- diagnóstico schema v7 OK, sin columnas legacy prohibidas;
- documento `docs/v7/ESTADO_V7_9.md`.

## v7.13 - Ampliacion limpia de campos utiles

Objetivo:

- anadir campos reales de explotación, maquinaria y equipos de aplicación sin
  recuperar columnas legacy duplicadas;
- mantener `PRAGMA user_version = 7`;
- asegurar bases v7 existentes con una ampliacion idempotente;
- probar insercion, lectura, listados, persistencia, PDF y flujo integral.

Estado v7.13:

- `core/schema_v7.py` incorpora `asegurar_ampliaciones_v7_13(conn)`;
- `core/db.py` aplica la ampliacion al arrancar una base v7 existente;
- Explotación distingue `identificador_oficial` y `registro_autonomico`;
- Maquinaria usa `horas_uso` como campo canónico;
- Equipos incorporan `matricula`, `numero_roma`, `fecha_adquisicion` y
  `capacidad_litros`;
- `scripts/probar_schema_v7_13.py` valida base nueva y ampliacion
  idempotente.

Entregable:

- diagnóstico v7 OK sobre `runtime/v7/prueba_schema_v7_13.db`;
- persistencia/listados/render/flujo integral OK;
- documento `docs/v7/ESTADO_V7_13.md`.

## v7.14 - Prueba completa pre-v8

Objetivo:

- simular un ciclo completo de agricultor nuevo sobre base v7 limpia;
- validar configuración inicial, explotación, campana, terceros, parcelas,
  cultivos, maquinaria, equipos, productos fito, tratamientos, fertilización,
  prácticas, cosecha, contabilidad, informes, Revisión SIEX, Excel SIEX, PDF y
  Mapas/SIGPAC;
- dejar una checklist manual para navegador antes de decidir el paso a v8.0.

Estado v7.14:

- `scripts/probar_pre_v8_v7_14.py` ejecuta la prueba automatizada sobre
  `runtime/v7/prueba_pre_v8_v7_14.db`;
- `docs/v7/PRUEBA_MANUAL_PRE_V8.md` recoge la checklist manual;
- `docs/v7/ESTADO_V7_14.md` documenta resultados y recomendacion.

Entregable:

- prueba pre-v8 automatizada OK;
- diagnóstico v7 OK en bases v7.14;
- auditor visual y persistencia siguen OK;
- recomendacion de candidata v8.0 condicionada a completar prueba manual.

## v7.16 - Cosecha multi-cultivo y multi-parcela

Objetivo:

- permitir una cosecha con varios cultivos, diferenciados por año de plantación;
- permitir varias parcelas por cultivo;
- calcular superficie desde el detalle seleccionado;
- mantener compatibilidad con cosechas antiguas de un solo cultivo.

Entregable:

- tabla puente `cosecha_cultivos`;
- ampliacion idempotente `asegurar_ampliaciones_v7_16(conn)`;
- alta de cosecha con selector multiple de cultivos y parcelas por cultivo;
- informes, PDF, revisión SIEX y Excel SIEX leyendo el detalle con fallback a
  `cosecha.cultivo_id`;
- prueba `scripts/probar_cosecha_multicultivo_v7.py`.

## v7.17 - Cálculo de árboles por marco de plantación

Objetivo:

- permitir que los cultivos lenosos guarden marco de plantación y número
  estimado de árboles;
- calcular árboles a partir de superficie en hectareas y marco en metros;
- permitir que el usuario ajuste manualmente el número calculado;
- mostrar los campos en Cultivos, informes internos y PDF oficial cuando haya
  datos;
- mantener Excel SIEX sin columnas nuevas si no corresponden al formato
  asistido.

Entregable:

- columnas canonicas en `cultivos`: `marco_plantacion` y `numero_arboles`;
- ampliacion idempotente `asegurar_ampliaciones_v7_17(conn)`;
- helper `parsear_marco_plantacion(texto)`;
- helper `calcular_numero_arboles(superficie_ha, marco_plantacion)`;
- prueba `scripts/probar_cultivos_arboles_v7.py`.

## Orden recomendado de implementacion

1. Congelar v6 con tag y ZIP estable.
2. Crear rama v7.
3. Implementar comprobacion de esquema v7.
4. Crear esquema limpio aislado en `core/schema_v7.py`.
5. Adaptar Cosecha, porque concentra `kg`, cliente textual y cultivo textual.
6. Adaptar Fertilización y Prácticas culturales.
7. Adaptar Contabilidad.
8. Adaptar Tratamientos.
9. Adaptar informes, PDF y exportación SIEX.
10. Integrar el esquema v7 en el flujo de instalación nueva.
11. Probar instalación desde cero con base vacía.
12. Validar render de pantallas maestras sobre v7 limpio.
13. Ejecutar prueba manual completa de interfaz para v7.10.

## Primer hito recomendado

El primer hito técnico debería ser `v7.1 - Esquema limpio base nueva`: crear una base nueva sin columnas legacy y un diagnóstico que falle si reaparecen. Sin ese hito, las fases posterhistóricauirán compensando deuda histórica.
