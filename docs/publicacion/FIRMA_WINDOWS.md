# Distribucion de Windows desde GitHub y cuadernopro.es

Se mantiene el instalador EXE de Inno Setup. No se cambia la distribucion a
Microsoft Store ni se contrata un certificado de pago.

## Estado y limites

El instalador publico 8.4.10 y su ejecutable no tienen firma Authenticode.
Una reinstalacion que funciona no demuestra que todos los equipos vayan a
aceptarlo: Smart App Control considera la reputacion y las firmas de los
archivos que se cargan. SmartScreen es otro control y puede mostrar avisos
de reputacion incluso con firmas validas.

Los recursos de version, los hashes SHA-256 y las pruebas mejoran la
identificacion y trazabilidad. **No sustituyen una firma ni garantizan que
Windows permita ejecutar el programa.**

La version de la aplicacion procede de `core/version.py`. El ejecutable lleva
nombre de producto, version y nombre original. No se usa UPX, para conservar
los binarios de dependencias sin esa transformacion adicional.

## Antes de subir un nuevo instalador

1. Construir desde el commit revisado que se etiquetara como release. El
   workflow `Comprobar instalador Windows` genera un candidato e informa de
   su commit; nunca crea una release ni actualiza la web. Solo se activa en
   cambios relacionados con Windows o manualmente. Los artefactos caducan
   a los tres dias.
2. Superar las pruebas de arranque, instalacion, desinstalacion y persistencia
   con datos temporales. Probar ademas una actualizacion sobre la version
   anterior, apertura de documentos y las funciones principales en una
   maquina Windows limpia con Smart App Control activo.
3. Firmar el ejecutable propio, el instalador y el desinstalador con un
   proveedor aceptado por Windows, usando RSA y sello de tiempo. Inno Setup
   permite integrar `SignTool` y `SignedUninstaller`; la conexion concreta
   se configurara cuando se disponga de proveedor y permisos de firma.
4. Revisar tambien las DLL y extensiones PYD distribuidas. No reemplazar
   firmas de terceros ni dar por hecho que firmar el Setup cubre los archivos
   que instala. Una dependencia sin firma puede seguir siendo bloqueada.
5. Extraer o instalar el **instalador final firmado en una maquina de pruebas**
   para obtener su desinstalador. Ejecutar el control estricto siguiente sobre
   el portable final y los archivos que realmente se van a publicar:

   ```powershell
   .\packaging\windows\audit_windows_release.ps1 `
     -AppDirectory .\dist_windows\CuadernoPro `
     -InstallerPath .\packaging\windows\output\CuadernoPro-8.4.11-Setup.exe `
     -UninstallerPath C:\Pruebas\CuadernoPro\unins000.exe `
     -ExpectedPublisher 'SUJETO EXACTO DEL CERTIFICADO APROBADO'
   ```

   Sustituir version, ruta de pruebas y sujeto por los valores reales. El
   control falla si faltan firmas RSA confiables en algun binario, identidad
   de producto correcta o sello de tiempo en los archivos propios. Exige
   comprobar el desinstalador. No cambia la confianza de Windows ni firma
   archivos. Que pase no sustituye las pruebas funcionales y de seguridad.
6. Subir el instalador comprobado y su `.sha256` a la release de GitHub.
   Apuntar la web a **ese mismo archivo**, sin recompilarlo ni reemplazarlo
   despues. Si cambian los bytes, repetir firma, pruebas y hashes con una
   nueva version.

El modo `-AuditOnly` genera un informe de diagnostico y permite candidatos
sin firma. Un resultado correcto del workflow con ese modo **no acredita
que el candidato este firmado ni autorizado para publicarse**. Hoy no hay
publicacion Windows automatica: el control estricto debe ejecutarse antes
de la subida manual, hasta integrar un proveedor en el proceso completo.

## Primera opcion sin coste: SignPath Foundation

CuadernoPro es publico, tiene licencia GPL-3.0 y dispone de un instalador
publicado. Se puede solicitar el programa gratuito; su aceptacion no esta
garantizada ni hay un plazo comprometido.

Se necesita construir desde el repositorio de forma verificable, MFA en
GitHub y SignPath, roles claros y aprobacion manual de las solicitudes de
firma. Tras la aceptacion se publicara una politica de firma y privacidad
con los datos que exijan. No se anunciara su patrocinio antes de aceptarlo.

**Punto a resolver con SignPath:** sus condiciones no autorizan firmar como
propios binarios de otros proyectos. Se deben indicar las dependencias
Python/DLL/PYD y acordar como tratar las que carecen de firma. El servicio
gratuito no debe presentarse como una solucion garantizada para todos esos
archivos. No se enviaran datos de usuarios: solo codigo publico y artefactos
de compilacion comprobados.

No se deben compartir certificados privados, contrasenas ni tokens en issues,
releases o archivos del repositorio. La solicitud requiere intervencion del
mantenedor y no se ha enviado automaticamente.

## Fuentes oficiales

- [Firmas para Smart App Control](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/code-signing-for-smart-app-control)
- [Pruebas de todos los componentes](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/test-your-app-with-smart-app-control)
- [Reputacion SmartScreen](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
- [SignPath: solicitud gratuita](https://signpath.org/apply)
- [SignPath: condiciones](https://signpath.org/terms.html)
- [Inno Setup: SignTool](https://jrsoftware.org/ishelp/topic_setup_signtool.htm)
- [Inno Setup: SignedUninstaller](https://jrsoftware.org/ishelp/topic_setup_signeduninstaller.htm)
