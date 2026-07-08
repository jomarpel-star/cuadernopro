# Estado del esquema v6.1

Este documento describe la primera preparación técnica del esquema v6.1. La fase no adapta formularios, no cambia exportadores, no elimina columnas antiguas y no migra relaciones ambiguas desde campos de texto.

## Objetivo de v6.1

Preparar la base para que fases posteriores puedan normalizar el modelo alrededor de `cultivos` como entidad central por campaña.

## Columnas preparadas

En `cultivos` se asegura la existencia de:

- `campana_id INTEGER`
- `codigo_siex TEXT`
- `superficie REAL`
- `activo INTEGER DEFAULT 1`

En `fertilizaciones` se asegura la existencia de:

- `cultivo_id INTEGER`

En `practicas_culturales` se asegura la existencia de:

- `cultivo_id INTEGER`

En `cosecha` se asegura la existencia de:

- `cultivo_id INTEGER`

Todas estas columnas son compatibles con la base actual: no son `NOT NULL` y no sustituyen todavía los campos existentes.

## Tabla preparada

Se asegura la existencia de `cultivo_parcelas` con:

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `cultivo_id INTEGER NOT NULL`
- `parcela_id INTEGER NOT NULL`
- `superficie REAL`
- `created_at TEXT`
- `updated_at TEXT`

También se preparan índices para:

- `cultivos.campana_id`
- `cultivos.codigo_siex`
- `cultivo_parcelas.cultivo_id`
- `cultivo_parcelas.parcela_id`
- `fertilizaciones.cultivo_id`
- `practicas_culturales.cultivo_id`
- `cosecha.cultivo_id`

## Campos antiguos mantenidos temporalmente

Se mantienen sin cambios:

- `cultivos.parcela_id`
- `cultivos.especie`
- `fertilizaciones.cultivo`
- `practicas_culturales.cultivo`
- `cosecha.cultivo`
- `cosecha.kg`
- `cosecha.parcelas`

Estos campos siguen siendo necesarios para que la aplicación actual no se rompa mientras se adaptan formularios, listados, PDF, informes y exportación asistida.

## Sin migración automática

No se ha hecho migración automática desde campos de texto a `cultivo_id`.

Motivo: los textos actuales pueden ser ambiguos. Un mismo texto de cultivo puede corresponder a varias parcelas, campañas o registros históricos. La relación debe completarse de forma asistida o mediante reglas revisables en una fase posterior.

Tampoco se ha rellenado automáticamente:

- `cultivos.campana_id`
- `cultivos.codigo_siex`
- `cultivos.superficie`
- `fertilizaciones.cultivo_id`
- `practicas_culturales.cultivo_id`
- `cosecha.cultivo_id`
- filas de `cultivo_parcelas`

## Qué queda listo

- Una base nueva creada con `crear_tablas()` tendrá las columnas v6.1.
- Una base existente recibirá solo `ALTER TABLE` seguros para columnas faltantes.
- La tabla `cultivo_parcelas` queda preparada para asociar cultivos con varias parcelas.
- Las actuaciones de fertilización, prácticas y cosecha quedan preparadas para apuntar a `cultivo_id` en fases posteriores.
- El script `scripts/diagnostico_modelo_v6.py` permite revisar el estado del esquema y los registros pendientes.

## Qué queda pendiente

- Completar datos antiguos de `cultivos` que aún no tengan `campana_id`, `codigo_siex`, `superficie` o filas en `cultivo_parcelas`.
- Adaptar `fertilizacion` para seleccionar y guardar `cultivo_id`.
- Adaptar `practicas_culturales` para seleccionar y guardar `cultivo_id`.
- Adaptar `cosecha` para seleccionar y guardar `cultivo_id`.
- Diseñar una revisión asistida para completar relaciones pendientes.
- Decidir cómo rellenar `cultivos.campana_id` en datos existentes.
- Decidir cómo calcular o introducir `cultivos.superficie`.
- Decidir cuándo conectar `codigo_siex` con los catálogos SIEX importados.
- Adaptar exportación asistida SIEX/CUE.
- Adaptar PDF oficial e informes cuando el modelo funcional cambie.

## Riesgo principal

Durante esta fase la aplicación seguirá funcionando con los campos antiguos. Las nuevas columnas estarán vacías en datos existentes hasta que se adapten los módulos y se complete la normalización. Esto es intencionado para evitar relaciones incorrectas.

## v6.2 - Cultivos adaptados

