# Distribución de CuadernoPro

## Mensaje público

CuadernoPro es el cuaderno agrícola libre para que ningún agricultor se quede
sin herramienta.

El programa completo será gratuito para agricultores. No habrá demo capada,
límites artificiales de parcelas, activación, bloqueo por licencia anual ni
funciones esenciales reservadas a una edición de pago.

## Principios

- Software libre con código abierto.
- Licencia de código: GNU GPL v3 o posterior.
- Documentación libre: CC BY-SA 4.0.
- Descarga libre del programa completo.
- Sin activación.
- Sin cuotas obligatorias.
- Datos locales del usuario.
- Marca CuadernoPro controlada para evitar confusión.

## Datos del usuario

CuadernoPro usa SQLite local. En la línea Windows prevista, los datos se
guardarán fuera de la carpeta de instalación, en `Documents/CuadernoPro`.

El usuario conserva su base de datos, documentos, copias de seguridad y
exportaciones. El proyecto no debe incluir datos reales en Git, ZIPs de release,
builds portables ni instaladores.

## Canales de distribución previstos

- Web principal: `cuadernopro.es`.
- Dominio corto: `cuaderno.pro`.
- Otros dominios pueden redirigir a la web principal si procede.
- GitHub Releases como canal técnico de descarga y trazabilidad.
- ZIP limpio del código fuente.
- Build portable Windows si procede.
- Instalador Windows futuro cuando esté validado.

El instalador Windows estable todavía no está prometido. La línea v8.2.0
prepara el build portable sin Docker; el instalador final queda para una fase
posterior.

## Servicios opcionales

El programa completo será gratuito, pero se podrán cobrar servicios
profesionales opcionales:

- instalación;
- puesta en marcha;
- formación;
- soporte prioritario;
- importación de datos;
- adaptaciones personalizadas;
- integraciones o despliegues específicos.

El soporte comunitario puede ser gratuito. El tiempo profesional, los trabajos
a medida y la atención prioritaria se pueden cobrar.

## Donativos y apoyo voluntario

El proyecto podrá aceptar donativos, patrocinios o aportaciones voluntarias para
financiar mantenimiento, documentación, pruebas, infraestructura y soporte
comunitario.

Los donativos no deben convertirse en una activación obligatoria ni en una
limitación artificial del programa completo.

## Marca

La libertad del código no implica libertad para confundir a usuarios usando la
marca oficial en versiones alteradas. Las versiones modificadas pueden existir,
pero deben identificarse de forma honesta y no presentarse como CuadernoPro
oficial sin autorización.
