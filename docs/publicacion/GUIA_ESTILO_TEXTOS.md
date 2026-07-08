# Guía de estilo para textos públicos

Esta guía ayuda a mantener una comunicación coherente en la web, README,
notas de versión, releases y documentación pública de CuadernoPro.

## Castellano cuidado

- Usar castellano con tildes correctas: instalación, configuración,
  documentación, explotación, información, aplicación, versión, publicación,
  restauración, validación, agrícola, prácticas y catálogos.
- Revisar encabezados, listados y llamadas a la acción antes de publicar.
- Mantener un tono cercano y profesional, especialmente en textos dirigidos a
  agricultores.
- Evitar frases artificiales, grandilocuentes o demasiado técnicas cuando haya
  una forma más clara de decir lo mismo.

## Tono

- Explicar qué hace CuadernoPro con claridad y sin exagerar.
- Evitar frases agresivas contra otras empresas, soluciones comerciales o
  administraciones.
- No prometer cumplimiento legal automático.
- Recordar que CuadernoPro ayuda a organizar datos, generar documentos y
  revisar información, pero el usuario debe comprobarla antes de presentarla.

## Terminología recomendada

- Mantener siempre la marca como `CuadernoPro`.
- Usar "cuaderno agrícola" cuando se hable de la herramienta de forma general.
- Usar "cuaderno de explotación" cuando el contexto sea administrativo o de
  gestión de una explotación concreta.
- Usar "software libre" mejor que "open source" en textos para agricultores.
- Usar "copias de seguridad" mejor que "backups" en textos públicos.
- Reservar "backup" para secciones técnicas, comandos, nombres de pantalla o
  textos donde sea el término ya visible en la aplicación.

## Precauciones

- No cambiar nombres de archivos, rutas, comandos, variables, tablas, URLs,
  licencias oficiales ni identificadores técnicos.
- No cambiar nombres técnicos consolidados como SIEX, REGEPA, SQLite, Docker,
  Streamlit, GitHub o Inno Setup.
- No modificar citas legales, SPDX ni nombres oficiales de licencias.

## Revisión antes de publicar

Antes de publicar README, web o notas de release:

1. Revisar tildes y ortografía.
2. Ejecutar `scripts/auditar_tildes_documentacion.py`.
3. Leer los textos principales en GitHub o en la web renderizada.
4. Comprobar que no se han tocado rutas, comandos ni nombres internos.
