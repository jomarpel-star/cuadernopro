# Estado v8.3.3 - PDF de portada y backup documental

## Objetivo del parche

Corregir dos detalles de v8.3.2 antes de avanzar a v8.4.0:

- completar en la portada del PDF oficial los datos de apertura y registros de
  explotación que ya existen en la base;
- hacer que el backup creado desde la app incluya también los documentos
  adjuntos de usuario, especialmente facturas y recetas.

## Correcciones aplicadas

- `services/cuadernopro_pdf.py` usa la campaña solicitada para obtener la fecha
  de apertura desde `campanas.fecha_inicio`.
- `services/cuadernopro_pdf.py` usa `explotacion.identificador_oficial` como
  campo canónico para el registro nacional, con fallback a campos legacy si una
  base antigua los conserva.
- `services/cuadernopro_pdf.py` usa `explotacion.registro_autonomico` para el
  registro autonómico y no reutiliza el identificador nacional como fallback.
- `modules/backup_page.py` crea backups ZIP con la base SQLite y el contenido
  permitido de `DOCS_DIR` bajo `documentos/`.
- `modules/backup_page.py` restaura backups antiguos con solo base y backups
  nuevos con documentos.

## Campos usados en portada PDF

La explotación usada sigue siendo la primera fila real de `explotacion`,
ordenada por `id`, porque esa era la lógica existente del generador.

- Titular: `explotacion.titular`, con fallback a `nombre_explotacion`.
- NIF: `explotacion.nif`.
- Campaña: `campanas.nombre` de la campaña generada.
- Fecha de apertura: `campanas.fecha_inicio`, formateada como `DD/MM/AAAA`.
- Registro de Explotación Nacional: `identificador_oficial`,
  `registro_explotacion`, `codigo_regepa`, `codigo_regea`.
- Registro autonómico: `registro_autonomico` y equivalentes autonómicos legacy
  si existieran.
- Municipio/provincia: `municipio` con fallback a `localidad`, y `provincia`.

## Contenido nuevo del backup

La estructura del ZIP creado desde `Backup / Restauracion` queda asi:

```text
<nombre-base>.db
documentos/
  facturas/
    ...
  recetas/
    ...
```

El backup conserva nombres de archivo y subcarpetas dentro de `DOCS_DIR`.
También evita rutas absolutas, `..`, symlinks, caches, temporales, exports,
backups y la propia base o ZIP si estuvieran dentro del arbol revisado.

## Restauración

- Los `.db`, `.sqlite` y `.zip` antiguos que solo contienen la base siguen
  funcionando.
- Los ZIP nuevos restauran también `documentos/...` dentro de `DOCS_DIR`.
- No se borra el arbol documental actual.
- Si un documento restaurado sobrescribe uno existente, antes se copia el
  existente a `BACKUPS_DIR/documentos_antes_restaurar_*`.

## Pruebas

Ejecutadas correctamente en este parche:

- `./venv/bin/python -m py_compile app.py`
- `./venv/bin/python -m py_compile core/version.py`
- `./venv/bin/python -m py_compile modules/backup_page.py`
- `./venv/bin/python -m py_compile services/cuadernopro_pdf.py`
- `./venv/bin/python -m py_compile scripts/probar_pdf_portada_y_backup_docs_v8.py`
- `./venv/bin/python -m py_compile scripts/probar_release_v8.py`
- `./venv/bin/python scripts/probar_pdf_portada_y_backup_docs_v8.py`
- `./venv/bin/python scripts/probar_release_v8.py`
- `./venv/bin/python scripts/probar_pre_v8_v7_14.py`
- `./venv/bin/python scripts/probar_flujo_integral_v7.py`
- `./venv/bin/python scripts/probar_persistencia_editores_v7.py`
- `git diff --check`
- `git status --short`

La prueba especifica genero el PDF, valido texto de portada, creo un ZIP con
base y documentos ficticios, y comprobo restauración documental en temporal.

## Pendientes

- Sin cambios de modelo de datos.
- Sin cambios en Docker.
- Sin cambios en instaladores.
- Sin incluir bases, PDFs reales, ZIPs ni documentos de usuario en Git.
