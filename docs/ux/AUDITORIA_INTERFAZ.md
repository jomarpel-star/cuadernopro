# Auditoria de interfaz de CuadernoPro

## Fecha

2026-07-01 00:48:07 CEST

## URL revisada

URL principal comprobada: `http://127.0.0.1:8501`.

Tambien se comprobo que la instancia Docker responde en `http://127.0.0.1:8503`.

No se uso URL publica. El acceso HTTP local funciono fuera del sandbox. Playwright no estaba instalado. Chromium estaba disponible, pero fallo en modo headless con `unrecognized flag --no-decommit-pooled-pages`. Firefox estaba disponible, pero no genero captura antes de quedar bloqueado en modo headless. La auditoria se completo con inspeccion estructural de Streamlit, widgets, columnas visibles y codigo local.

## Resumen ejecutivo

La aplicacion tiene una estructura funcional amplia y consistente: menu lateral unico, secciones por modulo, flujos separados de listado, alta, duplicado, edicion y borrado seguro. Las ultimas fases v6 han mejorado mucho el uso de selectores estructurados en cosecha, fertilizacion, practicas, contabilidad y tratamientos.

El principal problema UX pendiente es que todavia aparecen campos tecnicos o de compatibilidad en pantallas normales. En varios formularios el selector estructurado existe, pero el valor por defecto es "Sin ..." aunque hay registros maestros disponibles, lo que deja visibles campos manuales legacy y facilita introducir datos contradictorios. Tambien hay listados y editores con columnas `id`, `id_real`, `tabla_origen`, `registro_id` o "IDs que se eliminaran", utiles internamente pero poco claros para un agricultor o asesor no tecnico.

## Hallazgos criticos

- En Cosecha, el alta muestra a la vez `Cultivo`, `Cultivo textual de compatibilidad`, `Cliente / comprador`, `Cliente / comprador manual` y `NIF cliente manual` cuando el valor por defecto es "Sin ...", aunque hay cultivo y cliente disponibles.
- En Fertilizacion y Practicas culturales, el alta muestra `Cultivo` y `Cultivo textual de compatibilidad` por defecto, porque el selector queda en "Sin cultivo estructurado" aunque existen cultivos.
- En Contabilidad, el alta de ingreso muestra `Cliente` junto a `Tercero manual` y `NIF tercero manual` por defecto. La edicion tambien muestra selector y campos manuales en la misma pantalla.
- Varios listados y editores muestran columnas tecnicas visibles: `id`, `id_real`, `tabla_origen`, `id_visual`, `registro_id` y etiquetas como "IDs que se eliminaran".
- Tratamientos tiene selectores estructurados, pero el alta arranca con `Sin cultivo`, `Sin aplicador` y `Sin equipo` aunque hay opciones disponibles. A la vez, el producto queda preseleccionado con un producto real, lo que aumenta el riesgo de registrar un tratamiento con producto incorrecto por defecto.

## Hallazgos medios

- Las tablas principales son anchas: Parcelas, Tratamientos, Contabilidad, Maquinaria, Informes y Catalogos SIEX tienen demasiadas columnas para lectura rapida.
- Los formularios de Tratamientos y Contabilidad son largos y mezclan datos principales, datos tecnicos, documentos y validaciones en una unica pantalla.
- En edicion de Tratamientos aparecen varios bloques de gestion en la misma vista: parcelas, recetas y editor general. El flujo es potente, pero puede resultar denso.
- En Cosecha, Contabilidad y Tratamientos se repiten selectores con el mismo nombre dentro de la edicion, por ejemplo "Cosecha" o "Movimiento", lo que puede confundir.
- Hay nombres inconsistentes entre menu, titulos y botones: "Productos Fito" frente a "Productos fitosanitarios", "Cuaderno oficial" frente a "Cuaderno oficial / PDF", "tercero" frente a "cliente/proveedor".
- La salida tecnica detecta avisos de Streamlit por `use_container_width`, que sera retirado despues de 2025-12-31. No es un problema visual inmediato, pero conviene corregirlo antes de que genere ruido o roturas futuras.

## Hallazgos menores

- El menu lateral es largo y mezcla maestros, operaciones, informes, SIEX, mapas y mantenimiento sin agrupacion visual.
- Algunos botones usan iconos y otros no. La inconsistencia no bloquea, pero resta claridad.
- Los modulos de borrado usan "IDs que se eliminaran"; seria mas claro mostrar etiquetas legibles y dejar el ID en segundo plano.
- Catalogos SIEX y Revision SIEX son necesariamente tecnicos, pero podrian explicar mejor que son pantallas de diagnostico/consulta avanzada.
- Algunas etiquetas conservan nombres internos o formatos poco amables: `agregado_sigpac`, `zona_sigpac`, `sigpac_geojson_estado`, `registro_id`.

