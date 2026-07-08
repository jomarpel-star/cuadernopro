# Catálogos SIEX/CUE internos

Este documento registra el primer inventario de catálogos SIEX/CUE cargables en CuadernoPro. La finalidad es preparar una normalización interna para exportación asistida, no conectar con SIEX/CUE ni sustituir catálogos oficiales vigentes.

Archivo localizado para desarrollo:

- `data/20250217_Catalogos_SIEX _Circular_PAC_4-2025.zip`

El ZIP no debe versionarse en Git. Las carpetas `data/siex/originales/` y `data/siex/importados/` quedan reservadas para trabajo local e ignoradas por Git.

## Infraestructura creada

- Tabla `siex_catalogos`: cabecera de cada catálogo importado.
- Tabla `siex_catalogos_items`: items normalizados con código, descripción, fechas, activo y `datos_json`.
- Servicio `services/siex_catalogos.py`: lectura de ZIP/Excel, importación,
  diagnóstico y consulta.
- Fachada `services/catalogos_siex_importer.py`: punto reutilizable para UI,
  CLI y pruebas.
- Script `scripts/importar_catalogos_siex.py`: importación manual desde ZIP
  indicando base destino con `--db` o `CUADERNOPRO_DB_PATH`.
- Pantalla `Catálogos SIEX`: estado, importación desde ZIP, diagnóstico y
  consulta de catálogos importados.

En v8.0 los catálogos se usan como apoyo para selección/consulta cuando el
módulo ya lo permite, especialmente en códigos de cultivo. Si no hay catálogos
cargados, los formularios no deben romperse y se conserva la entrada manual
existente.

## Catálogos detectados

