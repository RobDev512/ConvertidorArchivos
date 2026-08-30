from funciones.archivos import obtener_extension_archivo


# ----------------------------------- #
#          Formatos de imagen         #
# ----------------------------------- #
FORMATOS_IMAGEN = {
    ".jpg": "JPG", ".jpeg": "JPG",
    ".jpe": "JPG", ".jfif": "JPG",
    ".jif": "JPG",

    ".png": "PNG", ".apng": "APNG",

    ".webp": "WEBP",

    ".avif": "AVIF",

    ".heic": "HEIC", ".heif": "HEIF",

    ".jxl": "JXL",

    ".gif": "GIF",

    ".bmp": "BMP", ".dib": "BMP",

    ".tif": "TIFF", ".tiff": "TIFF",

    ".ico": "ICO", ".cur": "CUR",

    ".jp2": "JP2", ".jpf": "JP2",
    ".jpx": "JP2", ".jpm": "JP2",

    ".j2k": "J2K", ".j2c": "J2K",
    ".jpc": "J2K",

    ".jxr": "JXR", ".wdp": "JXR",
    ".hdp": "JXR",

    ".qoi": "QOI",

    ".tga": "TGA", ".icb": "TGA",
    ".vda": "TGA", ".vst": "TGA",

    ".pcx": "PCX", ".dcx": "DCX",

    ".pnm": "PNM", ".pbm": "PBM",
    ".pgm": "PGM", ".ppm": "PPM",
    ".pam": "PAM", ".pfm": "PFM",

    ".hdr": "HDR", ".exr": "EXR",

    ".dpx": "DPX", ".cin": "CIN",

    ".dds": "DDS",

    ".psd": "PSD", ".psb": "PSB",

    ".miff": "MIFF", ".mng": "MNG",
    ".bpg": "BPG",

    ".wbmp": "WBMP",

    ".xbm": "XBM", ".xpm": "XPM",
    ".xwd": "XWD",

    ".pict": "PICT", ".pct": "PICT",

    ".svg": "SVG", ".svgz": "SVG",

    ".eps": "EPS", ".epsf": "EPS",
    ".epsi": "EPS"
}


# ----------------------------------- #
#          Formatos RAW               #
# ----------------------------------- #
FORMATOS_RAW = {
    ".3fr": "RAW", ".arw": "RAW",
    ".cr2": "RAW", ".cr3": "RAW",
    ".crw": "RAW", ".dcr": "RAW",
    ".dng": "RAW", ".erf": "RAW",
    ".iiq": "RAW", ".k25": "RAW",
    ".kdc": "RAW", ".mef": "RAW",
    ".mos": "RAW", ".mrw": "RAW",
    ".nef": "RAW", ".nrw": "RAW",
    ".orf": "RAW", ".pef": "RAW",
    ".raf": "RAW", ".raw": "RAW",
    ".rwl": "RAW", ".rw2": "RAW",
    ".sr2": "RAW", ".srf": "RAW",
    ".x3f": "RAW"
}

# ----------------------------------- #
#        Documentos de texto          #
# ----------------------------------- #
FORMATOS_DOCUMENTOS_TEXTO = {
    ".doc": "DOC", ".docx": "DOCX",
    ".docm": "DOCM",

    ".dot": "DOT", ".dotx": "DOTX",
    ".dotm": "DOTM",

    ".odt": "ODT", ".ott": "OTT",
    ".fodt": "FODT",

    ".sxw": "SXW", ".stw": "STW",

    ".rtf": "RTF",

    ".txt": "TXT",

    ".html": "HTML", ".htm": "HTML",

    ".xhtml": "XHTML",

    ".xml": "XML",

    ".md": "MD", ".markdown": "MD",

    ".wpd": "WPD", ".wps": "WPS",
    ".wri": "WRI",

    ".abw": "ABW", ".zabw": "ZABW",

    ".hwp": "HWP", ".lwp": "LWP",

    ".pages": "PAGES"
}

