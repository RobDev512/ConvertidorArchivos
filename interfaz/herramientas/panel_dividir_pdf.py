import math
import os

from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
    Slot,
    QObject,
    QThread,
    QRect,
    QPoint
)

from PySide6.QtGui import (
    QPixmap
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QFileDialog,
    QMessageBox,
    QSpinBox,
    QLineEdit,
    QScrollArea,
    QFrame,
    QProgressBar,
    QLayout,
    QSizePolicy,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QDialog
)

from conversiones.previsualizacion import (
    obtener_cantidad_paginas_pdf,
    renderizar_pagina_pdf
)

from herramientas.pdf.separar_pdf import (
    separar_pdf_por_cortes,
    separar_pdf_por_paginas,
    separar_pdf_por_bloques
)

from herramientas.pdf.extraer_paginas import (
    extraer_paginas_unidas,
    extraer_paginas_individuales,
    separar_seleccionadas_y_resto
)

from funciones.configuracion_app import (
    obtener_ruta_recurso
)


# ----------------------------------- #
#      Tamaño de las miniaturas       #
# ----------------------------------- #

ANCHO_TARJETA = 185
ALTO_TARJETA = 310

ANCHO_MINIATURA = 145
ALTO_MINIATURA = 185


# ================================================================
# ESTILO DE RADIO BUTTONS
# ================================================================
def obtener_estilo_radio(
    tamano=20,
    negrita=False
):

    ruta_lleno = obtener_ruta_recurso(
        "iconos",
        "RBlLleno.png"
    ).replace(
        "\\",
        "/"
    )

    ruta_vacio = obtener_ruta_recurso(
        "iconos",
        "RBVacio.png"
    ).replace(
        "\\",
        "/"
    )

    peso_fuente = (
        "600"
        if negrita
        else "400"
    )

    return f"""
    QRadioButton {{
        spacing: 8px;
        padding: 3px;
        font-weight: {peso_fuente};
    }}

    QRadioButton::indicator {{
        width: {tamano}px;
        height: {tamano}px;
    }}

    QRadioButton::indicator:unchecked {{
        image: url("{ruta_vacio}");
    }}

    QRadioButton::indicator:checked {{
        image: url("{ruta_lleno}");
    }}
    """


# ================================================================
# DISPOSICIÓN DE FLUJO
# ================================================================
class DisposicionFlujo(QLayout):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        parent=None,
        margen=0,
        espacio=8
    ):

        super().__init__(
            parent
        )

        self.elementos = []

        self.setContentsMargins(
            margen,
            margen,
            margen,
            margen
        )

        self.setSpacing(
            espacio
        )


    # ============================================================
    # AÑADIR ELEMENTO
    # ============================================================
    def addItem(
        self,
        elemento
    ):

        self.elementos.append(
            elemento
        )


    # ============================================================
    # CANTIDAD
    # ============================================================
    def count(
        self
    ):

        return len(
            self.elementos
        )


    # ============================================================
    # OBTENER ELEMENTO
    # ============================================================
    def itemAt(
        self,
        indice
    ):

        if (
            0
            <= indice
            < len(
                self.elementos
            )
        ):

            return self.elementos[
                indice
            ]

        return None


    # ============================================================
    # EXTRAER ELEMENTO
    # ============================================================
    def takeAt(
        self,
        indice
    ):

        if (
            0
            <= indice
            < len(
                self.elementos
            )
        ):

            return self.elementos.pop(
                indice
            )

        return None


    # ============================================================
    # ALTURA SEGÚN ANCHO
    # ============================================================
    def hasHeightForWidth(
        self
    ):

        return True


    # ============================================================
    # CALCULAR ALTURA
    # ============================================================
    def heightForWidth(
        self,
        ancho
    ):

        return self.hacer_disposicion(
            QRect(
                0,
                0,
                ancho,
                0
            ),
            True
        )


    # ============================================================
    # TAMAÑO MÍNIMO
    # ============================================================
    def minimumSize(
        self
    ):

        tamano = QSize()

        for elemento in self.elementos:

            tamano = tamano.expandedTo(
                elemento.minimumSize()
            )

        izquierda, arriba, derecha, abajo = (
            self.getContentsMargins()
        )

        tamano += QSize(
            izquierda + derecha,
            arriba + abajo
        )

        return tamano


    # ============================================================
    # TAMAÑO SUGERIDO
    # ============================================================
    def sizeHint(
        self
    ):

        return self.minimumSize()


    # ============================================================
    # ESTABLECER GEOMETRÍA
    # ============================================================
    def setGeometry(
        self,
        rectangulo
    ):

        super().setGeometry(
            rectangulo
        )

        self.hacer_disposicion(
            rectangulo,
            False
        )


    # ============================================================
    # HACER DISPOSICIÓN
    # ============================================================
    def hacer_disposicion(
        self,
        rectangulo,
        solo_calculo
    ):

        izquierda, arriba, derecha, abajo = (
            self.getContentsMargins()
        )

        area = rectangulo.adjusted(
            izquierda,
            arriba,
            -derecha,
            -abajo
        )

        x = area.x()
        y = area.y()

        alto_fila = 0

        espacio = self.spacing()

        if espacio < 0:

            espacio = 8

        for elemento in self.elementos:

            tamano = elemento.sizeHint()

            siguiente_x = (
                x
                + tamano.width()
                + espacio
            )

            if (
                x > area.x()
                and siguiente_x - espacio
                > area.right() + 1
            ):

                x = area.x()

                y += (
                    alto_fila
                    + espacio
                )

                alto_fila = 0

                siguiente_x = (
                    x
                    + tamano.width()
                    + espacio
                )

            if not solo_calculo:

                elemento.setGeometry(
                    QRect(
                        QPoint(
                            x,
                            y
                        ),
                        tamano
                    )
                )

            x = siguiente_x

            alto_fila = max(
                alto_fila,
                tamano.height()
            )

        return (
            y
            + alto_fila
            - rectangulo.y()
            + abajo
        )


# ================================================================
# CONTENEDOR DE FLUJO
# ================================================================
class ContenedorFlujo(QWidget):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        parent=None,
        margen=0,
        espacio=8
    ):

        super().__init__(
            parent
        )

        self.disposicion = DisposicionFlujo(
            self,
            margen=margen,
            espacio=espacio
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )


    # ============================================================
    # CAMBIAR TAMAÑO
    # ============================================================
    def resizeEvent(
        self,
        evento
    ):

        super().resizeEvent(
            evento
        )

        alto = self.disposicion.heightForWidth(
            evento.size().width()
        )

        self.setMinimumHeight(
            max(
                0,
                alto
            )
        )


    # ============================================================
    # LIMPIAR
    # ============================================================
    def limpiar(
        self
    ):

        while self.disposicion.count():

            elemento = self.disposicion.takeAt(
                0
            )

            widget = elemento.widget()

            if widget is not None:

                widget.deleteLater()

        self.setMinimumHeight(
            0
        )


# ================================================================
# MARCO DE PÁGINAS AMPLIABLE
# ================================================================
class MarcoPaginasAmpliable(QFrame):

    ampliar_solicitado = Signal()


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

        self.crear_boton_ampliar()


    # ============================================================
    # CREAR BOTÓN
    # ============================================================
    def crear_boton_ampliar(
        self
    ):

        self.boton_ampliar = QToolButton(
            self
        )

        self.boton_ampliar.setText(
            "⛶"
        )

        self.boton_ampliar.setToolTip(
            "Ampliar vista de páginas"
        )

        self.boton_ampliar.setFixedSize(
            36,
            36
        )

        self.boton_ampliar.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.boton_ampliar.setStyleSheet(
            """
            QToolButton {
                background-color: rgba(28, 28, 28, 225);
                border: 1px solid rgba(150, 150, 150, 90);
                border-radius: 8px;
                font-size: 19px;
                padding: 0px;
            }

            QToolButton:hover {
                background-color: rgba(80, 160, 255, 45);
                border: 1px solid rgba(80, 160, 255, 210);
            }

            QToolButton:pressed {
                background-color: rgba(80, 160, 255, 70);
            }
            """
        )

        self.boton_ampliar.clicked.connect(
            self.ampliar_solicitado.emit
        )


    # ============================================================
    # CAMBIAR ESTADO DEL BOTÓN
    # ============================================================
    def establecer_vista_ampliada(
        self,
        ampliada
    ):

        if ampliada:

            self.boton_ampliar.setText(
                "↙"
            )

            self.boton_ampliar.setToolTip(
                "Volver a la vista normal"
            )

        else:

            self.boton_ampliar.setText(
                "⛶"
            )

            self.boton_ampliar.setToolTip(
                "Ampliar vista de páginas"
            )


    # ============================================================
    # CAMBIO DE TAMAÑO
    # ============================================================
    def resizeEvent(
        self,
        evento
    ):

        super().resizeEvent(
            evento
        )

        margen_derecho = 28
        margen_superior = 8

        x = (
            self.width()
            - self.boton_ampliar.width()
            - margen_derecho
        )

        self.boton_ampliar.move(
            max(
                8,
                x
            ),
            margen_superior
        )

        self.boton_ampliar.raise_()


