import os
import tempfile

from funciones.archivos import obtener_nombre_sin_extension

from funciones.formatos import (
    obtener_formato_archivo,
    obtener_tipo_operacion
)

from conversiones.imagenes import (
    convertir_imagen,
    conversion_imagen_implementada,
    comprobar_imagen_disponible
)

from conversiones.comprimidos import (
    convertir_contenedor_zip,
    convertir_comprimido,
    conversion_comprimido_implementada,
    comprobar_comprimido_disponible
)

from conversiones.jar import (
    convertir_jar,
    conversion_jar_implementada,
    comprobar_jar_disponible
)

from conversiones.documentos_texto import (
    convertir_documento_texto,
    conversion_documento_texto_implementada,
    comprobar_documento_texto_disponible
)

from conversiones.hojas_calculo import (
    convertir_hoja_calculo,
    conversion_hoja_calculo_implementada,
    comprobar_hoja_calculo_disponible
)

from conversiones.presentaciones import (
    convertir_presentacion,
    conversion_presentacion_implementada,
    comprobar_presentacion_disponible
)

from conversiones.libros import (
    convertir_libro,
    conversion_libro_implementada,
    comprobar_libro_disponible
)

from conversiones.pdf import (
    FORMATOS_IMAGEN_PDF,
    resultado_pdf_requiere_zip,
    convertir_pdf,
    conversion_pdf_implementada,
    comprobar_pdf_disponible
)


# ----------------------------------- #
#       Extensiones de salida         #
# ----------------------------------- #

EXTENSIONES_SALIDA = {
    # Imágenes
    "JPG": ".jpg",
    "PNG": ".png",
    "APNG": ".apng",
    "WEBP": ".webp",
    "AVIF": ".avif",
    "HEIC": ".heic",
    "HEIF": ".heif",
    "JXL": ".jxl",
    "GIF": ".gif",
    "BMP": ".bmp",
    "TIFF": ".tiff",
    "ICO": ".ico",
    "JP2": ".jp2",
    "J2K": ".j2k",
    "JXR": ".jxr",
    "QOI": ".qoi",
    "TGA": ".tga",
    "PCX": ".pcx",
    "PNM": ".pnm",
    "PBM": ".pbm",
    "PGM": ".pgm",
    "PPM": ".ppm",
    "PAM": ".pam",
    "HDR": ".hdr",
    "EXR": ".exr",
    "DPX": ".dpx",
    "DDS": ".dds",
    "PSD": ".psd",
    "SVG": ".svg",
    "EPS": ".eps",

    # Documentos
    "PDF": ".pdf",
    "DOC": ".doc",
    "DOCX": ".docx",
    "ODT": ".odt",
    "RTF": ".rtf",
    "TXT": ".txt",
    "HTML": ".html",
    "XHTML": ".xhtml",
    "MD": ".md",
    "EPUB": ".epub",

    # Hojas de cálculo
    "XLS": ".xls",
    "XLSX": ".xlsx",
    "XLSM": ".xlsm",
    "XLSB": ".xlsb",
    "ODS": ".ods",
    "FODS": ".fods",
    "CSV": ".csv",
    "TSV": ".tsv",
    "DBF": ".dbf",

    # Presentaciones
    "PPT": ".ppt",
    "PPTX": ".pptx",
    "PPTM": ".pptm",
    "PPSX": ".ppsx",
    "PPSM": ".ppsm",
    "ODP": ".odp",
    "FODP": ".fodp",

    # Libros
    "RST": ".rst",
    "LATEX": ".tex",
    "ASCIIDOC": ".adoc",

    # Comprimidos
    "ZIP": ".zip",
    "ZIPX": ".zipx",
    "7Z": ".7z",
    "RAR": ".rar",
    "TAR": ".tar",
    "TAR.GZ": ".tar.gz",
    "TAR.BZ2": ".tar.bz2",
    "TAR.XZ": ".tar.xz",
    "TAR.ZST": ".tar.zst",
    "GZ": ".gz",
    "BZ2": ".bz2",
    "XZ": ".xz",
    "ZST": ".zst",
    "LZMA": ".lzma",
    "LZ4": ".lz4",
    "LZIP": ".lz",
    "WIM": ".wim",
    "CAB": ".cab",
    "LZH": ".lzh",
    "CPIO": ".cpio",
    "AR": ".ar",
    "XAR": ".xar",
    "ISO": ".iso",

    # Contenedores especiales
    "JAR": ".jar",
    "MCPACK": ".mcpack",
    "MCADDON": ".mcaddon",
    "MCWORLD": ".mcworld",
    "MCTEMPLATE": ".mctemplate"
}