| Código interno | Archivo origen | Columnas principales detectadas | Uso previsto en CuadernoPro | Se importa en esta fase | Observaciones |
| --- | --- | --- | --- | --- | --- |
| `cultivo` | `Cultivo.xlsx` | `Código`, `Cultivo`, `Latín`, `EPPO`, `C. UPOV`, `Fecha de alta`, `Fecha de baja` | Normalizar cultivos y futuro `codigo_cultivo_siex` | Sí | 459 items aprox. |
| `variedad_especie_tipo` | `20250217 Catálogo Variedad _ Especie _ Tipo.xlsx` | `Código cultivo`, `Cultivo`, `Código Variedad/ Especie/ Tipo`, `Variedad/ Especie/ Tipo`, `Fecha de baja` | Relacionar cultivos con variedad/especie/tipo cuando proceda | Sí | 19737 items aprox.; usa código secundario. |
| `actividad_agraria` | `Actividad agraria.xlsx` | `Código SIEX`, `Actividad agraria`, `Fecha de baja` | Clasificar actividad agraria si se confirma necesidad | Sí | Catálogo pequeño. |
| `actividad_cubierta` | `Actividad sobre la cubierta.xlsx` | `Código SIEX`, `Actividad sobre la cubierta`, `Fecha de baja` | Normalizar actuaciones sobre cubierta | Sí | Pendiente de encaje funcional. |
| `aprovechamiento` | `Aprovechamiento.xlsx` | `Código SIEX`, `Aprovechamiento`, `Descripción`, `Fecha de baja` | Normalizar aprovechamientos de parcela/cultivo si procede | Sí | Conserva descripción secundaria. |
| `certificacion_ecologica` | `Certificación producción ecológica.xlsx` | `Código SIEX`, `Descripción`, `Fecha de baja` | Marcar certificación ecológica si se añade campo futuro | Sí | No se aplica aún a explotación/cultivos. |
| `destino_cultivo` | `Destino del cultivo.xlsx` | `Código SIEX`, `Destino del cultivo`, `Observaciones`, `Fecha de baja` | Normalizar destino de cultivo/cosecha | Sí | Pendiente de confirmar uso en exportación asistida. |
| `edificaciones_instalaciones` | `Edificaciones e instalaciones.xlsx` | `Código`, `Tipología`, `Código SIEX`, `Edificación e instalación`, `Fecha de baja` | Normalizar instalaciones si CuadernoPro las modela en el futuro | Sí | Usa código secundario para conservar `Código`. |
| `material_vegetal_reproduccion` | `Material vegetal de reproducción.xlsx` | `Código del tipo`, `Tipo de material vegetal de reproducción`, `Código`, `Detalle del tipo`, `Fecha de baja` | Normalizar material vegetal si se añade al cultivo | Sí | Catálogo con doble código/descripcion. |
| `regimen_tenencia` | `Régimen de tenencia.xlsx` | `Código SIEX`, `Régimen de tenencia` | Normalizar régimen de tenencia de parcelas/explotación | Sí | Sin fecha de baja detectada. |
| `regimenes_calidad` | `Regímenes de calidad.xlsx` | `ID_TIPO_IG`, `Tipo_IIGG`, `ID_IIGG`, `IIGG nombre_oficial`, `Categoría`, `Fecha de baja` | Normalizar figuras de calidad si se modelan | Sí | 631 items aprox.; conserva muchos campos en `datos_json`. |
| `sistema_conduccion` | `Sistema de conducción.xlsx` | `Código SIEX`, `Sistema de conducción`, `Definición`, `Fecha de baja` | Normalizar sistema de conducción de cultivos leñosos si procede | Sí | Uso futuro. |
| `sistema_cultivo` | `Sistema de cultivo.xlsx` | `Código SIEX`, `Sistema de cultivo`, `Observaciones`, `Fecha de baja` | Normalizar sistema de cultivo | Sí | Relacionable con `cultivos.sistema` en fase posterior. |
| `sistema_explotacion` | `Sistema de explotación.xlsx` | `Código SIEX`, `Sistema de explotación`, `Fecha de baja` | Normalizar sistema de explotación | Sí | 2 items aprox. |
| `senp` | `Superficies y elementos no productivos (SENP).xlsx` | `Código SIEX`, `Código`, `Tipo`, `Fecha de baja` | Normalizar superficies/elementos no productivos si se añaden | Sí | Uso futuro; no existe módulo SENP actual. |
| `tipo_cobertura_suelo` | `Tipo de cobertura del suelo.xlsx` | `Código SIEX`, `Tipo de cobertura del suelo`, `Fecha de baja` | Normalizar cobertura de suelo | Sí | Uso futuro. |
| `tipo_entidad_asociacion` | `Tipo de entidad - asociación.xlsx` | `Código SIEX`, `Tipo de asociación`, `Fecha de baja` | Normalizar tipo de entidad/asociación si procede | Sí | Uso administrativo futuro. |
| `tipo_titular` | `Tipo de titular.xlsx` | `Código SIEX`, `Forma jurídica`, `Fecha de baja` | Normalizar tipo de titular/forma jurídica | Sí | Relacionable con explotación en fase posterior. |

## Normalización aplicada

Para cada fila se intenta detectar:

- `codigo`: `Código SIEX`, `Código`, `Código cultivo`, `ID_TIPO_IG` o variantes específicas.
- `codigo_secundario`: segundo código cuando el catálogo lo contiene.
- `descripcion`: columna principal del catálogo.
- `descripcion_secundaria`: descripción complementaria si existe.
- `fecha_alta` y `fecha_baja`.
- `activo`: `1` si no hay fecha de baja, `0` si existe.
- `datos_json`: fila Excel completa serializada, sin descartar columnas.

No se inventan códigos ni equivalencias oficiales. Cualquier uso funcional posterior deberá validarse con la documentación SIEX/CUE aplicable.

## Uso manual

```bash
python scripts/importar_catalogos_siex.py \
  "/ruta/al/20250217_Catalogos_SIEX _Circular_PAC_4-2025.zip" \
  --db runtime/cuadernopro.db
```

La reimportación reemplaza únicamente los items del mismo catálogo y vuelve a
insertar la versión importada. No borra campañas, parcelas, cultivos ni otros
datos de CuadernoPro. El ZIP oficial no se guarda en la base, no se versiona en
Git y no debe formar parte del ZIP de release.
