# Contribuir a CuadernoPro

Gracias por querer mejorar CuadernoPro. El objetivo del proyecto es mantener un
cuaderno agrícola libre, completo y útil para agricultores.

## Reportar errores

Al reportar un problema, incluye si puedes:

- versión de CuadernoPro;
- sistema operativo;
- forma de instalación;
- pasos para reproducirlo;
- mensaje de error completo;
- captura solo si no contiene datos privados.

No subas bases de datos reales, facturas, recetas, documentos privados,
exportaciones con datos personales ni ZIPs oficiales de catálogos.

## Proponer mejoras

Describe el problema agrícola o de uso que quieres resolver antes de proponer
una solución técnica. Es útil indicar:

- módulo afectado;
- flujo actual;
- resultado esperado;
- riesgos para datos existentes;
- si requiere cambios de modelo de datos.

## Enviar cambios

Antes de enviar cambios:

- trabaja sobre una rama limpia;
- mantén los cambios acotados;
- evita refactors no relacionados;
- no incluyas datos reales ni artefactos generados;
- conserva compatibilidad con Docker/Linux salvo que el cambio indique lo
  contrario;
- no cambies el modelo de datos sin documentarlo y probarlo.

## Estilo básico

- Python claro, funciones pequeñas cuando sea razonable.
- Reutilizar helpers existentes de `core/`, `modules/` y `services/`.
- Rutas persistentes siempre a traves de `core.paths` cuando aplique.
- SQLite local, sin dependencias externas innecesarias.
- Mensajes para usuarios en castellano claro.

## Pruebas

Antes de proponer una integración importante, ejecuta al menos:

```bash
./venv/bin/python -m py_compile app.py
./venv/bin/python scripts/probar_release_v8.py
git diff --check
```

Para cambios de empaquetado Windows, compila también:

```bash
./venv/bin/python -m py_compile packaging/windows/cuadernopro_launcher.py
```

## Datos reales

No se aceptan contribuciones que incluyan:

- `.db`, `.sqlite` o `.sqlite3`;
- `runtime/`;
- backups;
- facturas, recetas o PDFs reales;
- Excels generados con datos reales;
- ZIPs de catálogos oficiales;
- claves, contraseñas o secretos.