# ================================================================
# OBTENER EXTENSIÓN DE DESTINO
# ================================================================
def obtener_extension_destino(formato_destino):

    formato_destino = formato_destino.upper()

    extension = EXTENSIONES_SALIDA.get(
        formato_destino
    )

    if not extension:

        raise ValueError(
            f"No se conoce la extensión correspondiente "
            f"a {formato_destino}."
        )

    return extension


# ================================================================
# OBTENER EXTENSIÓN REAL DEL RESULTADO
# ================================================================
def obtener_extension_resultado(
    ruta_origen,
    formato_destino
):

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()

    # PDF multipágina convertido a imágenes
    # genera un ZIP
    if (
        formato_origen == "PDF"
        and formato_destino in FORMATOS_IMAGEN_PDF
        and resultado_pdf_requiere_zip(
            ruta_origen,
            formato_destino
        )
    ):
        return ".zip"

    # Resto de conversiones
    return obtener_extension_destino(
        formato_destino
    )


# ================================================================
# OBTENER NOMBRE SUGERIDO DEL RESULTADO
# ================================================================
def obtener_nombre_resultado_sugerido(
    ruta_origen,
    formato_destino
):

    nombre_base = obtener_nombre_sin_extension(
        ruta_origen
    )

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()

    extension = obtener_extension_resultado(
        ruta_origen,
        formato_destino
    )

    # PDF multipágina a imágenes
    if (
        formato_origen == "PDF"
        and formato_destino in FORMATOS_IMAGEN_PDF
        and extension == ".zip"
    ):

        return (
            f"{nombre_base}_"
            f"{formato_destino.lower()}"
            f".zip"
        )

    return (
        nombre_base
        + extension
    )


# ================================================================
# COMPROBAR CONVERSIÓN IMPLEMENTADA
# ================================================================
def conversion_implementada(
    ruta_origen,
    formato_destino
):

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()

    tipo_operacion = obtener_tipo_operacion(
        ruta_origen,
        formato_destino
    )


    # Imágenes
    if tipo_operacion == "conversion_imagen":

        return conversion_imagen_implementada(
            ruta_origen,
            formato_destino
        )


    # Minecraft
    formatos_minecraft = {
        "MCPACK",
        "MCADDON",
        "MCWORLD",
        "MCTEMPLATE"
    }

    if tipo_operacion == "cambio_extension":

        if (
            formato_origen == "ZIP"
            and formato_destino in formatos_minecraft
        ):
            return True

        if (
            formato_origen in formatos_minecraft
            and formato_destino == "ZIP"
        ):
            return True


    # JAR
    if tipo_operacion == "conversion_jar":

        return conversion_jar_implementada(
            ruta_origen,
            formato_destino
        )


    # Comprimidos
    if tipo_operacion == "conversion_comprimido":

        return conversion_comprimido_implementada(
            ruta_origen,
            formato_destino
        )


    # Documentos
    if tipo_operacion == "conversion_documento_texto":

        return conversion_documento_texto_implementada(
            ruta_origen,
            formato_destino
        )


    # Hojas de cálculo
    if tipo_operacion == "conversion_hoja_calculo":

        return conversion_hoja_calculo_implementada(
            ruta_origen,
            formato_destino
        )


    # Presentaciones
    if tipo_operacion == "conversion_presentacion":

        return conversion_presentacion_implementada(
            ruta_origen,
            formato_destino
        )


    # Libros
    if tipo_operacion == "conversion_libro":

        return conversion_libro_implementada(
            ruta_origen,
            formato_destino
        )


    # PDF
    if tipo_operacion == "conversion_pdf":

        return conversion_pdf_implementada(
            ruta_origen,
            formato_destino
        )


    return False


# ================================================================
# COMPROBAR CONVERSIÓN DISPONIBLE
# ================================================================
def comprobar_conversion_disponible(
    ruta_origen,
    formato_destino
):

    # Comprobar implementación
    if not conversion_implementada(
        ruta_origen,
        formato_destino
    ):

        return (
            False,
            f"La conversión a {formato_destino} está contemplada "
            f"por la aplicación, pero todavía no ha sido implementada."
        )


    tipo_operacion = obtener_tipo_operacion(
        ruta_origen,
        formato_destino
    )


    # Imagen
    if tipo_operacion == "conversion_imagen":

        return comprobar_imagen_disponible(
            ruta_origen,
            formato_destino
        )


    # JAR
    if tipo_operacion == "conversion_jar":

        return comprobar_jar_disponible(
            ruta_origen,
            formato_destino
        )


    # Comprimido
    if tipo_operacion == "conversion_comprimido":

        return comprobar_comprimido_disponible(
            ruta_origen,
            formato_destino
        )


    # Documento
    if tipo_operacion == "conversion_documento_texto":

        return comprobar_documento_texto_disponible(
            ruta_origen,
            formato_destino
        )


    # Hoja de cálculo
    if tipo_operacion == "conversion_hoja_calculo":

        return comprobar_hoja_calculo_disponible(
            ruta_origen,
            formato_destino
        )


    # Presentación
    if tipo_operacion == "conversion_presentacion":

        return comprobar_presentacion_disponible(
            ruta_origen,
            formato_destino
        )


    # Libro
    if tipo_operacion == "conversion_libro":

        return comprobar_libro_disponible(
            ruta_origen,
            formato_destino
        )


    # PDF
    if tipo_operacion == "conversion_pdf":

        return comprobar_pdf_disponible(
            ruta_origen,
            formato_destino
        )


    # ZIP / Minecraft
    return True, None


