# Despliegue de la web pública en Plesk

Esta carpeta contiene una web estática inicial para publicar en
`cuadernopro.es`. No incluye bases de datos, instaladores, ZIPs de backup,
Excels ni binarios Windows.

## Despliegue desde el panel de Plesk

1. Entra en Plesk con el usuario del VPS.
2. Abre el dominio `cuadernopro.es`.
3. Ve a **Administrador de archivos**.
4. Entra en la carpeta `httpdocs`.
5. Sube el contenido de `web_publica/`, no la carpeta completa si quieres que
   la portada quede directamente en `https://cuadernopro.es`.
6. Activa o comprueba el certificado SSL Let's Encrypt del dominio.
7. Prueba estas URLs:
   - `https://cuadernopro.es`
   - `https://cuadernopro.es/descargar.html`
8. Configura las redirecciones necesarias desde Plesk:
   - `www.cuadernopro.es` -> `cuadernopro.es`
   - `cuaderno.pro` -> `cuadernopro.es/descargar.html`
   - `cuadernopro.com` -> `cuadernopro.es`
   - `cuadernopro.org` -> `cuadernopro.es`
   - `cuadernopro.eu` -> `cuadernopro.es`

## Comprobación de enlaces

- Release estable: `https://github.com/jomarpel-star/cuadernopro/releases/latest`.
- Instalador Windows recomendado: `https://github.com/jomarpel-star/cuadernopro/releases/download/v8.4.10/CuadernoPro-8.4.10-Setup.exe`.
- SHA256: `https://github.com/jomarpel-star/cuadernopro/releases/download/v8.4.10/SHA256SUMS.txt`.
- Repositorio: `https://github.com/jomarpel-star/cuadernopro`.
- Soporte: `https://github.com/jomarpel-star/cuadernopro/issues`.
- Revisa que no se suben instaladores, bases, backups, runtime, documentos
  reales, catálogos, Excels ni binarios Windows.

## Alternativa por SCP

La ruta real depende de cómo esté configurado Plesk en el VPS. En muchas
instalaciones se parece a:

```bash
/var/www/vhosts/cuadernopro.es/httpdocs/
```

Ejemplo orientativo:

```bash
scp -r web_publica/* usuario@SERVIDOR:/RUTA_REAL_DE_PLESK/httpdocs/
scp web_publica/.htaccess usuario@SERVIDOR:/RUTA_REAL_DE_PLESK/httpdocs/.htaccess
```

Comprueba la ruta exacta en Plesk antes de ejecutar `scp`.
