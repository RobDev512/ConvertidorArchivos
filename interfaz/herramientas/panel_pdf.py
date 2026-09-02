import os

from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
    Slot,
    QObject,
    QThread,
    QMimeData
)

from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QKeyEvent,
    QDrag,
    QColor,
    QPen
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QListView,
    QAbstractItemView,
    QFileDialog,
    QMessageBox,
    QApplication,
    QStyledItemDelegate
)

from conversiones.previsualizacion import (
    obtener_cantidad_paginas_pdf,
    renderizar_pagina_pdf
)

from herramientas.pdf.unir_pdf import (
    unir_paginas_pdf
)


# ----------------------------------- #
#      Tamaño de las miniaturas       #
# ----------------------------------- #

ANCHO_ICONO_PAGINA = 150
ALTO_ICONO_PAGINA = 190

ANCHO_ELEMENTO_PAGINA = 180
ALTO_ELEMENTO_PAGINA = 245


# ----------------------------------- #
#       Tipo de arrastre interno      #
# ----------------------------------- #

MIME_PAGINAS_PDF = (
    "application/x-convertidor-archivos-paginas-pdf"
)


# ----------------------------------- #
#       Datos internos visuales       #
# ----------------------------------- #

ROL_MARCADOR_INSERCION = (
    Qt.ItemDataRole.UserRole
    + 10
)

ROL_ELEMENTO_ARRASTRANDO = (
    Qt.ItemDataRole.UserRole
    + 11
)


# ================================================================
# DELEGADO VISUAL DE PÁGINAS
# ================================================================
class DelegadoPaginasPDF(QStyledItemDelegate):

    # ============================================================
    # DIBUJAR ELEMENTO
    # ============================================================
    def paint(
        self,
        painter,
        option,
        index
    ):

        # ----------------------------------- #
        #        Marcador de inserción        #
        # ----------------------------------- #

        es_marcador = index.data(
            ROL_MARCADOR_INSERCION
        )


        if es_marcador:

            painter.save()

            painter.setRenderHint(
                painter.RenderHint.Antialiasing,
                True
            )


            # ----------------------------------- #
            #              Fondo                  #
            # ----------------------------------- #

            color_fondo = QColor(
                80,
                160,
                255,
                22
            )

            painter.setBrush(
                color_fondo
            )


            # ----------------------------------- #
            #          Borde punteado             #
            # ----------------------------------- #

            color_borde = QColor(
                80,
                160,
                255,
                220
            )

            lapiz = QPen(
                color_borde
            )

            lapiz.setWidth(
                2
            )

            lapiz.setStyle(
                Qt.PenStyle.DashLine
            )

            painter.setPen(
                lapiz
            )


            # ----------------------------------- #
            #            Rectángulo               #
            # ----------------------------------- #

            rectangulo = option.rect.adjusted(
                9,
                9,
                -9,
                -9
            )

            painter.drawRoundedRect(
                rectangulo,
                12,
                12
            )


            # ----------------------------------- #
            #              Texto                  #
            # ----------------------------------- #

            painter.setPen(
                QColor(
                    120,
                    185,
                    255,
                    230
                )
            )

            painter.drawText(
                rectangulo,
                Qt.AlignmentFlag.AlignCenter,
                "Soltar aquí"
            )

            painter.restore()

            return


        # ----------------------------------- #
        #         Página arrastrada           #
        # ----------------------------------- #

        arrastrando = index.data(
            ROL_ELEMENTO_ARRASTRANDO
        )


        if arrastrando:

            painter.save()

            painter.setOpacity(
                0.32
            )

            super().paint(
                painter,
                option,
                index
            )

            painter.restore()

            return


        # ----------------------------------- #
        #           Página normal             #
        # ----------------------------------- #

        super().paint(
            painter,
            option,
            index
        )


# ================================================================
# TRABAJADOR DE MINIATURAS PDF
# ================================================================
class TrabajadorMiniaturasPDF(QObject):

    pagina_generada = Signal(
        str,
        int,
        bytes
    )

    error_archivo = Signal(
        str,
        str
    )

    finalizado = Signal()


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        archivos
    ):

        super().__init__()

        self.archivos = archivos
        self.cancelado = False


    # ============================================================
    # EJECUTAR
    # ============================================================
    @Slot()
    def ejecutar(
        self
    ):

        try:

            for ruta_pdf in self.archivos:

                if self.cancelado:
                    break


                try:

                    cantidad_paginas = (
                        obtener_cantidad_paginas_pdf(
                            ruta_pdf
                        )
                    )


                    for indice_pagina in range(
                        cantidad_paginas
                    ):

                        if self.cancelado:
                            break


                        datos_imagen = (
                            renderizar_pagina_pdf(
                                ruta_pdf,
                                indice_pagina
                            )
                        )


                        self.pagina_generada.emit(
                            ruta_pdf,
                            indice_pagina,
                            datos_imagen
                        )


                except Exception as error:

                    self.error_archivo.emit(
                        ruta_pdf,
                        str(
                            error
                        )
                    )


        finally:

            self.finalizado.emit()


    # ============================================================
    # CANCELAR
    # ============================================================
    def cancelar(
        self
    ):

        self.cancelado = True


