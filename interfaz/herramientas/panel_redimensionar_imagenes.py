import os

from PIL import (
    Image,
    ImageOps
)

from PIL.ImageQt import toqpixmap

from PySide6.QtCore import (
    Qt,
    QRectF,
    Signal,
    Slot,
    QObject,
    QThread,
    QTimer
)

from PySide6.QtGui import (
    QColor,
    QBrush,
    QCursor,
    QPainter,
    QPen,
    QPixmap,
    QShortcut,
    QKeySequence
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
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QSizePolicy,
    QDialog
)

from herramientas.imagenes.redimensionar_imagenes import (
    MODO_EXACTO,
    generar_ruta_salida,
    obtener_dimensiones_imagen,
    redimensionar_imagen
)


# ----------------------------------- #
#             Unidades                #
# ----------------------------------- #

UNIDAD_PIXELES = "px"
UNIDAD_PORCENTAJE = "porcentaje"
UNIDAD_CENTIMETROS = "cm"


# ================================================================
# CARGAR PREVISUALIZACION
# ================================================================
def cargar_pixmap_previsualizacion(
    ruta_imagen
):

    pixmap = QPixmap(
        ruta_imagen
    )

    if not pixmap.isNull():

        return pixmap

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

            imagen = ImageOps.exif_transpose(
                imagen
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
# OBTENER DPI
# ================================================================
def obtener_dpi_imagen(
    ruta_imagen
):

    try:

        with Image.open(
            ruta_imagen
        ) as imagen:

            dpi = imagen.info.get(
                "dpi"
            )

            if isinstance(
                dpi,
                (
                    tuple,
                    list
                )
            ) and dpi:

                valores = []

                for valor in dpi[:2]:

                    try:

                        valor = float(
                            valor
                        )

                    except (
                        TypeError,
                        ValueError
                    ):

                        continue

                    if valor > 0:

                        valores.append(
                            valor
                        )

                if valores:

                    return (
                        sum(
                            valores
                        )
                        / len(
                            valores
                        )
                    ), True

            if isinstance(
                dpi,
                (
                    int,
                    float
                )
            ) and dpi > 0:

                return float(
                    dpi
                ), True

    except Exception:

        pass

    return 96.0, False


# ================================================================
# VISTA REDIMENSIONABLE
# ================================================================
class VistaRedimensionable(
    QWidget
):

    dimensiones_cambiadas = Signal(
        int,
        int
    )

    TAMANO_TIRADOR = 12

    MARGEN_VISUAL = 42

    ESCALA_BASE_ORIGINAL = 0.56

    ZOOM_MINIMO = 0.03

    ZOOM_MAXIMO = 30.0

    PASO_ZOOM = 1.12


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

        self.setMouseTracking(
            True
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        self.setMinimumSize(
            420,
            280
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.pixmap = QPixmap()

        self.ancho_original = 1

        self.alto_original = 1

        self.ancho_objetivo = 1

        self.alto_objetivo = 1

        self.mantener_proporcion = True

        self.zoom_visual = 1.0

        self.tirador_activo = None

        self.posicion_inicial = None

        self.ancho_inicial = 1

        self.alto_inicial = 1

        self.rectangulo_inicial = QRectF()


    # ============================================================
    # ESTABLECER IMAGEN
    # ============================================================
    def establecer_imagen(
        self,
        pixmap,
        ancho_original,
        alto_original
    ):

        self.pixmap = pixmap

        self.ancho_original = max(
            1,
            int(
                ancho_original
            )
        )

        self.alto_original = max(
            1,
            int(
                alto_original
            )
        )

        self.ancho_objetivo = (
            self.ancho_original
        )

        self.alto_objetivo = (
            self.alto_original
        )

        self.zoom_visual = 1.0

        self.update()


    # ============================================================
    # LIMPIAR
    # ============================================================
    def limpiar(
        self
    ):

        self.pixmap = QPixmap()

        self.ancho_original = 1

        self.alto_original = 1

        self.ancho_objetivo = 1

        self.alto_objetivo = 1

        self.zoom_visual = 1.0

        self.update()


    # ============================================================
    # ESTABLECER DIMENSIONES
    # ============================================================
    def establecer_dimensiones(
        self,
        ancho,
        alto,
        emitir=False
    ):

        ancho = max(
            1,
            int(
                round(
                    ancho
                )
            )
        )

        alto = max(
            1,
            int(
                round(
                    alto
                )
            )
        )

        if (
            ancho == self.ancho_objetivo
            and alto == self.alto_objetivo
        ):

            return

        self.ancho_objetivo = ancho

        self.alto_objetivo = alto

        self.update()

        if emitir:

            self.dimensiones_cambiadas.emit(
                ancho,
                alto
            )


    # ============================================================
    # ESTABLECER BLOQUEO DE PROPORCION
    # ============================================================
    def establecer_mantener_proporcion(
        self,
        mantener
    ):

        self.mantener_proporcion = bool(
            mantener
        )

        self.update()


    # ============================================================
    # ESTABLECER ZOOM VISUAL
    # ============================================================
    def establecer_zoom_visual(
        self,
        zoom
    ):

        self.zoom_visual = max(
            self.ZOOM_MINIMO,
            min(
                self.ZOOM_MAXIMO,
                float(
                    zoom
                )
            )
        )

        self.update()


    # ============================================================
    # OBTENER ZOOM VISUAL
    # ============================================================
    def obtener_zoom_visual(
        self
    ):

        return self.zoom_visual


    # ============================================================
    # RESTABLECER ZOOM
    # ============================================================
    def restablecer_zoom(
        self
    ):

        self.establecer_zoom_visual(
            1.0
        )


    # ============================================================
    # OBTENER AREA DISPONIBLE
    # ============================================================
    def obtener_area_disponible(
        self
    ):

        return (
            max(
                1.0,
                self.width()
                - self.MARGEN_VISUAL
                * 2
            ),
            max(
                1.0,
                self.height()
                - self.MARGEN_VISUAL
                * 2
            )
        )


    # ============================================================
    # OBTENER ESCALA BASE
    # ============================================================
    def obtener_escala_base(
        self
    ):

        (
            ancho_disponible,
            alto_disponible
        ) = self.obtener_area_disponible()

        escala_original = min(
            ancho_disponible
            / max(
                1,
                self.ancho_original
            ),
            alto_disponible
            / max(
                1,
                self.alto_original
            )
        )

        return max(
            0.000001,
            escala_original
            * self.ESCALA_BASE_ORIGINAL
        )


    # ============================================================
    # OBTENER ESCALA VISUAL
    # ============================================================
    def obtener_escala_visual(
        self
    ):

        return (
            self.obtener_escala_base()
            * self.zoom_visual
        )


    # ============================================================
    # AJUSTAR TAMANO ACTUAL A LA VISTA
    # ============================================================
    def ajustar_objetivo_a_vista(
        self
    ):

        if self.pixmap.isNull():

            return

        (
            ancho_disponible,
            alto_disponible
        ) = self.obtener_area_disponible()

        escala_base = (
            self.obtener_escala_base()
        )

        ancho_base = (
            self.ancho_objetivo
            * escala_base
        )

        alto_base = (
            self.alto_objetivo
            * escala_base
        )

        if (
            ancho_base <= 0
            or alto_base <= 0
        ):

            return

        zoom = min(
            ancho_disponible
            * 0.90
            / ancho_base,
            alto_disponible
            * 0.88
            / alto_base
        )

        self.establecer_zoom_visual(
            zoom
        )


    # ============================================================
    # OBTENER RECTANGULO SEGUN DIMENSIONES
    # ============================================================
    def obtener_rectangulo_dimensiones(
        self,
        ancho_pixels,
        alto_pixels
    ):

        escala = (
            self.obtener_escala_visual()
        )

        ancho = max(
            4.0,
            ancho_pixels
            * escala
        )

        alto = max(
            4.0,
            alto_pixels
            * escala
        )

        centro = (
            self.rect().center()
        )

        return QRectF(
            centro.x()
            - ancho / 2,
            centro.y()
            - alto / 2,
            ancho,
            alto
        )


    # ============================================================
    # OBTENER RECTANGULO OBJETIVO
    # ============================================================
    def obtener_rectangulo_objetivo(
        self
    ):

        return self.obtener_rectangulo_dimensiones(
            self.ancho_objetivo,
            self.alto_objetivo
        )


    # ============================================================
    # OBTENER RECTANGULO PUNTEADO
    # ============================================================
    def obtener_rectangulo_punteado(
        self
    ):

        return (
            self.obtener_rectangulo_objetivo()
            .adjusted(
                -8,
                -8,
                8,
                8
            )
        )


    # ============================================================
    # OBTENER TIRADORES
    # ============================================================
    def obtener_tiradores(
        self,
        rectangulo=None
    ):

        if rectangulo is None:

            rectangulo = (
                self.obtener_rectangulo_objetivo()
            )

        x_izquierda = rectangulo.left()

        x_centro = rectangulo.center().x()

        x_derecha = rectangulo.right()

        y_arriba = rectangulo.top()

        y_centro = rectangulo.center().y()

        y_abajo = rectangulo.bottom()

        mitad = (
            self.TAMANO_TIRADOR
            / 2
        )

        posiciones = {
            "arriba_izquierda": (
                x_izquierda,
                y_arriba
            ),
            "arriba": (
                x_centro,
                y_arriba
            ),
            "arriba_derecha": (
                x_derecha,
                y_arriba
            ),
            "derecha": (
                x_derecha,
                y_centro
            ),
            "abajo_derecha": (
                x_derecha,
                y_abajo
            ),
            "abajo": (
                x_centro,
                y_abajo
            ),
            "abajo_izquierda": (
                x_izquierda,
                y_abajo
            ),
            "izquierda": (
                x_izquierda,
                y_centro
            )
        }

        return {
            nombre: QRectF(
                x - mitad,
                y - mitad,
                self.TAMANO_TIRADOR,
                self.TAMANO_TIRADOR
            )
            for nombre, (
                x,
                y
            ) in posiciones.items()
        }


    # ============================================================
    # BUSCAR TIRADOR
    # ============================================================
    def buscar_tirador(
        self,
        posicion
    ):

        for (
            nombre,
            rectangulo
        ) in self.obtener_tiradores().items():

            if rectangulo.adjusted(
                -4,
                -4,
                4,
                4
            ).contains(
                posicion
            ):

                return nombre

        return None


    # ============================================================
    # CURSOR PARA TIRADOR
    # ============================================================
    def cursor_para_tirador(
        self,
        tirador
    ):

        if tirador in {
            "izquierda",
            "derecha"
        }:

            return (
                Qt.CursorShape.SizeHorCursor
            )

        if tirador in {
            "arriba",
            "abajo"
        }:

            return (
                Qt.CursorShape.SizeVerCursor
            )

        if tirador in {
            "arriba_izquierda",
            "abajo_derecha"
        }:

            return (
                Qt.CursorShape.SizeFDiagCursor
            )

        if tirador in {
            "arriba_derecha",
            "abajo_izquierda"
        }:

            return (
                Qt.CursorShape.SizeBDiagCursor
            )

        return (
            Qt.CursorShape.ArrowCursor
        )


    # ============================================================
    # DIBUJAR FONDO AJEDREZADO
    # ============================================================
    def dibujar_fondo_ajedrezado(
        self,
        painter
    ):

        tamano = 18

        color_1 = QColor(
            42,
            42,
            42
        )

        color_2 = QColor(
            52,
            52,
            52
        )

        for y in range(
            0,
            self.height(),
            tamano
        ):

            for x in range(
                0,
                self.width(),
                tamano
            ):

                color = (
                    color_1
                    if (
                        x // tamano
                        + y // tamano
                    ) % 2 == 0
                    else color_2
                )

                painter.fillRect(
                    x,
                    y,
                    tamano,
                    tamano,
                    color
                )


    # ============================================================
    # OBTENER PORCENTAJE OBJETIVO
    # ============================================================
    def obtener_porcentaje_objetivo(
        self
    ):

        porcentaje_ancho = (
            self.ancho_objetivo
            / max(
                1,
                self.ancho_original
            )
            * 100
        )

        porcentaje_alto = (
            self.alto_objetivo
            / max(
                1,
                self.alto_original
            )
            * 100
        )

        if self.mantener_proporcion:

            return porcentaje_ancho

        return (
            porcentaje_ancho,
            porcentaje_alto
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

        self.dibujar_fondo_ajedrezado(
            painter
        )

        if self.pixmap.isNull():

            painter.setPen(
                QColor(
                    190,
                    190,
                    190
                )
            )

            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Selecciona una imagen para comenzar"
            )

            return

        rect_objetivo = (
            self.obtener_rectangulo_objetivo()
        )

        rect_punteado = (
            self.obtener_rectangulo_punteado()
        )

        painter.setPen(
            QPen(
                QColor(
                    175,
                    175,
                    175,
                    210
                ),
                1.4,
                Qt.PenStyle.DashLine
            )
        )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.drawRect(
            rect_punteado
        )

        painter.drawPixmap(
            rect_objetivo,
            self.pixmap,
            QRectF(
                self.pixmap.rect()
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    75,
                    160,
                    255
                ),
                2
            )
        )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.drawRect(
            rect_objetivo
        )

        painter.setPen(
            QPen(
                QColor(
                    235,
                    235,
                    235
                ),
                1
            )
        )

        painter.setBrush(
            QBrush(
                QColor(
                    75,
                    160,
                    255
                )
            )
        )

        for rectangulo in (
            self.obtener_tiradores(
                rect_objetivo
            ).values()
        ):

            painter.drawRoundedRect(
                rectangulo,
                2,
                2
            )

        painter.setPen(
            QColor(
                230,
                230,
                230
            )
        )

        porcentaje = (
            self.obtener_porcentaje_objetivo()
        )

        if isinstance(
            porcentaje,
            tuple
        ):

            texto_porcentaje = (
                f"{porcentaje[0]:.1f}% × "
                f"{porcentaje[1]:.1f}%"
            )

        else:

            texto_porcentaje = (
                f"{porcentaje:.1f}%"
            )

        texto = (
            f"{self.ancho_objetivo} × "
            f"{self.alto_objetivo} px"
            f"   ·   {texto_porcentaje}"
            f"   ·   Zoom "
            f"{self.zoom_visual * 100:.0f}%"
        )

        painter.drawText(
            self.rect().adjusted(
                12,
                12,
                -12,
                -12
            ),
            (
                Qt.AlignmentFlag.AlignBottom
                | Qt.AlignmentFlag.AlignHCenter
            ),
            texto
        )

        painter.setPen(
            QColor(
                180,
                180,
                180
            )
        )

        painter.drawText(
            self.rect().adjusted(
                12,
                12,
                -12,
                -12
            ),
            (
                Qt.AlignmentFlag.AlignTop
                | Qt.AlignmentFlag.AlignRight
            ),
            "Rueda: acercar / alejar"
        )


    # ============================================================
    # RUEDA DEL MOUSE
    # ============================================================
    def wheelEvent(
        self,
        evento
    ):

        if self.pixmap.isNull():

            super().wheelEvent(
                evento
            )

            return

        delta = (
            evento.angleDelta().y()
        )

        if delta == 0:

            super().wheelEvent(
                evento
            )

            return

        if delta > 0:

            nuevo_zoom = (
                self.zoom_visual
                * self.PASO_ZOOM
            )

        else:

            nuevo_zoom = (
                self.zoom_visual
                / self.PASO_ZOOM
            )

        self.establecer_zoom_visual(
            nuevo_zoom
        )

        evento.accept()


    # ============================================================
    # DOBLE CLIC
    # ============================================================
    def mouseDoubleClickEvent(
        self,
        evento
    ):

        if (
            evento.button()
            == Qt.MouseButton.LeftButton
            and not self.pixmap.isNull()
        ):

            self.ajustar_objetivo_a_vista()

            evento.accept()

            return

        super().mouseDoubleClickEvent(
            evento
        )


    # ============================================================
    # PRESIONAR MOUSE
    # ============================================================
    def mousePressEvent(
        self,
        evento
    ):

        if (
            evento.button()
            != Qt.MouseButton.LeftButton
            or self.pixmap.isNull()
        ):

            super().mousePressEvent(
                evento
            )

            return

        tirador = self.buscar_tirador(
            evento.position()
        )

        if tirador is None:

            super().mousePressEvent(
                evento
            )

            return

        self.tirador_activo = tirador

        self.posicion_inicial = (
            evento.position()
        )

        self.ancho_inicial = (
            self.ancho_objetivo
        )

        self.alto_inicial = (
            self.alto_objetivo
        )

        self.rectangulo_inicial = (
            self.obtener_rectangulo_objetivo()
        )

        evento.accept()


    # ============================================================
    # MOVER MOUSE
    # ============================================================
    def mouseMoveEvent(
        self,
        evento
    ):

        if self.tirador_activo is None:

            tirador = self.buscar_tirador(
                evento.position()
            )

            self.setCursor(
                QCursor(
                    self.cursor_para_tirador(
                        tirador
                    )
                )
            )

            super().mouseMoveEvent(
                evento
            )

            return

        delta = (
            evento.position()
            - self.posicion_inicial
        )

        escala_x = (
            self.ancho_inicial
            / max(
                1.0,
                self.rectangulo_inicial.width()
            )
        )

        escala_y = (
            self.alto_inicial
            / max(
                1.0,
                self.rectangulo_inicial.height()
            )
        )

        nuevo_ancho = float(
            self.ancho_inicial
        )

        nuevo_alto = float(
            self.alto_inicial
        )

        tirador = (
            self.tirador_activo
        )

        if "derecha" in tirador:

            nuevo_ancho += (
                delta.x()
                * escala_x
                * 2
            )

        if "izquierda" in tirador:

            nuevo_ancho -= (
                delta.x()
                * escala_x
                * 2
            )

        if "abajo" in tirador:

            nuevo_alto += (
                delta.y()
                * escala_y
                * 2
            )

        if "arriba" in tirador:

            nuevo_alto -= (
                delta.y()
                * escala_y
                * 2
            )

        nuevo_ancho = max(
            1.0,
            nuevo_ancho
        )

        nuevo_alto = max(
            1.0,
            nuevo_alto
        )

        if self.mantener_proporcion:

            relacion = (
                self.ancho_original
                / max(
                    1,
                    self.alto_original
                )
            )

            es_horizontal = (
                "izquierda" in tirador
                or "derecha" in tirador
            )

            es_vertical = (
                "arriba" in tirador
                or "abajo" in tirador
            )

            if (
                es_horizontal
                and not es_vertical
            ):

                nuevo_alto = (
                    nuevo_ancho
                    / relacion
                )

            elif (
                es_vertical
                and not es_horizontal
            ):

                nuevo_ancho = (
                    nuevo_alto
                    * relacion
                )

            else:

                cambio_ancho = abs(
                    nuevo_ancho
                    / max(
                        1,
                        self.ancho_inicial
                    )
                    - 1
                )

                cambio_alto = abs(
                    nuevo_alto
                    / max(
                        1,
                        self.alto_inicial
                    )
                    - 1
                )

                if (
                    cambio_ancho
                    >= cambio_alto
                ):

                    nuevo_alto = (
                        nuevo_ancho
                        / relacion
                    )

                else:

                    nuevo_ancho = (
                        nuevo_alto
                        * relacion
                    )

        self.establecer_dimensiones(
            nuevo_ancho,
            nuevo_alto,
            emitir=True
        )

        evento.accept()


    # ============================================================
    # SOLTAR MOUSE
    # ============================================================
    def mouseReleaseEvent(
        self,
        evento
    ):

        if (
            evento.button()
            == Qt.MouseButton.LeftButton
            and self.tirador_activo
            is not None
        ):

            self.tirador_activo = None

            self.posicion_inicial = None

            evento.accept()

            return

        super().mouseReleaseEvent(
            evento
        )


# ================================================================
# DIALOGO DE PREVISUALIZACION A PANTALLA COMPLETA
# ================================================================
class DialogoVistaCompleta(
    QDialog
):

    dimensiones_cambiadas = Signal(
        int,
        int
    )


    # ============================================================
    # INICIALIZACION
    # ============================================================
    def __init__(
        self,
        pixmap,
        ancho_original,
        alto_original,
        ancho_objetivo,
        alto_objetivo,
        mantener_proporcion,
        zoom_visual,
        pantalla_objetivo=None,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.pantalla_objetivo = (
            pantalla_objetivo
        )

        self.fullscreen_aplicado = False

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
        )

        self.setWindowTitle(
            "Previsualización - Redimensionar imágenes"
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

        self.vista.establecer_imagen(
            pixmap,
            ancho_original,
            alto_original
        )

        self.vista.establecer_mantener_proporcion(
            mantener_proporcion
        )

        self.vista.establecer_dimensiones(
            ancho_objetivo,
            alto_objetivo,
            emitir=False
        )

        self.vista.establecer_zoom_visual(
            zoom_visual
        )

        self.vista.dimensiones_cambiadas.connect(
            self.dimensiones_cambiadas.emit
        )

        self.atajo_escape = QShortcut(
            QKeySequence(
                "Esc"
            ),
            self
        )

        self.atajo_escape.activated.connect(
            self.accept
        )

        self.atajo_f11 = QShortcut(
            QKeySequence(
                "F11"
            ),
            self
        )

        self.atajo_f11.activated.connect(
            self.accept
        )


    # ============================================================
    # MOSTRAR DIALOGO
    # ============================================================
    def showEvent(
        self,
        evento
    ):

        super().showEvent(
            evento
        )

        if self.fullscreen_aplicado:

            return

        QTimer.singleShot(
            0,
            self.aplicar_pantalla_completa
        )


    # ============================================================
    # APLICAR PANTALLA COMPLETA
    # ============================================================
    def aplicar_pantalla_completa(
        self
    ):

        if self.fullscreen_aplicado:

            return

        self.fullscreen_aplicado = True

        pantalla = (
            self.pantalla_objetivo
            or self.screen()
        )

        if pantalla is not None:

            self.winId()

            ventana_nativa = (
                self.windowHandle()
            )

            if ventana_nativa is not None:

                try:

                    ventana_nativa.setScreen(
                        pantalla
                    )

                except Exception:

                    pass

            self.setGeometry(
                pantalla.geometry()
            )

        self.showFullScreen()

        self.raise_()

        self.activateWindow()

        self.vista.setFocus(
            Qt.FocusReason.ActiveWindowFocusReason
        )


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self
    ):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            12,
            10,
            12,
            12
        )

        layout.setSpacing(
            8
        )

        fila_superior = QHBoxLayout()

        etiqueta = QLabel(
            "Arrastra los bordes o esquinas para cambiar el tamaño"
        )

        etiqueta.setStyleSheet(
            "font-size: 14px;"
        )

        etiqueta_zoom = QLabel(
            "Rueda: zoom  ·  "
            "Doble clic: ajustar a la vista"
        )

        etiqueta_zoom.setStyleSheet(
            "color: #aaaaaa;"
        )

        boton_salir = QPushButton(
            "Salir de pantalla completa"
        )

        boton_salir.clicked.connect(
            self.accept
        )

        fila_superior.addWidget(
            etiqueta
        )

        fila_superior.addSpacing(
            18
        )

        fila_superior.addWidget(
            etiqueta_zoom
        )

        fila_superior.addStretch()

        fila_superior.addWidget(
            boton_salir
        )

        layout.addLayout(
            fila_superior
        )

        self.vista = VistaRedimensionable(
            self
        )

        self.vista.setMinimumSize(
            640,
            480
        )

        layout.addWidget(
            self.vista,
            1
        )


    # ============================================================
    # ESTABLECER DIMENSIONES
    # ============================================================
    def establecer_dimensiones(
        self,
        ancho,
        alto
    ):

        self.vista.establecer_dimensiones(
            ancho,
            alto,
            emitir=False
        )


# ================================================================
# TRABAJADOR DE REDIMENSIONADO
# ================================================================
class TrabajadorRedimensionarImagen(
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
        ruta_origen,
        ruta_destino,
        ancho,
        alto,
        evitar_ampliar,
        calidad
    ):

        super().__init__()

        self.ruta_origen = ruta_origen

        self.ruta_destino = ruta_destino

        self.ancho = ancho

        self.alto = alto

        self.evitar_ampliar = (
            evitar_ampliar
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

            resultado = redimensionar_imagen(
                self.ruta_origen,
                self.ruta_destino,
                modo=MODO_EXACTO,
                ancho=self.ancho,
                alto=self.alto,
                evitar_ampliar=(
                    self.evitar_ampliar
                ),
                calidad=self.calidad,
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
# PANEL REDIMENSIONAR IMAGENES
# ================================================================
class PanelRedimensionarImagenes(
    QWidget
):

    ANCHO_INICIAL = 980

    ALTO_INICIAL = 645

    ANCHO_MINIMO = 980

    ALTO_MINIMO = 645


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

        self.ruta_imagen = None

        self.carpeta_salida = None

        self.ancho_original = 1

        self.alto_original = 1

        self.ancho_objetivo = 1

        self.alto_objetivo = 1

        self.dpi = 96.0

        self.dpi_detectado = False

        self.unidad_actual = (
            UNIDAD_PIXELES
        )

        self.actualizando_campos = False

        self.hilo = None

        self.trabajador = None

        self.dialogo_pantalla_completa = None

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

        self.conectar_eventos()

        self.actualizar_estado_interfaz()


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
            10,
            18,
            12
        )

        layout_principal.setSpacing(
            7
        )

        titulo = QLabel(
            "Redimensionar imágenes"
        )

        titulo.setStyleSheet(
            "font-size: 21px; font-weight: 600;"
        )

        descripcion = QLabel(
            "Cambia el tamaño escribiendo valores o "
            "arrastrando los bordes de la previsualización."
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

        fila_archivo = QHBoxLayout()

        self.campo_archivo = QLineEdit()

        self.campo_archivo.setReadOnly(
            True
        )

        self.campo_archivo.setPlaceholderText(
            "Selecciona o arrastra una imagen aquí"
        )

        self.boton_seleccionar = QPushButton(
            "Seleccionar imagen"
        )

        fila_archivo.addWidget(
            self.campo_archivo,
            1
        )

        fila_archivo.addWidget(
            self.boton_seleccionar
        )

        layout_principal.addLayout(
            fila_archivo
        )

        fila_contenido = QHBoxLayout()

        fila_contenido.setSpacing(
            14
        )

        zona_previsualizacion = QWidget()

        layout_previsualizacion = QVBoxLayout(
            zona_previsualizacion
        )

        layout_previsualizacion.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout_previsualizacion.setSpacing(
            4
        )

        fila_previsualizacion = QHBoxLayout()

        etiqueta_previsualizacion = QLabel(
            "Previsualización"
        )

        etiqueta_previsualizacion.setStyleSheet(
            "font-weight: 600;"
        )

        self.boton_pantalla_completa = QPushButton(
            "⛶  Pantalla completa"
        )

        self.boton_pantalla_completa.setMaximumWidth(
            190
        )

        fila_previsualizacion.addWidget(
            etiqueta_previsualizacion
        )

        fila_previsualizacion.addStretch()

        fila_previsualizacion.addWidget(
            self.boton_pantalla_completa
        )

        layout_previsualizacion.addLayout(
            fila_previsualizacion
        )

        self.vista = VistaRedimensionable(
            self
        )

        layout_previsualizacion.addWidget(
            self.vista,
            1
        )

        fila_contenido.addWidget(
            zona_previsualizacion,
            3
        )

        self.panel_controles = QFrame()

        self.panel_controles.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        self.panel_controles.setMinimumWidth(
            345
        )

        self.panel_controles.setMaximumWidth(
            410
        )

        layout_controles = QVBoxLayout(
            self.panel_controles
        )

        layout_controles.setContentsMargins(
            16,
            10,
            16,
            10
        )

        layout_controles.setSpacing(
            8
        )

        etiqueta_original = QLabel(
            "Tamaño original"
        )

        etiqueta_original.setStyleSheet(
            "font-weight: 600;"
        )

        self.etiqueta_original = QLabel(
            "—"
        )

        layout_controles.addWidget(
            etiqueta_original
        )

        layout_controles.addWidget(
            self.etiqueta_original
        )

        etiqueta_unidades = QLabel(
            "Unidades"
        )

        etiqueta_unidades.setStyleSheet(
            "font-weight: 600;"
        )

        layout_controles.addWidget(
            etiqueta_unidades
        )

        fila_unidades = QHBoxLayout()

        self.radio_px = QRadioButton(
            "Píxeles"
        )

        self.radio_porcentaje = QRadioButton(
            "%"
        )

        self.radio_cm = QRadioButton(
            "cm"
        )

        self.radio_px.setChecked(
            True
        )

        self.grupo_unidades = QButtonGroup(
            self
        )

        self.grupo_unidades.addButton(
            self.radio_px
        )

        self.grupo_unidades.addButton(
            self.radio_porcentaje
        )

        self.grupo_unidades.addButton(
            self.radio_cm
        )

        fila_unidades.addWidget(
            self.radio_px
        )

        fila_unidades.addWidget(
            self.radio_porcentaje
        )

        fila_unidades.addWidget(
            self.radio_cm
        )

        fila_unidades.addStretch()

        layout_controles.addLayout(
            fila_unidades
        )

        cuadricula_dimensiones = QGridLayout()

        cuadricula_dimensiones.setHorizontalSpacing(
            10
        )

        cuadricula_dimensiones.setVerticalSpacing(
            5
        )

        cuadricula_dimensiones.addWidget(
            QLabel(
                "Ancho"
            ),
            0,
            0
        )

        cuadricula_dimensiones.addWidget(
            QLabel(
                "Alto"
            ),
            0,
            1
        )

        self.campo_ancho = QDoubleSpinBox()

        self.campo_alto = QDoubleSpinBox()

        for campo in (
            self.campo_ancho,
            self.campo_alto
        ):

            campo.setRange(
                1,
                100000
            )

            campo.setDecimals(
                0
            )

            campo.setSingleStep(
                1
            )

            campo.setSuffix(
                " px"
            )

        cuadricula_dimensiones.addWidget(
            self.campo_ancho,
            1,
            0
        )

        cuadricula_dimensiones.addWidget(
            self.campo_alto,
            1,
            1
        )

        layout_controles.addLayout(
            cuadricula_dimensiones
        )

        self.check_proporcion = QCheckBox(
            "Mantener proporción"
        )

        self.check_proporcion.setChecked(
            True
        )

        layout_controles.addWidget(
            self.check_proporcion
        )

        self.check_no_ampliar = QCheckBox(
            "No ampliar por encima del tamaño original"
        )

        layout_controles.addWidget(
            self.check_no_ampliar
        )

        fila_dpi = QHBoxLayout()

        self.etiqueta_dpi = QLabel(
            "PPI para centímetros"
        )

        self.campo_dpi = QSpinBox()

        self.campo_dpi.setRange(
            1,
            2400
        )

        self.campo_dpi.setValue(
            96
        )

        self.campo_dpi.setSuffix(
            " ppi"
        )

        fila_dpi.addWidget(
            self.etiqueta_dpi
        )

        fila_dpi.addStretch()

        fila_dpi.addWidget(
            self.campo_dpi
        )

        layout_controles.addLayout(
            fila_dpi
        )

        self.etiqueta_dpi_info = QLabel(
            ""
        )

        self.etiqueta_dpi_info.setWordWrap(
            True
        )

        self.etiqueta_dpi_info.setStyleSheet(
            "color: #9d9d9d; font-size: 12px;"
        )

        layout_controles.addWidget(
            self.etiqueta_dpi_info
        )

        fila_calidad = QHBoxLayout()

        fila_calidad.addWidget(
            QLabel(
                "Calidad de escalado"
            )
        )

        fila_calidad.addStretch()

        self.combo_calidad = QComboBox()

        self.combo_calidad.addItem(
            "Alta",
            "alta"
        )

        self.combo_calidad.addItem(
            "Media",
            "media"
        )

        self.combo_calidad.addItem(
            "Rápida",
            "rapida"
        )

        fila_calidad.addWidget(
            self.combo_calidad
        )

        layout_controles.addLayout(
            fila_calidad
        )

        self.boton_restablecer = QPushButton(
            "Restablecer tamaño original"
        )

        layout_controles.addWidget(
            self.boton_restablecer
        )

        layout_controles.addStretch()

        fila_contenido.addWidget(
            self.panel_controles,
            1
        )

        layout_principal.addLayout(
            fila_contenido,
            1
        )

        fila_salida = QHBoxLayout()

        self.campo_salida = QLineEdit()

        self.campo_salida.setReadOnly(
            True
        )

        self.campo_salida.setPlaceholderText(
            "Carpeta de salida"
        )

        self.boton_salida = QPushButton(
            "Elegir carpeta"
        )

        self.campo_sufijo = QLineEdit(
            "_redimensionada"
        )

        self.campo_sufijo.setMaximumWidth(
            180
        )

        self.campo_sufijo.setPlaceholderText(
            "Sufijo"
        )

        fila_salida.addWidget(
            QLabel(
                "Guardar en:"
            )
        )

        fila_salida.addWidget(
            self.campo_salida,
            1
        )

        fila_salida.addWidget(
            self.boton_salida
        )

        fila_salida.addWidget(
            QLabel(
                "Sufijo:"
            )
        )

        fila_salida.addWidget(
            self.campo_sufijo
        )

        layout_principal.addLayout(
            fila_salida
        )

        fila_progreso = QHBoxLayout()

        fila_progreso.setSpacing(
            9
        )

        self.etiqueta_estado = QLabel(
            ""
        )

        self.etiqueta_estado.setMinimumWidth(
            0
        )

        self.etiqueta_estado.setMaximumWidth(
            260
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

        self.boton_redimensionar = QPushButton(
            "Redimensionar imagen"
        )

        self.boton_redimensionar.setMinimumWidth(
            185
        )

        self.boton_redimensionar.setMinimumHeight(
            34
        )

        self.boton_cancelar = QPushButton(
            "Cancelar"
        )

        self.boton_cancelar.setMinimumWidth(
            95
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
            self.boton_redimensionar
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

        self.boton_seleccionar.clicked.connect(
            self.seleccionar_imagen
        )

        self.boton_salida.clicked.connect(
            self.seleccionar_carpeta_salida
        )

        self.boton_pantalla_completa.clicked.connect(
            self.abrir_pantalla_completa
        )

        self.radio_px.toggled.connect(
            self.cambiar_unidad
        )

        self.radio_porcentaje.toggled.connect(
            self.cambiar_unidad
        )

        self.radio_cm.toggled.connect(
            self.cambiar_unidad
        )

        self.campo_ancho.valueChanged.connect(
            lambda valor:
            self.cambiar_dimension_desde_campo(
                "ancho",
                valor
            )
        )

        self.campo_alto.valueChanged.connect(
            lambda valor:
            self.cambiar_dimension_desde_campo(
                "alto",
                valor
            )
        )

        self.campo_dpi.valueChanged.connect(
            self.cambiar_dpi
        )

        self.check_proporcion.toggled.connect(
            self.cambiar_bloqueo_proporcion
        )

        self.check_no_ampliar.toggled.connect(
            self.aplicar_limite_ampliacion
        )

        self.vista.dimensiones_cambiadas.connect(
            self.cambiar_dimensiones_desde_vista
        )

        self.boton_restablecer.clicked.connect(
            self.restablecer_dimensiones
        )

        self.boton_redimensionar.clicked.connect(
            self.iniciar_redimensionado
        )

        self.boton_cancelar.clicked.connect(
            self.cancelar_redimensionado
        )


    # ============================================================
    # ARRASTRAR ARCHIVO
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
    # SOLTAR ARCHIVO
    # ============================================================
    def dropEvent(
        self,
        evento
    ):

        urls = (
            evento.mimeData().urls()
        )

        if not urls:

            evento.ignore()

            return

        ruta = (
            urls[0].toLocalFile()
        )

        if not ruta:

            evento.ignore()

            return

        self.cargar_imagen(
            ruta
        )

        evento.acceptProposedAction()


    # ============================================================
    # SELECCIONAR IMAGEN
    # ============================================================
    def seleccionar_imagen(
        self
    ):

        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen",
            "",
            (
                "Imágenes (*.jpg *.jpeg *.png *.webp *.bmp *.gif "
                "*.tif *.tiff *.ico *.avif *.heic *.heif *.jxl "
                "*.jp2 *.j2k *.jxr *.qoi *.tga *.pcx *.pnm *.pbm "
                "*.pgm *.ppm *.pam *.hdr *.exr *.dpx *.dds *.psd);;"
                "Todos los archivos (*.*)"
            )
        )

        if ruta:

            self.cargar_imagen(
                ruta
            )


    # ============================================================
    # CARGAR IMAGEN
    # ============================================================
    def cargar_imagen(
        self,
        ruta
    ):

        try:

            (
                ancho,
                alto
            ) = obtener_dimensiones_imagen(
                ruta
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "No fue posible abrir la imagen",
                str(
                    error
                )
            )

            return

        pixmap = cargar_pixmap_previsualizacion(
            ruta
        )

        if pixmap.isNull():

            QMessageBox.warning(
                self,
                "Previsualización no disponible",
                (
                    "La imagen puede redimensionarse, "
                    "pero este formato no pudo mostrarse "
                    "en la previsualización."
                )
            )

        self.ruta_imagen = os.path.abspath(
            ruta
        )

        self.carpeta_salida = os.path.dirname(
            self.ruta_imagen
        )

        self.ancho_original = ancho

        self.alto_original = alto

        self.ancho_objetivo = ancho

        self.alto_objetivo = alto

        (
            self.dpi,
            self.dpi_detectado
        ) = obtener_dpi_imagen(
            self.ruta_imagen
        )

        self.campo_dpi.setValue(
            max(
                1,
                int(
                    round(
                        self.dpi
                    )
                )
            )
        )

        self.dpi = float(
            self.campo_dpi.value()
        )

        self.campo_archivo.setText(
            self.ruta_imagen
        )

        self.campo_salida.setText(
            self.carpeta_salida
        )

        self.etiqueta_original.setText(
            f"{ancho} × {alto} px"
        )

        if self.dpi_detectado:

            self.etiqueta_dpi_info.setText(
                f"PPI detectado en la imagen: "
                f"{self.dpi:g}."
            )

        else:

            self.etiqueta_dpi_info.setText(
                (
                    "La imagen no informa un PPI fiable. "
                    "Para centímetros se usará 96 ppi "
                    "hasta que lo cambies."
                )
            )

        self.vista.establecer_imagen(
            pixmap,
            ancho,
            alto
        )

        self.vista.establecer_mantener_proporcion(
            self.check_proporcion.isChecked()
        )

        self.actualizar_campos_desde_pixeles()

        self.actualizar_estado_interfaz()


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
    # CAMBIAR UNIDAD
    # ============================================================
    def cambiar_unidad(
        self
    ):

        if self.radio_px.isChecked():

            self.unidad_actual = (
                UNIDAD_PIXELES
            )

        elif self.radio_porcentaje.isChecked():

            self.unidad_actual = (
                UNIDAD_PORCENTAJE
            )

        else:

            self.unidad_actual = (
                UNIDAD_CENTIMETROS
            )

        self.configurar_campos_unidad()

        self.actualizar_campos_desde_pixeles()

        self.actualizar_estado_interfaz()


    # ============================================================
    # CONFIGURAR CAMPOS SEGUN UNIDAD
    # ============================================================
    def configurar_campos_unidad(
        self
    ):

        self.actualizando_campos = True

        try:

            if (
                self.unidad_actual
                == UNIDAD_PIXELES
            ):

                for campo in (
                    self.campo_ancho,
                    self.campo_alto
                ):

                    campo.setDecimals(
                        0
                    )

                    campo.setRange(
                        1,
                        100000
                    )

                    campo.setSingleStep(
                        1
                    )

                    campo.setSuffix(
                        " px"
                    )

            elif (
                self.unidad_actual
                == UNIDAD_PORCENTAJE
            ):

                for campo in (
                    self.campo_ancho,
                    self.campo_alto
                ):

                    campo.setDecimals(
                        2
                    )

                    campo.setRange(
                        0.01,
                        10000
                    )

                    campo.setSingleStep(
                        1
                    )

                    campo.setSuffix(
                        " %"
                    )

            else:

                for campo in (
                    self.campo_ancho,
                    self.campo_alto
                ):

                    campo.setDecimals(
                        2
                    )

                    campo.setRange(
                        0.01,
                        10000
                    )

                    campo.setSingleStep(
                        0.1
                    )

                    campo.setSuffix(
                        " cm"
                    )

        finally:

            self.actualizando_campos = False


    # ============================================================
    # CONVERTIR PIXELES A UNIDAD
    # ============================================================
    def pixels_a_unidad(
        self,
        pixels,
        pixels_originales
    ):

        if (
            self.unidad_actual
            == UNIDAD_PIXELES
        ):

            return float(
                pixels
            )

        if (
            self.unidad_actual
            == UNIDAD_PORCENTAJE
        ):

            return (
                pixels
                / max(
                    1,
                    pixels_originales
                )
                * 100.0
            )

        return (
            pixels
            / max(
                1.0,
                self.dpi
            )
            * 2.54
        )


    # ============================================================
    # CONVERTIR UNIDAD A PIXELES
    # ============================================================
    def unidad_a_pixels(
        self,
        valor,
        pixels_originales
    ):

        if (
            self.unidad_actual
            == UNIDAD_PIXELES
        ):

            return max(
                1,
                int(
                    round(
                        valor
                    )
                )
            )

        if (
            self.unidad_actual
            == UNIDAD_PORCENTAJE
        ):

            return max(
                1,
                int(
                    round(
                        pixels_originales
                        * valor
                        / 100.0
                    )
                )
            )

        return max(
            1,
            int(
                round(
                    valor
                    / 2.54
                    * self.dpi
                )
            )
        )


    # ============================================================
    # ACTUALIZAR CAMPOS DESDE PIXELES
    # ============================================================
    def actualizar_campos_desde_pixeles(
        self
    ):

        if self.ruta_imagen is None:

            return

        self.actualizando_campos = True

        try:

            self.campo_ancho.setValue(
                self.pixels_a_unidad(
                    self.ancho_objetivo,
                    self.ancho_original
                )
            )

            self.campo_alto.setValue(
                self.pixels_a_unidad(
                    self.alto_objetivo,
                    self.alto_original
                )
            )

        finally:

            self.actualizando_campos = False


    # ============================================================
    # CAMBIAR DIMENSION DESDE CAMPO
    # ============================================================
    def cambiar_dimension_desde_campo(
        self,
        origen,
        valor
    ):

        if (
            self.actualizando_campos
            or self.ruta_imagen is None
        ):

            return

        if origen == "ancho":

            nuevo_ancho = (
                self.unidad_a_pixels(
                    valor,
                    self.ancho_original
                )
            )

            nuevo_alto = (
                self.alto_objetivo
            )

            if (
                self.check_proporcion.isChecked()
            ):

                nuevo_alto = max(
                    1,
                    int(
                        round(
                            nuevo_ancho
                            * self.alto_original
                            / max(
                                1,
                                self.ancho_original
                            )
                        )
                    )
                )

        else:

            nuevo_alto = (
                self.unidad_a_pixels(
                    valor,
                    self.alto_original
                )
            )

            nuevo_ancho = (
                self.ancho_objetivo
            )

            if (
                self.check_proporcion.isChecked()
            ):

                nuevo_ancho = max(
                    1,
                    int(
                        round(
                            nuevo_alto
                            * self.ancho_original
                            / max(
                                1,
                                self.alto_original
                            )
                        )
                    )
                )

        (
            nuevo_ancho,
            nuevo_alto
        ) = self.limitar_ampliacion(
            nuevo_ancho,
            nuevo_alto
        )

        self.establecer_dimensiones_objetivo(
            nuevo_ancho,
            nuevo_alto,
            actualizar_campos=True
        )


    # ============================================================
    # CAMBIAR DIMENSIONES DESDE VISTA
    # ============================================================
    def cambiar_dimensiones_desde_vista(
        self,
        ancho,
        alto
    ):

        if self.ruta_imagen is None:

            return

        (
            ancho,
            alto
        ) = self.limitar_ampliacion(
            ancho,
            alto
        )

        self.establecer_dimensiones_objetivo(
            ancho,
            alto,
            actualizar_campos=True
        )

        if (
            self.dialogo_pantalla_completa
            is not None
        ):

            self.dialogo_pantalla_completa.establecer_dimensiones(
                ancho,
                alto
            )


    # ============================================================
    # ESTABLECER DIMENSIONES OBJETIVO
    # ============================================================
    def establecer_dimensiones_objetivo(
        self,
        ancho,
        alto,
        actualizar_campos=True
    ):

        self.ancho_objetivo = max(
            1,
            int(
                round(
                    ancho
                )
            )
        )

        self.alto_objetivo = max(
            1,
            int(
                round(
                    alto
                )
            )
        )

        self.vista.establecer_dimensiones(
            self.ancho_objetivo,
            self.alto_objetivo,
            emitir=False
        )

        if actualizar_campos:

            self.actualizar_campos_desde_pixeles()


    # ============================================================
    # CAMBIAR DPI
    # ============================================================
    def cambiar_dpi(
        self,
        valor
    ):

        valor = max(
            1,
            int(
                valor
            )
        )

        if (
            self.unidad_actual
            == UNIDAD_CENTIMETROS
            and self.ruta_imagen
            is not None
            and not self.actualizando_campos
        ):

            ancho_cm = (
                self.campo_ancho.value()
            )

            alto_cm = (
                self.campo_alto.value()
            )

            self.dpi = float(
                valor
            )

            nuevo_ancho = (
                self.unidad_a_pixels(
                    ancho_cm,
                    self.ancho_original
                )
            )

            nuevo_alto = (
                self.unidad_a_pixels(
                    alto_cm,
                    self.alto_original
                )
            )

            (
                nuevo_ancho,
                nuevo_alto
            ) = self.limitar_ampliacion(
                nuevo_ancho,
                nuevo_alto
            )

            self.establecer_dimensiones_objetivo(
                nuevo_ancho,
                nuevo_alto,
                actualizar_campos=True
            )

            return

        self.dpi = float(
            valor
        )


    # ============================================================
    # CAMBIAR BLOQUEO DE PROPORCION
    # ============================================================
    def cambiar_bloqueo_proporcion(
        self,
        mantener
    ):

        self.vista.establecer_mantener_proporcion(
            mantener
        )

        if (
            mantener
            and self.ruta_imagen
            is not None
        ):

            nuevo_alto = max(
                1,
                int(
                    round(
                        self.ancho_objetivo
                        * self.alto_original
                        / max(
                            1,
                            self.ancho_original
                        )
                    )
                )
            )

            self.establecer_dimensiones_objetivo(
                self.ancho_objetivo,
                nuevo_alto,
                actualizar_campos=True
            )


    # ============================================================
    # LIMITAR AMPLIACION
    # ============================================================
    def limitar_ampliacion(
        self,
        ancho,
        alto
    ):

        ancho = max(
            1,
            int(
                round(
                    ancho
                )
            )
        )

        alto = max(
            1,
            int(
                round(
                    alto
                )
            )
        )

        if not (
            self.check_no_ampliar.isChecked()
        ):

            return (
                ancho,
                alto
            )

        if (
            self.check_proporcion.isChecked()
        ):

            if (
                ancho > self.ancho_original
                or alto > self.alto_original
            ):

                return (
                    self.ancho_original,
                    self.alto_original
                )

            return (
                ancho,
                alto
            )

        return (
            min(
                ancho,
                self.ancho_original
            ),
            min(
                alto,
                self.alto_original
            )
        )


    # ============================================================
    # APLICAR LIMITE DE AMPLIACION
    # ============================================================
    def aplicar_limite_ampliacion(
        self
    ):

        if self.ruta_imagen is None:

            return

        (
            ancho,
            alto
        ) = self.limitar_ampliacion(
            self.ancho_objetivo,
            self.alto_objetivo
        )

        self.establecer_dimensiones_objetivo(
            ancho,
            alto,
            actualizar_campos=True
        )


    # ============================================================
    # RESTABLECER DIMENSIONES
    # ============================================================
    def restablecer_dimensiones(
        self
    ):

        if self.ruta_imagen is None:

            return

        self.establecer_dimensiones_objetivo(
            self.ancho_original,
            self.alto_original,
            actualizar_campos=True
        )

        self.vista.restablecer_zoom()


    # ============================================================
    # ABRIR PANTALLA COMPLETA
    # ============================================================
    def abrir_pantalla_completa(
        self
    ):

        if (
            self.ruta_imagen is None
            or self.vista.pixmap.isNull()
        ):

            return

        pantalla_objetivo = (
            self.window().screen()
        )

        dialogo = DialogoVistaCompleta(
            self.vista.pixmap,
            self.ancho_original,
            self.alto_original,
            self.ancho_objetivo,
            self.alto_objetivo,
            self.check_proporcion.isChecked(),
            self.vista.obtener_zoom_visual(),
            pantalla_objetivo=pantalla_objetivo,
            parent=self.window()
        )

        self.dialogo_pantalla_completa = (
            dialogo
        )

        dialogo.dimensiones_cambiadas.connect(
            self.cambiar_dimensiones_desde_vista
        )

        dialogo.exec()

        self.vista.establecer_zoom_visual(
            dialogo.vista.obtener_zoom_visual()
        )

        self.dialogo_pantalla_completa = None


    # ============================================================
    # ACTUALIZAR ESTADO DE INTERFAZ
    # ============================================================
    def actualizar_estado_interfaz(
        self
    ):

        hay_imagen = (
            self.ruta_imagen
            is not None
        )

        trabajando = (
            self.hilo
            is not None
        )

        controles = [
            self.radio_px,
            self.radio_porcentaje,
            self.radio_cm,
            self.campo_ancho,
            self.campo_alto,
            self.check_proporcion,
            self.check_no_ampliar,
            self.combo_calidad,
            self.boton_restablecer,
            self.boton_salida,
            self.campo_sufijo,
            self.boton_pantalla_completa
        ]

        for control in controles:

            control.setEnabled(
                hay_imagen
                and not trabajando
            )

        self.campo_dpi.setEnabled(
            hay_imagen
            and not trabajando
            and self.unidad_actual
            == UNIDAD_CENTIMETROS
        )

        self.etiqueta_dpi.setEnabled(
            self.unidad_actual
            == UNIDAD_CENTIMETROS
        )

        self.boton_seleccionar.setEnabled(
            not trabajando
        )

        self.boton_redimensionar.setEnabled(
            hay_imagen
            and not trabajando
        )

        self.boton_cancelar.setEnabled(
            trabajando
        )


    # ============================================================
    # INICIAR REDIMENSIONADO
    # ============================================================
    def iniciar_redimensionado(
        self
    ):

        if self.ruta_imagen is None:

            return

        carpeta_salida = (
            self.carpeta_salida
            or os.path.dirname(
                self.ruta_imagen
            )
        )

        sufijo = (
            self.campo_sufijo.text().strip()
        )

        if not sufijo:

            sufijo = (
                "_redimensionada"
            )

        try:

            ruta_destino = generar_ruta_salida(
                self.ruta_imagen,
                carpeta_salida,
                sufijo=sufijo,
                sobrescribir=False
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "No fue posible preparar la salida",
                str(
                    error
                )
            )

            return

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
            TrabajadorRedimensionarImagen(
                self.ruta_imagen,
                str(
                    ruta_destino
                ),
                self.ancho_objetivo,
                self.alto_objetivo,
                self.check_no_ampliar.isChecked(),
                self.combo_calidad.currentData()
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
            self.redimensionado_terminado
        )

        self.trabajador.cancelado.connect(
            self.redimensionado_cancelado
        )

        self.trabajador.error.connect(
            self.error_redimensionado
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

        self.actualizar_estado_interfaz()

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
    # CANCELAR REDIMENSIONADO
    # ============================================================
    def cancelar_redimensionado(
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
    # REDIMENSIONADO TERMINADO
    # ============================================================
    @Slot(
        object
    )
    def redimensionado_terminado(
        self,
        resultado
    ):

        self.barra_progreso.setValue(
            100
        )

        self.etiqueta_estado.setText(
            "Completado"
        )

        QMessageBox.information(
            self,
            "Redimensionado terminado",
            (
                "La imagen se guardó correctamente en:\n\n"
                f"{resultado['ruta']}\n\n"
                f"Tamaño final: "
                f"{resultado['ancho']} × "
                f"{resultado['alto']} px"
            )
        )


    # ============================================================
    # REDIMENSIONADO CANCELADO
    # ============================================================
    @Slot()
    def redimensionado_cancelado(
        self
    ):

        self.etiqueta_estado.setText(
            "Cancelado"
        )


    # ============================================================
    # ERROR DE REDIMENSIONADO
    # ============================================================
    @Slot(
        str
    )
    def error_redimensionado(
        self,
        mensaje
    ):

        self.etiqueta_estado.setText(
            "Error"
        )

        QMessageBox.critical(
            self,
            "Error al redimensionar",
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

        self.actualizar_estado_interfaz()


    # ============================================================
    # CANCELAR SI ESTA TRABAJANDO
    # ============================================================
    def cancelar_si_esta_trabajando(
        self
    ):

        if self.trabajador is not None:

            self.trabajador.cancelar()