# ================================================================
# OPCIÓN DE RADIO TIPO TARJETA
# ================================================================
class OpcionRadioTarjeta(QFrame):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        titulo,
        descripcion,
        valor,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.valor = valor

        self.crear_interfaz(
            titulo,
            descripcion
        )

        self.actualizar_apariencia()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self,
        titulo,
        descripcion
    ):

        self.setObjectName(
            "OpcionRadioTarjeta"
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setMinimumHeight(
            74
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )


        self.distribucion = QVBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            12,
            9,
            12,
            9
        )

        self.distribucion.setSpacing(
            3
        )


        # ----------------------------------- #
        #            Radio button             #
        # ----------------------------------- #

        self.radio = QRadioButton(
            titulo
        )

        self.radio.setProperty(
            "valor",
            self.valor
        )

        self.radio.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.radio.setStyleSheet(
            obtener_estilo_radio(
                tamano=20,
                negrita=True
            )
        )

        self.distribucion.addWidget(
            self.radio
        )


        # ----------------------------------- #
        #            Descripción              #
        # ----------------------------------- #

        self.etiqueta_descripcion = QLabel(
            descripcion
        )

        self.etiqueta_descripcion.setWordWrap(
            True
        )

        self.etiqueta_descripcion.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        self.etiqueta_descripcion.setStyleSheet(
            """
            QLabel {
                color: #9e9e9e;
                font-size: 12px;
                padding-left: 31px;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_descripcion
        )


        self.radio.toggled.connect(
            self.actualizar_apariencia
        )


    # ============================================================
    # CLIC EN TARJETA
    # ============================================================
    def mousePressEvent(
        self,
        evento
    ):

        if evento.button() == Qt.MouseButton.LeftButton:

            self.radio.setChecked(
                True
            )

            evento.accept()

            return

        super().mousePressEvent(
            evento
        )


    # ============================================================
    # ACTUALIZAR APARIENCIA
    # ============================================================
    def actualizar_apariencia(
        self
    ):

        if self.radio.isChecked():

            self.setStyleSheet(
                """
                QFrame#OpcionRadioTarjeta {
                    background-color: rgba(80, 160, 255, 22);
                    border: 1px solid rgba(80, 160, 255, 210);
                    border-radius: 9px;
                }

                QFrame#OpcionRadioTarjeta:hover {
                    background-color: rgba(80, 160, 255, 30);
                }
                """
            )

        else:

            self.setStyleSheet(
                """
                QFrame#OpcionRadioTarjeta {
                    background-color: rgba(255, 255, 255, 7);
                    border: 1px solid rgba(145, 145, 145, 65);
                    border-radius: 9px;
                }

                QFrame#OpcionRadioTarjeta:hover {
                    background-color: rgba(255, 255, 255, 12);
                    border: 1px solid rgba(100, 170, 255, 130);
                }
                """
            )


# ================================================================
# TARJETA DE PÁGINA
# ================================================================
class TarjetaPaginaDivision(QFrame):

    corte_cambiado = Signal(
        int,
        bool
    )

    seleccion_cambiada = Signal(
        int,
        bool
    )

    rango_solicitado = Signal(
        int
    )


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        indice_pagina,
        cantidad_paginas,
        pixmap,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.indice_pagina = indice_pagina

        self.numero_pagina = (
            indice_pagina
            + 1
        )

        self.cantidad_paginas = cantidad_paginas

        self.es_ultima = (
            self.numero_pagina
            >= cantidad_paginas
        )

        self.modo_actual = "cortes"

        self.crear_interfaz(
            pixmap
        )

        self.actualizar_apariencia()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self,
        pixmap
    ):

        self.setObjectName(
            "TarjetaPaginaDivision"
        )

        self.setFixedSize(
            ANCHO_TARJETA,
            ALTO_TARJETA
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )


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
            6
        )


        # ----------------------------------- #
        #            Miniatura                #
        # ----------------------------------- #

        self.etiqueta_imagen = QLabel()

        self.etiqueta_imagen.setFixedSize(
            ANCHO_MINIATURA,
            ALTO_MINIATURA
        )

        self.etiqueta_imagen.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_imagen.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )


        pixmap_escalado = pixmap.scaled(
            ANCHO_MINIATURA,
            ALTO_MINIATURA,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.etiqueta_imagen.setPixmap(
            pixmap_escalado
        )

        self.etiqueta_imagen.setStyleSheet(
            """
            QLabel {
                background-color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_imagen,
            0,
            Qt.AlignmentFlag.AlignHCenter
        )


        # ----------------------------------- #
        #              Página                 #
        # ----------------------------------- #

        self.etiqueta_pagina = QLabel(
            f"Página {self.numero_pagina}"
        )

        self.etiqueta_pagina.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_pagina.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        self.etiqueta_pagina.setStyleSheet(
            """
            QLabel {
                font-weight: 600;
                font-size: 13px;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_pagina
        )


        # ----------------------------------- #
        #              Parte                  #
        # ----------------------------------- #

        self.etiqueta_parte = QLabel(
            "Parte 1"
        )

        self.etiqueta_parte.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_parte.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        self.etiqueta_parte.setStyleSheet(
            """
            QLabel {
                color: #9c9c9c;
                font-size: 12px;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_parte
        )


        # ----------------------------------- #
        #          Cortar después             #
        # ----------------------------------- #

        self.boton_corte = QPushButton(
            "✂  Cortar después"
        )

        self.boton_corte.setCheckable(
            True
        )

        self.boton_corte.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.boton_corte.toggled.connect(
            self.emitir_corte
        )

        self.distribucion.addWidget(
            self.boton_corte
        )


        # ----------------------------------- #
        #            Selección                #
        # ----------------------------------- #

        self.casilla_seleccion = QCheckBox(
            "Seleccionar"
        )

        self.casilla_seleccion.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.casilla_seleccion.toggled.connect(
            self.emitir_seleccion
        )

        self.distribucion.addWidget(
            self.casilla_seleccion,
            0,
            Qt.AlignmentFlag.AlignHCenter
        )


    # ============================================================
    # CAMBIAR MODO
    # ============================================================
    def establecer_modo(
        self,
        modo
    ):

        self.modo_actual = modo

        es_cortes = (
            modo == "cortes"
        )

        self.etiqueta_parte.setVisible(
            es_cortes
        )

        self.boton_corte.setVisible(
            es_cortes
            and not self.es_ultima
        )

        self.casilla_seleccion.setVisible(
            not es_cortes
        )

        self.actualizar_apariencia()


    # ============================================================
    # EMITIR CORTE
    # ============================================================
    def emitir_corte(
        self,
        activo
    ):

        self.corte_cambiado.emit(
            self.numero_pagina,
            activo
        )


    # ============================================================
    # EMITIR SELECCIÓN
    # ============================================================
    def emitir_seleccion(
        self,
        activo
    ):

        self.actualizar_apariencia()

        self.seleccion_cambiada.emit(
            self.numero_pagina,
            activo
        )


    # ============================================================
    # CLIC EN TARJETA
    # ============================================================
    def mousePressEvent(
        self,
        evento
    ):

        if (
            self.modo_actual == "seleccion"
            and evento.button()
            == Qt.MouseButton.LeftButton
        ):

            if (
                evento.modifiers()
                & Qt.KeyboardModifier.ShiftModifier
            ):

                self.rango_solicitado.emit(
                    self.numero_pagina
                )

            else:

                self.casilla_seleccion.toggle()

            evento.accept()

            return

        super().mousePressEvent(
            evento
        )


    # ============================================================
    # ESTABLECER CORTE
    # ============================================================
    def establecer_corte(
        self,
        activo,
        editable
    ):

        self.boton_corte.blockSignals(
            True
        )

        self.boton_corte.setChecked(
            activo
        )

        self.boton_corte.setEnabled(
            editable
        )

        self.boton_corte.blockSignals(
            False
        )


    # ============================================================
    # ESTABLECER SELECCIÓN
    # ============================================================
    def establecer_seleccion(
        self,
        seleccionada
    ):

        self.casilla_seleccion.blockSignals(
            True
        )

        self.casilla_seleccion.setChecked(
            seleccionada
        )

        self.casilla_seleccion.blockSignals(
            False
        )

        self.actualizar_apariencia()


    # ============================================================
    # ESTABLECER PARTE
    # ============================================================
    def establecer_parte(
        self,
        numero_parte
    ):

        self.etiqueta_parte.setText(
            f"Parte {numero_parte}"
        )


    # ============================================================
    # ACTUALIZAR APARIENCIA
    # ============================================================
    def actualizar_apariencia(
        self
    ):

        seleccionada = (
            self.modo_actual == "seleccion"
            and self.casilla_seleccion.isChecked()
        )


        if seleccionada:

            borde = (
                "2px solid rgba(80, 160, 255, 230)"
            )

            fondo = (
                "rgba(80, 160, 255, 28)"
            )

        else:

            borde = (
                "1px solid rgba(150, 150, 150, 70)"
            )

            fondo = (
                "rgba(255, 255, 255, 8)"
            )


        self.setStyleSheet(
            f"""
            QFrame#TarjetaPaginaDivision {{
                background-color: {fondo};
                border: {borde};
                border-radius: 10px;
            }}

            QPushButton {{
                min-height: 28px;
                border: 1px solid rgba(130, 130, 130, 90);
                border-radius: 6px;
                padding: 3px 7px;
            }}

            QPushButton:hover {{
                border: 1px solid rgba(100, 170, 255, 180);
            }}

            QPushButton:checked {{
                border: 2px dashed rgba(80, 160, 255, 230);
                background-color: rgba(80, 160, 255, 35);
                font-weight: 600;
            }}

            QPushButton:checked:disabled {{
                border: 2px dashed rgba(80, 160, 255, 150);
                background-color: rgba(80, 160, 255, 22);
            }}

            QCheckBox {{
                font-size: 12px;
                padding: 3px;
            }}
            """
        )


# ================================================================
# TRABAJADOR DE CARGA DE PDF
# ================================================================
class TrabajadorCargaDivisionPDF(QObject):

    cantidad_detectada = Signal(
        int
    )

    pagina_generada = Signal(
        int,
        bytes
    )

    error = Signal(
        str
    )

    finalizado = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        ruta_pdf
    ):

        super().__init__()

        self.ruta_pdf = ruta_pdf


    # ============================================================
    # EJECUTAR
    # ============================================================
    @Slot()
    def ejecutar(
        self
    ):

        try:

            cantidad_paginas = (
                obtener_cantidad_paginas_pdf(
                    self.ruta_pdf
                )
            )

            self.cantidad_detectada.emit(
                cantidad_paginas
            )


            for indice_pagina in range(
                cantidad_paginas
            ):

                datos_imagen = (
                    renderizar_pagina_pdf(
                        self.ruta_pdf,
                        indice_pagina
                    )
                )

                self.pagina_generada.emit(
                    indice_pagina,
                    datos_imagen
                )


        except Exception as error:

            self.error.emit(
                str(
                    error
                )
            )


        finally:

            self.finalizado.emit()


