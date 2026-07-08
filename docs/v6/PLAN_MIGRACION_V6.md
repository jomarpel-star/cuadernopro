# Plan de migración v6

Este documento plantea dos caminos posibles para llegar al modelo limpio v6. No ejecuta migraciones ni modifica la base actual.

## Objetivo de la migración

Normalizar CuadernoPro para que:

- cada cultivo pertenezca a una campaña;
- un cultivo pueda estar asociado a varias parcelas;
- tratamientos, fertilización, prácticas y cosecha usen `cultivo_id`;
- los catálogos SIEX/CUE puedan usarse como apoyo real;
- el exportador asistido dependa menos de inferencias y textos libres.

## Camino A: migración conservando base actual

Este camino mantiene `cuadernopro.db` y añade estructura nueva de forma progresiva.

### Fase A1: preparar esquema compatible

- Añadir `campana_id`, `nombre`, `codigo_siex`, `superficie` y observaciones a `cultivos`.
- Crear `cultivo_parcelas`.
- Añadir `cultivo_id` a `fertilizaciones`.
- Añadir `cultivo_id` a `practicas_culturales`.
- Añadir `cultivo_id`, `cantidad` y `unidad` a `cosecha`.
- Añadir `codigo_actuacion_siex` y `unidad_normalizada` donde proceda.

### Fase A2: rellenar datos inferibles

- Crear `cultivo_parcelas` desde `cultivos.parcela_id`.
- Inferir `cultivos.campana_id` desde campañas existentes solo cuando sea seguro.
- Rellenar `fertilizaciones.cultivo_id` comparando texto de cultivo y parcelas.
- Rellenar `practicas_culturales.cultivo_id` comparando texto de cultivo y parcelas.
- Rellenar `cosecha.cultivo_id` comparando texto de cultivo y parcelas.
- Copiar `cosecha.kg` a `cantidad` con `unidad='kg'`.

### Fase A3: compatibilidad temporal

- Mantener campos antiguos mientras módulos y exportadores se adaptan.
- Mostrar avisos de registros sin `cultivo_id`.
- Permitir edición de datos nuevos sin romper vistas antiguas.
- Documentar qué campos quedan legacy.

### Fase A4: cambio funcional progresivo

- Cambiar alta/edición de cultivos para elegir campaña y parcelas.
- Cambiar fertilización para guardar `cultivo_id`.
- Cambiar prácticas para guardar `cultivo_id`.
- Cambiar cosecha para guardar `cultivo_id`, `cantidad` y `unidad`.
- Adaptar revisión SIEX, exportador Excel y PDF oficial.

### Fase A5: limpieza final

- Retirar campos legacy cuando todos los módulos usen el modelo nuevo.
- Revisar índices y claves foráneas.
- Generar backup antes de cualquier eliminación.

### Ventajas del camino A

- Conserva todo el histórico.
- Evita reintroducir datos.
- Permite ir por fases y volver atrás con menos impacto visible.

### Riesgos del camino A

- La inferencia de `cultivo_id` puede ser ambigua.
- Se mantiene deuda técnica durante más tiempo.
- Habrá que escribir migraciones y compatibilidad.
- Se pueden arrastrar errores históricos a v6.

## Camino B: base nueva limpia

Este camino crea una base v6 nueva y carga manualmente los datos reales revisados.

### Fase B1: congelar estado actual

- Backup de `cuadernopro.db`.
- Backup de `documentos/`.
- Generar PDF oficial actual como referencia.
- Generar Excel asistido actual como referencia.
- Guardar ZIP de código estable.

### Fase B2: crear esquema v6

- Arrancar con base limpia.
- Crear tablas v6 sin columnas legacy.
- Importar catálogos SIEX.
- Validar que la aplicación abre con base vacía.

### Fase B3: cargar datos maestros

- Cargar explotación.
- Cargar campañas.
- Cargar parcelas SIGPAC.
- Cargar maquinaria y equipos de aplicación.
- Cargar personas, clientes y proveedores.
- Cargar productos fitosanitarios.

### Fase B4: cargar cultivos v6

- Crear cultivos por campaña.
- Asignar parcelas mediante `cultivo_parcelas`.
- Informar superficie propia.
- Informar `codigo_siex` cuando se confirme.
- Revisar variedad, sistema y año de plantación.

### Fase B5: cargar actuaciones reales

- Cargar tratamientos con `cultivo_id`.
- Cargar fertilización con `cultivo_id`.
- Cargar prácticas culturales con `cultivo_id`.
- Cargar cosecha con `cultivo_id`, `cantidad`, `unidad` y destino.
- Adjuntar recetas y facturas si se decide conservarlas.

### Fase B6: validar v6

- Revisión SIEX sin errores estructurales.
- Exportación Excel asistida con códigos/campos normalizados donde existan.
- PDF oficial coherente por campaña.
- Comparación manual contra PDF/Excel de referencia de la base antigua.

### Ventajas del camino B

- Modelo limpio desde el primer día.
- No arrastra columnas ni datos ambiguos.
- Reduce migraciones complejas.
- Facilita SIEX/exportación asistida.
- Obliga a revisar los datos reales y no solo copiarlos.

### Riesgos del camino B

- Hay que reintroducir datos.
- Hay que revisar documentos asociados.
- Puede llevar más trabajo operativo inicial.
- Requiere conservar la base antigua como archivo de consulta.

## Recomendación final

Para CuadernoPro v6, la recomendación principal es el camino B: base nueva limpia.

Motivo: el cuello de botella no es solo añadir columnas, sino corregir la interpretación funcional de cultivos por campaña y su relación con parcelas. Como el usuario acepta cargar datos reales a mano si hace falta, una base nueva reduce el riesgo de ambigüedades y evita arrastrar compatibilidad histórica.

El camino A solo sería preferible si:

- la base actual contiene mucho histórico difícil de reintroducir;
- los documentos PDF asociados son numerosos y críticos;
- se necesita continuidad exacta de IDs;
- no hay tiempo para revisión manual de datos.

## Orden recomendado si se elige base nueva

1. Cerrar una versión estable actual con backup completo.
2. Diseñar el esquema v6 definitivo en documentación.
3. Implementar esquema v6 en rama o copia de trabajo.
4. Probar arranque con base vacía.
5. Importar catálogos SIEX.
6. Cargar explotación, campañas y parcelas.
7. Cargar cultivos v6.
8. Adaptar tratamientos, fertilización, prácticas y cosecha.
9. Adaptar revisión SIEX, exportador y PDF.
10. Validar contra la base antigua.

## Primeros cambios técnicos de v6

1. Crear `cultivo_parcelas` y redefinir `cultivos` por campaña.
2. Pasar fertilización, prácticas y cosecha a `cultivo_id`.
3. Normalizar cantidades/unidades/códigos SIEX en exportación asistida.
