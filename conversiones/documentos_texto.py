import os
import tempfile

from funciones.formatos import obtener_formato_archivo

from funciones.capacidades import (
    detectar_pywin32,
    detectar_microsoft_word,
    detectar_microsoft_word_instalado,
    detectar_libreoffice,
    detectar_pandoc
)

from conversiones.microsoft_office import convertir_con_word
from conversiones.libreoffice import convertir_con_libreoffice

from conversiones.pandoc import (
    comprobar_conversion_pandoc,
    convertir_con_pandoc
)


# ----------------------------------- #
#     Entradas de Microsoft Word      #
# ----------------------------------- #

FORMATOS_ENTRADA_WORD = {
    "DOC",
    "DOCX",
    "DOCM",
    "DOT",
    "DOTX",
    "DOTM",
    "ODT",
    "RTF",
    "TXT",
    "HTML"
}


# ----------------------------------- #
#      Entradas de LibreOffice        #
# ----------------------------------- #

FORMATOS_ENTRADA_LIBREOFFICE = {
    "DOC",
    "DOCX",
    "DOCM",
    "DOT",
    "DOTX",
    "DOTM",
    "ODT",
    "OTT",
    "FODT",
    "SXW",
    "STW",
    "RTF",
    "TXT",
    "HTML",
    "XHTML",
    "XML",
    "WPD"
}


# ----------------------------------- #
#        Entradas de Pandoc           #
# ----------------------------------- #

FORMATOS_ENTRADA_PANDOC = {
    "MD",
    "HTML",
    "XHTML"
}


# ----------------------------------- #
#      Salidas de Microsoft Word      #
# ----------------------------------- #

FORMATOS_SALIDA_WORD = {
    "DOCX",
    "DOC",
    "ODT",
    "RTF",
    "TXT",
    "HTML",
    "PDF"
}


# ----------------------------------- #
#       Salidas de LibreOffice        #
# ----------------------------------- #

FORMATOS_SALIDA_LIBREOFFICE = {
    "DOCX",
    "DOC",
    "ODT",
    "RTF",
    "TXT",
    "HTML",
    "PDF"
}


# ----------------------------------- #
#          Salidas de Pandoc          #
# ----------------------------------- #

FORMATOS_SALIDA_PANDOC = {
    "DOCX",
    "ODT",
    "RTF",
    "TXT",
    "HTML",
    "XHTML",
    "MD",
    "EPUB"
}


# ----------------------------------- #
#     Salidas Pandoc + Office         #
# ----------------------------------- #

FORMATOS_SALIDA_PANDOC_OFFICE = {
    "DOC",
    "PDF"
}


# ================================================================
# COMPROBAR CONVERSIÓN IMPLEMENTADA
# ================================================================
def conversion_documento_texto_implementada(
    ruta_origen,
    formato_destino
):

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()

    compatible_word = (
        formato_origen in FORMATOS_ENTRADA_WORD
        and formato_destino in FORMATOS_SALIDA_WORD
    )

    compatible_libreoffice = (
        formato_origen in FORMATOS_ENTRADA_LIBREOFFICE
        and formato_destino in FORMATOS_SALIDA_LIBREOFFICE
    )

    compatible_pandoc = (
        formato_origen in FORMATOS_ENTRADA_PANDOC
        and (
            formato_destino in FORMATOS_SALIDA_PANDOC
            or formato_destino in FORMATOS_SALIDA_PANDOC_OFFICE
        )
    )

    return (
        formato_origen != formato_destino
        and (
            compatible_word
            or compatible_libreoffice
            or compatible_pandoc
        )
    )


# ================================================================
# OBTENER MOTOR
# ================================================================
def obtener_motor_documento_texto(
    ruta_origen,
    formato_destino
):

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()


    # ----------------------------------- #
    #       Preferir Microsoft Word       #
    # ----------------------------------- #

    if (
        formato_origen in FORMATOS_ENTRADA_WORD
        and formato_destino in FORMATOS_SALIDA_WORD
        and detectar_microsoft_word()
    ):

        return "microsoft_word"


    # ----------------------------------- #
    #         Después LibreOffice         #
    # ----------------------------------- #

    if (
        formato_origen in FORMATOS_ENTRADA_LIBREOFFICE
        and formato_destino in FORMATOS_SALIDA_LIBREOFFICE
        and detectar_libreoffice()
    ):

        return "libreoffice"


    # ----------------------------------- #
    #        Pandoc directamente          #
    # ----------------------------------- #

    if (
        formato_origen in FORMATOS_ENTRADA_PANDOC
        and formato_destino in FORMATOS_SALIDA_PANDOC
        and detectar_pandoc()
    ):

        return "pandoc"


    # ----------------------------------- #
    #       Pandoc + motor Office         #
    # ----------------------------------- #

    if (
        formato_origen in FORMATOS_ENTRADA_PANDOC
        and formato_destino in FORMATOS_SALIDA_PANDOC_OFFICE
        and detectar_pandoc()
        and (
            detectar_microsoft_word()
            or detectar_libreoffice()
        )
    ):

        return "pandoc_office"


    return None


