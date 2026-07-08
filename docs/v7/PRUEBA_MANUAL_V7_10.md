# Prueba manual v7.10 - Interfaz sobre base v7 limpia

## Objetivo

Validar CuadernoPro como lo veria un agricultor que empieza desde cero, usando
una base v7 limpia y sin tocar `cuadernopro.db`.

## Base usada

`runtime/v7/prueba_manual_v7_10.db`

Desde la normalización de listados, esta base queda reservada para navegador.
Las pruebas automáticas de listados usan:

`runtime/v7/prueba_listados_v7.db`

No mezclar datos `AUDITORIA LISTADOS V7` en la base manual.

Diagnóstico inicial:

- `PRAGMA user_version`: 7
- número de tablas: 25
- columnas legacy prohibidas detectadas: ninguna
- resultado diagnóstico: OK

## Arranque temporal

Comando:

```bash
CUADERNOPRO_DB_PATH=runtime/v7/prueba_manual_v7_10.db \
./venv/bin/streamlit run app.py \
  --server.address 0.0.0.0 \
  --server.port 8517 \
  --server.headless true
```

URL:

```text
http://192.168.0.13:8517
```

Estado de preparación:

- servidor temporal arrancado en `0.0.0.0:8517`;
- respuesta HTTP local: `200 OK`;
- PID registrado en `runtime/v7/streamlit_v7_10.pid`;
- log registrado en `runtime/v7/streamlit_v7_10.log`.

Al terminar la prueba, detener el proceso temporal de Streamlit. No debe quedar
como servicio.

## Checklist manual

### A) Inicio / Asistente inicial

- [ ] Abrir app.
- [ ] Comprobar que no hay errores al cargar.
- [ ] Completar explotación.
- [ ] Completar datos básicos.
- [ ] Completar persona/aplicador si aparece.
- [ ] Completar equipo si aparece.
- [ ] Guardar y comprobar que avanza correctamente.

### B) Explotación

- [ ] Abrir módulo Explotación.
- [ ] Revisar datos guardados.
- [ ] Editar municipio, provincia, dirección, NIF y titular.
- [ ] Guardar cambios.
- [ ] Comprobar que no falla por `localidad`,
  `carnet_fitosanitario` ni campos legacy.

### C) Campanas

- [ ] Comprobar campana activa.
- [ ] Crear campana `2025/2026` si no existe.
- [ ] Marcar campana activa.
- [ ] Editar fechas.
- [ ] Comprobar guardado.

### D) Clientes / proveedores / personas

- [ ] Crear cliente de prueba.
- [ ] Crear proveedor de prueba.
- [ ] Crear aplicador/persona si procede.
- [ ] Comprobar listados.

### E) Parcelas

- [ ] Crear parcela SIGPAC minima.
- [ ] Usar provincia `30`.
- [ ] Usar municipio `22`.
- [ ] Usar agregado `0`.
- [ ] Usar zona `0`.
- [ ] Informar poligono.
- [ ] Informar parcela.
- [ ] Informar recinto.
- [ ] Informar superficie.
- [ ] Guardar.
- [ ] Listar.
- [ ] Editar.
- [ ] Comprobar que no falla por municipio legacy.

### F) Cultivos

- [ ] Crear cultivo `Almendro`.
- [ ] Asociarlo a parcela mediante `cultivo_parcelas`.
- [ ] Indicar superficie.
- [ ] Indicar código SIEX si procede.
- [ ] Listar.
- [ ] Editar.
- [ ] Comprobar que no falla por `cultivos.parcela_id` ni
  `cultivos.especie`.

### G) Maquinaria / equipos

- [ ] Crear maquinaria general.
- [ ] Crear equipo de aplicación.
- [ ] Revisar fechas de revisión.
- [ ] Guardar.
- [ ] Listar.
- [ ] Editar.
- [ ] Comprobar que no falla por fechas legacy.

### H) Productos fitosanitarios

- [ ] Crear producto de prueba.
- [ ] Informar número de registro.
- [ ] Informar materia activa si procede.
- [ ] Guardar.
- [ ] Listar.

### I) Tratamientos

