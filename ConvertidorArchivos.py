import ctypes
import os
import sys

from PySide6.QtGui import QIcon

from PySide6.QtWidgets import QApplication

from funciones.configuracion_app import (
    ID_APLICACION_WINDOWS,
    NOMBRE_APLICACION,
    ORGANIZACION_APLICACION,
    VERSION_APLICACION,
    obtener_ruta_icono_principal
)

from interfaz.barra_superior import (
    BarraSuperiorPrincipal
)

from interfaz.dialogo_acerca_de import (
    DialogoAcercaDe
)

from interfaz.ventana_principal import (
    VentanaPrincipal
)

from interfaz.herramientas.ventana_herramientas import (
    VentanaHerramientas
)


# ================================================================
# CONFIGURAR IDENTIDAD EN WINDOWS
# ================================================================
def configurar_identidad_windows():

    if os.name != "nt":

        return


    try:

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            ID_APLICACION_WINDOWS
        )

    except Exception:

        pass


# ================================================================
# CONFIGURAR BARRA SUPERIOR
# ================================================================
def configurar_barra_superior(
    ventana
):

    barra_superior = BarraSuperiorPrincipal(
        ventana
    )

    ventana.barra_superior = barra_superior

    ventana.setMenuWidget(
        barra_superior
    )


    # ----------------------------------- #
    #             Unir PDFs               #
    # ----------------------------------- #

    barra_superior.unir_pdfs_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "unir_pdf"
        )
    )


    # ----------------------------------- #
    #           Dividir PDF               #
    # ----------------------------------- #

    barra_superior.dividir_pdf_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "dividir_pdf"
        )
    )


    # ----------------------------------- #
    #         Extraer páginas             #
    # ----------------------------------- #

    barra_superior.extraer_paginas_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "extraer_paginas"
        )
    )


    # ----------------------------------- #
    #        Reordenar páginas            #
    # ----------------------------------- #

    barra_superior.reordenar_paginas_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "reordenar_paginas"
        )
    )

    # ----------------------------------- #
    #          Comprimir PDF              #
    # ----------------------------------- #

    barra_superior.comprimir_pdf_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "comprimir_pdf"
        )
    )

    # ----------------------------------- #
    #            Acerca de                #
    # ----------------------------------- #

    barra_superior.acerca_de_solicitado.connect(
        lambda:
        mostrar_acerca_de(
            ventana
        )
    )


# ================================================================
# MOSTRAR HERRAMIENTA
# ================================================================
def mostrar_herramienta(
    ventana,
    herramienta
):

    # ----------------------------------- #
    #       Crear ventana una vez         #
    # ----------------------------------- #

    if (
        not hasattr(
            ventana,
            "ventana_herramientas"
        )
        or ventana.ventana_herramientas is None
    ):

        ventana.ventana_herramientas = (
            VentanaHerramientas()
        )


        ventana.ventana_herramientas.volver_solicitado.connect(
            lambda:
            volver_al_convertidor(
                ventana
            )
        )


    # ----------------------------------- #
    #      Seleccionar herramienta        #
    # ----------------------------------- #

    ventana.ventana_herramientas.mostrar_herramienta(
        herramienta
    )


    # ----------------------------------- #
    #        Centrar herramienta          #
    # ----------------------------------- #

    ventana.ventana_herramientas.centrar_en_pantalla(
        ventana
    )


    # ----------------------------------- #
    #      Ocultar ventana principal      #
    # ----------------------------------- #

    ventana.hide()


    # ----------------------------------- #
    #        Mostrar herramienta          #
    # ----------------------------------- #

    ventana.ventana_herramientas.show()

    ventana.ventana_herramientas.raise_()

    ventana.ventana_herramientas.activateWindow()


# ================================================================
# VOLVER AL CONVERTIDOR
# ================================================================
def volver_al_convertidor(
    ventana
):

    if hasattr(
        ventana,
        "ventana_herramientas"
    ):

        if ventana.ventana_herramientas is not None:

            ventana.ventana_herramientas.hide()


    ventana.show()

    ventana.raise_()

    ventana.activateWindow()


# ================================================================
# MOSTRAR ACERCA DE
# ================================================================
def mostrar_acerca_de(
    ventana
):

    dialogo = DialogoAcercaDe(
        ventana
    )

    dialogo.exec()


# ================================================================
# CREAR APLICACIÓN
# ================================================================
def crear_aplicacion():

    configurar_identidad_windows()


    aplicacion = QApplication(
        sys.argv
    )


    aplicacion.setApplicationName(
        NOMBRE_APLICACION
    )

    aplicacion.setApplicationDisplayName(
        NOMBRE_APLICACION
    )

    aplicacion.setApplicationVersion(
        VERSION_APLICACION
    )

    aplicacion.setOrganizationName(
        ORGANIZACION_APLICACION
    )


    # ----------------------------------- #
    #          Icono principal            #
    # ----------------------------------- #

    ruta_icono = obtener_ruta_icono_principal()


    if os.path.isfile(
        ruta_icono
    ):

        aplicacion.setWindowIcon(
            QIcon(
                ruta_icono
            )
        )


    return aplicacion


# ================================================================
# INICIAR APLICACIÓN
# ================================================================
def iniciar_aplicacion():

    aplicacion = crear_aplicacion()


    # ----------------------------------- #
    #         Ventana principal           #
    # ----------------------------------- #

    ventana = VentanaPrincipal()


    # ----------------------------------- #
    #          Barra superior             #
    # ----------------------------------- #

    configurar_barra_superior(
        ventana
    )


    # ----------------------------------- #
    #              Mostrar                #
    # ----------------------------------- #

    ventana.show()


    return aplicacion.exec()


# ================================================================
# INICIO
# ================================================================
if __name__ == "__main__":

    sys.exit(
        iniciar_aplicacion()
    )