# ================================================================
# LISTA DE PÁGINAS PDF
# ================================================================
class ListaPaginasPDF(QListWidget):

    archivos_pdf_soltados = Signal(
        list
    )

    paginas_modificadas = Signal()


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


        # ----------------------------------- #
        #          Estado de arrastre         #
        # ----------------------------------- #

        self.filas_arrastradas = []

        self.elementos_arrastrados = []

        self.marcador_insercion = None

        self.indice_insercion = None


        # ----------------------------------- #
        #          Preparar lista             #
        # ----------------------------------- #

        self.configurar_lista()


    # ============================================================
    # CONFIGURAR LISTA
    # ============================================================
    def configurar_lista(
        self
    ):

        # ----------------------------------- #
        #       Delegado personalizado        #
        # ----------------------------------- #

        self.setItemDelegate(
            DelegadoPaginasPDF(
                self
            )
        )


        # ----------------------------------- #
        #        Distribución visual          #
        # ----------------------------------- #

        self.setViewMode(
            QListView.ViewMode.IconMode
        )

        self.setFlow(
            QListView.Flow.LeftToRight
        )

        self.setWrapping(
            True
        )

        self.setResizeMode(
            QListView.ResizeMode.Adjust
        )

        self.setMovement(
            QListView.Movement.Snap
        )


        # ----------------------------------- #
        #          Tamaño de páginas          #
        # ----------------------------------- #

        self.setIconSize(
            QSize(
                ANCHO_ICONO_PAGINA,
                ALTO_ICONO_PAGINA
            )
        )

        self.setGridSize(
            QSize(
                ANCHO_ELEMENTO_PAGINA,
                ALTO_ELEMENTO_PAGINA
            )
        )

        self.setSpacing(
            8
        )

        self.setWordWrap(
            True
        )


        # ----------------------------------- #
        #             Selección               #
        # ----------------------------------- #

        self.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )


        # ----------------------------------- #
        #          Arrastrar y soltar         #
        # ----------------------------------- #

        self.setDragEnabled(
            True
        )

        self.setAcceptDrops(
            True
        )

        self.setDropIndicatorShown(
            False
        )

        self.setDragDropMode(
            QAbstractItemView.DragDropMode.DragDrop
        )

        self.setDefaultDropAction(
            Qt.DropAction.MoveAction
        )

        self.setDragDropOverwriteMode(
            False
        )


        # ----------------------------------- #
        #            Apariencia               #
        # ----------------------------------- #

        self.setMinimumHeight(
            420
        )

        self.setStyleSheet(
            """
            QListWidget {
                border: 1px solid rgba(128, 128, 128, 90);
                border-radius: 10px;
                padding: 12px;
            }

            QListWidget::item {
                border: 1px solid transparent;
                border-radius: 8px;
                padding: 6px;
            }

            QListWidget::item:hover {
                border: 1px solid rgba(100, 170, 255, 150);
            }

            QListWidget::item:selected {
                border: 2px solid rgba(80, 160, 255, 230);
            }
            """
        )


    # ============================================================
    # INICIAR ARRASTRE
    # ============================================================
    def startDrag(
        self,
        supported_actions
    ):

        elementos = self.selectedItems()


        if not elementos:

            return


        # ----------------------------------- #
        #      Guardar elementos actuales     #
        # ----------------------------------- #

        self.elementos_arrastrados = list(
            elementos
        )

        self.filas_arrastradas = sorted(
            [
                self.row(
                    elemento
                )
                for elemento in elementos
            ]
        )


        if not self.filas_arrastradas:

            return


        # ----------------------------------- #
        #       Reducir opacidad visual       #
        # ----------------------------------- #

        for elemento in self.elementos_arrastrados:

            elemento.setData(
                ROL_ELEMENTO_ARRASTRANDO,
                True
            )


        self.viewport().update()


        # ----------------------------------- #
        #       Datos del arrastre            #
        # ----------------------------------- #

        mime_data = QMimeData()

        mime_data.setData(
            MIME_PAGINAS_PDF,
            b"paginas_pdf"
        )


        # ----------------------------------- #
        #             Arrastre                #
        # ----------------------------------- #

        arrastre = QDrag(
            self
        )

        arrastre.setMimeData(
            mime_data
        )


        # ----------------------------------- #
        #     Miniatura durante arrastre      #
        # ----------------------------------- #

        primer_elemento = elementos[
            0
        ]

        pixmap = primer_elemento.icon().pixmap(
            QSize(
                110,
                140
            )
        )


        if not pixmap.isNull():

            arrastre.setPixmap(
                pixmap
            )


        # ----------------------------------- #
        #              Ejecutar               #
        # ----------------------------------- #

        try:

            arrastre.exec(
                Qt.DropAction.MoveAction
            )


        finally:

            # ----------------------------------- #
            #       Restaurar apariencia          #
            # ----------------------------------- #

            self.quitar_marcador_insercion()


            for elemento in self.elementos_arrastrados:

                elemento.setData(
                    ROL_ELEMENTO_ARRASTRANDO,
                    False
                )


            self.elementos_arrastrados = []

            self.filas_arrastradas = []

            self.viewport().update()


    # ============================================================
    # ARRASTRAR SOBRE LA LISTA
    # ============================================================
    def dragEnterEvent(
        self,
        evento
    ):

        # ----------------------------------- #
        #        Arrastre interno             #
        # ----------------------------------- #

        if evento.mimeData().hasFormat(
            MIME_PAGINAS_PDF
        ):

            evento.setDropAction(
                Qt.DropAction.MoveAction
            )

            evento.accept()

            return


        # ----------------------------------- #
        #       PDF desde Explorador          #
        # ----------------------------------- #

        if evento.mimeData().hasUrls():

            archivos = [
                url.toLocalFile()
                for url in evento.mimeData().urls()
            ]


            if any(
                archivo.lower().endswith(
                    ".pdf"
                )
                for archivo in archivos
            ):

                evento.acceptProposedAction()

                return


        evento.ignore()


    # ============================================================
    # MOVER SOBRE LA LISTA
    # ============================================================
    def dragMoveEvent(
        self,
        evento
    ):

        # ----------------------------------- #
        #        Arrastre interno             #
        # ----------------------------------- #

        if evento.mimeData().hasFormat(
            MIME_PAGINAS_PDF
        ):

            posicion = evento.position().toPoint()


            self.actualizar_marcador_insercion(
                posicion
            )


            evento.setDropAction(
                Qt.DropAction.MoveAction
            )

            evento.accept()

            return


        # ----------------------------------- #
        #       PDF desde Explorador          #
        # ----------------------------------- #

        if evento.mimeData().hasUrls():

            evento.acceptProposedAction()

            return


        evento.ignore()


    # ============================================================
    # SALIR DEL ÁREA DE ARRASTRE
    # ============================================================
    def dragLeaveEvent(
        self,
        evento
    ):

        self.quitar_marcador_insercion()

        evento.accept()


    # ============================================================
    # SOLTAR
    # ============================================================
    def dropEvent(
        self,
        evento
    ):

        # ----------------------------------- #
        #       PDF desde el explorador       #
        # ----------------------------------- #

        if evento.mimeData().hasUrls():

            archivos = []


            for url in evento.mimeData().urls():

                ruta = url.toLocalFile()


                if (
                    os.path.isfile(
                        ruta
                    )
                    and ruta.lower().endswith(
                        ".pdf"
                    )
                ):

                    archivos.append(
                        ruta
                    )


            if archivos:

                self.archivos_pdf_soltados.emit(
                    archivos
                )

                evento.acceptProposedAction()

                return


        # ----------------------------------- #
        #      Reordenamiento de páginas      #
        # ----------------------------------- #

        if evento.mimeData().hasFormat(
            MIME_PAGINAS_PDF
        ):

            indice_destino = self.indice_insercion


            if indice_destino is None:

                self.quitar_marcador_insercion()

                indice_destino = (
                    self.calcular_indice_insercion(
                        evento.position().toPoint()
                    )
                )


            else:

                self.quitar_marcador_insercion()


            self.mover_paginas_seleccionadas(
                indice_destino
            )


            evento.setDropAction(
                Qt.DropAction.MoveAction
            )

            evento.accept()

            return


        evento.ignore()


    # ============================================================
    # ACTUALIZAR MARCADOR DE INSERCIÓN
    # ============================================================
    def actualizar_marcador_insercion(
        self,
        posicion
    ):

        # ----------------------------------- #
        #        Quitar marcador previo       #
        # ----------------------------------- #

        self.quitar_marcador_insercion()


        # ----------------------------------- #
        #       Calcular nuevo destino        #
        # ----------------------------------- #

        indice = self.calcular_indice_insercion(
            posicion
        )


        # ----------------------------------- #
        #       Ignorar movimiento nulo       #
        # ----------------------------------- #

        if not self.movimiento_cambiaria_orden(
            indice
        ):

            self.viewport().update()

            return


        # ----------------------------------- #
        #          Crear marcador             #
        # ----------------------------------- #

        marcador = QListWidgetItem()

        marcador.setData(
            ROL_MARCADOR_INSERCION,
            True
        )

        marcador.setSizeHint(
            QSize(
                ANCHO_ELEMENTO_PAGINA,
                ALTO_ELEMENTO_PAGINA
            )
        )

        marcador.setFlags(
            Qt.ItemFlag.NoItemFlags
        )


        # ----------------------------------- #
        #           Insertarlo                #
        # ----------------------------------- #

        self.insertItem(
            indice,
            marcador
        )


        self.marcador_insercion = marcador

        self.indice_insercion = indice


        self.viewport().update()


    # ============================================================
    # QUITAR MARCADOR DE INSERCIÓN
    # ============================================================
    def quitar_marcador_insercion(
        self
    ):

        if self.marcador_insercion is not None:

            fila = self.row(
                self.marcador_insercion
            )


            if fila >= 0:

                self.takeItem(
                    fila
                )


        self.marcador_insercion = None

        self.indice_insercion = None


        self.viewport().update()


    # ============================================================
    # COMPROBAR SI EL MOVIMIENTO CAMBIA EL ORDEN
    # ============================================================
    def movimiento_cambiaria_orden(
        self,
        indice_destino
    ):

        filas = sorted(
            self.filas_arrastradas
        )


        if not filas:

            return False


        cantidad = self.count()


        indice_destino = max(
            0,
            min(
                indice_destino,
                cantidad
            )
        )


        # ----------------------------------- #
        #       Representar orden actual      #
        # ----------------------------------- #

        orden_original = list(
            range(
                cantidad
            )
        )


        filas_validas = [
            fila
            for fila in filas
            if 0 <= fila < cantidad
        ]


        if len(
            filas_validas
        ) != len(
            filas
        ):

            return False


        conjunto_filas = set(
            filas_validas
        )


        elementos_movidos = [
            orden_original[
                fila
            ]
            for fila in filas_validas
        ]


        elementos_restantes = [
            elemento
            for indice, elemento in enumerate(
                orden_original
            )
            if indice not in conjunto_filas
        ]


        # ----------------------------------- #
        #     Ajustar índice tras extraer     #
        # ----------------------------------- #

        cantidad_anteriores = sum(
            1
            for fila in filas_validas
            if fila < indice_destino
        )


        indice_ajustado = (
            indice_destino
            - cantidad_anteriores
        )


        indice_ajustado = max(
            0,
            min(
                indice_ajustado,
                len(
                    elementos_restantes
                )
            )
        )


        # ----------------------------------- #
        #       Simular resultado final       #
        # ----------------------------------- #

        orden_resultante = (
            elementos_restantes[
                :indice_ajustado
            ]
            + elementos_movidos
            + elementos_restantes[
                indice_ajustado:
            ]
        )


        return (
            orden_resultante
            != orden_original
        )

    # ============================================================
    # CALCULAR ÍNDICE DE INSERCIÓN
    # ============================================================
    def calcular_indice_insercion(
        self,
        posicion
    ):

        cantidad = self.count()


        if cantidad <= 0:

            return 0


        # ----------------------------------- #
        #       Obtener rectángulos           #
        # ----------------------------------- #

        datos_elementos = []


        for indice in range(
            cantidad
        ):

            elemento = self.item(
                indice
            )


            if elemento.data(
                ROL_MARCADOR_INSERCION
            ):

                continue


            rectangulo = self.visualItemRect(
                elemento
            )


            if not rectangulo.isValid():

                continue


            datos_elementos.append(
                (
                    indice,
                    rectangulo
                )
            )


        if not datos_elementos:

            return cantidad


        # ----------------------------------- #
        #       Antes del primer elemento     #
        # ----------------------------------- #

        _, primer_rectangulo = (
            datos_elementos[
                0
            ]
        )


        if posicion.y() < primer_rectangulo.top():

            return 0


        # ----------------------------------- #
        #      Después del último elemento    #
        # ----------------------------------- #

        _, ultimo_rectangulo = (
            datos_elementos[
                -1
            ]
        )


        if (
            posicion.y()
            > ultimo_rectangulo.bottom()
            + ALTO_ELEMENTO_PAGINA // 2
        ):

            return cantidad


        # ----------------------------------- #
        #       Buscar fila visual cercana    #
        # ----------------------------------- #

        distancia_vertical_minima = None

        centro_y_fila = None


        for _, rectangulo in datos_elementos:

            distancia = abs(
                posicion.y()
                - rectangulo.center().y()
            )


            if (
                distancia_vertical_minima is None
                or distancia < distancia_vertical_minima
            ):

                distancia_vertical_minima = distancia

                centro_y_fila = (
                    rectangulo.center().y()
                )


        # ----------------------------------- #
        #      Elementos de esa fila          #
        # ----------------------------------- #

        elementos_fila = []


        for indice, rectangulo in datos_elementos:

            if abs(
                rectangulo.center().y()
                - centro_y_fila
            ) <= 10:

                elementos_fila.append(
                    (
                        indice,
                        rectangulo
                    )
                )


        elementos_fila.sort(
            key=lambda datos:
            datos[
                1
            ].left()
        )


        if not elementos_fila:

            return cantidad


        # ----------------------------------- #
        #     Antes del primero de la fila    #
        # ----------------------------------- #

        primer_indice_fila, primer_rectangulo_fila = (
            elementos_fila[
                0
            ]
        )


        if (
            posicion.x()
            < primer_rectangulo_fila.center().x()
        ):

            return primer_indice_fila


        # ----------------------------------- #
        #       Entre las miniaturas          #
        # ----------------------------------- #

        for indice, rectangulo in elementos_fila:

            if (
                posicion.x()
                < rectangulo.center().x()
            ):

                return indice


        # ----------------------------------- #
        #      Después del último de fila     #
        # ----------------------------------- #

        ultimo_indice_fila, _ = elementos_fila[
            -1
        ]


        return min(
            ultimo_indice_fila + 1,
            cantidad
        )


    # ============================================================
    # MOVER PÁGINAS SELECCIONADAS
    # ============================================================
    def mover_paginas_seleccionadas(
        self,
        indice_destino
    ):

        filas = sorted(
            self.filas_arrastradas
        )


        if not filas:

            return


        # ----------------------------------- #
        #       Limitar destino               #
        # ----------------------------------- #

        indice_destino = max(
            0,
            min(
                indice_destino,
                self.count()
            )
        )

        # ----------------------------------- #
        #       Ignorar movimiento nulo       #
        # ----------------------------------- #

        if not self.movimiento_cambiaria_orden(
            indice_destino
        ):

            return


        # ----------------------------------- #
        # Ajustar destino por las extracciones#
        # ----------------------------------- #

        cantidad_anteriores = sum(
            1
            for fila in filas
            if fila < indice_destino
        )

        indice_destino_ajustado = (
            indice_destino
            - cantidad_anteriores
        )


        # ----------------------------------- #
        #        Extraer de atrás             #
        # ----------------------------------- #

        elementos_extraidos = []


        for fila in reversed(
            filas
        ):

            elemento = self.takeItem(
                fila
            )


            if elemento is not None:

                elementos_extraidos.append(
                    elemento
                )


        elementos_extraidos.reverse()


        # ----------------------------------- #
        #       Insertar en destino           #
        # ----------------------------------- #

        for desplazamiento, elemento in enumerate(
            elementos_extraidos
        ):

            self.insertItem(
                indice_destino_ajustado
                + desplazamiento,
                elemento
            )


        # ----------------------------------- #
        #        Restaurar selección          #
        # ----------------------------------- #

        self.clearSelection()


        for elemento in elementos_extraidos:

            elemento.setSelected(
                True
            )


        if elementos_extraidos:

            self.setCurrentItem(
                elementos_extraidos[
                    0
                ]
            )

            self.scrollToItem(
                elementos_extraidos[
                    0
                ],
                QAbstractItemView.ScrollHint.EnsureVisible
            )


        self.paginas_modificadas.emit()


    # ============================================================
    # TECLAS
    # ============================================================
    def keyPressEvent(
        self,
        evento: QKeyEvent
    ):

        if evento.key() == Qt.Key.Key_Delete:

            self.eliminar_paginas_seleccionadas()

            return


        super().keyPressEvent(
            evento
        )


    # ============================================================
    # ELIMINAR PÁGINAS SELECCIONADAS
    # ============================================================
    def eliminar_paginas_seleccionadas(
        self
    ):

        filas = sorted(
            [
                self.row(
                    elemento
                )
                for elemento in self.selectedItems()
            ],
            reverse=True
        )


        for fila in filas:

            self.takeItem(
                fila
            )


        if filas:

            self.paginas_modificadas.emit()