# ----------------------------------- #
#          Hojas de cálculo           #
# ----------------------------------- #
FORMATOS_HOJAS_CALCULO = {
    ".xls": "XLS", ".xlsx": "XLSX",
    ".xlsm": "XLSM", ".xlsb": "XLSB",

    ".xlt": "XLT", ".xltx": "XLTX",
    ".xltm": "XLTM",

    ".ods": "ODS", ".ots": "OTS",
    ".fods": "FODS",

    ".csv": "CSV", ".tsv": "TSV",

    ".dif": "DIF",

    ".slk": "SLK", ".sylk": "SLK",

    ".dbf": "DBF",

    ".gnumeric": "GNUMERIC", ".gnm": "GNUMERIC",

    ".wk1": "WK1", ".wk3": "WK3",
    ".wk4": "WK4", ".wks": "WKS",

    ".123": "123",

    ".wb1": "WB1", ".wb2": "WB2",

    ".wq1": "WQ1", ".wq2": "WQ2",

    ".numbers": "NUMBERS",

    ".parquet": "PARQUET"
}

# ----------------------------------- #
#            Presentaciones           #
# ----------------------------------- #
FORMATOS_PRESENTACIONES = {
    ".ppt": "PPT", ".pptx": "PPTX",
    ".pptm": "PPTM",

    ".pps": "PPS", ".ppsx": "PPSX",
    ".ppsm": "PPSM",

    ".pot": "POT", ".potx": "POTX",
    ".potm": "POTM",

    ".odp": "ODP", ".otp": "OTP",
    ".fodp": "FODP",

    ".key": "KEY",

    ".sxi": "SXI", ".sti": "STI"
}

# ----------------------------------- #
#        Libros y documentos          #
# ----------------------------------- #
FORMATOS_LIBROS = {
    ".epub": "EPUB", ".fb2": "FB2",

    ".rst": "RST",

    ".tex": "LATEX", ".latex": "LATEX",

    ".adoc": "ASCIIDOC", ".asciidoc": "ASCIIDOC",

    ".opml": "OPML",

    ".org": "ORG",

    ".ipynb": "JUPYTER"
}

# ----------------------------------- #
#                  PDF                #
# ----------------------------------- #
FORMATOS_PDF = {
    ".pdf": "PDF"
}

# ----------------------------------- #
#         Archivos comprimidos        #
# ----------------------------------- #
FORMATOS_COMPRIMIDOS = {
    ".zip": "ZIP", ".zipx": "ZIPX",

    ".jar": "JAR",

    ".7z": "7Z",

    ".rar": "RAR",

    ".tar": "TAR",

    ".tar.gz": "TAR.GZ", ".tgz": "TAR.GZ",

    ".tar.bz2": "TAR.BZ2", ".tbz": "TAR.BZ2",
    ".tbz2": "TAR.BZ2",

    ".tar.xz": "TAR.XZ", ".txz": "TAR.XZ",

    ".tar.zst": "TAR.ZST",

    ".gz": "GZ", ".gzip": "GZ",

    ".bz2": "BZ2", ".bzip2": "BZ2",

    ".xz": "XZ",

    ".zst": "ZST", ".zstd": "ZST",

    ".lzma": "LZMA",

    ".lz4": "LZ4",

    ".lz": "LZIP", ".lzip": "LZIP",

    ".lzo": "LZO",

    ".z": "Z",

    ".wim": "WIM",

    ".cab": "CAB",

    ".lha": "LHA", ".lzh": "LZH",

    ".cpio": "CPIO",

    ".ar": "AR",

    ".xar": "XAR",

    ".iso": "ISO",

    ".mcpack": "MCPACK", ".mcaddon": "MCADDON",
    ".mcworld": "MCWORLD", ".mctemplate": "MCTEMPLATE"
}

