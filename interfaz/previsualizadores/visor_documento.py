import os

from PySide6.QtCore import Qt, Signal

from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton
)


# ================================================================
# VISOR DE DOCUMENTO
# ================================================================
class VisorDocumento(QWidget):

    anterior_solicitada = Signal()
    siguiente_solicitada = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self, nombre_unidad="Página"):
        super().__init__()

        self.nombre_unidad = nombre_unidad

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
        #          Página renderizada         #
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
        #          Nombre de archivo          #
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


        # ----------------------------------- #
        #            Navegación               #
        # ----------------------------------- #

        self.widget_navegacion = QWidget()

        distribucion_navegacion = QHBoxLayout(
            self.widget_navegacion
        )

        distribucion_navegacion.setContentsMargins(
            0,
            0,
            0,
            0
        )


        self.boton_anterior = QPushButton(
            "‹"
        )

        self.boton_anterior.setFixedWidth(
            42
        )


        self.etiqueta_pagina = QLabel()

        self.etiqueta_pagina.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        self.boton_siguiente = QPushButton(
            "›"
        )

        self.boton_siguiente.setFixedWidth(
            42
        )


        distribucion_navegacion.addWidget(
            self.boton_anterior
        )

        distribucion_navegacion.addWidget(
            self.etiqueta_pagina,
            1
        )

        distribucion_navegacion.addWidget(
            self.boton_siguiente
        )


        self.distribucion.addWidget(
            self.widget_navegacion
        )


        # ----------------------------------- #
        #              Eventos                #
        # ----------------------------------- #

        self.boton_anterior.clicked.connect(
            self.anterior_solicitada.emit
        )

        self.boton_siguiente.clicked.connect(
            self.siguiente_solicitada.emit
        )


    # ============================================================
    # MOSTRAR PÁGINA
    # ============================================================
    def mostrar_pagina(
        self,
        ruta_archivo,
        datos_imagen,
        pagina_actual,
        cantidad_paginas
    ):

        pixmap = QPixmap()

        if not pixmap.loadFromData(
            datos_imagen,
            "PNG"
        ):

            raise RuntimeError(
                "Qt no pudo mostrar esta página."
            )

        self.pixmap_original = pixmap


        self.etiqueta_nombre.setText(
            os.path.basename(
                ruta_archivo
            )
        )


        numero = pagina_actual + 1

        self.etiqueta_pagina.setText(
            f"{self.nombre_unidad} "
            f"{numero} de {cantidad_paginas}"
        )


        self.boton_anterior.setEnabled(
            pagina_actual > 0
        )

        self.boton_siguiente.setEnabled(
            pagina_actual < cantidad_paginas - 1
        )


        self.widget_navegacion.setVisible(
            cantidad_paginas > 1
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