# ================================================================
# PANEL PDF
# ================================================================
class PanelPDF(QWidget):

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


        # ----------------------------------- #
        #       Carga de miniaturas           #
        # ----------------------------------- #

        self.hilo_carga = None
        self.trabajador_carga = None

        self.errores_carga = []


        # ----------------------------------- #
        #           Preparar panel            #
        # ----------------------------------- #

        self.crear_interfaz()
        self.conectar_eventos()

        self.actualizar_contador()


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
            20,
            22,
            20
        )

        self.distribucion.setSpacing(
            12
        )


        # ----------------------------------- #
        #               Título                #
        # ----------------------------------- #

        self.etiqueta_titulo = QLabel(
            "Unir PDFs"
        )

        self.etiqueta_titulo.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: 600;
            }
            """
        )

        self.distribucion.addWidget(
            self.etiqueta_titulo
        )


        # ----------------------------------- #
        #            Descripción              #
        # ----------------------------------- #

        self.etiqueta_descripcion = QLabel(
            "Añade uno o varios archivos PDF. "
            "Puedes arrastrar las páginas para cambiar su orden "
            "antes de crear el documento final."
        )

        self.etiqueta_descripcion.setWordWrap(
            True
        )

        self.distribucion.addWidget(
            self.etiqueta_descripcion
        )


        # ========================================================
        # BARRA DE ACCIONES
        # ========================================================

        self.distribucion_acciones = QHBoxLayout()

        self.distribucion_acciones.setSpacing(
            8
        )


        # ----------------------------------- #
        #           Añadir PDFs               #
        # ----------------------------------- #

        self.boton_agregar = QPushButton(
            "Añadir PDFs"
        )

        self.boton_agregar.setMinimumHeight(
            38
        )

        self.distribucion_acciones.addWidget(
            self.boton_agregar
        )


        # ----------------------------------- #
        #        Eliminar páginas             #
        # ----------------------------------- #

        self.boton_eliminar = QPushButton(
            "Eliminar páginas"
        )

        self.boton_eliminar.setMinimumHeight(
            38
        )

        self.boton_eliminar.setEnabled(
            False
        )

        self.distribucion_acciones.addWidget(
            self.boton_eliminar
        )


        # ----------------------------------- #
        #              Vaciar                 #
        # ----------------------------------- #

        self.boton_vaciar = QPushButton(
            "Vaciar"
        )

        self.boton_vaciar.setMinimumHeight(
            38
        )

        self.boton_vaciar.setEnabled(
            False
        )

        self.distribucion_acciones.addWidget(
            self.boton_vaciar
        )


        self.distribucion_acciones.addStretch(
            1
        )

        self.distribucion.addLayout(
            self.distribucion_acciones
        )


        # ========================================================
        # LISTA DE PÁGINAS
        # ========================================================

        self.lista_paginas = ListaPaginasPDF()

        self.distribucion.addWidget(
            self.lista_paginas,
            1
        )


        # ========================================================
        # INFORMACIÓN INFERIOR
        # ========================================================

        self.distribucion_informacion = QHBoxLayout()


        # ----------------------------------- #
        #            Contador                 #
        # ----------------------------------- #

        self.etiqueta_contador = QLabel()

        self.distribucion_informacion.addWidget(
            self.etiqueta_contador
        )


        self.distribucion_informacion.addStretch(
            1
        )


        # ----------------------------------- #
        #              Estado                 #
        # ----------------------------------- #

        self.etiqueta_estado = QLabel(
            "Arrastra las miniaturas para cambiar el orden."
        )

        self.distribucion_informacion.addWidget(
            self.etiqueta_estado
        )


        self.distribucion.addLayout(
            self.distribucion_informacion
        )


        # ========================================================
        # BOTÓN UNIR PDF
        # ========================================================

        self.boton_unir = QPushButton(
            "Unir PDFs"
        )

        self.boton_unir.setMinimumHeight(
            52
        )

        self.boton_unir.setEnabled(
            False
        )

        self.boton_unir.setStyleSheet(
            """
            QPushButton {
                font-size: 15px;
                font-weight: 600;
            }
            """
        )

        self.distribucion.addWidget(
            self.boton_unir
        )


    # ============================================================
    # CONECTAR EVENTOS
    # ============================================================
    def conectar_eventos(
        self
    ):

        self.boton_agregar.clicked.connect(
            self.seleccionar_pdfs
        )

        self.boton_eliminar.clicked.connect(
            self.eliminar_paginas
        )

        self.boton_vaciar.clicked.connect(
            self.vaciar_paginas
        )

        self.boton_unir.clicked.connect(
            self.crear_pdf_unido
        )


        # ----------------------------------- #
        #             Lista                   #
        # ----------------------------------- #

        self.lista_paginas.itemSelectionChanged.connect(
            self.actualizar_seleccion
        )

        self.lista_paginas.paginas_modificadas.connect(
            self.actualizar_contador
        )

        self.lista_paginas.archivos_pdf_soltados.connect(
            self.cargar_pdfs
        )


    # ============================================================
    # SELECCIONAR PDF
    # ============================================================
    def seleccionar_pdfs(
        self
    ):

        archivos, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivos PDF",
            "",
            "Archivos PDF (*.pdf)"
        )


        if not archivos:

            return


        self.cargar_pdfs(
            archivos
        )


    # ============================================================
    # CARGAR PDF
    # ============================================================
    def cargar_pdfs(
        self,
        archivos
    ):

        # ----------------------------------- #
        #           Normalizar                #
        # ----------------------------------- #

        archivos_validos = []


        for ruta in archivos:

            ruta = os.path.abspath(
                os.path.normpath(
                    ruta
                )
            )


            if (
                os.path.isfile(
                    ruta
                )
                and ruta.lower().endswith(
                    ".pdf"
                )
            ):

                archivos_validos.append(
                    ruta
                )


        if not archivos_validos:

            return


        # ----------------------------------- #
        #      Evitar dos cargas simultáneas  #
        # ----------------------------------- #

        if self.hilo_carga is not None:

            QMessageBox.information(
                self,
                "Unir PDFs",
                "Espera a que terminen de cargarse "
                "las páginas actuales."
            )

            return


        # ----------------------------------- #
        #          Preparar interfaz          #
        # ----------------------------------- #

        self.errores_carga = []

        self.boton_agregar.setEnabled(
            False
        )

        self.boton_unir.setEnabled(
            False
        )

        self.etiqueta_estado.setText(
            "Generando miniaturas..."
        )


        # ----------------------------------- #
        #               Hilo                  #
        # ----------------------------------- #

        self.hilo_carga = QThread(
            self
        )


        # ----------------------------------- #
        #            Trabajador               #
        # ----------------------------------- #

        self.trabajador_carga = TrabajadorMiniaturasPDF(
            archivos_validos
        )

        self.trabajador_carga.moveToThread(
            self.hilo_carga
        )


        # ----------------------------------- #
        #             Eventos                 #
        # ----------------------------------- #

        self.hilo_carga.started.connect(
            self.trabajador_carga.ejecutar
        )

        self.trabajador_carga.pagina_generada.connect(
            self.agregar_miniatura
        )

        self.trabajador_carga.error_archivo.connect(
            self.registrar_error_carga
        )

        self.trabajador_carga.finalizado.connect(
            self.hilo_carga.quit
        )

        self.trabajador_carga.finalizado.connect(
            self.trabajador_carga.deleteLater
        )

        self.hilo_carga.finished.connect(
            self.finalizar_carga
        )

        self.hilo_carga.finished.connect(
            self.hilo_carga.deleteLater
        )


        # ----------------------------------- #
        #              Iniciar                #
        # ----------------------------------- #

        self.hilo_carga.start()


    # ============================================================
    # AGREGAR MINIATURA
    # ============================================================
    @Slot(
        str,
        int,
        bytes
    )
    def agregar_miniatura(
        self,
        ruta_pdf,
        indice_pagina,
        datos_imagen
    ):

        # ----------------------------------- #
        #           Crear imagen              #
        # ----------------------------------- #

        pixmap = QPixmap()

        cargado = pixmap.loadFromData(
            datos_imagen,
            "PNG"
        )


        if not cargado:

            return


        pixmap = pixmap.scaled(
            ANCHO_ICONO_PAGINA,
            ALTO_ICONO_PAGINA,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )


        # ----------------------------------- #
        #           Datos visibles            #
        # ----------------------------------- #

        nombre_archivo = os.path.basename(
            ruta_pdf
        )

        numero_pagina = (
            indice_pagina
            + 1
        )


        texto = (
            f"{nombre_archivo}\n"
            f"Página {numero_pagina}"
        )


        # ----------------------------------- #
        #             Elemento                #
        # ----------------------------------- #

        elemento = QListWidgetItem()

        elemento.setIcon(
            QIcon(
                pixmap
            )
        )

        elemento.setText(
            texto
        )

        elemento.setTextAlignment(
            Qt.AlignmentFlag.AlignHCenter
            | Qt.AlignmentFlag.AlignTop
        )

        elemento.setSizeHint(
            QSize(
                ANCHO_ELEMENTO_PAGINA,
                ALTO_ELEMENTO_PAGINA
            )
        )


        # ----------------------------------- #
        #         Datos internos              #
        # ----------------------------------- #

        elemento.setData(
            Qt.ItemDataRole.UserRole,
            (
                ruta_pdf,
                indice_pagina
            )
        )


        elemento.setToolTip(
            (
                f"{ruta_pdf}\n"
                f"Página {numero_pagina}"
            )
        )


        self.lista_paginas.addItem(
            elemento
        )


        # ----------------------------------- #
        #           Actualizar                #
        # ----------------------------------- #

        self.etiqueta_estado.setText(
            (
                f"Cargando {nombre_archivo} "
                f"- página {numero_pagina}..."
            )
        )

        self.actualizar_contador()


    # ============================================================
    # REGISTRAR ERROR DE CARGA
    # ============================================================
    @Slot(
        str,
        str
    )
    def registrar_error_carga(
        self,
        ruta_pdf,
        mensaje
    ):

        self.errores_carga.append(
            (
                ruta_pdf,
                mensaje
            )
        )


    # ============================================================
    # FINALIZAR CARGA
    # ============================================================
    def finalizar_carga(
        self
    ):

        self.hilo_carga = None
        self.trabajador_carga = None


        # ----------------------------------- #
        #          Restaurar botones          #
        # ----------------------------------- #

        self.boton_agregar.setEnabled(
            True
        )

        self.actualizar_contador()


        # ----------------------------------- #
        #              Estado                 #
        # ----------------------------------- #

        self.etiqueta_estado.setText(
            "Arrastra las miniaturas para cambiar el orden."
        )


        # ----------------------------------- #
        #             Errores                 #
        # ----------------------------------- #

        if self.errores_carga:

            detalles = []


            for ruta_pdf, mensaje in self.errores_carga:

                detalles.append(
                    (
                        f"{os.path.basename(ruta_pdf)}:\n"
                        f"{mensaje}"
                    )
                )


            QMessageBox.warning(
                self,
                "Unir PDFs",
                (
                    "Algunos archivos no pudieron cargarse.\n\n"
                    + "\n\n".join(
                        detalles
                    )
                )
            )


    # ============================================================
    # ACTUALIZAR SELECCIÓN
    # ============================================================
    def actualizar_seleccion(
        self
    ):

        seleccionados = len(
            self.lista_paginas.selectedItems()
        )


        self.boton_eliminar.setEnabled(
            seleccionados > 0
        )


    # ============================================================
    # ELIMINAR PÁGINAS
    # ============================================================
    def eliminar_paginas(
        self
    ):

        self.lista_paginas.eliminar_paginas_seleccionadas()

        self.actualizar_seleccion()

        self.actualizar_contador()


    # ============================================================
    # VACIAR PÁGINAS
    # ============================================================
    def vaciar_paginas(
        self
    ):

        if self.lista_paginas.count() <= 0:

            return


        respuesta = QMessageBox.question(
            self,
            "Vaciar páginas",
            "¿Quieres quitar todas las páginas de la herramienta?",
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No
        )


        if respuesta != QMessageBox.StandardButton.Yes:

            return


        self.lista_paginas.clear()

        self.actualizar_seleccion()

        self.actualizar_contador()


    # ============================================================
    # OBTENER PÁGINAS
    # ============================================================
    def obtener_paginas(
        self
    ):

        paginas = []


        for indice in range(
            self.lista_paginas.count()
        ):

            elemento = self.lista_paginas.item(
                indice
            )


            # ----------------------------------- #
            #       Ignorar marcador visual      #
            # ----------------------------------- #

            if elemento.data(
                ROL_MARCADOR_INSERCION
            ):

                continue


            datos = elemento.data(
                Qt.ItemDataRole.UserRole
            )


            if not datos:

                continue


            paginas.append(
                (
                    datos[
                        0
                    ],
                    int(
                        datos[
                            1
                        ]
                    )
                )
            )


        return paginas


    # ============================================================
    # ACTUALIZAR CONTADOR
    # ============================================================
    def actualizar_contador(
        self
    ):

        paginas = self.obtener_paginas()

        cantidad_paginas = len(
            paginas
        )


        archivos = list(
            dict.fromkeys(
                ruta_pdf
                for ruta_pdf, _ in paginas
            )
        )

        cantidad_archivos = len(
            archivos
        )


        # ----------------------------------- #
        #              Texto                  #
        # ----------------------------------- #

        texto_paginas = (
            "1 página"
            if cantidad_paginas == 1
            else f"{cantidad_paginas} páginas"
        )

        texto_archivos = (
            "1 archivo"
            if cantidad_archivos == 1
            else f"{cantidad_archivos} archivos"
        )


        self.etiqueta_contador.setText(
            (
                f"{texto_paginas} · "
                f"{texto_archivos}"
            )
        )


        # ----------------------------------- #
        #             Botones                 #
        # ----------------------------------- #

        hay_paginas = (
            cantidad_paginas > 0
        )

        cargando = (
            self.hilo_carga is not None
        )


        self.boton_vaciar.setEnabled(
            hay_paginas
        )

        self.boton_unir.setEnabled(
            hay_paginas
            and not cargando
        )


    # ============================================================
    # CREAR PDF UNIDO
    # ============================================================
    def crear_pdf_unido(
        self
    ):

        paginas = self.obtener_paginas()


        if not paginas:

            return


        # ----------------------------------- #
        #         Ruta sugerida               #
        # ----------------------------------- #

        primera_ruta = paginas[
            0
        ][
            0
        ]

        carpeta_inicial = os.path.dirname(
            primera_ruta
        )

        ruta_sugerida = os.path.join(
            carpeta_inicial,
            "PDF_unido.pdf"
        )


        # ----------------------------------- #
        #        Seleccionar destino          #
        # ----------------------------------- #

        ruta_salida, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF unido",
            ruta_sugerida,
            "Archivos PDF (*.pdf)"
        )


        if not ruta_salida:

            return


        # ----------------------------------- #
        #       Preparar interfaz             #
        # ----------------------------------- #

        self.boton_unir.setEnabled(
            False
        )

        self.boton_agregar.setEnabled(
            False
        )

        self.boton_eliminar.setEnabled(
            False
        )

        self.boton_vaciar.setEnabled(
            False
        )


        QApplication.setOverrideCursor(
            Qt.CursorShape.WaitCursor
        )


        try:

            # ----------------------------------- #
            #          Progreso                   #
            # ----------------------------------- #

            def progreso(
                actual,
                total,
                ruta_pdf
            ):

                self.etiqueta_estado.setText(
                    (
                        f"Procesando página "
                        f"{actual} de {total}..."
                    )
                )

                QApplication.processEvents()


            # ----------------------------------- #
            #            Crear PDF                #
            # ----------------------------------- #

            ruta_resultado = unir_paginas_pdf(
                paginas,
                ruta_salida,
                progreso=progreso
            )


            # ----------------------------------- #
            #             Finalizado              #
            # ----------------------------------- #

            self.etiqueta_estado.setText(
                "PDF creado correctamente."
            )


            QMessageBox.information(
                self,
                "Unir PDFs",
                (
                    "El PDF se creó correctamente:\n\n"
                    f"{ruta_resultado}"
                )
            )


        except Exception as error:

            self.etiqueta_estado.setText(
                "No se pudo crear el PDF."
            )


            QMessageBox.critical(
                self,
                "Unir PDFs",
                str(
                    error
                )
            )


        finally:

            QApplication.restoreOverrideCursor()


            self.boton_agregar.setEnabled(
                True
            )

            self.actualizar_seleccion()

            self.actualizar_contador()


    # ============================================================
    # CANCELAR CARGA
    # ============================================================
    def cancelar_carga(
        self
    ):

        if self.trabajador_carga is not None:

            self.trabajador_carga.cancelar()