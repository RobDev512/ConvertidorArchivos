from PySide6.QtCore import (
    Qt,
    Signal,
    QTimer
)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget
)

from interfaz.barra_superior import (
    BarraSuperiorHerramienta
)

from interfaz.herramientas.panel_pdf import (
    PanelPDF
)

from interfaz.herramientas.panel_dividir_pdf import (
    PanelDividirPDF
)

from interfaz.herramientas.panel_extraer_paginas import (
    PanelExtraerPaginas
)

from interfaz.herramientas.panel_reordenar_paginas import (
    PanelReordenarPaginas
)

from interfaz.herramientas.panel_comprimir_pdf import (
    PanelComprimirPDF
)


# ================================================================
# VENTANA DE HERRAMIENTAS
# ================================================================
class VentanaHerramientas(QMainWindow):

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

        self._pantalla_objetivo = None

        self.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose,
            False
        )

        self.configurar_ventana()
        self.crear_interfaz()
        self.conectar_eventos()


    # ============================================================
    # CONFIGURAR VENTANA
    # ============================================================
    def configurar_ventana(
        self
    ):

        self.setWindowTitle(
            "Herramientas - Convertidor de Archivos"
        )

        self.resize(
            1150,
            760
        )

        self.setMinimumSize(
            1150,
            760
        )


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self
    ):

        # ----------------------------------- #
        #         Barra superior              #
        # ----------------------------------- #

        self.barra_superior = (
            BarraSuperiorHerramienta(
                self
            )
        )

        self.setMenuWidget(
            self.barra_superior
        )


        # ----------------------------------- #
        #         Pila de herramientas        #
        # ----------------------------------- #

        self.pila_herramientas = (
            QStackedWidget(
                self
            )
        )

        self.setCentralWidget(
            self.pila_herramientas
        )


        # ----------------------------------- #
        #             Unir PDF                #
        # ----------------------------------- #

        self.panel_unir_pdf = PanelPDF(
            self
        )

        self.pila_herramientas.addWidget(
            self.panel_unir_pdf
        )


        # ----------------------------------- #
        #           Dividir PDF               #
        # ----------------------------------- #

        self.panel_dividir_pdf = (
            PanelDividirPDF(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_dividir_pdf
        )


        # ----------------------------------- #
        #         Extraer páginas             #
        # ----------------------------------- #

        self.panel_extraer_paginas = (
            PanelExtraerPaginas(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_extraer_paginas
        )


        # ----------------------------------- #
        #        Reordenar páginas            #
        # ----------------------------------- #

        self.panel_reordenar_paginas = (
            PanelReordenarPaginas(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_reordenar_paginas
        )


        # ----------------------------------- #
        #          Comprimir PDF              #
        # ----------------------------------- #

        self.panel_comprimir_pdf = (
            PanelComprimirPDF(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_comprimir_pdf
        )


        # ----------------------------------- #
        #       Herramienta inicial           #
        # ----------------------------------- #

        self.mostrar_herramienta(
            "unir_pdf"
        )


    # ============================================================
    # CONECTAR EVENTOS
    # ============================================================
    def conectar_eventos(
        self
    ):

        self.barra_superior.volver_solicitado.connect(
            self.solicitar_volver
        )


    # ============================================================
    # APLICAR TAMAÑO DEL PANEL
    # ============================================================
    def aplicar_tamano_panel(
        self,
        panel
    ):

        ancho_inicial = getattr(
            panel,
            "ANCHO_INICIAL",
            1150
        )

        alto_inicial = getattr(
            panel,
            "ALTO_INICIAL",
            760
        )

        ancho_minimo = getattr(
            panel,
            "ANCHO_MINIMO",
            1150
        )

        alto_minimo = getattr(
            panel,
            "ALTO_MINIMO",
            760
        )


        # ----------------------------------- #
        #         Cambiar mínimo              #
        # ----------------------------------- #

        self.setMinimumSize(
            ancho_minimo,
            alto_minimo
        )


        # ----------------------------------- #
        #         Cambiar tamaño              #
        # ----------------------------------- #

        self.resize(
            ancho_inicial,
            alto_inicial
        )


    # ============================================================
    # MOSTRAR HERRAMIENTA
    # ============================================================
    def mostrar_herramienta(
        self,
        herramienta
    ):

        # ----------------------------------- #
        #             Unir PDF                #
        # ----------------------------------- #

        if herramienta == "unir_pdf":

            self.pila_herramientas.setCurrentWidget(
                self.panel_unir_pdf
            )

            self.aplicar_tamano_panel(
                self.panel_unir_pdf
            )

            self.setWindowTitle(
                "Unir PDFs - Convertidor de Archivos"
            )

            self.barra_superior.establecer_seccion(
                "PDF  ·  Unir PDFs"
            )

            return


        # ----------------------------------- #
        #           Dividir PDF               #
        # ----------------------------------- #

        if herramienta == "dividir_pdf":

            self.pila_herramientas.setCurrentWidget(
                self.panel_dividir_pdf
            )

            self.aplicar_tamano_panel(
                self.panel_dividir_pdf
            )

            self.setWindowTitle(
                "Dividir PDF - Convertidor de Archivos"
            )

            self.barra_superior.establecer_seccion(
                "PDF  ·  Dividir PDF"
            )

            return


        # ----------------------------------- #
        #         Extraer páginas             #
        # ----------------------------------- #

        if herramienta == "extraer_paginas":

            self.pila_herramientas.setCurrentWidget(
                self.panel_extraer_paginas
            )

            self.aplicar_tamano_panel(
                self.panel_extraer_paginas
            )

            self.setWindowTitle(
                "Extraer páginas - Convertidor de Archivos"
            )

            self.barra_superior.establecer_seccion(
                "PDF  ·  Extraer páginas"
            )

            return


        # ----------------------------------- #
        #        Reordenar páginas            #
        # ----------------------------------- #

        if herramienta == "reordenar_paginas":

            self.pila_herramientas.setCurrentWidget(
                self.panel_reordenar_paginas
            )

            self.aplicar_tamano_panel(
                self.panel_reordenar_paginas
            )

            self.setWindowTitle(
                "Reordenar páginas - Convertidor de Archivos"
            )

            self.barra_superior.establecer_seccion(
                "PDF  ·  Reordenar páginas"
            )

            return


        # ----------------------------------- #
        #          Comprimir PDF              #
        # ----------------------------------- #

        if herramienta == "comprimir_pdf":

            self.pila_herramientas.setCurrentWidget(
                self.panel_comprimir_pdf
            )

            self.aplicar_tamano_panel(
                self.panel_comprimir_pdf
            )

            self.setWindowTitle(
                "Comprimir PDF - Convertidor de Archivos"
            )

            self.barra_superior.establecer_seccion(
                "PDF  ·  Comprimir PDF"
            )

            return


        raise ValueError(
            f"Herramienta desconocida: {herramienta}"
        )


    # ============================================================
    # SOLICITAR VOLVER
    # ============================================================
    def solicitar_volver(
        self
    ):

        self.hide()

        self.volver_solicitado.emit()


    # ============================================================
    # OBTENER PANTALLA
    # ============================================================
    def obtener_pantalla(
        self,
        referencia=None
    ):

        pantalla = None


        # ----------------------------------- #
        #       Ventana de referencia         #
        # ----------------------------------- #

        if referencia is not None:

            try:

                pantalla = referencia.screen()

            except Exception:

                pantalla = None


        if pantalla is not None:

            self._pantalla_objetivo = pantalla

            return pantalla


        # ----------------------------------- #
        #     Última pantalla conocida        #
        # ----------------------------------- #

        if self._pantalla_objetivo is not None:

            return self._pantalla_objetivo


        # ----------------------------------- #
        #       Pantalla de esta ventana      #
        # ----------------------------------- #

        try:

            pantalla = self.screen()

        except Exception:

            pantalla = None


        # ----------------------------------- #
        #            Respaldo                 #
        # ----------------------------------- #

        if pantalla is None:

            pantalla = (
                QApplication.primaryScreen()
            )


        self._pantalla_objetivo = pantalla

        return pantalla


    # ============================================================
    # AJUSTAR TAMAÑO A PANTALLA
    # ============================================================
    def ajustar_tamano_a_pantalla(
        self,
        pantalla
    ):

        if pantalla is None:

            return


        # ----------------------------------- #
        #       Área útil de Windows          #
        # ----------------------------------- #

        area = pantalla.availableGeometry()

        margen = 16


        ancho_disponible = max(
            1,
            area.width()
            - margen * 2
        )

        alto_disponible = max(
            1,
            area.height()
            - margen * 2
        )


        # ----------------------------------- #
        #     Respetar tamaño del panel       #
        # ----------------------------------- #

        ancho = min(
            self.width(),
            ancho_disponible
        )

        alto = min(
            self.height(),
            alto_disponible
        )


        ancho = max(
            self.minimumWidth(),
            ancho
        )

        alto = max(
            self.minimumHeight(),
            alto
        )


        if (
            ancho != self.width()
            or alto != self.height()
        ):

            self.resize(
                ancho,
                alto
            )


    # ============================================================
    # CENTRAR EN PANTALLA
    # ============================================================
    def centrar_en_pantalla(
        self,
        referencia=None,
        ajustar_tamano=True
    ):

        pantalla = self.obtener_pantalla(
            referencia
        )

        if pantalla is None:

            return


        if ajustar_tamano:

            self.ajustar_tamano_a_pantalla(
                pantalla
            )


        area = pantalla.availableGeometry()

        marco = self.frameGeometry()

        marco.moveCenter(
            area.center()
        )


        x = marco.left()
        y = marco.top()

        x_minimo = area.left()
        y_minimo = area.top()

        x_maximo = (
            area.right()
            - marco.width()
            + 1
        )

        y_maximo = (
            area.bottom()
            - marco.height()
            + 1
        )


        if x_maximo < x_minimo:

            x = x_minimo

        else:

            x = max(
                x_minimo,
                min(
                    x,
                    x_maximo
                )
            )


        if y_maximo < y_minimo:

            y = y_minimo

        else:

            y = max(
                y_minimo,
                min(
                    y,
                    y_maximo
                )
            )


        self.move(
            x,
            y
        )


    # ============================================================
    # MOSTRAR VENTANA
    # ============================================================
    def showEvent(
        self,
        evento
    ):

        super().showEvent(
            evento
        )


        # ----------------------------------- #
        # El marco real de Windows se conoce  #
        # después de mostrar la ventana.      #
        # ----------------------------------- #

        QTimer.singleShot(
            0,
            lambda:
            self.centrar_en_pantalla(
                ajustar_tamano=False
            )
        )


    # ============================================================
    # CERRAR VENTANA
    # ============================================================
    def closeEvent(
        self,
        evento
    ):

        evento.ignore()

        self.hide()

        self.volver_solicitado.emit()