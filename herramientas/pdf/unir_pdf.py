import os
import uuid

from pypdf import PdfReader, PdfWriter


# ================================================================
# UNIR PDF
# ================================================================
def unir_pdfs(
    archivos,
    ruta_salida,
    progreso=None,
    comprobar_cancelacion=None
):

    # ----------------------------------- #
    #       Validar archivos              #
    # ----------------------------------- #

    archivos = validar_archivos_pdf(
        archivos
    )

    paginas = []


    # ----------------------------------- #
    #    Obtener todas las páginas        #
    # ----------------------------------- #

    for ruta_pdf in archivos:

        lector = abrir_pdf(
            ruta_pdf
        )

        for indice_pagina in range(
            len(
                lector.pages
            )
        ):

            paginas.append(
                (
                    ruta_pdf,
                    indice_pagina
                )
            )


    # ----------------------------------- #
    #        Unir páginas                 #
    # ----------------------------------- #

    return unir_paginas_pdf(
        paginas,
        ruta_salida,
        progreso,
        comprobar_cancelacion
    )


# ================================================================
# UNIR PÁGINAS PDF
# ================================================================
def unir_paginas_pdf(
    paginas,
    ruta_salida,
    progreso=None,
    comprobar_cancelacion=None
):

    paginas = validar_paginas(
        paginas
    )

    archivos_origen = list(
        dict.fromkeys(
            ruta_pdf
            for ruta_pdf, _ in paginas
        )
    )

    ruta_salida = preparar_ruta_salida(
        ruta_salida,
        archivos_origen
    )


    # ----------------------------------- #
    #        Archivo temporal             #
    # ----------------------------------- #

    carpeta_salida = os.path.dirname(
        ruta_salida
    )

    nombre_temporal = (
        f".union_pdf_{uuid.uuid4().hex}.pdf"
    )

    ruta_temporal = os.path.join(
        carpeta_salida,
        nombre_temporal
    )


    # ----------------------------------- #
    #          Lectores abiertos          #
    # ----------------------------------- #

    lectores = {}


    # ----------------------------------- #
    #             Escritor                #
    # ----------------------------------- #

    escritor = PdfWriter()

    cantidad_paginas = len(
        paginas
    )


    try:

        for posicion, datos_pagina in enumerate(
            paginas,
            start=1
        ):

            ruta_pdf, indice_pagina = datos_pagina


            # ----------------------------------- #
            #          Cancelación                #
            # ----------------------------------- #

            if (
                comprobar_cancelacion is not None
                and comprobar_cancelacion()
            ):

                raise RuntimeError(
                    "La unión de PDFs fue cancelada."
                )


            # ----------------------------------- #
            #         Obtener lector              #
            # ----------------------------------- #

            if ruta_pdf not in lectores:

                lectores[
                    ruta_pdf
                ] = abrir_pdf(
                    ruta_pdf
                )


            lector = lectores[
                ruta_pdf
            ]


            # ----------------------------------- #
            #        Comprobar página             #
            # ----------------------------------- #

            if indice_pagina < 0:

                raise ValueError(
                    "El índice de página no puede ser negativo."
                )


            if indice_pagina >= len(
                lector.pages
            ):

                raise ValueError(
                    "La página indicada no existe:\n"
                    f"{ruta_pdf}\n\n"
                    f"Página: {indice_pagina + 1}"
                )


            # ----------------------------------- #
            #           Añadir página             #
            # ----------------------------------- #

            escritor.add_page(
                lector.pages[
                    indice_pagina
                ]
            )


            # ----------------------------------- #
            #            Progreso                 #
            # ----------------------------------- #

            if progreso is not None:

                progreso(
                    posicion,
                    cantidad_paginas,
                    ruta_pdf
                )


        # ----------------------------------- #
        #          Guardar resultado          #
        # ----------------------------------- #

        with open(
            ruta_temporal,
            "wb"
        ) as archivo_salida:

            escritor.write(
                archivo_salida
            )


        # ----------------------------------- #
        #      Reemplazo seguro final         #
        # ----------------------------------- #

        os.replace(
            ruta_temporal,
            ruta_salida
        )


    except Exception:

        if os.path.isfile(
            ruta_temporal
        ):

            try:

                os.remove(
                    ruta_temporal
                )

            except OSError:

                pass

        raise


    finally:

        try:

            escritor.close()

        except Exception:

            pass


    return ruta_salida


