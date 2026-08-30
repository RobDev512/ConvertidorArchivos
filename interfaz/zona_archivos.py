import os

from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
    QEvent
)

from PySide6.QtGui import (
    QIcon
)

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QToolButton,
    QSizePolicy
)

from funciones.configuracion_app import (
    obtener_ruta_recurso
)


# ================================================================
# ZONA DE ARCHIVOS
# ================================================================
class ZonaArchivos(QFrame):

    archivos_soltados = Signal(
        list
    )


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self
    ):

        super().__init__()


        # ----------------------------------- #
        #          Estado general             #
        # ----------------------------------- #

        self.texto_actual = (
            "No hay archivos seleccionados"
        )

        self.texto_accion = (
            "Subir desde tu dispositivo"
        )

        self.icono_normal = QIcon()

        self.icono_iluminado = QIcon()


        # ----------------------------------- #
        #          Configuración              #
        # ----------------------------------- #

        self.setObjectName(
            "zonaArchivos"
        )

        self.setAcceptDrops(
            True
        )


        # La zona puede crecer verticalmente,
        # pero nunca cambia de tamaño por
        # aparecer el nombre del archivo.
        self.setMinimumHeight(
            300
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )


        self.crear_interfaz()
        self.cargar_iconos()
        self.aplicar_estilo()


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
            22,
            30,
            22,
            30
        )

        self.distribucion.setSpacing(
            8
        )


        # ----------------------------------- #
        #       Espacio superior flexible     #
        # ----------------------------------- #

        self.distribucion.addStretch(
            1
        )


        # ----------------------------------- #
        #      Archivo actualmente elegido    #
        # ----------------------------------- #

        self.etiqueta_archivo = QLabel()

        self.etiqueta_archivo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_archivo.setWordWrap(
            True
        )


        # Reservamos siempre el mismo espacio.
        # Así el cuadro y el contenido no
        # "saltan" al seleccionar un archivo.
        self.etiqueta_archivo.setFixedHeight(
            42
        )

        self.etiqueta_archivo.setStyleSheet(
            """
            QLabel {
                border: none;
                font-size: 13px;
                font-weight: 600;
                padding: 0px 8px;
            }
            """
        )


        self.distribucion.addWidget(
            self.etiqueta_archivo
        )


        # ----------------------------------- #
        #       Botón principal grande        #
        # ----------------------------------- #

        self.boton_seleccionar_archivos = QToolButton()

        self.boton_seleccionar_archivos.setText(
            self.texto_accion
        )

        self.boton_seleccionar_archivos.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )

        self.boton_seleccionar_archivos.setIconSize(
            QSize(
                56,
                56
            )
        )

        self.boton_seleccionar_archivos.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.boton_seleccionar_archivos.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.boton_seleccionar_archivos.setMinimumHeight(
            135
        )

        self.boton_seleccionar_archivos.setAcceptDrops(
            False
        )


        # Detectar entrada/salida del ratón
        self.boton_seleccionar_archivos.installEventFilter(
            self
        )


        self.distribucion.addWidget(
            self.boton_seleccionar_archivos
        )


        # ----------------------------------- #
        #       Espacio inferior flexible     #
        # ----------------------------------- #

        self.distribucion.addStretch(
            1
        )


    # ============================================================
    # CARGAR ICONOS
    # ============================================================
    def cargar_iconos(
        self
    ):

        ruta_normal = obtener_ruta_recurso(
            "iconos",
            "subir001.png"
        )

        ruta_iluminado = obtener_ruta_recurso(
            "iconos",
            "subir002.png"
        )


        # ----------------------------------- #
        #          Icono normal               #
        # ----------------------------------- #

        if os.path.isfile(
            ruta_normal
        ):

            self.icono_normal = QIcon(
                ruta_normal
            )


        # ----------------------------------- #
        #         Icono iluminado             #
        # ----------------------------------- #

        if os.path.isfile(
            ruta_iluminado
        ):

            self.icono_iluminado = QIcon(
                ruta_iluminado
            )


        self.actualizar_icono(
            False
        )


    # ============================================================
    # ACTUALIZAR ICONO
    # ============================================================
    def actualizar_icono(
        self,
        iluminado
    ):

        if (
            iluminado
            and not self.icono_iluminado.isNull()
        ):

            self.boton_seleccionar_archivos.setIcon(
                self.icono_iluminado
            )

            return


        if not self.icono_normal.isNull():

            self.boton_seleccionar_archivos.setIcon(
                self.icono_normal
            )


    # ============================================================
    # APLICAR ESTILO
    # ============================================================
    def aplicar_estilo(
        self
    ):

        self.setStyleSheet(
            """
            QFrame#zonaArchivos {
                border: 2px dashed palette(mid);
                border-radius: 18px;
                background-color: transparent;
            }

            QFrame#zonaArchivos[arrastrando="true"] {
                border: 2px dashed palette(highlight);
            }

            QToolButton {
                border: none;
                background-color: transparent;
                color: palette(text);
                font-size: 16px;
                font-weight: 600;
                padding: 14px;
            }

            QToolButton:hover {
                color: palette(highlight);
            }

            QToolButton:pressed {
                padding-top: 16px;
                padding-bottom: 12px;
            }
            """
        )


    # ============================================================
    # FILTRO DE EVENTOS
    # ============================================================
    def eventFilter(
        self,
        objeto,
        evento
    ):

        if objeto is self.boton_seleccionar_archivos:

            if evento.type() == QEvent.Type.Enter:

                self.actualizar_icono(
                    True
                )


            elif evento.type() == QEvent.Type.Leave:

                self.actualizar_icono(
                    False
                )


        return super().eventFilter(
            objeto,
            evento
        )


    # ============================================================
    # ACTUALIZAR TEXTO
    # ============================================================
    def actualizar_texto(
        self,
        texto
    ):

        self.texto_actual = texto


        # ----------------------------------- #
        #       Sin archivo seleccionado      #
        # ----------------------------------- #

        if (
            not texto
            or texto
            == "No hay archivos seleccionados"
        ):

            self.etiqueta_archivo.clear()

            self.etiqueta_archivo.setToolTip(
                ""
            )

            return


        # ----------------------------------- #
        #        Mostrar selección            #
        # ----------------------------------- #

        self.etiqueta_archivo.setText(
            texto
        )

        self.etiqueta_archivo.setToolTip(
            texto
        )


    # ============================================================
    # CAMBIAR ESTADO DE ARRASTRE
    # ============================================================
    def establecer_arrastrando(
        self,
        activo
    ):

        self.setProperty(
            "arrastrando",
            activo
        )


        self.style().unpolish(
            self
        )

        self.style().polish(
            self
        )

        self.update()


        self.actualizar_icono(
            activo
        )


    # ============================================================
    # ARCHIVOS ENTRANDO A LA ZONA
    # ============================================================
    def dragEnterEvent(
        self,
        evento
    ):

        if not evento.mimeData().hasUrls():

            evento.ignore()

            return


        archivos = []


        for url in evento.mimeData().urls():

            ruta = url.toLocalFile()


            if (
                ruta
                and os.path.isfile(
                    ruta
                )
            ):

                archivos.append(
                    ruta
                )


        # ----------------------------------- #
        #       Existen archivos válidos      #
        # ----------------------------------- #

        if archivos:

            cantidad = len(
                archivos
            )


            if cantidad == 1:

                texto = (
                    "Suelta el archivo aquí"
                )

            else:

                texto = (
                    f"Suelta los {cantidad} "
                    f"archivos aquí"
                )


            self.boton_seleccionar_archivos.setText(
                texto
            )

            self.establecer_arrastrando(
                True
            )

            evento.acceptProposedAction()


        else:

            evento.ignore()


    # ============================================================
    # ARCHIVOS MOVIÉNDOSE SOBRE LA ZONA
    # ============================================================
    def dragMoveEvent(
        self,
        evento
    ):

        if evento.mimeData().hasUrls():

            evento.acceptProposedAction()

        else:

            evento.ignore()


    # ============================================================
    # ARCHIVOS SALIENDO DE LA ZONA
    # ============================================================
    def dragLeaveEvent(
        self,
        evento
    ):

        self.boton_seleccionar_archivos.setText(
            self.texto_accion
        )

        self.establecer_arrastrando(
            False
        )

        evento.accept()


    # ============================================================
    # SOLTAR ARCHIVOS
    # ============================================================
    def dropEvent(
        self,
        evento
    ):

        archivos = []


        for url in evento.mimeData().urls():

            ruta = url.toLocalFile()


            if (
                ruta
                and os.path.isfile(
                    ruta
                )
            ):

                archivos.append(
                    ruta
                )


        # ----------------------------------- #
        #       Recuperar aspecto normal      #
        # ----------------------------------- #

        self.boton_seleccionar_archivos.setText(
            self.texto_accion
        )

        self.establecer_arrastrando(
            False
        )


        # ----------------------------------- #
        #           Emitir archivos           #
        # ----------------------------------- #

        if archivos:

            self.archivos_soltados.emit(
                archivos
            )

            evento.acceptProposedAction()


        else:

            evento.ignore()