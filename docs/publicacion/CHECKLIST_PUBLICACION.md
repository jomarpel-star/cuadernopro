# Checklist de publicación

## v8.4.2 - Web pública estática para Plesk

- [ ] Revisar la web estática creada en `web_publica/`.
- [ ] Sustituir placeholders de release, instalador, SHA256, repositorio y
  contacto antes de subir a producción.
- [ ] Confirmar que la web no cambia funcionalidad de la aplicación.
- [ ] Confirmar que la web no cambia el modelo de datos.
- [ ] Confirmar que la web no toca Docker, instalador Windows ni bases reales.

## Revisión lingüística

- [ ] Revisar tildes y ortografía de README, web y textos públicos.
- [ ] Ejecutar `./venv/bin/python scripts/auditar_tildes_documentacion.py`
  antes de publicar.
- [ ] Revisar que el tono sea cercano, profesional y sin promesas de
  cumplimiento legal automático.

## Web pública Plesk

- [ ] Revisar `web_publica/` antes de subir a Plesk.
- [ ] Sustituir placeholders de GitHub en `web_publica/descargar.html`.
- [ ] Sustituir placeholders de GitHub en enlaces comunes del footer.
- [ ] Subir el contenido de `web_publica/` a `httpdocs/`.
- [ ] Activar SSL Let's Encrypt en `cuadernopro.es`.
- [ ] Probar `https://cuadernopro.es`.
- [ ] Probar `https://cuadernopro.es/descargar.html`.
- [ ] Configurar redirecciones de dominios desde Plesk.
- [ ] Confirmar que no se suben instaladores, ZIPs, bases, documentos reales,
  PDFs, Excels, runtime ni backups.

Antes de hacer público el repositorio:

- [ ] `git status --short` limpio.
- [ ] No hay bases `.db`.
- [ ] No hay bases `.sqlite`.
- [ ] No hay documentos reales.
- [ ] No hay facturas reales.
- [ ] No hay recetas reales.
- [ ] No hay catálogos ZIP oficiales.
- [ ] `LICENSE` presente.
- [ ] `DISCLAIMER.md` presente.
- [ ] `README.md` revisado.
- [ ] Release revisada.
- [ ] Instalador comprobado.
- [ ] `SHA256SUMS.txt` generado.
- [ ] Repositorio inicialmente privado revisado.
- [ ] Cambiar a público solo tras última revisión.

Comprobaciones recomendadas:

```bash
git status --short
git diff --check
```

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

```bash
find . \
  -path ./.git -prune -o \
  -path ./venv -prune -o \
  -path ./runtime -prune -o \
  -path ./backups -prune -o \
  -type f \( -iname "*.db" -o -iname "*.sqlite" -o -iname "*.zip" -o -iname "*.xlsx" -o -iname "*.exe" -o -iname "*.msi" \) \
  -print
```
