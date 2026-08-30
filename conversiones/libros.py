import os
import tempfile

from funciones.formatos import (
    obtener_categoria_archivo,
    obtener_formato_archivo
)

from funciones.capacidades import (
    detectar_pandoc,
    detectar_microsoft_word,
    detectar_libreoffice
)

from conversiones.pandoc import (
    comprobar_conversion_pandoc,
    convertir_con_pandoc
)

from conversiones.microsoft_office import (
    convertir_con_word
)

from conversiones.libreoffice import (
    convertir_con_libreoffice
)


# ----------------------------------- #
#       Formatos de entrada           #
# ----------------------------------- #

FORMATOS_ENTRADA_LIBROS = {
    "EPUB",
    "FB2",
    "RST",
    "LATEX",
    "ASCIIDOC",
    "OPML",
    "ORG",
    "JUPYTER"
}


# ----------------------------------- #
#        Salidas directas             #
# ----------------------------------- #

FORMATOS_SALIDA_PANDOC = {
    "EPUB",
    "DOCX",
    "ODT",
    "HTML",
    "MD",
    "RST",
    "LATEX",
    "ASCIIDOC"
}


# ================================================================
# COMPROBAR CONVERSIÓN IMPLEMENTADA
# ================================================================
def conversion_libro_implementada(
    ruta_origen,
    formato_destino
):

    # Debe pertenecer a la categoría correcta
    if obtener_categoria_archivo(
        ruta_origen
    ) != "libro":

        return False

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()

    return (
        formato_origen in FORMATOS_ENTRADA_LIBROS
        and formato_origen != formato_destino
        and (
            formato_destino in FORMATOS_SALIDA_PANDOC
            or formato_destino == "PDF"
        )
    )


# ================================================================
# COMPROBAR PDF DISPONIBLE
# ================================================================
def comprobar_pdf_libro_disponible(
    ruta_origen
):

    # Pandoc debe poder crear el DOCX intermedio
    disponible, mensaje = comprobar_conversion_pandoc(
        ruta_origen,
        "DOCX"
    )

    if not disponible:
        return False, mensaje

    # Preferimos Microsoft Word
    if detectar_microsoft_word():
        return True, None

    # LibreOffice como respaldo
    if detectar_libreoffice():
        return True, None

    return (
        False,
        "Para convertir este archivo a PDF se necesita "
        "Pandoc y además Microsoft Word o LibreOffice."
    )


# ================================================================
# COMPROBAR CONVERSIÓN DISPONIBLE
# ================================================================
def comprobar_libro_disponible(
    ruta_origen,
    formato_destino
):

    # Comprobar implementación
    if not conversion_libro_implementada(
        ruta_origen,
        formato_destino
    ):

        return (
            False,
            f"La conversión a {formato_destino} todavía "
            f"no está implementada para este tipo de documento."
        )

    # Comprobar Pandoc
    if not detectar_pandoc():

        return (
            False,
            "Esta conversión necesita Pandoc, "
            "pero no se encontró disponible."
        )

    formato_destino = formato_destino.upper()

    # PDF utiliza DOCX como intermediario
    if formato_destino == "PDF":

        return comprobar_pdf_libro_disponible(
            ruta_origen
        )

    # Conversión directa
    return comprobar_conversion_pandoc(
        ruta_origen,
        formato_destino
    )


# ================================================================
# CONVERTIR LIBRO A PDF
# ================================================================
def convertir_libro_a_pdf(
    ruta_origen,
    ruta_destino
):

    # Crear entorno temporal
    with tempfile.TemporaryDirectory() as carpeta_temporal:

        ruta_docx = os.path.join(
            carpeta_temporal,
            "documento_intermedio.docx"
        )

        # Primero convertir a DOCX
        convertir_con_pandoc(
            ruta_origen,
            ruta_docx,
            "DOCX"
        )

        # Preferir Microsoft Word
        if detectar_microsoft_word():

            return convertir_con_word(
                ruta_docx,
                ruta_destino,
                "PDF"
            )

        # Utilizar LibreOffice como respaldo
        if detectar_libreoffice():

            return convertir_con_libreoffice(
                ruta_docx,
                ruta_destino,
                "PDF",
                "writer"
            )

    raise RuntimeError(
        "No existe un motor disponible para generar el PDF."
    )


# ================================================================
# CONVERTIR LIBRO
# ================================================================
def convertir_libro(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    # Comprobar disponibilidad
    disponible, mensaje = comprobar_libro_disponible(
        ruta_origen,
        formato_destino
    )

    if not disponible:
        raise RuntimeError(
            mensaje
        )

    formato_destino = formato_destino.upper()

    # PDF mediante documento intermedio
    if formato_destino == "PDF":

        return convertir_libro_a_pdf(
            ruta_origen,
            ruta_destino
        )

    # Resto directamente con Pandoc
    return convertir_con_pandoc(
        ruta_origen,
        ruta_destino,
        formato_destino
    )