El módulo `Cultivos` queda adaptado para empezar a usar el modelo v6 como entidad central:

- alta de cultivo con campaña asociada en `cultivos.campana_id`;
- selector o campo manual para `cultivos.codigo_siex`;
- superficie propia del cultivo en `cultivos.superficie`;
- estado activo en `cultivos.activo`;
- asociación de una o varias parcelas mediante `cultivo_parcelas`;
- edición segura de campaña, cultivo, variedad, código SIEX, superficie, año de plantación, parcelas, marco, árboles, sistema y estado activo;
- borrado seguro eliminando antes relaciones de `cultivo_parcelas` y bloqueando si el cultivo está usado por tablas con `cultivo_id`.

Para mantener compatibilidad temporal, el módulo sigue rellenando `cultivos.parcela_id` con la primera parcela seleccionada. Esto permite que las partes de la aplicación que aún consultan el campo antiguo no se rompan mientras se adaptan el resto de módulos.

Los cultivos antiguos siguen siendo visibles aunque no tengan `campana_id`, `codigo_siex`, `superficie` o filas en `cultivo_parcelas`. En el listado se muestran como registros incompletos y pueden editarse para completar esos datos.

No se ha realizado migración automática desde datos antiguos. Las relaciones con parcelas solo se escriben cuando el usuario crea o edita un cultivo desde el módulo adaptado.

Queda pendiente adaptar funcionalmente:

- `practicas_culturales`, para guardar y leer `cultivo_id`;
- `cosecha`, para guardar y leer `cultivo_id`;
- exportación asistida SIEX/CUE, informes y PDF oficial, para priorizar el modelo v6 cuando esos módulos se actualicen.

## v6.3 - Fertilización con cultivo_id

El módulo `Fertilización` queda adaptado para empezar a usar `fertilizaciones.cultivo_id`:

- el alta permite seleccionar un cultivo v6 desde `cultivos`;
- el selector prioriza cultivos de la campaña activa cuando están disponibles;
- al guardar se rellena `fertilizaciones.cultivo_id`;
- el campo textual antiguo `fertilizaciones.cultivo` se mantiene y se rellena con el nombre del cultivo seleccionado para conservar compatibilidad;
- si no se selecciona cultivo estructurado, se puede seguir usando cultivo textual;
- cuando el cultivo tiene parcelas en `cultivo_parcelas`, el formulario sugiere esas parcelas;
- la superficie se propone desde `cultivos.superficie` o desde la suma SIGPAC de las parcelas asociadas;
- el listado muestra el cultivo estructurado si existe y el texto antiguo si no existe `cultivo_id`;
- la edición incorpora una asignación segura de cultivo estructurado sin cambiar la lógica existente de fechas, producto, importes, unidades, parcelas o borrado;
- la duplicación copia `cultivo_id` y también el campo textual antiguo.

Los registros antiguos de fertilización siguen siendo válidos aunque solo tengan cultivo textual. No se ha hecho migración automática por coincidencia de texto, porque puede haber ambigüedad entre campañas, parcelas y cultivos históricos.

`Revisión SIEX` se ajusta para no avisar por cultivo textual cuando la fertilización ya tiene `cultivo_id`. Si falta `cultivo_id` pero hay texto, lo marca como pendiente de estructurar; si no hay ningún cultivo, lo marca como aviso.

Queda pendiente adaptar funcionalmente:

- exportación asistida SIEX/CUE, informes y PDF oficial, para priorizar `cultivo_id` cuando esos módulos se actualicen.

## v6.4 - Prácticas culturales con cultivo_id

El módulo `Prácticas culturales` queda adaptado para empezar a usar `practicas_culturales.cultivo_id`:

- el alta permite seleccionar un cultivo v6 desde `cultivos`;
- el selector prioriza cultivos de la campaña activa cuando están disponibles;
- al guardar se rellena `practicas_culturales.cultivo_id`;
- el campo textual antiguo `practicas_culturales.cultivo` se mantiene y se rellena con el nombre del cultivo seleccionado para conservar compatibilidad;
- si no se selecciona cultivo estructurado, se puede seguir usando cultivo textual;
- cuando el cultivo tiene parcelas en `cultivo_parcelas`, el formulario sugiere esas parcelas;
- si no hay filas en `cultivo_parcelas`, se usa como compatibilidad `cultivos.parcela_id` cuando existe;
- la superficie se propone desde `cultivos.superficie` o desde la suma SIGPAC de las parcelas asociadas;
- el listado muestra el cultivo estructurado si existe y el texto antiguo si no existe `cultivo_id`;
- la edición incorpora una asignación segura de cultivo estructurado sin cambiar la lógica existente de fechas, labor, parcelas, superficie, maquinaria, prestador o borrado;
- la duplicación copia `cultivo_id` y también el campo textual antiguo.

