# Descargar CuadernoPro

## Instalador Windows

Descarga el instalador desde la release pública:

```text
CuadernoPro-8.4.6-Setup.exe
```

También se pública:

```text
SHA256SUMS.txt
```

## Verificar SHA256

La verificación SHA256 es opcional, pero recomendable si quieres comprobar que
el archivo descargado coincide con el publicado.

En Windows PowerShell:

```powershell
Get-FileHash .\CuadernoPro-8.4.6-Setup.exe -Algorithm SHA256
```

Compara el resultado con `SHA256SUMS.txt`.

## Instalar

1. Ejecuta `CuadernoPro-8.4.6-Setup.exe`.
2. Sigue el asistente.
3. Abre CuadernoPro desde el acceso directo.

No necesitas Docker, WSL, Python ni terminal.

## Abrir

CuadernoPro arranca como aplicación local y abre la interfaz en el navegador del
equipo.

## Datos

Los datos se guardan en:

```text
Documentos\CuadernoPro
```

Esa carpeta contiene la base SQLite, documentos, backups, exportaciones y datos
de trabajo del usuario.

## Backup

Desde CuadernoPro:

1. Abre `Backup / Restauracion`.
2. Crea una copia de seguridad.
3. Guarda el ZIP en un lugar seguro.

Conserva copias fuera del equipo principal siempre que sea posible.