# ----------------------------------- #
#      Salidas para cada familia      #
# ----------------------------------- #
SALIDAS_IMAGEN = [
    "JPG", "PNG", "APNG", "WEBP", "AVIF", "HEIC",
    "HEIF", "JXL", "GIF", "BMP", "TIFF", "ICO",
    "JP2", "J2K", "JXR", "QOI", "TGA", "PCX",
    "PNM", "PBM", "PGM", "PPM", "PAM", "HDR",
    "EXR", "DPX", "DDS", "PSD", "SVG", "EPS", "PDF"
]

SALIDAS_DOCUMENTOS_TEXTO = [
    "DOCX", "DOC", "ODT", "RTF",
    "TXT", "HTML", "XHTML", "MD",
    "EPUB", "PDF"
]

SALIDAS_HOJAS_CALCULO = [
    "XLSX", "XLS", "ODS", "FODS", "CSV",
    "TSV", "DBF", "HTML", "PDF"
]

SALIDAS_PRESENTACIONES = [
    "PPTX", "PPT", "PPSX", "ODP", "FODP", "PDF"
]

SALIDAS_LIBROS = [
    "EPUB", "DOCX", "ODT", "HTML", "MD",
    "RST", "LATEX", "ASCIIDOC",
    "PDF"
]

SALIDAS_PDF = [
    "DOCX", "ODT", "RTF", "TXT", "HTML",
    "JPG", "PNG", "TIFF"
]

SALIDAS_COMPRIMIDOS = [
    "ZIP", "ZIPX", "7Z", "RAR", "TAR", "TAR.GZ", "TAR.BZ2",
    "TAR.XZ", "TAR.ZST", "GZ", "BZ2", "XZ", "ZST", "LZMA",
    "LZ4", "LZIP", "WIM", "CAB", "LZH", "CPIO", "AR", "XAR",
    "ISO", "JAR", "MCPACK", "MCADDON", "MCWORLD", "MCTEMPLATE"
]

# ----------------------------------- #
#        Categorías visibles          #
# ----------------------------------- #
NOMBRES_CATEGORIAS = {
    "imagen": "Imagen",
    "documento_texto": "Documento de texto",
    "hoja_calculo": "Hoja de cálculo",
    "presentacion": "Presentación",
    "libro": "Libro o documento estructurado",
    "pdf": "Documento PDF",
    "comprimido": "Archivo comprimido",
    "desconocido": "Formato desconocido"
}

# ----------------------------------- #
#      Contenedores ZIP especiales    #
# ----------------------------------- #
FORMATOS_MINECRAFT = {
    "MCPACK",
    "MCADDON",
    "MCWORLD",
    "MCTEMPLATE"
}

# ================================================================
# OBTENER CATEGORÍA DEL ARCHIVO
# ================================================================
def obtener_categoria_archivo(ruta_archivo):
    extension = obtener_extension_archivo(ruta_archivo)

    if extension in FORMATOS_IMAGEN or extension in FORMATOS_RAW:
        return "imagen"

    if extension in FORMATOS_DOCUMENTOS_TEXTO:
        return "documento_texto"

    if extension in FORMATOS_HOJAS_CALCULO:
        return "hoja_calculo"

    if extension in FORMATOS_PRESENTACIONES:
        return "presentacion"

    if extension in FORMATOS_LIBROS:
        return "libro"

    if extension in FORMATOS_PDF:
        return "pdf"

    if extension in FORMATOS_COMPRIMIDOS:
        return "comprimido"

    return "desconocido"

# ================================================================
# OBTENER NOMBRE DE LA CATEGORÍA
# ================================================================
def obtener_nombre_categoria(ruta_archivo):
    categoria = obtener_categoria_archivo(ruta_archivo)

    return NOMBRES_CATEGORIAS.get(
        categoria,
        "Formato desconocido"
    )