# ================================================================
# VALIDAR ARCHIVOS PDF
# ================================================================
def validar_archivos_pdf(
    archivos
):

    if not archivos:

        raise ValueError(
            "No se seleccionaron archivos PDF."
        )


    archivos_validos = []


    for ruta_archivo in archivos:

        ruta_archivo = normalizar_ruta_pdf(
            ruta_archivo
        )


        # ----------------------------------- #
        #       Comprobar existencia          #
        # ----------------------------------- #

        if not os.path.isfile(
            ruta_archivo
        ):

            raise FileNotFoundError(
                f"No se encontró el archivo:\n{ruta_archivo}"
            )


        # ----------------------------------- #
        #         Comprobar extensión         #
        # ----------------------------------- #

        if not ruta_archivo.lower().endswith(
            ".pdf"
        ):

            raise ValueError(
                "Solo se pueden unir archivos PDF:\n"
                f"{ruta_archivo}"
            )


        # ----------------------------------- #
        #           Comprobar PDF             #
        # ----------------------------------- #

        abrir_pdf(
            ruta_archivo
        )


        archivos_validos.append(
            ruta_archivo
        )


    # ----------------------------------- #
    #        Cantidad mínima              #
    # ----------------------------------- #

    if len(
        archivos_validos
    ) < 2:

        raise ValueError(
            "Selecciona al menos dos archivos PDF."
        )


    return archivos_validos


# ================================================================
# VALIDAR PÁGINAS
# ================================================================
def validar_paginas(
    paginas
):

    if not paginas:

        raise ValueError(
            "No hay páginas para unir."
        )


    paginas_validas = []


    for datos_pagina in paginas:

        if (
            not isinstance(
                datos_pagina,
                (tuple, list)
            )
            or len(
                datos_pagina
            ) != 2
        ):

            raise ValueError(
                "La información de una página no es válida."
            )


        ruta_pdf = normalizar_ruta_pdf(
            datos_pagina[
                0
            ]
        )

        indice_pagina = datos_pagina[
            1
        ]


        # ----------------------------------- #
        #          Validar archivo            #
        # ----------------------------------- #

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
                "Solo se pueden utilizar páginas de archivos PDF:\n"
                f"{ruta_pdf}"
            )


        # ----------------------------------- #
        #        Validar índice               #
        # ----------------------------------- #

        if not isinstance(
            indice_pagina,
            int
        ):

            raise ValueError(
                "El número de página no es válido."
            )


        paginas_validas.append(
            (
                ruta_pdf,
                indice_pagina
            )
        )


    return paginas_validas


# ================================================================
# PREPARAR RUTA DE SALIDA
# ================================================================
def preparar_ruta_salida(
    ruta_salida,
    archivos
):

    if not ruta_salida:

        raise ValueError(
            "No se indicó una ruta de salida."
        )


    ruta_salida = os.path.abspath(
        os.path.normpath(
            ruta_salida
        )
    )


    # ----------------------------------- #
    #           Extensión PDF             #
    # ----------------------------------- #

    if not ruta_salida.lower().endswith(
        ".pdf"
    ):

        ruta_salida += ".pdf"


    # ----------------------------------- #
    #         Crear carpeta               #
    # ----------------------------------- #

    carpeta_salida = os.path.dirname(
        ruta_salida
    )


    if not carpeta_salida:

        raise ValueError(
            "La ruta de salida no es válida."
        )


    os.makedirs(
        carpeta_salida,
        exist_ok=True
    )


    # ----------------------------------- #
    #      Evitar sobrescribir entrada    #
    # ----------------------------------- #

    ruta_salida_normalizada = os.path.normcase(
        ruta_salida
    )


    for ruta_archivo in archivos:

        if os.path.normcase(
            ruta_archivo
        ) == ruta_salida_normalizada:

            raise ValueError(
                "El archivo de salida no puede ser uno "
                "de los PDFs originales."
            )


    return ruta_salida


# ================================================================
# ABRIR PDF
# ================================================================
def abrir_pdf(
    ruta_pdf
):

    try:

        lector = PdfReader(
            ruta_pdf
        )


        # ----------------------------------- #
        #           PDF protegido             #
        # ----------------------------------- #

        if lector.is_encrypted:

            resultado = lector.decrypt(
                ""
            )

            if not resultado:

                raise ValueError(
                    "El PDF está protegido con contraseña:\n"
                    f"{ruta_pdf}"
                )


        # ----------------------------------- #
        #        Forzar lectura               #
        # ----------------------------------- #

        len(
            lector.pages
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
# NORMALIZAR RUTA PDF
# ================================================================
def normalizar_ruta_pdf(
    ruta_pdf
):

    return os.path.abspath(
        os.path.normpath(
            ruta_pdf
        )
    )