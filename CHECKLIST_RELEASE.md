# Checklist de Release

La checklist vigente para CuadernoPro v8 está en:

[docs/v8/CHECKLIST_RELEASE_V8.md](docs/v8/CHECKLIST_RELEASE_V8.md)

## Antes de publicar en GitHub

- [ ] Revisar que no hay claves ni secretos.
- [ ] Revisar que no hay bases de datos reales.
- [ ] Revisar que no hay documentos PDF reales.
- [ ] Revisar que no hay datos personales.
- [ ] Revisar que no hay catálogos ZIP oficiales versionados.
- [ ] Revisar compatibilidad de dependencias con GPLv3.
- [ ] Revisar `LICENSE`.
- [ ] Revisar `DISCLAIMER.md`.
- [ ] Revisar marca CuadernoPro en `TRADEMARKS.md`.
- [ ] Revisar `README.md`.
- [ ] Revisar tildes y ortografía de README, web y textos públicos.
- [ ] Ejecutar `./venv/bin/python scripts/auditar_tildes_documentacion.py`.
- [ ] Ejecutar grep de referencias antiguas:

```bash
grep -R "a[g]rogex\|A[g]roGEX\|A[G]ROGEX" -n . \
  --exclude-dir=.git \
  --exclude-dir=venv \
  --exclude-dir=runtime \
  --exclude-dir=backups \
  --exclude-dir=__pycache__ \
  --exclude="*.db" \
  --exclude="*.zip"
```

- [ ] Ejecutar `./venv/bin/python scripts/probar_release_v8.py`.
- [ ] Generar ZIP limpio desde commit/tag correcto.
- [ ] Verificar que el ZIP no incluye bases, backups, runtime, documentos
  privados, Excels, ZIPs oficiales, binarios ni instaladores.

Resumen mínimo antes de cerrar una release:

- [ ] `git status --short` sin cambios no deseados.
- [ ] Actualizar `core/version.py`.
- [ ] Verificar que la barra lateral muestra la versión correcta.
- [ ] Comprobar que `APP_VERSION` coincide con el tag a generar.
- [ ] `scripts/probar_release_v8.py` ejecutado con resultado OK.
- [ ] Base limpia diagnosticada.
- [ ] Docker Compose reconstruido y contenedor arrancado.
- [ ] Prueba manual final revisada.
- [ ] ZIP generado desde commit/tag correcto.
- [ ] ZIP sin bases, backups, runtime, exports, venv, caches, documentos
  subidos, PDFs ni Excels.
- [ ] Documentación v8 actualizada.

## v8.2.0

- [ ] Versión visible: `CuadernoPro v8.2.0`.
- [ ] `scripts/probar_release_v8.py` espera `8.2.0`.
- [ ] Spec PyInstaller revisado.
- [ ] Script `build_windows.ps1` preparado para `dist_windows/CuadernoPro`.
- [ ] En Windows, build portable generado con `-Clean`.
- [ ] En Windows, `dist_windows/CuadernoPro/CuadernoPro.exe` probado.
- [ ] Instalador Inno Setup no generado todavía.
- [ ] Modelo de datos sin cambios.

## v8.1.0

- [ ] Versión visible: versión 8.1.0.
- [ ] Licencia GPLv3 o posterior revisada.
- [ ] Documentación legal y distribución revisadas.
- [ ] Empaquetado Windows preparado, sin generar instalador.
- [ ] Modelo de datos sin cambios.