- [ ] Crear tratamiento.
- [ ] Seleccionar cultivo/parcela.
- [ ] Seleccionar producto.
- [ ] Seleccionar aplicador.
- [ ] Seleccionar equipo.
- [ ] Informar fechas.
- [ ] Informar dosis, caldo y superficie.
- [ ] Informar eficacia.
- [ ] Guardar.
- [ ] Listar.
- [ ] Editar si existe editor.
- [ ] Comprobar receta/documento si procede.

### J) Fertilización

- [ ] Crear fertilización.
- [ ] Seleccionar cultivo/parcela.
- [ ] Informar producto o tipo.
- [ ] Informar dosis/cantidad.
- [ ] Guardar.
- [ ] Listar.
- [ ] Editar.

### K) Prácticas culturales

- [ ] Crear practica.
- [ ] Seleccionar cultivo/parcela.
- [ ] Seleccionar maquinaria/proveedor si procede.
- [ ] Guardar.
- [ ] Listar.
- [ ] Editar.

### L) Cosecha

- [ ] Crear cosecha.
- [ ] Seleccionar cultivo.
- [ ] Seleccionar cliente.
- [ ] Informar kg/cantidad si aparece adaptado.
- [ ] Informar precio si procede.
- [ ] Guardar.
- [ ] Listar.
- [ ] Editar.

### M) Contabilidad

- [ ] Crear ingreso asociado a cliente/cultivo/campana.
- [ ] Crear gasto asociado a proveedor/cultivo/campana.
- [ ] Informar IVA.
- [ ] Adjuntar o simular factura si procede.
- [ ] Comprobar totales.

### N) Informes

- [ ] Abrir informes.
- [ ] Filtrar por campana.
- [ ] Comprobar resumen general.
- [ ] Comprobar tratamientos.
- [ ] Comprobar fertilización.
- [ ] Comprobar prácticas.
- [ ] Comprobar cosecha.
- [ ] Comprobar contabilidad.
- [ ] Comprobar pendientes.

### O) Cuaderno oficial PDF

- [ ] Generar PDF oficial.
- [ ] Comprobar que se crea.
- [ ] Comprobar que no falla por campos legacy.

### P) Revisión SIEX

- [ ] Ejecutar revisión.
- [ ] Comprobar bloqueos/avisos.
- [ ] Confirmar que no hay excepcion.

### Q) Exportación Excel SIEX

- [ ] Generar Excel asistido.
- [ ] Comprobar que se crea.
- [ ] Comprobar que abre o que tiene tamano valido.

### R) Mapas / SIGPAC

- [ ] Abrir módulo Mapas.
- [ ] Comprobar que no rompe con parcela sin geometría.
- [ ] Si intenta consultar SIGPAC, comprobar comportamiento.
- [ ] Si no hay geometría, debe avisar sin romper.

### S) Backup

- [ ] Crear backup desde módulo correspondiente.
- [ ] Comprobar que se genera.
- [ ] No restaurar sobre la base real.

## Resultados de la prueba manual

### Incidencia: campos guardados no visibles en listados

Durante la prueba manual se detecto que varios formularios permitian introducir
datos que luego no aparecian en listados o editores.

Ejemplos:

- nombre de explotación;
- Código REGEPA / identificador oficial;
- `nombre_explotacion = None` mostrado literalmente;
- identificador introducido mostrado bajo `codigo_regea` en vez de como Código
  REGEPA / identificador oficial;
- tabla visual de la pestaña Explotación mostrando nombres internos de
  columnas;
- encabezados tecnicos visibles en Campanas, Parcelas, Tratamientos,
  Productos, Fertilización, Prácticas, Cosecha y Contabilidad;
- `KeyError: responsable_nombre` al abrir Responsable / Asesor;
- `AssertionError` al abrir Contabilidad / Listado;
- Inicio / Configuración inicial / Campaña seguia mostrando `nombre`,
  `fecha_inicio`, `fecha_fin` y `activa`;
- Inicio / Configuración inicial / Explotación no pedia claramente
  `Nombre de la explotacion`, aunque después el resumen lo mostraba;
- número ROMA;
- número de serie;
- fechas;
- campos auxiliares de maquinaria/equipos.

Diagnóstico:

