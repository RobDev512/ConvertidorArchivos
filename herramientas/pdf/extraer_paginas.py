import os
import shutil
import tempfile

from pypdf import (
    PdfReader,
    PdfWriter
)


# ================================================================
# EXTRAER PÁGINAS UNIDAS
# ================================================================
def extraer_paginas_unidas(
    ruta_pdf,
    paginas,
    carpeta_salida,
    prefijo=None,
    progreso=None,
    comprobar_cancelacion=None,
    sobrescribir=False
):

    ruta_pdf = validar_ruta_pdf(
        ruta_pdf
    )

    carpeta_salida = preparar_carpeta_salida(
        carpeta_salida
    )


    with open(
        ruta_pdf,
        "rb"
    ) as archivo_pdf:

        lector = crear_lector_pdf(
            archivo_pdf,
            ruta_pdf
        )

        paginas = validar_paginas_seleccionadas(
            paginas,
            len(
                lector.pages
            )
        )


        if not prefijo:

            prefijo = obtener_prefijo_pdf(
                ruta_pdf
            )


        ruta_salida = os.path.join(
            carpeta_salida,
            f"{prefijo}_seleccion.pdf"
        )


        crear_pdfs_desde_grupos(
            lector,
            [
                paginas
            ],
            [
                ruta_salida
            ],
            progreso=progreso,
            comprobar_cancelacion=(
                comprobar_cancelacion
            ),
            sobrescribir=sobrescribir
        )


        return [
            ruta_salida
        ]


# ================================================================
# EXTRAER PÁGINAS INDIVIDUALES
# ================================================================
def extraer_paginas_individuales(
    ruta_pdf,
    paginas,
    carpeta_salida,
    prefijo=None,
    progreso=None,
    comprobar_cancelacion=None,
    sobrescribir=False
):

    ruta_pdf = validar_ruta_pdf(
        ruta_pdf
    )

    carpeta_salida = preparar_carpeta_salida(
        carpeta_salida
    )


    with open(
        ruta_pdf,
        "rb"
    ) as archivo_pdf:

        lector = crear_lector_pdf(
            archivo_pdf,
            ruta_pdf
        )

        cantidad_paginas = len(
            lector.pages
        )

        paginas = validar_paginas_seleccionadas(
            paginas,
            cantidad_paginas
        )


        if not prefijo:

            prefijo = obtener_prefijo_pdf(
                ruta_pdf
            )


        digitos = max(
            2,
            len(
                str(
                    cantidad_paginas
                )
            )
        )


        grupos = []

        rutas_salida = []


        for numero_pagina in paginas:

            grupos.append(
                [
                    numero_pagina
                ]
            )

            rutas_salida.append(
                os.path.join(
                    carpeta_salida,
                    (
                        f"{prefijo}_pagina_"
                        f"{numero_pagina:0{digitos}d}.pdf"
                    )
                )
            )


        crear_pdfs_desde_grupos(
            lector,
            grupos,
            rutas_salida,
            progreso=progreso,
            comprobar_cancelacion=(
                comprobar_cancelacion
            ),
            sobrescribir=sobrescribir
        )


        return rutas_salida


