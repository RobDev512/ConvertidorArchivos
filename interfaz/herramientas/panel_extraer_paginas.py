import os

from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
    Slot,
    QObject,
    QThread
)

from PySide6.QtGui import (
    QIcon,
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
    QLineEdit,
    QFrame,
    QProgressBar,
    QSizePolicy,
    QRadioButton,
    QButtonGroup,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QDialog,
    QComboBox,
    QSpinBox,
    QStackedWidget
)

from conversiones.previsualizacion import (
    obtener_cantidad_paginas_pdf,
    renderizar_pagina_pdf
)

from herramientas.pdf.exportar_paginas import (
    exportar_paginas_como_imagenes,
    exportar_paginas_como_texto
)

from funciones.configuracion_app import (
    obtener_ruta_recurso
)


# ----------------------------------- #
#      Tamaños de las miniaturas      #
# ----------------------------------- #

ANCHO_ICONO_PAGINA = 150
ALTO_ICONO_PAGINA = 190

ANCHO_TARJETA_PAGINA = 180
ALTO_TARJETA_PAGINA = 238


# ================================================================
# ESTILO DE RADIO BUTTONS
# ================================================================
def obtener_estilo_radio(
    tamano=20
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


    return f"""
    QRadioButton {{
        spacing: 8px;
        padding: 3px;
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
# LISTA DE PÁGINAS
# ================================================================
class ListaPaginasExtraer(QListWidget):

    seleccion_paginas_cambiada = Signal()


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


        self.setViewMode(
            QListWidget.ViewMode.IconMode
        )

        self.setMovement(
            QListWidget.Movement.Static
        )

        self.setResizeMode(
            QListWidget.ResizeMode.Adjust
        )

        self.setWrapping(
            True
        )

        self.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.setIconSize(
            QSize(
                ANCHO_ICONO_PAGINA,
                ALTO_ICONO_PAGINA
            )
        )

        self.setGridSize(
            QSize(
                ANCHO_TARJETA_PAGINA,
                ALTO_TARJETA_PAGINA
            )
        )

        self.setSpacing(
            6
        )

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        self.setUniformItemSizes(
            True
        )


        self.setStyleSheet(
            """
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 8px;
            }

            QListWidget::item {
                background-color: rgba(255, 255, 255, 7);
                border: 1px solid rgba(145, 145, 145, 65);
                border-radius: 10px;
                padding: 8px;
            }

            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 13);
                border: 1px solid rgba(100, 170, 255, 125);
            }

            QListWidget::item:selected {
                background-color: rgba(80, 160, 255, 28);
                border: 2px solid rgba(80, 160, 255, 220);
            }

            QListWidget::item:selected:!active {
                background-color: rgba(80, 160, 255, 24);
                border: 2px solid rgba(80, 160, 255, 190);
            }
            """
        )


        self.itemSelectionChanged.connect(
            self.seleccion_paginas_cambiada.emit
        )


    # ============================================================
    # AGREGAR PÁGINA
    # ============================================================
    def agregar_pagina(
        self,
        numero_pagina,
        pixmap
    ):

        pixmap_escalado = pixmap.scaled(
            ANCHO_ICONO_PAGINA,
            ALTO_ICONO_PAGINA,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )


        elemento = QListWidgetItem(
            QIcon(
                pixmap_escalado
            ),
            f"Página {numero_pagina}"
        )


        elemento.setData(
            Qt.ItemDataRole.UserRole,
            numero_pagina
        )

        elemento.setTextAlignment(
            Qt.AlignmentFlag.AlignHCenter
            | Qt.AlignmentFlag.AlignTop
        )

        elemento.setSizeHint(
            QSize(
                ANCHO_TARJETA_PAGINA,
                ALTO_TARJETA_PAGINA
            )
        )


        self.addItem(
            elemento
        )


    # ============================================================
    # OBTENER PÁGINAS SELECCIONADAS
    # ============================================================
    def obtener_paginas_seleccionadas(
        self
    ):

        paginas = []


        for elemento in self.selectedItems():

            pagina = elemento.data(
                Qt.ItemDataRole.UserRole
            )


            if pagina is not None:

                paginas.append(
                    int(
                        pagina
                    )
                )


        paginas.sort()


        return paginas


    # ============================================================
    # INVERTIR SELECCIÓN
    # ============================================================
    def invertir_seleccion(
        self
    ):

        self.blockSignals(
            True
        )


        for indice in range(
            self.count()
        ):

            elemento = self.item(
                indice
            )

            elemento.setSelected(
                not elemento.isSelected()
            )


        self.blockSignals(
            False
        )


        self.seleccion_paginas_cambiada.emit()


# ================================================================
# MARCO DE PÁGINAS AMPLIABLE
# ================================================================
class MarcoPaginasExtraer(QFrame):

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


        self.setObjectName(
            "MarcoPaginasExtraer"
        )


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
    # CAMBIAR VISTA
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


        x = (
            self.width()
            - self.boton_ampliar.width()
            - 14
        )


        self.boton_ampliar.move(
            max(
                8,
                x
            ),
            10
        )

        self.boton_ampliar.raise_()


# ================================================================
# TRABAJADOR DE MINIATURAS
# ================================================================
class TrabajadorMiniaturasExtraer(QObject):

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

                datos = renderizar_pagina_pdf(
                    self.ruta_pdf,
                    indice_pagina
                )


                self.pagina_generada.emit(
                    indice_pagina,
                    datos
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
# TRABAJADOR DE EXPORTACIÓN
# ================================================================
class TrabajadorExportacionPaginas(QObject):

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
        paginas,
        carpeta_salida,
        tipo,
        formato_imagen="JPG",
        calidad=90,
        txt_unico=True
    ):

        super().__init__()


        self.ruta_pdf = ruta_pdf

        self.paginas = paginas

        self.carpeta_salida = carpeta_salida

        self.tipo = tipo

        self.formato_imagen = formato_imagen

        self.calidad = calidad

        self.txt_unico = txt_unico


        self.cancelacion_solicitada = False


    # ============================================================
    # CANCELAR
    # ============================================================
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
    # INFORMAR PROGRESO
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

            if self.tipo == "imagenes":

                resultados = exportar_paginas_como_imagenes(
                    self.ruta_pdf,
                    self.paginas,
                    self.carpeta_salida,
                    formato=self.formato_imagen,
                    calidad=self.calidad,
                    progreso=self.informar_progreso,
                    comprobar_cancelacion=(
                        self.comprobar_cancelacion
                    )
                )


            elif self.tipo == "texto":

                resultados = exportar_paginas_como_texto(
                    self.ruta_pdf,
                    self.paginas,
                    self.carpeta_salida,
                    un_solo_archivo=self.txt_unico,
                    progreso=self.informar_progreso,
                    comprobar_cancelacion=(
                        self.comprobar_cancelacion
                    )
                )


            else:

                raise ValueError(
                    "El tipo de extracción no es válido."
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
# PANEL EXTRAER PÁGINAS
# ================================================================
class PanelExtraerPaginas(QWidget):

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


        # ----------------------------------- #
        #              Hilos                  #
        # ----------------------------------- #

        self.hilo_carga = None

        self.trabajador_carga = None

        self.error_carga_actual = None


        self.hilo_exportacion = None

        self.trabajador_exportacion = None


        # ----------------------------------- #
        #        Vista de páginas grande      #
        # ----------------------------------- #

        self.dialogo_paginas = None

        self.indice_marco_paginas = 0


        self.crear_interfaz()

        self.conectar_eventos()

        self.actualizar_tipo_extraccion()

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
        # TÍTULO
        # ========================================================

        self.etiqueta_titulo = QLabel(
            "Extraer páginas"
        )

        self.etiqueta_titulo.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: 600;
            }
            """
        )


        self.distribucion.addWidget(
            self.etiqueta_titulo
        )


        self.etiqueta_descripcion = QLabel(
            (
                "Selecciona páginas concretas de un PDF "
                "y expórtalas como imágenes o texto."
            )
        )

        self.etiqueta_descripcion.setWordWrap(
            True
        )


        self.distribucion.addWidget(
            self.etiqueta_descripcion
        )


        # ========================================================
        # ARCHIVO PDF
        # ========================================================

        self.fila_archivo = QHBoxLayout()

        self.fila_archivo.setSpacing(
            8
        )


        self.etiqueta_archivo = QLabel(
            "PDF:"
        )

        self.fila_archivo.addWidget(
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


        self.fila_archivo.addWidget(
            self.campo_archivo,
            1
        )


        self.boton_seleccionar_pdf = QPushButton(
            "Seleccionar PDF"
        )

        self.boton_seleccionar_pdf.setMinimumHeight(
            34
        )

        self.boton_seleccionar_pdf.setMinimumWidth(
            120
        )


        self.fila_archivo.addWidget(
            self.boton_seleccionar_pdf
        )


        self.distribucion.addLayout(
            self.fila_archivo
        )


        # ========================================================
        # TIPO DE EXTRACCIÓN
        # ========================================================

        self.contenedor_tipo = QFrame()

        self.contenedor_tipo.setObjectName(
            "ContenedorTipoExtraer"
        )


        self.contenedor_tipo.setStyleSheet(
            """
            QFrame#ContenedorTipoExtraer {
                background-color: rgba(255, 255, 255, 5);
                border: 1px solid rgba(145, 145, 145, 55);
                border-radius: 9px;
            }
            """
        )


        self.distribucion_tipo = QVBoxLayout(
            self.contenedor_tipo
        )

        self.distribucion_tipo.setContentsMargins(
            12,
            9,
            12,
            9
        )

        self.distribucion_tipo.setSpacing(
            7
        )


        self.etiqueta_tipo = QLabel(
            "¿Qué quieres extraer?"
        )

        self.etiqueta_tipo.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                font-weight: 600;
            }
            """
        )


        self.distribucion_tipo.addWidget(
            self.etiqueta_tipo
        )


        self.grupo_tipo = QButtonGroup(
            self
        )

        self.grupo_tipo.setExclusive(
            True
        )


        self.fila_tipo = QHBoxLayout()

        self.fila_tipo.setSpacing(
            24
        )


        self.radio_imagenes = QRadioButton(
            "Páginas como imágenes"
        )

        self.radio_imagenes.setProperty(
            "valor",
            "imagenes"
        )

        self.radio_imagenes.setStyleSheet(
            obtener_estilo_radio(
                20
            )
        )

        self.radio_imagenes.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )


        self.grupo_tipo.addButton(
            self.radio_imagenes
        )

        self.fila_tipo.addWidget(
            self.radio_imagenes,
            1
        )


        self.radio_texto = QRadioButton(
            "Texto de las páginas"
        )

        self.radio_texto.setProperty(
            "valor",
            "texto"
        )

        self.radio_texto.setStyleSheet(
            obtener_estilo_radio(
                20
            )
        )

        self.radio_texto.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )


        self.grupo_tipo.addButton(
            self.radio_texto
        )

        self.fila_tipo.addWidget(
            self.radio_texto,
            1
        )


        self.radio_imagenes.setChecked(
            True
        )


        self.distribucion_tipo.addLayout(
            self.fila_tipo
        )


        # ========================================================
        # OPCIONES SEGÚN TIPO
        # ========================================================

        self.pila_opciones = QStackedWidget()


        # ========================================================
        # OPCIONES DE IMAGEN
        # ========================================================

        self.panel_opciones_imagen = QWidget()


        self.fila_opciones_imagen = QHBoxLayout(
            self.panel_opciones_imagen
        )

        self.fila_opciones_imagen.setContentsMargins(
            0,
            4,
            0,
            0
        )

        self.fila_opciones_imagen.setSpacing(
            10
        )


        self.etiqueta_formato = QLabel(
            "Formato:"
        )

        self.fila_opciones_imagen.addWidget(
            self.etiqueta_formato
        )


        self.combo_formato = QComboBox()

        self.combo_formato.addItems(
            [
                "JPG",
                "PNG",
                "WebP"
            ]
        )

        self.combo_formato.setMinimumWidth(
            120
        )

        self.combo_formato.setMinimumHeight(
            32
        )


        self.fila_opciones_imagen.addWidget(
            self.combo_formato
        )


        self.fila_opciones_imagen.addSpacing(
            18
        )


        self.etiqueta_calidad = QLabel(
            "Calidad:"
        )

        self.fila_opciones_imagen.addWidget(
            self.etiqueta_calidad
        )


        self.selector_calidad = QSpinBox()

        self.selector_calidad.setRange(
            1,
            100
        )

        self.selector_calidad.setValue(
            90
        )

        self.selector_calidad.setSuffix(
            " %"
        )

        self.selector_calidad.setMinimumHeight(
            32
        )

        self.selector_calidad.setMinimumWidth(
            100
        )


        self.fila_opciones_imagen.addWidget(
            self.selector_calidad
        )


        self.fila_opciones_imagen.addStretch(
            1
        )


        self.pila_opciones.addWidget(
            self.panel_opciones_imagen
        )


        # ========================================================
        # OPCIONES DE TEXTO
        # ========================================================

        self.panel_opciones_texto = QWidget()


        self.distribucion_opciones_texto = QVBoxLayout(
            self.panel_opciones_texto
        )

        self.distribucion_opciones_texto.setContentsMargins(
            0,
            4,
            0,
            0
        )

        self.distribucion_opciones_texto.setSpacing(
            5
        )


        self.grupo_texto = QButtonGroup(
            self
        )

        self.grupo_texto.setExclusive(
            True
        )


        self.fila_modo_texto = QHBoxLayout()

        self.fila_modo_texto.setSpacing(
            24
        )


        self.radio_txt_unico = QRadioButton(
            "Un solo archivo TXT"
        )

        self.radio_txt_unico.setProperty(
            "valor",
            "unico"
        )

        self.radio_txt_unico.setStyleSheet(
            obtener_estilo_radio(
                18
            )
        )

        self.grupo_texto.addButton(
            self.radio_txt_unico
        )

        self.fila_modo_texto.addWidget(
            self.radio_txt_unico
        )


        self.radio_txt_individual = QRadioButton(
            "Un TXT por página"
        )

        self.radio_txt_individual.setProperty(
            "valor",
            "individual"
        )

        self.radio_txt_individual.setStyleSheet(
            obtener_estilo_radio(
                18
            )
        )

        self.grupo_texto.addButton(
            self.radio_txt_individual
        )

        self.fila_modo_texto.addWidget(
            self.radio_txt_individual
        )


        self.fila_modo_texto.addStretch(
            1
        )


        self.radio_txt_unico.setChecked(
            True
        )


        self.distribucion_opciones_texto.addLayout(
            self.fila_modo_texto
        )


        self.etiqueta_aviso_texto = QLabel(
            (
                "Nota: solo se puede extraer texto que exista "
                "realmente dentro del PDF. Una página escaneada "
                "como imagen puede no contener texto extraíble."
            )
        )

        self.etiqueta_aviso_texto.setWordWrap(
            True
        )

        self.etiqueta_aviso_texto.setStyleSheet(
            """
            QLabel {
                color: #9e9e9e;
                font-size: 11px;
            }
            """
        )


        self.distribucion_opciones_texto.addWidget(
            self.etiqueta_aviso_texto
        )


        self.pila_opciones.addWidget(
            self.panel_opciones_texto
        )


        self.distribucion_tipo.addWidget(
            self.pila_opciones
        )


        self.distribucion.addWidget(
            self.contenedor_tipo
        )


        # ========================================================
        # CONTROLES DE SELECCIÓN
        # ========================================================

        self.fila_seleccion = QHBoxLayout()

        self.fila_seleccion.setSpacing(
            10
        )


        self.etiqueta_paginas = QLabel(
            "Páginas:"
        )

        self.etiqueta_paginas.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                font-weight: 600;
            }
            """
        )


        self.fila_seleccion.addWidget(
            self.etiqueta_paginas
        )


        self.fila_seleccion.addStretch(
            1
        )


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

            boton.setMinimumHeight(
                34
            )

            boton.setMinimumWidth(
                145
            )


            self.fila_seleccion.addWidget(
                boton
            )


        self.fila_seleccion.addStretch(
            1
        )


        self.distribucion.addLayout(
            self.fila_seleccion
        )


        # ========================================================
        # ÁREA DE PÁGINAS
        # ========================================================

        self.marco_paginas = MarcoPaginasExtraer(
            self
        )

        self.marco_paginas.setMinimumHeight(
            170
        )


        self.marco_paginas.setStyleSheet(
            """
            QFrame#MarcoPaginasExtraer {
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


        self.lista_paginas = ListaPaginasExtraer(
            self.marco_paginas
        )


        self.distribucion_marco_paginas.addWidget(
            self.lista_paginas
        )


        self.distribucion.addWidget(
            self.marco_paginas,
            1
        )


        # ========================================================
        # SALIDA
        # ========================================================

        self.fila_salida = QHBoxLayout()

        self.fila_salida.setSpacing(
            8
        )


        self.etiqueta_salida = QLabel(
            "Salida:"
        )

        self.fila_salida.addWidget(
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


        self.fila_salida.addWidget(
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


        self.fila_salida.addWidget(
            self.boton_salida
        )


        self.distribucion.addLayout(
            self.fila_salida
        )


        # ========================================================
        # INFORMACIÓN
        # ========================================================

        self.fila_informacion = QHBoxLayout()

        self.fila_informacion.setSpacing(
            8
        )


        self.etiqueta_resumen = QLabel(
            "Selecciona un PDF."
        )

        self.etiqueta_resumen.setWordWrap(
            True
        )


        self.fila_informacion.addWidget(
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


        self.fila_informacion.addWidget(
            self.etiqueta_estado,
            1
        )


        self.distribucion.addLayout(
            self.fila_informacion
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

        self.fila_acciones = QHBoxLayout()

        self.fila_acciones.setSpacing(
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


        self.fila_acciones.addWidget(
            self.boton_cancelar
        )


        self.boton_extraer = QPushButton(
            "Extraer páginas como JPG"
        )

        self.boton_extraer.setMinimumHeight(
            46
        )

        self.boton_extraer.setStyleSheet(
            """
            QPushButton {
                font-size: 15px;
                font-weight: 600;
            }
            """
        )


        self.fila_acciones.addWidget(
            self.boton_extraer,
            1
        )


        self.distribucion.addLayout(
            self.fila_acciones
        )


    # ============================================================
    # CONECTAR EVENTOS
    # ============================================================
    def conectar_eventos(
        self
    ):

        self.boton_seleccionar_pdf.clicked.connect(
            self.seleccionar_pdf
        )

        self.boton_salida.clicked.connect(
            self.seleccionar_carpeta_salida
        )


        self.grupo_tipo.buttonToggled.connect(
            self.cambiar_tipo_radio
        )

        self.grupo_texto.buttonToggled.connect(
            self.cambiar_opcion_texto
        )

        self.combo_formato.currentTextChanged.connect(
            self.actualizar_opciones_imagen
        )


        self.lista_paginas.seleccion_paginas_cambiada.connect(
            self.actualizar_resumen
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


        self.marco_paginas.ampliar_solicitado.connect(
            self.alternar_vista_paginas
        )


        self.boton_extraer.clicked.connect(
            self.iniciar_exportacion
        )

        self.boton_cancelar.clicked.connect(
            self.cancelar_exportacion
        )


    # ============================================================
    # OBTENER TIPO DE EXTRACCIÓN
    # ============================================================
    def obtener_tipo_extraccion(
        self
    ):

        boton = self.grupo_tipo.checkedButton()


        if boton is None:

            return "imagenes"


        valor = boton.property(
            "valor"
        )


        return str(
            valor or "imagenes"
        )


    # ============================================================
    # OBTENER MODO TXT
    # ============================================================
    def obtener_txt_unico(
        self
    ):

        return self.radio_txt_unico.isChecked()


    # ============================================================
    # CAMBIAR TIPO
    # ============================================================
    def cambiar_tipo_radio(
        self,
        boton,
        marcado
    ):

        if marcado:

            self.actualizar_tipo_extraccion()


    # ============================================================
    # CAMBIAR OPCIÓN TXT
    # ============================================================
    def cambiar_opcion_texto(
        self,
        boton,
        marcado
    ):

        if marcado:

            self.actualizar_texto_boton()


    # ============================================================
    # ACTUALIZAR TIPO
    # ============================================================
    def actualizar_tipo_extraccion(
        self
    ):

        tipo = self.obtener_tipo_extraccion()


        if tipo == "imagenes":

            self.pila_opciones.setCurrentWidget(
                self.panel_opciones_imagen
            )


        else:

            self.pila_opciones.setCurrentWidget(
                self.panel_opciones_texto
            )


        self.actualizar_opciones_imagen()

        self.actualizar_texto_boton()

        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR OPCIONES DE IMAGEN
    # ============================================================
    def actualizar_opciones_imagen(
        self,
        *args
    ):

        formato = (
            self.combo_formato.currentText().upper()
        )


        permite_calidad = (
            formato in (
                "JPG",
                "WEBP"
            )
        )


        self.etiqueta_calidad.setEnabled(
            permite_calidad
        )

        self.selector_calidad.setEnabled(
            permite_calidad
        )


        self.actualizar_texto_boton()


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


        self.cantidad_paginas = 0

        self.error_carga_actual = None


        self.lista_paginas.clear()


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
        )[0]


        self.campo_salida.setText(
            os.path.join(
                carpeta_original,
                f"{nombre_base}_paginas_extraidas"
            )
        )


        self.iniciar_carga_pdf()


    # ============================================================
    # INICIAR CARGA
    # ============================================================
    def iniciar_carga_pdf(
        self
    ):

        if not self.ruta_pdf:

            return


        if self.hilo_carga is not None:

            return


        self.etiqueta_estado.setText(
            "Generando miniaturas..."
        )


        self.hilo_carga = QThread(
            self
        )


        self.trabajador_carga = (
            TrabajadorMiniaturasExtraer(
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


        self.actualizar_estado_controles()

        self.hilo_carga.start()


    # ============================================================
    # CANTIDAD DE PÁGINAS
    # ============================================================
    @Slot(
        int
    )
    def establecer_cantidad_paginas(
        self,
        cantidad
    ):

        self.cantidad_paginas = cantidad

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
        datos
    ):

        pixmap = QPixmap()


        if not pixmap.loadFromData(
            datos,
            "PNG"
        ):

            return


        numero_pagina = (
            indice_pagina
            + 1
        )


        self.lista_paginas.agregar_pagina(
            numero_pagina,
            pixmap
        )


        self.etiqueta_estado.setText(
            (
                f"Cargando página "
                f"{numero_pagina} de "
                f"{self.cantidad_paginas}..."
            )
        )


    # ============================================================
    # ERROR DE CARGA
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
                "Extraer páginas",
                self.error_carga_actual
            )


        else:

            self.etiqueta_estado.setText(
                "Documento listo."
            )


        self.actualizar_resumen()


    # ============================================================
    # SELECCIONAR SALIDA
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
    # SELECCIONAR TODAS
    # ============================================================
    def seleccionar_todas(
        self
    ):

        self.lista_paginas.selectAll()

        self.actualizar_resumen()


    # ============================================================
    # DESELECCIONAR TODAS
    # ============================================================
    def deseleccionar_todas(
        self
    ):

        self.lista_paginas.clearSelection()

        self.actualizar_resumen()


    # ============================================================
    # INVERTIR SELECCIÓN
    # ============================================================
    def invertir_seleccion(
        self
    ):

        self.lista_paginas.invertir_seleccion()


    # ============================================================
    # VISTA AMPLIADA
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


        self.indice_marco_paginas = (
            self.distribucion.indexOf(
                self.marco_paginas
            )
        )


        self.dialogo_paginas = QDialog(
            self.window()
        )

        self.dialogo_paginas.setWindowTitle(
            (
                "Vista ampliada de páginas - "
                "Convertidor de Archivos"
            )
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


        self.dialogo_paginas.finished.connect(
            self.restaurar_vista_paginas
        )


        self.dialogo_paginas.showMaximized()


    # ============================================================
    # RESTAURAR VISTA
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


        self.marco_paginas.updateGeometry()


        self.dialogo_paginas = None


        dialogo.deleteLater()


    # ============================================================
    # ACTUALIZAR RESUMEN
    # ============================================================
    def actualizar_resumen(
        self
    ):

        paginas = (
            self.lista_paginas.obtener_paginas_seleccionadas()
        )

        seleccionadas = len(
            paginas
        )


        if self.cantidad_paginas <= 0:

            self.etiqueta_resumen.setText(
                "Selecciona un PDF."
            )


        else:

            self.etiqueta_resumen.setText(
                (
                    f"{seleccionadas} de "
                    f"{self.cantidad_paginas} "
                    f"páginas seleccionadas"
                )
            )


        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR TEXTO DEL BOTÓN
    # ============================================================
    def actualizar_texto_boton(
        self
    ):

        tipo = self.obtener_tipo_extraccion()


        if tipo == "imagenes":

            formato = self.combo_formato.currentText()

            self.boton_extraer.setText(
                f"Extraer páginas como {formato}"
            )


        elif self.obtener_txt_unico():

            self.boton_extraer.setText(
                "Extraer texto a TXT"
            )


        else:

            self.boton_extraer.setText(
                "Extraer un TXT por página"
            )


    # ============================================================
    # ACTUALIZAR CONTROLES
    # ============================================================
    def actualizar_estado_controles(
        self
    ):

        cargando = (
            self.hilo_carga is not None
        )

        procesando = (
            self.hilo_exportacion is not None
        )


        habilitados = (
            not cargando
            and not procesando
        )


        paginas = (
            self.lista_paginas.obtener_paginas_seleccionadas()
        )


        puede_extraer = (
            self.ruta_pdf is not None
            and self.cantidad_paginas > 0
            and len(
                paginas
            ) > 0
            and bool(
                self.campo_salida.text().strip()
            )
            and habilitados
        )


        self.boton_extraer.setEnabled(
            puede_extraer
        )


        self.boton_seleccionar_pdf.setEnabled(
            habilitados
        )

        self.boton_salida.setEnabled(
            habilitados
        )


        self.lista_paginas.setEnabled(
            habilitados
        )


        hay_paginas = (
            self.cantidad_paginas > 0
        )


        self.boton_seleccionar_todas.setEnabled(
            habilitados
            and hay_paginas
        )

        self.boton_deseleccionar.setEnabled(
            habilitados
            and hay_paginas
        )

        self.boton_invertir.setEnabled(
            habilitados
            and hay_paginas
        )


        for boton in self.grupo_tipo.buttons():

            boton.setEnabled(
                habilitados
            )


        for boton in self.grupo_texto.buttons():

            boton.setEnabled(
                habilitados
            )


        self.combo_formato.setEnabled(
            habilitados
        )


        if habilitados:

            self.actualizar_opciones_imagen()


        else:

            self.selector_calidad.setEnabled(
                False
            )


        self.actualizar_texto_boton()


    # ============================================================
    # INICIAR EXPORTACIÓN
    # ============================================================
    def iniciar_exportacion(
        self
    ):

        if not self.ruta_pdf:

            return


        paginas = (
            self.lista_paginas.obtener_paginas_seleccionadas()
        )


        if not paginas:

            QMessageBox.information(
                self,
                "Extraer páginas",
                "Selecciona al menos una página."
            )

            return


        carpeta_salida = (
            self.campo_salida.text().strip()
        )


        if not carpeta_salida:

            QMessageBox.information(
                self,
                "Extraer páginas",
                "Selecciona una carpeta de salida."
            )

            return


        tipo = self.obtener_tipo_extraccion()


        self.barra_progreso.setVisible(
            True
        )

        self.barra_progreso.setRange(
            0,
            len(
                paginas
            )
        )

        self.barra_progreso.setValue(
            0
        )


        self.boton_cancelar.setVisible(
            True
        )

        self.etiqueta_estado.setText(
            "Extrayendo páginas..."
        )


        self.hilo_exportacion = QThread(
            self
        )


        self.trabajador_exportacion = (
            TrabajadorExportacionPaginas(
                self.ruta_pdf,
                paginas,
                carpeta_salida,
                tipo,
                formato_imagen=(
                    self.combo_formato.currentText()
                ),
                calidad=(
                    self.selector_calidad.value()
                ),
                txt_unico=(
                    self.obtener_txt_unico()
                )
            )
        )


        self.trabajador_exportacion.moveToThread(
            self.hilo_exportacion
        )


        self.hilo_exportacion.started.connect(
            self.trabajador_exportacion.ejecutar
        )

        self.trabajador_exportacion.progreso.connect(
            self.actualizar_progreso
        )

        self.trabajador_exportacion.completado.connect(
            self.exportacion_completada
        )

        self.trabajador_exportacion.cancelado.connect(
            self.exportacion_cancelada
        )

        self.trabajador_exportacion.error.connect(
            self.error_exportacion
        )

        self.trabajador_exportacion.finalizado.connect(
            self.hilo_exportacion.quit
        )

        self.trabajador_exportacion.finalizado.connect(
            self.trabajador_exportacion.deleteLater
        )

        self.hilo_exportacion.finished.connect(
            self.finalizar_exportacion
        )

        self.hilo_exportacion.finished.connect(
            self.hilo_exportacion.deleteLater
        )


        self.actualizar_estado_controles()


        self.hilo_exportacion.start()


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
            max(
                1,
                total
            )
        )

        self.barra_progreso.setValue(
            actual
        )


        self.etiqueta_estado.setText(
            f"Procesando {actual} de {total}..."
        )


    # ============================================================
    # EXPORTACIÓN COMPLETADA
    # ============================================================
    @Slot(
        list
    )
    def exportacion_completada(
        self,
        resultados
    ):

        cantidad = len(
            resultados
        )


        self.etiqueta_estado.setText(
            "Extracción completada."
        )


        QMessageBox.information(
            self,
            "Extraer páginas",
            (
                "La extracción terminó correctamente.\n\n"
                f"Archivos creados: {cantidad}\n"
                f"Carpeta:\n{self.campo_salida.text()}"
            )
        )


    # ============================================================
    # EXPORTACIÓN CANCELADA
    # ============================================================
    @Slot()
    def exportacion_cancelada(
        self
    ):

        self.etiqueta_estado.setText(
            "Extracción cancelada."
        )


    # ============================================================
    # ERROR DE EXPORTACIÓN
    # ============================================================
    @Slot(
        str
    )
    def error_exportacion(
        self,
        mensaje
    ):

        self.etiqueta_estado.setText(
            "No se pudo completar la extracción."
        )


        QMessageBox.critical(
            self,
            "Extraer páginas",
            mensaje
        )


    # ============================================================
    # CANCELAR
    # ============================================================
    def cancelar_exportacion(
        self
    ):

        if self.trabajador_exportacion is None:

            return


        self.boton_cancelar.setEnabled(
            False
        )

        self.etiqueta_estado.setText(
            "Cancelando..."
        )


        self.trabajador_exportacion.cancelar()


    # ============================================================
    # FINALIZAR
    # ============================================================
    def finalizar_exportacion(
        self
    ):

        self.hilo_exportacion = None

        self.trabajador_exportacion = None


        self.boton_cancelar.setVisible(
            False
        )

        self.boton_cancelar.setEnabled(
            True
        )


        self.actualizar_estado_controles()