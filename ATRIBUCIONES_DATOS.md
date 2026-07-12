# Atribuciones de datos y servicios externos

CuadernoPro consulta opcionalmente datos y servicios de terceros. La aplicación
no es una fuente oficial de datos administrativos, cartográficos o
meteorológicos y no redistribuye copias completas de esos servicios.

Las licencias del código y de la documentación de CuadernoPro no sustituyen las
condiciones propias de cada fuente externa.

## Fuentes utilizadas

| Fuente o servicio | Uso en CuadernoPro | Condiciones y atribución |
| --- | --- | --- |
| SIGPAC / FEGA | Consulta puntual de geometrías y datos de recintos mediante el servicio oficial | Fuente: SIGPAC / FEGA. Los datos deben comprobarse en la fuente oficial y utilizarse conforme a las condiciones de reutilización vigentes del servicio. CuadernoPro no incorpora una copia masiva de SIGPAC. |
| PNOA / IGN / SCNE | Ortofotografía del mapa general mediante WMS | Datos bajo CC BY 4.0. La atribución visible utilizada es `PNOA © IGN/SCNE, CC BY 4.0`. Condiciones: https://www.ign.es/resources/licencia/Condiciones_licenciaUso_IGN.pdf |
| OpenStreetMap | Capa cartográfica base opcional | Datos © OpenStreetMap contributors, disponibles bajo ODbL. Folium muestra la atribución y el enlace exigidos por el proveedor. Condiciones: https://www.openstreetmap.org/copyright |
| RainViewer / MeteoLab Inc. | Teselas temporales de radar de lluvia consultadas al activar la capa opcional | Debe mostrarse una atribución visible a RainViewer con enlace. La API pública se ofrece para uso personal, educativo y comunitario a pequeña escala, sin SLA; para uso comercial o de gran volumen deben acordarse condiciones con el proveedor. Condiciones: https://www.rainviewer.com/api.html |

## RainViewer en v8.4.8

- CuadernoPro consulta en tiempo de ejecución
  `https://api.rainviewer.com/public/weather-maps.json`.
- No se incluye ni redistribuye un archivo histórico de imágenes de radar.
- La capa permanece desactivada inicialmente y el mapa sigue funcionando si el
  servicio no está disponible.
- Se muestra `Radar: RainViewer` con enlace visible dentro del mapa y una nota
  explicativa bajo este.
- La API gratuita disponible desde 2026 ofrece observaciones de las dos últimas
  horas; no ofrece predicción futura, limita el zoom nativo y aplica límites de
  uso. Estas condiciones se verificaron el 12/07/2026.

## Aviso

Los proveedores pueden cambiar disponibilidad, cobertura, licencias o
condiciones. Antes de una distribución comercial, de gran volumen o que dependa
de disponibilidad garantizada, deben revisarse de nuevo las condiciones
vigentes y, cuando corresponda, solicitar autorización al proveedor.

El usuario debe comprobar el origen, actualidad y validez de los datos antes de
usarlos en trámites, inspecciones, comunicaciones oficiales o decisiones
agrarias.