## Revision por modulo

### Inicio

Estado general:
- Correcto

Problemas detectados:
- El menu lateral tiene muchas entradas y no agrupa visualmente maestros, trabajos, economia y salidas.
- Los accesos rapidos ayudan, pero pueden duplicar la navegacion lateral.

Mejoras propuestas:
- Agrupar el menu por bloques logicos o reordenar: configuracion, datos base, trabajos de campo, economia, informes/SIEX, mantenimiento.
- Mantener accesos rapidos a las tareas mas frecuentes.

Prioridad:
- Media

### Explotacion

Estado general:
- Mejorable

Problemas detectados:
- En personas y equipos aparecen flujos de edicion/borrado con "IDs que se eliminaran".
- Las secciones usan numeracion SIEX (`1.2`, `1.3`) mezclada con nombres funcionales.

Mejoras propuestas:
- Mostrar nombres de persona/equipo en borrado y ocultar IDs tecnicos.
- Mantener la numeracion SIEX como ayuda secundaria, no como parte principal del nombre.

Prioridad:
- Media

### Campanas

Estado general:
- Mejorable

Problemas detectados:
- La tabla editable muestra columna `id` visible.
- La edicion directa en tabla es rapida, pero puede no ser clara para usuarios no tecnicos.

Mejoras propuestas:
- Ocultar `id` o renombrarlo como "Ref. interna" solo si se necesita.
- Separar mejor "crear campana" de "editar campanas existentes".

Prioridad:
- Media

### Clientes / Proveedores

Estado general:
- Mejorable

Problemas detectados:
- Los listados y editores muestran `id`.
- Clientes y proveedores se renderizan en pestanas, pero ambos contienen formularios muy similares y pueden ocupar mucho espacio.

Mejoras propuestas:
- Ocultar `id` en tablas normales.
- Mostrar tarjetas/resumen de registro activo antes del editor completo.
- Unificar etiquetas de NIF, telefono, direccion y observaciones entre clientes y proveedores.

Prioridad:
- Media

### Parcelas

Estado general:
- Requiere revision

Problemas detectados:
- El listado muestra muchas columnas tecnicas: `id`, codigos SIGPAC, estados de `sigpac_geojson_*` y cultivo asociado.
- El alta incluye `agregado_sigpac` y `zona_sigpac` con nombre tecnico.
- El borrado usa "IDs que se eliminaran".

Mejoras propuestas:
- Crear vista normal con nombre, municipio, poligono, parcela, recinto, superficie y cultivo.
- Mover campos SIGPAC avanzados y geometria a un desplegable "Datos tecnicos".
- En borrado, seleccionar parcelas por etiqueta legible.

Prioridad:
- Alta

### Cultivos

Estado general:
- Mejorable

Problemas detectados:
- El listado muestra `id`.
- En edicion hay un selector "Cultivo" y un campo texto "Cultivo", que pueden parecer duplicados aunque uno selecciona el registro y otro edita el nombre/especie.
- El selector muestra varios cultivos con etiquetas iguales, por ejemplo varias entradas de almendro similares.

Mejoras propuestas:
- Renombrar el selector de edicion a "Registro de cultivo".
- Hacer que las etiquetas incluyan campana, superficie, parcelas y codigo SIEX para diferenciar duplicados.
- Ocultar `id` en listado normal.

Prioridad:
- Media

### Productos Fito

Estado general:
- Mejorable

Problemas detectados:
- Listado y edicion muestran `id`.
- El alta desde `Nº Registro MAPA` es simple, pero no queda claro si autocompleta desde catalogo o si se debe rellenar todo despues.

Mejoras propuestas:
- Ocultar `id`.
- Anadir ayuda breve: "Introduce el registro MAPA para buscar o crear el producto".
- En listado, priorizar nombre comercial, registro y materia activa.

Prioridad:
- Media

### Tratamientos

Estado general:
- Mejorable

Problemas detectados:
- El alta ya usa selectores estructurados de cultivo, producto, aplicador y equipo, pero por defecto deja `Sin cultivo`, `Sin aplicador` y `Sin equipo` aunque hay opciones disponibles.
- El producto queda preseleccionado con un producto real. Esto puede provocar errores si el usuario no cambia el selector.
- La edicion incluye gestion de parcelas, recetas y editor general en una sola vista.
- El listado todavia muestra `id`.

