import os

from PySide6.QtCore import QSize

from PySide6.QtGui import QIcon

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox
)

from interfaz.zona_archivos import ZonaArchivos

from funciones.configuracion_app import (
    obtener_ruta_recurso
)


# ----------------------------------- #
#      Separaciones de controles      #
# ----------------------------------- #

ESPACIO_CUADRO_CONTROLES = 5

ESPACIO_ETIQUETA_COMBO = 3

ESPACIO_COMBO_BOTON = 10

ESPACIO_BOTON_ESTADO = 10


# ================================================================
# PANEL DE CONVERSIÓN
# ================================================================
class PanelConversion(QWidget):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self
    ):

        super().__init__()

        self.crear_interfaz()
        self.conectar_eventos()


    # ============================================================
    # CREACIÓN DE LA INTERFAZ
    # ============================================================
    def crear_interfaz(
        self
    ):

        # ----------------------------------- #
        #       Distribución principal        #
        # ----------------------------------- #

        self.distribucion = QVBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            15,
            5,
            15,
            5
        )

        self.distribucion.setSpacing(
            15
        )


        # ----------------------------------- #
        #              Título                 #
        # ----------------------------------- #

        self.titulo = QLabel(
            "Conversión"
        )

        self.titulo.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        self.distribucion.addWidget(
            self.titulo
        )


        # ----------------------------------- #
        #        Zona de archivos             #
        # ----------------------------------- #

        self.zona_archivos = ZonaArchivos()

        self.distribucion.addWidget(
            self.zona_archivos,
            1
        )


        # Mantener accesos utilizados por
        # la ventana principal
        self.etiqueta_archivo = (
            self.zona_archivos.etiqueta_archivo
        )

        self.boton_seleccionar_archivos = (
            self.zona_archivos.boton_seleccionar_archivos
        )


        # ========================================================
        # CONTROLES INFERIORES
        # ========================================================

        self.contenedor_controles = QWidget()

        self.distribucion_controles = QVBoxLayout(
            self.contenedor_controles
        )


        # ----------------------------------- #
        #   Separación respecto al cuadro     #
        # ----------------------------------- #

        self.distribucion_controles.setContentsMargins(
            0,
            ESPACIO_CUADRO_CONTROLES,
            0,
            0
        )


        # Las separaciones se controlan
        # individualmente más abajo
        self.distribucion_controles.setSpacing(
            0
        )


        # ----------------------------------- #
        #        Selector de formato          #
        # ----------------------------------- #

        self.etiqueta_formato = QLabel(
            "Convertir a:"
        )

        self.distribucion_controles.addWidget(
            self.etiqueta_formato
        )


        # ----------------------------------- #
        #   Separación etiqueta → ComboBox    #
        # ----------------------------------- #

        self.distribucion_controles.addSpacing(
            ESPACIO_ETIQUETA_COMBO
        )


        self.selector_formato = QComboBox()

        self.selector_formato.addItem(
            "Selecciona primero un archivo"
        )

        self.selector_formato.setEnabled(
            False
        )

        self.selector_formato.setMaxVisibleItems(
            15
        )


        # ----------------------------------- #
        #       Altura del ComboBox           #
        # ----------------------------------- #

        self.selector_formato.setFixedHeight(
            52
        )

        self.selector_formato.setStyleSheet(
            """
            QComboBox {
                font-size: 14px;
                padding-left: 10px;
                padding-right: 10px;
            }
            """
        )

        self.distribucion_controles.addWidget(
            self.selector_formato
        )


        # ----------------------------------- #
        #    Separación ComboBox → botón      #
        # ----------------------------------- #

        self.distribucion_controles.addSpacing(
            ESPACIO_COMBO_BOTON
        )


        # ----------------------------------- #
        #            Botón convertir          #
        # ----------------------------------- #

        self.boton_convertir = QPushButton(
            "Convertir"
        )

        self.boton_convertir.setFixedHeight(
            60
        )

        self.boton_convertir.setIconSize(
            QSize(
                30,
                30
            )
        )

        self.boton_convertir.setStyleSheet(
            """
            QPushButton {
                font-size: 15px;
                font-weight: 600;
                padding-left: 16px;
                padding-right: 16px;
            }
            """
        )


        # ----------------------------------- #
        #       Icono del botón Convertir     #
        # ----------------------------------- #

        self.cargar_icono_convertir()

        self.boton_convertir.setEnabled(
            False
        )

        self.distribucion_controles.addWidget(
            self.boton_convertir
        )


        # ----------------------------------- #
        #     Separación botón → estado       #
        # ----------------------------------- #

        self.distribucion_controles.addSpacing(
            ESPACIO_BOTON_ESTADO
        )


        # ----------------------------------- #
        #              Estado                 #
        # ----------------------------------- #

        self.etiqueta_estado = QLabel(
            "Esperando archivo..."
        )

        self.etiqueta_estado.setWordWrap(
            True
        )

        self.etiqueta_estado.setMinimumHeight(
            22
        )

        self.distribucion_controles.addWidget(
            self.etiqueta_estado
        )


        # ----------------------------------- #
        #     Añadir bloque inferior          #
        # ----------------------------------- #

        self.distribucion.addWidget(
            self.contenedor_controles
        )


    # ============================================================
    # CARGAR ICONO CONVERTIR
    # ============================================================
    def cargar_icono_convertir(
        self
    ):

        ruta_normal = obtener_ruta_recurso(
            "iconos",
            "Convertir001.png"
        )

        ruta_deshabilitado = obtener_ruta_recurso(
            "iconos",
            "Convertir002.png"
        )

        icono = QIcon()


        # ----------------------------------- #
        #         Estado habilitado           #
        # ----------------------------------- #

        if os.path.isfile(
            ruta_normal
        ):

            icono.addFile(
                ruta_normal,
                QSize(
                    30,
                    30
                ),
                QIcon.Mode.Normal,
                QIcon.State.Off
            )


        # ----------------------------------- #
        #        Estado deshabilitado         #
        # ----------------------------------- #

        if os.path.isfile(
            ruta_deshabilitado
        ):

            icono.addFile(
                ruta_deshabilitado,
                QSize(
                    30,
                    30
                ),
                QIcon.Mode.Disabled,
                QIcon.State.Off
            )


        self.boton_convertir.setIcon(
            icono
        )


    # ============================================================
    # CONEXIÓN DE EVENTOS
    # ============================================================
    def conectar_eventos(
        self
    ):

        self.selector_formato.currentIndexChanged.connect(
            self.actualizar_boton_convertir
        )


    # ============================================================
    # MOSTRAR COMPROBACIÓN DE FORMATOS
    # ============================================================
    def mostrar_comprobando_formatos(
        self
    ):

        self.selector_formato.clear()

        self.selector_formato.addItem(
            "Comprobando formatos disponibles..."
        )

        self.selector_formato.setEnabled(
            False
        )

        self.boton_convertir.setEnabled(
            False
        )


    # ============================================================
    # MOSTRAR FORMATOS DISPONIBLES
    # ============================================================
    def mostrar_formatos_disponibles(
        self,
        formatos
    ):

        self.selector_formato.clear()


        # ----------------------------------- #
        #       Existen formatos disponibles  #
        # ----------------------------------- #

        if formatos:

            self.selector_formato.addItem(
                "Selecciona un formato"
            )

            self.selector_formato.addItems(
                formatos
            )

            self.selector_formato.setEnabled(
                True
            )


        # ----------------------------------- #
        #        No existen conversiones      #
        # ----------------------------------- #

        else:

            self.selector_formato.addItem(
                "No hay conversiones disponibles"
            )

            self.selector_formato.setEnabled(
                False
            )


        self.boton_convertir.setEnabled(
            False
        )


    # ============================================================
    # ACTUALIZAR BOTÓN CONVERTIR
    # ============================================================
    def actualizar_boton_convertir(
        self
    ):

        formato_seleccionado = (
            self.selector_formato.currentIndex()
            > 0
        )

        self.boton_convertir.setEnabled(
            self.selector_formato.isEnabled()
            and formato_seleccionado
        )


    # ============================================================
    # OBTENER FORMATO SELECCIONADO
    # ============================================================
    def obtener_formato_seleccionado(
        self
    ):

        if self.selector_formato.currentIndex() <= 0:

            return None

        return self.selector_formato.currentText()