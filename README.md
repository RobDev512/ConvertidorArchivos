# Convertidor de Archivos

Aplicación de escritorio para Windows que permite convertir archivos y trabajar con documentos e imágenes de forma local.

## Versión actual

**1.1.1**

## Características

- Conversión de imágenes
- Documentos de texto
- Hojas de cálculo
- Presentaciones
- PDF
- Libros y formatos de marcado
- Archivos comprimidos
- JAR
- Contenedores de Minecraft
- Previsualización de archivos
- Motores locales incluidos en el instalador

## Herramientas PDF

La sección PDF incluye:

- Unir PDFs
- Dividir PDF
- Extraer páginas
- Reordenar páginas
- Comprimir PDF

### PDF → DOCX

La versión 1.1.1 incorpora un motor propio para convertir PDF a DOCX.

El proceso puede utilizar información de texto, imágenes, fondos y estructura del documento sin depender de Aspose.PDF.

Cuando corresponde, la aplicación también puede utilizar Microsoft Word o motores de respaldo compatibles disponibles en el equipo.

## Herramientas de imágenes

La versión 1.1.1 completa la sección de herramientas de imágenes con cinco utilidades.

### Redimensionar

Permite cambiar el tamaño de una o varias imágenes mediante:

- Píxeles
- Porcentaje
- Centímetros y PPI
- Conservación opcional de proporciones
- Control para evitar ampliaciones accidentales

### Comprimir imágenes

Permite reducir el peso de imágenes con controles de calidad y previsualización.

### Imágenes → PDF

Permite crear documentos PDF a partir de varias imágenes.

Incluye:

- Configuración por página
- Tamaños de papel habituales
- Orientación y ajustes de página
- Reordenamiento de imágenes
- Salida a un único PDF

### Mejorar calidad

Permite aumentar la resolución de una imagen mediante:

- Real-ESRGAN local
- Mejora clásica conservadora
- Escalas 2×, 3× y 4×
- Modelos para fotografía e ilustración

La superresolución se ejecuta localmente y no necesita subir imágenes a Internet.

### Quitar fondo

Permite eliminar el fondo de una imagen y guardar el resultado como PNG con transparencia.

Incluye tres modelos locales:

- U²-NetP
- IS-Net General Use
- BiRefNet General

También permite ajustar suavizado de bordes y tratamiento de transparencia.

## Motores y tecnologías

La aplicación puede utilizar:

- Motor propio PDF → DOCX
- LibreOffice
- ImageMagick
- 7-Zip
- Pandoc
- PDFium
- pypdf
- pdfplumber
- pikepdf
- python-docx
- lxml
- OpenPyXL
- Pillow
- NumPy
- Real-ESRGAN NCNN/Vulkan
- rembg
- ONNX Runtime
- U²-NetP
- IS-Net
- BiRefNet
- Microsoft Office, cuando está disponible
- WinRAR, cuando está disponible

## Procesamiento local

Las conversiones y las herramientas de imágenes se realizan localmente en el equipo.

Los modelos de IA incluidos funcionan sin necesidad de subir imágenes a servicios externos y no requieren conexión a Internet durante su uso.

## Instalación

La aplicación está disponible para **Windows de 64 bits**.

[Descargar Convertidor de Archivos 1.1.1](https://github.com/RobDev512/ConvertidorArchivos/releases/download/v1.1.1/ConvertidorArchivos_Setup_1.1.1.exe)

Ejecuta el instalador y sigue los pasos indicados.

El instalador muestra el tamaño del paquete y el espacio requerido antes de comenzar la instalación.

No es necesario instalar Python ni los motores incluidos por separado.

## Licencias de terceros

La aplicación utiliza bibliotecas, motores y modelos de terceros sujetos a sus propias licencias.

Los avisos correspondientes se incluyen en la carpeta `licencias_terceros` de la instalación.