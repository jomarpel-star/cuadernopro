# CuadernoPro v8.3.2 - Windows portable e instalador

Esta carpeta prepara el build Windows de CuadernoPro sin Docker, sin WSL y sin
terminal para el usuario final.

## Artefactos

Portable PyInstaller:

```text
dist_windows\CuadernoPro\CuadernoPro.exe
```

Instalador Inno Setup:

```text
packaging\windows\output\CuadernoPro-8.3.2-Setup.exe
```

`dist_windows/`, `build/`, `dist/`, `.venv-windows/`, `packaging/windows/output/`
y los `.exe` generados no deben versionarse en Git.

## Branding e iconos

Los recursos de marca esperados viven en:

```text
assets\branding\cuadernopro.ico
assets\branding\cuadernopro.png
```

`cuadernopro.ico` se usa para el icono de `CuadernoPro.exe`, el instalador
Inno Setup y los accesos directos. `cuadernopro.png` se usa como favicon de
Streamlit cuando existe; si falta, la aplicación mantiene el icono `🚜`.

En modo desarrollo los scripts muestran un aviso si falta
`assets\branding\cuadernopro.ico` y continuan con el icono por defecto. Para
release, ejecutar con `-Release` para bloquear el build si falta el icono:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_installer_windows.ps1 -Clean -Release
```

## Datos del agricultor

El programa instalado no guarda datos reales dentro de la carpeta del programa.
El launcher crea automáticamente:

```text
Documents\CuadernoPro\datos
Documents\CuadernoPro\documentos
Documents\CuadernoPro\copias
Documents\CuadernoPro\exportaciones
Documents\CuadernoPro\logs
```

La base SQLite queda en:

```text
Documents\CuadernoPro\datos\cuadernopro.db
```

El desinstalador de Windows no borra `Documents\CuadernoPro`. Esos datos solo
deben borrarse manualmente por el usuario si está seguro de que no son reales.

## Navegador y cierre de la app

Por defecto, el launcher Windows intenta abrir Microsoft Edge en modo app:

```text
msedge.exe --app=http://127.0.0.1:<puerto> --user-data-dir=Documents\CuadernoPro\browser-profile
```

Ese modo abre una ventana dedicada y permite monitorizar el proceso del
navegador. Al cerrar la ventana, el launcher registra el cierre y termina
`CuadernoPro.exe`.

Si Edge no está disponible, el launcher usa el navegador predeterminado y deja
aviso en logs porque ese modo no permite detectar el cierre de la pestaña o
ventana. Para desarrollo se puede usar:

```powershell
CuadernoPro.exe --no-exit-on-browser-close
CuadernoPro.exe --browser-mode default
```

El launcher crea `Documents\CuadernoPro\cuadernopro.lock` con PID, puerto, URL,
fecha de arranque y raíz de datos. Si el usuario abre CuadernoPro dos veces y
la instancia anterior responde por HTTP, se abre otra ventana al mismo puerto y
no se arranca un segundo servidor Streamlit.

## Requisitos de build

- Windows 10/11.
- PowerShell 5.1 o superior.
- Python compatible con el proyecto.
- Inno Setup 6 para generar el instalador.

Rutas habituales de Inno Setup:

```text
C:\Program Files (x86)\Inno Setup 6\ISCC.exe
C:\Program Files\Inno Setup 6\ISCC.exe
```

Si `ISCC.exe` no existe, instalar Inno Setup 6 y volver a ejecutar.

## Generar portable

Desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_windows.ps1 -Clean
```

El script crea o reutiliza `.venv-windows`, instala dependencias, ejecuta
PyInstaller y valida que el portable no incluya datos reales del proyecto.

## Probar portable

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\test_portable_windows.ps1
```

La prueba usa una carpeta temporal de datos, arranca `CuadernoPro.exe`, espera
HTTP local y cierra el proceso.

## Generar instalador

Desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_installer_windows.ps1 -Clean
```

El script:

1. Comprueba Windows e Inno Setup.
2. Lee la versión desde `core/version.py`.
3. Reconstruye el portable con PyInstaller.
4. Valida que la fuente del instalador no incluya datos reales.
5. Genera `packaging\windows\CuadernoPro.iss` desde la plantilla.
6. Ejecuta `ISCC.exe`.
7. Valida que exista `packaging\windows\output\CuadernoPro-8.3.2-Setup.exe`.

## Probar instalador

Prueba automatizada básica:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\test_installer_windows.ps1
```

La prueba instala en una carpeta temporal, arranca el ejecutable instalado con
un `--data-root` temporal, comprueba respuesta HTTP local, desinstala y confirma
que la carpeta de datos de prueba no se borra.

La comprobacion visual de `CuadernoPro v8.3.2` requiere navegador real porque
Streamlit renderiza parte de la interfaz en el cliente.

## Prueba manual obligatoria

Ejecutar:

```text
packaging\windows\output\CuadernoPro-8.3.2-Setup.exe
```

Comprobar:

1. Instala sin pedir Docker, WSL, Python ni terminal.
2. Crea acceso directo en escritorio.
3. Crea acceso directo en menú inicio.
4. Abre CuadernoPro al finalizar si se deja marcada la opción.
5. Muestra `CuadernoPro v8.3.2`.
6. `CuadernoPro.exe` tiene el icono personalizado.
7. `CuadernoPro-8.3.2-Setup.exe` tiene el icono personalizado.
8. Los accesos directos de escritorio y menú inicio tienen icono.
9. Crea `Documents\CuadernoPro\datos\cuadernopro.db`.
10. Crea logs en `Documents\CuadernoPro\logs`.
11. Abre una ventana dedicada de Edge en modo app si Edge está disponible.
12. Al cerrar esa ventana, `Get-Process CuadernoPro -ErrorAction SilentlyContinue`
    no devuelve procesos.
13. Permite abrir de nuevo desde el acceso directo.
14. Permite llegar a `Inicio / Configuracion`.
15. Desinstala desde Windows.
16. Confirma que `Documents\CuadernoPro` no se borra.

## Archivos fuente relevantes

- `packaging/windows/build_windows.ps1`
- `packaging/windows/test_portable_windows.ps1`
- `packaging/windows/cuadernopro_launcher.py`
- `packaging/windows/CuadernoPro.spec`
- `packaging/windows/CuadernoPro.iss.template`
- `packaging/windows/CuadernoPro.iss`
- `packaging/windows/build_installer_windows.ps1`
- `packaging/windows/test_installer_windows.ps1`

No copiar de vuelta a Raspberry los artefactos generados:

- `packaging/windows/output/`
- `dist_windows/`
- `build/`
- `dist/`
- `.venv-windows/`
- `.exe`
- `.db`
- `.zip` generado
- logs
