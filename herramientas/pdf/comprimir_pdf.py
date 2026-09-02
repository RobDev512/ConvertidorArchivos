import os
import shutil
import tempfile

from PIL import Image
from pypdf import (
    PdfReader,
    PdfWriter
)


# ----------------------------------- #
#       Niveles de compresión         #
# ----------------------------------- #

NIVELES_COMPRESION = {
    "sin_perdida": {
        "nombre": "Sin pérdida",
        "calidad_imagen": None,
        "dimension_maxima": None,
        "tamano_minimo_imagen": None
    },
    "equilibrada": {
        "nombre": "Equilibrada",
        "calidad_imagen": 82,
        "dimension_maxima": 2400,
        "tamano_minimo_imagen": 50 * 1024
    },
    "fuerte": {
        "nombre": "Fuerte",
        "calidad_imagen": 62,
        "dimension_maxima": 1600,
        "tamano_minimo_imagen": 30 * 1024
    }
}


# ================================================================
# VALIDAR PDF
# ================================================================
def _validar_pdf(
    ruta_pdf
):

    if not ruta_pdf:

        raise ValueError(
            "No se indicó ningún archivo PDF."
        )

    ruta_pdf = os.path.abspath(
        ruta_pdf
    )

    if not os.path.isfile(
        ruta_pdf
    ):

        raise FileNotFoundError(
            "El archivo PDF no existe."
        )

    if (
        os.path.splitext(
            ruta_pdf
        )[1].lower()
        != ".pdf"
    ):

        raise ValueError(
            "El archivo seleccionado no es un PDF."
        )

    return ruta_pdf


# ================================================================
# VALIDAR NIVEL
# ================================================================
def _validar_nivel(
    nivel
):

    nivel = str(
        nivel
    ).strip().lower()

    if nivel not in NIVELES_COMPRESION:

        raise ValueError(
            "El nivel de compresión no es válido."
        )

    return nivel


# ================================================================
# ABRIR PDF
# ================================================================
def _abrir_pdf(
    ruta_pdf
):

    lector = PdfReader(
        ruta_pdf
    )

    if lector.is_encrypted:

        lector.close()

        raise RuntimeError(
            "La compresión de PDFs protegidos o cifrados "
            "todavía no está disponible."
        )

    if len(
        lector.pages
    ) <= 0:

        lector.close()

        raise RuntimeError(
            "El PDF no contiene páginas."
        )

    return lector


# ================================================================
# COMPROBAR CANCELACIÓN
# ================================================================
def _esta_cancelado(
    comprobar_cancelacion
):

    if comprobar_cancelacion is None:

        return False

    try:

        return bool(
            comprobar_cancelacion()
        )

    except Exception:

        return False


# ================================================================
# INFORMAR PROGRESO
# ================================================================
def _informar_progreso(
    progreso,
    porcentaje,
    mensaje
):

    if progreso is None:

        return

    progreso(
        max(
            0,
            min(
                100,
                int(
                    porcentaje
                )
            )
        ),
        mensaje
    )


# ================================================================
# CREAR ARCHIVO TEMPORAL
# ================================================================
def _crear_ruta_temporal(
    ruta_salida
):

    carpeta = os.path.dirname(
        os.path.abspath(
            ruta_salida
        )
    )

    os.makedirs(
        carpeta,
        exist_ok=True
    )

    descriptor, ruta_temporal = tempfile.mkstemp(
        prefix=".comprimir_pdf_",
        suffix=".pdf",
        dir=carpeta
    )

    os.close(
        descriptor
    )

    return ruta_temporal


# ================================================================
# PREPARAR IMAGEN PARA RECOMPRESIÓN
# ================================================================
def _preparar_imagen(
    imagen,
    dimension_maxima
):

    if imagen is None:

        return None, False


    # ----------------------------------- #
    #     Evitar perder transparencia     #
    # ----------------------------------- #

    if imagen.mode in {
        "RGBA",
        "LA"
    }:

        return None, False


    if (
        imagen.mode == "P"
        and "transparency" in imagen.info
    ):

        return None, False


    # ----------------------------------- #
    #          Copia independiente        #
    # ----------------------------------- #

    imagen_salida = imagen.copy()


    # ----------------------------------- #
    #        Normalizar modo              #
    # ----------------------------------- #

    if imagen_salida.mode == "1":

        imagen_salida = imagen_salida.convert(
            "L"
        )

    elif imagen_salida.mode == "P":

        imagen_salida = imagen_salida.convert(
            "RGB"
        )

    elif imagen_salida.mode not in {
        "RGB",
        "L",
        "CMYK"
    }:

        imagen_salida = imagen_salida.convert(
            "RGB"
        )


    # ----------------------------------- #
    #        Reducir dimensiones          #
    # ----------------------------------- #

    redimensionada = False

    if (
        dimension_maxima is not None
        and max(
            imagen_salida.size
        ) > dimension_maxima
    ):

        imagen_salida.thumbnail(
            (
                dimension_maxima,
                dimension_maxima
            ),
            Image.Resampling.LANCZOS
        )

        redimensionada = True


    return (
        imagen_salida,
        redimensionada
    )


