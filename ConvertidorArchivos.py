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

from interfaz.dialogo_acerca_de import DialogoAcercaDe
from interfaz.ventana_principal import VentanaPrincipal


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
# CONFIGURAR MENÚ DE AYUDA
# ================================================================
def configurar_menu_ayuda(
    ventana
):

    # ----------------------------------- #
    #            Menú Ayuda               #
    # ----------------------------------- #

    menu_ayuda = ventana.menuBar().addMenu(
        "Ayuda"
    )


    # ----------------------------------- #
    #           Acerca de                 #
    # ----------------------------------- #

    accion_acerca_de = menu_ayuda.addAction(
        f"Acerca de {NOMBRE_APLICACION}"
    )


    accion_acerca_de.triggered.connect(
        lambda checked=False:
        mostrar_acerca_de(
            ventana
        )
    )


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

    # ----------------------------------- #
    #       Identidad para Windows        #
    # ----------------------------------- #

    configurar_identidad_windows()


    # ----------------------------------- #
    #          Crear QApplication         #
    # ----------------------------------- #

    aplicacion = QApplication(
        sys.argv
    )


    # ----------------------------------- #
    #       Información general           #
    # ----------------------------------- #

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
    #       Icono general de la app       #
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
    #        Ventana principal            #
    # ----------------------------------- #

    ventana = VentanaPrincipal()


    # ----------------------------------- #
    #          Menú de ayuda              #
    # ----------------------------------- #

    configurar_menu_ayuda(
        ventana
    )


    # ----------------------------------- #
    #          Mostrar ventana            #
    # ----------------------------------- #

    ventana.show()


    # ----------------------------------- #
    #           Ejecutar Qt               #
    # ----------------------------------- #

    return aplicacion.exec()


# ================================================================
# INICIO
# ================================================================
if __name__ == "__main__":

    sys.exit(
        iniciar_aplicacion()
    )