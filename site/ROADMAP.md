# ROADMAP — Convertidor de Archivos

## Estado actual

**Versión vigente:** v1.1.1
**Estado general:** Estable / publicada
**Plataforma principal:** Windows 64-bit

> La ruta futura conserva la planificación original del proyecto. Los estados
> pueden cambiar conforme evolucione el desarrollo.

> Nota histórica: el primer tag y release público conservado en GitHub es
> `v1.0.1`. Para documentar el origen real del proyecto, el roadmap incorpora
> `v1.0.0` como versión histórica reconstruida del convertidor inicial; no se
> presenta como un release público que nunca existió.

---

## v1.0.0 — Convertidor inicial

**Estado:** Aplicada
**Hito histórico:** versión inicial reconstruida / sin tag público

Primera etapa del proyecto, centrada únicamente en convertir un archivo de un
formato a otro desde el flujo principal.

### Base funcional

- Seleccionar un archivo de origen.
- Elegir un formato de destino compatible.
- Ejecutar la conversión.
- Guardar el archivo resultante.
- Interfaz de escritorio para el flujo de conversión.
- Sin menú de herramientas especializadas.

---

## v1.0.1 — Primera versión pública estable

**Estado:** Aplicada

Primera versión pública estable y distribuible del proyecto.

### Conversión

- Imágenes.
- Documentos.
- Hojas de cálculo.
- Presentaciones.
- PDF.
- Libros y formatos de marcado.
- Archivos comprimidos.
- Compatibilidad con JAR.
- Contenedores de Minecraft.
- Conversión múltiple.
- Previsualización de archivos.
- Procesamiento local.

### Motores incluidos

- LibreOffice.
- ImageMagick.
- 7-Zip.
- Pandoc.
- PDFium y bibliotecas internas.
- Microsoft Office y WinRAR aprovechados de forma opcional cuando están disponibles.

### Presentación

- Nuevo logo e identidad visual.
- Icono propio para aplicación e instalador.
- Ventana Acerca de.
- Rediseño de la zona para seleccionar o arrastrar archivos.
- Nuevos iconos y ajustes generales de interfaz.

---

## v1.1.0 — Herramientas PDF

**Estado:** Aplicada

Primera gran expansión del proyecto más allá del convertidor principal.

### Incluido

- Unir PDFs.
- Dividir PDF.
- Extraer páginas.
- Reordenar páginas.
- Comprimir PDF.
- Herramientas visuales con miniaturas y arrastrar y soltar.
- Mejoras de navegación y presentación.

### Evolución de PDF → DOCX

La familia v1.1 incorpora y evoluciona la conversión PDF → DOCX; el motor propio
queda consolidado en v1.1.1.

---

## v1.1.1 — Herramientas de imágenes

**Estado:** Aplicada

Versión vigente.

### PDF

- Motor propio de conversión PDF → DOCX.
- Eliminación de la dependencia de Aspose.PDF.
- Mejoras en análisis de texto, imágenes, fondos, tablas y estructura.

### Imágenes

- Redimensionar imágenes.
- Comprimir imágenes.
- Imágenes → PDF.
- Mejorar calidad mediante Real-ESRGAN local y mejora clásica.
- Quitar fondo mediante modelos locales.
- Procesamiento por lotes en herramientas compatibles.
- Funcionamiento local sin necesidad de subir imágenes a Internet.

### Instalación

- Nuevos motores y modelos incluidos.
- Actualización desde versiones anteriores.
- Windows 64-bit sin necesidad de instalar Python por separado.

---

## v1.1.2 — Soporte multimedia

**Estado:** En desarrollo

Incorporación de audio, video y GIF.

### Motor previsto

- FFmpeg.
- ffprobe.

### Convertidor principal

Conversión de archivo completo A → archivo completo B.

### Ejemplos previstos

- MP4 → MP3.
- MP4 → GIF.
- GIF → MP4.
- MP3 → WAV.
- WAV → MP3.
- MP4 → WebM.
- M4A → MP3.

### Herramientas multimedia

- Extraer fotogramas.
- Recortar video, audio o GIF.
- Unir multimedia.
- Comprimir multimedia.
- Cambiar velocidad.

---

## v1.1.3 — Herramientas de archivos comprimidos

**Estado:** Siguiente

Nueva sección para trabajar con archivos comprimidos.

### Objetivos