- En maquinaria general v7 el nombre persistente es `descripcion`, no
  `nombre`.
- En maquinaria general v7 existen `matricula`, `numero_roma`, `tipo`,
  `marca`, `modelo` y `observaciones`, pero no existen `numero_serie`,
  `fecha_compra` ni `num_horas`.
- En equipos de aplicación v7 existen `numero_serie`, `fecha_revision` y
  `fecha_proxima_revision`, pero no existen `numero_roma`,
  `fecha_adquisicion` ni `capacidad_litros`.
- En personas v7 existe `carnet_aplicador`, pero no
  `fecha_caducidad_carnet`.
- El `KeyError: responsable_nombre` se debia a renombrar fisicamente columnas
  de un `st.data_editor` y guardar luego esperando nombres internos.
- El `AssertionError` se debia a un `assert` de desarrollo dentro del render de
  Contabilidad que exigia dtype `datetime64` para `fecha`.
- La incoherencia Titular / Nombre de explotación se debia a que el asistente
  solo recogia el titular legal y no persistia `nombre_explotacion`.

Correcciones aplicadas:

- `modules/explotacion.py` muestra en el resumen/listado el nombre de
  explotación y el Código REGEPA / identificador oficial.
- `modules/explotacion.py` guarda el Código REGEPA / identificador oficial en
  `identificador_oficial` y mantiene compatibilidad con `codigo_regepa` /
  `codigo_regea` si existen en bases antiguas.
- `modules/explotacion.py` deja de mostrar `codigo_regea` y `codigo_regepa`
  como columnas separadas en la pestaña Explotación sobre v7 limpia.
- `modules/explotacion.py` usa etiquetas limpias para Nombre de la explotación
  y Código REGEPA / identificador oficial.
- `modules/explotacion.py` renombra el DataFrame antes de pasarlo al
  `st.data_editor` y mapea de vuelta las etiquetas visuales al guardar.
- `modules/explotacion.py` muestra Datos del titular, Datos de la explotación,
  Responsable y Asesor como vista limpia; la edición queda en desplegable.
- `modules/explotacion.py` muestra Personas relacionadas y Equipos de
  aplicación con etiquetas limpias en el editor.
- `modules/explotacion.py` mantiene columnas internas en Responsable / Asesor
  y usa `column_config` para mostrar etiquetas limpias.
- `modules/explotacion.py` pasa una vista visual limpia al borrado seguro de la
  sección para que no reaparezcan columnas internas al seleccionar registros.
- `core/borrado.py` normaliza la previsualizacion de borrado en todos los
  módulos y mantiene `ID` solo para confirmar eliminaciónion.
- `modules/contabilidad.py` elimina el `assert` de fecha y convierte con
  `pd.to_datetime(..., errors="coerce")`.
- `modules/asistente_inicio.py` corrige la tabla de Campaña del asistente
  inicial para mostrar `Campaña`, `Fecha inicio`, `Fecha fin` y `Activa`.
- `modules/asistente_inicio.py` añade `Nombre de la explotacion` al formulario
  inicial y lo guarda en `nombre_explotacion`.
- Si ese campo se deja vacío, se persiste `Titular / razon social` como
  fallback en `nombre_explotacion`.
- `modules/explotacion.py` muestra el titular como fallback visual si una fila
  antigua aún tiene `nombre_explotacion` vacío.
- `modules/explotacion.py` recupera esos campos en el editor sin perderlos al
  guardar otros cambios.
- `core/ui_tablas.py` centraliza etiquetas visibles y ocultacion de columnas
  técnicas.
- Se normalizan listados principales de Campanas, Parcelas, Cultivos,
  Maquinaria, Productos fito, Tratamientos, Fertilización, Prácticas,
  Cosecha y Contabilidad.
- Se normalizan tablas auxiliares visibles de Tratamientos, Contabilidad y alta
  de Productos fitosanitarios.
- `scripts/probar_listados_v7.py` usa `runtime/v7/prueba_listados_v7.db`.
- `scripts/auditar_tablas_visuales_v7.py` detecta usos pendientes de
  `st.dataframe`, `st.data_editor` y `st.table`.
- `modules/explotacion.py` no marca los datos básicos como incompletos por
  `tipo_explotacion` cuando esa columna no existe en v7 limpia.
