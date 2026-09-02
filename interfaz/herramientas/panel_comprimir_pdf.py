import os

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QObject,
    QThread
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QFrame,
    QProgressBar,
    QRadioButton,
    QButtonGroup,
    QSizePolicy
)

from herramientas.pdf.comprimir_pdf import (
    comprimir_pdf
)

from funciones.configuracion_app import (
    obtener_ruta_recurso
)


# ================================================================
# ESTILO DE RADIO BUTTON
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
# FORMATEAR TAMAÑO
# ================================================================
def formatear_tamano(
    cantidad_bytes
):

    cantidad = float(
        cantidad_bytes
    )

    unidades = [
        "B",
        "KB",
        "MB",
        "GB"
    ]


    for unidad in unidades:

        if (
            cantidad < 1024
            or unidad == unidades[-1]
        ):

            if unidad == "B":

                return (
                    f"{int(cantidad)} {unidad}"
                )

            return (
                f"{cantidad:.2f} {unidad}"
            )

        cantidad /= 1024


    return (
        f"{cantidad_bytes} B"
    )


# ================================================================
# TRABAJADOR DE COMPRESIÓN
# ================================================================
class TrabajadorComprimirPDF(
    QObject
):

    progreso = Signal(
        int,
        str
    )

    terminado = Signal(
        object
    )

    cancelado = Signal()

    error = Signal(
        str
    )


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        ruta_pdf,
        ruta_salida,
        nivel
    ):

        super().__init__()

        self.ruta_pdf = ruta_pdf
        self.ruta_salida = ruta_salida
        self.nivel = nivel

        self.cancelacion_solicitada = False


    # ============================================================
    # CANCELAR
    # ============================================================
    @Slot()
    def cancelar(
        self
    ):

        self.cancelacion_solicitada = True


    # ============================================================
    # COMPROBAR CANCELACIÓN
    # ============================================================
    def comprobar_cancelacion(
        self
    ):

        return self.cancelacion_solicitada


    # ============================================================
    # EJECUTAR
    # ============================================================
    @Slot()
    def ejecutar(
        self
    ):

        try:

            resultado = comprimir_pdf(
                self.ruta_pdf,
                self.ruta_salida,
                nivel=self.nivel,
                progreso=self.progreso.emit,
                comprobar_cancelacion=(
                    self.comprobar_cancelacion
                )
            )


            if (
                self.cancelacion_solicitada
                or resultado is None
            ):

                self.cancelado.emit()

                return


            self.terminado.emit(
                resultado
            )


        except Exception as error:

            self.error.emit(
                str(
                    error
                )
            )


