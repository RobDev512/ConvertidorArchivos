import os

from PySide6.QtCore import (
    Qt,
    QUrl
)

from PySide6.QtGui import (
    QDesktopServices,
    QIcon,
    QPixmap
)

from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget
)

from funciones.configuracion_app import (
    NOMBRE_APLICACION,
    VERSION_APLICACION,
    obtener_carpeta_licencias,
    obtener_ruta_icono_principal,
    obtener_ruta_icono_windows
)


# ================================================================
# DIÁLOGO ACERCA DE
# ================================================================
class DialogoAcercaDe(QDialog):

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

        self.configurar_ventana()
        self.crear_interfaz()


    # ============================================================
    # CONFIGURAR VENTANA
    # ============================================================
    def configurar_ventana(
        self
    ):

        self.setWindowTitle(
            f"Acerca de {NOMBRE_APLICACION}"
        )

        self.setModal(
            True
        )

        self.resize(
            520,
            650
        )

        self.setMinimumSize(
            470,
            540
        )


        # ----------------------------------- #
        #        Icono de la ventana          #
        # ----------------------------------- #

        ruta_icono = obtener_ruta_icono_windows()


        if os.path.isfile(
            ruta_icono
        ):

            self.setWindowIcon(
                QIcon(
                    ruta_icono
                )
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
            28,
            24,
            28,
            24
        )

        layout_principal.setSpacing(
            18
        )


        # ----------------------------------- #
        #             Cabecera                #
        # ----------------------------------- #

        cabecera = self.crear_cabecera()

        layout_principal.addWidget(
            cabecera
        )


        # ----------------------------------- #
        #           Separador                 #
        # ----------------------------------- #

        separador = QFrame()

        separador.setFrameShape(
            QFrame.Shape.HLine
        )

        separador.setFrameShadow(
            QFrame.Shadow.Sunken
        )

        layout_principal.addWidget(
            separador
        )


        # ----------------------------------- #
        #            Contenido                #
        # ----------------------------------- #

        contenido = self.crear_contenido()

        layout_principal.addWidget(
            contenido,
            1
        )


        # ----------------------------------- #
        #             Botones                 #
        # ----------------------------------- #

        layout_botones = QHBoxLayout()

        layout_botones.setSpacing(
            10
        )


        # ----------------------------------- #
        #      Licencias de terceros          #
        # ----------------------------------- #

        self.boton_licencias = QPushButton(
            "Licencias de terceros"
        )

        self.boton_licencias.clicked.connect(
            self.abrir_licencias
        )


        carpeta_licencias = obtener_carpeta_licencias()


        if not os.path.isdir(
            carpeta_licencias
        ):

            self.boton_licencias.setEnabled(
                False
            )

            self.boton_licencias.setToolTip(
                "La carpeta de licencias todavía no está disponible."
            )


        layout_botones.addWidget(
            self.boton_licencias
        )

        layout_botones.addStretch()


        # ----------------------------------- #
        #              Cerrar                 #
        # ----------------------------------- #

        boton_cerrar = QPushButton(
            "Cerrar"
        )

        boton_cerrar.setMinimumWidth(
            100
        )

        boton_cerrar.clicked.connect(
            self.accept
        )

        boton_cerrar.setDefault(
            True
        )

        layout_botones.addWidget(
            boton_cerrar
        )


        layout_principal.addLayout(
            layout_botones
        )


    # ============================================================
    # CREAR CABECERA
    # ============================================================
    def crear_cabecera(
        self
    ):

        contenedor = QWidget()

        layout = QVBoxLayout(
            contenedor
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            8
        )

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        # ----------------------------------- #
        #               Logo                  #
        # ----------------------------------- #

        etiqueta_logo = QLabel()

        etiqueta_logo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        etiqueta_logo.setFixedSize(
            170,
            170
        )


        ruta_logo = obtener_ruta_icono_principal()


        if os.path.isfile(
            ruta_logo
        ):

            pixmap = QPixmap(
                ruta_logo
            )


            if not pixmap.isNull():

                pixmap = pixmap.scaled(
                    160,
                    160,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                etiqueta_logo.setPixmap(
                    pixmap
                )


        layout.addWidget(
            etiqueta_logo,
            alignment=Qt.AlignmentFlag.AlignCenter
        )


        # ----------------------------------- #
        #         Nombre de aplicación        #
        # ----------------------------------- #

        etiqueta_nombre = QLabel(
            NOMBRE_APLICACION
        )

        etiqueta_nombre.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        etiqueta_nombre.setStyleSheet(
            """
            QLabel {
                font-size: 23px;
                font-weight: 600;
            }
            """
        )

        layout.addWidget(
            etiqueta_nombre
        )


        # ----------------------------------- #
        #             Versión                 #
        # ----------------------------------- #

        etiqueta_version = QLabel(
            f"Versión {VERSION_APLICACION}"
        )

        etiqueta_version.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        etiqueta_version.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                color: #777777;
            }
            """
        )

        layout.addWidget(
            etiqueta_version
        )


        return contenedor


    # ============================================================
    # CREAR CONTENIDO
    # ============================================================
    def crear_contenido(
        self
    ):

        area = QScrollArea()

        area.setWidgetResizable(
            True
        )

        area.setFrameShape(
            QFrame.Shape.NoFrame
        )


        contenido = QWidget()

        layout = QVBoxLayout(
            contenido
        )

        layout.setContentsMargins(
            4,
            2,
            4,
            2
        )

        layout.setSpacing(
            16
        )


        # ----------------------------------- #
        #          Descripción                #
        # ----------------------------------- #

        descripcion = QLabel(
            "Aplicación de escritorio para convertir archivos "
            "de forma local entre diferentes formatos."
        )

        descripcion.setWordWrap(
            True
        )

        descripcion.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        descripcion.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(
            descripcion
        )


        # ----------------------------------- #
        #             Motores                 #
        # ----------------------------------- #

        titulo_motores = self.crear_titulo_seccion(
            "Motores y tecnologías"
        )

        layout.addWidget(
            titulo_motores
        )


        motores = QLabel(
            "• LibreOffice\n"
            "• ImageMagick\n"
            "• 7-Zip\n"
            "• Pandoc\n"
            "• PDFium\n"
            "• Aspose.PDF\n"
            "• Microsoft Office, cuando está disponible\n"
            "• WinRAR, cuando está disponible"
        )

        motores.setWordWrap(
            True
        )

        motores.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(
            motores
        )


        # ----------------------------------- #
        #       Procesamiento local           #
        # ----------------------------------- #

        titulo_procesamiento = self.crear_titulo_seccion(
            "Procesamiento local"
        )

        layout.addWidget(
            titulo_procesamiento
        )


        procesamiento = QLabel(
            "Las conversiones se realizan localmente en el equipo. "
            "La aplicación utiliza sus motores incluidos y, cuando "
            "corresponde, programas compatibles disponibles en Windows."
        )

        procesamiento.setWordWrap(
            True
        )

        procesamiento.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(
            procesamiento
        )


        # ----------------------------------- #
        #       Componentes externos          #
        # ----------------------------------- #

        titulo_terceros = self.crear_titulo_seccion(
            "Componentes de terceros"
        )

        layout.addWidget(
            titulo_terceros
        )


        terceros = QLabel(
            "Convertidor de Archivos utiliza componentes, bibliotecas "
            "y motores desarrollados por terceros. Cada uno se encuentra "
            "sujeto a sus propios términos y licencias."
        )

        terceros.setWordWrap(
            True
        )

        terceros.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(
            terceros
        )


        # ----------------------------------- #
        #             Versión                 #
        # ----------------------------------- #

        titulo_version = self.crear_titulo_seccion(
            "Información de versión"
        )

        layout.addWidget(
            titulo_version
        )


        informacion_version = QLabel(
            f"{NOMBRE_APLICACION}\n"
            f"Versión {VERSION_APLICACION}"
        )

        informacion_version.setWordWrap(
            True
        )

        informacion_version.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(
            informacion_version
        )


        layout.addStretch()


        area.setWidget(
            contenido
        )


        return area


    # ============================================================
    # CREAR TÍTULO DE SECCIÓN
    # ============================================================
    def crear_titulo_seccion(
        self,
        texto
    ):

        etiqueta = QLabel(
            texto
        )

        etiqueta.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                font-weight: 600;
            }
            """
        )

        return etiqueta


    # ============================================================
    # ABRIR LICENCIAS
    # ============================================================
    def abrir_licencias(
        self
    ):

        carpeta_licencias = obtener_carpeta_licencias()


        if not os.path.isdir(
            carpeta_licencias
        ):

            return


        QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                carpeta_licencias
            )
        )