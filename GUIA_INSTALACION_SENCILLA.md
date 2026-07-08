# Guía de Instalación Sencilla

Esta guía está pensada para un técnico o usuario con conocimientos básicos que
quiera instalar CuadernoPro desde un ZIP limpio usando Docker Compose.

Versión recomendada: CuadernoPro v8.0.0 estable.

## Requisitos

- Un equipo Linux, Raspberry o NAS con Docker instalado.
- Acceso a terminal.
- ZIP de CuadernoPro.

## Pasos de instalación

1. Descomprimir el ZIP de CuadernoPro.
2. Entrar en la carpeta descomprimida.
3. Ejecutar:

```bash
./install.sh
```

4. Abrir la dirección que muestre el instalador.
5. Completar el asistente inicial de CuadernoPro.

## Parar CuadernoPro

```bash
./stop.sh
```

Este comando detiene los contenedores, pero no borra los datos.

## Arrancar CuadernoPro

```bash
./start.sh
```

## Ver estado

```bash
./status.sh
```

Muestra el estado de Docker Compose, la base de datos local si existe y las
últimas copias de seguridad disponibles.

## Ver logs

```bash
./logs.sh
```

## Crear backup manual

```bash
./backup.sh
```

La copia se guarda como un archivo `.db` dentro de `runtime/backups/`.

## Actualizar CuadernoPro

Para actualizar una instalación distribuida desde ZIP:

1. Sustituir los archivos del programa por los de la nueva versión.
2. Conservar siempre la carpeta `runtime/`.
3. Ejecutar:

```bash
./update.sh
```

El script crea un backup previo de `runtime/cuadernopro.db` si existe y reconstruye
los contenedores con Docker Compose.

Las bases v7 existentes reciben ampliaciones limpias idempotentes al arrancar.
Una instalación nueva nace directamente con el esquema limpio actual.

## Dónde están los datos

- `runtime/cuadernopro.db`: base de datos principal.
- `runtime/backups/`: copias de seguridad.
- `runtime/exports/`: exportaciones generadas por la aplicación.
- `runtime/documentos/`: documentos y ficheros asociados.

## Advertencia

No borres `runtime/` si quieres conservar los datos de CuadernoPro.