# ================================================================
# PANEL COMPRIMIR PDF
# ================================================================
class PanelComprimirPDF(
    QWidget
):

    # ============================================================
    # DIMENSIONES DE LA VENTANA
    # ============================================================

    ANCHO_INICIAL = 850
    ALTO_INICIAL = 580

    ANCHO_MINIMO = 850
    ALTO_MINIMO = 580


    # ============================================================
    # DIMENSIONES DE LA GUÍA ADAPTATIVA
    # ============================================================

    ANCHO_MINIMO_GUIA = 1000
    ALTO_MINIMO_GUIA = 700


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

        self.ruta_pdf = None

        self.procesando = False

        self.hilo_compresion = None
        self.trabajador_compresion = None

        self.crear_interfaz()

        self.conectar_eventos()

        self.actualizar_estado_controles()

        self.actualizar_visibilidad_guia()


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
            24,
            20,
            24,
            22
        )

        self.distribucion.setSpacing(
            14
        )


        # ----------------------------------- #
        #               Título                #
        # ----------------------------------- #

        self.etiqueta_titulo = QLabel(
            "Comprimir PDF"
        )

        self.etiqueta_titulo.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: 700;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_titulo
        )


        # ----------------------------------- #
        #            Descripción              #
        # ----------------------------------- #

        self.etiqueta_descripcion = QLabel(
            "Reduce el tamaño de un PDF optimizando su estructura "
            "y, si lo deseas, comprimiendo las imágenes que contiene."
        )

        self.etiqueta_descripcion.setWordWrap(
            True
        )

        self.etiqueta_descripcion.setStyleSheet(
            """
            QLabel {
                color: #8590a5;
                font-size: 13px;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_descripcion
        )


        # ========================================================
        # ARCHIVO DE ENTRADA
        # ========================================================

        fila_archivo = QHBoxLayout()

        fila_archivo.setSpacing(
            10
        )


        self.campo_pdf = QLineEdit()

        self.campo_pdf.setReadOnly(
            True
        )

        self.campo_pdf.setPlaceholderText(
            "Selecciona un archivo PDF"
        )

        self.campo_pdf.setMinimumHeight(
            38
        )


        self.boton_seleccionar = QPushButton(
            "Seleccionar PDF"
        )

        self.boton_seleccionar.setMinimumSize(
            150,
            38
        )


        fila_archivo.addWidget(
            self.campo_pdf,
            1
        )

        fila_archivo.addWidget(
            self.boton_seleccionar
        )


        self.distribucion.addLayout(
            fila_archivo
        )


        # ----------------------------------- #
        #         Información original        #
        # ----------------------------------- #

        self.etiqueta_original = QLabel(
            "Tamaño original: —"
        )

        self.etiqueta_original.setStyleSheet(
            """
            QLabel {
                color: #aeb6c4;
                font-size: 13px;
                font-weight: 600;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_original
        )


        # ========================================================
        # NIVEL DE COMPRESIÓN
        # ========================================================

        self.marco_niveles = QFrame()

        self.marco_niveles.setStyleSheet(
            """
            QFrame {
                border: 1px solid rgba(128, 128, 128, 90);
                border-radius: 10px;
            }

            QLabel {
                border: none;
            }

            QRadioButton {
                border: none;
            }
            """
        )


        distribucion_niveles = QVBoxLayout(
            self.marco_niveles
        )

        distribucion_niveles.setContentsMargins(
            18,
            15,
            18,
            16
        )

        distribucion_niveles.setSpacing(
            12
        )


        etiqueta_nivel = QLabel(
            "Nivel de compresión"
        )

        etiqueta_nivel.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                font-weight: 600;
            }
            """
        )

        distribucion_niveles.addWidget(
            etiqueta_nivel
        )


        # ----------------------------------- #
        #             Radios                  #
        # ----------------------------------- #

        fila_niveles = QHBoxLayout()

        fila_niveles.setSpacing(
            20
        )


        self.grupo_niveles = QButtonGroup(
            self
        )


        # ----------------------------------- #
        #          Sin pérdida                #
        # ----------------------------------- #

        self.radio_sin_perdida = QRadioButton(
            "Sin pérdida"
        )

        self.radio_sin_perdida.setStyleSheet(
            obtener_estilo_radio(
                20,
                True
            )
        )

        self.radio_sin_perdida.setToolTip(
            "Optimiza la estructura del PDF sin reducir "
            "la calidad de sus imágenes."
        )


        # ----------------------------------- #
        #          Equilibrada                #
        # ----------------------------------- #

        self.radio_equilibrada = QRadioButton(
            "Equilibrada"
        )

        self.radio_equilibrada.setStyleSheet(
            obtener_estilo_radio(
                20,
                True
            )
        )

        self.radio_equilibrada.setToolTip(
            "Reduce también la calidad de las imágenes "
            "de forma moderada."
        )

        self.radio_equilibrada.setChecked(
            True
        )


        # ----------------------------------- #
        #             Fuerte                  #
        # ----------------------------------- #

        self.radio_fuerte = QRadioButton(
            "Fuerte"
        )

        self.radio_fuerte.setStyleSheet(
            obtener_estilo_radio(
                20,
                True
            )
        )

        self.radio_fuerte.setToolTip(
            "Busca una reducción mayor mediante una "
            "compresión más agresiva de las imágenes."
        )


        self.grupo_niveles.addButton(
            self.radio_sin_perdida
        )

        self.grupo_niveles.addButton(
            self.radio_equilibrada
        )

        self.grupo_niveles.addButton(
            self.radio_fuerte
        )


        fila_niveles.addStretch(
            1
        )

        fila_niveles.addWidget(
            self.radio_sin_perdida
        )

        fila_niveles.addSpacing(
            28
        )

        fila_niveles.addWidget(
            self.radio_equilibrada
        )

        fila_niveles.addSpacing(
            28
        )

        fila_niveles.addWidget(
            self.radio_fuerte
        )

        fila_niveles.addStretch(
            1
        )


        distribucion_niveles.addLayout(
            fila_niveles
        )


        # ----------------------------------- #
        #          Explicación                #
        # ----------------------------------- #

        self.etiqueta_detalle_nivel = QLabel()

        self.etiqueta_detalle_nivel.setWordWrap(
            True
        )

        self.etiqueta_detalle_nivel.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_detalle_nivel.setStyleSheet(
            """
            QLabel {
                color: #8590a5;
                font-size: 12px;
            }
            """
        )

        distribucion_niveles.addWidget(
            self.etiqueta_detalle_nivel
        )


        self.distribucion.addWidget(
            self.marco_niveles
        )


        # ========================================================
        # INFORMACIÓN
        # ========================================================

        self.etiqueta_aviso = QLabel(
            "La compresión mantiene las páginas, texto y contenido "
            "vectorial. Los niveles Equilibrada y Fuerte pueden "
            "reducir la calidad de las imágenes. "
            "Modificar un PDF firmado digitalmente puede invalidar "
            "su firma."
        )

        self.etiqueta_aviso.setWordWrap(
            True
        )

        self.etiqueta_aviso.setStyleSheet(
            """
            QLabel {
                color: #8590a5;
                font-size: 12px;
                padding: 4px 2px;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_aviso
        )


        # ========================================================
        # SALIDA
        # ========================================================

        fila_salida = QHBoxLayout()

        fila_salida.setSpacing(
            10
        )


        self.campo_salida = QLineEdit()

        self.campo_salida.setReadOnly(
            True
        )

        self.campo_salida.setPlaceholderText(
            "Archivo PDF de salida"
        )

        self.campo_salida.setMinimumHeight(
            38
        )


        self.boton_salida = QPushButton(
            "Elegir salida"
        )

        self.boton_salida.setMinimumSize(
            150,
            38
        )


        fila_salida.addWidget(
            self.campo_salida,
            1
        )

        fila_salida.addWidget(
            self.boton_salida
        )


        self.distribucion.addLayout(
            fila_salida
        )


        # ========================================================
        # RESULTADO
        # ========================================================

        self.etiqueta_resultado = QLabel()

        self.etiqueta_resultado.setWordWrap(
            True
        )

        self.etiqueta_resultado.setVisible(
            False
        )

        self.etiqueta_resultado.setStyleSheet(
            """
            QLabel {
                border: 1px solid rgba(100, 170, 255, 110);
                border-radius: 8px;
                padding: 10px 12px;
                color: #d9e9ff;
                background-color: rgba(50, 100, 170, 35);
                font-size: 13px;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_resultado
        )


        # ========================================================
        # ESPACIO ADAPTATIVO
        # ========================================================

        self.contenedor_adaptativo = QFrame()

        self.contenedor_adaptativo.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )


        distribucion_adaptativa = QVBoxLayout(
            self.contenedor_adaptativo
        )

        distribucion_adaptativa.setContentsMargins(
            6,
            4,
            6,
            4
        )

        distribucion_adaptativa.setSpacing(
            0
        )


        distribucion_adaptativa.addStretch(
            1
        )


        # ----------------------------------- #
        #          Guía adaptativa            #
        # ----------------------------------- #

        self.marco_guia = QFrame()

        self.marco_guia.setMaximumWidth(
            1100
        )

        self.marco_guia.setStyleSheet(
            """
            QFrame {
                border: 1px solid rgba(128, 128, 128, 65);
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 4);
            }

            QLabel {
                border: none;
                background: transparent;
            }
            """
        )


        distribucion_guia = QVBoxLayout(
            self.marco_guia
        )

        distribucion_guia.setContentsMargins(
            18,
            14,
            18,
            14
        )

        distribucion_guia.setSpacing(
            9
        )


        # ----------------------------------- #
        #         Título de la guía           #
        # ----------------------------------- #

        self.etiqueta_titulo_guia = QLabel(
            "Guía rápida de compresión"
        )

        self.etiqueta_titulo_guia.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_titulo_guia.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                font-weight: 600;
            }
            """
        )

        distribucion_guia.addWidget(
            self.etiqueta_titulo_guia
        )


        self.etiqueta_nivel_guia = QLabel()

        self.etiqueta_nivel_guia.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_nivel_guia.setStyleSheet(
            """
            QLabel {
                color: #8590a5;
                font-size: 12px;
            }
            """
        )

        distribucion_guia.addWidget(
            self.etiqueta_nivel_guia
        )


        # ----------------------------------- #
        #             Tarjetas                #
        # ----------------------------------- #

        fila_tarjetas = QHBoxLayout()

        fila_tarjetas.setSpacing(
            12
        )


        self.tarjeta_sin_perdida = (
            self.crear_tarjeta_guia(
                "Sin pérdida",
                (
                    "Conserva la calidad visual. Ideal para "
                    "documentos, formularios y PDFs donde la "
                    "fidelidad es más importante que el tamaño."
                )
            )
        )


        self.tarjeta_equilibrada = (
            self.crear_tarjeta_guia(
                "Equilibrada",
                (
                    "Recomendada para uso general. Reduce el peso "
                    "de las imágenes manteniendo una buena relación "
                    "entre calidad y tamaño."
                )
            )
        )


        self.tarjeta_fuerte = (
            self.crear_tarjeta_guia(
                "Fuerte",
                (
                    "Busca el menor tamaño posible. Es útil para "
                    "PDFs pesados con muchas imágenes cuando el "
                    "tamaño final es la prioridad."
                )
            )
        )


        fila_tarjetas.addWidget(
            self.tarjeta_sin_perdida,
            1
        )

        fila_tarjetas.addWidget(
            self.tarjeta_equilibrada,
            1
        )

        fila_tarjetas.addWidget(
            self.tarjeta_fuerte,
            1
        )


        distribucion_guia.addLayout(
            fila_tarjetas
        )


        distribucion_adaptativa.addWidget(
            self.marco_guia,
            0,
            Qt.AlignmentFlag.AlignHCenter
        )


        distribucion_adaptativa.addStretch(
            1
        )


        self.distribucion.addWidget(
            self.contenedor_adaptativo,
            1
        )


        # ========================================================
        # ESTADO Y PROGRESO
        # ========================================================

        self.etiqueta_estado = QLabel(
            "Selecciona un PDF para comenzar."
        )

        self.etiqueta_estado.setStyleSheet(
            """
            QLabel {
                color: #8590a5;
                font-size: 12px;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_estado
        )


        self.barra_progreso = QProgressBar()

        self.barra_progreso.setRange(
            0,
            100
        )

        self.barra_progreso.setValue(
            0
        )

        self.barra_progreso.setVisible(
            False
        )

        self.distribucion.addWidget(
            self.barra_progreso
        )


        # ========================================================
        # ACCIONES
        # ========================================================

        fila_acciones = QHBoxLayout()

        fila_acciones.addStretch(
            1
        )


        self.boton_cancelar = QPushButton(
            "Cancelar"
        )

        self.boton_cancelar.setMinimumSize(
            130,
            44
        )

        self.boton_cancelar.setVisible(
            False
        )


        self.boton_comprimir = QPushButton(
            "Comprimir PDF"
        )

        self.boton_comprimir.setMinimumSize(
            200,
            44
        )

        self.boton_comprimir.setStyleSheet(
            """
            QPushButton {
                background-color: #2d7ff9;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #1f6fe5;
            }

            QPushButton:pressed {
                background-color: #185fc6;
            }

            QPushButton:disabled {
                background-color: #566071;
                color: #b7bdc8;
            }
            """
        )


        fila_acciones.addWidget(
            self.boton_cancelar
        )

        fila_acciones.addWidget(
            self.boton_comprimir
        )


        self.distribucion.addLayout(
            fila_acciones
        )


        self.marco_guia.setVisible(
            False
        )


        self.actualizar_descripcion_nivel()


    # ============================================================
    # CREAR TARJETA DE GUÍA
    # ============================================================
    def crear_tarjeta_guia(
        self,
        titulo,
        descripcion
    ):

        tarjeta = QFrame()

        tarjeta.setMinimumHeight(
            88
        )


        distribucion = QVBoxLayout(
            tarjeta
        )

        distribucion.setContentsMargins(
            14,
            10,
            14,
            10
        )

        distribucion.setSpacing(
            5
        )


        etiqueta_titulo = QLabel(
            titulo
        )

        etiqueta_titulo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        etiqueta_titulo.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                font-weight: 600;
            }
            """
        )


        etiqueta_descripcion = QLabel(
            descripcion
        )

        etiqueta_descripcion.setWordWrap(
            True
        )

        etiqueta_descripcion.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        etiqueta_descripcion.setStyleSheet(
            """
            QLabel {
                color: #8590a5;
                font-size: 11px;
            }
            """
        )


        distribucion.addWidget(
            etiqueta_titulo
        )

        distribucion.addWidget(
            etiqueta_descripcion,
            1
        )


        return tarjeta


    # ============================================================
    # ESTILO DE TARJETA
    # ============================================================
    def establecer_tarjeta_seleccionada(
        self,
        tarjeta,
        seleccionada
    ):

        if seleccionada:

            tarjeta.setStyleSheet(
                """
                QFrame {
                    border: 1px solid rgba(45, 127, 249, 210);
                    border-radius: 8px;
                    background-color: rgba(45, 127, 249, 24);
                }

                QLabel {
                    border: none;
                    background: transparent;
                }
                """
            )

        else:

            tarjeta.setStyleSheet(
                """
                QFrame {
                    border: 1px solid rgba(128, 128, 128, 65);
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 4);
                }

                QLabel {
                    border: none;
                    background: transparent;
                }
                """
            )


    # ============================================================
    # ACTUALIZAR GUÍA DE NIVEL
    # ============================================================
    def actualizar_guia_nivel(
        self
    ):

        if not hasattr(
            self,
            "etiqueta_nivel_guia"
        ):

            return


        nivel = self.obtener_nivel()


        if nivel == "sin_perdida":

            nombre = "Sin pérdida"

        elif nivel == "fuerte":

            nombre = "Fuerte"

        else:

            nombre = "Equilibrada"


        self.etiqueta_nivel_guia.setText(
            f"Nivel seleccionado: {nombre}"
        )


        self.establecer_tarjeta_seleccionada(
            self.tarjeta_sin_perdida,
            nivel == "sin_perdida"
        )

        self.establecer_tarjeta_seleccionada(
            self.tarjeta_equilibrada,
            nivel == "equilibrada"
        )

        self.establecer_tarjeta_seleccionada(
            self.tarjeta_fuerte,
            nivel == "fuerte"
        )


    # ============================================================
    # ACTUALIZAR VISIBILIDAD DE LA GUÍA
    # ============================================================
    def actualizar_visibilidad_guia(
        self
    ):

        if not hasattr(
            self,
            "marco_guia"
        ):

            return


        mostrar = (
            self.width()
            >= self.ANCHO_MINIMO_GUIA
            and self.height()
            >= self.ALTO_MINIMO_GUIA
        )


        self.marco_guia.setVisible(
            mostrar
        )


        if mostrar:

            self.actualizar_guia_nivel()


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

        self.actualizar_visibilidad_guia()


    # ============================================================
    # MOSTRAR PANEL
    # ============================================================
    def showEvent(
        self,
        evento
    ):

        super().showEvent(
            evento
        )

        self.actualizar_visibilidad_guia()


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
            self.seleccionar_salida
        )

        self.boton_comprimir.clicked.connect(
            self.iniciar_compresion
        )

        self.boton_cancelar.clicked.connect(
            self.cancelar_compresion
        )


        self.radio_sin_perdida.toggled.connect(
            self.actualizar_descripcion_nivel
        )

        self.radio_equilibrada.toggled.connect(
            self.actualizar_descripcion_nivel
        )

        self.radio_fuerte.toggled.connect(
            self.actualizar_descripcion_nivel
        )


    # ============================================================
    # ACTUALIZAR DESCRIPCIÓN DEL NIVEL
    # ============================================================
    @Slot()
    def actualizar_descripcion_nivel(
        self
    ):

        if self.radio_sin_perdida.isChecked():

            texto = (
                "Optimiza streams, objetos duplicados y contenido "
                "no utilizado sin modificar la calidad visual."
            )

        elif self.radio_fuerte.isChecked():

            texto = (
                "Busca reducir más el archivo recomprimiendo las "
                "imágenes con mayor intensidad y reduciendo las "
                "que tengan una resolución excesiva."
            )

        else:

            texto = (
                "Recomprime las imágenes de forma moderada para "
                "conseguir un buen equilibrio entre calidad y tamaño."
            )


        self.etiqueta_detalle_nivel.setText(
            texto
        )


        self.actualizar_guia_nivel()


    # ============================================================
    # OBTENER NIVEL
    # ============================================================
    def obtener_nivel(
        self
    ):

        if self.radio_sin_perdida.isChecked():

            return "sin_perdida"

        if self.radio_fuerte.isChecked():

            return "fuerte"

        return "equilibrada"


    # ============================================================
    # SELECCIONAR PDF
    # ============================================================
    @Slot()
    def seleccionar_pdf(
        self
    ):

        if self.procesando:

            return


        ruta_pdf, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar PDF",
            "",
            "Archivos PDF (*.pdf)"
        )


        if not ruta_pdf:

            return


        ruta_pdf = os.path.abspath(
            ruta_pdf
        )


        self.ruta_pdf = ruta_pdf


        self.campo_pdf.setText(
            ruta_pdf
        )


        tamano = os.path.getsize(
            ruta_pdf
        )


        self.etiqueta_original.setText(
            (
                "Tamaño original: "
                f"{formatear_tamano(tamano)}"
            )
        )


        self.asignar_salida_predeterminada()


        self.etiqueta_resultado.setVisible(
            False
        )


        self.etiqueta_estado.setText(
            "Listo para comprimir."
        )


        self.actualizar_estado_controles()


    # ============================================================
    # ASIGNAR SALIDA PREDETERMINADA
    # ============================================================
    def asignar_salida_predeterminada(
        self
    ):

        if not self.ruta_pdf:

            self.campo_salida.clear()

            return


        carpeta = os.path.dirname(
            self.ruta_pdf
        )


        nombre = os.path.splitext(
            os.path.basename(
                self.ruta_pdf
            )
        )[0]


        ruta_salida = os.path.join(
            carpeta,
            f"{nombre}_comprimido.pdf"
        )


        self.campo_salida.setText(
            ruta_salida
        )


    # ============================================================
    # SELECCIONAR SALIDA
    # ============================================================
    @Slot()
    def seleccionar_salida(
        self
    ):

        if (
            self.procesando
            or not self.ruta_pdf
        ):

            return


        ruta_inicial = (
            self.campo_salida.text().strip()
        )


        ruta_salida, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF comprimido",
            ruta_inicial,
            "Archivos PDF (*.pdf)"
        )


        if not ruta_salida:

            return


        if not ruta_salida.lower().endswith(
            ".pdf"
        ):

            ruta_salida += ".pdf"


        self.campo_salida.setText(
            os.path.abspath(
                ruta_salida
            )
        )


        self.actualizar_estado_controles()


    # ============================================================
    # INICIAR COMPRESIÓN
    # ============================================================
    @Slot()
    def iniciar_compresion(
        self
    ):

        if self.procesando:

            return


        if not self.ruta_pdf:

            QMessageBox.warning(
                self,
                "Falta el PDF",
                "Selecciona un archivo PDF."
            )

            return


        ruta_salida = (
            self.campo_salida.text().strip()
        )


        if not ruta_salida:

            QMessageBox.warning(
                self,
                "Falta la salida",
                "Elige dónde guardar el PDF comprimido."
            )

            return


        if not ruta_salida.lower().endswith(
            ".pdf"
        ):

            ruta_salida += ".pdf"

            self.campo_salida.setText(
                ruta_salida
            )


        ruta_salida = os.path.abspath(
            ruta_salida
        )


        # ----------------------------------- #
        #       Evitar reemplazar original    #
        # ----------------------------------- #

        if (
            os.path.normcase(
                ruta_salida
            )
            == os.path.normcase(
                self.ruta_pdf
            )
        ):

            QMessageBox.warning(
                self,
                "Ruta no válida",
                (
                    "El archivo comprimido debe guardarse "
                    "con una ruta diferente al PDF original."
                )
            )

            return


        # ----------------------------------- #
        #        Confirmar sobrescritura      #
        # ----------------------------------- #

        if os.path.isfile(
            ruta_salida
        ):

            respuesta = QMessageBox.question(
                self,
                "El archivo ya existe",
                (
                    "Ya existe un archivo con ese nombre.\n\n"
                    "¿Quieres reemplazarlo?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No
            )


            if (
                respuesta
                != QMessageBox.StandardButton.Yes
            ):

                return


        self.ejecutar_compresion(
            ruta_salida
        )


    # ============================================================
    # EJECUTAR COMPRESIÓN
    # ============================================================
    def ejecutar_compresion(
        self,
        ruta_salida
    ):

        self.procesando = True


        self.etiqueta_resultado.setVisible(
            False
        )


        self.barra_progreso.setValue(
            0
        )

        self.barra_progreso.setVisible(
            True
        )


        self.etiqueta_estado.setText(
            "Preparando compresión..."
        )


        self.actualizar_estado_controles()


        # ----------------------------------- #
        #               Hilo                  #
        # ----------------------------------- #

        hilo = QThread(
            self
        )


        trabajador = TrabajadorComprimirPDF(
            self.ruta_pdf,
            ruta_salida,
            self.obtener_nivel()
        )


        trabajador.moveToThread(
            hilo
        )


        hilo.started.connect(
            trabajador.ejecutar
        )


        trabajador.progreso.connect(
            self.actualizar_progreso
        )

        trabajador.terminado.connect(
            self.compresion_terminada
        )

        trabajador.cancelado.connect(
            self.compresion_cancelada
        )

        trabajador.error.connect(
            self.error_compresion
        )


        trabajador.terminado.connect(
            hilo.quit
        )

        trabajador.cancelado.connect(
            hilo.quit
        )

        trabajador.error.connect(
            hilo.quit
        )


        hilo.finished.connect(
            trabajador.deleteLater
        )

        hilo.finished.connect(
            hilo.deleteLater
        )

        hilo.finished.connect(
            self.limpiar_hilo
        )


        self.hilo_compresion = hilo

        self.trabajador_compresion = trabajador


        hilo.start()


    # ============================================================
    # ACTUALIZAR PROGRESO
    # ============================================================
    @Slot(
        int,
        str
    )
    def actualizar_progreso(
        self,
        porcentaje,
        mensaje
    ):

        self.barra_progreso.setValue(
            porcentaje
        )

        self.etiqueta_estado.setText(
            mensaje
        )


    # ============================================================
    # COMPRESIÓN TERMINADA
    # ============================================================
    @Slot(
        object
    )
    def compresion_terminada(
        self,
        resultado
    ):

        self.procesando = False


        self.barra_progreso.setValue(
            100
        )

        self.barra_progreso.setVisible(
            False
        )


        tamano_original = resultado[
            "tamano_original"
        ]

        tamano_final = resultado[
            "tamano_final"
        ]

        reduccion = resultado[
            "porcentaje_reduccion"
        ]


        if resultado[
            "se_conservo_original"
        ]:

            texto_resultado = (
                "El PDF ya estaba suficientemente optimizado y "
                "el proceso no consiguió producir un archivo más "
                "pequeño. Se conservó el tamaño original.\n\n"
                f"{formatear_tamano(tamano_original)} → "
                f"{formatear_tamano(tamano_final)}"
            )

            self.etiqueta_estado.setText(
                "El PDF ya estaba optimizado."
            )

        else:

            texto_resultado = (
                f"{formatear_tamano(tamano_original)} → "
                f"{formatear_tamano(tamano_final)}"
                f"  ·  {reduccion:.1f} % menos"
            )

            self.etiqueta_estado.setText(
                "PDF comprimido correctamente."
            )


        self.etiqueta_resultado.setText(
            texto_resultado
        )

        self.etiqueta_resultado.setVisible(
            True
        )


        self.actualizar_estado_controles()


        mensaje = (
            "El PDF se procesó correctamente.\n\n"
            f"Tamaño original: "
            f"{formatear_tamano(tamano_original)}\n"
            f"Tamaño final: "
            f"{formatear_tamano(tamano_final)}\n"
            f"Reducción: {reduccion:.1f} %\n\n"
            f"{resultado['ruta_salida']}"
        )


        QMessageBox.information(
            self,
            "Comprimir PDF",
            mensaje
        )


    # ============================================================
    # COMPRESIÓN CANCELADA
    # ============================================================
    @Slot()
    def compresion_cancelada(
        self
    ):

        self.procesando = False


        self.barra_progreso.setVisible(
            False
        )


        self.etiqueta_estado.setText(
            "Compresión cancelada."
        )


        self.actualizar_estado_controles()


    # ============================================================
    # ERROR DE COMPRESIÓN
    # ============================================================
    @Slot(
        str
    )
    def error_compresion(
        self,
        mensaje
    ):

        self.procesando = False


        self.barra_progreso.setVisible(
            False
        )


        self.etiqueta_estado.setText(
            "No se pudo comprimir el PDF."
        )


        self.actualizar_estado_controles()


        QMessageBox.critical(
            self,
            "No se pudo comprimir el PDF",
            mensaje
        )


    # ============================================================
    # CANCELAR COMPRESIÓN
    # ============================================================
    @Slot()
    def cancelar_compresion(
        self
    ):

        if (
            self.procesando
            and self.trabajador_compresion is not None
        ):

            self.trabajador_compresion.cancelar()

            self.etiqueta_estado.setText(
                "Cancelando..."
            )


    # ============================================================
    # LIMPIAR HILO
    # ============================================================
    @Slot()
    def limpiar_hilo(
        self
    ):

        self.hilo_compresion = None

        self.trabajador_compresion = None


    # ============================================================
    # ACTUALIZAR ESTADO DE CONTROLES
    # ============================================================
    def actualizar_estado_controles(
        self
    ):

        hay_pdf = bool(
            self.ruta_pdf
        )

        hay_salida = bool(
            self.campo_salida.text().strip()
        )


        self.boton_seleccionar.setEnabled(
            not self.procesando
        )

        self.boton_salida.setEnabled(
            not self.procesando
            and hay_pdf
        )


        self.radio_sin_perdida.setEnabled(
            not self.procesando
        )

        self.radio_equilibrada.setEnabled(
            not self.procesando
        )

        self.radio_fuerte.setEnabled(
            not self.procesando
        )


        self.boton_comprimir.setEnabled(
            not self.procesando
            and hay_pdf
            and hay_salida
        )


        self.boton_cancelar.setVisible(
            self.procesando
        )