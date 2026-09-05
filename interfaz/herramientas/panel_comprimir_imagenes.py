import os

from collections import OrderedDict

from PIL import (
    Image,
    ImageOps
)

from PIL.ImageQt import (
    toqpixmap
)

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QObject,
    QThread,
    QTimer,
    QEvent,
    QSize
)

from PySide6.QtGui import (
    QPixmap,
    QImageReader
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
    QSlider,
    QSpinBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QSizePolicy,
    QApplication
)

from herramientas.imagenes.comprimir_imagenes import (
    comprimir_imagenes,
    obtener_informacion_imagen
)


# ================================================================
# ROLES DE DATOS
# ================================================================

ROL_INFORMACION_IMAGEN = (
    int(
        Qt.ItemDataRole.UserRole
    )
    + 1
)


# ================================================================
# FORMATEAR TAMANO
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
# CARGAR PREVISUALIZACION OPTIMIZADA
# ================================================================
def cargar_pixmap_previsualizacion(
    ruta_imagen,
    ancho_maximo=1280,
    alto_maximo=960
):

    # ----------------------------------- #
    #         Lector optimizado Qt        #
    # ----------------------------------- #

    try:

        lector = QImageReader(
            ruta_imagen
        )

        lector.setAutoTransform(
            True
        )

        tamano_original = lector.size()

        if (
            tamano_original.isValid()
            and tamano_original.width() > 0
            and tamano_original.height() > 0
        ):

            if (
                tamano_original.width() > ancho_maximo
                or tamano_original.height() > alto_maximo
            ):

                tamano_destino = QSize(
                    tamano_original.width(),
                    tamano_original.height()
                )

                tamano_destino.scale(
                    QSize(
                        ancho_maximo,
                        alto_maximo
                    ),
                    Qt.AspectRatioMode.KeepAspectRatio
                )

                lector.setScaledSize(
                    tamano_destino
                )

        imagen_qt = lector.read()

        if not imagen_qt.isNull():

            return QPixmap.fromImage(
                imagen_qt
            )

    except Exception:

        pass


    # ----------------------------------- #
    #           Respaldo Pillow            #
    # ----------------------------------- #

    try:

        with Image.open(
            ruta_imagen
        ) as imagen:

            try:

                imagen.seek(
                    0
                )

            except EOFError:

                pass

            try:

                imagen.draft(
                    "RGB",
                    (
                        ancho_maximo,
                        alto_maximo
                    )
                )

            except Exception:

                pass

            imagen = ImageOps.exif_transpose(
                imagen
            )

            imagen.thumbnail(
                (
                    ancho_maximo,
                    alto_maximo
                ),
                Image.Resampling.LANCZOS
            )

            if imagen.mode not in {
                "RGB",
                "RGBA"
            }:

                imagen = imagen.convert(
                    "RGBA"
                )

            return toqpixmap(
                imagen
            )

    except Exception:

        return QPixmap()


