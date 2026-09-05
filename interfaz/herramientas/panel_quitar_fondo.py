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
    QPainter,
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
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)

from funciones.configuracion_app import (
    obtener_ruta_recurso
)

from herramientas.imagenes.quitar_fondo import (
    METODO_AUTOMATICO,
    METODO_RAPIDO,
    METODO_EQUILIBRADO,
    METODO_PRECISO,

    RECORTE_SUAVE,
    RECORTE_NORMAL,
    RECORTE_FIRME,

    QuitarFondoCancelado,
    comprobar_motor_quitar_fondo,
    generar_ruta_salida,
    obtener_informacion_imagen,
    quitar_fondo_imagen
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
# CREAR FONDO CUADRICULADO
# ================================================================
def crear_fondo_cuadriculado(
    ancho,
    alto,
    tamano_celda=16
):

    ancho = max(
        1,
        int(
            ancho
        )
    )

    alto = max(
        1,
        int(
            alto
        )
    )

    pixmap = QPixmap(
        ancho,
        alto
    )

    pixmap.fill(
        QColor(
            230,
            230,
            230
        )
    )

    pintor = QPainter(
        pixmap
    )

    color_secundario = QColor(
        190,
        190,
        190
    )

    for y in range(
        0,
        alto,
        tamano_celda
    ):

        for x in range(
            0,
            ancho,
            tamano_celda
        ):

            if (
                (
                    x // tamano_celda
                    + y // tamano_celda
                )
                % 2
                == 1
            ):

                pintor.fillRect(
                    x,
                    y,
                    tamano_celda,
                    tamano_celda,
                    color_secundario
                )

    pintor.end()

    return pixmap


# ================================================================
# COMPONER TRANSPARENCIA
# ================================================================
def componer_sobre_cuadricula(
    pixmap
):

    if pixmap.isNull():

        return QPixmap()

    fondo = crear_fondo_cuadriculado(
        pixmap.width(),
        pixmap.height()
    )

    pintor = QPainter(
        fondo
    )

    pintor.drawPixmap(
        0,
        0,
        pixmap
    )

    pintor.end()

    return fondo


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
        mostrar_transparencia=False,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.texto_vacio = texto_vacio

        self.mostrar_transparencia = (
            mostrar_transparencia
        )

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

        if self.mostrar_transparencia:

            pixmap = componer_sobre_cuadricula(
                pixmap
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
def obtener_ruta_icono_cierre(
    nombre
):

    ruta_recursos = obtener_ruta_recurso(
        "iconos",
        nombre
    )

    if os.path.isfile(
        ruta_recursos
    ):

        return ruta_recursos

    # Compatibilidad con la ubicación que usa actualmente
    # panel_mejorar_calidad.py en el proyecto local.
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "recursos",
            "iconos",
            nombre
        )
    )


RUTA_CERRAR_NORMAL = obtener_ruta_icono_cierre(
    "cerrar_normal.png"
)

RUTA_CERRAR_HOVER = obtener_ruta_icono_cierre(
    "cerrar_hover.png"
)