- Comprimir archivos y carpetas.
- ZIP.
- 7Z.
- RAR cuando WinRAR/RAR esté disponible.
- Elegir nivel de compresión.
- Extraer archivos.
- Explorar el contenido sin extraer todo.
- Validar integridad.
- Estudiar soporte para volúmenes divididos.

---

## v1.1.4 — Herramientas de Minecraft

**Estado:** Pendiente

Inicialmente centradas en Minecraft Bedrock.

### Objetivos

- Crear `.mcpack`.
- Crear `.mcaddon`.
- Crear `.mcworld`.
- Crear `.mctemplate`.
- Extraer paquetes.
- Visualizar estructura.
- Validar estructura ZIP y `manifest.json`.
- Leer UUID, versión, módulos y dependencias.
- Generar UUID nuevos.
- Actualizar versiones.
- Combinar Resource Pack + Behavior Pack.

---

## v1.1.5 — Actualizaciones e integración con Windows

**Estado:** Pendiente

### Actualizador integrado

- Consultar GitHub Releases.
- Detectar versiones nuevas.
- Mostrar novedades.
- Descargar instalador.
- Verificar descarga.
- Cerrar la aplicación y ejecutar el instalador.

### Integración con Windows

- Abrir con Convertidor de Archivos.
- Recibir rutas como argumentos.
- Menú contextual.
- Arrastrar archivos sobre el ejecutable o acceso directo.

---

## v1.2.0 — Conversión por lotes y cola de trabajo

**Estado:** Pendiente

Primera actualización grande después de la familia v1.1.x.

### Objetivos

- Añadir múltiples archivos.
- Elegir carpetas completas.
- Procesar subcarpetas.
- Mantener estructura de carpetas.
- Cola de trabajos.
- Pausar.
- Continuar.
- Cancelar.
- Reintentar.
- Progreso individual y global.
- Resumen de completados, fallidos y omitidos.
- Integración con selección múltiple desde Windows.

---

## v1.3.0 — Perfiles y configuración

**Estado:** Pendiente

### Perfiles

Guardar configuraciones reutilizables para distintos tipos de conversión.

### Configuración general

- Carpeta de salida predeterminada.
- Recordar última carpeta.
- Comportamiento ante archivos existentes.
- Preferencias de motores.
- Calidad predeterminada.
- Actualizador.
- Integración con Windows.

---

## v1.4.0 — Herramientas avanzadas de documentos

**Estado:** Pendiente

### Objetivos

- Extraer imágenes.
- Extraer archivos incrustados cuando sea posible.
- Mostrar metadatos.
- Rotar, eliminar y duplicar páginas PDF.
- Combinar varias operaciones antes de guardar.

### OCR — posible

Se evaluará únicamente si existe un motor offline adecuado por calidad,
tamaño, rendimiento y licencia.

---

## v1.5.0 — Multimedia avanzada

**Estado:** Pendiente

### Video

- Resolución.
- FPS.
- Bitrate.
- Rotación.
- Volteo.
- Relación de aspecto.
- Recorte físico.

### Audio de video

- Quitar audio.
- Reemplazar audio.
- Extraer pistas.
- Trabajar con múltiples pistas cuando sea viable.

### GIF y fotogramas

- Crear GIF desde fragmentos.
- Elegir FPS, resolución y calidad.
- Extraer fotogramas concretos.
- Crear portadas y miniaturas.

---

## v1.6.0 — Productividad y experiencia de usuario

**Estado:** Pendiente

### Objetivos

- Historial de conversiones.
- Repetir conversiones.
- Accesos rápidos.
- Favoritos.
- Mejoras de drag & drop.
- Diagnóstico de motores.
- Información de errores más clara.
- Registro opcional de operaciones.

---

## v2.0.0 — Gran actualización futura

**Estado:** Visión

Reservada para cambios de alcance mayor.

### Líneas posibles

- Arquitectura todavía más modular.
- Incorporación más sencilla de formatos y motores.
- Mejor separación entre interfaz, conversión y herramientas.
- Flujos de procesamiento encadenados.
- Flujos personalizados reutilizables.
- Ejecución sobre múltiples archivos.
- Posible rediseño de interfaz si el crecimiento del producto lo requiere.

---

## Regla de avance

Una versión puede cambiar de alcance, dividirse, adelantarse o retrasarse si el
desarrollo real lo requiere.