Los registros antiguos de prácticas culturales siguen siendo válidos aunque solo tengan cultivo textual. No se ha hecho migración automática por coincidencia de texto, porque puede haber ambigüedad entre campañas, parcelas y cultivos históricos.

`Revisión SIEX` se ajusta para no avisar por cultivo textual cuando la práctica ya tiene `cultivo_id`. Si falta `cultivo_id` pero hay texto, lo marca como pendiente de estructurar; si no hay ningún cultivo, lo marca como aviso.

Queda pendiente adaptar funcionalmente:

- exportación asistida SIEX/CUE, informes y PDF oficial, para priorizar `cultivo_id` cuando esos módulos se actualicen.

## v6.5 - Cosecha con cultivo_id

El módulo `Cosecha` queda adaptado para empezar a usar `cosecha.cultivo_id`:

- el alta permite seleccionar un cultivo v6 desde `cultivos`;
- el selector prioriza cultivos de la campaña activa cuando están disponibles;
- al guardar se rellena `cosecha.cultivo_id`;
- el campo textual antiguo `cosecha.cultivo` se mantiene y se rellena con el nombre del cultivo seleccionado para conservar compatibilidad;
- si no se selecciona cultivo estructurado, se puede seguir usando cultivo textual;
- cuando el cultivo tiene parcelas en `cultivo_parcelas`, el formulario sugiere esas parcelas;
- si no hay filas en `cultivo_parcelas`, se usa como compatibilidad `cultivos.parcela_id` cuando existe;
- el módulo muestra la superficie sugerida desde `cultivos.superficie` o desde la suma SIGPAC de las parcelas asociadas, sin guardarla en nuevos campos;
- el listado muestra el cultivo estructurado si existe y el texto antiguo si no existe `cultivo_id`;
- como la tabla actual guarda la cantidad en `cosecha.kg`, el listado muestra `kg` como cantidad y una unidad derivada `kg`;
- la edición incorpora una asignación segura de cultivo estructurado sin cambiar la lógica existente de fechas, kg, precio, destino, cliente, observaciones o borrado;
- la duplicación copia `cultivo_id` y también el campo textual antiguo.

Los registros antiguos de cosecha siguen siendo válidos aunque solo tengan cultivo textual. No se ha hecho migración automática por coincidencia de texto, porque puede haber ambigüedad entre campañas, parcelas y cultivos históricos.

`Revisión SIEX` se ajusta para no avisar por cultivo textual cuando la cosecha ya tiene `cultivo_id`. Si falta `cultivo_id` pero hay texto, lo marca como pendiente de estructurar; si no hay ningún cultivo, lo marca como aviso.

Con esta fase queda conectado al modelo v6 el eje funcional `Cultivos -> Fertilización -> Prácticas culturales -> Cosecha`. Siguen pendientes la exportación asistida SIEX/CUE, informes y PDF oficial para priorizar `cultivo_id` cuando esos módulos se actualicen.

## v6.7 - Limpieza de duplicidades en Fertilización y Prácticas culturales

Los módulos `Fertilización` y `Prácticas culturales` limpian la interfaz visible para evitar duplicidades entre el campo textual antiguo `cultivo` y el campo estructurado `cultivo_id`:

- el usuario trabaja con un único selector principal `Cultivo` basado en la tabla `cultivos`;
- al guardar se mantiene `cultivo_id` como referencia estructurada;
- los campos textuales legacy `fertilizaciones.cultivo` y `practicas_culturales.cultivo` se siguen rellenando automáticamente desde el cultivo seleccionado para conservar compatibilidad;
- el campo textual manual solo queda disponible cuando se elige `Sin cultivo estructurado`;
- los listados muestran el cultivo legible resuelto desde `cultivo_id` y usan el texto legacy solo como fallback;
- las columnas técnicas `cultivo_id` y `cultivo_origen` se ocultan en la vista normal;
- la edición segura permite reasignar el cultivo estructurado y muestra el cultivo legacy solo como información cuando procede;
- la edición tabular deja de editar directamente el texto legacy de cultivo.

