# Prueba manual pre-v8

## Datos de prueba

Base:

- `runtime/v7/prueba_manual_v7_14.db`

URL:

- `http://192.168.0.13:8517`

Arranque:

```bash
CUADERNOPRO_DB_PATH=runtime/v7/prueba_manual_v7_14.db ./venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8517 --server.headless true
```

PID:

- `runtime/v7/streamlit_v7_14.pid`

## Criterio general

Para cada módulo:

- abre sin error;
- permite crear;
- permite listar;
- permite editar si procede;
- mantiene datos tras recargar;
- no muestra columnas técnicas crudas en listados principales;
- no consulta columnas legacy inexistentes.

## Pulido UX: reseteo de formularios tras guardar

Base sugerida para v7.15:

- `runtime/v7/prueba_manual_v7_15.db`

Arranque:

```bash
CUADERNOPRO_DB_PATH=runtime/v7/prueba_manual_v7_15.db ./venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8517 --server.headless true
```

PID:

- `runtime/v7/streamlit_v7_15.pid`

Criterio adicional tras cada guardado correcto:

- aparece mensaje OK;
- el listado se refresca;
- el formulario de alta queda limpio;
- no se duplica el registro al pulsar de nuevo accidentalmente;
- no se pierden filtros/listados utiles;
- no se cambia la campana activa global salvo en el módulo Campanas.

Comprobar como mínimo:

- crear cliente y proveedor;
- crear parcela;
- crear cultivo;
- crear maquinaria;
- crear equipo de aplicación;
- crear producto fitosanitario;
- crear tratamiento;
- crear fertilización;
- crear practica cultural;
- crear cosecha;
- crear movimiento contable.

## Cosecha multi-cultivo y multi-parcela

Base sugerida para v7.16:

- `runtime/v7/prueba_manual_v7_16.db`

Arranque:

```bash
CUADERNOPRO_DB_PATH=runtime/v7/prueba_manual_v7_16.db ./venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8517 --server.headless true
```

PID:

- `runtime/v7/streamlit_v7_16.pid`

Criterio adicional:

- crear varios cultivos de almendro diferenciados por año de plantación;
- asociar una o varias parcelas a cada cultivo;
- crear una cosecha seleccionando varios cultivos;
- seleccionar parcelas dentro de cada cultivo;
- comprobar que la superficie total coincide con las parcelas seleccionadas;
- guardar y comprobar listado, informes, PDF, revisión SIEX y Excel SIEX;
- editar datos generales de la cosecha y confirmar que no se pierde el
  detalle cultivo/parcela.

## Cultivos: árboles por marco de plantación

Base sugerida para v7.17:

- `runtime/v7/prueba_manual_v7_17.db`

Arranque:

```bash
CUADERNOPRO_DB_PATH=runtime/v7/prueba_manual_v7_17.db ./venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8517 --server.headless true
```

PID:

- `runtime/v7/streamlit_v7_17.pid`

Criterio adicional:

- crear explotación y campana minima;
- crear una parcela con superficie 2.5 ha;
- crear cultivo `Almendro 2018`;
- introducir superficie `2.5` y marco `7x7`;
- comprobar que se calcula aproximadamente `510` árboles;
- guardar y comprobar listado de Cultivos;
- editar el cultivo cambiando el marco a `6x5`;
- comprobar que se propone aproximadamente `833` árboles y que puede
  modificarse manualmente;
- guardar, recargar el módulo y confirmar persistencia;
- generar informes internos, PDF oficial, revisión SIEX y Excel SIEX sin
  excepciones.

## Checklist

| Punto | Módulo | Abre | Crear | Listar | Editar | Recarga | Resultado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Inicio / configuración inicial | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Crear explotación desde cero |
| 2 | Explotación | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Revisar titular, nombre explotación, REGEPA y registro autonómico |
| 3 | Campanas | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Crear 2025/2026 y marcar activa |
| 4 | Terceros / clientes / proveedores | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Cliente, proveedor y aplicador/persona |
| 5 | Parcelas | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Parcela SIGPAC minima |
| 6 | Cultivos | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Almendro asociado a parcela |
| 7 | Maquinaria | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Matricula, ROMA, serie, fecha compra, horas uso |
| 8 | Equipos de aplicación | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Matricula, ROMA, serie, capacidad, revisiones |
| 9 | Productos fitosanitarios | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Número registro, materia activa, plazo seguridad |
| 10 | Tratamientos | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Producto, aplicador, equipo, dosis, caldo y parcelas |
| 11 | Fertilización | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Cultivo, parcelas, producto/tipo, cantidad y unidad |
| 12 | Prácticas culturales | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Labor, cultivo, parcelas, maquinaria/proveedor |
| 13 | Cosecha | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Cultivo, cliente, cantidad, unidad y destino |
| 14 | Contabilidad | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Ingreso, gasto, IVA, total y cobrado/pagado |
| 15 | Informes | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Resumen general y secciones por campana |
| 16 | Cuaderno oficial PDF | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Generar PDF y comprobar tamano |
| 17 | Revisión SIEX | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Ejecutar revisión sin excepcion |
| 18 | Excel SIEX | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Generar Excel asistido y comprobar tamano |
| 19 | Mapas / SIGPAC | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Sin geometría debe avisar sin romper |
| 20 | Backup | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | Crear backup, no restaurar sobre base real |

## Datos mínimos sugeridos

Explotación:

- titular: `Agricultor Pre V8`
- NIF: `00000000V`
- nombre explotación: `Finca Pre V8`
- identificador oficial: `REGEPA-PREV8-001`
- registro autonómico: `REG-AUT-PREV8-001`
- municipio: `Jumilla`
- provincia: `Murcia`

Parcela:

- provincia SIGPAC: `30`
- municipio SIGPAC: `22`
- agregado: `0`
- zona: `0`
- poligono: `7`
- parcela: `45`
- recinto: `2`
- superficie SIGPAC: `4.5`

Cultivo:

- nombre: `Almendro`
- código SIEX: `104`
- superficie: `4.5`
- marco plantación: `6x5`
- número árboles: `1500`

## Resultado manual

Estado actual:

- pendiente de ejecución visual en navegador.

Incidencias:

- ninguna registrada todavía.
