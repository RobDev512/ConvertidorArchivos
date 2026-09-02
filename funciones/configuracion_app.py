import os
import sys


# ================================================================
# INFORMACIÓN DE LA APLICACIÓN
# ================================================================

NOMBRE_APLICACION = "Convertidor de Archivos"

NOMBRE_EJECUTABLE = "ConvertidorArchivos"

VERSION_APLICACION = "1.1.0"

ORGANIZACION_APLICACION = "Robert"

ID_APLICACION_WINDOWS = (
    "Robert.ConvertidorDeArchivos.1"
)


# ================================================================
# OBTENER CARPETA DE LA APLICACIÓN
# ================================================================
def obtener_carpeta_aplicacion():

    # ----------------------------------- #
    #       Aplicación empaquetada        #
    # ----------------------------------- #

    if getattr(
        sys,
        "frozen",
        False
    ):

        return os.path.dirname(
            sys.executable
        )


    # ----------------------------------- #
    #        Proyecto en desarrollo       #
    # ----------------------------------- #

    return os.path.dirname(
        os.path.dirname(
            os.path.abspath(
                __file__
            )
        )
    )


# ================================================================
# OBTENER CARPETA DE RECURSOS
# ================================================================
def obtener_carpeta_recursos():

    # ----------------------------------- #
    #       Aplicación empaquetada        #
    # ----------------------------------- #

    if getattr(
        sys,
        "frozen",
        False
    ):

        carpeta_interna = getattr(
            sys,
            "_MEIPASS",
            None
        )

        if carpeta_interna:

            return os.path.join(
                carpeta_interna,
                "recursos"
            )


    # ----------------------------------- #
    #        Proyecto en desarrollo       #
    # ----------------------------------- #

    return os.path.join(
        obtener_carpeta_aplicacion(),
        "recursos"
    )


# ================================================================
# OBTENER RUTA DE RECURSO
# ================================================================
def obtener_ruta_recurso(
    *partes
):

    return os.path.join(
        obtener_carpeta_recursos(),
        *partes
    )


# ================================================================
# OBTENER ICONO PRINCIPAL
# ================================================================
def obtener_ruta_icono_principal():

    return obtener_ruta_recurso(
        "iconos",
        "FileConverter.png"
    )


# ================================================================
# OBTENER ICONO WINDOWS
# ================================================================
def obtener_ruta_icono_windows():

    return obtener_ruta_recurso(
        "iconos",
        "FileConverter.ico"
    )


# ================================================================
# OBTENER CARPETA DE LICENCIAS
# ================================================================
def obtener_carpeta_licencias():

    return os.path.join(
        obtener_carpeta_aplicacion(),
        "licencias_terceros"
    )