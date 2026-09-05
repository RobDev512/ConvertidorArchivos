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

from interfaz.herramientas.panel_redimensionar_imagenes import (
    PanelRedimensionarImagenes
)

from interfaz.herramientas.panel_comprimir_imagenes import (
    PanelComprimirImagenes
)

from interfaz.herramientas.panel_imagenes_a_pdf import (
    PanelImagenesAPDF
)

from interfaz.herramientas.panel_mejorar_calidad import (
    PanelMejorarCalidad
)

from interfaz.herramientas.panel_quitar_fondo import (
    PanelQuitarFondo
)


# ================================================================
# VENTANA DE HERRAMIENTAS
# ================================================================
class VentanaHerramientas(
    QMainWindow
):

    volver_solicitado = Signal()


    # ============================================================
    # INICIALIZACION
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

        self.barra_superior = (
            BarraSuperiorHerramienta(
                self
            )
        )

        self.setMenuWidget(
            self.barra_superior
        )

        self.pila_herramientas = (
            QStackedWidget(
                self
            )
        )

        self.setCentralWidget(
            self.pila_herramientas
        )


        # ========================================================
        # PDF
        # ========================================================

        self.panel_unir_pdf = PanelPDF(
            self
        )

        self.pila_herramientas.addWidget(
            self.panel_unir_pdf
        )

        self.panel_dividir_pdf = (
            PanelDividirPDF(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_dividir_pdf
        )

        self.panel_extraer_paginas = (
            PanelExtraerPaginas(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_extraer_paginas
        )

        self.panel_reordenar_paginas = (
            PanelReordenarPaginas(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_reordenar_paginas
        )

        self.panel_comprimir_pdf = (
            PanelComprimirPDF(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_comprimir_pdf
        )


        # ========================================================
        # IMAGENES
        # ========================================================

        self.panel_redimensionar_imagenes = (
            PanelRedimensionarImagenes(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_redimensionar_imagenes
        )

        self.panel_comprimir_imagenes = (
            PanelComprimirImagenes(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_comprimir_imagenes
        )

        self.panel_imagenes_a_pdf = (
            PanelImagenesAPDF(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_imagenes_a_pdf
        )

        self.panel_mejorar_calidad = (
            PanelMejorarCalidad(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_mejorar_calidad
        )

        self.panel_quitar_fondo = (
            PanelQuitarFondo(
                self
            )
        )

        self.pila_herramientas.addWidget(
            self.panel_quitar_fondo
        )

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
    # APLICAR TAMANO DEL PANEL
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

        self.setMinimumSize(
            ancho_minimo,
            alto_minimo
        )

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

        configuraciones = {
            "unir_pdf": (
                self.panel_unir_pdf,
                "Unir PDFs - Convertidor de Archivos",
                "PDF  ·  Unir PDFs"
            ),
            "dividir_pdf": (
                self.panel_dividir_pdf,
                "Dividir PDF - Convertidor de Archivos",
                "PDF  ·  Dividir PDF"
            ),
            "extraer_paginas": (
                self.panel_extraer_paginas,
                "Extraer páginas - Convertidor de Archivos",
                "PDF  ·  Extraer páginas"
            ),
            "reordenar_paginas": (
                self.panel_reordenar_paginas,
                "Reordenar páginas - Convertidor de Archivos",
                "PDF  ·  Reordenar páginas"
            ),
            "comprimir_pdf": (
                self.panel_comprimir_pdf,
                "Comprimir PDF - Convertidor de Archivos",
                "PDF  ·  Comprimir PDF"
            ),
            "redimensionar_imagenes": (
                self.panel_redimensionar_imagenes,
                "Redimensionar imágenes - Convertidor de Archivos",
                "Imágenes  ·  Redimensionar"
            ),
            "comprimir_imagenes": (
                self.panel_comprimir_imagenes,
                "Comprimir imágenes - Convertidor de Archivos",
                "Imágenes  ·  Comprimir"
            ),
            "imagenes_a_pdf": (
                self.panel_imagenes_a_pdf,
                "Imágenes a PDF - Convertidor de Archivos",
                "Imágenes  ·  Imágenes → PDF"
            ),
            "mejorar_calidad_imagenes": (
                self.panel_mejorar_calidad,
                "Mejorar calidad - Convertidor de Archivos",
                "Imágenes  ·  Mejorar calidad"
            ),
            "quitar_fondo_imagenes": (
                self.panel_quitar_fondo,
                "Quitar fondo - Convertidor de Archivos",
                "Imágenes  ·  Quitar fondo"
            )
        }

        configuracion = configuraciones.get(
            herramienta
        )

        if configuracion is None:

            raise ValueError(
                f"Herramienta desconocida: "
                f"{herramienta}"
            )

        panel, titulo, seccion = (
            configuracion
        )

        self.pila_herramientas.setCurrentWidget(
            panel
        )

        self.aplicar_tamano_panel(
            panel
        )

        self.setWindowTitle(
            titulo
        )

        self.barra_superior.establecer_seccion(
            seccion
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

        if referencia is not None:

            try:

                pantalla = referencia.screen()

            except Exception:

                pantalla = None

        if pantalla is not None:

            self._pantalla_objetivo = (
                pantalla
            )

            return pantalla

        if self._pantalla_objetivo is not None:

            return self._pantalla_objetivo

        try:

            pantalla = self.screen()

        except Exception:

            pantalla = None

        if pantalla is None:

            pantalla = (
                QApplication.primaryScreen()
            )

        self._pantalla_objetivo = pantalla

        return pantalla


    # ============================================================
    # AJUSTAR TAMANO A PANTALLA
    # ============================================================
    def ajustar_tamano_a_pantalla(
        self,
        pantalla
    ):

        if pantalla is None:

            return

        area = pantalla.availableGeometry()

        margen = 16

        ancho_disponible = max(
            1,
            area.width()
            - margen
            * 2
        )

        alto_disponible = max(
            1,
            area.height()
            - margen
            * 2
        )

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