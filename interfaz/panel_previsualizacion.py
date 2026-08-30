from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QFrame
)

from interfaz.previsualizadores.visor_archivo import VisorArchivo
from interfaz.previsualizadores.visor_imagen import VisorImagen
from interfaz.previsualizadores.visor_documento import VisorDocumento
from interfaz.previsualizadores.visor_presentacion import VisorPresentacion
from interfaz.previsualizadores.visor_hoja_calculo import VisorHojaCalculo


# ================================================================
# LADO DE PREVISUALIZACIÓN
# ================================================================
class LadoPrevisualizacion(QFrame):

    anterior_solicitada = Signal()
    siguiente_solicitada = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self, titulo):
        super().__init__()

        self.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        self.crear_interfaz(
            titulo
        )

        self.conectar_eventos()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(self, titulo):

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
            8
        )


        # ----------------------------------- #
        #              Título                 #
        # ----------------------------------- #

        self.etiqueta_titulo = QLabel(
            titulo
        )

        self.etiqueta_titulo.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )

        self.distribucion.addWidget(
            self.etiqueta_titulo
        )


        # ----------------------------------- #
        #            Visores                  #
        # ----------------------------------- #

        self.contenedor = QStackedWidget()

        self.distribucion.addWidget(
            self.contenedor,
            1
        )


        # Estado simple
        self.etiqueta_estado = QLabel(
            "Sin archivo"
        )

        self.etiqueta_estado.setWordWrap(
            True
        )

        self.contenedor.addWidget(
            self.etiqueta_estado
        )


        # Archivo genérico
        self.visor_archivo = VisorArchivo()

        self.contenedor.addWidget(
            self.visor_archivo
        )


        # Imagen
        self.visor_imagen = VisorImagen()

        self.contenedor.addWidget(
            self.visor_imagen
        )


        # Documento
        self.visor_documento = VisorDocumento(
            "Página"
        )

        self.contenedor.addWidget(
            self.visor_documento
        )


        # Presentación
        self.visor_presentacion = VisorPresentacion()

        self.contenedor.addWidget(
            self.visor_presentacion
        )


        # Hoja de cálculo
        self.visor_hoja_calculo = VisorHojaCalculo()

        self.contenedor.addWidget(
            self.visor_hoja_calculo
        )


    # ============================================================
    # CONECTAR EVENTOS
    # ============================================================
    def conectar_eventos(self):

        self.visor_documento.anterior_solicitada.connect(
            self.anterior_solicitada.emit
        )

        self.visor_documento.siguiente_solicitada.connect(
            self.siguiente_solicitada.emit
        )

        self.visor_presentacion.anterior_solicitada.connect(
            self.anterior_solicitada.emit
        )

        self.visor_presentacion.siguiente_solicitada.connect(
            self.siguiente_solicitada.emit
        )


    # ============================================================
    # MOSTRAR ESTADO
    # ============================================================
    def mostrar_estado(self, texto):

        self.etiqueta_estado.setText(
            texto
        )

        self.contenedor.setCurrentWidget(
            self.etiqueta_estado
        )


    # ============================================================
    # MOSTRAR ARCHIVO
    # ============================================================
    def mostrar_archivo(
        self,
        ruta_archivo,
        texto_personalizado=None
    ):

        self.visor_archivo.mostrar_archivo(
            ruta_archivo,
            texto_personalizado
        )

        self.contenedor.setCurrentWidget(
            self.visor_archivo
        )


    # ============================================================
    # MOSTRAR IMAGEN
    # ============================================================
    def mostrar_imagen(
        self,
        resultado
    ):

        self.visor_imagen.mostrar_imagen(
            resultado["ruta_archivo"],
            resultado["datos_imagen"]
        )

        self.contenedor.setCurrentWidget(
            self.visor_imagen
        )


    # ============================================================
    # MOSTRAR DOCUMENTO
    # ============================================================
    def mostrar_documento(
        self,
        resultado
    ):

        self.visor_documento.mostrar_pagina(
            resultado["ruta_archivo"],
            resultado["datos_imagen"],
            resultado["pagina_actual"],
            resultado["cantidad_paginas"]
        )

        self.contenedor.setCurrentWidget(
            self.visor_documento
        )


    # ============================================================
    # MOSTRAR PRESENTACIÓN
    # ============================================================
    def mostrar_presentacion(
        self,
        resultado
    ):

        self.visor_presentacion.mostrar_pagina(
            resultado["ruta_archivo"],
            resultado["datos_imagen"],
            resultado["pagina_actual"],
            resultado["cantidad_paginas"]
        )

        self.contenedor.setCurrentWidget(
            self.visor_presentacion
        )


    # ============================================================
    # MOSTRAR HOJA DE CÁLCULO
    # ============================================================
    def mostrar_hoja_calculo(
        self,
        resultado
    ):

        self.visor_hoja_calculo.mostrar_libro(
            resultado["ruta_archivo"],
            resultado["hojas"]
        )

        self.contenedor.setCurrentWidget(
            self.visor_hoja_calculo
        )


