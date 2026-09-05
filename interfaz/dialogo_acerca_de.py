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
# DIALOGO ACERCA DE
# ================================================================
class DialogoAcercaDe(
    QDialog
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
            560,
            700
        )

        self.setMinimumSize(
            500,
            570
        )

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

        cabecera = self.crear_cabecera()

        layout_principal.addWidget(
            cabecera
        )

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

        contenido = self.crear_contenido()

        layout_principal.addWidget(
            contenido,
            1
        )

        layout_botones = QHBoxLayout()

        layout_botones.setSpacing(
            10
        )

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
                color: #8a8a8a;
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

        descripcion = QLabel(
            "Aplicación de escritorio para convertir archivos y "
            "trabajar con documentos e imágenes de forma local."
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

        titulo_novedades = self.crear_titulo_seccion(
            "Novedades de la versión 1.1.1"
        )

        layout.addWidget(
            titulo_novedades
        )

        novedades = QLabel(
            "• Motor propio PDF → DOCX, sin Aspose.PDF\n"
            "• Redimensionar imágenes\n"
            "• Comprimir imágenes\n"
            "• Imágenes → PDF\n"
            "• Mejorar calidad con Real-ESRGAN o método clásico\n"
            "• Quitar fondo con modelos de IA locales"
        )

        novedades.setWordWrap(
            True
        )

        novedades.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(
            novedades
        )

        titulo_imagenes = self.crear_titulo_seccion(
            "Imagen e inteligencia artificial"
        )

        layout.addWidget(
            titulo_imagenes
        )

        imagenes = QLabel(
            "• Pillow\n"
            "• NumPy\n"
            "• Real-ESRGAN NCNN/Vulkan\n"
            "• rembg\n"
            "• ONNX Runtime\n"
            "• U²-NetP\n"
            "• IS-Net General Use\n"
            "• BiRefNet General"
        )

        imagenes.setWordWrap(
            True
        )

        imagenes.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(
            imagenes
        )

        titulo_motores = self.crear_titulo_seccion(
            "Motores y tecnologías"
        )

        layout.addWidget(
            titulo_motores
        )

        motores = QLabel(
            "• Motor propio PDF → DOCX\n"
            "• LibreOffice\n"
            "• ImageMagick\n"
            "• 7-Zip\n"
            "• Pandoc\n"
            "• PDFium\n"
            "• pypdf\n"
            "• pdfplumber\n"
            "• pikepdf\n"
            "• python-docx\n"
            "• lxml\n"
            "• OpenPyXL\n"
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

        titulo_procesamiento = self.crear_titulo_seccion(
            "Procesamiento local"
        )

        layout.addWidget(
            titulo_procesamiento
        )

        procesamiento = QLabel(
            "Las conversiones y las herramientas de imágenes se "
            "ejecutan localmente en el equipo. Los modelos de IA "
            "incluidos no necesitan subir imágenes a servicios externos "
            "ni requieren conexión a Internet durante su uso."
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

        titulo_terceros = self.crear_titulo_seccion(
            "Componentes de terceros"
        )

        layout.addWidget(
            titulo_terceros
        )

        terceros = QLabel(
            "Convertidor de Archivos utiliza componentes, bibliotecas, "
            "motores y modelos desarrollados por terceros. Cada uno se "
            "encuentra sujeto a sus propios términos y licencias. "
            "Puedes consultar los avisos incluidos mediante el botón "
            "«Licencias de terceros»."
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

        titulo_version = self.crear_titulo_seccion(
            "Información de versión"
        )

        layout.addWidget(
            titulo_version
        )

        informacion_version = QLabel(
            f"{NOMBRE_APLICACION}\n"
            f"Versión {VERSION_APLICACION}\n"
            "Windows de 64 bits"
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
    # CREAR TITULO DE SECCION
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