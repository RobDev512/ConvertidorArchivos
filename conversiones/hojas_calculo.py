from funciones.formatos import obtener_formato_archivo

from funciones.capacidades import (
    detectar_pywin32,
    detectar_microsoft_excel,
    detectar_microsoft_excel_instalado,
    detectar_libreoffice
)

from conversiones.microsoft_office import convertir_con_excel
from conversiones.libreoffice import convertir_con_libreoffice


# ----------------------------------- #
#      Entradas de Microsoft Excel    #
# ----------------------------------- #

FORMATOS_ENTRADA_EXCEL = {
    "XLS",
    "XLSX",
    "XLSM",
    "XLSB",
    "XLT",
    "XLTX",
    "XLTM",
    "ODS",
    "CSV",
    "TSV",
    "DIF",
    "SLK",
    "DBF"
}


# ----------------------------------- #
#      Entradas de LibreOffice        #
# ----------------------------------- #

FORMATOS_ENTRADA_LIBREOFFICE = {
    "XLS",
    "XLSX",
    "XLSM",
    "XLSB",
    "XLT",
    "XLTX",
    "XLTM",
    "ODS",
    "OTS",
    "FODS",
    "CSV",
    "TSV",
    "DIF",
    "SLK",
    "DBF"
}


# ----------------------------------- #
#      Salidas de Microsoft Excel     #
# ----------------------------------- #

FORMATOS_SALIDA_EXCEL = {
    "XLSX",
    "XLS",
    "ODS",
    "HTML",
    "PDF"
}


# ----------------------------------- #
#       Salidas de LibreOffice        #
# ----------------------------------- #

FORMATOS_SALIDA_LIBREOFFICE = {
    "XLSX",
    "XLS",
    "ODS",
    "FODS",
    "HTML",
    "PDF"
}


# ================================================================
# COMPROBAR CONVERSIÓN IMPLEMENTADA
# ================================================================
def conversion_hoja_calculo_implementada(
    ruta_origen,
    formato_destino
):

    formato_origen = obtener_formato_archivo(ruta_origen)
    formato_destino = formato_destino.upper()

    compatible_excel = (
        formato_origen in FORMATOS_ENTRADA_EXCEL
        and formato_destino in FORMATOS_SALIDA_EXCEL
    )

    compatible_libreoffice = (
        formato_origen in FORMATOS_ENTRADA_LIBREOFFICE
        and formato_destino in FORMATOS_SALIDA_LIBREOFFICE
    )

    return (
        formato_origen != formato_destino
        and (
            compatible_excel
            or compatible_libreoffice
        )
    )


# ================================================================
# OBTENER MOTOR
# ================================================================
def obtener_motor_hoja_calculo(
    ruta_origen,
    formato_destino
):

    formato_origen = obtener_formato_archivo(ruta_origen)
    formato_destino = formato_destino.upper()

    # Preferir Microsoft Excel
    if (
        formato_origen in FORMATOS_ENTRADA_EXCEL
        and formato_destino in FORMATOS_SALIDA_EXCEL
        and detectar_microsoft_excel()
    ):
        return "microsoft_excel"

    # LibreOffice Calc como respaldo
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
def comprobar_hoja_calculo_disponible(
    ruta_origen,
    formato_destino
):

    # Comprobar implementación
    if not conversion_hoja_calculo_implementada(
        ruta_origen,
        formato_destino
    ):
        return (
            False,
            f"La conversión a {formato_destino} todavía "
            f"no está implementada para esta hoja de cálculo."
        )

    # Comprobar motor
    if obtener_motor_hoja_calculo(
        ruta_origen,
        formato_destino
    ):
        return True, None

    # Excel existe pero falta pywin32
    if (
        detectar_microsoft_excel_instalado()
        and not detectar_pywin32()
    ):
        return (
            False,
            "Microsoft Excel está instalado, pero falta pywin32.\n\n"
            "Instálalo con:\n"
            "python -m pip install pywin32"
        )

    return (
        False,
        "No se encontró un motor disponible para esta conversión.\n\n"
        "Se necesita Microsoft Excel o LibreOffice."
    )


# ================================================================
# CONVERTIR HOJA DE CÁLCULO
# ================================================================
def convertir_hoja_calculo(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    # Obtener motor
    motor = obtener_motor_hoja_calculo(
        ruta_origen,
        formato_destino
    )

    # Microsoft Excel
    if motor == "microsoft_excel":
        return convertir_con_excel(
            ruta_origen,
            ruta_destino,
            formato_destino
        )

    # LibreOffice Calc
    if motor == "libreoffice":
        return convertir_con_libreoffice(
            ruta_origen,
            ruta_destino,
            formato_destino,
            "calc"
        )

    raise RuntimeError(
        "No existe un motor disponible para realizar esta conversión."
    )