# ================================================================
# TRABAJADOR DE PROCESAMIENTO
# ================================================================
class TrabajadorDivisionPDF(QObject):

    progreso = Signal(
        int,
        int
    )

    completado = Signal(
        list
    )

    cancelado = Signal()

    error = Signal(
        str
    )

    finalizado = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        ruta_pdf,
        carpeta_salida,
        operacion,
        modo=None,
        cortes=None,
        paginas=None,
        paginas_por_archivo=None
    ):

        super().__init__()

        self.ruta_pdf = ruta_pdf
        self.carpeta_salida = carpeta_salida

        self.operacion = operacion
        self.modo = modo

        self.cortes = cortes or []
        self.paginas = paginas or []

        self.paginas_por_archivo = (
            paginas_por_archivo
        )

        self.cancelacion_solicitada = False


    # ============================================================
    # COMPROBAR CANCELACIÓN
    # ============================================================
    def comprobar_cancelacion(
        self
    ):

        return self.cancelacion_solicitada


    # ============================================================
    # CANCELAR
    # ============================================================
    def cancelar(
        self
    ):

        self.cancelacion_solicitada = True


    # ============================================================
    # PROGRESO
    # ============================================================
    def informar_progreso(
        self,
        actual,
        total,
        *datos
    ):

        self.progreso.emit(
            actual,
            total
        )


    # ============================================================
    # EJECUTAR
    # ============================================================
    @Slot()
    def ejecutar(
        self
    ):

        try:

            # ================================================ #
            # CORTAR DOCUMENTO
            # ================================================ #

            if self.operacion == "cortes":

                if self.modo == "manual":

                    resultados = separar_pdf_por_cortes(
                        self.ruta_pdf,
                        self.cortes,
                        self.carpeta_salida,
                        progreso=self.informar_progreso,
                        comprobar_cancelacion=(
                            self.comprobar_cancelacion
                        )
                    )


                elif self.modo == "paginas":

                    resultados = separar_pdf_por_paginas(
                        self.ruta_pdf,
                        self.carpeta_salida,
                        progreso=self.informar_progreso,
                        comprobar_cancelacion=(
                            self.comprobar_cancelacion
                        )
                    )


                elif self.modo == "bloques":

                    resultados = separar_pdf_por_bloques(
                        self.ruta_pdf,
                        self.paginas_por_archivo,
                        self.carpeta_salida,
                        progreso=self.informar_progreso,
                        comprobar_cancelacion=(
                            self.comprobar_cancelacion
                        )
                    )


                else:

                    raise ValueError(
                        "El modo de división no es válido."
                    )


            # ================================================ #
            # SELECCIONAR PÁGINAS
            # ================================================ #

            elif self.operacion == "seleccion":

                if self.modo == "unidas":

                    resultados = extraer_paginas_unidas(
                        self.ruta_pdf,
                        self.paginas,
                        self.carpeta_salida,
                        progreso=self.informar_progreso,
                        comprobar_cancelacion=(
                            self.comprobar_cancelacion
                        )
                    )


                elif self.modo == "individuales":

                    resultados = extraer_paginas_individuales(
                        self.ruta_pdf,
                        self.paginas,
                        self.carpeta_salida,
                        progreso=self.informar_progreso,
                        comprobar_cancelacion=(
                            self.comprobar_cancelacion
                        )
                    )


                elif self.modo == "seleccion_resto":

                    resultados = separar_seleccionadas_y_resto(
                        self.ruta_pdf,
                        self.paginas,
                        self.carpeta_salida,
                        progreso=self.informar_progreso,
                        comprobar_cancelacion=(
                            self.comprobar_cancelacion
                        )
                    )


                else:

                    raise ValueError(
                        "La acción de selección no es válida."
                    )


            else:

                raise ValueError(
                    "La operación seleccionada no es válida."
                )


            if self.cancelacion_solicitada:

                self.cancelado.emit()

                return


            self.completado.emit(
                resultados
            )


        except Exception as error:

            if self.cancelacion_solicitada:

                self.cancelado.emit()

            else:

                self.error.emit(
                    str(
                        error
                    )
                )


        finally:

            self.finalizado.emit()


