import os
from interfaz.dialogo_acerca_de import DialogoAcercaDe

from PySide6.QtCore import (
    Qt,
    QThread,
    QTimer
)

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QFileDialog,
    QSplitter,
    QMessageBox,
    QCheckBox
)

from interfaz.panel_conversion import PanelConversion
from interfaz.panel_previsualizacion import PanelPrevisualizacion
from interfaz.ventana_progreso import VentanaProgreso
from interfaz.trabajador_previsualizacion import TrabajadorPrevisualizacion

from funciones.archivos import (
    obtener_nombre_archivo,
    asegurar_extension,
    crear_ruta_unica,
    normalizar_ruta
)

from funciones.formatos import (
    obtener_formato_archivo,
    obtener_nombre_categoria,
    obtener_formatos_compatibles
)

from conversiones.controlador_conversiones import (
    obtener_extension_resultado,
    obtener_nombre_resultado_sugerido,
    comprobar_conversion_disponible
)

from conversiones.trabajador_conversion import TrabajadorConversion

from conversiones.previsualizacion import (
    obtener_tipo_previsualizacion,
    obtener_imagen_pagina_previsualizacion,
    limpiar_previsualizacion
)

from funciones.configuracion_app import NOMBRE_APLICACION

# ================================================================
# VENTANA PRINCIPAL
# ================================================================
class VentanaPrincipal(QMainWindow):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self):
        super().__init__()


        # ----------------------------------- #
        #        Archivos seleccionados       #
        # ----------------------------------- #

        self.archivos_seleccionados = []
        self.archivos_convertidos = []

        self.archivos_omitidos_conversion = 0


        # ----------------------------------- #
        #            Conversión               #
        # ----------------------------------- #

        self.hilo_conversion = None
        self.trabajador_conversion = None
        self.ventana_progreso = None


        # ----------------------------------- #
        #         Previsualización            #
        # ----------------------------------- #

        self.previsualizaciones = {
            "original": None,
            "resultado": None
        }

        self.tokens_previsualizacion = {
            "original": 0,
            "resultado": 0
        }

        self.trabajos_previsualizacion = []


        # ----------------------------------- #
        #          Interfaz responsive        #
        # ----------------------------------- #

        self.ancho_minimo_previsualizacion = 1200
        self.previsualizacion_visible = False


        # ----------------------------------- #
        #        Preparar aplicación          #
        # ----------------------------------- #

        self.configurar_ventana()
        self.crear_interfaz()
        self.conectar_eventos()
        self.actualizar_interfaz_responsive()


    # ============================================================
    # CONFIGURACIÓN DE LA VENTANA
    # ============================================================
    def configurar_ventana(self):

        self.setWindowTitle(
            "Convertidor de Archivos"
        )

        self.resize(
            900,
            650
        )

        self.setMinimumSize(
            700,
            500
        )


    # ============================================================
    # CREACIÓN DE LA INTERFAZ
    # ============================================================
    def crear_interfaz(self):

        self.contenedor_principal = QWidget()

        self.setCentralWidget(
            self.contenedor_principal
        )

        self.distribucion_principal = QVBoxLayout(
            self.contenedor_principal
        )

        self.distribucion_principal.setContentsMargins(
            20,
            8,
            20,
            5
        )

        self.distribucion_principal.setSpacing(
            15
        )


        # ----------------------------------- #
        #              Título                 #
        # ----------------------------------- #

        self.etiqueta_titulo = QLabel(
            "Convertidor de Archivos"
        )

        self.etiqueta_titulo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_titulo.setStyleSheet(
            "font-size: 24px;"
        )

        self.distribucion_principal.addWidget(
            self.etiqueta_titulo
        )


        # ----------------------------------- #
        #             Subtítulo               #
        # ----------------------------------- #

        self.etiqueta_subtitulo = QLabel(
            "Selecciona o arrastra uno o varios archivos y elige "
            "el formato al que deseas convertirlos."
        )

        self.etiqueta_subtitulo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_subtitulo.setWordWrap(
            True
        )

        self.distribucion_principal.addWidget(
            self.etiqueta_subtitulo
        )


        # ----------------------------------- #
        #             Paneles                 #
        # ----------------------------------- #

        self.divisor_principal = QSplitter(
            Qt.Orientation.Horizontal
        )

        self.distribucion_principal.addWidget(
            self.divisor_principal,
            1
        )

        self.panel_conversion = PanelConversion()
        self.panel_previsualizacion = PanelPrevisualizacion()

        self.divisor_principal.addWidget(
            self.panel_conversion
        )

        self.divisor_principal.addWidget(
            self.panel_previsualizacion
        )

        self.divisor_principal.setChildrenCollapsible(
            False
        )

        self.panel_previsualizacion.setVisible(
            False
        )


    # ============================================================
    # CONEXIÓN DE EVENTOS
    # ============================================================
    def conectar_eventos(self):

        self.panel_conversion.boton_seleccionar_archivos.clicked.connect(
            self.seleccionar_archivos
        )

        self.panel_conversion.zona_archivos.archivos_soltados.connect(
            self.cargar_archivos
        )

        self.panel_conversion.boton_convertir.clicked.connect(
            self.convertir_archivos
        )


        # ----------------------------------- #
        #     Navegación previsualización     #
        # ----------------------------------- #

        self.panel_previsualizacion.pagina_anterior_solicitada.connect(
            lambda lado:
            self.cambiar_pagina_previsualizacion(
                lado,
                -1
            )
        )

        self.panel_previsualizacion.pagina_siguiente_solicitada.connect(
            lambda lado:
            self.cambiar_pagina_previsualizacion(
                lado,
                1
            )
        )


    # ============================================================
    # SELECCIONAR ARCHIVOS
    # ============================================================
    def seleccionar_archivos(self):

        archivos, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivos"
        )

        if not archivos:
            return

        self.cargar_archivos(
            archivos
        )


    # ============================================================
    # INVALIDAR PREVISUALIZACIÓN
    # ============================================================
    def invalidar_previsualizacion(
        self,
        lado
    ):

        self.tokens_previsualizacion[
            lado
        ] += 1


        resultado = self.previsualizaciones.get(
            lado
        )

        if resultado:

            limpiar_previsualizacion(
                resultado
            )


        self.previsualizaciones[
            lado
        ] = None


    # ============================================================
    # PREVISUALIZAR ARCHIVO
    # ============================================================
    def previsualizar_archivo(
        self,
        lado,
        ruta_archivo
    ):

        self.invalidar_previsualizacion(
            lado
        )


        tipo = obtener_tipo_previsualizacion(
            ruta_archivo
        )


        # ----------------------------------- #
        #       Archivo genérico              #
        # ----------------------------------- #

        if tipo == "archivo":

            self.panel_previsualizacion.mostrar_archivo(
                lado,
                ruta_archivo
            )

            return


        # ----------------------------------- #
        #      Vista que necesita trabajo     #
        # ----------------------------------- #

        self.panel_previsualizacion.mostrar_estado(
            lado,
            "Generando previsualización..."
        )

        self.iniciar_previsualizacion_segundo_plano(
            lado,
            ruta_archivo
        )


    # ============================================================
    # INICIAR PREVISUALIZACIÓN EN SEGUNDO PLANO
    # ============================================================
    def iniciar_previsualizacion_segundo_plano(
        self,
        lado,
        ruta_archivo
    ):

        token = self.tokens_previsualizacion[
            lado
        ]


        # ----------------------------------- #
        #              Hilo                   #
        # ----------------------------------- #

        hilo = QThread(
            self
        )


        # ----------------------------------- #
        #           Trabajador                #
        # ----------------------------------- #

        trabajador = TrabajadorPrevisualizacion(
            lado,
            token,
            ruta_archivo
        )

        trabajador.moveToThread(
            hilo
        )


        registro = {
            "hilo": hilo,
            "trabajador": trabajador
        }

        self.trabajos_previsualizacion.append(
            registro
        )


        # ----------------------------------- #
        #             Eventos                 #
        # ----------------------------------- #

        hilo.started.connect(
            trabajador.ejecutar
        )

        trabajador.finalizado.connect(
            self.recibir_previsualizacion
        )

        trabajador.error.connect(
            self.recibir_error_previsualizacion
        )

        trabajador.trabajo_terminado.connect(
            hilo.quit
        )

        trabajador.trabajo_terminado.connect(
            trabajador.deleteLater
        )

        hilo.finished.connect(
            lambda registro=registro:
            self.limpiar_trabajo_previsualizacion(
                registro
            )
        )

        hilo.finished.connect(
            hilo.deleteLater
        )


        hilo.start()


    # ============================================================
    # RECIBIR PREVISUALIZACIÓN
    # ============================================================
    def recibir_previsualizacion(
        self,
        lado,
        token,
        resultado
    ):

        # Resultado antiguo
        if token != self.tokens_previsualizacion[
            lado
        ]:

            limpiar_previsualizacion(
                resultado
            )

            return


        self.previsualizaciones[
            lado
        ] = resultado


        self.panel_previsualizacion.mostrar_previsualizacion(
            lado,
            resultado
        )


    # ============================================================
    # RECIBIR ERROR DE PREVISUALIZACIÓN
    # ============================================================
    def recibir_error_previsualizacion(
        self,
        lado,
        token,
        ruta_archivo,
        mensaje
    ):

        if token != self.tokens_previsualizacion[
            lado
        ]:
            return


        # Si falla la vista avanzada,
        # usar icono del sistema como respaldo
        self.panel_previsualizacion.mostrar_archivo(
            lado,
            ruta_archivo
        )

        self.panel_previsualizacion.obtener_lado(
            lado
        ).visor_archivo.setToolTip(
            mensaje
        )


    # ============================================================
    # LIMPIAR TRABAJO DE PREVISUALIZACIÓN
    # ============================================================
    def limpiar_trabajo_previsualizacion(
        self,
        registro
    ):

        if registro in self.trabajos_previsualizacion:

            self.trabajos_previsualizacion.remove(
                registro
            )


    # ============================================================
    # CAMBIAR PÁGINA
    # ============================================================
    def cambiar_pagina_previsualizacion(
        self,
        lado,
        desplazamiento
    ):

        resultado = self.previsualizaciones.get(
            lado
        )

        if not resultado:
            return


        if resultado["tipo"] not in {
            "documento",
            "presentacion"
        }:

            return


        actual = resultado[
            "pagina_actual"
        ]

        cantidad = resultado[
            "cantidad_paginas"
        ]

        nueva = (
            actual
            + desplazamiento
        )


        if nueva < 0:
            return

        if nueva >= cantidad:
            return


        try:

            datos_imagen = obtener_imagen_pagina_previsualizacion(
                resultado,
                nueva
            )

        except Exception as error:

            QMessageBox.warning(
                self,
                "Previsualización",
                str(error)
            )

            return


        resultado[
            "pagina_actual"
        ] = nueva

        resultado[
            "datos_imagen"
        ] = datos_imagen


        self.panel_previsualizacion.mostrar_previsualizacion(
            lado,
            resultado
        )


    # ============================================================
    # CARGAR ARCHIVOS
    # ============================================================
    def cargar_archivos(self, archivos):

        archivos = list(
            dict.fromkeys(
                archivos
            )
        )

        archivos = [
            archivo
            for archivo in archivos
            if os.path.isfile(
                archivo
            )
        ]

        if not archivos:
            return


        # ----------------------------------- #
        #       Limpiar vistas anteriores     #
        # ----------------------------------- #

        self.invalidar_previsualizacion(
            "original"
        )

        self.invalidar_previsualizacion(
            "resultado"
        )

        self.panel_previsualizacion.mostrar_estado(
            "resultado",
            "Aún no hay resultado"
        )


        # ----------------------------------- #
        #         Guardar selección           #
        # ----------------------------------- #

        self.archivos_seleccionados = archivos
        self.archivos_convertidos = []


        # ========================================================
        # UN SOLO ARCHIVO
        # ========================================================

        if len(
            archivos
        ) == 1:

            ruta_archivo = archivos[
                0
            ]

            nombre_archivo = obtener_nombre_archivo(
                ruta_archivo
            )

            formato_archivo = obtener_formato_archivo(
                ruta_archivo
            )

            categoria_archivo = obtener_nombre_categoria(
                ruta_archivo
            )


            self.panel_conversion.zona_archivos.actualizar_texto(
                nombre_archivo
            )

            self.panel_conversion.etiqueta_estado.setText(
                f"Formato: {formato_archivo} | "
                f"Tipo: {categoria_archivo}"
            )


            # Vista original
            self.previsualizar_archivo(
                "original",
                ruta_archivo
            )


        # ========================================================
        # VARIOS ARCHIVOS
        # ========================================================

        else:

            cantidad_archivos = len(
                archivos
            )

            self.panel_conversion.zona_archivos.actualizar_texto(
                f"{cantidad_archivos} archivos seleccionados"
            )

            self.panel_conversion.etiqueta_estado.setText(
                f"{cantidad_archivos} archivos seleccionados."
            )


            # Mostrar grupo mediante el icono
            # del primer archivo seleccionado
            self.panel_previsualizacion.mostrar_archivo(
                "original",
                archivos[0],
                (
                    f"{cantidad_archivos} "
                    f"archivos seleccionados"
                )
            )


        # ----------------------------------- #
        #      Buscar formatos disponibles    #
        # ----------------------------------- #

        self.panel_conversion.mostrar_comprobando_formatos()

        QTimer.singleShot(
            10,
            self.actualizar_formatos_disponibles
        )


    # ============================================================
    # ACTUALIZAR FORMATOS DISPONIBLES
    # ============================================================
    def actualizar_formatos_disponibles(self):

        formatos_posibles = obtener_formatos_compatibles(
            self.archivos_seleccionados
        )

        formatos_disponibles = []


        for formato_destino in formatos_posibles:

            disponible_para_todos = True


            for ruta_archivo in self.archivos_seleccionados:

                disponible, _ = comprobar_conversion_disponible(
                    ruta_archivo,
                    formato_destino
                )

                if not disponible:

                    disponible_para_todos = False
                    break


            if disponible_para_todos:

                formatos_disponibles.append(
                    formato_destino
                )


        self.panel_conversion.mostrar_formatos_disponibles(
            formatos_disponibles
        )


        if not formatos_disponibles:

            self.panel_conversion.etiqueta_estado.setText(
                "No hay conversiones disponibles "
                "para los archivos seleccionados."
            )


    # ============================================================
    # SELECCIONAR DESTINO INDIVIDUAL
    # ============================================================
    def seleccionar_destino_individual(
        self,
        ruta_origen,
        formato_destino
    ):

        extension = obtener_extension_resultado(
            ruta_origen,
            formato_destino
        )

        nombre_sugerido = obtener_nombre_resultado_sugerido(
            ruta_origen,
            formato_destino
        )

        carpeta_origen = os.path.dirname(
            ruta_origen
        )

        ruta_sugerida = os.path.join(
            carpeta_origen,
            nombre_sugerido
        )


        if (
            extension == ".zip"
            and formato_destino.upper() != "ZIP"
        ):

            filtro = (
                "Archivo ZIP con imágenes (*.zip);;"
                "Todos los archivos (*.*)"
            )

        else:

            filtro = (
                f"Archivo {formato_destino} (*{extension});;"
                "Todos los archivos (*.*)"
            )


        ruta_destino, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo convertido",
            ruta_sugerida,
            filtro
        )

        if not ruta_destino:
            return None


        return asegurar_extension(
            ruta_destino,
            extension
        )


    # ============================================================
    # SELECCIONAR CARPETA DE DESTINO
    # ============================================================
    def seleccionar_carpeta_destino(self):

        carpeta_inicial = os.path.dirname(
            self.archivos_seleccionados[0]
        )

        carpeta_destino = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de destino",
            carpeta_inicial
        )

        if not carpeta_destino:
            return None

        return carpeta_destino


    # ============================================================
    # RESOLVER CONFLICTO DE ARCHIVO
    # ============================================================
    def resolver_conflicto_archivo(
        self,
        ruta_destino
    ):

        mensaje = QMessageBox(
            self
        )

        mensaje.setWindowTitle(
            "El archivo ya existe"
        )

        mensaje.setIcon(
            QMessageBox.Icon.Question
        )

        mensaje.setText(
            f"Ya existe un archivo llamado:\n\n"
            f"{obtener_nombre_archivo(ruta_destino)}"
        )

        mensaje.setInformativeText(
            "¿Qué deseas hacer?"
        )


        boton_reemplazar = mensaje.addButton(
            "Reemplazar",
            QMessageBox.ButtonRole.AcceptRole
        )

        boton_copia = mensaje.addButton(
            "Crear copia",
            QMessageBox.ButtonRole.ActionRole
        )

        boton_omitir = mensaje.addButton(
            "Omitir",
            QMessageBox.ButtonRole.DestructiveRole
        )

        mensaje.addButton(
            "Cancelar",
            QMessageBox.ButtonRole.RejectRole
        )


        casilla_aplicar_todos = QCheckBox(
            "Hacer esto para los demás conflictos"
        )

        mensaje.setCheckBox(
            casilla_aplicar_todos
        )

        mensaje.exec()

        boton_seleccionado = mensaje.clickedButton()


        if boton_seleccionado == boton_reemplazar:

            accion = "reemplazar"

        elif boton_seleccionado == boton_copia:

            accion = "copia"

        elif boton_seleccionado == boton_omitir:

            accion = "omitir"

        else:

            accion = "cancelar"


        return (
            accion,
            casilla_aplicar_todos.isChecked()
        )


    # ============================================================
    # COMPROBAR CONVERSIÓN SELECCIONADA
    # ============================================================
    def comprobar_conversion_seleccionada(
        self,
        formato_destino
    ):

        for ruta_archivo in self.archivos_seleccionados:

            disponible, mensaje = comprobar_conversion_disponible(
                ruta_archivo,
                formato_destino
            )

            if not disponible:

                QMessageBox.information(
                    self,
                    "Conversión no disponible",
                    mensaje
                )

                return False

        return True


    # ============================================================
    # PREPARAR TAREAS DE CONVERSIÓN
    # ============================================================
    def preparar_tareas_conversion(
        self,
        formato_destino
    ):

        self.archivos_omitidos_conversion = 0


        # ========================================================
        # UN SOLO ARCHIVO
        # ========================================================

        if len(
            self.archivos_seleccionados
        ) == 1:

            ruta_origen = self.archivos_seleccionados[
                0
            ]

            ruta_destino = self.seleccionar_destino_individual(
                ruta_origen,
                formato_destino
            )

            if not ruta_destino:
                return None

            return [
                {
                    "ruta_origen": ruta_origen,
                    "ruta_destino": ruta_destino
                }
            ]


        # ========================================================
        # VARIOS ARCHIVOS
        # ========================================================

        carpeta_destino = self.seleccionar_carpeta_destino()

        if not carpeta_destino:
            return None


        tareas = []
        rutas_reservadas = set()
        accion_conflictos = None


        for ruta_origen in self.archivos_seleccionados:

            nombre_destino = obtener_nombre_resultado_sugerido(
                ruta_origen,
                formato_destino
            )

            ruta_destino = os.path.join(
                carpeta_destino,
                nombre_destino
            )


            if normalizar_ruta(
                ruta_destino
            ) in rutas_reservadas:

                ruta_destino = crear_ruta_unica(
                    ruta_destino,
                    rutas_reservadas
                )


            if os.path.exists(
                ruta_destino
            ):

                if accion_conflictos is None:

                    accion, aplicar_todos = (
                        self.resolver_conflicto_archivo(
                            ruta_destino
                        )
                    )

                    if aplicar_todos:

                        accion_conflictos = accion

                else:

                    accion = accion_conflictos


                if accion == "cancelar":
                    return None


                if accion == "omitir":

                    self.archivos_omitidos_conversion += 1
                    continue


                if accion == "copia":

                    ruta_destino = crear_ruta_unica(
                        ruta_destino,
                        rutas_reservadas
                    )


            rutas_reservadas.add(
                normalizar_ruta(
                    ruta_destino
                )
            )


            tareas.append(
                {
                    "ruta_origen": ruta_origen,
                    "ruta_destino": ruta_destino
                }
            )


        return tareas


    # ============================================================
    # CONVERTIR ARCHIVOS
    # ============================================================
    def convertir_archivos(self):

        formato_destino = (
            self.panel_conversion.obtener_formato_seleccionado()
        )

        if not formato_destino:
            return

        if not self.archivos_seleccionados:
            return


        if not self.comprobar_conversion_seleccionada(
            formato_destino
        ):

            return


        tareas = self.preparar_tareas_conversion(
            formato_destino
        )

        if tareas is None:
            return


        if not tareas:

            QMessageBox.information(
                self,
                "Sin archivos para convertir",
                "Todos los archivos fueron omitidos."
            )

            return


        self.iniciar_conversion_segundo_plano(
            tareas,
            formato_destino
        )


    # ============================================================
    # INICIAR CONVERSIÓN EN SEGUNDO PLANO
    # ============================================================
    def iniciar_conversion_segundo_plano(
        self,
        tareas,
        formato_destino
    ):

        self.archivos_convertidos = []

        self.panel_conversion.etiqueta_estado.setText(
            "Convirtiendo..."
        )


        self.ventana_progreso = VentanaProgreso(
            len(tareas),
            self
        )

        self.ventana_progreso.cancelacion_solicitada.connect(
            self.solicitar_cancelacion_conversion
        )


        self.hilo_conversion = QThread(
            self
        )


        self.trabajador_conversion = TrabajadorConversion(
            tareas,
            formato_destino
        )

        self.trabajador_conversion.moveToThread(
            self.hilo_conversion
        )


        self.hilo_conversion.started.connect(
            self.trabajador_conversion.ejecutar
        )

        self.trabajador_conversion.archivo_iniciado.connect(
            self.ventana_progreso.actualizar_archivo
        )

        self.trabajador_conversion.progreso_actualizado.connect(
            self.ventana_progreso.actualizar_progreso
        )

        self.trabajador_conversion.estado_actualizado.connect(
            self.ventana_progreso.actualizar_estado
        )

        self.trabajador_conversion.finalizado.connect(
            self.finalizar_conversion
        )

        self.trabajador_conversion.trabajo_terminado.connect(
            self.hilo_conversion.quit
        )

        self.trabajador_conversion.trabajo_terminado.connect(
            self.trabajador_conversion.deleteLater
        )

        self.hilo_conversion.finished.connect(
            self.limpiar_hilo_conversion
        )

        self.hilo_conversion.finished.connect(
            self.hilo_conversion.deleteLater
        )


        self.ventana_progreso.show()

        QTimer.singleShot(
            100,
            self.hilo_conversion.start
        )


    # ============================================================
    # SOLICITAR CANCELACIÓN
    # ============================================================
    def solicitar_cancelacion_conversion(self):

        if self.trabajador_conversion:

            self.trabajador_conversion.solicitar_cancelacion()


    # ============================================================
    # FINALIZAR CONVERSIÓN
    # ============================================================
    def finalizar_conversion(
        self,
        archivos_convertidos,
        errores,
        conversion_cancelada
    ):

        self.archivos_convertidos = archivos_convertidos


        if conversion_cancelada:

            self.ventana_progreso.marcar_cancelada()

        elif errores:

            self.ventana_progreso.completar_con_errores()

        else:

            self.ventana_progreso.completar()


        QTimer.singleShot(
            650,
            lambda: self.mostrar_resultado_conversion(
                list(archivos_convertidos),
                list(errores),
                conversion_cancelada
            )
        )


    # ============================================================
    # MOSTRAR RESULTADO DE LA CONVERSIÓN
    # ============================================================
    def mostrar_resultado_conversion(
        self,
        archivos_convertidos,
        errores,
        conversion_cancelada
    ):

        if self.ventana_progreso:

            self.ventana_progreso.close()


        cantidad_convertidos = len(
            archivos_convertidos
        )

        cantidad_omitidos = (
            self.archivos_omitidos_conversion
        )


        # ----------------------------------- #
        #     Previsualizar resultado         #
        # ----------------------------------- #

        self.invalidar_previsualizacion(
            "resultado"
        )


        if cantidad_convertidos == 1:

            self.previsualizar_archivo(
                "resultado",
                archivos_convertidos[0]
            )

        elif cantidad_convertidos > 1:

            self.panel_previsualizacion.mostrar_archivo(
                "resultado",
                archivos_convertidos[0],
                (
                    f"{cantidad_convertidos} "
                    f"archivos convertidos"
                )
            )

        else:

            self.panel_previsualizacion.mostrar_estado(
                "resultado",
                "No se generó ningún archivo"
            )


        # ========================================================
        # CONVERSIÓN CANCELADA
        # ========================================================

        if conversion_cancelada:

            if cantidad_convertidos:

                texto = (
                    "La conversión fue cancelada.\n\n"
                    f"{cantidad_convertidos} archivo(s) alcanzaron "
                    "a convertirse correctamente."
                )

            else:

                texto = (
                    "La conversión fue cancelada antes de "
                    "completar ningún archivo."
                )


            self.panel_conversion.etiqueta_estado.setText(
                "Conversión cancelada."
            )

            QMessageBox.information(
                self,
                "Conversión cancelada",
                texto
            )

            return


        # ========================================================
        # TODO CORRECTO
        # ========================================================

        if archivos_convertidos and not errores:

            if cantidad_convertidos == 1:

                nombre_resultado = obtener_nombre_archivo(
                    archivos_convertidos[0]
                )

                self.panel_conversion.etiqueta_estado.setText(
                    "Archivo convertido correctamente."
                )

                texto_aviso = (
                    "El archivo se convirtió correctamente.\n\n"
                    f"{nombre_resultado}"
                )

            else:

                self.panel_conversion.etiqueta_estado.setText(
                    f"{cantidad_convertidos} archivos "
                    "convertidos correctamente."
                )

                texto_aviso = (
                    f"{cantidad_convertidos} archivos se "
                    "convirtieron correctamente."
                )


            if cantidad_omitidos:

                texto_aviso += (
                    f"\n\n{cantidad_omitidos} archivo(s) "
                    "fueron omitidos."
                )


            QMessageBox.information(
                self,
                "Conversión completada",
                texto_aviso
            )

            return


        # ========================================================
        # CONVERSIÓN CON ERRORES
        # ========================================================

        if errores:

            if cantidad_convertidos:

                self.panel_conversion.etiqueta_estado.setText(
                    f"{cantidad_convertidos} archivo(s) convertidos, "
                    "pero se encontraron algunos errores."
                )

                texto = (
                    f"{cantidad_convertidos} archivo(s) se "
                    "convirtieron correctamente.\n\n"
                    "Se encontraron estos errores:\n\n"
                    + "\n\n".join(
                        errores
                    )
                )

            else:

                self.panel_conversion.etiqueta_estado.setText(
                    "No fue posible realizar la conversión."
                )

                texto = (
                    "No fue posible convertir los archivos.\n\n"
                    + "\n\n".join(
                        errores
                    )
                )


            QMessageBox.warning(
                self,
                "Conversión incompleta",
                texto
            )


    # ============================================================
    # LIMPIAR HILO DE CONVERSIÓN
    # ============================================================
    def limpiar_hilo_conversion(self):

        self.trabajador_conversion = None
        self.hilo_conversion = None


    # ============================================================
    # INTERFAZ RESPONSIVE
    # ============================================================
    def actualizar_interfaz_responsive(self):

        ancho_ventana = self.width()


        if ancho_ventana >= self.ancho_minimo_previsualizacion:

            if not self.previsualizacion_visible:

                self.panel_previsualizacion.setVisible(
                    True
                )

                self.divisor_principal.setSizes(
                    [
                        400,
                        ancho_ventana - 400
                    ]
                )

                self.previsualizacion_visible = True


        else:

            if self.previsualizacion_visible:

                self.panel_previsualizacion.setVisible(
                    False
                )

                self.previsualizacion_visible = False


    # ============================================================
    # CAMBIO DE TAMAÑO
    # ============================================================
    def resizeEvent(self, evento):

        if hasattr(
            self,
            "panel_previsualizacion"
        ):

            self.actualizar_interfaz_responsive()

        super().resizeEvent(
            evento
        )


    # ============================================================
    # CERRAR APLICACIÓN
    # ============================================================
    def closeEvent(self, evento):

        self.invalidar_previsualizacion(
            "original"
        )

        self.invalidar_previsualizacion(
            "resultado"
        )


        # Esperar a que terminen los trabajos
        # de previsualización activos
        for registro in list(
            self.trabajos_previsualizacion
        ):

            hilo = registro[
                "hilo"
            ]

            if hilo.isRunning():

                hilo.quit()
                hilo.wait()


        super().closeEvent(
            evento
        )