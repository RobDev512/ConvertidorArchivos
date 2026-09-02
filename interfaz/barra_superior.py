from PySide6.QtCore import (
    Qt,
    Signal,
    QTimer,
    QPoint
)

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QMenu,
    QToolButton,
    QApplication
)


# ================================================================
# ESTILOS DE BARRA SUPERIOR
# ================================================================

ESTILO_MENU = """
QMenu {
    background-color: #252526;
    border: 1px solid #454545;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    min-width: 235px;
    padding: 8px 28px 8px 12px;
    border-radius: 5px;
    color: #f0f0f0;
}

QMenu::item:selected {
    background-color: #3a3d41;
}

QMenu::item:disabled {
    color: #777777;
}

QMenu::separator {
    height: 1px;
    background-color: #454545;
    margin: 6px 8px;
}

QMenu::right-arrow {
    width: 8px;
    height: 8px;
}
"""


# ================================================================
# BOTÓN DE MENÚ CON HOVER
# ================================================================
class BotonMenuHover(QToolButton):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.temporizador_hover = QTimer(
            self
        )

        self.temporizador_hover.setSingleShot(
            True
        )

        self.temporizador_hover.setInterval(
            150
        )

        self.temporizador_hover.timeout.connect(
            self.mostrar_menu_hover
        )


    # ============================================================
    # ENTRAR CON EL CURSOR
    # ============================================================
    def enterEvent(
        self,
        evento
    ):

        super().enterEvent(
            evento
        )


        if (
            self.menu() is not None
            and not self.menu().isVisible()
        ):

            self.temporizador_hover.start()


    # ============================================================
    # SALIR CON EL CURSOR
    # ============================================================
    def leaveEvent(
        self,
        evento
    ):

        self.temporizador_hover.stop()

        super().leaveEvent(
            evento
        )


    # ============================================================
    # MOSTRAR MENÚ POR HOVER
    # ============================================================
    def mostrar_menu_hover(
        self
    ):

        menu = self.menu()


        if menu is None:

            return


        if menu.isVisible():

            return


        # ----------------------------------- #
        #       Cerrar otro menú abierto      #
        # ----------------------------------- #

        widget_popup = (
            QApplication.activePopupWidget()
        )


        if (
            widget_popup is not None
            and widget_popup is not menu
        ):

            widget_popup.close()


        # ----------------------------------- #
        #       Posición bajo el botón        #
        # ----------------------------------- #

        posicion = self.mapToGlobal(
            QPoint(
                0,
                self.height()
            )
        )


        # ----------------------------------- #
        #           Mostrar menú              #
        # ----------------------------------- #

        menu.popup(
            posicion
        )