# ================================================================
# OBTENER IDENTIFICADOR DE IMAGEN
# ================================================================
def _obtener_identificador_imagen(
    imagen_pdf
):

    referencia = getattr(
        imagen_pdf,
        "indirect_reference",
        None
    )

    if referencia is None:

        return None

    return (
        getattr(
            referencia,
            "idnum",
            None
        ),
        getattr(
            referencia,
            "generation",
            None
        )
    )


# ================================================================
# RECOMPRIMIR IMÁGENES DE PÁGINA
# ================================================================
def _recomprimir_imagenes_pagina(
    pagina,
    configuracion,
    referencias_procesadas,
    comprobar_cancelacion=None
):

    calidad = configuracion[
        "calidad_imagen"
    ]

    dimension_maxima = configuracion[
        "dimension_maxima"
    ]

    tamano_minimo = configuracion[
        "tamano_minimo_imagen"
    ]


    if calidad is None:

        return (
            0,
            0,
            0
        )


    recomprimidas = 0
    redimensionadas = 0
    omitidas = 0


    try:

        imagenes = list(
            pagina.images
        )

    except Exception:

        return (
            0,
            0,
            0
        )


    for imagen_pdf in imagenes:

        if _esta_cancelado(
            comprobar_cancelacion
        ):

            break


        # ----------------------------------- #
        #       Evitar procesar repetida      #
        # ----------------------------------- #

        identificador = (
            _obtener_identificador_imagen(
                imagen_pdf
            )
        )


        if identificador is None:

            omitidas += 1

            continue


        if identificador in referencias_procesadas:

            continue


        referencias_procesadas.add(
            identificador
        )


        # ----------------------------------- #
        #        Ignorar imágenes pequeñas    #
        # ----------------------------------- #

        datos = getattr(
            imagen_pdf,
            "data",
            b""
        )


        if (
            tamano_minimo is not None
            and datos
            and len(
                datos
            ) < tamano_minimo
        ):

            omitidas += 1

            continue


        # ----------------------------------- #
        #        Obtener imagen Pillow        #
        # ----------------------------------- #

        imagen_original = getattr(
            imagen_pdf,
            "image",
            None
        )


        if imagen_original is None:

            omitidas += 1

            continue


        imagen_salida = None


        try:

            (
                imagen_salida,
                fue_redimensionada
            ) = _preparar_imagen(
                imagen_original,
                dimension_maxima
            )


            if imagen_salida is None:

                omitidas += 1

                continue


            # ----------------------------------- #
            #        Reemplazar en el PDF         #
            # ----------------------------------- #

            imagen_pdf.replace(
                imagen_salida,
                quality=calidad
            )


            recomprimidas += 1


            if fue_redimensionada:

                redimensionadas += 1


        except Exception:

            omitidas += 1


        finally:

            if imagen_salida is not None:

                try:

                    imagen_salida.close()

                except Exception:

                    pass


    return (
        recomprimidas,
        redimensionadas,
        omitidas
    )


# ================================================================
# CALCULAR PORCENTAJE DE REDUCCIÓN
# ================================================================
def _calcular_reduccion(
    tamano_original,
    tamano_final
):

    if tamano_original <= 0:

        return 0.0

    reduccion = (
        tamano_original
        - tamano_final
    )

    return (
        reduccion
        / tamano_original
        * 100
    )


