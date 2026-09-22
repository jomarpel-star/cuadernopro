# Datos preparados para solicitar SignPath Foundation

Estado: borrador para revisar y enviar por el mantenedor. No enviado.
Formulario oficial: https://signpath.org/apply

- Project name: CuadernoPro
- Website: https://cuadernopro.es
- Repository: https://github.com/jomarpel-star/cuadernopro
- License: GNU General Public License v3.0
- Public Windows release: https://github.com/jomarpel-star/cuadernopro/releases/tag/v8.4.10
- Maintainer GitHub account: jomarpel-star
- Build: Python 3.13, PyInstaller, Inno Setup; Windows validation in GitHub Actions.
- Distribution: EXE installers in GitHub Releases, linked from the project website.

## Project description

CuadernoPro is a free, open-source agricultural record-keeping application
for farmers. The Windows edition runs locally and stores farm records and
documents on the user's computer. It also provides an independently deployed
Docker edition. We would like to sign our Windows executable, installer and
uninstaller to establish a consistent publisher identity for our releases.

## Technical question to include

Our PyInstaller distribution includes third-party Python native extensions
and DLLs, some of which are unsigned. We understand that the Foundation's
terms do not allow signing upstream binaries as our own. What supported
configuration would you recommend for this application, including Inno Setup's
uninstaller, while complying with your signing policy and Windows Smart App
Control? We do not want to imply that signing the installer alone covers all
executable components.

## El mantenedor debe completar

- Nombre y correo de contacto en el formulario, sin anadirlos a este archivo.
- Confirmacion de MFA y personas responsables de revision y aprobacion.
- Aceptacion de condiciones y politica de privacidad tras revisar las
  conexiones de red de la aplicacion y sus componentes.
- Enlace al workflow Windows cuando los cambios esten integrados en main.

No incluir bases de datos, documentos, claves privadas ni tokens.
