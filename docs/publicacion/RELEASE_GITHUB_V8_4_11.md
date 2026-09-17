# CuadernoPro v8.4.11 - Seguridad y persistencia de Docker

Actualización de mantenimiento para las instalaciones Docker de CuadernoPro.
Esta release distribuye la imagen Docker y el código fuente. El instalador
Windows disponible sigue siendo el de la versión 8.4.10.

## Cambios

- Base Debian Trixie con Python 3.13 y paquetes del sistema actualizados.
- Dependencias fijadas con hashes y Streamlit 1.64.0 sin GitPython.
- Auditoría de dependencias y escaneo de imágenes AMD64/ARM64 antes de publicar.
- Pruebas de la aplicación y de persistencia al recrear los contenedores.
- Inventario SBOM e informes de seguridad conservados en GitHub Actions.
- Restricciones de capacidades y de escalada de privilegios del contenedor.
- Persistencia de base, documentos, backups y exportaciones en `/app/runtime`.

## Actualización

La imagen de esta versión es `jomarpel74/cuadernopro:8.4.11`. Su publicación
queda condicionada a que finalice correctamente el workflow de Docker.

Crear una copia de seguridad antes de actualizar. Conservar el montaje actual:
`./runtime:/app/runtime` en Compose o el volumen `cuadernopro_data` en Portainer.
No borrar los volúmenes al recrear los contenedores.

**Cambio de acceso en Portainer:** el Compose actualizado vincula el puerto a
`127.0.0.1` por defecto. Para acceder desde otro equipo de una red de confianza,
definir `CUADERNOPRO_BIND_ADDRESS` con la IP privada del servidor en las variables
del stack. Para Internet, utilizar un proxy con HTTPS y autenticación o una VPN.

No cambia el esquema de datos. La actualización conserva los datos existentes
si se mantiene el mismo volumen.

## Seguridad

Los controles bloquean vulnerabilidades conocidas en las dependencias Python
y vulnerabilidades altas o críticas corregibles en las imágenes. Los informes
completos también muestran los avisos restantes, incluidos los que aún no tienen
corrección. Estos controles no constituyen una garantía de ausencia de fallos.

Consultar `docs/SEGURIDAD_DOCKER.md` para el proceso de mantenimiento y validación.
