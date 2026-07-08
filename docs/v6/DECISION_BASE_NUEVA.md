# Decisión sobre base nueva para v6

Este documento analiza si conviene empezar CuadernoPro v6 con una base nueva limpia o migrar la base actual.

## Contexto

La base actual funciona, pero contiene decisiones acumuladas por fases:

- `cultivos` depende de `parcela_id` y no de campaña.
- Varias actuaciones guardan el cultivo como texto.
- Hay campos que nacieron como compatibilidad y ya no representan el modelo objetivo.
- Los catálogos SIEX internos se añadieron después y aún no están conectados al modelo principal.

El usuario ha indicado que, si hace falta, puede empezar con una base nueva y cargar datos reales a mano.

## Ventajas de empezar con base nueva

- Elimina basura histórica.
- Evita migraciones complejas.
- Permite probar el modelo limpio desde cero.
- Reduce riesgo de incoherencias al inferir `cultivo_id`.
- Facilita SIEX/exportación asistida.
- Permite revisar datos reales antes de cargarlos.
- Evita mantener campos legacy durante mucho tiempo.
- Hace más claro qué tablas y columnas pertenecen realmente a v6.

## Inconvenientes de empezar con base nueva

- Hay que reintroducir datos.
- Hay que conservar copia de seguridad de la base antigua.
- Hay que revisar documentos PDF asociados.
- Hay que reimportar catálogos SIEX.
- Hay que reconstruir relaciones entre cultivos, parcelas y actuaciones.
- Puede haber pérdida de comodidad si se necesita consultar histórico antiguo con frecuencia.

## Ventajas de migrar la base actual

- Conserva histórico y documentos enlazados.
- Evita cargar todo manualmente.
- Permite hacer cambios graduales.
- Reduce el riesgo operativo inmediato si hay muchos datos.

## Inconvenientes de migrar la base actual

- Requiere inferencias ambiguas.
- Puede arrastrar errores antiguos.
- Obliga a mantener campos antiguos y nuevos a la vez.
- Complica la lógica de formularios y exportadores durante la transición.
- No garantiza que los datos queden realmente limpios.

## Recomendación

La recomendación para v6 es empezar con base nueva limpia, siempre que el volumen de datos reales a reintroducir sea asumible.

La razón principal es que el cambio central afecta a cómo se entiende un cultivo: debe ser una entidad de campaña, con parcelas asociadas, y usada por todas las actuaciones. Convertir automáticamente textos históricos a esa estructura puede crear relaciones incorrectas difíciles de detectar.

## Proceso seguro si se elige base nueva

1. Crear backup de `cuadernopro.db`.
2. Crear backup completo de `documentos/`.
3. Generar PDF oficial de referencia por campaña.
4. Generar Excel asistido de referencia.
5. Guardar ZIP de código de la versión estable anterior.
6. Renombrar la base antigua, por ejemplo `cuadernopro_v5_backup.db`.
7. Iniciar base nueva vacía.
8. Importar catálogos SIEX.
9. Cargar explotación.
10. Cargar campañas.
11. Cargar parcelas SIGPAC.
12. Cargar cultivos v6 con `campana_id`, superficie y parcelas asociadas.
13. Cargar maquinaria general.
14. Cargar equipos de aplicación.
15. Cargar personas, clientes y proveedores.
16. Cargar productos fitosanitarios.
17. Cargar tratamientos reales.
18. Cargar fertilización real.
19. Cargar prácticas culturales reales.
20. Cargar cosecha real.
21. Adjuntar recetas y facturas si se decide conservar esos documentos en v6.
22. Ejecutar revisión SIEX.
23. Generar Excel asistido v6.
24. Comparar con PDF/Excel de referencia de v5.

## Criterios para decidir definitivamente

Elegir base nueva si:

- Hay pocos datos reales o son fáciles de revisar.
- Se prioriza limpieza frente a histórico exacto.
- Se quiere una v6 sólida para SIEX/exportación asistida.
- Se acepta conservar la base antigua como consulta.

Elegir migración conservadora si:

- Hay mucho histórico que debe mantenerse editable.
- Hay muchos documentos enlazados.
- Los IDs existentes son importantes.
- No hay tiempo para recarga manual.

## Salvaguardas mínimas

- No borrar nunca la base antigua hasta validar v6.
- Guardar backup externo además del backup local.
- Mantener documentos PDF originales.
- Documentar fecha y versión de la base congelada.
- Probar v6 en copia antes de sustituir la instancia real.