# ================================================================
# COMPRIMIR PDF
# ================================================================
def comprimir_pdf(
    ruta_pdf,
    ruta_salida,
    nivel="equilibrada",
    progreso=None,
    comprobar_cancelacion=None
):

    ruta_pdf = _validar_pdf(
        ruta_pdf
    )

    nivel = _validar_nivel(
        nivel
    )

    configuracion = NIVELES_COMPRESION[
        nivel
    ]


    if not ruta_salida:

        raise ValueError(
            "No se indicó una ruta de salida."
        )


    ruta_salida = os.path.abspath(
        ruta_salida
    )


    if not ruta_salida.lower().endswith(
        ".pdf"
    ):

        ruta_salida += ".pdf"


    if (
        os.path.normcase(
            ruta_pdf
        )
        == os.path.normcase(
            ruta_salida
        )
    ):

        raise ValueError(
            "El archivo de salida debe ser diferente "
            "al PDF original."
        )


    tamano_original = os.path.getsize(
        ruta_pdf
    )


    ruta_temporal = _crear_ruta_temporal(
        ruta_salida
    )


    lector = None


    try:

        # ----------------------------------- #
        #            Abrir PDF                #
        # ----------------------------------- #

        _informar_progreso(
            progreso,
            2,
            "Analizando PDF..."
        )


        lector = _abrir_pdf(
            ruta_pdf
        )


        if _esta_cancelado(
            comprobar_cancelacion
        ):

            return None


        cantidad_paginas = len(
            lector.pages
        )


        # ----------------------------------- #
        #        Crear copia editable         #
        # ----------------------------------- #

        _informar_progreso(
            progreso,
            5,
            "Preparando documento..."
        )


        escritor = PdfWriter(
            clone_from=lector
        )


        referencias_procesadas = set()

        total_recomprimidas = 0
        total_redimensionadas = 0
        total_omitidas = 0

        paginas_stream_omitidas = 0


        # ----------------------------------- #
        #           Procesar páginas          #
        # ----------------------------------- #

        for indice, pagina in enumerate(
            escritor.pages
        ):

            if _esta_cancelado(
                comprobar_cancelacion
            ):

                return None


            # ----------------------------------- #
            #      Compresión sin pérdida         #
            # ----------------------------------- #

            try:

                pagina.compress_content_streams(
                    level=9
                )

            except Exception:

                paginas_stream_omitidas += 1


            # ----------------------------------- #
            #        Compresión de imágenes       #
            # ----------------------------------- #

            (
                recomprimidas,
                redimensionadas,
                omitidas
            ) = _recomprimir_imagenes_pagina(
                pagina,
                configuracion,
                referencias_procesadas,
                comprobar_cancelacion
            )


            total_recomprimidas += (
                recomprimidas
            )

            total_redimensionadas += (
                redimensionadas
            )

            total_omitidas += (
                omitidas
            )


            porcentaje = (
                5
                + round(
                    (
                        indice + 1
                    )
                    / cantidad_paginas
                    * 70
                )
            )


            _informar_progreso(
                progreso,
                porcentaje,
                (
                    f"Procesando página "
                    f"{indice + 1} de "
                    f"{cantidad_paginas}..."
                )
            )


        if _esta_cancelado(
            comprobar_cancelacion
        ):

            return None


        # ----------------------------------- #
        #       Eliminar duplicaciones        #
        # ----------------------------------- #

        _informar_progreso(
            progreso,
            80,
            "Optimizando estructura..."
        )


        optimizacion_objetos_aplicada = True


        try:

            escritor.compress_identical_objects(
                remove_duplicates=True,
                remove_unreferenced=True
            )

        except Exception:

            optimizacion_objetos_aplicada = False


        if _esta_cancelado(
            comprobar_cancelacion
        ):

            return None


        # ----------------------------------- #
        #              Escribir               #
        # ----------------------------------- #

        _informar_progreso(
            progreso,
            90,
            "Escribiendo PDF comprimido..."
        )


        with open(
            ruta_temporal,
            "wb"
        ) as archivo:

            escritor.write(
                archivo
            )


        if _esta_cancelado(
            comprobar_cancelacion
        ):

            return None


        # ----------------------------------- #
        #       Comprobar resultado           #
        # ----------------------------------- #

        _informar_progreso(
            progreso,
            96,
            "Comprobando resultado..."
        )


        tamano_candidato = os.path.getsize(
            ruta_temporal
        )


        se_conservo_original = False


        # ----------------------------------- #
        #       Nunca crear uno más grande    #
        # ----------------------------------- #

        if tamano_candidato >= tamano_original:

            shutil.copyfile(
                ruta_pdf,
                ruta_temporal
            )

            se_conservo_original = True


        tamano_final = os.path.getsize(
            ruta_temporal
        )


        # ----------------------------------- #
        #          Guardado atómico           #
        # ----------------------------------- #

        os.replace(
            ruta_temporal,
            ruta_salida
        )

        ruta_temporal = None


        porcentaje_reduccion = (
            _calcular_reduccion(
                tamano_original,
                tamano_final
            )
        )


        _informar_progreso(
            progreso,
            100,
            "Compresión terminada."
        )


        return {
            "ruta_salida": ruta_salida,
            "nivel": nivel,
            "nombre_nivel": configuracion[
                "nombre"
            ],
            "paginas": cantidad_paginas,
            "tamano_original": tamano_original,
            "tamano_final": tamano_final,
            "bytes_ahorrados": max(
                0,
                tamano_original
                - tamano_final
            ),
            "porcentaje_reduccion": max(
                0.0,
                porcentaje_reduccion
            ),
            "imagenes_recomprimidas": (
                total_recomprimidas
            ),
            "imagenes_redimensionadas": (
                total_redimensionadas
            ),
            "imagenes_omitidas": (
                total_omitidas
            ),
            "paginas_stream_omitidas": (
                paginas_stream_omitidas
            ),
            "optimizacion_objetos_aplicada": (
                optimizacion_objetos_aplicada
            ),
            "se_conservo_original": (
                se_conservo_original
            )
        }


    finally:

        if lector is not None:

            try:

                lector.close()

            except Exception:

                pass


        if (
            ruta_temporal
            and os.path.isfile(
                ruta_temporal
            )
        ):

            try:

                os.remove(
                    ruta_temporal
                )

            except OSError:

                pass