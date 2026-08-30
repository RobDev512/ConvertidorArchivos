from funciones.formatos import obtener_formato_archivo

from funciones.capacidades import (
    detectar_pywin32,
    detectar_microsoft_powerpoint,
    detectar_microsoft_powerpoint_instalado,
    detectar_libreoffice
)

from conversiones.microsoft_office import convertir_con_powerpoint
from conversiones.libreoffice import convertir_con_libreoffice


# ----------------------------------- #
#   Entradas de Microsoft PowerPoint  #
# ----------------------------------- #

FORMATOS_ENTRADA_POWERPOINT = {
    "PPT",
    "PPTX",
    "PPTM",
    "PPS",
    "PPSX",
    "PPSM",
    "POT",
    "POTX",
    "POTM",
    "ODP"
}


# ----------------------------------- #
#      Entradas de LibreOffice        #
# ----------------------------------- #

FORMATOS_ENTRADA_LIBREOFFICE = {
    "PPT",
    "PPTX",
    "PPTM",
    "PPS",
    "PPSX",
    "PPSM",
    "POT",
    "POTX",
    "POTM",
    "ODP",
    "OTP",
    "FODP",
    "SXI",
    "STI"
}


# ----------------------------------- #
#  Salidas de Microsoft PowerPoint    #
# ----------------------------------- #

FORMATOS_SALIDA_POWERPOINT = {
    "PPTX",
    "PPT",
    "ODP",
    "PDF"
}


# ----------------------------------- #
#       Salidas de LibreOffice        #
# ----------------------------------- #

FORMATOS_SALIDA_LIBREOFFICE = {
    "PPTX",
    "PPT",
    "ODP",
    "FODP",
    "PDF"
}


# ================================================================
# COMPROBAR CONVERSIÓN IMPLEMENTADA
# ================================================================
def conversion_presentacion_implementada(
    ruta_origen,
    formato_destino
):

    formato_origen = obtener_formato_archivo(ruta_origen)
    formato_destino = formato_destino.upper()

    compatible_powerpoint = (
        formato_origen in FORMATOS_ENTRADA_POWERPOINT
        and formato_destino in FORMATOS_SALIDA_POWERPOINT
    )

    compatible_libreoffice = (
        formato_origen in FORMATOS_ENTRADA_LIBREOFFICE
        and formato_destino in FORMATOS_SALIDA_LIBREOFFICE
    )

    return (
        formato_origen != formato_destino
        and (
            compatible_powerpoint
            or compatible_libreoffice
        )
    )


# ================================================================
# OBTENER MOTOR
# ================================================================
def obtener_motor_presentacion(
    ruta_origen,
    formato_destino
):

    formato_origen = obtener_formato_archivo(ruta_origen)
    formato_destino = formato_destino.upper()

    # Preferir Microsoft PowerPoint
    if (
        formato_origen in FORMATOS_ENTRADA_POWERPOINT
        and formato_destino in FORMATOS_SALIDA_POWERPOINT
        and detectar_microsoft_powerpoint()
    ):
        return "microsoft_powerpoint"

    # LibreOffice Impress como respaldo
    if (
        formato_origen in FORMATOS_ENTRADA_LIBREOFFICE
        and formato_destino in FORMATOS_SALIDA_LIBREOFFICE
        and detectar_libreoffice()
    ):
        return "libreoffice"

    return None


# ================================================================
# COMPROBAR CONVERSIÓN DISPONIBLE
# ================================================================
def comprobar_presentacion_disponible(
    ruta_origen,
    formato_destino
):

    # Comprobar implementación
    if not conversion_presentacion_implementada(
        ruta_origen,
        formato_destino
    ):
        return (
            False,
            f"La conversión a {formato_destino} todavía "
            f"no está implementada para esta presentación."
        )

    # Comprobar motor
    if obtener_motor_presentacion(
        ruta_origen,
        formato_destino
    ):
        return True, None

    # PowerPoint existe pero falta pywin32
    if (
        detectar_microsoft_powerpoint_instalado()
        and not detectar_pywin32()
    ):
        return (
            False,
            "Microsoft PowerPoint está instalado, pero falta pywin32.\n\n"
            "Instálalo con:\n"
            "python -m pip install pywin32"
        )

    return (
        False,
        "No se encontró un motor disponible para esta conversión.\n\n"
        "Se necesita Microsoft PowerPoint o LibreOffice."
    )


# ================================================================
# CONVERTIR PRESENTACIÓN
# ================================================================
def convertir_presentacion(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    # Obtener motor
    motor = obtener_motor_presentacion(
        ruta_origen,
        formato_destino
    )

    # Microsoft PowerPoint
    if motor == "microsoft_powerpoint":
        return convertir_con_powerpoint(
            ruta_origen,
            ruta_destino,
            formato_destino
        )

    # LibreOffice Impress
    if motor == "libreoffice":
        return convertir_con_libreoffice(
            ruta_origen,
            ruta_destino,
            formato_destino,
            "impress"
        )

    raise RuntimeError(
        "No existe un motor disponible para realizar esta conversión."
    )