# ================================================================
# COMPROBAR PANDOC + OFFICE
# ================================================================
def comprobar_pandoc_office_disponible(
    ruta_origen
):

    # Pandoc debe crear primero un DOCX
    disponible, mensaje = comprobar_conversion_pandoc(
        ruta_origen,
        "DOCX"
    )

    if not disponible:
        return False, mensaje

    # Comprobar motor final
    if (
        detectar_microsoft_word()
        or detectar_libreoffice()
    ):
        return True, None

    return (
        False,
        "La conversión necesita Pandoc y además "
        "Microsoft Word o LibreOffice."
    )


# ================================================================
# COMPROBAR CONVERSIÓN DISPONIBLE
# ================================================================
def comprobar_documento_texto_disponible(
    ruta_origen,
    formato_destino
):

    # Comprobar implementación
    if not conversion_documento_texto_implementada(
        ruta_origen,
        formato_destino
    ):

        return (
            False,
            f"La conversión a {formato_destino} todavía "
            f"no está implementada para este documento."
        )

    # Obtener motor
    motor = obtener_motor_documento_texto(
        ruta_origen,
        formato_destino
    )

    # Pandoc directo
    if motor == "pandoc":

        return comprobar_conversion_pandoc(
            ruta_origen,
            formato_destino
        )

    # Pandoc + Office
    if motor == "pandoc_office":

        return comprobar_pandoc_office_disponible(
            ruta_origen
        )

    # Word o LibreOffice
    if motor:
        return True, None


    # ----------------------------------- #
    #       Comprobar pywin32             #
    # ----------------------------------- #

    if (
        detectar_microsoft_word_instalado()
        and not detectar_pywin32()
    ):

        return (
            False,
            "Microsoft Word está instalado, pero falta pywin32.\n\n"
            "Instálalo con:\n"
            "python -m pip install pywin32"
        )


    # ----------------------------------- #
    #         Comprobar Pandoc            #
    # ----------------------------------- #

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    if (
        formato_origen in FORMATOS_ENTRADA_PANDOC
        and not detectar_pandoc()
    ):

        return (
            False,
            "Esta conversión necesita Pandoc, "
            "pero no se encontró disponible."
        )


    return (
        False,
        "No se encontró un motor disponible "
        "para realizar esta conversión."
    )


# ================================================================
# CONVERTIR CON PANDOC Y OFFICE
# ================================================================
def convertir_pandoc_y_office(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    # Crear DOCX intermedio
    with tempfile.TemporaryDirectory() as carpeta_temporal:

        ruta_intermedia = os.path.join(
            carpeta_temporal,
            "documento_intermedio.docx"
        )

        # Pandoc crea DOCX
        convertir_con_pandoc(
            ruta_origen,
            ruta_intermedia,
            "DOCX"
        )

        # Preferir Microsoft Word
        if detectar_microsoft_word():

            return convertir_con_word(
                ruta_intermedia,
                ruta_destino,
                formato_destino
            )

        # LibreOffice como respaldo
        if detectar_libreoffice():

            return convertir_con_libreoffice(
                ruta_intermedia,
                ruta_destino,
                formato_destino,
                "writer"
            )

    raise RuntimeError(
        "No existe un motor disponible "
        "para terminar la conversión."
    )


# ================================================================
# CONVERTIR DOCUMENTO DE TEXTO
# ================================================================
def convertir_documento_texto(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    # Obtener motor
    motor = obtener_motor_documento_texto(
        ruta_origen,
        formato_destino
    )

    # Microsoft Word
    if motor == "microsoft_word":

        return convertir_con_word(
            ruta_origen,
            ruta_destino,
            formato_destino
        )

    # LibreOffice
    if motor == "libreoffice":

        return convertir_con_libreoffice(
            ruta_origen,
            ruta_destino,
            formato_destino,
            "writer"
        )

    # Pandoc directo
    if motor == "pandoc":

        return convertir_con_pandoc(
            ruta_origen,
            ruta_destino,
            formato_destino
        )

    # Pandoc + Word/LibreOffice
    if motor == "pandoc_office":

        return convertir_pandoc_y_office(
            ruta_origen,
            ruta_destino,
            formato_destino
        )

    raise RuntimeError(
        "No existe un motor disponible "
        "para realizar esta conversión."
    )