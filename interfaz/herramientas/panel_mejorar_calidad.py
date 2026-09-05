import os

from collections import OrderedDict

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
    QColor,
    QCursor,
    QIcon,
    QImageReader,
    QPixmap
)

from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)

from herramientas.imagenes.mejorar_calidad import (
    MODO_IA,
    MODO_CLASICO,

    TIPO_AUTOMATICO,
    TIPO_FOTOGRAFIA,
    TIPO_ILUSTRACION,

    comprobar_motor_ia,
    mejorar_imagenes,
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
# CARGAR PREVISUALIZACION
# ================================================================
def cargar_pixmap_previsualizacion(
    ruta,
    ancho_maximo=1200,
    alto_maximo=900
):

    lector = QImageReader(
        ruta
    )

    lector.setAutoTransform(
        True
    )

    tamano = lector.size()

    if (
        tamano.isValid()
        and (
            tamano.width() > ancho_maximo
            or tamano.height() > alto_maximo
        )
    ):

        destino = QSize(
            tamano.width(),
            tamano.height()
        )

        destino.scale(
            QSize(
                ancho_maximo,
                alto_maximo
            ),
            Qt.AspectRatioMode.KeepAspectRatio
        )

        lector.setScaledSize(
            destino
        )

    imagen = lector.read()

    if imagen.isNull():

        return QPixmap()

    return QPixmap.fromImage(
        imagen
    )


# ================================================================
# VISTA PREVIA
# ================================================================
class VistaPreviaImagen(
    QLabel
):

    clic_solicitado = Signal()


    # ============================================================
    # INICIALIZACION
    # ============================================================
    def __init__(
        self,
        texto_vacio,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.texto_vacio = texto_vacio

        self.pixmap_original = QPixmap()

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setMinimumSize(
            260,
            250
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
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

        self.setToolTip(
            "Haz clic para ver la imagen en grande."
        )

        self.limpiar()


    # ============================================================
    # ESTABLECER IMAGEN
    # ============================================================
    def establecer_imagen(
        self,
        pixmap
    ):

        self.pixmap_original = pixmap

        if self.pixmap_original.isNull():

            self.setCursor(
                Qt.CursorShape.ArrowCursor
            )

        else:

            self.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

        self.actualizar_imagen()


    # ============================================================
    # LIMPIAR
    # ============================================================
    def limpiar(
        self,
        texto=None
    ):

        self.pixmap_original = QPixmap()

        self.setPixmap(
            QPixmap()
        )

        self.setText(
            texto
            or self.texto_vacio
        )

        self.setCursor(
            Qt.CursorShape.ArrowCursor
        )


    # ============================================================
    # ACTUALIZAR IMAGEN
    # ============================================================
    def actualizar_imagen(
        self
    ):

        if self.pixmap_original.isNull():

            return

        pixmap = self.pixmap_original.scaled(
            max(
                1,
                self.width() - 18
            ),
            max(
                1,
                self.height() - 18
            ),
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
    # PRESIONAR CON EL MOUSE
    # ============================================================
    def mousePressEvent(
        self,
        evento
    ):

        if (
            evento.button()
            == Qt.MouseButton.LeftButton
            and not self.pixmap_original.isNull()
        ):

            self.clic_solicitado.emit()

            evento.accept()

            return

        super().mousePressEvent(
            evento
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
# ETIQUETA DE IMAGEN AMPLIADA
# ================================================================
class EtiquetaImagenAmpliada(
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

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setStyleSheet(
            """
            QLabel {
                background-color: transparent;
                border: none;
            }
            """
        )


# ================================================================
# RUTAS DE ICONOS DE CIERRE
# ================================================================
CARPETA_ICONOS = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "recursos",
        "iconos"
    )
)

RUTA_CERRAR_NORMAL = os.path.join(
    CARPETA_ICONOS,
    "cerrar_normal.png"
)

RUTA_CERRAR_HOVER = os.path.join(
    CARPETA_ICONOS,
    "cerrar_hover.png"
)

RUTA_CERRAR_PRESIONADA = os.path.join(
    CARPETA_ICONOS,
    "cerrar_presionada.png"
)


# ================================================================
# BOTON DE CERRAR PARA VISTA AMPLIADA
# ================================================================
class BotonCerrarVistaAmpliada(
    QPushButton
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

        self.pixmap_normal = QPixmap(
            RUTA_CERRAR_NORMAL
        )

        self.pixmap_hover = QPixmap(
            RUTA_CERRAR_HOVER
        )

        self.pixmap_presionada = QPixmap(
            RUTA_CERRAR_PRESIONADA
        )

        self.setObjectName(
            "BotonCerrarVistaAmpliada"
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setToolTip(
            "Cerrar"
        )

        self.setFlat(
            True
        )

        self.setFixedSize(
            42,
            42
        )

        self.setIconSize(
            QSize(
                30,
                30
            )
        )

        self.setStyleSheet(
            """
            QPushButton#BotonCerrarVistaAmpliada {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }

            QPushButton#BotonCerrarVistaAmpliada:hover {
                background: transparent;
                border: none;
            }

            QPushButton#BotonCerrarVistaAmpliada:pressed {
                background: transparent;
                border: none;
            }
            """
        )

        self._usar_fallback_texto = (
            self.pixmap_normal.isNull()
            or self.pixmap_hover.isNull()
            or self.pixmap_presionada.isNull()
        )

        if self._usar_fallback_texto:

            self.setText(
                "×"
            )

            self.setStyleSheet(
                """
                QPushButton#BotonCerrarVistaAmpliada {
                    background: transparent;
                    border: none;
                    padding: 0px;
                    margin: 0px;
                    color: white;
                    font-size: 28px;
                    font-weight: 500;
                }

                QPushButton#BotonCerrarVistaAmpliada:hover {
                    color: #d0d0d0;
                }

                QPushButton#BotonCerrarVistaAmpliada:pressed {
                    color: #9a9a9a;
                }
                """
            )

        else:

            self.setText(
                ""
            )

            self.aplicar_estado_normal()


    # ============================================================
    # APLICAR ICONO
    # ============================================================
    def aplicar_icono(
        self,
        pixmap
    ):

        if pixmap.isNull():

            return

        self.setIcon(
            QIcon(
                pixmap
            )
        )


    # ============================================================
    # ESTADO NORMAL
    # ============================================================
    def aplicar_estado_normal(
        self
    ):

        if self._usar_fallback_texto:

            return

        self.aplicar_icono(
            self.pixmap_normal
        )


    # ============================================================
    # ESTADO HOVER
    # ============================================================
    def aplicar_estado_hover(
        self
    ):

        if self._usar_fallback_texto:

            return

        self.aplicar_icono(
            self.pixmap_hover
        )


    # ============================================================
    # ESTADO PRESIONADO
    # ============================================================
    def aplicar_estado_presionado(
        self
    ):

        if self._usar_fallback_texto:

            return

        self.aplicar_icono(
            self.pixmap_presionada
        )


    # ============================================================
    # ENTRAR
    # ============================================================
    def enterEvent(
        self,
        evento
    ):

        super().enterEvent(
            evento
        )

        self.aplicar_estado_hover()


    # ============================================================
    # SALIR
    # ============================================================
    def leaveEvent(
        self,
        evento
    ):

        super().leaveEvent(
            evento
        )

        self.aplicar_estado_normal()


    # ============================================================
    # PRESIONAR
    # ============================================================
    def mousePressEvent(
        self,
        evento
    ):

        super().mousePressEvent(
            evento
        )

        if (
            evento.button()
            == Qt.MouseButton.LeftButton
        ):

            self.aplicar_estado_presionado()


    # ============================================================
    # SOLTAR
    # ============================================================
    def mouseReleaseEvent(
        self,
        evento
    ):

        super().mouseReleaseEvent(
            evento
        )

        if self.underMouse():

            self.aplicar_estado_hover()

        else:

            self.aplicar_estado_normal()


# ================================================================
# DIALOGO DE VISTA AMPLIADA
# ================================================================
class DialogoVistaAmpliada(
    QDialog
):

    # ============================================================
    # INICIALIZACION
    # ============================================================
    def __init__(
        self,
        ruta_imagen,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.ruta_imagen = ruta_imagen

        self.setModal(
            True
        )

        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True
        )

        self.crear_interfaz()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self
    ):

        layout_exterior = QVBoxLayout(
            self
        )

        layout_exterior.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.fondo_overlay = QFrame(
            self
        )

        self.fondo_overlay.setObjectName(
            "FondoVistaAmpliada"
        )

        self.fondo_overlay.setStyleSheet(
            """
            QFrame#FondoVistaAmpliada {
                background-color: rgba(0, 0, 0, 190);
            }
            """
        )

        layout_exterior.addWidget(
            self.fondo_overlay
        )

        layout = QVBoxLayout(
            self.fondo_overlay
        )

        layout.setContentsMargins(
            26,
            18,
            26,
            28
        )

        layout.setSpacing(
            8
        )


        # ----------------------------------- #
        #           Boton de cerrar           #
        # ----------------------------------- #

        fila_superior = QHBoxLayout()

        fila_superior.setContentsMargins(
            0,
            0,
            0,
            0
        )

        fila_superior.addStretch()

        self.boton_cerrar = (
            BotonCerrarVistaAmpliada(
                self.fondo_overlay
            )
        )

        self.boton_cerrar.clicked.connect(
            self.accept
        )

        fila_superior.addWidget(
            self.boton_cerrar
        )

        layout.addLayout(
            fila_superior
        )


        # ----------------------------------- #
        #              Imagen                 #
        # ----------------------------------- #

        self.etiqueta_imagen = (
            EtiquetaImagenAmpliada(
                self.fondo_overlay
            )
        )

        sombra = QGraphicsDropShadowEffect(
            self.etiqueta_imagen
        )

        sombra.setBlurRadius(
            48
        )

        sombra.setOffset(
            0,
            8
        )

        sombra.setColor(
            QColor(
                0,
                0,
                0,
                230
            )
        )

        self.etiqueta_imagen.setGraphicsEffect(
            sombra
        )

        layout.addStretch()

        layout.addWidget(
            self.etiqueta_imagen,
            0,
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addStretch()


    # ============================================================
    # OBTENER PANTALLA OBJETIVO
    # ============================================================
    def obtener_pantalla_objetivo(
        self
    ):

        if self.parentWidget() is not None:

            try:

                pantalla = (
                    self.parentWidget()
                    .window()
                    .screen()
                )

                if pantalla is not None:

                    return pantalla

            except Exception:

                pass

        pantalla = QApplication.screenAt(
            QCursor.pos()
        )

        if pantalla is not None:

            return pantalla

        return QApplication.primaryScreen()


    # ============================================================
    # CARGAR IMAGEN
    # ============================================================
    def cargar_imagen(
        self
    ):

        pantalla = self.obtener_pantalla_objetivo()

        if pantalla is None:

            ancho_maximo = 1600
            alto_maximo = 1000

        else:

            geometria = pantalla.geometry()

            ancho_maximo = max(
                1,
                int(
                    geometria.width()
                    * 0.90
                )
            )

            alto_maximo = max(
                1,
                int(
                    geometria.height()
                    * 0.82
                )
            )

        pixmap = cargar_pixmap_previsualizacion(
            self.ruta_imagen,
            ancho_maximo=ancho_maximo,
            alto_maximo=alto_maximo
        )

        if pixmap.isNull():

            self.reject()

            return False

        self.etiqueta_imagen.setPixmap(
            pixmap
        )

        self.etiqueta_imagen.setFixedSize(
            pixmap.size()
        )

        return True


    # ============================================================
    # MOSTRAR VISTA AMPLIADA
    # ============================================================
    def mostrar(
        self
    ):

        if not self.cargar_imagen():

            return

        self.showFullScreen()

        self.exec()


    # ============================================================
    # PRESIONAR TECLA
    # ============================================================
    def keyPressEvent(
        self,
        evento
    ):

        if evento.key() == Qt.Key.Key_Escape:

            self.accept()

            return

        super().keyPressEvent(
            evento
        )


    # ============================================================
    # PRESIONAR FONDO
    # ============================================================
    def mousePressEvent(
        self,
        evento
    ):

        if (
            evento.button()
            == Qt.MouseButton.LeftButton
        ):

            posicion_dialogo = evento.position().toPoint()

            posicion_imagen = self.etiqueta_imagen.mapFrom(
                self,
                posicion_dialogo
            )

            if not self.etiqueta_imagen.rect().contains(
                posicion_imagen
            ):

                posicion_boton = self.boton_cerrar.mapFrom(
                    self,
                    posicion_dialogo
                )

                if not self.boton_cerrar.rect().contains(
                    posicion_boton
                ):

                    self.accept()

                    return

        super().mousePressEvent(
            evento
        )


# ================================================================
# TRABAJADOR
# ================================================================
class TrabajadorMejorarCalidad(
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
        modo,
        tipo_imagen,
        escala,
        conservar_transparencia,
        conservar_metadatos,
        sufijo
    ):

        super().__init__()

        self.rutas = rutas

        self.carpeta_salida = (
            carpeta_salida
        )

        self.modo = modo

        self.tipo_imagen = (
            tipo_imagen
        )

        self.escala = escala

        self.conservar_transparencia = (
            conservar_transparencia
        )

        self.conservar_metadatos = (
            conservar_metadatos
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

        return self.cancelacion_solicitada


    # ============================================================
    # EJECUTAR
    # ============================================================
    @Slot()
    def ejecutar(
        self
    ):

        try:

            resultados = mejorar_imagenes(
                self.rutas,
                self.carpeta_salida,
                modo=self.modo,
                tipo_imagen=self.tipo_imagen,
                escala=self.escala,
                conservar_transparencia=(
                    self.conservar_transparencia
                ),
                conservar_metadatos=(
                    self.conservar_metadatos
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
# PANEL MEJORAR CALIDAD
# ================================================================
class PanelMejorarCalidad(
    QWidget
):

    ANCHO_INICIAL = 930

    ALTO_INICIAL = 690

    ANCHO_MINIMO = 930

    ALTO_MINIMO = 690

    DURACION_RESULTADO_MS = 6000

    INTERVALO_RESULTADO_MS = 10

    RETARDO_PREVISUALIZACION_MS = 25

    MAXIMO_CACHE = 12


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

        self.resultados_por_origen = {}

        self.cache_previsualizaciones = (
            OrderedDict()
        )

        self.item_previsualizacion_pendiente = None

        self.tiempo_resultado_transcurrido = 0

        self.actualizando_checks = False

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

        self.crear_temporizadores()

        self.conectar_eventos()

        self.configurar_navegacion_teclado()

        self.actualizar_metodo()

        self.actualizar_estado_controles()


    # ============================================================
    # CREAR TEMPORIZADORES
    # ============================================================
    def crear_temporizadores(
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
        #               Titulo                #
        # ----------------------------------- #

        titulo = QLabel(
            "Mejorar calidad"
        )

        titulo.setStyleSheet(
            "font-size: 22px; font-weight: 600;"
        )

        descripcion = QLabel(
            "Aumenta la resolución de imágenes con "
            "superresolución IA local o con un escalado "
            "clásico conservador."
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
        #              Entrada                #
        # ----------------------------------- #

        fila_entrada = QHBoxLayout()

        self.boton_agregar = QPushButton(
            "Añadir imágenes"
        )

        self.boton_quitar = QPushButton(
            "Quitar imagen"
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
        #            Zona izquierda           #
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
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.lista_imagenes.setMinimumHeight(
            105
        )

        self.lista_imagenes.setMaximumHeight(
            150
        )

        self.lista_imagenes.setToolTip(
            "La fila resaltada controla la vista previa. "
            "La casilla indica si la imagen se incluirá en la mejora."
        )

        layout_izquierdo.addWidget(
            self.lista_imagenes
        )

        self.etiqueta_info = QLabel(
            "Selecciona una imagen para verla."
        )

        self.etiqueta_info.setWordWrap(
            True
        )

        self.etiqueta_info.setStyleSheet(
            "color: #aaaaaa;"
        )

        layout_izquierdo.addWidget(
            self.etiqueta_info
        )


        # ----------------------------------- #
        #         Antes y despues             #
        # ----------------------------------- #

        fila_previsualizaciones = QHBoxLayout()

        fila_previsualizaciones.setSpacing(
            8
        )

        contenedor_antes = QWidget()

        layout_antes = QVBoxLayout(
            contenedor_antes
        )

        layout_antes.setContentsMargins(
            0,
            0,
            0,
            0
        )

        etiqueta_antes = QLabel(
            "Antes"
        )

        etiqueta_antes.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        etiqueta_antes.setStyleSheet(
            "font-weight: 600;"
        )

        self.vista_antes = VistaPreviaImagen(
            "Selecciona una imagen",
            self
        )

        layout_antes.addWidget(
            etiqueta_antes
        )

        layout_antes.addWidget(
            self.vista_antes,
            1
        )

        contenedor_despues = QWidget()

        layout_despues = QVBoxLayout(
            contenedor_despues
        )

        layout_despues.setContentsMargins(
            0,
            0,
            0,
            0
        )

        etiqueta_despues = QLabel(
            "Después"
        )

        etiqueta_despues.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        etiqueta_despues.setStyleSheet(
            "font-weight: 600;"
        )

        self.vista_despues = VistaPreviaImagen(
            "La imagen mejorada aparecerá aquí",
            self
        )

        layout_despues.addWidget(
            etiqueta_despues
        )

        layout_despues.addWidget(
            self.vista_despues,
            1
        )

        fila_previsualizaciones.addWidget(
            contenedor_antes,
            1
        )

        fila_previsualizaciones.addWidget(
            contenedor_despues,
            1
        )

        layout_izquierdo.addLayout(
            fila_previsualizaciones,
            1
        )

        fila_contenido.addWidget(
            contenedor_izquierdo,
            1
        )


        # ----------------------------------- #
        #          Panel derecho              #
        # ----------------------------------- #

        panel_controles = QFrame()

        panel_controles.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        panel_controles.setMinimumWidth(
            320
        )

        panel_controles.setMaximumWidth(
            365
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
        #              Metodo                 #
        # ----------------------------------- #

        etiqueta_metodo = QLabel(
            "Método"
        )

        etiqueta_metodo.setStyleSheet(
            "font-weight: 600;"
        )

        layout_controles.addWidget(
            etiqueta_metodo
        )

        self.combo_metodo = QComboBox()

        self.combo_metodo.addItem(
            "Superresolución IA · Real-ESRGAN",
            MODO_IA
        )

        self.combo_metodo.addItem(
            "Mejora clásica · Sin IA",
            MODO_CLASICO
        )

        layout_controles.addWidget(
            self.combo_metodo
        )

        self.etiqueta_motor = QLabel(
            ""
        )

        self.etiqueta_motor.setWordWrap(
            True
        )

        layout_controles.addWidget(
            self.etiqueta_motor
        )


        # ----------------------------------- #
        #          Tipo y escala              #
        # ----------------------------------- #

        fila_tipo = QHBoxLayout()

        columna_tipo = QVBoxLayout()

        columna_tipo.addWidget(
            QLabel(
                "Tipo de imagen"
            )
        )

        self.combo_tipo = QComboBox()

        self.combo_tipo.addItem(
            "Automático / general",
            TIPO_AUTOMATICO
        )

        self.combo_tipo.addItem(
            "Fotografía",
            TIPO_FOTOGRAFIA
        )

        self.combo_tipo.addItem(
            "Ilustración / anime",
            TIPO_ILUSTRACION
        )

        columna_tipo.addWidget(
            self.combo_tipo
        )

        columna_escala = QVBoxLayout()

        columna_escala.addWidget(
            QLabel(
                "Escala"
            )
        )

        self.combo_escala = QComboBox()

        self.combo_escala.addItem(
            "2×",
            2
        )

        self.combo_escala.addItem(
            "3×",
            3
        )

        self.combo_escala.addItem(
            "4×",
            4
        )

        columna_escala.addWidget(
            self.combo_escala
        )

        fila_tipo.addLayout(
            columna_tipo,
            2
        )

        fila_tipo.addLayout(
            columna_escala,
            1
        )

        layout_controles.addLayout(
            fila_tipo
        )


        # ----------------------------------- #
        #             Opciones                #
        # ----------------------------------- #

        self.check_transparencia = QCheckBox(
            "Conservar transparencia"
        )

        self.check_transparencia.setChecked(
            True
        )

        self.check_metadatos = QCheckBox(
            "Conservar metadatos"
        )

        self.check_metadatos.setChecked(
            True
        )

        layout_controles.addWidget(
            self.check_transparencia
        )

        layout_controles.addWidget(
            self.check_metadatos
        )

        nota = QLabel(
            "La IA se ejecuta completamente en tu equipo. "
            "La herramienta no necesita conexión a Internet."
        )

        nota.setWordWrap(
            True
        )

        nota.setStyleSheet(
            "color: #8f8f8f; font-size: 12px;"
        )

        layout_controles.addWidget(
            nota
        )


        # ----------------------------------- #
        #              Salida                 #
        # ----------------------------------- #

        separador = QFrame()

        separador.setFrameShape(
            QFrame.Shape.HLine
        )

        layout_controles.addWidget(
            separador
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
            "Carpeta de salida"
        )

        self.boton_salida = QPushButton(
            "Elegir carpeta"
        )

        layout_controles.addWidget(
            self.campo_salida
        )

        layout_controles.addWidget(
            self.boton_salida
        )

        fila_sufijo = QHBoxLayout()

        fila_sufijo.addWidget(
            QLabel(
                "Sufijo:"
            )
        )

        self.campo_sufijo = QLineEdit(
            "_mejorada"
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
            panel_controles
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
            "ResultadoMejora"
        )

        self.contenedor_resultado.setVisible(
            False
        )

        self.contenedor_resultado.setStyleSheet(
            """
            QFrame#ResultadoMejora {
                border: 1px solid rgba(100, 170, 255, 150);
                border-radius: 7px;
                background-color: rgba(50, 100, 170, 40);
            }

            QFrame#ResultadoMejora QLabel {
                border: none;
                background-color: transparent;
                color: #d9e9ff;
            }

            QFrame#ResultadoMejora QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 35);
                border-radius: 2px;
            }

            QFrame#ResultadoMejora QProgressBar::chunk {
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

        self.etiqueta_resultado = QLabel(
            ""
        )

        self.etiqueta_resultado.setWordWrap(
            True
        )

        self.barra_tiempo_resultado = QProgressBar()

        self.barra_tiempo_resultado.setRange(
            0,
            self.DURACION_RESULTADO_MS
        )

        self.barra_tiempo_resultado.setTextVisible(
            False
        )

        self.barra_tiempo_resultado.setFixedHeight(
            4
        )

        layout_resultado.addWidget(
            self.etiqueta_resultado
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

        self.etiqueta_estado = QLabel(
            ""
        )

        self.etiqueta_estado.setMaximumWidth(
            180
        )

        self.barra_progreso = QProgressBar()

        self.barra_progreso.setRange(
            0,
            100
        )

        self.boton_mejorar = QPushButton(
            "Mejorar imágenes"
        )

        self.boton_mejorar.setMinimumWidth(
            155
        )

        self.boton_mejorar.setMinimumHeight(
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

        fila_progreso.addWidget(
            self.etiqueta_estado
        )

        fila_progreso.addWidget(
            self.barra_progreso,
            1
        )

        fila_progreso.addWidget(
            self.boton_mejorar
        )

        fila_progreso.addWidget(
            self.boton_cancelar
        )

        layout_principal.addLayout(
            fila_progreso
        )


    # ================================================================
    # CONECTAR EVENTOS
    # ================================================================
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

        self.lista_imagenes.itemChanged.connect(
            self.estado_item_cambiado
        )

        self.vista_antes.clic_solicitado.connect(
            self.abrir_vista_antes
        )

        self.vista_despues.clic_solicitado.connect(
            self.abrir_vista_despues
        )

        self.combo_metodo.currentIndexChanged.connect(
            self.actualizar_metodo
        )

        self.combo_tipo.currentIndexChanged.connect(
            self.actualizar_metodo
        )

        self.boton_salida.clicked.connect(
            self.seleccionar_carpeta_salida
        )

        self.boton_mejorar.clicked.connect(
            self.iniciar_mejora
        )

        self.boton_cancelar.clicked.connect(
            self.cancelar_mejora
        )


    # ================================================================
    # CONFIGURAR NAVEGACION
    # ================================================================
    def configurar_navegacion_teclado(
        self
    ):

        aplicacion = QApplication.instance()

        if aplicacion is not None:

            aplicacion.installEventFilter(
                self
            )


    # ================================================================
    # FILTRAR FLECHAS
    # ================================================================
    def eventFilter(
        self,
        objeto,
        evento
    ):

        if (
            evento.type()
            == QEvent.Type.KeyPress
            and self.isVisible()
            and self.foco_pertenece_al_panel()
        ):

            if evento.key() == Qt.Key.Key_Up:

                self.mover_imagen_activa(
                    -1
                )

                return True

            if evento.key() == Qt.Key.Key_Down:

                self.mover_imagen_activa(
                    1
                )

                return True

        return super().eventFilter(
            objeto,
            evento
        )


    # ================================================================
    # COMPROBAR FOCO
    # ================================================================
    def foco_pertenece_al_panel(
        self
    ):

        foco = QApplication.focusWidget()

        if foco is None:

            return False

        return (
            foco is self
            or self.isAncestorOf(
                foco
            )
        )


    # ================================================================
    # MOVER IMAGEN ACTIVA
    # ================================================================
    def mover_imagen_activa(
        self,
        desplazamiento
    ):

        if self.hilo is not None:

            return

        total = self.lista_imagenes.count()

        if total <= 0:

            return

        fila = self.lista_imagenes.currentRow()

        if fila < 0:

            fila = 0

        nueva_fila = max(
            0,
            min(
                total - 1,
                fila + desplazamiento
            )
        )

        self.lista_imagenes.setCurrentRow(
            nueva_fila
        )

        item = self.lista_imagenes.item(
            nueva_fila
        )

        if item is not None:

            self.lista_imagenes.scrollToItem(
                item,
                QAbstractItemView.ScrollHint.EnsureVisible
            )


    # ================================================================
    # CLAVE DE CACHE
    # ================================================================
    def clave_cache(
        self,
        ruta
    ):

        return os.path.normcase(
            os.path.abspath(
                ruta
            )
        )


    # ================================================================
    # OBTENER CACHE
    # ================================================================
    def obtener_cache(
        self,
        ruta
    ):

        clave = self.clave_cache(
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


    # ================================================================
    # GUARDAR CACHE
    # ================================================================
    def guardar_cache(
        self,
        ruta,
        pixmap
    ):

        if pixmap.isNull():

            return

        clave = self.clave_cache(
            ruta
        )

        self.cache_previsualizaciones.pop(
            clave,
            None
        )

        self.cache_previsualizaciones[
            clave
        ] = pixmap

        while (
            len(
                self.cache_previsualizaciones
            )
            > self.MAXIMO_CACHE
        ):

            self.cache_previsualizaciones.popitem(
                last=False
            )


    # ================================================================
    # OBTENER ITEMS MARCADOS
    # ================================================================
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


    # ================================================================
    # OBTENER RUTAS MARCADAS
    # ================================================================
    def obtener_rutas_marcadas(
        self
    ):

        return [
            item.data(
                Qt.ItemDataRole.UserRole
            )
            for item
            in self.obtener_items_marcados()
        ]


    # ================================================================
    # ESTADO DE ITEM CAMBIADO
    # ================================================================
    def estado_item_cambiado(
        self,
        item
    ):

        if self.actualizando_checks:

            return

        if (
            item is not None
            and item.checkState()
            == Qt.CheckState.Checked
        ):

            self.actualizando_checks = True

            try:

                for indice in range(
                    self.lista_imagenes.count()
                ):

                    otro_item = self.lista_imagenes.item(
                        indice
                    )

                    if (
                        otro_item is not item
                        and otro_item.checkState()
                        == Qt.CheckState.Checked
                    ):

                        otro_item.setCheckState(
                            Qt.CheckState.Unchecked
                        )

            finally:

                self.actualizando_checks = False

            self.lista_imagenes.setCurrentItem(
                item
            )

        self.actualizar_resumen()

        self.actualizar_estado_controles()


    # ================================================================
    # ABRIR VISTA ANTES
    # ================================================================
    def abrir_vista_antes(
        self
    ):

        item = self.lista_imagenes.currentItem()

        if item is None:

            return

        ruta = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not ruta:

            return

        DialogoVistaAmpliada(
            ruta,
            self
        ).mostrar()


    # ================================================================
    # ABRIR VISTA DESPUES
    # ================================================================
    def abrir_vista_despues(
        self
    ):

        item = self.lista_imagenes.currentItem()

        if item is None:

            return

        ruta_origen = item.data(
            Qt.ItemDataRole.UserRole
        )

        ruta_resultado = self.resultados_por_origen.get(
            self.clave_cache(
                ruta_origen
            )
        )

        if (
            not ruta_resultado
            or not os.path.isfile(
                ruta_resultado
            )
        ):

            return

        DialogoVistaAmpliada(
            ruta_resultado,
            self
        ).mostrar()


    # ================================================================
    # ARRASTRAR ARCHIVOS
    # ================================================================
    def dragEnterEvent(
        self,
        evento
    ):

        if evento.mimeData().hasUrls():

            evento.acceptProposedAction()

        else:

            evento.ignore()


    # ================================================================
    # SOLTAR ARCHIVOS
    # ================================================================
    def dropEvent(
        self,
        evento
    ):

        rutas = [
            url.toLocalFile()
            for url in evento.mimeData().urls()
            if url.toLocalFile()
        ]

        if rutas:

            self.agregar_rutas(
                rutas
            )

            evento.acceptProposedAction()


    # ================================================================
    # SELECCIONAR IMAGENES
    # ================================================================
    def seleccionar_imagenes(
        self
    ):

        rutas, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar imágenes",
            "",
            (
                "Imágenes "
                "(*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff);;"
                "Todos los archivos (*.*)"
            )
        )

        if rutas:

            self.agregar_rutas(
                rutas
            )


    # ================================================================
    # AGREGAR RUTAS
    # ================================================================
    def agregar_rutas(
        self,
        rutas
    ):

        existentes = {
            self.clave_cache(
                ruta
            )
            for ruta in self.rutas_imagenes
        }

        errores = []

        lista_estaba_vacia = (
            self.lista_imagenes.count() == 0
        )

        primer_item_agregado = None

        for ruta in rutas:

            ruta = os.path.abspath(
                ruta
            )

            clave = self.clave_cache(
                ruta
            )

            if clave in existentes:

                continue

            try:

                informacion = obtener_informacion_imagen(
                    ruta
                )

            except Exception as error:

                errores.append(
                    (
                        f"{os.path.basename(ruta)}: "
                        f"{error}"
                    )
                )

                continue

            self.rutas_imagenes.append(
                ruta
            )

            item = QListWidgetItem(
                (
                    f"{os.path.basename(ruta)}"
                    f"   ·   "
                    f"{informacion['ancho']} × "
                    f"{informacion['alto']} px"
                    f"   ·   "
                    f"{formatear_tamano(informacion['tamano'])}"
                )
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
                ruta
            )

            item.setData(
                ROL_INFORMACION_IMAGEN,
                informacion
            )

            item.setToolTip(
                ruta
            )

            self.lista_imagenes.addItem(
                item
            )

            if primer_item_agregado is None:

                primer_item_agregado = item

            existentes.add(
                clave
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
            lista_estaba_vacia
            and primer_item_agregado is not None
        ):

            primer_item_agregado.setCheckState(
                Qt.CheckState.Checked
            )

        if (
            self.lista_imagenes.count() > 0
            and self.lista_imagenes.currentRow() < 0
        ):

            self.lista_imagenes.setCurrentRow(
                0
            )

        self.actualizar_resumen()

        self.actualizar_estado_controles()

        if errores:

            QMessageBox.warning(
                self,
                "Algunas imágenes no se añadieron",
                "\n\n".join(
                    errores
                )
            )


    # ================================================================
    # QUITAR SELECCIONADAS
    # ================================================================
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

            try:

                self.rutas_imagenes.remove(
                    ruta
                )

            except ValueError:

                pass

            self.cache_previsualizaciones.pop(
                self.clave_cache(
                    ruta
                ),
                None
            )

            self.resultados_por_origen.pop(
                self.clave_cache(
                    ruta
                ),
                None
            )

        if (
            self.lista_imagenes.count() > 0
            and self.lista_imagenes.currentRow() < 0
        ):

            self.lista_imagenes.setCurrentRow(
                0
            )

        if not self.rutas_imagenes:

            self.vista_antes.limpiar()

            self.vista_despues.limpiar()

            self.etiqueta_info.setText(
                "Selecciona una imagen para verla."
            )

        self.actualizar_resumen()

        self.actualizar_estado_controles()


    # ================================================================
    # LIMPIAR
    # ================================================================
    def limpiar_lista(
        self
    ):

        self.temporizador_previsualizacion.stop()

        self.rutas_imagenes.clear()

        self.lista_imagenes.clear()

        self.cache_previsualizaciones.clear()

        self.resultados_por_origen.clear()

        self.vista_antes.limpiar()

        self.vista_despues.limpiar()

        self.etiqueta_info.setText(
            "Selecciona una imagen para verla."
        )

        self.actualizar_resumen()

        self.actualizar_estado_controles()


    # ================================================================
    # ACTUALIZAR RESUMEN
    # ================================================================
    def actualizar_resumen(
        self
    ):

        cantidad = len(
            self.rutas_imagenes
        )

        seleccionadas = len(
            self.obtener_items_marcados()
        )

        if cantidad == 0:

            texto = "0 imágenes"

        elif cantidad == 1:

            texto = "1 imagen"

        else:

            texto = f"{cantidad} imágenes"

        if seleccionadas == 1:

            texto += " · 1 elegida para mejorar"

        self.etiqueta_total.setText(
            texto
        )

        self.boton_mejorar.setText(
            "Mejorar imagen"
        )


    # ================================================================
    # ACTUALIZAR PREVISUALIZACION
    # ================================================================
    def actualizar_previsualizacion(
        self,
        item_actual,
        item_anterior
    ):

        self.temporizador_previsualizacion.stop()

        self.item_previsualizacion_pendiente = (
            item_actual
        )

        if item_actual is None:

            self.vista_antes.limpiar()

            self.vista_despues.limpiar()

            return

        informacion = item_actual.data(
            ROL_INFORMACION_IMAGEN
        )

        ruta = item_actual.data(
            Qt.ItemDataRole.UserRole
        )

        self.etiqueta_info.setText(
            (
                f"{informacion['formato']} · "
                f"{informacion['ancho']} × "
                f"{informacion['alto']} px · "
                f"{formatear_tamano(informacion['tamano'])}"
            )
        )

        pixmap = self.obtener_cache(
            ruta
        )

        if pixmap is not None:

            self.vista_antes.establecer_imagen(
                pixmap
            )

        resultado = self.resultados_por_origen.get(
            self.clave_cache(
                ruta
            )
        )

        if resultado:

            pixmap_resultado = self.obtener_cache(
                resultado
            )

            if pixmap_resultado is not None:

                self.vista_despues.establecer_imagen(
                    pixmap_resultado
                )

            else:

                self.vista_despues.limpiar(
                    "Cargando resultado..."
                )

        else:

            self.vista_despues.limpiar()

        self.temporizador_previsualizacion.start()


    # ================================================================
    # CARGAR PREVISUALIZACION PENDIENTE
    # ================================================================
    def cargar_previsualizacion_pendiente(
        self
    ):

        item = self.item_previsualizacion_pendiente

        self.item_previsualizacion_pendiente = None

        if (
            item is None
            or item is not self.lista_imagenes.currentItem()
        ):

            return

        ruta = item.data(
            Qt.ItemDataRole.UserRole
        )

        pixmap = self.obtener_cache(
            ruta
        )

        if pixmap is None:

            pixmap = cargar_pixmap_previsualizacion(
                ruta
            )

            self.guardar_cache(
                ruta,
                pixmap
            )

        if item is not self.lista_imagenes.currentItem():

            return

        self.vista_antes.establecer_imagen(
            pixmap
        )

        resultado = self.resultados_por_origen.get(
            self.clave_cache(
                ruta
            )
        )

        if not resultado:

            return

        pixmap_resultado = self.obtener_cache(
            resultado
        )

        if pixmap_resultado is None:

            pixmap_resultado = (
                cargar_pixmap_previsualizacion(
                    resultado
                )
            )

            self.guardar_cache(
                resultado,
                pixmap_resultado
            )

        if item is self.lista_imagenes.currentItem():

            self.vista_despues.establecer_imagen(
                pixmap_resultado
            )


    # ================================================================
    # ACTUALIZAR METODO
    # ================================================================
    def actualizar_metodo(
        self,
        *args
    ):

        modo = self.combo_metodo.currentData()

        es_ia = (
            modo == MODO_IA
        )

        self.combo_tipo.setEnabled(
            es_ia
        )

        if es_ia:

            estado = comprobar_motor_ia(
                self.combo_tipo.currentData()
            )

            if estado[
                "disponible"
            ]:

                self.etiqueta_motor.setText(
                    "✓ Motor IA local disponible."
                )

                self.etiqueta_motor.setStyleSheet(
                    "color: #8bd58b;"
                )

            else:

                self.etiqueta_motor.setText(
                    (
                        "⚠ "
                        + estado[
                            "mensaje"
                        ]
                    )
                )

                self.etiqueta_motor.setStyleSheet(
                    "color: #e3b66a;"
                )

        else:

            self.etiqueta_motor.setText(
                "La mejora clásica no requiere motor externo."
            )

            self.etiqueta_motor.setStyleSheet(
                "color: #aaaaaa;"
            )

        self.actualizar_estado_controles()


    # ================================================================
    # SELECCIONAR SALIDA
    # ================================================================
    def seleccionar_carpeta_salida(
        self
    ):

        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de salida",
            (
                self.carpeta_salida
                or os.path.expanduser(
                    "~"
                )
            )
        )

        if carpeta:

            self.carpeta_salida = carpeta

            self.campo_salida.setText(
                carpeta
            )


    # ================================================================
    # ACTUALIZAR ESTADO
    # ================================================================
    def actualizar_estado_controles(
        self
    ):

        hay_imagenes = bool(
            self.rutas_imagenes
        )

        procesando = (
            self.hilo is not None
        )

        hay_seleccionadas = bool(
            self.obtener_items_marcados()
        )

        modo_ia = (
            self.combo_metodo.currentData()
            == MODO_IA
        )

        ia_disponible = True

        if modo_ia:

            ia_disponible = comprobar_motor_ia(
                self.combo_tipo.currentData()
            )[
                "disponible"
            ]

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

        self.combo_metodo.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.combo_tipo.setEnabled(
            hay_imagenes
            and modo_ia
            and not procesando
        )

        self.combo_escala.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.check_transparencia.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.check_metadatos.setEnabled(
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

        self.boton_mejorar.setEnabled(
            hay_seleccionadas
            and ia_disponible
            and not procesando
        )

        self.boton_cancelar.setEnabled(
            procesando
        )


    # ================================================================
    # INICIAR MEJORA
    # ================================================================
    def iniciar_mejora(
        self
    ):

        rutas_seleccionadas = (
            self.obtener_rutas_marcadas()
        )

        if not rutas_seleccionadas:

            QMessageBox.information(
                self,
                "Selecciona una imagen",
                "Marca una imagen para mejorarla."
            )

            return

        rutas_seleccionadas = [
            rutas_seleccionadas[0]
        ]

        carpeta = (
            self.carpeta_salida
            or os.path.dirname(
                rutas_seleccionadas[0]
            )
        )

        sufijo = self.campo_sufijo.text().strip()

        if not sufijo:

            sufijo = "_mejorada"

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

        self.trabajador = TrabajadorMejorarCalidad(
            list(
                rutas_seleccionadas
            ),
            carpeta,
            self.combo_metodo.currentData(),
            self.combo_tipo.currentData(),
            self.combo_escala.currentData(),
            self.check_transparencia.isChecked(),
            self.check_metadatos.isChecked(),
            sufijo
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
            self.mejora_terminada
        )

        self.trabajador.cancelado.connect(
            self.mejora_cancelada
        )

        self.trabajador.error.connect(
            self.error_mejora
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


    # ================================================================
    # PROGRESO
    # ================================================================
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


    # ================================================================
    # CANCELAR
    # ================================================================
    def cancelar_mejora(
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


    # ================================================================
    # TERMINADO
    # ================================================================
    @Slot(
        object
    )
    def mejora_terminada(
        self,
        resultados
    ):

        self.barra_progreso.setValue(
            100
        )

        self.etiqueta_estado.setText(
            "Completado"
        )

        for resultado in resultados:

            self.resultados_por_origen[
                self.clave_cache(
                    resultado[
                        "ruta_origen"
                    ]
                )
            ] = resultado[
                "ruta"
            ]

        cantidad = len(
            resultados
        )

        if cantidad == 1:

            texto = (
                "1 imagen mejorada correctamente."
            )

        else:

            texto = (
                f"{cantidad} imágenes mejoradas "
                "correctamente."
            )

        self.mostrar_resultado_temporal(
            texto
        )

        self.actualizar_previsualizacion(
            self.lista_imagenes.currentItem(),
            None
        )


    # ================================================================
    # CANCELADO
    # ================================================================
    @Slot()
    def mejora_cancelada(
        self
    ):

        self.etiqueta_estado.setText(
            "Cancelado"
        )


    # ================================================================
    # ERROR
    # ================================================================
    @Slot(
        str
    )
    def error_mejora(
        self,
        mensaje
    ):

        self.etiqueta_estado.setText(
            "Error"
        )

        QMessageBox.critical(
            self,
            "Error al mejorar imágenes",
            mensaje
        )


    # ================================================================
    # LIMPIAR HILO
    # ================================================================
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


    # ================================================================
    # MOSTRAR RESULTADO TEMPORAL
    # ================================================================
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


    # ================================================================
    # TEMPORIZADOR DE RESULTADO
    # ================================================================
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


    # ================================================================
    # OCULTAR RESULTADO
    # ================================================================
    def ocultar_resultado_temporal(
        self
    ):

        self.temporizador_resultado.stop()

        self.contenedor_resultado.setVisible(
            False
        )

        self.barra_tiempo_resultado.setValue(
            0
        )


    # ================================================================
    # CANCELAR SI ESTA TRABAJANDO
    # ================================================================
    def cancelar_si_esta_trabajando(
        self
    ):

        if self.trabajador is not None:

            self.trabajador.cancelar()