# ================================================================
# SEPARAR SELECCIONADAS Y RESTO
# ================================================================
def separar_seleccionadas_y_resto(
    ruta_pdf,
    paginas,
    carpeta_salida,
    prefijo=None,
    progreso=None,
    comprobar_cancelacion=None,
    sobrescribir=False
):

    ruta_pdf = validar_ruta_pdf(
        ruta_pdf
    )

    carpeta_salida = preparar_carpeta_salida(
        carpeta_salida
    )


    with open(
        ruta_pdf,
        "rb"
    ) as archivo_pdf:

        lector = crear_lector_pdf(
            archivo_pdf,
            ruta_pdf
        )

        cantidad_paginas = len(
            lector.pages
        )

        seleccionadas = validar_paginas_seleccionadas(
            paginas,
            cantidad_paginas
        )


        # ----------------------------------- #
        #              Resto                  #
        # ----------------------------------- #

        conjunto_seleccionadas = set(
            seleccionadas
        )

        resto = [
            numero_pagina
            for numero_pagina in range(
                1,
                cantidad_paginas + 1
            )
            if numero_pagina
            not in conjunto_seleccionadas
        ]


        if not resto:

            raise ValueError(
                "Para separar las páginas seleccionadas "
                "del resto debe quedar al menos una página "
                "sin seleccionar."
            )


        # ----------------------------------- #
        #             Prefijo                 #
        # ----------------------------------- #

        if not prefijo:

            prefijo = obtener_prefijo_pdf(
                ruta_pdf
            )


        ruta_seleccionadas = os.path.join(
            carpeta_salida,
            f"{prefijo}_seleccionadas.pdf"
        )

        ruta_resto = os.path.join(
            carpeta_salida,
            f"{prefijo}_resto.pdf"
        )


        # ----------------------------------- #
        #             Crear PDFs              #
        # ----------------------------------- #

        crear_pdfs_desde_grupos(
            lector,
            [
                seleccionadas,
                resto
            ],
            [
                ruta_seleccionadas,
                ruta_resto
            ],
            progreso=progreso,
            comprobar_cancelacion=(
                comprobar_cancelacion
            ),
            sobrescribir=sobrescribir
        )


        return [
            ruta_seleccionadas,
            ruta_resto
        ]


# ================================================================
# CREAR PDFS DESDE GRUPOS
# ================================================================
def crear_pdfs_desde_grupos(
    lector,
    grupos,
    rutas_salida,
    progreso=None,
    comprobar_cancelacion=None,
    sobrescribir=False
):

    if len(
        grupos
    ) != len(
        rutas_salida
    ):

        raise ValueError(
            "La cantidad de grupos y archivos de salida "
            "no coincide."
        )


    # ----------------------------------- #
    #       Comprobar conflictos          #
    # ----------------------------------- #

    if not sobrescribir:

        for ruta_salida in rutas_salida:

            if os.path.exists(
                ruta_salida
            ):

                raise FileExistsError(
                    "Ya existe el archivo:\n\n"
                    f"{ruta_salida}"
                )


    # ----------------------------------- #
    #       Carpeta de trabajo            #
    # ----------------------------------- #

    carpeta_salida = os.path.dirname(
        rutas_salida[
            0
        ]
    )

    carpeta_temporal = tempfile.mkdtemp(
        prefix=".extraer_paginas_",
        dir=carpeta_salida
    )


    rutas_temporales = []


    try:

        cantidad_grupos = len(
            grupos
        )


        # ================================================ #
        # CREAR ARCHIVOS TEMPORALES
        # ================================================ #

        for indice_grupo, grupo in enumerate(
            grupos,
            start=1
        ):

            comprobar_cancelacion_solicitada(
                comprobar_cancelacion
            )


            escritor = PdfWriter()


            try:

                for numero_pagina in grupo:

                    comprobar_cancelacion_solicitada(
                        comprobar_cancelacion
                    )


                    escritor.add_page(
                        lector.pages[
                            numero_pagina - 1
                        ]
                    )


                nombre_temporal = (
                    f"resultado_{indice_grupo:04d}.pdf"
                )

                ruta_temporal = os.path.join(
                    carpeta_temporal,
                    nombre_temporal
                )


                with open(
                    ruta_temporal,
                    "wb"
                ) as archivo_salida:

                    escritor.write(
                        archivo_salida
                    )


                rutas_temporales.append(
                    ruta_temporal
                )


            finally:

                try:

                    escritor.close()

                except Exception:

                    pass


            # ----------------------------------- #
            #             Progreso                #
            # ----------------------------------- #

            if progreso is not None:

                progreso(
                    indice_grupo,
                    cantidad_grupos
                )


        # ================================================ #
        # MOVER A DESTINO
        # ================================================ #

        for ruta_temporal, ruta_final in zip(
            rutas_temporales,
            rutas_salida
        ):

            comprobar_cancelacion_solicitada(
                comprobar_cancelacion
            )


            if (
                os.path.exists(
                    ruta_final
                )
                and not sobrescribir
            ):

                raise FileExistsError(
                    "Ya existe el archivo:\n\n"
                    f"{ruta_final}"
                )


            os.replace(
                ruta_temporal,
                ruta_final
            )


    finally:

        shutil.rmtree(
            carpeta_temporal,
            ignore_errors=True
        )