# ================================================================
# BARRA SUPERIOR PRINCIPAL
# ================================================================
class BarraSuperiorPrincipal(QWidget):

    unir_pdfs_solicitado = Signal()

    dividir_pdf_solicitado = Signal()

    extraer_paginas_solicitado = Signal()

    reordenar_paginas_solicitado = Signal()

    comprimir_pdf_solicitado = Signal()

    acerca_de_solicitado = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.crear_interfaz()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self
    ):

        self.setObjectName(
            "BarraSuperiorPrincipal"
        )

        self.setFixedHeight(
            42
        )


        self.distribucion = QHBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            8,
            4,
            8,
            4
        )

        self.distribucion.setSpacing(
            2
        )


        # ----------------------------------- #
        #          Herramientas               #
        # ----------------------------------- #

        self.menu_herramientas = (
            self.crear_menu_herramientas()
        )

        self.boton_herramientas = (
            self.crear_boton_menu(
                "Herramientas",
                self.menu_herramientas
            )
        )

        self.distribucion.addWidget(
            self.boton_herramientas
        )


        # ----------------------------------- #
        #              Ayuda                  #
        # ----------------------------------- #

        self.menu_ayuda = (
            self.crear_menu_ayuda()
        )

        self.boton_ayuda = (
            self.crear_boton_menu(
                "Ayuda",
                self.menu_ayuda
            )
        )

        self.distribucion.addWidget(
            self.boton_ayuda
        )


        self.distribucion.addStretch(
            1
        )


        # ----------------------------------- #
        #            Apariencia               #
        # ----------------------------------- #

        self.setStyleSheet(
            """
            QWidget#BarraSuperiorPrincipal {
                background-color: #202020;
                border-bottom: 1px solid #353535;
            }

            QToolButton {
                border: none;
                border-radius: 5px;
                padding: 6px 11px;
                color: #f0f0f0;
                font-size: 13px;
            }

            QToolButton:hover {
                background-color: #333333;
            }

            QToolButton:pressed {
                background-color: #3f3f3f;
            }

            QToolButton::menu-indicator {
                image: none;
            }
            """
        )


    # ============================================================
    # CREAR BOTÓN DE MENÚ
    # ============================================================
    def crear_boton_menu(
        self,
        texto,
        menu
    ):

        boton = BotonMenuHover(
            self
        )

        boton.setText(
            f"{texto}  ▾"
        )

        boton.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextOnly
        )

        boton.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )

        boton.setMenu(
            menu
        )

        boton.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        return boton


    # ============================================================
    # CREAR MENÚ DE HERRAMIENTAS
    # ============================================================
    def crear_menu_herramientas(
        self
    ):

        menu = QMenu(
            self
        )

        menu.setMinimumWidth(
            285
        )

        menu.setStyleSheet(
            ESTILO_MENU
        )


        # ========================================================
        # PDF
        # ========================================================

        menu_pdf = menu.addMenu(
            "PDF"
        )

        menu_pdf.setMinimumWidth(
            285
        )


        # ----------------------------------- #
        #            Unir PDFs                #
        # ----------------------------------- #

        accion_unir = menu_pdf.addAction(
            "Unir PDFs"
        )

        accion_unir.triggered.connect(
            lambda checked=False:
            self.unir_pdfs_solicitado.emit()
        )


        # ----------------------------------- #
        #           Dividir PDF               #
        # ----------------------------------- #

        accion_dividir = menu_pdf.addAction(
            "Dividir PDF"
        )

        accion_dividir.triggered.connect(
            lambda checked=False:
            self.dividir_pdf_solicitado.emit()
        )


        # ----------------------------------- #
        #         Extraer páginas             #
        # ----------------------------------- #

        accion_extraer = menu_pdf.addAction(
            "Extraer páginas"
        )

        accion_extraer.triggered.connect(
            lambda checked=False:
            self.extraer_paginas_solicitado.emit()
        )


        # ----------------------------------- #
        #        Reordenar páginas            #
        # ----------------------------------- #

        accion_reordenar = menu_pdf.addAction(
            "Reordenar páginas"
        )

        accion_reordenar.triggered.connect(
            lambda checked=False:
            self.reordenar_paginas_solicitado.emit()
        )


        # ----------------------------------- #
        #         Comprimir PDF               #
        # ----------------------------------- #

        accion_comprimir = menu_pdf.addAction(
            "Comprimir PDF"
        )

        accion_comprimir.triggered.connect(
            lambda checked=False:
            self.comprimir_pdf_solicitado.emit()
        )


        # ========================================================
        # IMÁGENES
        # ========================================================

        menu_imagenes = menu.addMenu(
            "Imágenes"
        )

        menu_imagenes.setMinimumWidth(
            285
        )


        accion_redimensionar = (
            menu_imagenes.addAction(
                "Redimensionar  ·  Próximamente"
            )
        )

        accion_redimensionar.setEnabled(
            False
        )


        accion_comprimir_imagenes = (
            menu_imagenes.addAction(
                "Comprimir imágenes  ·  Próximamente"
            )
        )

        accion_comprimir_imagenes.setEnabled(
            False
        )


        accion_imagenes_pdf = (
            menu_imagenes.addAction(
                "Imágenes → PDF  ·  Próximamente"
            )
        )

        accion_imagenes_pdf.setEnabled(
            False
        )


        # ========================================================
        # RESTO DE HERRAMIENTAS
        # ========================================================

        menu.addSeparator()


        accion_comprimidos = menu.addAction(
            "Comprimidos  ·  Próximamente"
        )

        accion_comprimidos.setEnabled(
            False
        )


        accion_minecraft = menu.addAction(
            "Minecraft  ·  Próximamente"
        )

        accion_minecraft.setEnabled(
            False
        )


        return menu


    # ============================================================
    # CREAR MENÚ DE AYUDA
    # ============================================================
    def crear_menu_ayuda(
        self
    ):

        menu = QMenu(
            self
        )

        menu.setMinimumWidth(
            285
        )

        menu.setStyleSheet(
            ESTILO_MENU
        )


        accion_acerca_de = menu.addAction(
            "Acerca de Convertidor de Archivos"
        )

        accion_acerca_de.triggered.connect(
            lambda checked=False:
            self.acerca_de_solicitado.emit()
        )


        return menu


# ================================================================
# BARRA SUPERIOR DE HERRAMIENTA
# ================================================================
class BarraSuperiorHerramienta(QWidget):

    volver_solicitado = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.crear_interfaz()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self
    ):

        self.setObjectName(
            "BarraSuperiorHerramienta"
        )

        self.setFixedHeight(
            46
        )


        self.distribucion = QHBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            8,
            4,
            12,
            4
        )

        self.distribucion.setSpacing(
            10
        )


        # ----------------------------------- #
        #          Botón volver               #
        # ----------------------------------- #

        self.boton_volver = QToolButton(
            self
        )

        self.boton_volver.setText(
            "←  Volver al convertidor"
        )

        self.boton_volver.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.boton_volver.clicked.connect(
            self.volver_solicitado.emit
        )

        self.distribucion.addWidget(
            self.boton_volver
        )


        # ----------------------------------- #
        #          Separador                  #
        # ----------------------------------- #

        self.etiqueta_separador = QLabel(
            "│"
        )

        self.etiqueta_separador.setStyleSheet(
            "color: #555555;"
        )

        self.distribucion.addWidget(
            self.etiqueta_separador
        )


        # ----------------------------------- #
        #             Sección                 #
        # ----------------------------------- #

        self.etiqueta_seccion = QLabel(
            "Herramientas"
        )

        self.etiqueta_seccion.setStyleSheet(
            """
            QLabel {
                color: #cfcfcf;
                font-size: 13px;
                font-weight: 500;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_seccion
        )


        self.distribucion.addStretch(
            1
        )


        # ----------------------------------- #
        #            Apariencia               #
        # ----------------------------------- #

        self.setStyleSheet(
            """
            QWidget#BarraSuperiorHerramienta {
                background-color: #202020;
                border-bottom: 1px solid #353535;
            }

            QToolButton {
                border: none;
                border-radius: 5px;
                padding: 6px 11px;
                color: #f0f0f0;
                font-size: 13px;
            }

            QToolButton:hover {
                background-color: #333333;
            }

            QToolButton:pressed {
                background-color: #3f3f3f;
            }
            """
        )


    # ============================================================
    # ESTABLECER SECCIÓN
    # ============================================================
    def establecer_seccion(
        self,
        texto
    ):

        self.etiqueta_seccion.setText(
            texto
        )