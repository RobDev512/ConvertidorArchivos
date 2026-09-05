import ctypes
import os
import sys

from PySide6.QtGui import (
    QIcon
)

from PySide6.QtWidgets import (
    QApplication
)

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

    ventana.barra_superior = (
        barra_superior
    )

    ventana.setMenuWidget(
        barra_superior
    )

    barra_superior.unir_pdfs_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "unir_pdf"
        )
    )

    barra_superior.dividir_pdf_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "dividir_pdf"
        )
    )

    barra_superior.extraer_paginas_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "extraer_paginas"
        )
    )

    barra_superior.reordenar_paginas_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "reordenar_paginas"
        )
    )

    barra_superior.comprimir_pdf_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "comprimir_pdf"
        )
    )

    barra_superior.redimensionar_imagenes_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "redimensionar_imagenes"
        )
    )

    barra_superior.comprimir_imagenes_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "comprimir_imagenes"
        )
    )

    barra_superior.imagenes_a_pdf_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "imagenes_a_pdf"
        )
    )

    barra_superior.mejorar_calidad_imagenes_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "mejorar_calidad_imagenes"
        )
    )

    barra_superior.quitar_fondo_imagenes_solicitado.connect(
        lambda:
        mostrar_herramienta(
            ventana,
            "quitar_fondo_imagenes"
        )
    )

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

    ventana.ventana_herramientas.mostrar_herramienta(
        herramienta
    )

    ventana.ventana_herramientas.centrar_en_pantalla(
        ventana
    )

    ventana.hide()

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

        if (
            ventana.ventana_herramientas
            is not None
        ):

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
# CREAR APLICACION
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

    ruta_icono = (
        obtener_ruta_icono_principal()
    )

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
# INICIAR APLICACION
# ================================================================
def iniciar_aplicacion():

    aplicacion = crear_aplicacion()

    ventana = VentanaPrincipal()

    configurar_barra_superior(
        ventana
    )

    ventana.show()

    return aplicacion.exec()


# ================================================================
# INICIO
# ================================================================
if __name__ == "__main__":

    sys.exit(
        iniciar_aplicacion()
    )