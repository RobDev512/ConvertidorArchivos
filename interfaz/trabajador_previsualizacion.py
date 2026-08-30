from PySide6.QtCore import (
    QObject,
    Signal,
    Slot
)

from conversiones.previsualizacion import preparar_previsualizacion


# ================================================================
# TRABAJADOR DE PREVISUALIZACIÓN
# ================================================================
class TrabajadorPrevisualizacion(QObject):

    finalizado = Signal(
        str,
        int,
        object
    )

    error = Signal(
        str,
        int,
        str,
        str
    )

    trabajo_terminado = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        lado,
        token,
        ruta_archivo
    ):
        super().__init__()

        self.lado = lado
        self.token = token
        self.ruta_archivo = ruta_archivo


    # ============================================================
    # EJECUTAR
    # ============================================================
    @Slot()
    def ejecutar(self):

        try:

            resultado = preparar_previsualizacion(
                self.ruta_archivo
            )

            self.finalizado.emit(
                self.lado,
                self.token,
                resultado
            )

        except Exception as error:

            self.error.emit(
                self.lado,
                self.token,
                self.ruta_archivo,
                str(error)
            )

        finally:

            self.trabajo_terminado.emit()