# ================================================================
# OBTENER FORMATO DEL ARCHIVO
# ================================================================
def obtener_formato_archivo(ruta_archivo):
    extension = obtener_extension_archivo(ruta_archivo)

    catalogos = [
        FORMATOS_IMAGEN,
        FORMATOS_RAW,
        FORMATOS_DOCUMENTOS_TEXTO,
        FORMATOS_HOJAS_CALCULO,
        FORMATOS_PRESENTACIONES,
        FORMATOS_LIBROS,
        FORMATOS_PDF,
        FORMATOS_COMPRIMIDOS
    ]

    # Buscar la extensión en todos los catálogos
    for catalogo in catalogos:
        if extension in catalogo:
            return catalogo[extension]

    return "DESCONOCIDO"


# ================================================================
# OBTENER FORMATOS DISPONIBLES
# ================================================================
def obtener_formatos_archivo(ruta_archivo):
    categoria = obtener_categoria_archivo(ruta_archivo)
    formato_actual = obtener_formato_archivo(ruta_archivo)

    # Seleccionar salidas correspondientes a la categoría
    if categoria == "imagen":
        formatos = SALIDAS_IMAGEN.copy()

    elif categoria == "documento_texto":
        formatos = SALIDAS_DOCUMENTOS_TEXTO.copy()

    elif categoria == "hoja_calculo":
        formatos = SALIDAS_HOJAS_CALCULO.copy()

    elif categoria == "presentacion":
        formatos = SALIDAS_PRESENTACIONES.copy()

    elif categoria == "libro":
        formatos = SALIDAS_LIBROS.copy()

    elif categoria == "pdf":
        formatos = SALIDAS_PDF.copy()

    elif categoria == "comprimido":
        formatos = SALIDAS_COMPRIMIDOS.copy()

    else:
        return []

    # Evitar ofrecer el mismo formato de entrada
    if formato_actual in formatos:
        formatos.remove(formato_actual)

    return formatos


# ================================================================
# OBTENER FORMATOS COMPATIBLES
# ================================================================
def obtener_formatos_compatibles(archivos):
    # Sin archivos no existen conversiones
    if not archivos:
        return []

    # Tomar inicialmente las opciones del primer archivo
    formatos_compatibles = obtener_formatos_archivo(
        archivos[0]
    ).copy()

    # Conservar únicamente salidas comunes entre todos
    for archivo in archivos[1:]:

        formatos_archivo = obtener_formatos_archivo(archivo)

        formatos_compatibles = [
            formato
            for formato in formatos_compatibles
            if formato in formatos_archivo
        ]

    return formatos_compatibles


# ================================================================
# OBTENER TIPO DE OPERACIÓN
# ================================================================
def obtener_tipo_operacion(ruta_archivo, formato_destino):
    categoria = obtener_categoria_archivo(ruta_archivo)
    formato_origen = obtener_formato_archivo(ruta_archivo)
    formato_destino = formato_destino.upper()

    # ZIP y formatos de Minecraft pueden conservar
    # exactamente el mismo contenido interno
    if formato_origen == "ZIP" and formato_destino in FORMATOS_MINECRAFT:
        return "cambio_extension"

    if formato_origen in FORMATOS_MINECRAFT and formato_destino == "ZIP":
        return "cambio_extension"

    # JAR se manejará por separado
    if {formato_origen, formato_destino} == {"JAR", "ZIP"}:
        return "conversion_jar"

    # Conversiones normales por familia
    if categoria == "imagen":
        return "conversion_imagen"

    if categoria == "documento_texto":
        return "conversion_documento_texto"

    if categoria == "hoja_calculo":
        return "conversion_hoja_calculo"

    if categoria == "presentacion":
        return "conversion_presentacion"

    if categoria == "libro":
        return "conversion_libro"

    if categoria == "pdf":
        return "conversion_pdf"

    if categoria == "comprimido":
        return "conversion_comprimido"

    return "desconocido"