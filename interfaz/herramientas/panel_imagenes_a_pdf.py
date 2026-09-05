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
    QRect,
    QRectF,
    QEvent,
    QSize
)

from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QPixmap,
    QImageReader
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QFrame,
    QProgressBar,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QSizePolicy,
    QScrollArea,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QStyleOptionButton,
    QStyle,
    QApplication
)

from herramientas.imagenes.imagenes_a_pdf import (
    TAMANO_AUTOMATICO,

    TAMANO_A0,
    TAMANO_A1,
    TAMANO_A2,
    TAMANO_A3,
    TAMANO_A4,
    TAMANO_A5,
    TAMANO_A6,

    TAMANO_B0,
    TAMANO_B1,
    TAMANO_B2,
    TAMANO_B3,
    TAMANO_B4,
    TAMANO_B5,
    TAMANO_B6,

    TAMANO_CARTA,
    TAMANO_LEGAL,
    TAMANO_SOBRE_10,
    TAMANO_TABLOIDE,
    TAMANO_EJECUTIVO,

    TAMANOS_PAGINA_MM,

    ORIENTACION_AUTOMATICA,
    ORIENTACION_VERTICAL,
    ORIENTACION_HORIZONTAL,

    AJUSTE_ENCAJAR,
    AJUSTE_LLENAR,

    crear_pdf_desde_imagenes,
    obtener_informacion_imagen
)


# ================================================================
# AMBITO DE CONFIGURACION
# ================================================================

AMBITO_DOCUMENTO = "documento"

AMBITO_PAGINA = "pagina"


ROL_CONFIGURACION_PAGINA = (
    int(
        Qt.ItemDataRole.UserRole
    )
    + 1
)

ROL_INFORMACION_IMAGEN = (
    int(
        Qt.ItemDataRole.UserRole
    )
    + 2
)


# ================================================================
# FORMATEAR TAMANO DE ARCHIVO
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
# FORMATEAR DIMENSION
# ================================================================
def formatear_dimension_mm(
    valor
):

    valor = float(
        valor
    )

    if valor.is_integer():

        return str(
            int(
                valor
            )
        )

    texto = (
        f"{valor:.2f}"
        .rstrip(
            "0"
        )
        .rstrip(
            "."
        )
    )

    return texto


# ================================================================
# CREAR TEXTO DE TAMANO DE PAGINA
# ================================================================
def crear_texto_tamano_pagina(
    nombre,
    identificador
):

    ancho, alto = TAMANOS_PAGINA_MM[
        identificador
    ]

    return (
        f"{nombre} — "
        f"{formatear_dimension_mm(ancho)} × "
        f"{formatear_dimension_mm(alto)} mm"
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
# DELEGADO DE CASILLA DE SELECCION
# ================================================================
class DelegadoSeleccionPagina(
    QStyledItemDelegate
):

    MARGEN_DERECHO = 10

    SEPARACION_TEXTO = 10


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


    # ============================================================
    # OBTENER ESTILO
    # ============================================================
    def obtener_estilo(
        self,
        opcion
    ):

        if opcion.widget is not None:

            return opcion.widget.style()

        return QApplication.style()


    # ============================================================
    # OBTENER RECTANGULO DE CASILLA
    # ============================================================
    def obtener_rectangulo_casilla(
        self,
        opcion
    ):

        estilo = self.obtener_estilo(
            opcion
        )

        ancho_indicador = estilo.pixelMetric(
            QStyle.PixelMetric.PM_IndicatorWidth,
            None,
            opcion.widget
        )

        alto_indicador = estilo.pixelMetric(
            QStyle.PixelMetric.PM_IndicatorHeight,
            None,
            opcion.widget
        )

        if ancho_indicador <= 0:

            ancho_indicador = 16

        if alto_indicador <= 0:

            alto_indicador = 16

        x = (
            opcion.rect.right()
            - self.MARGEN_DERECHO
            - ancho_indicador
            + 1
        )

        y = (
            opcion.rect.center().y()
            - alto_indicador // 2
        )

        return QRect(
            x,
            y,
            ancho_indicador,
            alto_indicador
        )


    # ============================================================
    # NORMALIZAR ESTADO
    # ============================================================
    def normalizar_estado(
        self,
        estado
    ):

        try:

            return Qt.CheckState(
                estado
            )

        except (
            TypeError,
            ValueError
        ):

            return Qt.CheckState.Unchecked


    # ============================================================
    # PINTAR ITEM
    # ============================================================
    def paint(
        self,
        painter,
        opcion,
        indice
    ):

        opcion_item = QStyleOptionViewItem(
            opcion
        )

        self.initStyleOption(
            opcion_item,
            indice
        )

        rectangulo_casilla = (
            self.obtener_rectangulo_casilla(
                opcion
            )
        )

        espacio_derecho = (
            rectangulo_casilla.width()
            + self.MARGEN_DERECHO
            + self.SEPARACION_TEXTO
        )

        opcion_item.rect = QRect(
            opcion.rect.left(),
            opcion.rect.top(),
            max(
                1,
                opcion.rect.width()
                - espacio_derecho
            ),
            opcion.rect.height()
        )

        opcion_item.features = (
            opcion_item.features
            & ~QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator
        )

        estilo = self.obtener_estilo(
            opcion
        )

        estilo.drawControl(
            QStyle.ControlElement.CE_ItemViewItem,
            opcion_item,
            painter,
            opcion.widget
        )

        estado = self.normalizar_estado(
            indice.data(
                Qt.ItemDataRole.CheckStateRole
            )
        )

        opcion_casilla = QStyleOptionButton()

        opcion_casilla.rect = (
            rectangulo_casilla
        )

        opcion_casilla.state = (
            QStyle.StateFlag.State_Enabled
        )

        if estado == Qt.CheckState.Checked:

            opcion_casilla.state |= (
                QStyle.StateFlag.State_On
            )

        elif estado == Qt.CheckState.PartiallyChecked:

            opcion_casilla.state |= (
                QStyle.StateFlag.State_NoChange
            )

        else:

            opcion_casilla.state |= (
                QStyle.StateFlag.State_Off
            )

        if (
            opcion.state
            & QStyle.StateFlag.State_MouseOver
        ):

            opcion_casilla.state |= (
                QStyle.StateFlag.State_MouseOver
            )

        estilo.drawPrimitive(
            QStyle.PrimitiveElement.PE_IndicatorCheckBox,
            opcion_casilla,
            painter,
            opcion.widget
        )


    # ============================================================
    # INTERACCION CON CASILLA
    # ============================================================
    def editorEvent(
        self,
        evento,
        modelo,
        opcion,
        indice
    ):

        if not indice.isValid():

            return False

        if (
            evento.type()
            == QEvent.Type.MouseButtonRelease
        ):

            try:

                posicion = (
                    evento.position().toPoint()
                )

            except AttributeError:

                posicion = evento.pos()

            rectangulo_casilla = (
                self.obtener_rectangulo_casilla(
                    opcion
                )
            )

            if rectangulo_casilla.contains(
                posicion
            ):

                estado_actual = (
                    self.normalizar_estado(
                        indice.data(
                            Qt.ItemDataRole.CheckStateRole
                        )
                    )
                )

                nuevo_estado = (
                    Qt.CheckState.Unchecked
                    if estado_actual
                    == Qt.CheckState.Checked
                    else Qt.CheckState.Checked
                )

                modelo.setData(
                    indice,
                    nuevo_estado,
                    Qt.ItemDataRole.CheckStateRole
                )

                return True

        if (
            evento.type()
            == QEvent.Type.KeyPress
        ):

            if (
                evento.key()
                == Qt.Key.Key_Space
            ):

                estado_actual = (
                    self.normalizar_estado(
                        indice.data(
                            Qt.ItemDataRole.CheckStateRole
                        )
                    )
                )

                nuevo_estado = (
                    Qt.CheckState.Unchecked
                    if estado_actual
                    == Qt.CheckState.Checked
                    else Qt.CheckState.Checked
                )

                modelo.setData(
                    indice,
                    nuevo_estado,
                    Qt.ItemDataRole.CheckStateRole
                )

                return True

        return super().editorEvent(
            evento,
            modelo,
            opcion,
            indice
        )


# ================================================================
# LISTA DE IMAGENES ORDENABLE
# ================================================================
class ListaImagenesOrdenable(
    QListWidget
):

    archivos_soltados = Signal(
        object
    )

    orden_cambiado = Signal()


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

        self.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.setDragEnabled(
            True
        )

        self.setAcceptDrops(
            True
        )

        self.setDropIndicatorShown(
            True
        )

        self.setDefaultDropAction(
            Qt.DropAction.MoveAction
        )

        self.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove
        )

        self.setItemDelegate(
            DelegadoSeleccionPagina(
                self
            )
        )


    # ============================================================
    # ENTRAR ARRASTRANDO
    # ============================================================
    def dragEnterEvent(
        self,
        evento
    ):

        if evento.mimeData().hasUrls():

            evento.acceptProposedAction()

            return

        super().dragEnterEvent(
            evento
        )


    # ============================================================
    # MOVER ARRASTRE
    # ============================================================
    def dragMoveEvent(
        self,
        evento
    ):

        if evento.mimeData().hasUrls():

            evento.acceptProposedAction()

            return

        super().dragMoveEvent(
            evento
        )


    # ============================================================
    # SOLTAR
    # ============================================================
    def dropEvent(
        self,
        evento
    ):

        if evento.mimeData().hasUrls():

            rutas = []

            for url in evento.mimeData().urls():

                ruta = url.toLocalFile()

                if ruta:

                    rutas.append(
                        ruta
                    )

            if rutas:

                self.archivos_soltados.emit(
                    rutas
                )

                evento.acceptProposedAction()

                return

        super().dropEvent(
            evento
        )

        self.orden_cambiado.emit()


