# Campos pendientes SIEX/CUE

Lista inicial de campos y decisiones a resolver para preparar una exportación asistida SIEX/CUE. No implica cambios de base de datos en esta fase.

## A) Pendientes para exportación asistida local

- Detectar campos obligatorios incompletos por explotación, campaña y actuación.
- Confirmar identificador oficial de explotación aplicable: REA, REGEA, REGEPA u otro código exigido por la comunidad autónoma.
- Validar identificación del titular: formato, representante y datos mínimos.
- Preparar códigos normalizados SIEX/CUE de cultivos, variedades y sistemas de cultivo.
- Preparar códigos normalizados de actuaciones: tratamientos, fertilizaciones, prácticas culturales, cosecha y otras labores.
- Normalizar unidades para dosis, caldo, cantidad, superficie y producción.
- Confirmar si productos fertilizantes y fitosanitarios requieren catálogo oficial o código específico.
- Definir superficies por cultivo y campaña cuando una parcela tenga varios cultivos o cambios de uso.
- Mejorar la relación entre cultivo, parcela, recinto y campaña.
- Sustituir en exportación los cultivos de fertilización, prácticas culturales y cosecha como texto por referencias estructuradas cuando exista soporte interno.
- Revisar motivos, labores y tipos de explotación contra catálogos oficiales antes de exportar.
- Crear validación previa a exportación con errores, avisos y recomendaciones.
- Generar Excel, CSV o JSON estructurado para revisión del asesor o agricultor autorizado.
- Incluir resumen de validación en los paquetes de trabajo.
- Registrar trazabilidad local de generación de archivos, sin comunicación telemática.
- Definir qué anexos PDF deben incluirse en un paquete ZIP asistido y cuáles no.

## B) Pendientes para conexión directa futura

Este bloque no forma parte del objetivo inmediato. Solo tendría sentido si en el futuro se decide evaluar una conexión directa con SIEX/CUE o con el Interfaz Único.

- Certificados, firma o mecanismos de identidad técnica.
- Autenticación y autorización.
- Autorización expresa del titular para acceso o comunicación administrativa.
- Alta como aplicación comercial o entidad habilitada, si procede.
- Acceso a entorno de pruebas o preproducción.
- Documentación técnica oficial SIEX/CUE actualizada y aplicable al Interfaz Único.
- Comunicación con CARM u organismo competente para confirmar requisitos técnicos.
- Formato de intercambio para servicios web o mecanismos equivalentes.
- Logs de envío, respuestas oficiales y acuses.
- Gestión de errores de servicios web.
- Reintentos, idempotencia y control de duplicados.
- Auditoría técnica de comunicaciones.
- Procedimiento RGPD específico para comunicación con sistemas administrativos.

