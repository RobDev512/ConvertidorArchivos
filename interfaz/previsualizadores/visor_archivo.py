import os

from PySide6.QtCore import Qt, QSize, QFileInfo

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFileIconProvider
)


# ================================================================
# VISOR DE ARCHIVO
# ================================================================
class VisorArchivo(QWidget):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self):
        super().__init__()

        self.crear_interfaz()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(self):

        self.distribucion = QVBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            20,
            20,
            20,
            20
        )

        self.distribucion.setSpacing(
            15
        )


        # ----------------------------------- #
        #              Icono                  #
        # ----------------------------------- #

        self.etiqueta_icono = QLabel()

        self.etiqueta_icono.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_icono.setMinimumHeight(
            180
        )

        self.distribucion.addStretch()

        self.distribucion.addWidget(
            self.etiqueta_icono
        )


        # ----------------------------------- #
        #           Nombre de archivo         #
        # ----------------------------------- #

        self.etiqueta_nombre = QLabel()

        self.etiqueta_nombre.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_nombre.setWordWrap(
            True
        )

        self.distribucion.addWidget(
            self.etiqueta_nombre
        )

        self.distribucion.addStretch()


    # ============================================================
    # MOSTRAR ARCHIVO
    # ============================================================
    def mostrar_archivo(
        self,
        ruta_archivo,
        texto_personalizado=None
    ):

        proveedor = QFileIconProvider()

        icono = proveedor.icon(
            QFileInfo(
                ruta_archivo
            )
        )

        pixmap = icono.pixmap(
            QSize(
                128,
                128
            )
        )

        self.etiqueta_icono.setPixmap(
            pixmap
        )

        if texto_personalizado:

            texto = texto_personalizado

        else:

            texto = os.path.basename(
                ruta_archivo
            )

        self.etiqueta_nombre.setText(
            texto
        )