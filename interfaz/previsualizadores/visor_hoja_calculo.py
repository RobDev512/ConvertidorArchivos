from PySide6.QtCore import Qt

from PySide6.QtGui import (
    QColor,
    QFont
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView
)


# ================================================================
# VISOR DE HOJA DE CÁLCULO
# ================================================================
class VisorHojaCalculo(QWidget):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self):
        super().__init__()

        self.crear_interfaz()


    # ============================================================
    # CREAR INTERFAZ
    # ============================================================
    def crear_interfaz(self):

        self.distribucion = QVBoxLayout(
            self
        )

        self.distribucion.setContentsMargins(
            5,
            5,
            5,
            5
        )

        self.distribucion.setSpacing(
            8
        )


        # ----------------------------------- #
        #          Nombre del archivo         #
        # ----------------------------------- #

        self.etiqueta_nombre = QLabel()

        self.etiqueta_nombre.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_nombre.setWordWrap(
            True
        )

        self.distribucion.addWidget(
            self.etiqueta_nombre
        )


        # ----------------------------------- #
        #        Pestañas de hojas            #
        # ----------------------------------- #

        self.pestanas = QTabWidget()

        self.distribucion.addWidget(
            self.pestanas,
            1
        )


        # ----------------------------------- #
        #         Información adicional       #
        # ----------------------------------- #

        self.etiqueta_aviso = QLabel()

        self.etiqueta_aviso.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.etiqueta_aviso.setWordWrap(
            True
        )

        self.etiqueta_aviso.setVisible(
            False
        )

        self.distribucion.addWidget(
            self.etiqueta_aviso
        )


    # ============================================================
    # CONVERTIR COLUMNA A LETRA
    # ============================================================
    def columna_a_letra(self, numero):

        resultado = ""

        numero += 1

        while numero:

            numero, resto = divmod(
                numero - 1,
                26
            )

            resultado = (
                chr(
                    65 + resto
                )
                + resultado
            )

        return resultado


    # ============================================================
    # OBTENER ALINEACIÓN QT
    # ============================================================
    def obtener_alineacion(
        self,
        horizontal,
        vertical
    ):

        alineacion = (
            Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignLeft
        )


        # ----------------------------------- #
        #           Horizontal               #
        # ----------------------------------- #

        if horizontal == "center":

            alineacion = (
                alineacion
                & ~Qt.AlignmentFlag.AlignLeft
            )

            alineacion |= (
                Qt.AlignmentFlag.AlignHCenter
            )

        elif horizontal == "right":

            alineacion = (
                alineacion
                & ~Qt.AlignmentFlag.AlignLeft
            )

            alineacion |= (
                Qt.AlignmentFlag.AlignRight
            )


        # ----------------------------------- #
        #            Vertical                #
        # ----------------------------------- #

        if vertical == "top":

            alineacion = (
                alineacion
                & ~Qt.AlignmentFlag.AlignVCenter
            )

            alineacion |= (
                Qt.AlignmentFlag.AlignTop
            )

        elif vertical == "bottom":

            alineacion = (
                alineacion
                & ~Qt.AlignmentFlag.AlignVCenter
            )

            alineacion |= (
                Qt.AlignmentFlag.AlignBottom
            )


        return alineacion


    # ============================================================
    # CREAR TABLA
    # ============================================================
    def crear_tabla(self, hoja):

        tabla = QTableWidget(
            hoja["filas"],
            hoja["columnas"]
        )

        tabla.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        tabla.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectItems
        )

        tabla.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        tabla.setWordWrap(
            True
        )


        # ----------------------------------- #
        #        Encabezados de columnas      #
        # ----------------------------------- #

        encabezados = [
            self.columna_a_letra(
                indice
            )
            for indice in range(
                hoja["columnas"]
            )
        ]

        tabla.setHorizontalHeaderLabels(
            encabezados
        )


        # ----------------------------------- #
        #          Celdas                     #
        # ----------------------------------- #

        for datos in hoja["celdas"]:

            item = QTableWidgetItem(
                datos["texto"]
            )

            item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )


            # -------------------------------- #
            #             Fuente               #
            # -------------------------------- #

            fuente = QFont()

            fuente.setBold(
                datos["negrita"]
            )

            fuente.setItalic(
                datos["cursiva"]
            )

            fuente.setUnderline(
                datos["subrayado"]
            )

            if datos["tamano_fuente"]:

                fuente.setPointSizeF(
                    datos["tamano_fuente"]
                )

            item.setFont(
                fuente
            )


            # -------------------------------- #
            #             Colores              #
            # -------------------------------- #

            if datos["color_fuente"]:

                item.setForeground(
                    QColor(
                        datos["color_fuente"]
                    )
                )

            if datos["color_fondo"]:

                item.setBackground(
                    QColor(
                        datos["color_fondo"]
                    )
                )


            # -------------------------------- #
            #           Alineación             #
            # -------------------------------- #

            item.setTextAlignment(
                self.obtener_alineacion(
                    datos[
                        "alineacion_horizontal"
                    ],
                    datos[
                        "alineacion_vertical"
                    ]
                )
            )


            tabla.setItem(
                datos["fila"],
                datos["columna"],
                item
            )


        # ----------------------------------- #
        #         Celdas combinadas           #
        # ----------------------------------- #

        for (
            fila,
            columna,
            cantidad_filas,
            cantidad_columnas
        ) in hoja["combinadas"]:

            tabla.setSpan(
                fila,
                columna,
                cantidad_filas,
                cantidad_columnas
            )


        # ----------------------------------- #
        #         Anchos de columnas          #
        # ----------------------------------- #

        for columna, ancho in hoja[
            "anchos_columnas"
        ].items():

            tabla.setColumnWidth(
                columna,
                ancho
            )


        # ----------------------------------- #
        #           Altos de filas            #
        # ----------------------------------- #

        for fila, alto in hoja[
            "altos_filas"
        ].items():

            tabla.setRowHeight(
                fila,
                alto
            )


        return tabla


    # ============================================================
    # MOSTRAR LIBRO
    # ============================================================
    def mostrar_libro(
        self,
        ruta_archivo,
        hojas
    ):

        import os

        self.pestanas.clear()

        self.etiqueta_nombre.setText(
            os.path.basename(
                ruta_archivo
            )
        )


        truncada = False


        # ----------------------------------- #
        #         Crear cada hoja             #
        # ----------------------------------- #

        for hoja in hojas:

            tabla = self.crear_tabla(
                hoja
            )

            self.pestanas.addTab(
                tabla,
                hoja["nombre"]
            )

            if hoja["truncada"]:
                truncada = True


        # ----------------------------------- #
        #      Advertencia por tamaño         #
        # ----------------------------------- #

        if truncada:

            self.etiqueta_aviso.setText(
                "La vista previa está limitada a las primeras "
                "300 filas y 80 columnas de hojas muy grandes."
            )

            self.etiqueta_aviso.setVisible(
                True
            )

        else:

            self.etiqueta_aviso.setVisible(
                False
            )