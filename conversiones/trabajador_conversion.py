import threading

from PySide6.QtCore import QObject, Signal, Slot

from funciones.archivos import obtener_nombre_archivo

from conversiones.controlador_conversiones import convertir_archivo


# ================================================================
# TRABAJADOR DE CONVERSIÓN
# ================================================================
class TrabajadorConversion(QObject):

    # Archivo actualmente procesado
    archivo_iniciado = Signal(str, int, int)

    # Progreso general
    progreso_actualizado = Signal(int)

    # Estado detallado
    estado_actualizado = Signal(str)

    # Resultado final
    finalizado = Signal(list, list, bool)

    # Finalización completa del trabajador
    trabajo_terminado = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self, tareas, formato_destino):
        super().__init__()

        self.tareas = tareas
        self.formato_destino = formato_destino

        # Evento seguro de cancelación
        self.evento_cancelacion = threading.Event()


    # ============================================================
    # SOLICITAR CANCELACIÓN
    # ============================================================
    def solicitar_cancelacion(self):

        self.evento_cancelacion.set()


    # ============================================================
    # EJECUTAR CONVERSIONES
    # ============================================================
    @Slot()
    def ejecutar(self):

        archivos_convertidos = []
        errores = []

        cantidad_total = len(
            self.tareas
        )

        cantidad_procesados = 0
        conversion_cancelada = False


        # ----------------------------------- #
        #         Procesar tareas             #
        # ----------------------------------- #

        for indice, tarea in enumerate(
            self.tareas,
            start=1
        ):

            # Cancelar antes del siguiente archivo
            if self.evento_cancelacion.is_set():

                conversion_cancelada = True
                break


            ruta_origen = tarea[
                "ruta_origen"
            ]

            ruta_destino = tarea[
                "ruta_destino"
            ]


            # Informar archivo actual
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

                # Limitar porcentaje
                progreso_archivo = max(
                    0,
                    min(
                        100,
                        int(progreso_archivo)
                    )
                )

                # Convertir progreso interno en
                # progreso general del lote
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
                    callback_progreso
                )

                archivos_convertidos.append(
                    ruta_convertida
                )


            except Exception as error:

                errores.append(
                    f"{obtener_nombre_archivo(ruta_origen)}: {error}"
                )


            # ----------------------------------- #
            #        Archivo completado           #
            # ----------------------------------- #

            cantidad_procesados = indice

            progreso_general = round(
                cantidad_procesados
                / cantidad_total
                * 100
            )

            self.progreso_actualizado.emit(
                progreso_general
            )


        # ----------------------------------- #
        #          Cancelación final          #
        # ----------------------------------- #

        if (
            self.evento_cancelacion.is_set()
            and cantidad_procesados < cantidad_total
        ):

            conversion_cancelada = True


        # ----------------------------------- #
        #            Finalizar                #
        # ----------------------------------- #

        self.finalizado.emit(
            archivos_convertidos,
            errores,
            conversion_cancelada
        )

        self.trabajo_terminado.emit()