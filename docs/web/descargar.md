# Descargar CuadernoPro

## Instalador Windows

Descarga el instalador desde la release pública:

```text
CuadernoPro-8.4.7-Setup.exe
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
certutil -hashfile CuadernoPro-8.4.7-Setup.exe SHA256
```

Compara el resultado con el archivo `SHA256SUMS.txt` publicado en la release de
GitHub.

## Aviso de Windows al instalar

Windows puede mostrar un aviso de seguridad al descargar o ejecutar CuadernoPro
porque el instalador todavía no está firmado digitalmente y el proyecto es
reciente.

Este aviso no significa necesariamente que el programa sea peligroso. Indica
que Windows no reconoce aún al editor o que el archivo no tiene reputación
suficiente.

Para instalar con seguridad:

1. Descarga CuadernoPro solo desde esta página oficial o desde GitHub Releases.
2. Comprueba que el archivo se llama `CuadernoPro-8.4.7-Setup.exe`.
3. Verifica el SHA256 publicado en la release.
4. Si confías en el origen, en el aviso de Windows pulsa `Más información` y
   después `Ejecutar de todas formas`.

Estamos estudiando la firma digital del instalador para futuras versiones.

## Instalar

1. Ejecuta `CuadernoPro-8.4.7-Setup.exe`.
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