Mejoras propuestas:
- Usar opcion inicial "Selecciona..." para producto, cultivo, aplicador y equipo, y validar antes de guardar.
- Si hay un unico aplicador/equipo activo, sugerirlo pero mostrarlo como sugerencia clara.
- Dividir edicion en bloques mas visibles: datos principales, parcelas, recetas.
- Ocultar `id` del listado normal.

Prioridad:
- Alta

### Fertilizacion

Estado general:
- Requiere revision

Problemas detectados:
- En alta aparecen a la vez `Cultivo` y `Cultivo textual de compatibilidad`.
- El selector queda por defecto en "Sin cultivo estructurado" aunque hay cultivos disponibles.
- El editor conserva columnas tecnicas `id`, `campana_id` y `operario_id` en configuracion visible/usable.

Mejoras propuestas:
- Preseleccionar un cultivo de la campana activa si existe, o usar "Selecciona cultivo".
- Mostrar el campo textual solo cuando el usuario elija explicitamente "Sin cultivo estructurado".
- Sustituir `operario_id` por selector de operario tambien en edicion.
- Ocultar `id` y `campana_id` en la vista normal.

Prioridad:
- Alta

### Practicas culturales

Estado general:
- Requiere revision

Problemas detectados:
- En alta aparecen `Cultivo` y `Cultivo textual de compatibilidad` por defecto.
- El selector queda en "Sin cultivo estructurado" aunque hay cultivos disponibles.
- El listado y editor muestran `id`.

Mejoras propuestas:
- Igual que Fertilizacion: seleccionar cultivo estructurado como flujo principal y ocultar texto legacy salvo compatibilidad explicita.
- Mantener maquinaria/prestador como selectores, pero revisar etiquetas para que no dependan de IDs.
- Ocultar `id` en listado y editor normal.

Prioridad:
- Alta

### Cosecha

Estado general:
- Requiere revision

Problemas detectados:
- En alta se ven `Cultivo`, `Cultivo textual de compatibilidad`, `Cliente / comprador`, `Cliente / comprador manual` y `NIF cliente manual` con valores por defecto "Sin ...".
- En edicion aparecen dos selectores "Cosecha", selector de cultivo, selector de cliente y campos manuales de compatibilidad.
- Listado y editor muestran `id`.

Mejoras propuestas:
- Cambiar el valor inicial a "Selecciona cultivo" y "Selecciona cliente" cuando existan maestros.
- Mostrar cliente/NIF manual solo tras elegir "Sin cliente".
- Renombrar los selectores de edicion: "Cosecha para asignar cultivo" y "Cosecha para asignar cliente".
- Ocultar `id` del listado normal.

Prioridad:
- Alta

### Maquinaria

Estado general:
- Requiere revision

Problemas detectados:
- El listado muestra `id_visual`, `tabla_origen` e `id_real`.
- Mezcla maquinaria general y equipos de aplicacion en la misma tabla, lo cual es util pero tecnicamente visible.
- El editor permite seleccionar "Registro", pero la tabla de apoyo tambien expone origen tecnico.

Mejoras propuestas:
- Mostrar "Tipo de registro" y "Nombre" en lugar de `tabla_origen`/`id_real`.
- Separar visualmente maquinaria general y equipos de aplicacion o usar filtros mas claros.
- Ocultar identificadores tecnicos de la tabla normal.

Prioridad:
- Alta

### Contabilidad

Estado general:
- Requiere revision

Problemas detectados:
- En alta de ingreso aparece selector `Cliente` junto a `Tercero manual` y `NIF tercero manual` porque el valor inicial es "Sin cliente".
- En edicion aparecen selector de cliente/proveedor y campos manuales a la vez.
- En edicion hay varios selectores con etiqueta "Movimiento", lo que dificulta saber si se esta cambiando tercero, facturas o detalle.
- Listado y editor muestran `id`.

Mejoras propuestas:
- Mostrar tercero/NIF manual solo cuando el usuario elija explicitamente "Sin cliente" o "Sin proveedor".
- Renombrar selectores de edicion: "Movimiento para tercero", "Movimiento para facturas", "Movimiento con desglose IVA".
- Ocultar `id` del listado normal.
- Mantener protecciones de IVA y facturas, pero separarlas en secciones mas claras.

Prioridad:
- Alta

### Informes