# ================================================================
# VISTA PREVIA DE PAGINA
# ================================================================
class VistaPreviaPagina(
    QWidget
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

        self.pixmap = QPixmap()

        self.ancho_imagen = 1

        self.alto_imagen = 1

        self.tamano_pagina = (
            TAMANO_A4
        )

        self.orientacion = (
            ORIENTACION_AUTOMATICA
        )

        self.ajuste = (
            AJUSTE_ENCAJAR
        )

        self.margen_mm = 8.0

        self.no_ampliar = False

        self.resolucion_ppp = 200

        self.setMinimumSize(
            360,
            280
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )


    # ============================================================
    # ESTABLECER IMAGEN
    # ============================================================
    def establecer_imagen(
        self,
        pixmap,
        ancho,
        alto
    ):

        self.pixmap = pixmap

        self.ancho_imagen = max(
            1,
            int(
                ancho
            )
        )

        self.alto_imagen = max(
            1,
            int(
                alto
            )
        )

        self.update()


    # ============================================================
    # LIMPIAR
    # ============================================================
    def limpiar(
        self
    ):

        self.pixmap = QPixmap()

        self.ancho_imagen = 1

        self.alto_imagen = 1

        self.update()


    # ============================================================
    # ESTABLECER CONFIGURACION
    # ============================================================
    def establecer_configuracion(
        self,
        tamano_pagina,
        orientacion,
        ajuste,
        margen_mm,
        no_ampliar,
        resolucion_ppp
    ):

        self.tamano_pagina = tamano_pagina

        self.orientacion = orientacion

        self.ajuste = ajuste

        self.margen_mm = float(
            margen_mm
        )

        self.no_ampliar = bool(
            no_ampliar
        )

        self.resolucion_ppp = max(
            1,
            int(
                resolucion_ppp
            )
        )

        self.update()


    # ============================================================
    # OBTENER TAMANO FISICO DE PAGINA
    # ============================================================
    def obtener_tamano_pagina_mm(
        self
    ):

        if (
            self.tamano_pagina
            == TAMANO_AUTOMATICO
        ):

            ancho = (
                self.ancho_imagen
                / self.resolucion_ppp
                * 25.4
                + self.margen_mm
                * 2
            )

            alto = (
                self.alto_imagen
                / self.resolucion_ppp
                * 25.4
                + self.margen_mm
                * 2
            )

        else:

            ancho, alto = (
                TAMANOS_PAGINA_MM[
                    self.tamano_pagina
                ]
            )

        if (
            self.orientacion
            == ORIENTACION_VERTICAL
        ):

            if ancho > alto:

                ancho, alto = (
                    alto,
                    ancho
                )

        elif (
            self.orientacion
            == ORIENTACION_HORIZONTAL
        ):

            if alto > ancho:

                ancho, alto = (
                    alto,
                    ancho
                )

        elif (
            self.orientacion
            == ORIENTACION_AUTOMATICA
        ):

            imagen_horizontal = (
                self.ancho_imagen
                > self.alto_imagen
            )

            pagina_horizontal = (
                ancho > alto
            )

            if imagen_horizontal != pagina_horizontal:

                ancho, alto = (
                    alto,
                    ancho
                )

        return (
            max(
                1.0,
                float(
                    ancho
                )
            ),
            max(
                1.0,
                float(
                    alto
                )
            )
        )


    # ============================================================
    # PINTAR
    # ============================================================
    def paintEvent(
        self,
        evento
    ):

        super().paintEvent(
            evento
        )

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True
        )

        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform,
            True
        )

        painter.fillRect(
            self.rect(),
            QColor(
                37,
                37,
                37
            )
        )

        if self.pixmap.isNull():

            painter.setPen(
                QColor(
                    180,
                    180,
                    180
                )
            )

            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                (
                    "Selecciona una imagen para "
                    "previsualizar la página"
                )
            )

            return

        (
            ancho_pagina,
            alto_pagina
        ) = self.obtener_tamano_pagina_mm()

        margen_visual = 26

        ancho_disponible = max(
            1,
            self.width()
            - margen_visual
            * 2
        )

        alto_disponible = max(
            1,
            self.height()
            - margen_visual
            * 2
        )

        escala_pagina = min(
            ancho_disponible
            / ancho_pagina,
            alto_disponible
            / alto_pagina
        )

        ancho_visual_pagina = (
            ancho_pagina
            * escala_pagina
        )

        alto_visual_pagina = (
            alto_pagina
            * escala_pagina
        )

        x_pagina = (
            self.width()
            - ancho_visual_pagina
        ) / 2

        y_pagina = (
            self.height()
            - alto_visual_pagina
        ) / 2

        rect_pagina = QRectF(
            x_pagina,
            y_pagina,
            ancho_visual_pagina,
            alto_visual_pagina
        )

        painter.setPen(
            QPen(
                QColor(
                    80,
                    80,
                    80
                ),
                1
            )
        )

        painter.setBrush(
            QColor(
                250,
                250,
                250
            )
        )

        painter.drawRoundedRect(
            rect_pagina,
            4,
            4
        )

        margen_relativo_x = min(
            0.45,
            self.margen_mm
            / max(
                1.0,
                ancho_pagina
            )
        )

        margen_relativo_y = min(
            0.45,
            self.margen_mm
            / max(
                1.0,
                alto_pagina
            )
        )

        margen_x = (
            rect_pagina.width()
            * margen_relativo_x
        )

        margen_y = (
            rect_pagina.height()
            * margen_relativo_y
        )

        rect_disponible = rect_pagina.adjusted(
            margen_x,
            margen_y,
            -margen_x,
            -margen_y
        )

        if (
            rect_disponible.width() <= 1
            or rect_disponible.height() <= 1
        ):

            return

        ancho_imagen = max(
            1,
            self.pixmap.width()
        )

        alto_imagen = max(
            1,
            self.pixmap.height()
        )

        if self.ajuste == AJUSTE_LLENAR:

            escala = max(
                rect_disponible.width()
                / ancho_imagen,
                rect_disponible.height()
                / alto_imagen
            )

        else:

            escala = min(
                rect_disponible.width()
                / ancho_imagen,
                rect_disponible.height()
                / alto_imagen
            )

        if self.no_ampliar:

            ancho_fisico_mm = (
                self.ancho_imagen
                / self.resolucion_ppp
                * 25.4
            )

            alto_fisico_mm = (
                self.alto_imagen
                / self.resolucion_ppp
                * 25.4
            )

            ancho_visual_original = (
                ancho_fisico_mm
                * escala_pagina
            )

            alto_visual_original = (
                alto_fisico_mm
                * escala_pagina
            )

            if ancho_visual_original > 0:

                escala = min(
                    escala,
                    ancho_visual_original
                    / ancho_imagen
                )

            if alto_visual_original > 0:

                escala = min(
                    escala,
                    alto_visual_original
                    / alto_imagen
                )

        ancho_dibujado = (
            ancho_imagen
            * escala
        )

        alto_dibujado = (
            alto_imagen
            * escala
        )

        x_imagen = (
            rect_disponible.center().x()
            - ancho_dibujado
            / 2
        )

        y_imagen = (
            rect_disponible.center().y()
            - alto_dibujado
            / 2
        )

        rect_imagen = QRectF(
            x_imagen,
            y_imagen,
            ancho_dibujado,
            alto_dibujado
        )

        painter.save()

        painter.setClipRect(
            rect_disponible
        )

        painter.drawPixmap(
            rect_imagen,
            self.pixmap,
            QRectF(
                self.pixmap.rect()
            )
        )

        painter.restore()

        painter.setPen(
            QColor(
                150,
                150,
                150
            )
        )

        painter.drawText(
            self.rect().adjusted(
                10,
                10,
                -10,
                -10
            ),
            (
                Qt.AlignmentFlag.AlignBottom
                | Qt.AlignmentFlag.AlignHCenter
            ),
            "Vista previa aproximada de la página"
        )


