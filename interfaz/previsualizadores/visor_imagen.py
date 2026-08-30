import os

from PySide6.QtCore import Qt

from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel
)


# ================================================================
# VISOR DE IMAGEN
# ================================================================
class VisorImagen(QWidget):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self):
        super().__init__()

        self.pixmap_original = None

        self.crear_interfaz()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(self):

        self.distribucion = QVBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            10,
            10,
            10,
            10
        )

        self.distribucion.setSpacing(
            10
        )


        # ----------------------------------- #
        #              Imagen                 #
        # ----------------------------------- #

        self.etiqueta_imagen = QLabel()

        self.etiqueta_imagen.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_imagen.setMinimumSize(
            200,
            250
        )

        self.distribucion.addWidget(
            self.etiqueta_imagen,
            1
        )


        # ----------------------------------- #
        #              Nombre                 #
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


    # ============================================================
    # MOSTRAR IMAGEN
    # ============================================================
    def mostrar_imagen(
        self,
        ruta_archivo,
        datos_imagen
    ):

        pixmap = QPixmap()

        if not pixmap.loadFromData(
            datos_imagen,
            "PNG"
        ):

            raise RuntimeError(
                "Qt no pudo mostrar la imagen de previsualización."
            )

        self.pixmap_original = pixmap

        self.etiqueta_nombre.setText(
            os.path.basename(
                ruta_archivo
            )
        )

        self.actualizar_imagen()


    # ============================================================
    # ACTUALIZAR IMAGEN
    # ============================================================
    def actualizar_imagen(self):

        if self.pixmap_original is None:
            return

        ancho = max(
            1,
            self.etiqueta_imagen.width() - 20
        )

        alto = max(
            1,
            self.etiqueta_imagen.height() - 20
        )

        pixmap = self.pixmap_original.scaled(
            ancho,
            alto,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.etiqueta_imagen.setPixmap(
            pixmap
        )


    # ============================================================
    # CAMBIO DE TAMAÑO
    # ============================================================
    def resizeEvent(self, evento):

        self.actualizar_imagen()

        super().resizeEvent(
            evento
        )