Estado general:
- Mejorable

Problemas detectados:
- La vista carga muchos bloques y tablas a la vez.
- Algunas tablas muestran `id` o campos internos de movimientos.
- Hay mucha informacion contable/agronomica en una sola pantalla.

Mejoras propuestas:
- Separar por pestanas: economia, tratamientos, fertilizacion, practicas, cosecha.
- Ocultar IDs y priorizar nombres resueltos.
- Permitir exportar por bloque.

Prioridad:
- Media

### Cuaderno oficial

Estado general:
- Correcto

Problemas detectados:
- El flujo principal es comprensible: seleccionar campana, comprobar y generar PDF.
- Depende de avisos de revision que pueden ser tecnicos.

Mejoras propuestas:
- Resumir avisos por impacto: "impide generar", "conviene revisar", "informativo".
- Mantener el boton de generar separado de la revision.

Prioridad:
- Baja

### Revision SIEX

Estado general:
- Mejorable

Problemas detectados:
- La tabla muestra `registro_id`, que es tecnico, aunque tiene sentido para diagnostico.
- Las columnas son utiles pero densas para usuario no tecnico.

Mejoras propuestas:
- Mantener `registro_id` en modo diagnostico, pero mostrar por defecto una etiqueta legible del registro cuando sea posible.
- Anadir agrupacion por area y gravedad.

Prioridad:
- Media

### Catalogos SIEX

Estado general:
- Mejorable

Problemas detectados:
- Pantalla necesariamente tecnica, con columnas `id`, `codigo_catalogo`, archivo origen y version.
- El selector "Detalle de fila original" muestra IDs numericos.

Mejoras propuestas:
- Enfatizar que es una pantalla de consulta tecnica.
- Mostrar descripcion/codigo como etiqueta principal y dejar el ID como referencia secundaria.

Prioridad:
- Baja

### Mapas

Estado general:
- Mejorable

Problemas detectados:
- La pantalla muestra diagnostico de geometrias y botones de actualizacion/reconsulta que pueden resultar sensibles.
- Si no hay mapa visible o geometria cargada, el usuario puede no saber si falta dato o si hubo error de consulta.

Mejoras propuestas:
- Separar claramente mapa, diagnostico y acciones de reconsulta.
- Anadir mensajes de estado por parcela: pendiente, correcta, error.

Prioridad:
- Media

### Backup / Restauracion

Estado general:
- Correcto

Problemas detectados:
- Tiene acciones destructivas bien protegidas con textos de confirmacion.
- La pantalla mezcla copia, restauracion y reset, pero estan separadas por pestanas.

Mejoras propuestas:
- Mantener las confirmaciones actuales.
- Anadir un resumen visible de ultima copia valida si esta disponible.

Prioridad:
- Baja

## Mejoras rapidas recomendadas

- Ocultar columnas `id`, `id_real`, `tabla_origen`, `campana_id`, `operario_id` y similares en listados normales.
- Cambiar "IDs que se eliminaran" por selectores con nombre legible del registro.
- Mostrar campos manuales legacy solo tras elegir explicitamente "Sin cultivo", "Sin cliente" o "Sin proveedor".
- Usar "Selecciona..." como valor inicial en selectores criticos para evitar guardados por defecto incorrectos.
- Renombrar selectores repetidos en edicion para indicar su finalidad concreta.

## Mejoras estructurales recomendadas

- Crear un patron comun de UI v6 para referencias: selector estructurado, etiqueta legible, fallback legacy oculto y columna resuelta en listado.
- Separar ediciones complejas en bloques o pestanas: datos principales, parcelas, documentos, validaciones.
- Definir una vista normal y una vista tecnica/diagnostico para cada tabla ancha.
- Reorganizar el menu lateral por grupos funcionales.
- Sustituir progresivamente `use_container_width` por `width="stretch"` para evitar deprecaciones futuras de Streamlit.

## Siguiente paso propuesto

Corregir primero Fertilizacion, Practicas culturales y Cosecha en una pasada corta de UX, porque comparten el mismo problema: el flujo estructurado existe, pero el formulario muestra campos legacy por defecto. El cambio de mayor impacto seria ocultar `Cultivo textual de compatibilidad`, `Cliente manual` y `NIF manual` salvo cuando el usuario elija explicitamente trabajar sin entidad estructurada.

Despues conviene abordar Maquinaria, porque expone columnas tecnicas (`id_visual`, `tabla_origen`, `id_real`) y se usa como base para tratamientos y practicas.