RUTA_CERRAR_PRESIONADA = obtener_ruta_icono_cierre(
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
        mostrar_transparencia=False,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.ruta_imagen = ruta_imagen

        self.mostrar_transparencia = (
            mostrar_transparencia
        )

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

        if self.mostrar_transparencia:

            pixmap = componer_sobre_cuadricula(
                pixmap
            )

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
class TrabajadorQuitarFondo(
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
        metodo,
        suavizado_bordes,
        recorte,
        conservar_transparencia,
        conservar_metadatos
    ):

        super().__init__()

        self.ruta_origen = ruta_origen

        self.ruta_destino = ruta_destino

        self.metodo = metodo

        self.suavizado_bordes = (
            suavizado_bordes
        )

        self.recorte = recorte

        self.conservar_transparencia = (
            conservar_transparencia
        )

        self.conservar_metadatos = (
            conservar_metadatos
        )

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

            resultado = quitar_fondo_imagen(
                self.ruta_origen,
                self.ruta_destino,
                metodo=self.metodo,
                suavizado_bordes=(
                    self.suavizado_bordes
                ),
                recorte=self.recorte,
                conservar_transparencia_original=(
                    self.conservar_transparencia
                ),
                conservar_metadatos=(
                    self.conservar_metadatos
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

        except QuitarFondoCancelado:

            self.cancelado.emit()

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
# PANEL QUITAR FONDO
# ================================================================
class PanelQuitarFondo(
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
            "Quitar fondo"
        )

        titulo.setStyleSheet(
            "font-size: 22px; font-weight: 600;"
        )

        descripcion = QLabel(
            "Elimina el fondo de una imagen con modelos de "
            "segmentación IA que se ejecutan completamente en tu equipo."
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
            "Sólo una casilla puede estar marcada para procesar."
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
        #       Original y sin fondo          #
        # ----------------------------------- #

        fila_previsualizaciones = QHBoxLayout()

        fila_previsualizaciones.setSpacing(
            8
        )

        contenedor_original = QWidget()

        layout_original = QVBoxLayout(
            contenedor_original
        )

        layout_original.setContentsMargins(
            0,
            0,
            0,
            0
        )

        etiqueta_original = QLabel(
            "Original"
        )

        etiqueta_original.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        etiqueta_original.setStyleSheet(
            "font-weight: 600;"
        )

        self.vista_original = VistaPreviaImagen(
            "Selecciona una imagen",
            False,
            self
        )

        layout_original.addWidget(
            etiqueta_original
        )

        layout_original.addWidget(
            self.vista_original,
            1
        )

        contenedor_resultado = QWidget()

        layout_resultado_imagen = QVBoxLayout(
            contenedor_resultado
        )

        layout_resultado_imagen.setContentsMargins(
            0,
            0,
            0,
            0
        )

        etiqueta_sin_fondo = QLabel(
            "Sin fondo"
        )

        etiqueta_sin_fondo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        etiqueta_sin_fondo.setStyleSheet(
            "font-weight: 600;"
        )

        self.vista_sin_fondo = VistaPreviaImagen(
            "El resultado aparecerá aquí",
            True,
            self
        )

        layout_resultado_imagen.addWidget(
            etiqueta_sin_fondo
        )

        layout_resultado_imagen.addWidget(
            self.vista_sin_fondo,
            1
        )

        fila_previsualizaciones.addWidget(
            contenedor_original,
            1
        )

        fila_previsualizaciones.addWidget(
            contenedor_resultado,
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

        self.scroll_controles = QScrollArea()

        self.scroll_controles.setWidgetResizable(
            True
        )

        self.scroll_controles.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_controles.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scroll_controles.verticalScrollBar().setSingleStep(
            28
        )

        self.scroll_controles.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_controles.setMinimumWidth(
            320
        )

        self.scroll_controles.setMaximumWidth(
            365
        )

        self.scroll_controles.setStyleSheet(
            """
            QScrollArea {
                background-color: transparent;
                border: none;
            }

            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            """
        )

        panel_controles = QFrame()

        panel_controles.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        panel_controles.setMinimumWidth(
            300
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

        # Evitar que Qt comprima verticalmente los controles.
        # Si el contenido no cabe, el desplazamiento lo gestiona
        # exclusivamente el QScrollArea.
        layout_controles.setSizeConstraint(
            QLayout.SizeConstraint.SetMinimumSize
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
            "Automático recomendado · IS-Net",
            METODO_AUTOMATICO
        )

        self.combo_metodo.addItem(
            "Rápido · U²-NetP",
            METODO_RAPIDO
        )

        self.combo_metodo.addItem(
            "Equilibrado · IS-Net",
            METODO_EQUILIBRADO
        )

        self.combo_metodo.addItem(
            "Alta precisión · BiRefNet",
            METODO_PRECISO
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
        #            Refinado                 #
        # ----------------------------------- #

        etiqueta_refinado = QLabel(
            "Refinado"
        )

        etiqueta_refinado.setStyleSheet(
            "font-weight: 600;"
        )

        layout_controles.addWidget(
            etiqueta_refinado
        )

        fila_refinado = QHBoxLayout()

        columna_suavizado = QVBoxLayout()

        columna_suavizado.addWidget(
            QLabel(
                "Suavizado de bordes"
            )
        )

        self.combo_suavizado = QComboBox()

        for valor in range(
            0,
            6
        ):

            self.combo_suavizado.addItem(
                f"{valor} px",
                valor
            )

        self.combo_suavizado.setCurrentIndex(
            1
        )

        columna_suavizado.addWidget(
            self.combo_suavizado
        )

        columna_recorte = QVBoxLayout()

        columna_recorte.addWidget(
            QLabel(
                "Transparencia"
            )
        )

        self.combo_recorte = QComboBox()

        self.combo_recorte.addItem(
            "Suave",
            RECORTE_SUAVE
        )

        self.combo_recorte.addItem(
            "Normal",
            RECORTE_NORMAL
        )

        self.combo_recorte.addItem(
            "Firme",
            RECORTE_FIRME
        )

        self.combo_recorte.setCurrentIndex(
            1
        )

        columna_recorte.addWidget(
            self.combo_recorte
        )

        fila_refinado.addLayout(
            columna_suavizado,
            1
        )

        fila_refinado.addLayout(
            columna_recorte,
            1
        )

        layout_controles.addLayout(
            fila_refinado
        )


        # ----------------------------------- #
        #             Opciones                #
        # ----------------------------------- #

        self.check_transparencia = QCheckBox(
            "Conservar transparencia previa"
        )

        self.check_transparencia.setChecked(
            True
        )

        self.check_metadatos = QCheckBox(
            "Conservar metadatos compatibles"
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
            "Los modelos se ejecutan completamente en tu equipo. "
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
            "_sin_fondo"
        )

        fila_sufijo.addWidget(
            self.campo_sufijo,
            1
        )

        layout_controles.addLayout(
            fila_sufijo
        )

        nota_png = QLabel(
            "La salida se guarda siempre como PNG para conservar transparencia."
        )

        nota_png.setWordWrap(
            True
        )

        nota_png.setStyleSheet(
            "color: #8f8f8f; font-size: 12px;"
        )

        layout_controles.addWidget(
            nota_png
        )

        layout_controles.addStretch()

        panel_controles.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.MinimumExpanding
        )

        panel_controles.adjustSize()

        panel_controles.setMinimumHeight(
            max(
                620,
                panel_controles.sizeHint().height()
            )
        )

        self.scroll_controles.setWidget(
            panel_controles
        )

        fila_contenido.addWidget(
            self.scroll_controles
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
            "ResultadoQuitarFondo"
        )

        self.contenedor_resultado.setVisible(
            False
        )

        self.contenedor_resultado.setStyleSheet(
            """
            QFrame#ResultadoQuitarFondo {
                border: 1px solid rgba(100, 170, 255, 150);
                border-radius: 7px;
                background-color: rgba(50, 100, 170, 40);
            }

            QFrame#ResultadoQuitarFondo QLabel {
                border: none;
                background-color: transparent;
                color: #d9e9ff;
            }

            QFrame#ResultadoQuitarFondo QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 35);
                border-radius: 2px;
            }

            QFrame#ResultadoQuitarFondo QProgressBar::chunk {
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
            190
        )

        self.barra_progreso = QProgressBar()

        self.barra_progreso.setRange(
            0,
            100
        )

        self.boton_procesar = QPushButton(
            "Quitar fondo"
        )

        self.boton_procesar.setMinimumWidth(
            155
        )

        self.boton_procesar.setMinimumHeight(
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
            self.boton_procesar
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

        self.lista_imagenes.itemChanged.connect(
            self.estado_item_cambiado
        )

        self.vista_original.clic_solicitado.connect(
            self.abrir_vista_original
        )

        self.vista_sin_fondo.clic_solicitado.connect(
            self.abrir_vista_resultado
        )

        self.combo_metodo.currentIndexChanged.connect(
            self.actualizar_metodo
        )

        self.boton_salida.clicked.connect(
            self.seleccionar_carpeta_salida
        )

        self.boton_procesar.clicked.connect(
            self.iniciar_proceso
        )

        self.boton_cancelar.clicked.connect(
            self.cancelar_proceso
        )


    # ============================================================
    # CONFIGURAR NAVEGACION
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
    # FILTRAR FLECHAS
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


    # ============================================================
    # COMPROBAR FOCO
    # ============================================================
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


    # ============================================================
    # MOVER IMAGEN ACTIVA
    # ============================================================
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


    # ============================================================
    # CLAVE DE CACHE
    # ============================================================
    def clave_cache(
        self,
        ruta
    ):

        return os.path.normcase(
            os.path.abspath(
                ruta
            )
        )


    # ============================================================
    # OBTENER CACHE
    # ============================================================
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


    # ============================================================
    # GUARDAR CACHE
    # ============================================================
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


    # ============================================================
    # OBTENER ITEM MARCADO
    # ============================================================
    def obtener_item_marcado(
        self
    ):

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

                return item

        return None


    # ============================================================
    # OBTENER RUTA MARCADA
    # ============================================================
    def obtener_ruta_marcada(
        self
    ):

        item = self.obtener_item_marcado()

        if item is None:

            return None

        return item.data(
            Qt.ItemDataRole.UserRole
        )


    # ============================================================
    # ESTADO DE ITEM CAMBIADO
    # ============================================================
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


    # ============================================================
    # ABRIR VISTA ORIGINAL
    # ============================================================
    def abrir_vista_original(
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
            False,
            self
        ).mostrar()


    # ============================================================
    # ABRIR VISTA RESULTADO
    # ============================================================
    def abrir_vista_resultado(
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
            True,
            self
        ).mostrar()


    # ============================================================
    # ARRASTRAR ARCHIVOS
    # ============================================================
    def dragEnterEvent(
        self,
        evento
    ):

        if evento.mimeData().hasUrls():

            evento.acceptProposedAction()

        else:

            evento.ignore()


    # ============================================================
    # SOLTAR ARCHIVOS
    # ============================================================
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
                "Imágenes "
                "(*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff);;"
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

            self.vista_original.limpiar()

            self.vista_sin_fondo.limpiar()

            self.etiqueta_info.setText(
                "Selecciona una imagen para verla."
            )

        self.actualizar_resumen()

        self.actualizar_estado_controles()


    # ============================================================
    # LIMPIAR
    # ============================================================
    def limpiar_lista(
        self
    ):

        self.temporizador_previsualizacion.stop()

        self.rutas_imagenes.clear()

        self.lista_imagenes.clear()

        self.cache_previsualizaciones.clear()

        self.resultados_por_origen.clear()

        self.vista_original.limpiar()

        self.vista_sin_fondo.limpiar()

        self.etiqueta_info.setText(
            "Selecciona una imagen para verla."
        )

        self.actualizar_resumen()

        self.actualizar_estado_controles()


    # ============================================================
    # ACTUALIZAR RESUMEN
    # ============================================================
    def actualizar_resumen(
        self
    ):

        cantidad = len(
            self.rutas_imagenes
        )

        hay_marcada = (
            self.obtener_item_marcado()
            is not None
        )

        if cantidad == 0:

            texto = "0 imágenes"

        elif cantidad == 1:

            texto = "1 imagen"

        else:

            texto = f"{cantidad} imágenes"

        if hay_marcada:

            texto += " · 1 elegida para procesar"

        self.etiqueta_total.setText(
            texto
        )

        self.boton_procesar.setText(
            "Quitar fondo"
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

        self.item_previsualizacion_pendiente = (
            item_actual
        )

        if item_actual is None:

            self.vista_original.limpiar()

            self.vista_sin_fondo.limpiar()

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

            self.vista_original.establecer_imagen(
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

                self.vista_sin_fondo.establecer_imagen(
                    pixmap_resultado
                )

            else:

                self.vista_sin_fondo.limpiar(
                    "Cargando resultado..."
                )

        else:

            self.vista_sin_fondo.limpiar()

        self.temporizador_previsualizacion.start()


    # ============================================================
    # CARGAR PREVISUALIZACION PENDIENTE
    # ============================================================
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

        self.vista_original.establecer_imagen(
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

            self.vista_sin_fondo.establecer_imagen(
                pixmap_resultado
            )


    # ============================================================
    # ACTUALIZAR METODO
    # ============================================================
    def actualizar_metodo(
        self,
        *args
    ):

        metodo = self.combo_metodo.currentData()

        estado = comprobar_motor_quitar_fondo(
            metodo
        )

        if estado[
            "disponible"
        ]:

            if metodo == METODO_RAPIDO:

                detalle = (
                    "Rápido y ligero; ideal para recortes sencillos."
                )

            elif metodo == METODO_PRECISO:

                detalle = (
                    "Mayor precisión; puede tardar considerablemente más."
                )

            else:

                detalle = (
                    "Buen equilibrio entre calidad y tiempo de procesamiento."
                )

            self.etiqueta_motor.setText(
                "✓ Modelo local disponible. "
                + detalle
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

        self.actualizar_estado_controles()


    # ============================================================
    # SELECCIONAR SALIDA
    # ============================================================
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


    # ============================================================
    # ACTUALIZAR ESTADO
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

        hay_marcada = (
            self.obtener_item_marcado()
            is not None
        )

        estado_motor = comprobar_motor_quitar_fondo(
            self.combo_metodo.currentData()
        )

        motor_disponible = estado_motor[
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

        self.combo_suavizado.setEnabled(
            hay_imagenes
            and not procesando
        )

        self.combo_recorte.setEnabled(
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

        self.boton_procesar.setEnabled(
            hay_marcada
            and motor_disponible
            and not procesando
        )

        self.boton_cancelar.setEnabled(
            procesando
        )


    # ============================================================
    # INICIAR PROCESO
    # ============================================================
    def iniciar_proceso(
        self
    ):

        ruta_origen = self.obtener_ruta_marcada()

        if not ruta_origen:

            QMessageBox.information(
                self,
                "Selecciona una imagen",
                "Marca una imagen para quitarle el fondo."
            )

            return

        carpeta = (
            self.carpeta_salida
            or os.path.dirname(
                ruta_origen
            )
        )

        sufijo = self.campo_sufijo.text().strip()

        if not sufijo:

            sufijo = "_sin_fondo"

        try:

            ruta_destino = generar_ruta_salida(
                ruta_origen,
                carpeta,
                sufijo=sufijo,
                sobrescribir=False
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error en la salida",
                str(
                    error
                )
            )

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

        self.trabajador = TrabajadorQuitarFondo(
            ruta_origen,
            str(
                ruta_destino
            ),
            self.combo_metodo.currentData(),
            self.combo_suavizado.currentData(),
            self.combo_recorte.currentData(),
            self.check_transparencia.isChecked(),
            self.check_metadatos.isChecked()
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
            self.proceso_terminado
        )

        self.trabajador.cancelado.connect(
            self.proceso_cancelado
        )

        self.trabajador.error.connect(
            self.error_proceso
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
    # PROGRESO
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
    # CANCELAR
    # ============================================================
    def cancelar_proceso(
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
    # TERMINADO
    # ============================================================
    @Slot(
        object
    )
    def proceso_terminado(
        self,
        resultado
    ):

        self.barra_progreso.setValue(
            100
        )

        self.etiqueta_estado.setText(
            "Completado"
        )

        ruta_origen = resultado[
            "ruta_origen"
        ]

        ruta_resultado = resultado[
            "ruta"
        ]

        self.resultados_por_origen[
            self.clave_cache(
                ruta_origen
            )
        ] = ruta_resultado

        self.cache_previsualizaciones.pop(
            self.clave_cache(
                ruta_resultado
            ),
            None
        )

        self.mostrar_resultado_temporal(
            (
                "Fondo eliminado correctamente con "
                f"{resultado['nombre_modelo']}."
            )
        )

        self.actualizar_previsualizacion(
            self.lista_imagenes.currentItem(),
            None
        )


    # ============================================================
    # CANCELADO
    # ============================================================
    @Slot()
    def proceso_cancelado(
        self
    ):

        self.etiqueta_estado.setText(
            "Cancelado"
        )


    # ============================================================
    # ERROR
    # ============================================================
    @Slot(
        str
    )
    def error_proceso(
        self,
        mensaje
    ):

        self.etiqueta_estado.setText(
            "Error"
        )

        QMessageBox.critical(
            self,
            "Error al quitar fondo",
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
    # TEMPORIZADOR DE RESULTADO
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
    # OCULTAR RESULTADO
    # ============================================================
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


    # ============================================================
    # CANCELAR SI ESTA TRABAJANDO
    # ============================================================
    def cancelar_si_esta_trabajando(
        self
    ):

        if self.trabajador is not None:

            self.trabajador.cancelar()