# ================================================================
# TRABAJADOR IMAGENES A PDF
# ================================================================
class TrabajadorImagenesAPDF(
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
        configuraciones_paginas,
        ruta_destino,
        resolucion_ppp,
        calidad
    ):

        super().__init__()

        self.rutas = rutas

        self.configuraciones_paginas = (
            configuraciones_paginas
        )

        self.ruta_destino = (
            ruta_destino
        )

        self.resolucion_ppp = (
            resolucion_ppp
        )

        self.calidad = calidad

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

            resultado = crear_pdf_desde_imagenes(
                self.rutas,
                self.ruta_destino,
                resolucion_ppp=(
                    self.resolucion_ppp
                ),
                calidad=self.calidad,
                configuraciones_paginas=(
                    self.configuraciones_paginas
                ),
                progreso=self.progreso.emit,
                comprobar_cancelacion_callback=(
                    self.comprobar_cancelacion
                )
            )

            if self.cancelacion_solicitada:

                self.cancelado.emit()

                return

            self.terminado.emit(
                resultado
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
# PANEL IMAGENES A PDF
# ================================================================
class PanelImagenesAPDF(
    QWidget
):

    ANCHO_INICIAL = 860
    ALTO_INICIAL = 680

    ANCHO_MINIMO = 860
    ALTO_MINIMO = 680

    DURACION_RESULTADO_MS = 6000

    INTERVALO_RESULTADO_MS = 16

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

        self.hilo = None

        self.trabajador = None

        self.ruta_salida = None

        self.tiempo_resultado_transcurrido = 0

        self.actualizando_controles_diseno = False

        self.actualizando_seleccion_total = False

        self.item_previsualizacion_pendiente = None

        self.cache_previsualizaciones = (
            OrderedDict()
        )

        self.configuracion_documento = {
            "tamano_pagina": TAMANO_A4,
            "orientacion": ORIENTACION_AUTOMATICA,
            "ajuste": AJUSTE_ENCAJAR,
            "margen_mm": 8.0,
            "no_ampliar": False
        }

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

        self.cargar_configuracion_en_controles(
            self.configuracion_documento
        )

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
            "Imágenes → PDF"
        )

        titulo.setStyleSheet(
            "font-size: 22px; font-weight: 600;"
        )

        descripcion = QLabel(
            "Crea un PDF con una página por imagen "
            "y reordena las páginas arrastrando "
            "los elementos de la lista."
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
        #         Botones de entrada          #
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

        self.etiqueta_seleccionar_todas = QLabel(
            "Seleccionar todas"
        )

        self.check_seleccionar_todas = QCheckBox()

        self.check_seleccionar_todas.setTristate(
            True
        )

        self.check_seleccionar_todas.setToolTip(
            "Marcar o desmarcar todas las páginas."
        )

        fila_entrada.addWidget(
            self.etiqueta_seleccionar_todas
        )

        fila_entrada.addWidget(
            self.check_seleccionar_todas
        )

        fila_entrada.addSpacing(
            12
        )

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
        # CONTENIDO CENTRAL
        # ========================================================

        fila_contenido = QHBoxLayout()

        fila_contenido.setSpacing(
            12
        )


        # ----------------------------------- #
        #         Lado izquierdo              #
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

        self.lista_imagenes = (
            ListaImagenesOrdenable(
                self
            )
        )

        self.lista_imagenes.setMinimumHeight(
            145
        )

        self.lista_imagenes.setMaximumHeight(
            205
        )

        layout_izquierdo.addWidget(
            self.lista_imagenes
        )

        self.etiqueta_info_imagen = QLabel(
            "La fila resaltada es la página activa. "
            "Usa las casillas de la derecha para seleccionar varias."
        )

        self.etiqueta_info_imagen.setWordWrap(
            True
        )

        self.etiqueta_info_imagen.setStyleSheet(
            "color: #aaaaaa;"
        )

        layout_izquierdo.addWidget(
            self.etiqueta_info_imagen
        )

        self.vista_previa = VistaPreviaPagina(
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
        #         Scroll de controles         #
        # ----------------------------------- #

        self.scroll_controles = QScrollArea(
            self
        )

        self.scroll_controles.setWidgetResizable(
            True
        )

        self.scroll_controles.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_controles.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_controles.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scroll_controles.setMinimumWidth(
            355
        )

        self.scroll_controles.setMaximumWidth(
            410
        )

        self.panel_controles = QFrame()

        self.panel_controles.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        self.panel_controles.setMinimumWidth(
            335
        )

        layout_controles = QVBoxLayout(
            self.panel_controles
        )

        layout_controles.setContentsMargins(
            14,
            12,
            14,
            12
        )

        layout_controles.setSpacing(
            10
        )


        # ========================================================
        # DISENO DE PAGINAS
        # ========================================================

        etiqueta_diseno = QLabel(
            "Diseño de páginas"
        )

        etiqueta_diseno.setStyleSheet(
            "font-weight: 600;"
        )

        layout_controles.addWidget(
            etiqueta_diseno
        )

        layout_controles.addWidget(
            QLabel(
                "Aplicar cambios a"
            )
        )

        self.combo_ambito = QComboBox()

        self.combo_ambito.addItem(
            "Todo el documento",
            AMBITO_DOCUMENTO
        )

        self.combo_ambito.addItem(
            "Página/s seleccionada/s",
            AMBITO_PAGINA
        )

        layout_controles.addWidget(
            self.combo_ambito
        )

        self.etiqueta_ambito = QLabel(
            "Los cambios de diseño se aplicarán "
            "a todas las páginas."
        )

        self.etiqueta_ambito.setWordWrap(
            True
        )

        self.etiqueta_ambito.setStyleSheet(
            "color: #8f8f8f; font-size: 12px;"
        )

        layout_controles.addWidget(
            self.etiqueta_ambito
        )


        # ----------------------------------- #
        #      Cuadricula compacta            #
        # ----------------------------------- #

        cuadricula_diseno = QGridLayout()

        cuadricula_diseno.setHorizontalSpacing(
            10
        )

        cuadricula_diseno.setVerticalSpacing(
            6
        )

        cuadricula_diseno.addWidget(
            QLabel(
                "Tamaño"
            ),
            0,
            0
        )

        cuadricula_diseno.addWidget(
            QLabel(
                "Orientación"
            ),
            0,
            1
        )

        self.combo_tamano = QComboBox()

        self.combo_orientacion = QComboBox()

        self.configurar_combo_tamanos()

        self.combo_orientacion.addItem(
            "Automática",
            ORIENTACION_AUTOMATICA
        )

        self.combo_orientacion.addItem(
            "Vertical",
            ORIENTACION_VERTICAL
        )

        self.combo_orientacion.addItem(
            "Horizontal",
            ORIENTACION_HORIZONTAL
        )

        self.combo_tamano.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.combo_orientacion.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        cuadricula_diseno.addWidget(
            self.combo_tamano,
            1,
            0
        )

        cuadricula_diseno.addWidget(
            self.combo_orientacion,
            1,
            1
        )

        cuadricula_diseno.addWidget(
            QLabel(
                "Ajuste de imagen"
            ),
            2,
            0
        )

        cuadricula_diseno.addWidget(
            QLabel(
                "Margen"
            ),
            2,
            1
        )

        self.combo_ajuste = QComboBox()

        self.combo_ajuste.addItem(
            "Encajar completa",
            AJUSTE_ENCAJAR
        )

        self.combo_ajuste.addItem(
            "Llenar página",
            AJUSTE_LLENAR
        )

        self.combo_ajuste.setToolTip(
            "Llenar página puede recortar partes "
            "de la imagen para ocupar toda el área disponible."
        )

        self.campo_margen = QDoubleSpinBox()

        self.campo_margen.setRange(
            0.0,
            50.0
        )

        self.campo_margen.setDecimals(
            1
        )

        self.campo_margen.setSingleStep(
            1.0
        )

        self.campo_margen.setValue(
            8.0
        )

        self.campo_margen.setSuffix(
            " mm"
        )

        cuadricula_diseno.addWidget(
            self.combo_ajuste,
            3,
            0
        )

        cuadricula_diseno.addWidget(
            self.campo_margen,
            3,
            1
        )

        cuadricula_diseno.setColumnStretch(
            0,
            3
        )

        cuadricula_diseno.setColumnStretch(
            1,
            2
        )

        layout_controles.addLayout(
            cuadricula_diseno
        )

        self.check_no_ampliar = QCheckBox(
            "No ampliar imágenes pequeñas"
        )

        layout_controles.addWidget(
            self.check_no_ampliar
        )

        self.etiqueta_tamano_info = QLabel(
            ""
        )

        self.etiqueta_tamano_info.setWordWrap(
            True
        )

        self.etiqueta_tamano_info.setStyleSheet(
            "color: #8f8f8f; font-size: 12px;"
        )

        layout_controles.addWidget(
            self.etiqueta_tamano_info
        )


        # ========================================================
        # CALIDAD GLOBAL
        # ========================================================

        separador_calidad = QFrame()

        separador_calidad.setFrameShape(
            QFrame.Shape.HLine
        )

        layout_controles.addWidget(
            separador_calidad
        )

        etiqueta_calidad = QLabel(
            "Calidad del PDF"
        )

        etiqueta_calidad.setStyleSheet(
            "font-weight: 600;"
        )

        layout_controles.addWidget(
            etiqueta_calidad
        )

        etiqueta_calidad_global = QLabel(
            "Estas opciones se aplican al documento completo."
        )

        etiqueta_calidad_global.setWordWrap(
            True
        )

        etiqueta_calidad_global.setStyleSheet(
            "color: #8f8f8f; font-size: 12px;"
        )

        layout_controles.addWidget(
            etiqueta_calidad_global
        )

        cuadricula_calidad = QGridLayout()

        cuadricula_calidad.setHorizontalSpacing(
            10
        )

        cuadricula_calidad.setVerticalSpacing(
            6
        )

        cuadricula_calidad.addWidget(
            QLabel(
                "Resolución"
            ),
            0,
            0
        )

        cuadricula_calidad.addWidget(
            QLabel(
                "Compresión"
            ),
            0,
            1
        )

        self.combo_resolucion = QComboBox()

        self.combo_resolucion.addItem(
            "150 ppp",
            150
        )

        self.combo_resolucion.addItem(
            "200 ppp",
            200
        )

        self.combo_resolucion.addItem(
            "300 ppp",
            300
        )

        self.combo_resolucion.setCurrentIndex(
            1
        )

        self.campo_calidad = QSpinBox()

        self.campo_calidad.setRange(
            1,
            100
        )

        self.campo_calidad.setValue(
            92
        )

        self.campo_calidad.setSuffix(
            " %"
        )

        cuadricula_calidad.addWidget(
            self.combo_resolucion,
            1,
            0
        )

        cuadricula_calidad.addWidget(
            self.campo_calidad,
            1,
            1
        )

        cuadricula_calidad.setColumnStretch(
            0,
            1
        )

        cuadricula_calidad.setColumnStretch(
            1,
            1
        )

        layout_controles.addLayout(
            cuadricula_calidad
        )

        etiqueta_calidad_info = QLabel(
            "Más resolución y calidad producen "
            "archivos PDF más grandes."
        )

        etiqueta_calidad_info.setWordWrap(
            True
        )

        etiqueta_calidad_info.setStyleSheet(
            "color: #8f8f8f; font-size: 12px;"
        )

        layout_controles.addWidget(
            etiqueta_calidad_info
        )


        # ========================================================
        # SALIDA
        # ========================================================

        separador_salida = QFrame()

        separador_salida.setFrameShape(
            QFrame.Shape.HLine
        )

        layout_controles.addWidget(
            separador_salida
        )

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
            "Archivo PDF de salida"
        )

        layout_controles.addWidget(
            self.campo_salida
        )

        self.boton_salida = QPushButton(
            "Guardar PDF como..."
        )

        layout_controles.addWidget(
            self.boton_salida
        )

        layout_controles.addStretch()

        self.scroll_controles.setWidget(
            self.panel_controles
        )

        fila_contenido.addWidget(
            self.scroll_controles,
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
            "ContenedorResultadoPDF"
        )

        self.contenedor_resultado.setVisible(
            False
        )

        self.contenedor_resultado.setStyleSheet(
            """
            QFrame#ContenedorResultadoPDF {
                border: 1px solid rgba(100, 170, 255, 150);
                border-radius: 7px;
                background-color: rgba(50, 100, 170, 40);
            }

            QFrame#ContenedorResultadoPDF QLabel {
                border: none;
                background-color: transparent;
                color: #d9e9ff;
            }

            QFrame#ContenedorResultadoPDF QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 35);
                border-radius: 2px;
            }

            QFrame#ContenedorResultadoPDF QProgressBar::chunk {
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
        # PROGRESO
        # ========================================================

        fila_progreso = QHBoxLayout()

        fila_progreso.setSpacing(
            8
        )

        self.etiqueta_estado = QLabel(
            ""
        )

        self.etiqueta_estado.setMaximumWidth(
            190
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

        self.boton_crear = QPushButton(
            "Crear PDF"
        )

        self.boton_crear.setMinimumWidth(
            150
        )

        self.boton_crear.setMinimumHeight(
            34
        )

        self.boton_cancelar = QPushButton(
            "Cancelar"
        )

        self.boton_cancelar.setMinimumWidth(
            90
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
            self.boton_crear
        )

        fila_progreso.addWidget(
            self.boton_cancelar
        )

        layout_principal.addLayout(
            fila_progreso
        )


    # ============================================================
    # CONFIGURAR COMBO DE TAMANOS
    # ============================================================
    def configurar_combo_tamanos(
        self
    ):

        self.combo_tamano.clear()

        self.combo_tamano.addItem(
            "Automático — según imagen",
            TAMANO_AUTOMATICO
        )


        # ----------------------------------- #
        #       Formatos prioritarios         #
        # ----------------------------------- #

        prioritarios = [
            (
                "A4",
                TAMANO_A4
            ),
            (
                "Carta",
                TAMANO_CARTA
            ),
            (
                "Legal",
                TAMANO_LEGAL
            ),
            (
                "Sobre #10",
                TAMANO_SOBRE_10
            )
        ]

        for nombre, identificador in prioritarios:

            self.combo_tamano.addItem(
                crear_texto_tamano_pagina(
                    nombre,
                    identificador
                ),
                identificador
            )

        self.combo_tamano.insertSeparator(
            self.combo_tamano.count()
        )


        # ----------------------------------- #
        #           Serie ISO A               #
        # ----------------------------------- #

        tamanos_iso_a = [
            (
                "A0",
                TAMANO_A0
            ),
            (
                "A1",
                TAMANO_A1
            ),
            (
                "A2",
                TAMANO_A2
            ),
            (
                "A3",
                TAMANO_A3
            ),
            (
                "A5",
                TAMANO_A5
            ),
            (
                "A6",
                TAMANO_A6
            )
        ]

        for nombre, identificador in tamanos_iso_a:

            self.combo_tamano.addItem(
                crear_texto_tamano_pagina(
                    nombre,
                    identificador
                ),
                identificador
            )


        # ----------------------------------- #
        #           Serie ISO B               #
        # ----------------------------------- #

        tamanos_iso_b = [
            (
                "B0",
                TAMANO_B0
            ),
            (
                "B1",
                TAMANO_B1
            ),
            (
                "B2",
                TAMANO_B2
            ),
            (
                "B3",
                TAMANO_B3
            ),
            (
                "B4",
                TAMANO_B4
            ),
            (
                "B5",
                TAMANO_B5
            ),
            (
                "B6",
                TAMANO_B6
            )
        ]

        for nombre, identificador in tamanos_iso_b:

            self.combo_tamano.addItem(
                crear_texto_tamano_pagina(
                    nombre,
                    identificador
                ),
                identificador
            )

        self.combo_tamano.addItem(
            crear_texto_tamano_pagina(
                "Tabloide",
                TAMANO_TABLOIDE
            ),
            TAMANO_TABLOIDE
        )

        self.combo_tamano.addItem(
            crear_texto_tamano_pagina(
                "Ejecutivo",
                TAMANO_EJECUTIVO
            ),
            TAMANO_EJECUTIVO
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

        self.check_seleccionar_todas.clicked.connect(
            self.cambiar_seleccion_todas
        )

        self.lista_imagenes.itemChanged.connect(
            self.seleccion_item_cambiada
        )

        self.lista_imagenes.archivos_soltados.connect(
            self.agregar_rutas
        )

        self.lista_imagenes.orden_cambiado.connect(
            self.orden_lista_cambiado
        )

        self.lista_imagenes.currentItemChanged.connect(
            self.actualizar_previsualizacion
        )

        self.combo_ambito.currentIndexChanged.connect(
            self.cambiar_ambito_ajustes
        )

        self.combo_tamano.currentIndexChanged.connect(
            self.ajustes_diseno_cambiados
        )

        self.combo_orientacion.currentIndexChanged.connect(
            self.ajustes_diseno_cambiados
        )

        self.combo_ajuste.currentIndexChanged.connect(
            self.ajustes_diseno_cambiados
        )

        self.campo_margen.valueChanged.connect(
            self.ajustes_diseno_cambiados
        )

        self.check_no_ampliar.toggled.connect(
            self.ajustes_diseno_cambiados
        )

        self.combo_resolucion.currentIndexChanged.connect(
            self.actualizar_configuracion_previsualizacion
        )

        self.boton_salida.clicked.connect(
            self.seleccionar_salida
        )

        self.boton_crear.clicked.connect(
            self.iniciar_creacion_pdf
        )

        self.boton_cancelar.clicked.connect(
            self.cancelar_creacion_pdf
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

                if self.mover_pagina_activa(
                    -1
                ):

                    evento.accept()

                    return True

            elif tecla == Qt.Key.Key_Down:

                if self.mover_pagina_activa(
                    1
                ):

                    evento.accept()

                    return True

        return super().eventFilter(
            objeto,
            evento
        )


    # ============================================================
    # MOVER PAGINA ACTIVA
    # ============================================================
    def mover_pagina_activa(
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

        informacion = item.data(
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

                item.setData(
                    ROL_INFORMACION_IMAGEN,
                    dict(
                        informacion
                    )
                )

            except Exception:

                return

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
            pixmap,
            informacion[
                "ancho"
            ],
            informacion[
                "alto"
            ]
        )


    # ============================================================
    # OBTENER ITEMS MARCADOS
    # ============================================================
    def obtener_items_marcados(
        self
    ):

        items = []

        for indice in range(
            self.lista_imagenes.count()
        ):

            item = self.lista_imagenes.item(
                indice
            )

            if (
                item.checkState()
                == Qt.CheckState.Checked
            ):

                items.append(
                    item
                )

        return items


    # ============================================================
    # CAMBIAR SELECCION DE TODAS
    # ============================================================
    def cambiar_seleccion_todas(
        self,
        marcada
    ):

        if self.actualizando_seleccion_total:

            return

        estado = (
            Qt.CheckState.Checked
            if marcada
            else Qt.CheckState.Unchecked
        )

        self.actualizando_seleccion_total = True

        try:

            for indice in range(
                self.lista_imagenes.count()
            ):

                self.lista_imagenes.item(
                    indice
                ).setCheckState(
                    estado
                )

        finally:

            self.actualizando_seleccion_total = False

        self.actualizar_check_seleccionar_todas()

        self.actualizar_resumen_lista()

        self.actualizar_estado_controles()


    # ============================================================
    # SELECCION DE ITEM CAMBIADA
    # ============================================================
    def seleccion_item_cambiada(
        self,
        item
    ):

        if self.actualizando_seleccion_total:

            return

        self.actualizar_check_seleccionar_todas()

        self.actualizar_resumen_lista()

        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR CHECK SELECCIONAR TODAS
    # ============================================================
    def actualizar_check_seleccionar_todas(
        self
    ):

        total = (
            self.lista_imagenes.count()
        )

        marcadas = len(
            self.obtener_items_marcados()
        )

        self.actualizando_seleccion_total = True

        try:

            if (
                total == 0
                or marcadas == 0
            ):

                self.check_seleccionar_todas.setCheckState(
                    Qt.CheckState.Unchecked
                )

            elif marcadas == total:

                self.check_seleccionar_todas.setCheckState(
                    Qt.CheckState.Checked
                )

            else:

                self.check_seleccionar_todas.setCheckState(
                    Qt.CheckState.PartiallyChecked
                )

        finally:

            self.actualizando_seleccion_total = False


    # ============================================================
    # OBTENER CONFIGURACION DE CONTROLES
    # ============================================================
    def obtener_configuracion_controles(
        self
    ):

        return {
            "tamano_pagina": (
                self.combo_tamano.currentData()
            ),
            "orientacion": (
                self.combo_orientacion.currentData()
            ),
            "ajuste": (
                self.combo_ajuste.currentData()
            ),
            "margen_mm": (
                self.campo_margen.value()
            ),
            "no_ampliar": (
                self.check_no_ampliar.isChecked()
            )
        }


    # ============================================================
    # CARGAR CONFIGURACION EN CONTROLES
    # ============================================================
    def cargar_configuracion_en_controles(
        self,
        configuracion
    ):

        self.actualizando_controles_diseno = True

        try:

            indice = self.combo_tamano.findData(
                configuracion[
                    "tamano_pagina"
                ]
            )

            if indice >= 0:

                self.combo_tamano.setCurrentIndex(
                    indice
                )

            indice = self.combo_orientacion.findData(
                configuracion[
                    "orientacion"
                ]
            )

            if indice >= 0:

                self.combo_orientacion.setCurrentIndex(
                    indice
                )

            indice = self.combo_ajuste.findData(
                configuracion[
                    "ajuste"
                ]
            )

            if indice >= 0:

                self.combo_ajuste.setCurrentIndex(
                    indice
                )

            self.campo_margen.setValue(
                float(
                    configuracion[
                        "margen_mm"
                    ]
                )
            )

            self.check_no_ampliar.setChecked(
                bool(
                    configuracion[
                        "no_ampliar"
                    ]
                )
            )

        finally:

            self.actualizando_controles_diseno = False

        self.actualizar_informacion_tamano()

        self.actualizar_configuracion_previsualizacion()


    # ============================================================
    # OBTENER CONFIGURACION DE ITEM
    # ============================================================
    def obtener_configuracion_item(
        self,
        item
    ):

        if item is None:

            return dict(
                self.configuracion_documento
            )

        configuracion = item.data(
            ROL_CONFIGURACION_PAGINA
        )

        if not isinstance(
            configuracion,
            dict
        ):

            configuracion = dict(
                self.configuracion_documento
            )

            item.setData(
                ROL_CONFIGURACION_PAGINA,
                configuracion
            )

        return dict(
            configuracion
        )


    # ============================================================
    # GUARDAR CONFIGURACION DE ITEM
    # ============================================================
    def guardar_configuracion_item(
        self,
        item,
        configuracion
    ):

        if item is None:

            return

        item.setData(
            ROL_CONFIGURACION_PAGINA,
            dict(
                configuracion
            )
        )


    # ============================================================
    # CAMBIAR AMBITO DE AJUSTES
    # ============================================================
    def cambiar_ambito_ajustes(
        self,
        *args
    ):

        if (
            self.combo_ambito.currentData()
            == AMBITO_PAGINA
        ):

            item = (
                self.lista_imagenes.currentItem()
            )

            if item is not None:

                configuracion = (
                    self.obtener_configuracion_item(
                        item
                    )
                )

                self.cargar_configuracion_en_controles(
                    configuracion
                )

        else:

            self.cargar_configuracion_en_controles(
                self.configuracion_documento
            )

        self.actualizar_texto_ambito()

        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR TEXTO DE AMBITO
    # ============================================================
    def actualizar_texto_ambito(
        self
    ):

        if (
            self.combo_ambito.currentData()
            == AMBITO_PAGINA
        ):

            fila = (
                self.lista_imagenes.currentRow()
            )

            total = (
                self.lista_imagenes.count()
            )

            if (
                fila >= 0
                and total > 0
            ):

                self.etiqueta_ambito.setText(
                    (
                        f"Editando únicamente la "
                        f"página {fila + 1} de {total}."
                    )
                )

            else:

                self.etiqueta_ambito.setText(
                    "Selecciona una página para editarla."
                )

        else:

            self.etiqueta_ambito.setText(
                (
                    "Los cambios de diseño se aplicarán "
                    "a todas las páginas."
                )
            )


    # ============================================================
    # ACTUALIZAR INFORMACION DEL TAMANO
    # ============================================================
    def actualizar_informacion_tamano(
        self
    ):

        tamano = (
            self.combo_tamano.currentData()
        )

        orientacion = (
            self.combo_orientacion.currentData()
        )

        if tamano == TAMANO_AUTOMATICO:

            self.etiqueta_tamano_info.setText(
                (
                    "El tamaño automático usa las dimensiones "
                    "de cada imagen y añade el margen configurado."
                )
            )

            return

        ancho, alto = TAMANOS_PAGINA_MM[
            tamano
        ]

        if orientacion == ORIENTACION_VERTICAL:

            ancho_final = min(
                ancho,
                alto
            )

            alto_final = max(
                ancho,
                alto
            )

            texto_orientacion = (
                "vertical"
            )

        elif orientacion == ORIENTACION_HORIZONTAL:

            ancho_final = max(
                ancho,
                alto
            )

            alto_final = min(
                ancho,
                alto
            )

            texto_orientacion = (
                "horizontal"
            )

        else:

            ancho_final = ancho

            alto_final = alto

            texto_orientacion = (
                "orientación automática"
            )

        self.etiqueta_tamano_info.setText(
            (
                f"Página: "
                f"{formatear_dimension_mm(ancho_final)} × "
                f"{formatear_dimension_mm(alto_final)} mm · "
                f"{texto_orientacion}."
            )
        )


    # ============================================================
    # AJUSTES DE DISENO CAMBIADOS
    # ============================================================
    def ajustes_diseno_cambiados(
        self,
        *args
    ):

        if self.actualizando_controles_diseno:

            return

        configuracion = (
            self.obtener_configuracion_controles()
        )

        if (
            self.combo_ambito.currentData()
            == AMBITO_PAGINA
        ):

            item = (
                self.lista_imagenes.currentItem()
            )

            if item is not None:

                self.guardar_configuracion_item(
                    item,
                    configuracion
                )

        else:

            self.configuracion_documento = dict(
                configuracion
            )

            for indice in range(
                self.lista_imagenes.count()
            ):

                item = (
                    self.lista_imagenes.item(
                        indice
                    )
                )

                self.guardar_configuracion_item(
                    item,
                    configuracion
                )

        self.actualizar_informacion_tamano()

        self.actualizar_configuracion_previsualizacion()


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

        for url in evento.mimeData().urls():

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
                "Imágenes (*.jpg *.jpeg *.png *.webp *.bmp "
                "*.gif *.tif *.tiff *.ico *.apng *.avif "
                "*.heic *.heif *.jxl *.jp2 *.j2k *.jxr "
                "*.qoi *.tga *.pcx *.pnm *.pbm *.pgm "
                "*.ppm *.pam *.hdr *.exr *.dpx *.dds "
                "*.psd);;"
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

        existentes = set()

        for indice in range(
            self.lista_imagenes.count()
        ):

            item = self.lista_imagenes.item(
                indice
            )

            ruta_existente = item.data(
                Qt.ItemDataRole.UserRole
            )

            if ruta_existente:

                existentes.add(
                    os.path.normcase(
                        os.path.abspath(
                            ruta_existente
                        )
                    )
                )

        errores = []

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

            texto = (
                f"{os.path.basename(ruta_absoluta)}"
                f"   ·   "
                f"{informacion['ancho']} × "
                f"{informacion['alto']} px"
                f"   ·   "
                f"{formatear_tamano(informacion['tamano'])}"
            )

            item = QListWidgetItem(
                texto
            )

            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
            )

            item.setCheckState(
                Qt.CheckState.Unchecked
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                ruta_absoluta
            )

            item.setData(
                ROL_CONFIGURACION_PAGINA,
                dict(
                    self.configuracion_documento
                )
            )

            item.setData(
                ROL_INFORMACION_IMAGEN,
                dict(
                    informacion
                )
            )

            item.setToolTip(
                ruta_absoluta
            )

            self.lista_imagenes.addItem(
                item
            )

            existentes.add(
                clave
            )

        if (
            self.lista_imagenes.count() > 0
            and self.lista_imagenes.currentRow() < 0
        ):

            self.lista_imagenes.setCurrentRow(
                0
            )

        if (
            self.ruta_salida is None
            and self.lista_imagenes.count() > 0
        ):

            primera_ruta = (
                self.lista_imagenes.item(
                    0
                ).data(
                    Qt.ItemDataRole.UserRole
                )
            )

            carpeta = os.path.dirname(
                primera_ruta
            )

            nombre = os.path.splitext(
                os.path.basename(
                    primera_ruta
                )
            )[0]

            self.ruta_salida = os.path.join(
                carpeta,
                (
                    f"{nombre}_imagenes.pdf"
                )
            )

            self.campo_salida.setText(
                self.ruta_salida
            )

        self.actualizar_check_seleccionar_todas()

        self.actualizar_resumen_lista()

        self.actualizar_texto_ambito()

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
    # OBTENER RUTAS ORDENADAS
    # ============================================================
    def obtener_rutas_ordenadas(
        self
    ):

        rutas = []

        for indice in range(
            self.lista_imagenes.count()
        ):

            item = self.lista_imagenes.item(
                indice
            )

            rutas.append(
                item.data(
                    Qt.ItemDataRole.UserRole
                )
            )

        return rutas


    # ============================================================
    # OBTENER CONFIGURACIONES ORDENADAS
    # ============================================================
    def obtener_configuraciones_ordenadas(
        self
    ):

        configuraciones = []

        for indice in range(
            self.lista_imagenes.count()
        ):

            item = self.lista_imagenes.item(
                indice
            )

            configuraciones.append(
                self.obtener_configuracion_item(
                    item
                )
            )

        return configuraciones


    # ============================================================
    # QUITAR SELECCIONADAS
    # ============================================================
    def quitar_seleccionadas(
        self
    ):

        items_marcados = (
            self.obtener_items_marcados()
        )

        if not items_marcados:

            return

        filas = sorted(
            {
                self.lista_imagenes.row(
                    item
                )
                for item in items_marcados
            },
            reverse=True
        )

        fila_actual = (
            self.lista_imagenes.currentRow()
        )

        for fila in filas:

            item = self.lista_imagenes.item(
                fila
            )

            if item is not None:

                ruta = item.data(
                    Qt.ItemDataRole.UserRole
                )

                self.eliminar_previsualizacion_cache(
                    ruta
                )

            self.lista_imagenes.takeItem(
                fila
            )

        if self.lista_imagenes.count() == 0:

            self.temporizador_previsualizacion.stop()

            self.item_previsualizacion_pendiente = None

            self.vista_previa.limpiar()

            self.etiqueta_info_imagen.setText(
                (
                    "La fila resaltada es la página activa. "
                    "Usa las casillas de la derecha para "
                    "seleccionar varias."
                )
            )

        else:

            nueva_fila = min(
                max(
                    0,
                    fila_actual
                ),
                self.lista_imagenes.count()
                - 1
            )

            self.lista_imagenes.setCurrentRow(
                nueva_fila
            )

        self.actualizar_check_seleccionar_todas()

        self.actualizar_resumen_lista()

        self.actualizar_texto_ambito()

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

        self.lista_imagenes.clear()

        self.vista_previa.limpiar()

        self.etiqueta_info_imagen.setText(
            (
                "La fila resaltada es la página activa. "
                "Usa las casillas de la derecha para "
                "seleccionar varias."
            )
        )

        self.ocultar_resultado_temporal()

        self.actualizar_check_seleccionar_todas()

        self.actualizar_resumen_lista()

        self.actualizar_texto_ambito()

        self.actualizar_estado_controles()


    # ============================================================
    # ORDEN DE LISTA CAMBIADO
    # ============================================================
    def orden_lista_cambiado(
        self
    ):

        self.actualizar_check_seleccionar_todas()

        self.actualizar_resumen_lista()

        self.actualizar_texto_ambito()

        self.actualizar_previsualizacion(
            self.lista_imagenes.currentItem(),
            None
        )


    # ============================================================
    # ACTUALIZAR RESUMEN
    # ============================================================
    def actualizar_resumen_lista(
        self
    ):

        cantidad = (
            self.lista_imagenes.count()
        )

        seleccionadas = len(
            self.obtener_items_marcados()
        )

        if cantidad == 0:

            texto = (
                "0 imágenes"
            )

        elif cantidad == 1:

            texto = (
                "1 imagen · 1 página"
            )

        else:

            texto = (
                f"{cantidad} imágenes · "
                f"{cantidad} páginas"
            )

        if seleccionadas == 1:

            texto += (
                " · 1 seleccionada"
            )

        elif seleccionadas > 1:

            texto += (
                f" · {seleccionadas} seleccionadas"
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

            self.actualizar_texto_ambito()

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

        fila = self.lista_imagenes.row(
            item_actual
        )

        self.etiqueta_info_imagen.setText(
            (
                f"Página {fila + 1} · "
                f"{os.path.basename(ruta)} · "
                f"{informacion['ancho']} × "
                f"{informacion['alto']} px · "
                f"{formatear_tamano(informacion['tamano'])}"
            )
        )


        # ----------------------------------- #
        #        Vista ya almacenada          #
        # ----------------------------------- #

        pixmap_cache = (
            self.obtener_previsualizacion_cache(
                ruta
            )
        )

        if pixmap_cache is not None:

            self.vista_previa.establecer_imagen(
                pixmap_cache,
                informacion[
                    "ancho"
                ],
                informacion[
                    "alto"
                ]
            )

        else:

            self.item_previsualizacion_pendiente = (
                item_actual
            )

            self.temporizador_previsualizacion.start()


        # ----------------------------------- #
        #       Configuracion de pagina       #
        # ----------------------------------- #

        if (
            self.combo_ambito.currentData()
            == AMBITO_PAGINA
        ):

            configuracion = (
                self.obtener_configuracion_item(
                    item_actual
                )
            )

            self.cargar_configuracion_en_controles(
                configuracion
            )

        else:

            self.actualizar_configuracion_previsualizacion()

        self.actualizar_texto_ambito()

        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR CONFIGURACION DE PREVISUALIZACION
    # ============================================================
    def actualizar_configuracion_previsualizacion(
        self,
        *args
    ):

        item = (
            self.lista_imagenes.currentItem()
        )

        if item is None:

            configuracion = dict(
                self.configuracion_documento
            )

        else:

            configuracion = (
                self.obtener_configuracion_item(
                    item
                )
            )

        resolucion = (
            self.combo_resolucion.currentData()
        )

        if resolucion is None:

            resolucion = 200

        self.vista_previa.establecer_configuracion(
            configuracion[
                "tamano_pagina"
            ],
            configuracion[
                "orientacion"
            ],
            configuracion[
                "ajuste"
            ],
            configuracion[
                "margen_mm"
            ],
            configuracion[
                "no_ampliar"
            ],
            resolucion
        )


    # ============================================================
    # SELECCIONAR SALIDA
    # ============================================================
    def seleccionar_salida(
        self
    ):

        ruta_inicial = (
            self.ruta_salida
            or os.path.join(
                os.path.expanduser(
                    "~"
                ),
                "imagenes.pdf"
            )
        )

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF como",
            ruta_inicial,
            "Documento PDF (*.pdf)"
        )

        if not ruta:

            return

        if not ruta.lower().endswith(
            ".pdf"
        ):

            ruta += ".pdf"

        self.ruta_salida = os.path.abspath(
            ruta
        )

        self.campo_salida.setText(
            self.ruta_salida
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
    # AVANZAR TEMPORIZADOR
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
    # ACTUALIZAR ESTADO DE CONTROLES
    # ============================================================
    def actualizar_estado_controles(
        self
    ):

        hay_imagenes = (
            self.lista_imagenes.count()
            > 0
        )

        hay_pagina_actual = (
            self.lista_imagenes.currentItem()
            is not None
        )

        hay_seleccionadas = bool(
            self.obtener_items_marcados()
        )

        procesando = (
            self.hilo is not None
        )

        self.boton_agregar.setEnabled(
            not procesando
        )

        self.boton_quitar.setEnabled(
            hay_seleccionadas
            and not procesando
        )

        self.boton_limpiar.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.lista_imagenes.setEnabled(
            not procesando
        )

        self.etiqueta_seleccionar_todas.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.check_seleccionar_todas.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.combo_ambito.setEnabled(
            hay_imagenes
            and not procesando
        )

        ambito_pagina = (
            self.combo_ambito.currentData()
            == AMBITO_PAGINA
        )

        habilitar_diseno = (
            hay_imagenes
            and not procesando
            and (
                not ambito_pagina
                or hay_pagina_actual
            )
        )

        for control in (
            self.combo_tamano,
            self.combo_orientacion,
            self.combo_ajuste,
            self.campo_margen,
            self.check_no_ampliar
        ):

            control.setEnabled(
                habilitar_diseno
            )

        for control in (
            self.combo_resolucion,
            self.campo_calidad,
            self.boton_salida
        ):

            control.setEnabled(
                hay_imagenes
                and not procesando
            )

        self.boton_crear.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.boton_cancelar.setEnabled(
            procesando
        )


    # ============================================================
    # INICIAR CREACION DEL PDF
    # ============================================================
    def iniciar_creacion_pdf(
        self
    ):

        rutas = (
            self.obtener_rutas_ordenadas()
        )

        if not rutas:

            return

        configuraciones = (
            self.obtener_configuraciones_ordenadas()
        )

        if not self.ruta_salida:

            self.seleccionar_salida()

            if not self.ruta_salida:

                return

        if os.path.exists(
            self.ruta_salida
        ):

            respuesta = QMessageBox.question(
                self,
                "Reemplazar PDF",
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

        self.trabajador = TrabajadorImagenesAPDF(
            rutas,
            configuraciones,
            self.ruta_salida,
            self.combo_resolucion.currentData(),
            self.campo_calidad.value()
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
            self.creacion_terminada
        )

        self.trabajador.cancelado.connect(
            self.creacion_cancelada
        )

        self.trabajador.error.connect(
            self.error_creacion
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
    # CANCELAR CREACION
    # ============================================================
    def cancelar_creacion_pdf(
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
    # CREACION TERMINADA
    # ============================================================
    @Slot(
        object
    )
    def creacion_terminada(
        self,
        resultado
    ):

        self.barra_progreso.setValue(
            100
        )

        self.etiqueta_estado.setText(
            "Completado"
        )

        paginas = resultado[
            "paginas"
        ]

        texto_paginas = (
            "1 página"
            if paginas == 1
            else f"{paginas} páginas"
        )

        self.mostrar_resultado_temporal(
            (
                f"PDF creado correctamente · "
                f"{texto_paginas} · "
                f"{formatear_tamano(resultado['tamano'])}\n"
                f"{resultado['ruta']}"
            )
        )


    # ============================================================
    # CREACION CANCELADA
    # ============================================================
    @Slot()
    def creacion_cancelada(
        self
    ):

        self.etiqueta_estado.setText(
            "Cancelado"
        )


    # ============================================================
    # ERROR DE CREACION
    # ============================================================
    @Slot(
        str
    )
    def error_creacion(
        self,
        mensaje
    ):

        self.etiqueta_estado.setText(
            "Error"
        )

        QMessageBox.critical(
            self,
            "Error al crear el PDF",
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