No se han eliminado columnas antiguas ni se han migrado datos automáticamente desde texto. La compatibilidad con registros históricos se mantiene.

## v6.8 - Limpieza de duplicidades en Contabilidad

El módulo `Contabilidad` limpia la interfaz visible para evitar duplicidades entre `tercero`/`nif_tercero` y las relaciones estructuradas `cliente_id`/`proveedor_id`:

- los ingresos trabajan con selector `Cliente` desde la tabla `clientes`;
- los gastos trabajan con selector `Proveedor` desde la tabla `proveedores`;
- al guardar un ingreso se rellena `cliente_id`, se limpia `proveedor_id` y se actualizan `tercero` y `nif_tercero` desde el cliente seleccionado;
- al guardar un gasto se rellena `proveedor_id`, se limpia `cliente_id` y se actualizan `tercero` y `nif_tercero` desde el proveedor seleccionado;
- si se elige `Sin cliente` o `Sin proveedor`, se mantiene la entrada manual de `tercero` y `nif_tercero` como compatibilidad;
- los listados y pendientes muestran el tercero resuelto desde cliente/proveedor y usan el texto legacy solo como fallback;
- la edición segura permite reasignar cliente/proveedor sin exponer campos duplicados contradictorios en el editor tabular;
- informes y PDF oficial resuelven cliente/proveedor desde ID con fallback a `tercero`.

No se han eliminado columnas antiguas, no se ha modificado el esquema físico y no se han migrado datos automáticamente desde texto.

## v6.9 - Limpieza de duplicidades en Tratamientos

El módulo `Tratamientos fitosanitarios` limpia la interfaz visible para trabajar con referencias estructuradas y ocultar IDs técnicos:

- el alta usa selector `Cultivo` desde `cultivos`;
- las parcelas se sugieren desde `cultivo_parcelas` y, si no existe relación v6, desde `cultivos.parcela_id` como compatibilidad;
- el producto se selecciona desde `productos_fito` con etiqueta legible de nombre, número de registro y materia activa;
- el aplicador se selecciona desde `personas`, mostrando nombre y NIF/carné cuando existen;
- el equipo se selecciona desde `equipos_aplicacion`, sin mezclarlo visualmente con maquinaria general;
- el listado muestra cultivo, producto, registro, aplicador, equipo, parcelas, eficacia y recetas como datos legibles;
- la edición tabular usa selectores legibles para cultivo, producto, aplicador y equipo, y deja de exponer `cultivo_id`, `producto_id`, `aplicador_id`, `equipo_id` o `equipo_aplicacion_id`;
- la edición segura permite actualizar parcelas desde un selector legible;
- las recetas PDF y la eficacia B/R/M se mantienen;
- `Revisión SIEX` mantiene avisos prudentes cuando faltan cultivo, producto, aplicador o equipo estructurados.

No se han eliminado columnas antiguas, no se ha modificado el esquema físico y no se han migrado datos automáticamente desde textos legacy.

## v6.11 - Tratamientos con selectores seguros

El alta de `Tratamientos fitosanitarios` refuerza la seguridad de entrada para evitar registros creados por valores reales preseleccionados accidentalmente:

- el selector de cultivo arranca en `Selecciona cultivo...` y no elige automáticamente el primer cultivo real;
- el selector de producto arranca en `Selecciona producto...` y no preselecciona un producto fitosanitario real;
- el selector de aplicador arranca en `Selecciona aplicador...` cuando hay personas disponibles;
- el selector de equipo arranca en `Selecciona equipo de aplicación...` cuando hay equipos de aplicación disponibles;
- la campaña activa puede seguir usándose como valor por defecto visible; si no hay campaña seleccionada, el alta queda bloqueada;
- antes de guardar se valida campaña, cultivo, parcelas, producto, fechas, superficie tratada mayor que cero, aplicador cuando hay personas disponibles y equipo cuando hay equipos disponibles;
- las recetas PDF siguen siendo opcionales y la eficacia mantiene `Sin evaluar` como valor por defecto;
- el duplicado conserva las referencias estructuradas del registro origen y no cae al primer producto real si el origen no tiene producto estructurado;
- el listado normal oculta el identificador interno del tratamiento y mantiene columnas legibles de campaña, cultivo, parcelas, producto, registro, aplicador, equipo, superficie, eficacia y recetas.

No se han eliminado columnas antiguas, no se ha modificado la base de datos y no se han migrado datos automáticamente.
