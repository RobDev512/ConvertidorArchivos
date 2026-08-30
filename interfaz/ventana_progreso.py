from PySide6.QtCore import Qt, Signal

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton
)


# ================================================================
# VENTANA DE PROGRESO
# ================================================================
class VentanaProgreso(QDialog):

    cancelacion_solicitada = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self, cantidad_archivos, parent=None):
        super().__init__(parent)

        # ----------------------------------- #
        #         Variables generales         #
        # ----------------------------------- #

        self.cantidad_archivos = cantidad_archivos

        self.proceso_activo = True
        self.cancelacion_pedida = False


        # ----------------------------------- #
        #     Preparación de la ventana       #
        # ----------------------------------- #

        self.configurar_ventana()
        self.crear_interfaz()


    # ============================================================
    # CONFIGURACIÓN DE LA VENTANA
    # ============================================================
    def configurar_ventana(self):

        if self.cantidad_archivos == 1:

            self.setWindowTitle(
                "Convirtiendo archivo"
            )

        else:

            self.setWindowTitle(
                "Convirtiendo archivos"
            )

        self.setWindowModality(
            Qt.WindowModality.ApplicationModal
        )

        self.setMinimumWidth(
            420
        )

        self.setMinimumHeight(
            210
        )


    # ============================================================
    # CREACIÓN DE LA INTERFAZ
    # ============================================================
    def crear_interfaz(self):

        # Distribución principal
        self.distribucion = QVBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            25,
            25,
            25,
            25
        )

        self.distribucion.setSpacing(
            15
        )


        # ----------------------------------- #
        #              Título                 #
        # ----------------------------------- #

        self.etiqueta_titulo = QLabel(
            "Convirtiendo..."
        )

        self.etiqueta_titulo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_titulo.setStyleSheet(
            """ font-size: 18px; font-weight: bold; """
        )

        self.distribucion.addWidget(
            self.etiqueta_titulo
        )


        # ----------------------------------- #
        #         Archivo actual              #
        # ----------------------------------- #

        self.etiqueta_archivo = QLabel(
            "Preparando archivo..."
        )

        self.etiqueta_archivo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_archivo.setWordWrap(
            True
        )

        self.distribucion.addWidget(
            self.etiqueta_archivo
        )


        # ----------------------------------- #
        #        Barra de progreso            #
        # ----------------------------------- #

        self.barra_progreso = QProgressBar()

        self.barra_progreso.setFixedHeight(
            28
        )

        self.barra_progreso.setTextVisible(
            True
        )

        self.distribucion.addWidget(
            self.barra_progreso
        )


        # ----------------------------------- #
        #             Estado                  #
        # ----------------------------------- #

        self.etiqueta_estado = QLabel(
            "Preparando conversión..."
        )

        self.etiqueta_estado.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_estado.setWordWrap(
            True
        )

        self.distribucion.addWidget(
            self.etiqueta_estado
        )


        # ----------------------------------- #
        #            Cancelar                 #
        # ----------------------------------- #

        self.boton_cancelar = QPushButton(
            "Cancelar"
        )

        self.boton_cancelar.clicked.connect(
            self.solicitar_cancelacion
        )

        self.distribucion.addWidget(
            self.boton_cancelar
        )


        # Configurar barra inicial
        self.configurar_barra_progreso()


    # ============================================================
    # CONFIGURAR BARRA DE PROGRESO
    # ============================================================
    def configurar_barra_progreso(self):

        # Un archivo comienza indeterminado
        if self.cantidad_archivos == 1:

            self.barra_progreso.setRange(
                0,
                0
            )

            self.etiqueta_estado.setText(
                "Procesando archivo..."
            )

        # Varios archivos
        else:

            self.barra_progreso.setRange(
                0,
                100
            )

            self.barra_progreso.setValue(
                0
            )

            self.etiqueta_estado.setText(
                f"0 de {self.cantidad_archivos} "
                f"archivos completados"
            )


    # ============================================================
    # ACTUALIZAR ARCHIVO ACTUAL
    # ============================================================
    def actualizar_archivo(
        self,
        nombre_archivo,
        indice,
        total
    ):

        self.etiqueta_archivo.setText(
            nombre_archivo
        )

        if total > 1:

            self.etiqueta_estado.setText(
                f"Convirtiendo archivo "
                f"{indice} de {total}..."
            )

        else:

            self.etiqueta_estado.setText(
                "Procesando archivo..."
            )


    # ============================================================
    # ACTUALIZAR ESTADO
    # ============================================================
    def actualizar_estado(self, estado):

        if self.proceso_activo:

            self.etiqueta_estado.setText(
                estado
            )


    # ============================================================
    # ACTUALIZAR PROGRESO
    # ============================================================
    def actualizar_progreso(self, progreso):

        # Si estaba en modo indeterminado,
        # pasar automáticamente a porcentaje
        if (
            self.barra_progreso.minimum() == 0
            and self.barra_progreso.maximum() == 0
        ):

            self.barra_progreso.setRange(
                0,
                100
            )

        self.barra_progreso.setValue(
            progreso
        )


    # ============================================================
    # SOLICITAR CANCELACIÓN
    # ============================================================
    def solicitar_cancelacion(self):

        if (
            not self.proceso_activo
            or self.cancelacion_pedida
        ):
            return

        self.cancelacion_pedida = True

        self.boton_cancelar.setEnabled(
            False
        )

        self.etiqueta_titulo.setText(
            "Cancelando..."
        )

        self.etiqueta_estado.setText(
            "La conversión actual terminará antes de cancelar."
        )

        self.cancelacion_solicitada.emit()


    # ============================================================
    # CONVERSIÓN COMPLETADA
    # ============================================================
    def completar(self):

        self.proceso_activo = False

        self.barra_progreso.setRange(
            0,
            100
        )

        self.barra_progreso.setValue(
            100
        )

        self.etiqueta_titulo.setText(
            "Conversión completada"
        )

        self.etiqueta_estado.setText(
            "El proceso terminó correctamente."
        )

        self.boton_cancelar.setEnabled(
            False
        )


    # ============================================================
    # CONVERSIÓN COMPLETADA CON ERRORES
    # ============================================================
    def completar_con_errores(self):

        self.proceso_activo = False

        self.barra_progreso.setRange(
            0,
            100
        )

        self.barra_progreso.setValue(
            100
        )

        self.etiqueta_titulo.setText(
            "Proceso completado"
        )

        self.etiqueta_estado.setText(
            "Algunos archivos no pudieron convertirse."
        )

        self.boton_cancelar.setEnabled(
            False
        )


    # ============================================================
    # CONVERSIÓN CANCELADA
    # ============================================================
    def marcar_cancelada(self):

        self.proceso_activo = False

        self.etiqueta_titulo.setText(
            "Conversión cancelada"
        )

        self.etiqueta_estado.setText(
            "El proceso fue detenido."
        )

        self.boton_cancelar.setEnabled(
            False
        )


    # ============================================================
    # CERRAR VENTANA
    # ============================================================
    def closeEvent(self, evento):

        if self.proceso_activo:

            self.solicitar_cancelacion()
            evento.ignore()

            return

        evento.accept()