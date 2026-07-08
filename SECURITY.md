# Seguridad

## Reportar problemas de seguridad

Si detectas un problema de seguridad en CuadernoPro, no publiques datos reales
ni bases privadas para demostrarlo.

Contacto público definitivo: pendiente.

Mientras no haya un correo público definitivo, abre un aviso mínimo en el canal
del proyecto indicando que quieres reportar una vulnerabilidad, sin incluir
datos sensibles ni instrucciones explotables detalladas.

## Qué reportar

Son ejemplos de problemas de seguridad:

- acceso indebido a bases SQLite o documentos;
- escritura de archivos fuera de las carpetas configuradas;
- restauración insegura de backups o ZIPs;
- exposición accidental de datos personales;
- rutas que permitan sobrescribir archivos no previstos;
- configuraciones que publiquen Streamlit en red sin advertencia clara;
- dependencias con vulnerabilidades relevantes.

## Datos privados

No subas ni compartas:

- bases de datos reales;
- copias de seguridad;
- facturas;
- recetas;
- documentos de explotación;
- exportaciones Excel/PDF con datos personales;
- capturas con NIF, telefonos, direcciones o información sensible;
- claves, tokens, contraseñas o certificados.

Si necesitas reproducir un fallo, usa una base sintética sin datos personales.

## Alcance

CuadernoPro es una aplicación local con SQLite. Aun así, los datos agrarios,
contables y personales pueden ser sensibles. Cualquier cambio que afecte a
rutas, backups, documentos, restauración, red o empaquetado debe revisarse con
especial cuidado.