# ================================================================
# CREAR RUTA TEMPORAL
# ================================================================
def crear_ruta_temporal(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    carpeta_destino = os.path.dirname(
        ruta_destino
    )

    # Importante: puede ser diferente del formato
    # solicitado, por ejemplo PDF → JPG multipágina
    extension = obtener_extension_resultado(
        ruta_origen,
        formato_destino
    )

    descriptor, ruta_temporal = tempfile.mkstemp(
        prefix=".conversion_",
        suffix=extension,
        dir=carpeta_destino
    )

    os.close(
        descriptor
    )

    os.remove(
        ruta_temporal
    )

    return ruta_temporal


# ================================================================
# EJECUTAR TIPO DE CONVERSIÓN
# ================================================================
def ejecutar_conversion(
    ruta_origen,
    ruta_destino,
    formato_destino,
    tipo_operacion,
    callback_progreso=None
):

    # Imagen
    if tipo_operacion == "conversion_imagen":

        return convertir_imagen(
            ruta_origen,
            ruta_destino,
            formato_destino
        )


    # ZIP / Minecraft
    if tipo_operacion == "cambio_extension":

        return convertir_contenedor_zip(
            ruta_origen,
            ruta_destino
        )


    # JAR
    if tipo_operacion == "conversion_jar":

        return convertir_jar(
            ruta_origen,
            ruta_destino,
            formato_destino
        )


    # Comprimido
    if tipo_operacion == "conversion_comprimido":

        return convertir_comprimido(
            ruta_origen,
            ruta_destino,
            formato_destino
        )


    # Documento
    if tipo_operacion == "conversion_documento_texto":

        return convertir_documento_texto(
            ruta_origen,
            ruta_destino,
            formato_destino
        )


    # Hoja de cálculo
    if tipo_operacion == "conversion_hoja_calculo":

        return convertir_hoja_calculo(
            ruta_origen,
            ruta_destino,
            formato_destino
        )


    # Presentación
    if tipo_operacion == "conversion_presentacion":

        return convertir_presentacion(
            ruta_origen,
            ruta_destino,
            formato_destino
        )


    # Libro
    if tipo_operacion == "conversion_libro":

        return convertir_libro(
            ruta_origen,
            ruta_destino,
            formato_destino
        )


    # PDF
    if tipo_operacion == "conversion_pdf":

        return convertir_pdf(
            ruta_origen,
            ruta_destino,
            formato_destino,
            callback_progreso
        )


    raise NotImplementedError(
        f"El tipo de operación '{tipo_operacion}' "
        f"todavía no está implementado."
    )


# ================================================================
# CONVERTIR ARCHIVO
# ================================================================
def convertir_archivo(
    ruta_origen,
    ruta_destino,
    formato_destino,
    callback_progreso=None
):

    disponible, mensaje = comprobar_conversion_disponible(
        ruta_origen,
        formato_destino
    )

    if not disponible:

        raise RuntimeError(
            mensaje
        )


    tipo_operacion = obtener_tipo_operacion(
        ruta_origen,
        formato_destino
    )


    ruta_temporal = crear_ruta_temporal(
        ruta_origen,
        ruta_destino,
        formato_destino
    )


    try:

        ejecutar_conversion(
            ruta_origen,
            ruta_temporal,
            formato_destino,
            tipo_operacion,
            callback_progreso
        )


        if not os.path.isfile(
            ruta_temporal
        ):

            raise RuntimeError(
                "La conversión terminó sin generar un archivo."
            )


        if os.path.getsize(
            ruta_temporal
        ) == 0:

            raise RuntimeError(
                "La conversión generó un archivo vacío."
            )


        os.replace(
            ruta_temporal,
            ruta_destino
        )


    except Exception:

        if os.path.exists(
            ruta_temporal
        ):

            try:

                os.remove(
                    ruta_temporal
                )

            except OSError:

                pass

        raise


    return ruta_destino