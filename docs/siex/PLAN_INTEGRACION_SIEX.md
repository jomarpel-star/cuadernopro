# Plan de exportación asistida SIEX/CUE

Este plan propone fases graduales para que CuadernoPro prepare datos y paquetes de trabajo SIEX/CUE sin implementar conexión externa. La tramitación oficial seguirá correspondiendo al agricultor, asesor o entidad autorizada.

## Decisión actual de producto

CuadernoPro seguirá siendo una herramienta local de gestión del cuaderno de explotación. Su objetivo respecto a SIEX/CUE será preparar y revisar datos para exportación asistida. La carga oficial, firma, presentación o comunicación con sistemas administrativos quedará en manos del agricultor, asesor o entidad autorizada.

## Fase 0: Auditoria interna

- Ya iniciada con la matriz de campos CuadernoPro - SIEX/CUE.
- Detectar campos faltantes.
- Revisar estructura de datos y relaciones actuales.
- Identificar datos exportables, datos que requieren normalización y datos que requieren catálogo oficial.
- Mantener la auditoría como documentación, sin cambios funcionales.

## Fase 1: Normalizacion interna

- Añadir campos faltantes solo cuando estén confirmados por documentación oficial o por una necesidad clara de exportación asistida.
- Mejorar relaciones de cultivos, parcelas, recintos y campañas.
- Preparar catálogos internos mapeables a catálogos oficiales.
- Mejorar validaciones de campos obligatorios.
- Normalizar unidades, fechas, superficies y cantidades.
- Definir trazabilidad interna de preparación y generación de archivos.

## Fase 2: Revisión SIEX dentro de CuadernoPro

- Crear un módulo "Revisión SIEX".
- Generar checklist de datos por explotación y campaña.
- Mostrar avisos de campos incompletos o no normalizados.
- Distinguir errores bloqueantes, avisos y recomendaciones.
- No exportar todavía; solo revisar y orientar correcciones.

## Fase 3: Exportador Excel SIEX asistido

- Generar archivo Excel para asesor o agricultor autorizado.
- Incluir pestañas por áreas:
  - Explotación
  - Parcelas SIGPAC
  - Cultivos
  - Tratamientos
  - Fertilización
  - Prácticas culturales
  - Cosecha
  - Maquinaria
  - Validación
- Incluir avisos de campos pendientes en una pestaña de validación.
- No realizar envío telemático ni comunicación con sistemas oficiales.

## Fase 4: Paquete ZIP de exportación asistida

- Generar un paquete ZIP de trabajo para revisión y tramitación.
- Incluir Excel principal.
- Incluir JSON interno con estructura y metadatos locales.
- Incluir CSV si procede.
- Incluir anexos PDF seleccionados cuando sean útiles para la revisión.
- Incluir resumen de validación.
- Registrar trazabilidad local de generación del paquete.

## Fase 5: Conexión directa opcional futura

- Solo se evaluaría si algún día compensa.
- Solo con documentación técnica completa, autorización del titular, certificados y entorno de pruebas.
- Podría requerir Interfaz Único, alta como aplicación comercial o entidad habilitada y requisitos autonómicos.
- No forma parte del objetivo actual de CuadernoPro.

## Recomendacion

Antes de preparar formatos de exportación asistida para Murcia, contactar con la CARM en cuaderno_digital_agri@carm.es para confirmar plantillas admitidas, vías de carga, requisitos autonómicos y criterios de revisión para CUE comercial o tramitación equivalente.