# ================================================================
# VISTA PREVIA
# ================================================================
class VistaPreviaImagen(
    QLabel
):

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

        self.pixmap_original = QPixmap()

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setMinimumSize(
            360,
            240
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.setText(
            "Selecciona una imagen de la lista"
        )

        self.setStyleSheet(
            """
            QLabel {
                background-color: #252525;
                border: 1px solid #3b3b3b;
                border-radius: 8px;
                color: #aaaaaa;
            }
            """
        )


    # ============================================================
    # ESTABLECER IMAGEN
    # ============================================================
    def establecer_imagen(
        self,
        pixmap
    ):

        self.pixmap_original = pixmap

        self.actualizar_imagen()


    # ============================================================
    # LIMPIAR
    # ============================================================
    def limpiar(
        self
    ):

        self.pixmap_original = QPixmap()

        self.setPixmap(
            QPixmap()
        )

        self.setText(
            "Selecciona una imagen de la lista"
        )


    # ============================================================
    # ACTUALIZAR IMAGEN
    # ============================================================
    def actualizar_imagen(
        self
    ):

        if self.pixmap_original.isNull():

            self.limpiar()

            return

        ancho = max(
            1,
            self.width()
            - 20
        )

        alto = max(
            1,
            self.height()
            - 20
        )

        pixmap = self.pixmap_original.scaled(
            ancho,
            alto,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.setText(
            ""
        )

        self.setPixmap(
            pixmap
        )


    # ============================================================
    # CAMBIAR TAMANO
    # ============================================================
    def resizeEvent(
        self,
        evento
    ):

        super().resizeEvent(
            evento
        )

        self.actualizar_imagen()


# ================================================================
# TRABAJADOR DE COMPRESION
# ================================================================
class TrabajadorComprimirImagenes(
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
    # INICIALIZACION
    # ============================================================
    def __init__(
        self,
        rutas,
        carpeta_salida,
        calidad,
        eliminar_metadatos,
        evitar_archivo_mayor,
        sufijo
    ):

        super().__init__()

        self.rutas = rutas

        self.carpeta_salida = (
            carpeta_salida
        )

        self.calidad = calidad

        self.eliminar_metadatos = (
            eliminar_metadatos
        )

        self.evitar_archivo_mayor = (
            evitar_archivo_mayor
        )

        self.sufijo = sufijo

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
    # COMPROBAR CANCELACION
    # ============================================================
    def comprobar_cancelacion(
        self
    ):

        return (
            self.cancelacion_solicitada
        )


    # ============================================================
    # EJECUTAR
    # ============================================================
    @Slot()
    def ejecutar(
        self
    ):

        try:

            resultados = comprimir_imagenes(
                self.rutas,
                self.carpeta_salida,
                calidad=self.calidad,
                eliminar_metadatos=(
                    self.eliminar_metadatos
                ),
                evitar_archivo_mayor=(
                    self.evitar_archivo_mayor
                ),
                sobrescribir=False,
                sufijo=self.sufijo,
                progreso=self.progreso.emit,
                comprobar_cancelacion_callback=(
                    self.comprobar_cancelacion
                )
            )

            if self.cancelacion_solicitada:

                self.cancelado.emit()

                return

            self.terminado.emit(
                resultados
            )

        except Exception as error:

            if self.cancelacion_solicitada:

                self.cancelado.emit()

                return

            self.error.emit(
                str(
                    error
                )
            )


# ================================================================
# PANEL COMPRIMIR IMAGENES
# ================================================================
class PanelComprimirImagenes(
    QWidget
):

    # ============================================================
    # DIMENSIONES DE VENTANA
    # ============================================================

    ANCHO_INICIAL = 820
    ALTO_INICIAL = 700

    ANCHO_MINIMO = 820
    ALTO_MINIMO = 700

    DURACION_RESULTADO_MS = 8000

    INTERVALO_RESULTADO_MS = 10

    RETARDO_PREVISUALIZACION_MS = 30

    MAXIMO_CACHE_PREVISUALIZACIONES = 12


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

        self.rutas_imagenes = []

        self.carpeta_salida = None

        self.hilo = None

        self.trabajador = None

        self.actualizando_calidad = False

        self.tiempo_resultado_transcurrido = 0

        self.item_previsualizacion_pendiente = None

        self.cache_previsualizaciones = (
            OrderedDict()
        )

        self.setAcceptDrops(
            True
        )

        self.setStyleSheet(
            """
            QPushButton {
                min-height: 30px;
                padding: 3px 11px;
            }
            """
        )

        self.crear_interfaz()

        self.crear_temporizador_resultado()

        self.crear_temporizador_previsualizacion()

        self.conectar_eventos()

        self.configurar_navegacion_teclado()

        self.actualizar_estado_controles()


    # ============================================================
    # CREAR TEMPORIZADOR DE RESULTADO
    # ============================================================
    def crear_temporizador_resultado(
        self
    ):

        self.temporizador_resultado = QTimer(
            self
        )

        self.temporizador_resultado.setInterval(
            self.INTERVALO_RESULTADO_MS
        )

        self.temporizador_resultado.timeout.connect(
            self.avanzar_temporizador_resultado
        )


    # ============================================================
    # CREAR TEMPORIZADOR DE PREVISUALIZACION
    # ============================================================
    def crear_temporizador_previsualizacion(
        self
    ):

        self.temporizador_previsualizacion = QTimer(
            self
        )

        self.temporizador_previsualizacion.setSingleShot(
            True
        )

        self.temporizador_previsualizacion.setInterval(
            self.RETARDO_PREVISUALIZACION_MS
        )

        self.temporizador_previsualizacion.timeout.connect(
            self.cargar_previsualizacion_pendiente
        )


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self
    ):

        layout_principal = QVBoxLayout(
            self
        )

        layout_principal.setContentsMargins(
            18,
            12,
            18,
            14
        )

        layout_principal.setSpacing(
            8
        )


        # ----------------------------------- #
        #              Titulo                 #
        # ----------------------------------- #

        titulo = QLabel(
            "Comprimir imágenes"
        )

        titulo.setStyleSheet(
            "font-size: 22px; font-weight: 600;"
        )

        descripcion = QLabel(
            "Reduce el tamaño de una o varias imágenes "
            "manteniendo su formato original."
        )

        descripcion.setWordWrap(
            True
        )

        layout_principal.addWidget(
            titulo
        )

        layout_principal.addWidget(
            descripcion
        )


        # ----------------------------------- #
        #          Botones de entrada         #
        # ----------------------------------- #

        fila_entrada = QHBoxLayout()

        fila_entrada.setSpacing(
            7
        )

        self.boton_agregar = QPushButton(
            "Añadir imágenes"
        )

        self.boton_quitar = QPushButton(
            "Quitar seleccionadas"
        )

        self.boton_limpiar = QPushButton(
            "Limpiar"
        )

        fila_entrada.addWidget(
            self.boton_agregar
        )

        fila_entrada.addWidget(
            self.boton_quitar
        )

        fila_entrada.addWidget(
            self.boton_limpiar
        )

        fila_entrada.addStretch()

        self.etiqueta_total = QLabel(
            "0 imágenes"
        )

        self.etiqueta_total.setStyleSheet(
            "color: #aaaaaa;"
        )

        fila_entrada.addWidget(
            self.etiqueta_total
        )

        layout_principal.addLayout(
            fila_entrada
        )


        # ========================================================
        # CONTENIDO
        # ========================================================

        fila_contenido = QHBoxLayout()

        fila_contenido.setSpacing(
            12
        )


        # ----------------------------------- #
        #      Lista y previsualizacion       #
        # ----------------------------------- #

        contenedor_izquierdo = QWidget()

        layout_izquierdo = QVBoxLayout(
            contenedor_izquierdo
        )

        layout_izquierdo.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout_izquierdo.setSpacing(
            6
        )

        self.lista_imagenes = QListWidget()

        self.lista_imagenes.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.lista_imagenes.setMinimumHeight(
            115
        )

        self.lista_imagenes.setMaximumHeight(
            180
        )

        self.lista_imagenes.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        layout_izquierdo.addWidget(
            self.lista_imagenes
        )

        self.etiqueta_info_imagen = QLabel(
            "Selecciona una imagen para ver sus datos."
        )

        self.etiqueta_info_imagen.setStyleSheet(
            "color: #aaaaaa;"
        )

        self.etiqueta_info_imagen.setWordWrap(
            True
        )

        layout_izquierdo.addWidget(
            self.etiqueta_info_imagen
        )

        self.vista_previa = VistaPreviaImagen(
            self
        )

        layout_izquierdo.addWidget(
            self.vista_previa,
            1
        )

        fila_contenido.addWidget(
            contenedor_izquierdo,
            1
        )


        # ----------------------------------- #
        #          Panel de controles         #
        # ----------------------------------- #

        panel_controles = QFrame()

        panel_controles.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        panel_controles.setMinimumWidth(
            310
        )

        panel_controles.setMaximumWidth(
            350
        )

        layout_controles = QVBoxLayout(
            panel_controles
        )

        layout_controles.setContentsMargins(
            14,
            12,
            14,
            12
        )

        layout_controles.setSpacing(
            9
        )


        # ----------------------------------- #
        #              Calidad                #
        # ----------------------------------- #

        etiqueta_calidad = QLabel(
            "Calidad"
        )

        etiqueta_calidad.setStyleSheet(
            "font-weight: 600;"
        )

        layout_controles.addWidget(
            etiqueta_calidad
        )

        fila_calidad = QHBoxLayout()

        fila_calidad.setSpacing(
            8
        )

        self.slider_calidad = QSlider(
            Qt.Orientation.Horizontal
        )

        self.slider_calidad.setRange(
            1,
            100
        )

        self.slider_calidad.setValue(
            85
        )

        self.campo_calidad = QSpinBox()

        self.campo_calidad.setRange(
            1,
            100
        )

        self.campo_calidad.setValue(
            85
        )

        self.campo_calidad.setSuffix(
            " %"
        )

        self.campo_calidad.setMinimumWidth(
            76
        )

        fila_calidad.addWidget(
            self.slider_calidad,
            1
        )

        fila_calidad.addWidget(
            self.campo_calidad
        )

        layout_controles.addLayout(
            fila_calidad
        )

        self.etiqueta_calidad_info = QLabel(
            "85% · Equilibrada"
        )

        self.etiqueta_calidad_info.setStyleSheet(
            "color: #9d9d9d;"
        )

        layout_controles.addWidget(
            self.etiqueta_calidad_info
        )

        explicacion = QLabel(
            "La calidad afecta a formatos con compresión "
            "con pérdida como JPG o WEBP. PNG y otros "
            "formatos se optimizan sin pérdida cuando corresponde."
        )

        explicacion.setWordWrap(
            True
        )

        explicacion.setStyleSheet(
            "color: #8f8f8f; font-size: 12px;"
        )

        layout_controles.addWidget(
            explicacion
        )


        # ----------------------------------- #
        #             Opciones                #
        # ----------------------------------- #

        self.check_metadatos = QCheckBox(
            "Eliminar metadatos para reducir más"
        )

        self.check_metadatos.setToolTip(
            "Puede quitar EXIF, comentarios, ubicación GPS "
            "y otros metadatos almacenados en la imagen."
        )

        layout_controles.addWidget(
            self.check_metadatos
        )

        self.check_evitar_mayor = QCheckBox(
            "No guardar si la recompresión pesa más"
        )

        self.check_evitar_mayor.setChecked(
            True
        )

        self.check_evitar_mayor.setToolTip(
            "Si la recompresión resulta más grande que "
            "el archivo original, se conserva una copia "
            "del archivo original en su lugar. "
            "Si eliges eliminar metadatos, se prioriza "
            "la eliminación de metadatos."
        )

        layout_controles.addWidget(
            self.check_evitar_mayor
        )

        separador = QFrame()

        separador.setFrameShape(
            QFrame.Shape.HLine
        )

        layout_controles.addWidget(
            separador
        )


        # ----------------------------------- #
        #               Salida                #
        # ----------------------------------- #

        etiqueta_salida = QLabel(
            "Salida"
        )

        etiqueta_salida.setStyleSheet(
            "font-weight: 600;"
        )

        layout_controles.addWidget(
            etiqueta_salida
        )

        self.campo_salida = QLineEdit()

        self.campo_salida.setReadOnly(
            True
        )

        self.campo_salida.setPlaceholderText(
            "Carpeta de salida"
        )

        layout_controles.addWidget(
            self.campo_salida
        )

        self.boton_salida = QPushButton(
            "Elegir carpeta"
        )

        layout_controles.addWidget(
            self.boton_salida
        )

        fila_sufijo = QHBoxLayout()

        fila_sufijo.setSpacing(
            7
        )

        fila_sufijo.addWidget(
            QLabel(
                "Sufijo:"
            )
        )

        self.campo_sufijo = QLineEdit(
            "_comprimida"
        )

        fila_sufijo.addWidget(
            self.campo_sufijo,
            1
        )

        layout_controles.addLayout(
            fila_sufijo
        )

        layout_controles.addStretch()

        fila_contenido.addWidget(
            panel_controles,
            0
        )

        layout_principal.addLayout(
            fila_contenido,
            1
        )


        # ========================================================
        # RESULTADO TEMPORAL
        # ========================================================

        self.contenedor_resultado = QFrame()

        self.contenedor_resultado.setObjectName(
            "ContenedorResultado"
        )

        self.contenedor_resultado.setVisible(
            False
        )

        self.contenedor_resultado.setStyleSheet(
            """
            QFrame#ContenedorResultado {
                border: 1px solid rgba(100, 170, 255, 150);
                border-radius: 7px;
                background-color: rgba(50, 100, 170, 40);
            }

            QFrame#ContenedorResultado QLabel {
                border: none;
                background-color: transparent;
                color: #d9e9ff;
            }

            QFrame#ContenedorResultado QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 35);
                border-radius: 2px;
            }

            QFrame#ContenedorResultado QProgressBar::chunk {
                background-color: #4da3ff;
                border-radius: 2px;
            }
            """
        )

        layout_resultado = QVBoxLayout(
            self.contenedor_resultado
        )

        layout_resultado.setContentsMargins(
            10,
            8,
            10,
            5
        )

        layout_resultado.setSpacing(
            5
        )

        self.etiqueta_resultado = QLabel(
            ""
        )

        self.etiqueta_resultado.setWordWrap(
            True
        )

        layout_resultado.addWidget(
            self.etiqueta_resultado
        )

        self.barra_tiempo_resultado = QProgressBar()

        self.barra_tiempo_resultado.setRange(
            0,
            self.DURACION_RESULTADO_MS
        )

        self.barra_tiempo_resultado.setValue(
            0
        )

        self.barra_tiempo_resultado.setTextVisible(
            False
        )

        self.barra_tiempo_resultado.setFixedHeight(
            4
        )

        layout_resultado.addWidget(
            self.barra_tiempo_resultado
        )

        layout_principal.addWidget(
            self.contenedor_resultado
        )


        # ========================================================
        # PROGRESO Y ACCIONES
        # ========================================================

        fila_progreso = QHBoxLayout()

        fila_progreso.setSpacing(
            8
        )

        self.etiqueta_estado = QLabel(
            ""
        )

        self.etiqueta_estado.setMaximumWidth(
            170
        )

        self.etiqueta_estado.setStyleSheet(
            "color: #bcbcbc;"
        )

        self.barra_progreso = QProgressBar()

        self.barra_progreso.setRange(
            0,
            100
        )

        self.barra_progreso.setValue(
            0
        )

        self.boton_comprimir = QPushButton(
            "Comprimir imágenes"
        )

        self.boton_comprimir.setMinimumWidth(
            160
        )

        self.boton_comprimir.setMinimumHeight(
            34
        )

        self.boton_cancelar = QPushButton(
            "Cancelar"
        )

        self.boton_cancelar.setMinimumWidth(
            85
        )

        self.boton_cancelar.setMinimumHeight(
            34
        )

        self.boton_cancelar.setEnabled(
            False
        )

        fila_progreso.addWidget(
            self.etiqueta_estado
        )

        fila_progreso.addWidget(
            self.barra_progreso,
            1
        )

        fila_progreso.addWidget(
            self.boton_comprimir
        )

        fila_progreso.addWidget(
            self.boton_cancelar
        )

        layout_principal.addLayout(
            fila_progreso
        )


    # ============================================================
    # CONECTAR EVENTOS
    # ============================================================
    def conectar_eventos(
        self
    ):

        self.boton_agregar.clicked.connect(
            self.seleccionar_imagenes
        )

        self.boton_quitar.clicked.connect(
            self.quitar_seleccionadas
        )

        self.boton_limpiar.clicked.connect(
            self.limpiar_lista
        )

        self.lista_imagenes.currentItemChanged.connect(
            self.actualizar_previsualizacion
        )

        self.slider_calidad.valueChanged.connect(
            self.cambiar_calidad_slider
        )

        self.campo_calidad.valueChanged.connect(
            self.cambiar_calidad_campo
        )

        self.boton_salida.clicked.connect(
            self.seleccionar_carpeta_salida
        )

        self.boton_comprimir.clicked.connect(
            self.iniciar_compresion
        )

        self.boton_cancelar.clicked.connect(
            self.cancelar_compresion
        )


    # ============================================================
    # CONFIGURAR NAVEGACION GLOBAL CON FLECHAS
    # ============================================================
    def configurar_navegacion_teclado(
        self
    ):

        aplicacion = QApplication.instance()

        if aplicacion is not None:

            aplicacion.installEventFilter(
                self
            )


    # ============================================================
    # COMPROBAR SI EL FOCO PERTENECE AL PANEL
    # ============================================================
    def foco_pertenece_al_panel(
        self
    ):

        foco = QApplication.focusWidget()

        if foco is None:

            return False

        if foco is self:

            return True

        return self.isAncestorOf(
            foco
        )


    # ============================================================
    # FILTRO GLOBAL DE EVENTOS
    # ============================================================
    def eventFilter(
        self,
        objeto,
        evento
    ):

        if (
            evento.type()
            == QEvent.Type.KeyPress
            and self.isVisible()
            and self.isEnabled()
            and self.foco_pertenece_al_panel()
        ):

            tecla = evento.key()

            if tecla == Qt.Key.Key_Up:

                if self.mover_imagen_activa(
                    -1
                ):

                    evento.accept()

                    return True

            elif tecla == Qt.Key.Key_Down:

                if self.mover_imagen_activa(
                    1
                ):

                    evento.accept()

                    return True

        return super().eventFilter(
            objeto,
            evento
        )


    # ============================================================
    # MOVER IMAGEN ACTIVA
    # ============================================================
    def mover_imagen_activa(
        self,
        desplazamiento
    ):

        if self.hilo is not None:

            return True

        total = (
            self.lista_imagenes.count()
        )

        if total <= 0:

            return False

        fila_actual = (
            self.lista_imagenes.currentRow()
        )

        if fila_actual < 0:

            nueva_fila = (
                0
                if desplazamiento > 0
                else total - 1
            )

        else:

            nueva_fila = max(
                0,
                min(
                    total - 1,
                    fila_actual
                    + desplazamiento
                )
            )

        if nueva_fila != fila_actual:

            self.lista_imagenes.setCurrentRow(
                nueva_fila
            )

            item = (
                self.lista_imagenes.item(
                    nueva_fila
                )
            )

            if item is not None:

                self.lista_imagenes.scrollToItem(
                    item,
                    QAbstractItemView.ScrollHint.EnsureVisible
                )

        return True


    # ============================================================
    # OBTENER CLAVE DE CACHE
    # ============================================================
    def obtener_clave_cache(
        self,
        ruta
    ):

        return os.path.normcase(
            os.path.abspath(
                ruta
            )
        )


    # ============================================================
    # OBTENER PREVISUALIZACION DE CACHE
    # ============================================================
    def obtener_previsualizacion_cache(
        self,
        ruta
    ):

        clave = self.obtener_clave_cache(
            ruta
        )

        if clave not in self.cache_previsualizaciones:

            return None

        pixmap = self.cache_previsualizaciones.pop(
            clave
        )

        self.cache_previsualizaciones[
            clave
        ] = pixmap

        return pixmap


    # ============================================================
    # GUARDAR PREVISUALIZACION EN CACHE
    # ============================================================
    def guardar_previsualizacion_cache(
        self,
        ruta,
        pixmap
    ):

        if pixmap.isNull():

            return

        clave = self.obtener_clave_cache(
            ruta
        )

        if clave in self.cache_previsualizaciones:

            self.cache_previsualizaciones.pop(
                clave
            )

        self.cache_previsualizaciones[
            clave
        ] = pixmap

        while (
            len(
                self.cache_previsualizaciones
            )
            > self.MAXIMO_CACHE_PREVISUALIZACIONES
        ):

            self.cache_previsualizaciones.popitem(
                last=False
            )


    # ============================================================
    # ELIMINAR PREVISUALIZACION DE CACHE
    # ============================================================
    def eliminar_previsualizacion_cache(
        self,
        ruta
    ):

        clave = self.obtener_clave_cache(
            ruta
        )

        self.cache_previsualizaciones.pop(
            clave,
            None
        )


    # ============================================================
    # CARGAR PREVISUALIZACION PENDIENTE
    # ============================================================
    def cargar_previsualizacion_pendiente(
        self
    ):

        item = (
            self.item_previsualizacion_pendiente
        )

        self.item_previsualizacion_pendiente = None

        if item is None:

            return

        if (
            item
            is not self.lista_imagenes.currentItem()
        ):

            return

        ruta = item.data(
            Qt.ItemDataRole.UserRole
        )

        pixmap = self.obtener_previsualizacion_cache(
            ruta
        )

        if pixmap is None:

            pixmap = cargar_pixmap_previsualizacion(
                ruta
            )

            self.guardar_previsualizacion_cache(
                ruta,
                pixmap
            )

        if (
            item
            is not self.lista_imagenes.currentItem()
        ):

            return

        self.vista_previa.establecer_imagen(
            pixmap
        )


    # ============================================================
    # MOSTRAR RESULTADO TEMPORAL
    # ============================================================
    def mostrar_resultado_temporal(
        self,
        texto
    ):

        self.temporizador_resultado.stop()

        self.tiempo_resultado_transcurrido = 0

        self.etiqueta_resultado.setText(
            texto
        )

        self.barra_tiempo_resultado.setValue(
            0
        )

        self.contenedor_resultado.setVisible(
            True
        )

        self.temporizador_resultado.start()


    # ============================================================
    # AVANZAR TEMPORIZADOR DE RESULTADO
    # ============================================================
    def avanzar_temporizador_resultado(
        self
    ):

        self.tiempo_resultado_transcurrido += (
            self.INTERVALO_RESULTADO_MS
        )

        self.barra_tiempo_resultado.setValue(
            self.tiempo_resultado_transcurrido
        )

        if (
            self.tiempo_resultado_transcurrido
            >= self.DURACION_RESULTADO_MS
        ):

            self.ocultar_resultado_temporal()


    # ============================================================
    # OCULTAR RESULTADO TEMPORAL
    # ============================================================
    def ocultar_resultado_temporal(
        self
    ):

        self.temporizador_resultado.stop()

        self.tiempo_resultado_transcurrido = 0

        self.barra_tiempo_resultado.setValue(
            0
        )

        self.contenedor_resultado.setVisible(
            False
        )


    # ============================================================
    # ARRASTRAR ARCHIVOS
    # ============================================================
    def dragEnterEvent(
        self,
        evento
    ):

        if evento.mimeData().hasUrls():

            evento.acceptProposedAction()

            return

        evento.ignore()


    # ============================================================
    # SOLTAR ARCHIVOS
    # ============================================================
    def dropEvent(
        self,
        evento
    ):

        rutas = []

        for url in (
            evento.mimeData().urls()
        ):

            ruta = url.toLocalFile()

            if ruta:

                rutas.append(
                    ruta
                )

        if rutas:

            self.agregar_rutas(
                rutas
            )

            evento.acceptProposedAction()

            return

        evento.ignore()


    # ============================================================
    # SELECCIONAR IMAGENES
    # ============================================================
    def seleccionar_imagenes(
        self
    ):

        rutas, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar imágenes",
            "",
            (
                "Imágenes (*.jpg *.jpeg *.png *.webp *.bmp *.gif "
                "*.tif *.tiff *.ico *.apng *.avif *.heic *.heif "
                "*.jxl *.jp2 *.j2k *.jxr *.qoi *.tga *.pcx *.pnm "
                "*.pbm *.pgm *.ppm *.pam *.hdr *.exr *.dpx *.dds);;"
                "Todos los archivos (*.*)"
            )
        )

        if rutas:

            self.agregar_rutas(
                rutas
            )


    # ============================================================
    # AGREGAR RUTAS
    # ============================================================
    def agregar_rutas(
        self,
        rutas
    ):

        existentes = {
            os.path.normcase(
                os.path.abspath(
                    ruta
                )
            )
            for ruta
            in self.rutas_imagenes
        }

        errores = []

        agregadas = []

        for ruta in rutas:

            ruta_absoluta = os.path.abspath(
                ruta
            )

            clave = os.path.normcase(
                ruta_absoluta
            )

            if clave in existentes:

                continue

            try:

                informacion = obtener_informacion_imagen(
                    ruta_absoluta
                )

            except Exception as error:

                errores.append(
                    (
                        f"{os.path.basename(ruta_absoluta)}: "
                        f"{error}"
                    )
                )

                continue

            self.rutas_imagenes.append(
                ruta_absoluta
            )

            existentes.add(
                clave
            )

            agregadas.append(
                (
                    ruta_absoluta,
                    informacion
                )
            )

        for (
            ruta,
            informacion
        ) in agregadas:

            texto = (
                f"{os.path.basename(ruta)}"
                f"   ·   "
                f"{formatear_tamano(informacion['tamano'])}"
            )

            item = QListWidgetItem(
                texto
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                ruta
            )

            item.setData(
                ROL_INFORMACION_IMAGEN,
                dict(
                    informacion
                )
            )

            item.setToolTip(
                ruta
            )

            self.lista_imagenes.addItem(
                item
            )

        if (
            self.carpeta_salida is None
            and self.rutas_imagenes
        ):

            self.carpeta_salida = os.path.dirname(
                self.rutas_imagenes[0]
            )

            self.campo_salida.setText(
                self.carpeta_salida
            )

        if (
            self.lista_imagenes.count() > 0
            and self.lista_imagenes.currentRow() < 0
        ):

            self.lista_imagenes.setCurrentRow(
                0
            )

        self.actualizar_resumen_lista()

        self.actualizar_estado_controles()

        if errores:

            QMessageBox.warning(
                self,
                "Algunas imágenes no se añadieron",
                "\n\n".join(
                    errores
                )
            )


    # ============================================================
    # QUITAR SELECCIONADAS
    # ============================================================
    def quitar_seleccionadas(
        self
    ):

        filas = sorted(
            {
                self.lista_imagenes.row(
                    item
                )
                for item
                in self.lista_imagenes.selectedItems()
            },
            reverse=True
        )

        for fila in filas:

            item = self.lista_imagenes.takeItem(
                fila
            )

            if item is None:

                continue

            ruta = item.data(
                Qt.ItemDataRole.UserRole
            )

            self.eliminar_previsualizacion_cache(
                ruta
            )

            try:

                self.rutas_imagenes.remove(
                    ruta
                )

            except ValueError:

                pass

        if not self.rutas_imagenes:

            self.temporizador_previsualizacion.stop()

            self.item_previsualizacion_pendiente = None

            self.vista_previa.limpiar()

            self.etiqueta_info_imagen.setText(
                "Selecciona una imagen para ver sus datos."
            )

        elif self.lista_imagenes.currentRow() < 0:

            self.lista_imagenes.setCurrentRow(
                0
            )

        self.actualizar_resumen_lista()

        self.actualizar_estado_controles()


    # ============================================================
    # LIMPIAR LISTA
    # ============================================================
    def limpiar_lista(
        self
    ):

        self.temporizador_previsualizacion.stop()

        self.item_previsualizacion_pendiente = None

        self.cache_previsualizaciones.clear()

        self.rutas_imagenes.clear()

        self.lista_imagenes.clear()

        self.vista_previa.limpiar()

        self.etiqueta_info_imagen.setText(
            "Selecciona una imagen para ver sus datos."
        )

        self.ocultar_resultado_temporal()

        self.actualizar_resumen_lista()

        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR RESUMEN DE LISTA
    # ============================================================
    def actualizar_resumen_lista(
        self
    ):

        cantidad = len(
            self.rutas_imagenes
        )

        tamano_total = 0

        for ruta in self.rutas_imagenes:

            try:

                tamano_total += os.path.getsize(
                    ruta
                )

            except OSError:

                pass

        if cantidad == 0:

            texto = (
                "0 imágenes"
            )

        elif cantidad == 1:

            texto = (
                f"1 imagen · "
                f"{formatear_tamano(tamano_total)}"
            )

        else:

            texto = (
                f"{cantidad} imágenes · "
                f"{formatear_tamano(tamano_total)}"
            )

        self.etiqueta_total.setText(
            texto
        )


    # ============================================================
    # ACTUALIZAR PREVISUALIZACION
    # ============================================================
    def actualizar_previsualizacion(
        self,
        item_actual,
        item_anterior
    ):

        self.temporizador_previsualizacion.stop()

        self.item_previsualizacion_pendiente = None

        if item_actual is None:

            self.vista_previa.limpiar()

            return

        ruta = item_actual.data(
            Qt.ItemDataRole.UserRole
        )

        informacion = item_actual.data(
            ROL_INFORMACION_IMAGEN
        )

        if not isinstance(
            informacion,
            dict
        ):

            try:

                informacion = obtener_informacion_imagen(
                    ruta
                )

                item_actual.setData(
                    ROL_INFORMACION_IMAGEN,
                    dict(
                        informacion
                    )
                )

            except Exception as error:

                self.etiqueta_info_imagen.setText(
                    str(
                        error
                    )
                )

                self.vista_previa.limpiar()

                return

        tipo_calidad = (
            "calidad ajustable"
            if informacion[
                "calidad_ajustable"
            ]
            else "optimización sin pérdida"
        )

        self.etiqueta_info_imagen.setText(
            (
                f"{informacion['formato']} · "
                f"{informacion['ancho']} × "
                f"{informacion['alto']} px · "
                f"{formatear_tamano(informacion['tamano'])} · "
                f"{tipo_calidad}"
            )
        )


        # ----------------------------------- #
        #          Cache inmediata            #
        # ----------------------------------- #

        pixmap_cache = (
            self.obtener_previsualizacion_cache(
                ruta
            )
        )

        if pixmap_cache is not None:

            self.vista_previa.establecer_imagen(
                pixmap_cache
            )

            return


        # ----------------------------------- #
        #         Carga diferida corta        #
        # ----------------------------------- #

        self.item_previsualizacion_pendiente = (
            item_actual
        )

        self.temporizador_previsualizacion.start()


    # ============================================================
    # CAMBIAR CALIDAD DESDE SLIDER
    # ============================================================
    def cambiar_calidad_slider(
        self,
        valor
    ):

        if self.actualizando_calidad:

            return

        self.actualizando_calidad = True

        self.campo_calidad.setValue(
            valor
        )

        self.actualizando_calidad = False

        self.actualizar_texto_calidad(
            valor
        )


    # ============================================================
    # CAMBIAR CALIDAD DESDE CAMPO
    # ============================================================
    def cambiar_calidad_campo(
        self,
        valor
    ):

        if self.actualizando_calidad:

            return

        self.actualizando_calidad = True

        self.slider_calidad.setValue(
            valor
        )

        self.actualizando_calidad = False

        self.actualizar_texto_calidad(
            valor
        )


    # ============================================================
    # ACTUALIZAR TEXTO DE CALIDAD
    # ============================================================
    def actualizar_texto_calidad(
        self,
        valor
    ):

        if valor >= 92:

            descripcion = (
                "Alta calidad"
            )

        elif valor >= 78:

            descripcion = (
                "Equilibrada"
            )

        elif valor >= 60:

            descripcion = (
                "Compresión fuerte"
            )

        else:

            descripcion = (
                "Compresión muy fuerte"
            )

        self.etiqueta_calidad_info.setText(
            f"{valor}% · {descripcion}"
        )


    # ============================================================
    # SELECCIONAR CARPETA DE SALIDA
    # ============================================================
    def seleccionar_carpeta_salida(
        self
    ):

        carpeta_inicial = (
            self.carpeta_salida
            or os.path.expanduser(
                "~"
            )
        )

        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de salida",
            carpeta_inicial
        )

        if carpeta:

            self.carpeta_salida = carpeta

            self.campo_salida.setText(
                carpeta
            )


    # ============================================================
    # ACTUALIZAR ESTADO DE CONTROLES
    # ============================================================
    def actualizar_estado_controles(
        self
    ):

        hay_imagenes = bool(
            self.rutas_imagenes
        )

        procesando = (
            self.hilo is not None
        )

        self.boton_agregar.setEnabled(
            not procesando
        )

        self.boton_quitar.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.boton_limpiar.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.lista_imagenes.setEnabled(
            not procesando
        )

        self.slider_calidad.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.campo_calidad.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.check_metadatos.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.check_evitar_mayor.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.boton_salida.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.campo_sufijo.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.boton_comprimir.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.boton_cancelar.setEnabled(
            procesando
        )


    # ============================================================
    # INICIAR COMPRESION
    # ============================================================
    def iniciar_compresion(
        self
    ):

        if not self.rutas_imagenes:

            return

        carpeta_salida = (
            self.carpeta_salida
            or os.path.dirname(
                self.rutas_imagenes[0]
            )
        )

        sufijo = (
            self.campo_sufijo.text().strip()
        )

        if not sufijo:

            sufijo = (
                "_comprimida"
            )

        self.ocultar_resultado_temporal()

        self.barra_progreso.setValue(
            0
        )

        self.etiqueta_estado.setText(
            "Preparando..."
        )

        self.hilo = QThread(
            self
        )

        self.trabajador = (
            TrabajadorComprimirImagenes(
                list(
                    self.rutas_imagenes
                ),
                carpeta_salida,
                self.campo_calidad.value(),
                self.check_metadatos.isChecked(),
                self.check_evitar_mayor.isChecked(),
                sufijo
            )
        )

        self.trabajador.moveToThread(
            self.hilo
        )

        self.hilo.started.connect(
            self.trabajador.ejecutar
        )

        self.trabajador.progreso.connect(
            self.actualizar_progreso
        )

        self.trabajador.terminado.connect(
            self.compresion_terminada
        )

        self.trabajador.cancelado.connect(
            self.compresion_cancelada
        )

        self.trabajador.error.connect(
            self.error_compresion
        )

        self.trabajador.terminado.connect(
            self.hilo.quit
        )

        self.trabajador.cancelado.connect(
            self.hilo.quit
        )

        self.trabajador.error.connect(
            self.hilo.quit
        )

        self.hilo.finished.connect(
            self.limpiar_hilo
        )

        self.actualizar_estado_controles()

        self.hilo.start()


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
        estado
    ):

        self.barra_progreso.setValue(
            porcentaje
        )

        self.etiqueta_estado.setText(
            estado
        )

        self.etiqueta_estado.setToolTip(
            estado
        )


    # ============================================================
    # CANCELAR COMPRESION
    # ============================================================
    def cancelar_compresion(
        self
    ):

        if self.trabajador is None:

            return

        self.trabajador.cancelar()

        self.etiqueta_estado.setText(
            "Cancelando..."
        )

        self.boton_cancelar.setEnabled(
            False
        )


    # ============================================================
    # COMPRESION TERMINADA
    # ============================================================
    @Slot(
        object
    )
    def compresion_terminada(
        self,
        resultados
    ):

        self.barra_progreso.setValue(
            100
        )

        self.etiqueta_estado.setText(
            "Completado"
        )

        tamano_original = sum(
            resultado[
                "tamano_original"
            ]
            for resultado
            in resultados
        )

        tamano_final = sum(
            resultado[
                "tamano_final"
            ]
            for resultado
            in resultados
        )

        reduccion = max(
            0,
            tamano_original
            - tamano_final
        )

        porcentaje = (
            reduccion
            / tamano_original
            * 100
            if tamano_original > 0
            else 0.0
        )

        sin_ganancia = sum(
            1
            for resultado
            in resultados
            if resultado[
                "recompresion_descartada"
            ]
        )

        cantidad = len(
            resultados
        )

        encabezado = (
            "1 imagen comprimida correctamente."
            if cantidad == 1
            else (
                f"{cantidad} imágenes comprimidas "
                "correctamente."
            )
        )

        texto = (
            f"{encabezado}\n"
            f"Tamaño original total: "
            f"{formatear_tamano(tamano_original)}\n"
            f"Tamaño final total: "
            f"{formatear_tamano(tamano_final)}\n"
            f"Reducción: "
            f"{formatear_tamano(reduccion)} "
            f"({porcentaje:.1f}%)"
        )

        if sin_ganancia:

            texto += (
                "\n"
                f"{sin_ganancia} archivo"
                + (
                    " no se recompresionó porque "
                    "el resultado era más grande."
                    if sin_ganancia == 1
                    else
                    "s no se recompresionaron porque "
                    "el resultado era más grande."
                )
            )

        self.mostrar_resultado_temporal(
            texto
        )


    # ============================================================
    # COMPRESION CANCELADA
    # ============================================================
    @Slot()
    def compresion_cancelada(
        self
    ):

        self.etiqueta_estado.setText(
            "Cancelado"
        )


    # ============================================================
    # ERROR DE COMPRESION
    # ============================================================
    @Slot(
        str
    )
    def error_compresion(
        self,
        mensaje
    ):

        self.etiqueta_estado.setText(
            "Error"
        )

        QMessageBox.critical(
            self,
            "Error al comprimir imágenes",
            mensaje
        )


    # ============================================================
    # LIMPIAR HILO
    # ============================================================
    @Slot()
    def limpiar_hilo(
        self
    ):

        if self.trabajador is not None:

            self.trabajador.deleteLater()

        if self.hilo is not None:

            self.hilo.deleteLater()

        self.trabajador = None

        self.hilo = None

        self.actualizar_estado_controles()


    # ============================================================
    # CANCELAR SI ESTA TRABAJANDO
    # ============================================================
    def cancelar_si_esta_trabajando(
        self
    ):

        if self.trabajador is not None:

            self.trabajador.cancelar()