- `modules/maquinaria.py` muestra y edita `Nombre / descripcion` sobre
  `descripcion` cuando no existe `nombre`.
- `modules/maquinaria.py` incorpora `matricula` en formulario, listado,
  previsualizacion y editor.
- `modules/maquinaria.py` oculta `fecha_compra`, `num_horas` y `numero_serie`
  si esas columnas no existen.
- `modules/explotacion.py` oculta campos de equipos no persistibles en v7:
  `numero_roma`, `fecha_adquisicion` y `capacidad_litros`.
- `modules/explotacion.py` muestra las fechas de equipo como
  `fecha_revision` y `fecha_proxima_revision`.
- `modules/explotacion.py` oculta `fecha_caducidad_carnet` en personas si la
  columna no existe.
- Se crea `scripts/probar_listados_v7.py` para verificar por consultas directas
  que los campos guardados se recuperan para listados.

Resultado automatizado:

- `scripts/probar_listados_v7.py`: OK.
- `scripts/auditar_tablas_visuales_v7.py`: 45 llamadas detectadas, 25 OK y 20
  advertencias pendientes.
- `scripts/probar_render_modulos_v7.py`: OK incluyendo Explotación Responsable
  / Asesor y Contabilidad / Listado vacío.
- Auditoria visual actualizada: 46 llamadas detectadas, 28 OK y 18
  advertencias pendientes.
- Tras corregir Campaña del asistente inicial: 46 llamadas detectadas, 29 OK y
  17 advertencias pendientes.
- `scripts/probar_listados_v7.py`: OK con nombre de explotación explicito y
  fallback desde titular.
- `scripts/probar_render_modulos_v7.py`: OK con fallback de nombre en el
  asistente.

Pendientes:

- Revisar visualmente en navegador que Explotación ya muestra nombre y Código
  REGEPA / identificador oficial tras crear/editar.
- Revisar visualmente que Explotación, Campanas, Parcelas, Cultivos,
  Tratamientos, Fertilización, Prácticas, Productos y Cosecha no muestran
  encabezados tecnicos crudos en listados principales.
- Revisar visualmente Inicio / Configuración inicial / Campaña sin encabezados
  `nombre`, `fecha_inicio`, `fecha_fin`, `activa`.
- Revisar visualmente Inicio / Configuración inicial / Explotación con
  `Nombre de la explotacion` y `Titular / razon social` separados.
- Repetir la prueba manual visual en navegador tras estas correcciones.
- Normalizar editores complejos de Contabilidad, Cosecha, Fertilización,
  Prácticas y Tratamientos en v7.11.
- Revisar si producto quiere conservar datos no existentes en v7, como
  `fecha_compra` o `num_horas`, en una futura ampliacion limpia del esquema.

| Módulo | Acción probada | Resultado | Error exacto | Captura o descripcion | Prioridad |
| --- | --- | --- | --- | --- | --- |
| Inicio / Asistente inicial | Carga y flujo inicial | PENDIENTE | - | - | alta |
| Explotación | Revisar, editar y guardar datos básicos | PENDIENTE | - | Corregido por código; pendiente revisión visual de nombre, Código REGEPA / identificador oficial y Responsable / Asesor sin `KeyError`. | alta |
| Inicio / Configuración inicial / Explotación | Crear explotación inicial | PENDIENTE | - | Corregido por código; debe pedir Nombre de la explotación y Titular / razon social. | alta |
| Inicio / Configuración inicial / Campaña | Revisar tabla de campañas creadas | PENDIENTE | - | Corregido por código; debe mostrar Campaña, Fecha inicio, Fecha fin y Activa. | alta |
| Campanas | Crear/editar campana activa | PENDIENTE | - | - | alta |
| Clientes / proveedores / personas | Crear terceros y aplicador | PENDIENTE | - | - | alta |
| Parcelas | Crear, listar y editar parcela SIGPAC minima | PENDIENTE | - | - | alta |
| Cultivos | Crear cultivo y asociarlo a parcela | PENDIENTE | - | - | alta |
| Maquinaria / equipos | Crear maquinaria y equipo de aplicación | PENDIENTE | - | - | alta |
| Productos fitosanitarios | Crear y listar producto | PENDIENTE | - | - | alta |
| Tratamientos | Crear/listar/editar tratamiento | PENDIENTE | - | - | alta |
| Fertilización | Crear/listar/editar fertilización | PENDIENTE | - | - | alta |
| Prácticas culturales | Crear/listar/editar practica | PENDIENTE | - | - | alta |
| Cosecha | Crear/listar/editar cosecha | PENDIENTE | - | - | alta |
| Contabilidad | Abrir listado y comprobar totales | PENDIENTE | - | Corregido por código; pendiente revisión visual de listado sin `AssertionError`. | alta |
| Informes | Abrir y filtrar informes | PENDIENTE | - | - | media |
| Cuaderno oficial PDF | Generar PDF oficial | PENDIENTE | - | - | alta |
| Revisión SIEX | Ejecutar revisión | PENDIENTE | - | - | media |
| Exportación Excel SIEX | Generar Excel asistido | PENDIENTE | - | - | media |
| Mapas / SIGPAC | Abrir módulo y revisar parcela sin geometría | PENDIENTE | - | - | media |
| Backup | Crear backup desde la app | PENDIENTE | - | - | baja |