# ================================================================
# VALIDAR PÁGINAS SELECCIONADAS
# ================================================================
def validar_paginas_seleccionadas(
    paginas,
    cantidad_paginas
):

    if not paginas:

        raise ValueError(
            "No hay páginas seleccionadas."
        )


    paginas_validas = []


    for numero_pagina in paginas:

        if not isinstance(
            numero_pagina,
            int
        ):

            raise ValueError(
                "El número de página no es válido."
            )


        if (
            numero_pagina < 1
            or numero_pagina > cantidad_paginas
        ):

            raise ValueError(
                "Una de las páginas seleccionadas no existe."
            )


        paginas_validas.append(
            numero_pagina
        )


    # ----------------------------------- #
    #     Sin duplicados y en orden       #
    # ----------------------------------- #

    return sorted(
        set(
            paginas_validas
        )
    )


# ================================================================
# VALIDAR RUTA PDF
# ================================================================
def validar_ruta_pdf(
    ruta_pdf
):

    if not ruta_pdf:

        raise ValueError(
            "No se indicó un archivo PDF."
        )


    ruta_pdf = os.path.abspath(
        os.path.normpath(
            ruta_pdf
        )
    )


    if not os.path.isfile(
        ruta_pdf
    ):

        raise FileNotFoundError(
            f"No se encontró el archivo:\n{ruta_pdf}"
        )


    if not ruta_pdf.lower().endswith(
        ".pdf"
    ):

        raise ValueError(
            "El archivo seleccionado no es un PDF."
        )


    return ruta_pdf


# ================================================================
# PREPARAR CARPETA DE SALIDA
# ================================================================
def preparar_carpeta_salida(
    carpeta_salida
):

    if not carpeta_salida:

        raise ValueError(
            "No se indicó una carpeta de salida."
        )


    carpeta_salida = os.path.abspath(
        os.path.normpath(
            carpeta_salida
        )
    )


    os.makedirs(
        carpeta_salida,
        exist_ok=True
    )


    if not os.path.isdir(
        carpeta_salida
    ):

        raise ValueError(
            "La carpeta de salida no es válida."
        )


    return carpeta_salida


# ================================================================
# CREAR LECTOR PDF
# ================================================================
def crear_lector_pdf(
    archivo_pdf,
    ruta_pdf
):

    try:

        lector = PdfReader(
            archivo_pdf
        )


        if lector.is_encrypted:

            resultado = lector.decrypt(
                ""
            )


            if not resultado:

                raise ValueError(
                    "El PDF está protegido con contraseña:\n"
                    f"{ruta_pdf}"
                )


        cantidad_paginas = len(
            lector.pages
        )


        if cantidad_paginas <= 0:

            raise ValueError(
                "El PDF no contiene páginas."
            )


        return lector


    except ValueError:

        raise


    except Exception as error:

        raise ValueError(
            "No se pudo leer el archivo PDF:\n"
            f"{ruta_pdf}\n\n"
            f"{error}"
        ) from error


# ================================================================
# COMPROBAR CANCELACIÓN
# ================================================================
def comprobar_cancelacion_solicitada(
    comprobar_cancelacion
):

    if (
        comprobar_cancelacion is not None
        and comprobar_cancelacion()
    ):

        raise RuntimeError(
            "La operación fue cancelada."
        )


# ================================================================
# OBTENER PREFIJO PDF
# ================================================================
def obtener_prefijo_pdf(
    ruta_pdf
):

    prefijo = os.path.splitext(
        os.path.basename(
            ruta_pdf
        )
    )[
        0
    ]


    caracteres_invalidos = (
        '<>:"/\\|?*'
    )


    for caracter in caracteres_invalidos:

        prefijo = prefijo.replace(
            caracter,
            "_"
        )


    prefijo = prefijo.rstrip(
        ". "
    )


    if not prefijo:

        return "PDF"


    return prefijo