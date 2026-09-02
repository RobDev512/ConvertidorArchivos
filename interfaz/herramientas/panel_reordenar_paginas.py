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
    QToolButton,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QFrame,
    QProgressBar,
    QSizePolicy,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QListView,
    QDialog,
    QStyledItemDelegate
)

from conversiones.previsualizacion import (
    obtener_cantidad_paginas_pdf,
    renderizar_pagina_pdf
)

from herramientas.pdf.reordenar_paginas import (
    reordenar_paginas_pdf
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

MIME_REORDENAR_PAGINAS = (
    "application/x-convertidor-archivos-reordenar-paginas-pdf"
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
class DelegadoPaginasReordenar(
    QStyledItemDelegate
):

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
# LISTA DE PÁGINAS
# ================================================================
class ListaPaginasReordenar(
    QListWidget
):

    orden_modificado = Signal()


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
            DelegadoPaginasReordenar(
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
            QAbstractItemView.SelectionMode.SingleSelection
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

        self.viewport().setAcceptDrops(
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

        self.setAutoScroll(
            True
        )

        self.setAutoScrollMargin(
            45
        )


        # ----------------------------------- #
        #             Tamaño                  #
        # ----------------------------------- #

        self.setMinimumHeight(
            280
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )


        # ----------------------------------- #
        #            Apariencia               #
        # ----------------------------------- #

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
    # AGREGAR PÁGINA
    # ============================================================
    def agregar_pagina(
        self,
        numero_pagina,
        pixmap
    ):

        # ----------------------------------- #
        #            Elemento                 #
        # ----------------------------------- #

        elemento = QListWidgetItem()

        elemento.setIcon(
            QIcon(
                pixmap
            )
        )

        elemento.setText(
            f"Página {numero_pagina}"
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
            numero_pagina - 1
        )

        elemento.setData(
            ROL_MARCADOR_INSERCION,
            False
        )

        elemento.setData(
            ROL_ELEMENTO_ARRASTRANDO,
            False
        )

        elemento.setToolTip(
            f"Página original {numero_pagina}"
        )


        # ----------------------------------- #
        #             Añadir                  #
        # ----------------------------------- #

        self.addItem(
            elemento
        )


    # ============================================================
    # OBTENER ORDEN
    # ============================================================
    def obtener_orden(
        self
    ):

        orden = []

        for indice in range(
            self.count()
        ):

            elemento = self.item(
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

            if datos is None:

                continue


            orden.append(
                int(
                    datos
                )
            )


        return orden


    # ============================================================
    # CONTAR PÁGINAS REALES
    # ============================================================
    def obtener_cantidad_paginas(
        self
    ):

        return len(
            self.obtener_orden()
        )


    # ============================================================
    # RESTABLECER ORDEN
    # ============================================================
    def restablecer_orden(
        self
    ):

        self.quitar_marcador_insercion()


        # ----------------------------------- #
        #         Obtener elementos           #
        # ----------------------------------- #

        elementos = []

        while self.count() > 0:

            elemento = self.takeItem(
                0
            )

            if elemento is None:

                continue

            if elemento.data(
                ROL_MARCADOR_INSERCION
            ):

                continue

            elementos.append(
                elemento
            )


        # ----------------------------------- #
        #           Orden original            #
        # ----------------------------------- #

        elementos.sort(
            key=lambda elemento:
            int(
                elemento.data(
                    Qt.ItemDataRole.UserRole
                )
            )
        )


        # ----------------------------------- #
        #            Restaurar                #
        # ----------------------------------- #

        for elemento in elementos:

            elemento.setData(
                ROL_ELEMENTO_ARRASTRANDO,
                False
            )

            self.addItem(
                elemento
            )


        self.clearSelection()

        self.orden_modificado.emit()


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
            MIME_REORDENAR_PAGINAS,
            b"reordenar_paginas_pdf"
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

        if evento.mimeData().hasFormat(
            MIME_REORDENAR_PAGINAS
        ):

            evento.setDropAction(
                Qt.DropAction.MoveAction
            )

            evento.accept()

            return


        evento.ignore()


    # ============================================================
    # MOVER SOBRE LA LISTA
    # ============================================================
    def dragMoveEvent(
        self,
        evento
    ):

        if evento.mimeData().hasFormat(
            MIME_REORDENAR_PAGINAS
        ):

            posicion = evento.position().toPoint()


            # ----------------------------------- #
            #      Marcador como elemento real   #
            # ----------------------------------- #

            self.actualizar_marcador_insercion(
                posicion
            )


            evento.setDropAction(
                Qt.DropAction.MoveAction
            )

            evento.accept()

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

        if evento.mimeData().hasFormat(
            MIME_REORDENAR_PAGINAS
        ):

            indice_destino = (
                self.indice_insercion
            )


            # ----------------------------------- #
            #     Si no quedó marcador activo    #
            # ----------------------------------- #

            if indice_destino is None:

                self.quitar_marcador_insercion()

                indice_destino = (
                    self.calcular_indice_insercion(
                        evento.position().toPoint()
                    )
                )


            else:

                # ----------------------------------- #
                # Quitar el hueco antes de mover     #
                # ----------------------------------- #

                self.quitar_marcador_insercion()


            # ----------------------------------- #
            #            Mover página             #
            # ----------------------------------- #

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

        if len(
            self.filas_arrastradas
        ) == 1:

            fila_origen = self.filas_arrastradas[
                0
            ]

            if indice in {
                fila_origen,
                fila_origen + 1
            }:

                self.indice_insercion = None

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

        (
            primer_indice_fila,
            primer_rectangulo_fila
        ) = elementos_fila[
            0
        ]


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

        ultimo_indice_fila, _ = (
            elementos_fila[
                -1
            ]
        )


        return min(
            ultimo_indice_fila + 1,
            cantidad
        )


    # ============================================================
    # MOVER PÁGINA SELECCIONADA
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


        self.orden_modificado.emit()


# ================================================================
# DIÁLOGO DE VISTA AMPLIADA
# ================================================================
class DialogoPaginasAmpliadas(
    QDialog
):

    cierre_solicitado = Signal()


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

        self.permitir_cierre = False

        self.setWindowTitle(
            "Reordenar páginas - Vista ampliada"
        )

        self.setWindowModality(
            Qt.WindowModality.ApplicationModal
        )

        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e1e;
            }
            """
        )


    # ============================================================
    # EVENTO DE CIERRE
    # ============================================================
    def closeEvent(
        self,
        event
    ):

        if self.permitir_cierre:

            event.accept()

            return

        self.cierre_solicitado.emit()

        event.ignore()


# ================================================================
# MARCO DE PÁGINAS AMPLIABLE
# ================================================================
class MarcoPaginasReordenar(
    QFrame
):

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

        self.dialogo_ampliado = None

        self.padre_original = None

        self.layout_original = None

        self.indice_original = -1

        self.setFrameShape(
            QFrame.Shape.NoFrame
        )


        # ----------------------------------- #
        #          Botón ampliar              #
        # ----------------------------------- #

        self.boton_ampliar = QToolButton(
            self
        )

        self.boton_ampliar.setText(
            "⛶"
        )

        self.boton_ampliar.setToolTip(
            "Ampliar área de páginas"
        )

        self.boton_ampliar.setFixedSize(
            36,
            36
        )

        self.boton_ampliar.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.boton_ampliar.setStyleSheet(
            """
            QToolButton {
                background-color: #2d2d30;
                color: #f0f0f0;
                border: 1px solid #555555;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 600;
            }

            QToolButton:hover {
                background-color: #353b45;
                border-color: #6b9ee8;
                color: #ffffff;
            }

            QToolButton:pressed {
                background-color: #29384f;
                border-color: #2d7ff9;
            }
            """
        )

        self.boton_ampliar.clicked.connect(
            self.alternar_ampliacion
        )

        self.boton_ampliar.raise_()


    # ============================================================
    # EVENTO DE REDIMENSIONADO
    # ============================================================
    def resizeEvent(
        self,
        event
    ):

        super().resizeEvent(
            event
        )

        self.boton_ampliar.move(
            max(
                0,
                self.width()
                - self.boton_ampliar.width()
                - 14
            ),
            10
        )

        self.boton_ampliar.raise_()


    # ============================================================
    # ALTERNAR AMPLIACIÓN
    # ============================================================
    def alternar_ampliacion(
        self
    ):

        if self.dialogo_ampliado is None:

            self.ampliar()

        else:

            self.restaurar()


    # ============================================================
    # AMPLIAR
    # ============================================================
    def ampliar(
        self
    ):

        padre = self.parentWidget()


        if padre is None:

            return


        layout_padre = padre.layout()


        if layout_padre is None:

            return


        indice = layout_padre.indexOf(
            self
        )


        if indice < 0:

            return


        # ----------------------------------- #
        #       Recordar posición original    #
        # ----------------------------------- #

        self.padre_original = padre

        self.layout_original = layout_padre

        self.indice_original = indice


        # ----------------------------------- #
        #       Sacar del panel actual        #
        # ----------------------------------- #

        layout_padre.removeWidget(
            self
        )


        # ----------------------------------- #
        #       Crear ventana ampliada        #
        # ----------------------------------- #

        dialogo = DialogoPaginasAmpliadas(
            self.window()
        )

        layout_dialogo = QVBoxLayout(
            dialogo
        )

        layout_dialogo.setContentsMargins(
            12,
            12,
            12,
            12
        )


        # ----------------------------------- #
        #       Reutilizar mismo marco        #
        # ----------------------------------- #

        self.setParent(
            dialogo
        )

        layout_dialogo.addWidget(
            self
        )


        self.dialogo_ampliado = dialogo


        dialogo.cierre_solicitado.connect(
            self.restaurar
        )


        self.boton_ampliar.setText(
            "↙"
        )

        self.boton_ampliar.setToolTip(
            "Restaurar área de páginas"
        )


        dialogo.showMaximized()


    # ============================================================
    # RESTAURAR
    # ============================================================
    def restaurar(
        self
    ):

        if self.dialogo_ampliado is None:

            return


        dialogo = self.dialogo_ampliado

        layout_dialogo = dialogo.layout()


        if layout_dialogo is not None:

            layout_dialogo.removeWidget(
                self
            )


        # ----------------------------------- #
        #       Volver al panel original      #
        # ----------------------------------- #

        self.setParent(
            self.padre_original
        )


        if (
            self.layout_original is not None
            and self.indice_original >= 0
        ):

            self.layout_original.insertWidget(
                self.indice_original,
                self
            )


        self.boton_ampliar.setText(
            "⛶"
        )

        self.boton_ampliar.setToolTip(
            "Ampliar área de páginas"
        )


        self.dialogo_ampliado = None


        dialogo.permitir_cierre = True

        dialogo.close()

        dialogo.deleteLater()


        self.show()


# ================================================================
# TRABAJADOR DE MINIATURAS
# ================================================================
class TrabajadorMiniaturasReordenar(
    QObject
):

    pagina_lista = Signal(
        int,
        bytes
    )

    progreso = Signal(
        int
    )

    terminado = Signal(
        int
    )

    cancelado = Signal()

    error = Signal(
        str
    )


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        ruta_pdf
    ):

        super().__init__()

        self.ruta_pdf = ruta_pdf

        self.cancelacion_solicitada = False


    # ============================================================
    # CANCELAR
    # ============================================================
    @Slot()
    def cancelar(
        self
    ):

        self.cancelacion_solicitada = True


    # ============================================================
    # EJECUTAR
    # ============================================================
    @Slot()
    def ejecutar(
        self
    ):

        try:

            cantidad_paginas = (
                obtener_cantidad_paginas_pdf(
                    self.ruta_pdf
                )
            )


            for indice_pagina in range(
                cantidad_paginas
            ):

                if self.cancelacion_solicitada:

                    self.cancelado.emit()

                    return


                datos = renderizar_pagina_pdf(
                    self.ruta_pdf,
                    indice_pagina
                )


                if self.cancelacion_solicitada:

                    self.cancelado.emit()

                    return


                self.pagina_lista.emit(
                    indice_pagina + 1,
                    datos
                )


                porcentaje = round(
                    (
                        indice_pagina + 1
                    )
                    / cantidad_paginas
                    * 100
                )


                self.progreso.emit(
                    porcentaje
                )


            self.terminado.emit(
                cantidad_paginas
            )


        except Exception as error:

            self.error.emit(
                str(
                    error
                )
            )


# ================================================================
# TRABAJADOR DE REORDENAMIENTO
# ================================================================
class TrabajadorReordenarPDF(
    QObject
):

    progreso = Signal(
        int
    )

    terminado = Signal(
        str
    )

    cancelado = Signal()

    error = Signal(
        str
    )


    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(
        self,
        ruta_pdf,
        orden_paginas,
        ruta_salida
    ):

        super().__init__()

        self.ruta_pdf = ruta_pdf

        self.orden_paginas = orden_paginas

        self.ruta_salida = ruta_salida

        self.cancelacion_solicitada = False


    # ============================================================
    # CANCELAR
    # ============================================================
    @Slot()
    def cancelar(
        self
    ):

        self.cancelacion_solicitada = True


    # ============================================================
    # COMPROBAR CANCELACIÓN
    # ============================================================
    def comprobar_cancelacion(
        self
    ):

        return self.cancelacion_solicitada


    # ============================================================
    # EJECUTAR
    # ============================================================
    @Slot()
    def ejecutar(
        self
    ):

        try:

            resultado = reordenar_paginas_pdf(
                self.ruta_pdf,
                self.orden_paginas,
                self.ruta_salida,
                progreso=self.progreso.emit,
                comprobar_cancelacion=(
                    self.comprobar_cancelacion
                )
            )


            if (
                self.cancelacion_solicitada
                or resultado is None
            ):

                self.cancelado.emit()

                return


            self.terminado.emit(
                resultado
            )


        except Exception as error:

            self.error.emit(
                str(
                    error
                )
            )


# ================================================================
# PANEL REORDENAR PÁGINAS
# ================================================================
class PanelReordenarPaginas(
    QWidget
):

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
        #            Archivo PDF              #
        # ----------------------------------- #

        self.ruta_pdf = None


        # ----------------------------------- #
        #         Carga de miniaturas         #
        # ----------------------------------- #

        self.hilo_miniaturas = None

        self.trabajador_miniaturas = None


        # ----------------------------------- #
        #          Reordenamiento             #
        # ----------------------------------- #

        self.hilo_reordenamiento = None

        self.trabajador_reordenamiento = None


        # ----------------------------------- #
        #              Estado                 #
        # ----------------------------------- #

        self.cargando = False

        self.procesando = False


        # ----------------------------------- #
        #             Interfaz                #
        # ----------------------------------- #

        self.crear_interfaz()

        self.conectar_eventos()

        self.actualizar_estado_controles()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(
        self
    ):

        distribucion_principal = QVBoxLayout(
            self
        )

        distribucion_principal.setContentsMargins(
            24,
            20,
            24,
            22
        )

        distribucion_principal.setSpacing(
            14
        )


        # ----------------------------------- #
        #               Título                #
        # ----------------------------------- #

        titulo = QLabel(
            "Reordenar páginas"
        )

        titulo.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: 700;
            }
            """
        )


        descripcion = QLabel(
            "Cambia el orden de las páginas de un PDF "
            "arrastrándolas a la posición que quieras."
        )

        descripcion.setWordWrap(
            True
        )

        descripcion.setStyleSheet(
            """
            QLabel {
                color: #8590a5;
                font-size: 13px;
            }
            """
        )


        distribucion_principal.addWidget(
            titulo
        )

        distribucion_principal.addWidget(
            descripcion
        )


        # ----------------------------------- #
        #          Archivo de entrada         #
        # ----------------------------------- #

        fila_archivo = QHBoxLayout()

        fila_archivo.setSpacing(
            10
        )


        self.campo_pdf = QLineEdit()

        self.campo_pdf.setReadOnly(
            True
        )

        self.campo_pdf.setPlaceholderText(
            "Selecciona un archivo PDF"
        )

        self.campo_pdf.setMinimumHeight(
            38
        )


        self.boton_seleccionar = QPushButton(
            "Seleccionar PDF"
        )

        self.boton_seleccionar.setMinimumSize(
            150,
            38
        )


        fila_archivo.addWidget(
            self.campo_pdf,
            1
        )

        fila_archivo.addWidget(
            self.boton_seleccionar
        )


        distribucion_principal.addLayout(
            fila_archivo
        )


        # ----------------------------------- #
        #          Controles de orden         #
        # ----------------------------------- #

        fila_controles = QHBoxLayout()

        fila_controles.setSpacing(
            10
        )


        etiqueta_paginas = QLabel(
            "Páginas"
        )

        etiqueta_paginas.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                font-weight: 600;
            }
            """
        )


        self.boton_restablecer = QPushButton(
            "Restablecer orden"
        )

        self.boton_restablecer.setMinimumSize(
            160,
            34
        )


        fila_controles.addWidget(
            etiqueta_paginas
        )

        fila_controles.addStretch(
            1
        )

        fila_controles.addWidget(
            self.boton_restablecer
        )


        distribucion_principal.addLayout(
            fila_controles
        )


        # ----------------------------------- #
        #           Área de páginas           #
        # ----------------------------------- #

        self.marco_paginas = (
            MarcoPaginasReordenar()
        )


        distribucion_marco = QVBoxLayout(
            self.marco_paginas
        )

        distribucion_marco.setContentsMargins(
            0,
            0,
            0,
            0
        )


        self.lista_paginas = (
            ListaPaginasReordenar()
        )


        distribucion_marco.addWidget(
            self.lista_paginas
        )


        distribucion_principal.addWidget(
            self.marco_paginas,
            1
        )


        # ----------------------------------- #
        #          Resumen del orden          #
        # ----------------------------------- #

        self.etiqueta_resumen = QLabel(
            "Selecciona un PDF para comenzar."
        )

        self.etiqueta_resumen.setStyleSheet(
            """
            QLabel {
                color: #8590a5;
                font-size: 12px;
            }
            """
        )


        distribucion_principal.addWidget(
            self.etiqueta_resumen
        )


        # ----------------------------------- #
        #          Archivo de salida          #
        # ----------------------------------- #

        fila_salida = QHBoxLayout()

        fila_salida.setSpacing(
            10
        )


        self.campo_salida = QLineEdit()

        self.campo_salida.setReadOnly(
            True
        )

        self.campo_salida.setPlaceholderText(
            "Archivo PDF de salida"
        )

        self.campo_salida.setMinimumHeight(
            38
        )


        self.boton_salida = QPushButton(
            "Elegir salida"
        )

        self.boton_salida.setMinimumSize(
            150,
            38
        )


        fila_salida.addWidget(
            self.campo_salida,
            1
        )

        fila_salida.addWidget(
            self.boton_salida
        )


        distribucion_principal.addLayout(
            fila_salida
        )


        # ----------------------------------- #
        #              Progreso               #
        # ----------------------------------- #

        self.barra_progreso = QProgressBar()

        self.barra_progreso.setRange(
            0,
            100
        )

        self.barra_progreso.setValue(
            0
        )

        self.barra_progreso.setTextVisible(
            True
        )

        self.barra_progreso.setVisible(
            False
        )


        distribucion_principal.addWidget(
            self.barra_progreso
        )


        # ----------------------------------- #
        #         Botones principales         #
        # ----------------------------------- #

        fila_acciones = QHBoxLayout()

        fila_acciones.addStretch(
            1
        )


        self.boton_cancelar = QPushButton(
            "Cancelar"
        )

        self.boton_cancelar.setMinimumSize(
            130,
            42
        )

        self.boton_cancelar.setVisible(
            False
        )


        self.boton_guardar = QPushButton(
            "Guardar PDF reordenado"
        )

        self.boton_guardar.setMinimumSize(
            210,
            42
        )

        self.boton_guardar.setStyleSheet(
            """
            QPushButton {
                background-color: #2d7ff9;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #1f6fe5;
            }

            QPushButton:pressed {
                background-color: #185fc6;
            }

            QPushButton:disabled {
                background-color: #566071;
                color: #b7bdc8;
            }
            """
        )


        fila_acciones.addWidget(
            self.boton_cancelar
        )

        fila_acciones.addWidget(
            self.boton_guardar
        )


        distribucion_principal.addLayout(
            fila_acciones
        )


    # ============================================================
    # CONECTAR EVENTOS
    # ============================================================
    def conectar_eventos(
        self
    ):

        self.boton_seleccionar.clicked.connect(
            self.seleccionar_pdf
        )

        self.boton_salida.clicked.connect(
            self.seleccionar_salida
        )

        self.boton_restablecer.clicked.connect(
            self.restablecer_orden
        )

        self.boton_guardar.clicked.connect(
            self.guardar_pdf
        )

        self.boton_cancelar.clicked.connect(
            self.cancelar_operacion
        )

        self.lista_paginas.orden_modificado.connect(
            self.actualizar_resumen
        )


    # ============================================================
    # SELECCIONAR PDF
    # ============================================================
    @Slot()
    def seleccionar_pdf(
        self
    ):

        if (
            self.cargando
            or self.procesando
        ):

            return


        ruta_pdf, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar PDF",
            "",
            "Archivos PDF (*.pdf)"
        )


        if not ruta_pdf:

            return


        self.cargar_pdf(
            ruta_pdf
        )


    # ============================================================
    # CARGAR PDF
    # ============================================================
    def cargar_pdf(
        self,
        ruta_pdf
    ):

        ruta_pdf = os.path.abspath(
            ruta_pdf
        )


        self.ruta_pdf = ruta_pdf


        self.campo_pdf.setText(
            ruta_pdf
        )


        self.lista_paginas.clear()


        self.asignar_salida_predeterminada()


        # ----------------------------------- #
        #           Estado de carga           #
        # ----------------------------------- #

        self.cargando = True


        self.barra_progreso.setValue(
            0
        )

        self.barra_progreso.setVisible(
            True
        )


        self.etiqueta_resumen.setText(
            "Cargando páginas..."
        )


        self.actualizar_estado_controles()


        # ----------------------------------- #
        #               Hilo                  #
        # ----------------------------------- #

        hilo = QThread(
            self
        )


        trabajador = (
            TrabajadorMiniaturasReordenar(
                ruta_pdf
            )
        )


        trabajador.moveToThread(
            hilo
        )


        hilo.started.connect(
            trabajador.ejecutar
        )


        trabajador.pagina_lista.connect(
            self.agregar_miniatura
        )

        trabajador.progreso.connect(
            self.barra_progreso.setValue
        )

        trabajador.terminado.connect(
            self.carga_terminada
        )

        trabajador.cancelado.connect(
            self.carga_cancelada
        )

        trabajador.error.connect(
            self.error_carga
        )


        trabajador.terminado.connect(
            hilo.quit
        )

        trabajador.cancelado.connect(
            hilo.quit
        )

        trabajador.error.connect(
            hilo.quit
        )


        hilo.finished.connect(
            trabajador.deleteLater
        )

        hilo.finished.connect(
            hilo.deleteLater
        )

        hilo.finished.connect(
            self.limpiar_hilo_miniaturas
        )


        self.hilo_miniaturas = hilo

        self.trabajador_miniaturas = trabajador


        hilo.start()


    # ============================================================
    # AGREGAR MINIATURA
    # ============================================================
    @Slot(
        int,
        bytes
    )
    def agregar_miniatura(
        self,
        numero_pagina,
        datos
    ):

        pixmap = QPixmap()


        cargado = pixmap.loadFromData(
            datos,
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


        self.lista_paginas.agregar_pagina(
            numero_pagina,
            pixmap
        )


    # ============================================================
    # CARGA TERMINADA
    # ============================================================
    @Slot(
        int
    )
    def carga_terminada(
        self,
        cantidad_paginas
    ):

        self.cargando = False


        self.barra_progreso.setVisible(
            False
        )


        self.actualizar_resumen()

        self.actualizar_estado_controles()


    # ============================================================
    # CARGA CANCELADA
    # ============================================================
    @Slot()
    def carga_cancelada(
        self
    ):

        self.cargando = False


        self.lista_paginas.clear()


        self.barra_progreso.setVisible(
            False
        )


        self.etiqueta_resumen.setText(
            "Carga cancelada."
        )


        self.actualizar_estado_controles()


    # ============================================================
    # ERROR DE CARGA
    # ============================================================
    @Slot(
        str
    )
    def error_carga(
        self,
        mensaje
    ):

        self.cargando = False


        self.lista_paginas.clear()


        self.barra_progreso.setVisible(
            False
        )


        self.actualizar_estado_controles()


        QMessageBox.critical(
            self,
            "No se pudo abrir el PDF",
            mensaje
        )


    # ============================================================
    # LIMPIAR HILO DE MINIATURAS
    # ============================================================
    @Slot()
    def limpiar_hilo_miniaturas(
        self
    ):

        self.hilo_miniaturas = None

        self.trabajador_miniaturas = None


    # ============================================================
    # ASIGNAR SALIDA PREDETERMINADA
    # ============================================================
    def asignar_salida_predeterminada(
        self
    ):

        if not self.ruta_pdf:

            self.campo_salida.clear()

            return


        carpeta = os.path.dirname(
            self.ruta_pdf
        )


        nombre = os.path.splitext(
            os.path.basename(
                self.ruta_pdf
            )
        )[0]


        ruta_salida = os.path.join(
            carpeta,
            f"{nombre}_reordenado.pdf"
        )


        self.campo_salida.setText(
            ruta_salida
        )


    # ============================================================
    # SELECCIONAR SALIDA
    # ============================================================
    @Slot()
    def seleccionar_salida(
        self
    ):

        if (
            self.cargando
            or self.procesando
        ):

            return


        ruta_inicial = (
            self.campo_salida.text().strip()
        )


        if not ruta_inicial:

            ruta_inicial = ""


        ruta_salida, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Guardar PDF reordenado",
                ruta_inicial,
                "Archivos PDF (*.pdf)"
            )
        )


        if not ruta_salida:

            return


        if not ruta_salida.lower().endswith(
            ".pdf"
        ):

            ruta_salida += ".pdf"


        self.campo_salida.setText(
            os.path.abspath(
                ruta_salida
            )
        )


        self.actualizar_estado_controles()


    # ============================================================
    # RESTABLECER ORDEN
    # ============================================================
    @Slot()
    def restablecer_orden(
        self
    ):

        if (
            self.cargando
            or self.procesando
        ):

            return


        self.lista_paginas.restablecer_orden()


    # ============================================================
    # OBTENER ORDEN
    # ============================================================
    def obtener_orden_actual(
        self
    ):

        return self.lista_paginas.obtener_orden()


    # ============================================================
    # ORDEN ORIGINAL
    # ============================================================
    def orden_es_original(
        self
    ):

        orden = self.obtener_orden_actual()


        return orden == list(
            range(
                len(
                    orden
                )
            )
        )


    # ============================================================
    # ACTUALIZAR RESUMEN
    # ============================================================
    @Slot()
    def actualizar_resumen(
        self
    ):

        orden = self.obtener_orden_actual()

        cantidad = len(
            orden
        )


        if cantidad <= 0:

            if not self.cargando:

                self.etiqueta_resumen.setText(
                    "Selecciona un PDF para comenzar."
                )


            self.actualizar_estado_controles()

            return


        if orden == list(
            range(
                cantidad
            )
        ):

            estado = "Orden original"

        else:

            estado = "Orden modificado"


        texto_paginas = (
            "página"
            if cantidad == 1
            else "páginas"
        )


        self.etiqueta_resumen.setText(
            f"{cantidad} {texto_paginas} · {estado}"
        )


        self.actualizar_estado_controles()


    # ============================================================
    # GUARDAR PDF
    # ============================================================
    @Slot()
    def guardar_pdf(
        self
    ):

        if (
            self.cargando
            or self.procesando
        ):

            return


        if not self.ruta_pdf:

            QMessageBox.warning(
                self,
                "Falta el PDF",
                "Selecciona un archivo PDF."
            )

            return


        orden = self.obtener_orden_actual()


        if not orden:

            QMessageBox.warning(
                self,
                "Sin páginas",
                "No hay páginas para guardar."
            )

            return


        ruta_salida = (
            self.campo_salida.text().strip()
        )


        if not ruta_salida:

            QMessageBox.warning(
                self,
                "Falta la salida",
                (
                    "Elige dónde guardar "
                    "el PDF reordenado."
                )
            )

            return


        if not ruta_salida.lower().endswith(
            ".pdf"
        ):

            ruta_salida += ".pdf"


            self.campo_salida.setText(
                ruta_salida
            )


        ruta_salida = os.path.abspath(
            ruta_salida
        )


        # ----------------------------------- #
        #       No reemplazar original        #
        # ----------------------------------- #

        if (
            os.path.normcase(
                ruta_salida
            )
            == os.path.normcase(
                self.ruta_pdf
            )
        ):

            QMessageBox.warning(
                self,
                "Ruta no válida",
                (
                    "El archivo de salida debe "
                    "ser diferente al PDF original."
                )
            )

            return


        # ----------------------------------- #
        #          Archivo existente          #
        # ----------------------------------- #

        if os.path.isfile(
            ruta_salida
        ):

            respuesta = QMessageBox.question(
                self,
                "El archivo ya existe",
                (
                    "Ya existe un archivo con ese nombre.\n\n"
                    "¿Quieres reemplazarlo?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No
            )


            if (
                respuesta
                != QMessageBox.StandardButton.Yes
            ):

                return


        # ----------------------------------- #
        #         Crear resultado             #
        # ----------------------------------- #

        self.iniciar_reordenamiento(
            orden,
            ruta_salida
        )


    # ============================================================
    # INICIAR REORDENAMIENTO
    # ============================================================
    def iniciar_reordenamiento(
        self,
        orden,
        ruta_salida
    ):

        self.procesando = True


        self.barra_progreso.setValue(
            0
        )

        self.barra_progreso.setVisible(
            True
        )


        self.actualizar_estado_controles()


        # ----------------------------------- #
        #               Hilo                  #
        # ----------------------------------- #

        hilo = QThread(
            self
        )


        trabajador = (
            TrabajadorReordenarPDF(
                self.ruta_pdf,
                orden,
                ruta_salida
            )
        )


        trabajador.moveToThread(
            hilo
        )


        hilo.started.connect(
            trabajador.ejecutar
        )


        trabajador.progreso.connect(
            self.barra_progreso.setValue
        )

        trabajador.terminado.connect(
            self.reordenamiento_terminado
        )

        trabajador.cancelado.connect(
            self.reordenamiento_cancelado
        )

        trabajador.error.connect(
            self.error_reordenamiento
        )


        trabajador.terminado.connect(
            hilo.quit
        )

        trabajador.cancelado.connect(
            hilo.quit
        )

        trabajador.error.connect(
            hilo.quit
        )


        hilo.finished.connect(
            trabajador.deleteLater
        )

        hilo.finished.connect(
            hilo.deleteLater
        )

        hilo.finished.connect(
            self.limpiar_hilo_reordenamiento
        )


        self.hilo_reordenamiento = hilo

        self.trabajador_reordenamiento = trabajador


        hilo.start()


    # ============================================================
    # REORDENAMIENTO TERMINADO
    # ============================================================
    @Slot(
        str
    )
    def reordenamiento_terminado(
        self,
        ruta_salida
    ):

        self.procesando = False


        self.barra_progreso.setValue(
            100
        )

        self.barra_progreso.setVisible(
            False
        )


        self.actualizar_estado_controles()


        QMessageBox.information(
            self,
            "PDF reordenado",
            (
                "El PDF se guardó correctamente.\n\n"
                f"{ruta_salida}"
            )
        )


    # ============================================================
    # REORDENAMIENTO CANCELADO
    # ============================================================
    @Slot()
    def reordenamiento_cancelado(
        self
    ):

        self.procesando = False


        self.barra_progreso.setVisible(
            False
        )


        self.actualizar_estado_controles()


    # ============================================================
    # ERROR DE REORDENAMIENTO
    # ============================================================
    @Slot(
        str
    )
    def error_reordenamiento(
        self,
        mensaje
    ):

        self.procesando = False


        self.barra_progreso.setVisible(
            False
        )


        self.actualizar_estado_controles()


        QMessageBox.critical(
            self,
            "No se pudo reordenar el PDF",
            mensaje
        )


    # ============================================================
    # LIMPIAR HILO DE REORDENAMIENTO
    # ============================================================
    @Slot()
    def limpiar_hilo_reordenamiento(
        self
    ):

        self.hilo_reordenamiento = None

        self.trabajador_reordenamiento = None


    # ============================================================
    # CANCELAR OPERACIÓN
    # ============================================================
    @Slot()
    def cancelar_operacion(
        self
    ):

        if (
            self.cargando
            and self.trabajador_miniaturas is not None
        ):

            self.trabajador_miniaturas.cancelar()

            return


        if (
            self.procesando
            and self.trabajador_reordenamiento is not None
        ):

            self.trabajador_reordenamiento.cancelar()


    # ============================================================
    # ACTUALIZAR ESTADO DE CONTROLES
    # ============================================================
    def actualizar_estado_controles(
        self
    ):

        ocupado = (
            self.cargando
            or self.procesando
        )


        hay_pdf = bool(
            self.ruta_pdf
        )


        hay_paginas = (
            self.lista_paginas.obtener_cantidad_paginas()
            > 0
        )


        hay_salida = bool(
            self.campo_salida.text().strip()
        )


        # ----------------------------------- #
        #         Archivo de entrada          #
        # ----------------------------------- #

        self.boton_seleccionar.setEnabled(
            not ocupado
        )


        # ----------------------------------- #
        #             Salida                  #
        # ----------------------------------- #

        self.boton_salida.setEnabled(
            not ocupado
            and hay_pdf
        )


        # ----------------------------------- #
        #             Páginas                 #
        # ----------------------------------- #

        self.lista_paginas.setEnabled(
            not ocupado
            and hay_paginas
        )


        self.boton_restablecer.setEnabled(
            not ocupado
            and hay_paginas
            and not self.orden_es_original()
        )


        # ----------------------------------- #
        #             Guardar                 #
        # ----------------------------------- #

        self.boton_guardar.setEnabled(
            not ocupado
            and hay_pdf
            and hay_paginas
            and hay_salida
        )


        # ----------------------------------- #
        #             Cancelar                #
        # ----------------------------------- #

        self.boton_cancelar.setVisible(
            ocupado
        )