## Validaciones finales previstas

Ejecutadas antes de la prueba manual:

```bash
./venv/bin/python -m py_compile app.py
./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v7/prueba_manual_v7_10.db
./venv/bin/python scripts/probar_flujo_integral_v7.py
./venv/bin/python scripts/probar_render_modulos_v7.py
```

Resultado:

- `py_compile app.py`: OK
- diagnóstico de `runtime/v7/prueba_manual_v7_10.db`: OK
- flujo integral v7: OK
- revisión SIEX por script integral: OK
- Excel SIEX por script integral: OK, 15429 bytes
- PDF oficial por script integral: OK, 27833 bytes
- render AppTest de Explotación, Cultivos, Parcelas y Maquinaria: OK

Ejecutar de nuevo al terminar la prueba manual:

```bash
./venv/bin/python scripts/diagnostico_schema_v7.py runtime/v7/prueba_manual_v7_10.db
./venv/bin/python scripts/probar_flujo_integral_v7.py
./venv/bin/python scripts/probar_render_modulos_v7.py
./venv/bin/python -m py_compile app.py
git diff --check
git status --short
```

## Resultado final

Pendiente de completar tras la prueba manual en navegador.

Resumen a rellenar:

- módulos OK:
- módulos con fallo:
- errores exactos:
- PDF oficial generado:
- Excel SIEX generado:
- Revisión SIEX:
- Mapas/SIGPAC:
- recomendacion v7.11:

## Seguimiento v7.11 - editores y pantallas auxiliares

Se prepara una base manual separada para la siguiente ronda:

- `runtime/v7/prueba_manual_v7_11.db`

Y dos bases auxiliares:

- `runtime/v7/prueba_editores_v7.db`
- `runtime/v7/prueba_auxiliares_v7.db`

Correcciones aplicadas en v7.11:

- asistente inicial: tabla de personas con etiquetas limpias.
- catálogos SIEX: tablas visuales con etiquetas comprensibles.
- informes: resumenes y detalles por helper visual comun.
- revisión SIEX: resultado con etiquetas limpias.
- mapas: avisos SIGPAC sin columnas técnicas crudas.
- terceros: listado visual limpio y editor con `column_config`.
- contabilidad y tratamientos: editores complejos mantienen columnas internas y
  muestran etiquetas limpias mediante `column_config`.

Resultado automatizado actual:

- `scripts/auditar_tablas_visuales_v7.py`: 47 llamadas, 0 advertencias.
- `scripts/probar_editores_auxiliares_v7.py`: OK.

Prueba manual pendiente en v7.11:

- Inicio / configuración inicial.
- Explotación.
- Tratamientos.
- Fertilización.
- Prácticas culturales.
- Cosecha.
- Contabilidad.
- Informes.
- Revisión SIEX.
- Mapas.

Criterio: no deben verse columnas técnicas crudas en flujo normal y no deben
aparecer `KeyError`, `AssertionError` ni errores de guardado por columnas
renombradas.