# ================================================================
# PANEL DIVIDIR PDF
# ================================================================
class PanelDividirPDF(QWidget):

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


        # ----------------------------------- #
        #          Documento actual           #
        # ----------------------------------- #

        self.ruta_pdf = None
        self.cantidad_paginas = 0
        self.tarjetas = []


        # ----------------------------------- #
        #       Cortes y selección            #
        # ----------------------------------- #

        self.cortes_manuales = set()

        self.paginas_seleccionadas = set()

        self.ultima_pagina_seleccionada = None


        # ----------------------------------- #
        #              Hilos                  #
        # ----------------------------------- #

        self.hilo_carga = None
        self.trabajador_carga = None
        self.error_carga_actual = None

        self.hilo_division = None
        self.trabajador_division = None


        # ----------------------------------- #
        #        Vista de páginas grande      #
        # ----------------------------------- #

        self.dialogo_paginas = None
        self.indice_marco_paginas = 1


        self.crear_interfaz()
        self.conectar_eventos()

        self.actualizar_operacion()
        self.actualizar_estado_controles()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self
    ):

        self.distribucion = QVBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            18,
            14,
            18,
            14
        )

        self.distribucion.setSpacing(
            8
        )


        # ========================================================
        # CONFIGURACIÓN
        # ========================================================

        self.contenedor_configuracion = QWidget()

        self.contenedor_configuracion.setStyleSheet(
            "background: transparent;"
        )


        self.distribucion_configuracion = QVBoxLayout(
            self.contenedor_configuracion
        )

        self.distribucion_configuracion.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.distribucion_configuracion.setSpacing(
            8
        )


        self.distribucion.addWidget(
            self.contenedor_configuracion
        )


        # ----------------------------------- #
        #               Título                #
        # ----------------------------------- #

        self.etiqueta_titulo = QLabel(
            "Dividir PDF"
        )

        self.etiqueta_titulo.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: 600;
            }
            """
        )

        self.distribucion_configuracion.addWidget(
            self.etiqueta_titulo
        )


        # ----------------------------------- #
        #            Descripción              #
        # ----------------------------------- #

        self.etiqueta_descripcion = QLabel()

        self.etiqueta_descripcion.setWordWrap(
            True
        )

        self.distribucion_configuracion.addWidget(
            self.etiqueta_descripcion
        )


        # ========================================================
        # ARCHIVO PDF
        # ========================================================

        self.distribucion_archivo = QHBoxLayout()

        self.distribucion_archivo.setSpacing(
            8
        )


        self.etiqueta_archivo = QLabel(
            "PDF:"
        )

        self.distribucion_archivo.addWidget(
            self.etiqueta_archivo
        )


        self.campo_archivo = QLineEdit()

        self.campo_archivo.setReadOnly(
            True
        )

        self.campo_archivo.setPlaceholderText(
            "Selecciona un archivo PDF"
        )

        self.campo_archivo.setMinimumWidth(
            0
        )

        self.distribucion_archivo.addWidget(
            self.campo_archivo,
            1
        )


        self.boton_seleccionar = QPushButton(
            "Seleccionar PDF"
        )

        self.boton_seleccionar.setMinimumHeight(
            34
        )

        self.boton_seleccionar.setMinimumWidth(
            120
        )

        self.distribucion_archivo.addWidget(
            self.boton_seleccionar
        )


        self.distribucion_configuracion.addLayout(
            self.distribucion_archivo
        )


        # ========================================================
        # OPERACIÓN PRINCIPAL
        # ========================================================

        self.etiqueta_operacion = QLabel(
            "¿Qué quieres hacer?"
        )

        self.etiqueta_operacion.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                font-weight: 600;
            }
            """
        )

        self.distribucion_configuracion.addWidget(
            self.etiqueta_operacion
        )


        self.grupo_operacion = QButtonGroup(
            self
        )

        self.grupo_operacion.setExclusive(
            True
        )


        self.distribucion_operaciones = QHBoxLayout()

        self.distribucion_operaciones.setSpacing(
            10
        )


        self.opcion_cortar = OpcionRadioTarjeta(
            "Cortar documento",
            (
                "Divide el PDF en varias partes utilizando "
                "puntos de corte."
            ),
            "cortes",
            self
        )

        self.grupo_operacion.addButton(
            self.opcion_cortar.radio
        )

        self.distribucion_operaciones.addWidget(
            self.opcion_cortar,
            1
        )


        self.opcion_seleccionar_paginas = (
            OpcionRadioTarjeta(
                "Seleccionar páginas",
                (
                    "Extrae páginas concretas o separa "
                    "la selección del resto."
                ),
                "seleccion",
                self
            )
        )

        self.grupo_operacion.addButton(
            self.opcion_seleccionar_paginas.radio
        )

        self.distribucion_operaciones.addWidget(
            self.opcion_seleccionar_paginas,
            1
        )


        self.opcion_cortar.radio.setChecked(
            True
        )


        self.distribucion_configuracion.addLayout(
            self.distribucion_operaciones
        )


        # ========================================================
        # OPCIONES DE CORTE
        # ========================================================

        self.contenedor_opciones_corte = QFrame()

        self.contenedor_opciones_corte.setObjectName(
            "ContenedorOpciones"
        )


        self.distribucion_corte = QVBoxLayout(
            self.contenedor_opciones_corte
        )

        self.distribucion_corte.setContentsMargins(
            12,
            9,
            12,
            9
        )

        self.distribucion_corte.setSpacing(
            7
        )


        # ----------------------------------- #
        #              Título                 #
        # ----------------------------------- #

        self.etiqueta_modo_corte = QLabel(
            "¿Cómo quieres dividirlo?"
        )

        self.etiqueta_modo_corte.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                font-weight: 600;
            }
            """
        )

        self.distribucion_corte.addWidget(
            self.etiqueta_modo_corte
        )


        # ----------------------------------- #
        #        Modos en una sola fila       #
        # ----------------------------------- #

        self.fila_modos_corte = QHBoxLayout()

        self.fila_modos_corte.setSpacing(
            22
        )


        self.grupo_modo_corte = QButtonGroup(
            self
        )

        self.grupo_modo_corte.setExclusive(
            True
        )


        self.radio_corte_manual = QRadioButton(
            "Elegir cortes manualmente"
        )

        self.radio_corte_manual.setProperty(
            "valor",
            "manual"
        )

        self.radio_corte_manual.setStyleSheet(
            obtener_estilo_radio(
                tamano=20
            )
        )

        self.radio_corte_manual.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.grupo_modo_corte.addButton(
            self.radio_corte_manual
        )

        self.fila_modos_corte.addWidget(
            self.radio_corte_manual,
            1
        )


        self.radio_corte_paginas = QRadioButton(
            "Una página por archivo"
        )

        self.radio_corte_paginas.setProperty(
            "valor",
            "paginas"
        )

        self.radio_corte_paginas.setStyleSheet(
            obtener_estilo_radio(
                tamano=20
            )
        )

        self.radio_corte_paginas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.grupo_modo_corte.addButton(
            self.radio_corte_paginas
        )

        self.fila_modos_corte.addWidget(
            self.radio_corte_paginas,
            1
        )


        self.radio_corte_bloques = QRadioButton(
            "Dividir cada N páginas"
        )

        self.radio_corte_bloques.setProperty(
            "valor",
            "bloques"
        )

        self.radio_corte_bloques.setStyleSheet(
            obtener_estilo_radio(
                tamano=20
            )
        )

        self.radio_corte_bloques.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.grupo_modo_corte.addButton(
            self.radio_corte_bloques
        )

        self.fila_modos_corte.addWidget(
            self.radio_corte_bloques,
            1
        )


        self.distribucion_corte.addLayout(
            self.fila_modos_corte
        )


        # ----------------------------------- #
        #         Cantidad por bloque         #
        # ----------------------------------- #

        self.contenedor_cantidad_bloques = QWidget()


        self.fila_cantidad_bloques = QHBoxLayout(
            self.contenedor_cantidad_bloques
        )

        self.fila_cantidad_bloques.setContentsMargins(
            31,
            0,
            0,
            0
        )

        self.fila_cantidad_bloques.setSpacing(
            7
        )


        self.etiqueta_bloques = QLabel(
            "Cada:"
        )

        self.fila_cantidad_bloques.addWidget(
            self.etiqueta_bloques
        )


        self.selector_bloques = QSpinBox()

        self.selector_bloques.setRange(
            1,
            99999
        )

        self.selector_bloques.setValue(
            5
        )

        self.selector_bloques.setSuffix(
            " páginas"
        )

        self.selector_bloques.setMinimumHeight(
            30
        )

        self.selector_bloques.setMaximumWidth(
            150
        )

        self.fila_cantidad_bloques.addWidget(
            self.selector_bloques
        )

        self.fila_cantidad_bloques.addStretch(
            1
        )


        self.distribucion_corte.addWidget(
            self.contenedor_cantidad_bloques
        )


        self.radio_corte_manual.setChecked(
            True
        )


        self.distribucion_configuracion.addWidget(
            self.contenedor_opciones_corte
        )


        # ========================================================
        # OPCIONES DE SELECCIÓN
        # ========================================================

        self.contenedor_opciones_seleccion = QFrame()

        self.contenedor_opciones_seleccion.setObjectName(
            "ContenedorOpciones"
        )


        self.distribucion_seleccion = QVBoxLayout(
            self.contenedor_opciones_seleccion
        )

        self.distribucion_seleccion.setContentsMargins(
            12,
            9,
            12,
            9
        )

        self.distribucion_seleccion.setSpacing(
            9
        )


        # ----------------------------------- #
        #              Título                 #
        # ----------------------------------- #

        self.etiqueta_accion_seleccion = QLabel(
            "¿Qué quieres hacer con las páginas seleccionadas?"
        )

        self.etiqueta_accion_seleccion.setWordWrap(
            True
        )

        self.etiqueta_accion_seleccion.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                font-weight: 600;
            }
            """
        )

        self.distribucion_seleccion.addWidget(
            self.etiqueta_accion_seleccion
        )


        # ----------------------------------- #
        #       Opciones en una fila          #
        # ----------------------------------- #

        self.fila_radios_seleccion = QHBoxLayout()

        self.fila_radios_seleccion.setSpacing(
            22
        )


        self.grupo_accion_seleccion = QButtonGroup(
            self
        )

        self.grupo_accion_seleccion.setExclusive(
            True
        )


        self.radio_seleccion_unidas = QRadioButton(
            "Unirlas en un solo PDF"
        )

        self.radio_seleccion_unidas.setProperty(
            "valor",
            "unidas"
        )

        self.radio_seleccion_unidas.setStyleSheet(
            obtener_estilo_radio(
                tamano=20
            )
        )

        self.radio_seleccion_unidas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.grupo_accion_seleccion.addButton(
            self.radio_seleccion_unidas
        )

        self.fila_radios_seleccion.addWidget(
            self.radio_seleccion_unidas,
            1
        )


        self.radio_seleccion_individuales = QRadioButton(
            "Un PDF por página seleccionada"
        )

        self.radio_seleccion_individuales.setProperty(
            "valor",
            "individuales"
        )

        self.radio_seleccion_individuales.setStyleSheet(
            obtener_estilo_radio(
                tamano=20
            )
        )

        self.radio_seleccion_individuales.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.grupo_accion_seleccion.addButton(
            self.radio_seleccion_individuales
        )

        self.fila_radios_seleccion.addWidget(
            self.radio_seleccion_individuales,
            1
        )


        self.radio_seleccion_resto = QRadioButton(
            "Seleccionadas y resto en dos PDFs"
        )

        self.radio_seleccion_resto.setProperty(
            "valor",
            "seleccion_resto"
        )

        self.radio_seleccion_resto.setStyleSheet(
            obtener_estilo_radio(
                tamano=20
            )
        )

        self.radio_seleccion_resto.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.grupo_accion_seleccion.addButton(
            self.radio_seleccion_resto
        )

        self.fila_radios_seleccion.addWidget(
            self.radio_seleccion_resto,
            1
        )


        self.radio_seleccion_unidas.setChecked(
            True
        )


        self.distribucion_seleccion.addLayout(
            self.fila_radios_seleccion
        )


        # ----------------------------------- #
        #       Botones de selección          #
        # ----------------------------------- #

        self.fila_botones_seleccion = QHBoxLayout()

        self.fila_botones_seleccion.setSpacing(
            14
        )


        # ----------------------------------- #
        #        Espacio izquierdo            #
        # ----------------------------------- #

        self.fila_botones_seleccion.addStretch(
            1
        )


        # ----------------------------------- #
        #             Botones                 #
        # ----------------------------------- #

        self.boton_seleccionar_todas = QPushButton(
            "Seleccionar todas"
        )

        self.boton_deseleccionar = QPushButton(
            "Deseleccionar"
        )

        self.boton_invertir = QPushButton(
            "Invertir selección"
        )


        for boton in (
            self.boton_seleccionar_todas,
            self.boton_deseleccionar,
            self.boton_invertir
        ):

            boton.setMinimumSize(
                185,
                54
            )

            boton.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed
            )

            self.fila_botones_seleccion.addWidget(
                boton
            )


        # ----------------------------------- #
        #         Espacio derecho             #
        # ----------------------------------- #

        self.fila_botones_seleccion.addStretch(
            1
        )


        self.distribucion_seleccion.addLayout(
            self.fila_botones_seleccion
        )

        self.distribucion_configuracion.addWidget(
            self.contenedor_opciones_seleccion
        )


        # ----------------------------------- #
        #        Apariencia opciones          #
        # ----------------------------------- #

        estilo_contenedores = """
        QFrame#ContenedorOpciones {
            background-color: rgba(255, 255, 255, 5);
            border: 1px solid rgba(145, 145, 145, 55);
            border-radius: 9px;
        }
        """


        self.contenedor_opciones_corte.setStyleSheet(
            estilo_contenedores
        )

        self.contenedor_opciones_seleccion.setStyleSheet(
            estilo_contenedores
        )


        # ========================================================
        # CARPETA DE SALIDA
        # ========================================================

        self.distribucion_salida = QHBoxLayout()

        self.distribucion_salida.setSpacing(
            8
        )


        self.etiqueta_salida = QLabel(
            "Salida:"
        )

        self.distribucion_salida.addWidget(
            self.etiqueta_salida
        )


        self.campo_salida = QLineEdit()

        self.campo_salida.setReadOnly(
            True
        )

        self.campo_salida.setPlaceholderText(
            "Selecciona una carpeta de salida"
        )

        self.campo_salida.setMinimumWidth(
            0
        )

        self.distribucion_salida.addWidget(
            self.campo_salida,
            1
        )


        self.boton_salida = QPushButton(
            "Elegir carpeta"
        )

        self.boton_salida.setMinimumHeight(
            34
        )

        self.boton_salida.setMinimumWidth(
            120
        )

        self.distribucion_salida.addWidget(
            self.boton_salida
        )


        self.distribucion_configuracion.addLayout(
            self.distribucion_salida
        )


        # ========================================================
        # ÁREA DE PÁGINAS
        # ========================================================

        self.marco_paginas = MarcoPaginasAmpliable(
            self
        )

        self.marco_paginas.setObjectName(
            "MarcoPaginas"
        )

        self.marco_paginas.setMinimumHeight(
            120
        )

        self.marco_paginas.setStyleSheet(
            """
            QFrame#MarcoPaginas {
                background-color: rgba(255, 255, 255, 4);
                border: 1px solid rgba(128, 128, 128, 90);
                border-radius: 12px;
            }
            """
        )


        self.distribucion_marco_paginas = QVBoxLayout(
            self.marco_paginas
        )

        self.distribucion_marco_paginas.setContentsMargins(
            4,
            4,
            4,
            4
        )

        self.distribucion_marco_paginas.setSpacing(
            0
        )


        self.area_paginas = QScrollArea()

        self.area_paginas.setObjectName(
            "AreaPaginas"
        )

        self.area_paginas.setWidgetResizable(
            True
        )

        self.area_paginas.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.area_paginas.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.area_paginas.setStyleSheet(
            """
            QScrollArea#AreaPaginas {
                background: transparent;
                border: none;
            }

            QScrollArea#AreaPaginas > QWidget > QWidget {
                background: transparent;
            }
            """
        )

        self.area_paginas.viewport().setStyleSheet(
            "background: transparent;"
        )


        self.contenedor_paginas = ContenedorFlujo(
            margen=14,
            espacio=12
        )

        self.contenedor_paginas.setStyleSheet(
            "background: transparent;"
        )


        self.area_paginas.setWidget(
            self.contenedor_paginas
        )


        self.distribucion_marco_paginas.addWidget(
            self.area_paginas
        )


        self.distribucion.addWidget(
            self.marco_paginas,
            1
        )


        # ========================================================
        # INFORMACIÓN
        # ========================================================

        self.distribucion_informacion = QHBoxLayout()

        self.distribucion_informacion.setSpacing(
            8
        )


        self.etiqueta_resumen = QLabel(
            "Selecciona un PDF."
        )

        self.etiqueta_resumen.setWordWrap(
            True
        )

        self.distribucion_informacion.addWidget(
            self.etiqueta_resumen,
            1
        )


        self.etiqueta_estado = QLabel()

        self.etiqueta_estado.setWordWrap(
            True
        )

        self.etiqueta_estado.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.distribucion_informacion.addWidget(
            self.etiqueta_estado,
            1
        )


        self.distribucion.addLayout(
            self.distribucion_informacion
        )


        # ========================================================
        # PROGRESO
        # ========================================================

        self.barra_progreso = QProgressBar()

        self.barra_progreso.setVisible(
            False
        )

        self.distribucion.addWidget(
            self.barra_progreso
        )


        # ========================================================
        # ACCIONES
        # ========================================================

        self.distribucion_acciones = QHBoxLayout()

        self.distribucion_acciones.setSpacing(
            8
        )


        self.boton_cancelar = QPushButton(
            "Cancelar"
        )

        self.boton_cancelar.setMinimumHeight(
            46
        )

        self.boton_cancelar.setVisible(
            False
        )

        self.distribucion_acciones.addWidget(
            self.boton_cancelar
        )


        self.boton_procesar = QPushButton(
            "Dividir PDF"
        )

        self.boton_procesar.setMinimumHeight(
            46
        )

        self.boton_procesar.setStyleSheet(
            """
            QPushButton {
                font-size: 15px;
                font-weight: 600;
            }
            """
        )

        self.distribucion_acciones.addWidget(
            self.boton_procesar,
            1
        )


        self.distribucion.addLayout(
            self.distribucion_acciones
        )


    # ============================================================
    # CONECTAR EVENTOS
    # ============================================================
    def conectar_eventos(
        self
    ):

        self.boton_seleccionar.clicked.connect(
            self.seleccionar_pdf
        )

        self.boton_salida.clicked.connect(
            self.seleccionar_carpeta_salida
        )


        self.grupo_operacion.buttonToggled.connect(
            self.cambiar_operacion_radio
        )

        self.grupo_modo_corte.buttonToggled.connect(
            self.cambiar_modo_corte_radio
        )

        self.grupo_accion_seleccion.buttonToggled.connect(
            self.cambiar_accion_seleccion_radio
        )


        self.selector_bloques.valueChanged.connect(
            self.actualizar_cortes_visuales
        )


        self.boton_seleccionar_todas.clicked.connect(
            self.seleccionar_todas
        )

        self.boton_deseleccionar.clicked.connect(
            self.deseleccionar_todas
        )

        self.boton_invertir.clicked.connect(
            self.invertir_seleccion
        )


        self.boton_procesar.clicked.connect(
            self.iniciar_procesamiento
        )

        self.boton_cancelar.clicked.connect(
            self.cancelar_procesamiento
        )


        self.marco_paginas.ampliar_solicitado.connect(
            self.alternar_vista_paginas
        )


    # ============================================================
    # VISTA AMPLIADA DE PÁGINAS
    # ============================================================
    def alternar_vista_paginas(
        self
    ):

        if self.dialogo_paginas is None:

            self.abrir_vista_paginas()

        else:

            self.dialogo_paginas.close()


    # ============================================================
    # ABRIR VISTA AMPLIADA
    # ============================================================
    def abrir_vista_paginas(
        self
    ):

        if self.dialogo_paginas is not None:

            return


        # ----------------------------------- #
        #       Recordar posición original    #
        # ----------------------------------- #

        self.indice_marco_paginas = (
            self.distribucion.indexOf(
                self.marco_paginas
            )
        )


        # ----------------------------------- #
        #        Crear nueva ventana          #
        # ----------------------------------- #

        self.dialogo_paginas = QDialog(
            self.window()
        )

        self.dialogo_paginas.setWindowTitle(
            "Vista ampliada de páginas - Convertidor de Archivos"
        )

        self.dialogo_paginas.setWindowModality(
            Qt.WindowModality.ApplicationModal
        )

        self.dialogo_paginas.setMinimumSize(
            900,
            650
        )


        distribucion_dialogo = QVBoxLayout(
            self.dialogo_paginas
        )

        distribucion_dialogo.setContentsMargins(
            12,
            12,
            12,
            12
        )

        distribucion_dialogo.setSpacing(
            0
        )


        # ----------------------------------- #
        #       Mover el mismo cuadro         #
        # ----------------------------------- #

        self.distribucion.removeWidget(
            self.marco_paginas
        )

        self.marco_paginas.setParent(
            self.dialogo_paginas
        )

        distribucion_dialogo.addWidget(
            self.marco_paginas,
            1
        )


        self.marco_paginas.establecer_vista_ampliada(
            True
        )


        # ----------------------------------- #
        #        Restaurar al cerrar          #
        # ----------------------------------- #

        self.dialogo_paginas.finished.connect(
            self.restaurar_vista_paginas
        )


        self.dialogo_paginas.showMaximized()


    # ============================================================
    # RESTAURAR VISTA DE PÁGINAS
    # ============================================================
    def restaurar_vista_paginas(
        self,
        *args
    ):

        if self.dialogo_paginas is None:

            return


        dialogo = self.dialogo_paginas

        distribucion_dialogo = dialogo.layout()


        if distribucion_dialogo is not None:

            distribucion_dialogo.removeWidget(
                self.marco_paginas
            )


        self.marco_paginas.setParent(
            self
        )


        self.distribucion.insertWidget(
            self.indice_marco_paginas,
            self.marco_paginas,
            1
        )


        self.marco_paginas.establecer_vista_ampliada(
            False
        )


        self.contenedor_paginas.updateGeometry()

        self.marco_paginas.updateGeometry()


        self.dialogo_paginas = None

        dialogo.deleteLater()


    # ============================================================
    # OBTENER VALOR DE GRUPO
    # ============================================================
    def obtener_valor_grupo(
        self,
        grupo,
        valor_respaldo
    ):

        boton = grupo.checkedButton()


        if boton is None:

            return valor_respaldo


        valor = boton.property(
            "valor"
        )


        if not valor:

            return valor_respaldo


        return str(
            valor
        )


    # ============================================================
    # OBTENER OPERACIÓN
    # ============================================================
    def obtener_operacion(
        self
    ):

        return self.obtener_valor_grupo(
            self.grupo_operacion,
            "cortes"
        )


    # ============================================================
    # OBTENER MODO DE CORTE
    # ============================================================
    def obtener_modo_corte(
        self
    ):

        return self.obtener_valor_grupo(
            self.grupo_modo_corte,
            "manual"
        )


    # ============================================================
    # OBTENER ACCIÓN DE SELECCIÓN
    # ============================================================
    def obtener_accion_seleccion(
        self
    ):

        return self.obtener_valor_grupo(
            self.grupo_accion_seleccion,
            "unidas"
        )


    # ============================================================
    # EVENTOS DE RADIO
    # ============================================================
    def cambiar_operacion_radio(
        self,
        boton,
        marcado
    ):

        if marcado:

            self.actualizar_operacion()


    def cambiar_modo_corte_radio(
        self,
        boton,
        marcado
    ):

        if marcado:

            self.actualizar_opciones_corte()


    def cambiar_accion_seleccion_radio(
        self,
        boton,
        marcado
    ):

        if marcado:

            self.actualizar_seleccion_visual()


    # ============================================================
    # SELECCIONAR PDF
    # ============================================================
    def seleccionar_pdf(
        self
    ):

        ruta_pdf, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar PDF",
            "",
            "Archivos PDF (*.pdf)"
        )


        if not ruta_pdf:

            return


        self.ruta_pdf = os.path.abspath(
            os.path.normpath(
                ruta_pdf
            )
        )


        self.cortes_manuales.clear()

        self.paginas_seleccionadas.clear()

        self.ultima_pagina_seleccionada = None

        self.cantidad_paginas = 0

        self.tarjetas = []

        self.error_carga_actual = None


        self.campo_archivo.setText(
            self.ruta_pdf
        )


        carpeta_original = os.path.dirname(
            self.ruta_pdf
        )

        nombre_base = os.path.splitext(
            os.path.basename(
                self.ruta_pdf
            )
        )[
            0
        ]


        self.campo_salida.setText(
            os.path.join(
                carpeta_original,
                f"{nombre_base}_dividido"
            )
        )


        self.contenedor_paginas.limpiar()

        self.iniciar_carga_pdf()


    # ============================================================
    # CARGAR MINIATURAS
    # ============================================================
    def iniciar_carga_pdf(
        self
    ):

        if not self.ruta_pdf:

            return


        if self.hilo_carga is not None:

            return


        self.boton_seleccionar.setEnabled(
            False
        )

        self.boton_procesar.setEnabled(
            False
        )

        self.etiqueta_estado.setText(
            "Generando miniaturas..."
        )


        self.hilo_carga = QThread(
            self
        )

        self.trabajador_carga = (
            TrabajadorCargaDivisionPDF(
                self.ruta_pdf
            )
        )

        self.trabajador_carga.moveToThread(
            self.hilo_carga
        )


        self.hilo_carga.started.connect(
            self.trabajador_carga.ejecutar
        )

        self.trabajador_carga.cantidad_detectada.connect(
            self.establecer_cantidad_paginas
        )

        self.trabajador_carga.pagina_generada.connect(
            self.agregar_pagina
        )

        self.trabajador_carga.error.connect(
            self.registrar_error_carga
        )

        self.trabajador_carga.finalizado.connect(
            self.hilo_carga.quit
        )

        self.trabajador_carga.finalizado.connect(
            self.trabajador_carga.deleteLater
        )

        self.hilo_carga.finished.connect(
            self.finalizar_carga
        )

        self.hilo_carga.finished.connect(
            self.hilo_carga.deleteLater
        )


        self.hilo_carga.start()


    # ============================================================
    # ESTABLECER CANTIDAD DE PÁGINAS
    # ============================================================
    @Slot(
        int
    )
    def establecer_cantidad_paginas(
        self,
        cantidad
    ):

        self.cantidad_paginas = cantidad


        self.selector_bloques.setMaximum(
            max(
                1,
                cantidad
            )
        )


        self.actualizar_resumen()


    # ============================================================
    # AGREGAR PÁGINA
    # ============================================================
    @Slot(
        int,
        bytes
    )
    def agregar_pagina(
        self,
        indice_pagina,
        datos_imagen
    ):

        pixmap = QPixmap()


        if not pixmap.loadFromData(
            datos_imagen,
            "PNG"
        ):

            return


        tarjeta = TarjetaPaginaDivision(
            indice_pagina,
            self.cantidad_paginas,
            pixmap,
            self.contenedor_paginas
        )


        tarjeta.corte_cambiado.connect(
            self.cambiar_corte_manual
        )

        tarjeta.seleccion_cambiada.connect(
            self.cambiar_seleccion
        )

        tarjeta.rango_solicitado.connect(
            self.seleccionar_rango
        )


        self.tarjetas.append(
            tarjeta
        )


        self.contenedor_paginas.disposicion.addWidget(
            tarjeta
        )

        self.contenedor_paginas.updateGeometry()


        tarjeta.establecer_modo(
            self.obtener_operacion()
        )


        self.etiqueta_estado.setText(
            (
                f"Cargando página "
                f"{indice_pagina + 1} "
                f"de {self.cantidad_paginas}..."
            )
        )


        self.actualizar_visualizacion()


    # ============================================================
    # REGISTRAR ERROR DE CARGA
    # ============================================================
    @Slot(
        str
    )
    def registrar_error_carga(
        self,
        mensaje
    ):

        self.error_carga_actual = mensaje


    # ============================================================
    # FINALIZAR CARGA
    # ============================================================
    def finalizar_carga(
        self
    ):

        self.hilo_carga = None

        self.trabajador_carga = None


        if self.error_carga_actual:

            self.etiqueta_estado.setText(
                "No se pudo cargar el PDF."
            )

            QMessageBox.critical(
                self,
                "Dividir PDF",
                self.error_carga_actual
            )


        else:

            self.etiqueta_estado.setText(
                "Documento listo."
            )


        self.actualizar_visualizacion()

        self.actualizar_estado_controles()


    # ============================================================
    # CARPETA DE SALIDA
    # ============================================================
    def seleccionar_carpeta_salida(
        self
    ):

        carpeta_inicial = (
            self.campo_salida.text().strip()
        )


        if (
            carpeta_inicial
            and not os.path.isdir(
                carpeta_inicial
            )
        ):

            carpeta_inicial = os.path.dirname(
                carpeta_inicial
            )


        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de salida",
            carpeta_inicial
        )


        if not carpeta:

            return


        self.campo_salida.setText(
            carpeta
        )


        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR OPERACIÓN
    # ============================================================
    def actualizar_operacion(
        self
    ):

        operacion = self.obtener_operacion()

        es_cortes = (
            operacion == "cortes"
        )


        self.contenedor_opciones_corte.setVisible(
            es_cortes
        )

        self.contenedor_opciones_seleccion.setVisible(
            not es_cortes
        )


        if es_cortes:

            self.etiqueta_titulo.setText(
                "Dividir PDF"
            )

            self.etiqueta_descripcion.setText(
                "Divide el documento indicando puntos de corte "
                "o utilizando una división automática."
            )


        else:

            self.etiqueta_titulo.setText(
                "Seleccionar páginas"
            )

            self.etiqueta_descripcion.setText(
                "Selecciona las páginas que quieres extraer. "
                "Puedes unirlas en un PDF, guardarlas por separado "
                "o separar la selección del resto."
            )


        for tarjeta in self.tarjetas:

            tarjeta.establecer_modo(
                operacion
            )


        self.actualizar_opciones_corte()


    # ============================================================
    # ACTUALIZAR OPCIONES DE CORTE
    # ============================================================
    def actualizar_opciones_corte(
        self
    ):

        es_bloques = (
            self.obtener_operacion()
            == "cortes"
            and self.obtener_modo_corte()
            == "bloques"
        )


        self.contenedor_cantidad_bloques.setVisible(
            es_bloques
        )


        self.actualizar_visualizacion()


    # ============================================================
    # CAMBIAR CORTE
    # ============================================================
    @Slot(
        int,
        bool
    )
    def cambiar_corte_manual(
        self,
        numero_pagina,
        activo
    ):

        if activo:

            self.cortes_manuales.add(
                numero_pagina
            )

        else:

            self.cortes_manuales.discard(
                numero_pagina
            )


        self.actualizar_cortes_visuales()


    # ============================================================
    # OBTENER CORTES
    # ============================================================
    def obtener_cortes_actuales(
        self
    ):

        if self.cantidad_paginas <= 1:

            return []


        modo = self.obtener_modo_corte()


        if modo == "manual":

            return sorted(
                corte
                for corte in self.cortes_manuales
                if (
                    0
                    < corte
                    < self.cantidad_paginas
                )
            )


        if modo == "paginas":

            return list(
                range(
                    1,
                    self.cantidad_paginas
                )
            )


        if modo == "bloques":

            tamano = self.selector_bloques.value()

            return list(
                range(
                    tamano,
                    self.cantidad_paginas,
                    tamano
                )
            )


        return []


    # ============================================================
    # CAMBIAR SELECCIÓN
    # ============================================================
    @Slot(
        int,
        bool
    )
    def cambiar_seleccion(
        self,
        numero_pagina,
        seleccionada
    ):

        if seleccionada:

            self.paginas_seleccionadas.add(
                numero_pagina
            )

            self.ultima_pagina_seleccionada = (
                numero_pagina
            )

        else:

            self.paginas_seleccionadas.discard(
                numero_pagina
            )


        self.actualizar_seleccion_visual()


    # ============================================================
    # SELECCIONAR RANGO
    # ============================================================
    @Slot(
        int
    )
    def seleccionar_rango(
        self,
        numero_pagina
    ):

        if self.ultima_pagina_seleccionada is None:

            self.paginas_seleccionadas.add(
                numero_pagina
            )

            self.ultima_pagina_seleccionada = (
                numero_pagina
            )

        else:

            inicio = min(
                self.ultima_pagina_seleccionada,
                numero_pagina
            )

            fin = max(
                self.ultima_pagina_seleccionada,
                numero_pagina
            )


            for pagina in range(
                inicio,
                fin + 1
            ):

                self.paginas_seleccionadas.add(
                    pagina
                )


        self.actualizar_seleccion_visual()


    # ============================================================
    # SELECCIONAR TODAS
    # ============================================================
    def seleccionar_todas(
        self
    ):

        self.paginas_seleccionadas = set(
            range(
                1,
                self.cantidad_paginas + 1
            )
        )


        if self.cantidad_paginas > 0:

            self.ultima_pagina_seleccionada = (
                self.cantidad_paginas
            )


        self.actualizar_seleccion_visual()


    # ============================================================
    # DESELECCIONAR TODAS
    # ============================================================
    def deseleccionar_todas(
        self
    ):

        self.paginas_seleccionadas.clear()

        self.ultima_pagina_seleccionada = None

        self.actualizar_seleccion_visual()


    # ============================================================
    # INVERTIR SELECCIÓN
    # ============================================================
    def invertir_seleccion(
        self
    ):

        todas = set(
            range(
                1,
                self.cantidad_paginas + 1
            )
        )


        self.paginas_seleccionadas = (
            todas
            - self.paginas_seleccionadas
        )

        self.ultima_pagina_seleccionada = None

        self.actualizar_seleccion_visual()


    # ============================================================
    # ACTUALIZAR VISUALIZACIÓN
    # ============================================================
    def actualizar_visualizacion(
        self
    ):

        if self.obtener_operacion() == "cortes":

            self.actualizar_cortes_visuales()

        else:

            self.actualizar_seleccion_visual()


    # ============================================================
    # ACTUALIZAR CORTES VISUALES
    # ============================================================
    def actualizar_cortes_visuales(
        self
    ):

        cortes = set(
            self.obtener_cortes_actuales()
        )


        editable = (
            self.obtener_modo_corte()
            == "manual"
        )


        numero_parte = 1


        for tarjeta in self.tarjetas:

            tarjeta.establecer_modo(
                "cortes"
            )

            tarjeta.establecer_parte(
                numero_parte
            )


            corte_activo = (
                tarjeta.numero_pagina
                in cortes
            )


            tarjeta.establecer_corte(
                corte_activo,
                editable
            )


            if corte_activo:

                numero_parte += 1


        self.actualizar_resumen()

        self.actualizar_texto_boton()

        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR SELECCIÓN VISUAL
    # ============================================================
    def actualizar_seleccion_visual(
        self
    ):

        for tarjeta in self.tarjetas:

            tarjeta.establecer_modo(
                "seleccion"
            )

            tarjeta.establecer_seleccion(
                tarjeta.numero_pagina
                in self.paginas_seleccionadas
            )


        self.actualizar_resumen()

        self.actualizar_texto_boton()

        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR RESUMEN
    # ============================================================
    def actualizar_resumen(
        self
    ):

        if self.cantidad_paginas <= 0:

            self.etiqueta_resumen.setText(
                "Selecciona un PDF."
            )

            return


        if self.obtener_operacion() == "cortes":

            cantidad_salidas = (
                len(
                    self.obtener_cortes_actuales()
                )
                + 1
            )


            self.etiqueta_resumen.setText(
                (
                    f"{self.cantidad_paginas} páginas · "
                    f"{cantidad_salidas} archivos resultantes"
                )
            )


        else:

            cantidad_seleccionadas = len(
                self.paginas_seleccionadas
            )


            self.etiqueta_resumen.setText(
                (
                    f"{cantidad_seleccionadas} de "
                    f"{self.cantidad_paginas} "
                    f"páginas seleccionadas"
                )
            )


    # ============================================================
    # ACTUALIZAR TEXTO DE BOTÓN
    # ============================================================
    def actualizar_texto_boton(
        self
    ):

        if self.obtener_operacion() == "cortes":

            self.boton_procesar.setText(
                "Dividir PDF"
            )

            return


        accion = self.obtener_accion_seleccion()


        if accion == "unidas":

            self.boton_procesar.setText(
                "Crear PDF con seleccionadas"
            )

        elif accion == "individuales":

            self.boton_procesar.setText(
                "Extraer páginas"
            )

        else:

            self.boton_procesar.setText(
                "Separar selección y resto"
            )


    # ============================================================
    # CALCULAR CANTIDAD DE SALIDAS
    # ============================================================
    def calcular_cantidad_salidas(
        self
    ):

        if self.obtener_operacion() == "cortes":

            modo = self.obtener_modo_corte()


            if modo == "manual":

                return (
                    len(
                        self.obtener_cortes_actuales()
                    )
                    + 1
                )


            if modo == "paginas":

                return self.cantidad_paginas


            if modo == "bloques":

                if self.cantidad_paginas <= 0:

                    return 0


                return math.ceil(
                    self.cantidad_paginas
                    / self.selector_bloques.value()
                )


        cantidad = len(
            self.paginas_seleccionadas
        )


        if cantidad <= 0:

            return 0


        accion = self.obtener_accion_seleccion()


        if accion == "unidas":

            return 1


        if accion == "individuales":

            return cantidad


        if accion == "seleccion_resto":

            if cantidad >= self.cantidad_paginas:

                return 0

            return 2


        return 0


    # ============================================================
    # ACTUALIZAR ESTADO DE CONTROLES
    # ============================================================
    def actualizar_estado_controles(
        self
    ):

        cargando = (
            self.hilo_carga is not None
        )

        procesando = (
            self.hilo_division is not None
        )

        habilitados = (
            not cargando
            and not procesando
        )


        puede_procesar = (
            self.ruta_pdf is not None
            and self.cantidad_paginas > 0
            and bool(
                self.campo_salida.text().strip()
            )
            and self.calcular_cantidad_salidas() > 0
            and habilitados
        )


        if self.obtener_operacion() == "cortes":

            puede_procesar = (
                puede_procesar
                and self.calcular_cantidad_salidas() > 1
            )


        self.boton_procesar.setEnabled(
            puede_procesar
        )

        self.boton_seleccionar.setEnabled(
            habilitados
        )

        self.boton_salida.setEnabled(
            habilitados
        )


        for boton in self.grupo_operacion.buttons():

            boton.setEnabled(
                habilitados
            )


        for boton in self.grupo_modo_corte.buttons():

            boton.setEnabled(
                habilitados
            )


        self.selector_bloques.setEnabled(
            habilitados
            and self.obtener_operacion() == "cortes"
            and self.obtener_modo_corte() == "bloques"
        )


        for boton in self.grupo_accion_seleccion.buttons():

            boton.setEnabled(
                habilitados
            )


        self.boton_seleccionar_todas.setEnabled(
            habilitados
        )

        self.boton_deseleccionar.setEnabled(
            habilitados
        )

        self.boton_invertir.setEnabled(
            habilitados
        )


        self.actualizar_texto_boton()


    # ============================================================
    # INICIAR PROCESAMIENTO
    # ============================================================
    def iniciar_procesamiento(
        self
    ):

        if not self.ruta_pdf:

            return


        operacion = self.obtener_operacion()


        if operacion == "cortes":

            modo = self.obtener_modo_corte()

            cortes = self.obtener_cortes_actuales()

            paginas = []


        else:

            modo = self.obtener_accion_seleccion()

            cortes = []

            paginas = sorted(
                self.paginas_seleccionadas
            )


            if not paginas:

                QMessageBox.information(
                    self,
                    "Seleccionar páginas",
                    "Selecciona al menos una página."
                )

                return


            if (
                modo == "seleccion_resto"
                and len(
                    paginas
                ) >= self.cantidad_paginas
            ):

                QMessageBox.information(
                    self,
                    "Seleccionar páginas",
                    (
                        "Para separar la selección del resto "
                        "debe quedar al menos una página "
                        "sin seleccionar."
                    )
                )

                return


        cantidad_salidas = (
            self.calcular_cantidad_salidas()
        )


        self.barra_progreso.setVisible(
            True
        )

        self.barra_progreso.setRange(
            0,
            cantidad_salidas
        )

        self.barra_progreso.setValue(
            0
        )


        self.boton_cancelar.setVisible(
            True
        )

        self.etiqueta_estado.setText(
            "Procesando PDF..."
        )


        self.hilo_division = QThread(
            self
        )


        self.trabajador_division = (
            TrabajadorDivisionPDF(
                self.ruta_pdf,
                self.campo_salida.text().strip(),
                operacion,
                modo=modo,
                cortes=cortes,
                paginas=paginas,
                paginas_por_archivo=(
                    self.selector_bloques.value()
                )
            )
        )


        self.trabajador_division.moveToThread(
            self.hilo_division
        )


        self.hilo_division.started.connect(
            self.trabajador_division.ejecutar
        )

        self.trabajador_division.progreso.connect(
            self.actualizar_progreso
        )

        self.trabajador_division.completado.connect(
            self.procesamiento_completado
        )

        self.trabajador_division.cancelado.connect(
            self.procesamiento_cancelado
        )

        self.trabajador_division.error.connect(
            self.error_procesamiento
        )

        self.trabajador_division.finalizado.connect(
            self.hilo_division.quit
        )

        self.trabajador_division.finalizado.connect(
            self.trabajador_division.deleteLater
        )

        self.hilo_division.finished.connect(
            self.finalizar_procesamiento
        )

        self.hilo_division.finished.connect(
            self.hilo_division.deleteLater
        )


        self.actualizar_estado_controles()

        self.hilo_division.start()


    # ============================================================
    # ACTUALIZAR PROGRESO
    # ============================================================
    @Slot(
        int,
        int
    )
    def actualizar_progreso(
        self,
        actual,
        total
    ):

        self.barra_progreso.setMaximum(
            total
        )

        self.barra_progreso.setValue(
            actual
        )

        self.etiqueta_estado.setText(
            (
                f"Creando archivo "
                f"{actual} de {total}..."
            )
        )


    # ============================================================
    # PROCESAMIENTO COMPLETADO
    # ============================================================
    @Slot(
        list
    )
    def procesamiento_completado(
        self,
        resultados
    ):

        cantidad = len(
            resultados
        )

        self.etiqueta_estado.setText(
            "Operación completada."
        )

        QMessageBox.information(
            self,
            "PDF",
            (
                "La operación terminó correctamente.\n\n"
                f"Archivos creados: {cantidad}\n"
                f"Carpeta:\n{self.campo_salida.text()}"
            )
        )


    # ============================================================
    # PROCESAMIENTO CANCELADO
    # ============================================================
    @Slot()
    def procesamiento_cancelado(
        self
    ):

        self.etiqueta_estado.setText(
            "Operación cancelada."
        )


    # ============================================================
    # ERROR DE PROCESAMIENTO
    # ============================================================
    @Slot(
        str
    )
    def error_procesamiento(
        self,
        mensaje
    ):

        self.etiqueta_estado.setText(
            "No se pudo completar la operación."
        )

        QMessageBox.critical(
            self,
            "PDF",
            mensaje
        )


    # ============================================================
    # CANCELAR
    # ============================================================
    def cancelar_procesamiento(
        self
    ):

        if self.trabajador_division is None:

            return


        self.boton_cancelar.setEnabled(
            False
        )

        self.etiqueta_estado.setText(
            "Cancelando..."
        )

        self.trabajador_division.cancelar()


    # ============================================================
    # FINALIZAR
    # ============================================================
    def finalizar_procesamiento(
        self
    ):

        self.hilo_division = None

        self.trabajador_division = None


        self.boton_cancelar.setVisible(
            False
        )

        self.boton_cancelar.setEnabled(
            True
        )


        self.actualizar_estado_controles()