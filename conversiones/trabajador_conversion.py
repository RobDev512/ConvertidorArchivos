import threading

from PySide6.QtCore import QObject, Signal, Slot

from funciones.archivos import obtener_nombre_archivo

from conversiones.controlador_conversiones import convertir_archivo

from conversiones.pdf_docx import (
    ConversionPDFDOCXCancelada
)


# ================================================================
# TRABAJADOR DE CONVERSIÓN
# ================================================================
class TrabajadorConversion(QObject):

    archivo_iniciado = Signal(str, int, int)
    progreso_actualizado = Signal(int)
    estado_actualizado = Signal(str)
    finalizado = Signal(list, list, bool)
    trabajo_terminado = Signal()

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        tareas,
        formato_destino
    ):

        super().__init__()

        self.tareas = tareas
        self.formato_destino = formato_destino

        self.evento_cancelacion = threading.Event()

    # ============================================================
    # SOLICITAR CANCELACIÓN
    # ============================================================
    def solicitar_cancelacion(
        self
    ):

        self.evento_cancelacion.set()

    # ============================================================
    # EJECUTAR CONVERSIONES
    # ============================================================
    @Slot()
    def ejecutar(
        self
    ):

        archivos_convertidos = []
        errores = []

        cantidad_total = len(
            self.tareas
        )

        cantidad_procesados = 0
        conversion_cancelada = False

        for indice, tarea in enumerate(
            self.tareas,
            start=1
        ):
            if self.evento_cancelacion.is_set():
                conversion_cancelada = True
                break

            ruta_origen = tarea[
                "ruta_origen"
            ]

            ruta_destino = tarea[
                "ruta_destino"
            ]

            self.archivo_iniciado.emit(
                obtener_nombre_archivo(
                    ruta_origen
                ),
                indice,
                cantidad_total
            )

            # ----------------------------------- #
            #      Progreso interno del archivo   #
            # ----------------------------------- #

            def callback_progreso(
                progreso_archivo,
                estado=None
            ):

                progreso_archivo = max(
                    0,
                    min(
                        100,
                        int(
                            progreso_archivo
                        )
                    )
                )

                progreso_general = round(
                    (
                        (indice - 1)
                        + (
                            progreso_archivo
                            / 100
                        )
                    )
                    / cantidad_total
                    * 100
                )

                self.progreso_actualizado.emit(
                    progreso_general
                )

                if estado:
                    self.estado_actualizado.emit(
                        estado
                    )

            # ----------------------------------- #
            #         Realizar conversión         #
            # ----------------------------------- #

            try:
                ruta_convertida = convertir_archivo(
                    ruta_origen,
                    ruta_destino,
                    self.formato_destino,
                    callback_progreso,
                    self.evento_cancelacion.is_set
                )

                archivos_convertidos.append(
                    ruta_convertida
                )

            except ConversionPDFDOCXCancelada:
                conversion_cancelada = True
                break

            except Exception as error:
                if self.evento_cancelacion.is_set():
                    conversion_cancelada = True
                    break

                errores.append(
                    f"{obtener_nombre_archivo(ruta_origen)}: {error}"
                )

            cantidad_procesados = indice

            progreso_general = round(
                cantidad_procesados
                / cantidad_total
                * 100
            )

            self.progreso_actualizado.emit(
                progreso_general
            )

        if self.evento_cancelacion.is_set():
            conversion_cancelada = True

        self.finalizado.emit(
            archivos_convertidos,
            errores,
            conversion_cancelada
        )

        self.trabajo_terminado.emit()