# ================================================================
# PANEL DE PREVISUALIZACIÓN
# ================================================================
class PanelPrevisualizacion(QWidget):

    pagina_anterior_solicitada = Signal(str)
    pagina_siguiente_solicitada = Signal(str)


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self):
        super().__init__()

        self.crear_interfaz()
        self.conectar_eventos()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(self):

        self.distribucion = QHBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.distribucion.setSpacing(
            12
        )


        # ----------------------------------- #
        #            Original                 #
        # ----------------------------------- #

        self.original = LadoPrevisualizacion(
            "Original"
        )

        self.distribucion.addWidget(
            self.original,
            1
        )


        # ----------------------------------- #
        #            Resultado                #
        # ----------------------------------- #

        self.resultado = LadoPrevisualizacion(
            "Resultado"
        )

        self.resultado.mostrar_estado(
            "Aún no hay resultado"
        )

        self.distribucion.addWidget(
            self.resultado,
            1
        )


    # ============================================================
    # CONECTAR EVENTOS
    # ============================================================
    def conectar_eventos(self):

        self.original.anterior_solicitada.connect(
            lambda: self.pagina_anterior_solicitada.emit(
                "original"
            )
        )

        self.original.siguiente_solicitada.connect(
            lambda: self.pagina_siguiente_solicitada.emit(
                "original"
            )
        )

        self.resultado.anterior_solicitada.connect(
            lambda: self.pagina_anterior_solicitada.emit(
                "resultado"
            )
        )

        self.resultado.siguiente_solicitada.connect(
            lambda: self.pagina_siguiente_solicitada.emit(
                "resultado"
            )
        )


    # ============================================================
    # OBTENER LADO
    # ============================================================
    def obtener_lado(self, lado):

        if lado == "original":
            return self.original

        if lado == "resultado":
            return self.resultado

        raise ValueError(
            f"Lado desconocido: {lado}"
        )


    # ============================================================
    # MOSTRAR ESTADO
    # ============================================================
    def mostrar_estado(
        self,
        lado,
        texto
    ):

        self.obtener_lado(
            lado
        ).mostrar_estado(
            texto
        )


    # ============================================================
    # MOSTRAR ARCHIVO
    # ============================================================
    def mostrar_archivo(
        self,
        lado,
        ruta_archivo,
        texto_personalizado=None
    ):

        self.obtener_lado(
            lado
        ).mostrar_archivo(
            ruta_archivo,
            texto_personalizado
        )


    # ============================================================
    # MOSTRAR RESULTADO PREPARADO
    # ============================================================
    def mostrar_previsualizacion(
        self,
        lado,
        resultado
    ):

        visor = self.obtener_lado(
            lado
        )

        tipo = resultado[
            "tipo"
        ]


        if tipo == "archivo":

            visor.mostrar_archivo(
                resultado["ruta_archivo"]
            )

            return


        if tipo == "imagen":

            visor.mostrar_imagen(
                resultado
            )

            return


        if tipo == "documento":

            visor.mostrar_documento(
                resultado
            )

            return


        if tipo == "presentacion":

            visor.mostrar_presentacion(
                resultado
            )

            return


        if tipo == "hoja_calculo":

            visor.mostrar_hoja_calculo(
                resultado
            )

            return


        visor.mostrar_estado(
            "No existe previsualización para este archivo."
        )