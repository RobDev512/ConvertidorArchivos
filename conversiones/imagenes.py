from PIL import Image

from funciones.formatos import (
    obtener_categoria_archivo,
    obtener_formato_archivo
)

from funciones.capacidades import detectar_imagemagick

from conversiones.imagemagick import (
    CODERS_SALIDA_IMAGEMAGICK,
    comprobar_conversion_imagemagick,
    convertir_con_imagemagick
)


# ----------------------------------- #
#       Formatos de Pillow            #
# ----------------------------------- #

FORMATOS_PILLOW = {
    "JPG": "JPEG",
    "PNG": "PNG",
    "WEBP": "WEBP",
    "BMP": "BMP",
    "TIFF": "TIFF",
    "GIF": "GIF",
    "ICO": "ICO"
}


# ----------------------------------- #
#      Entradas de Pillow             #
# ----------------------------------- #

FORMATOS_ENTRADA_PILLOW = {
    "JPG",
    "PNG",
    "WEBP",
    "BMP",
    "TIFF",
    "GIF",
    "ICO"
}


# ----------------------------------- #
#      Salidas de ImageMagick         #
# ----------------------------------- #

FORMATOS_SALIDA_IMAGEMAGICK = set(
    CODERS_SALIDA_IMAGEMAGICK.keys()
)


# ----------------------------------- #
#       Todas las salidas             #
# ----------------------------------- #

FORMATOS_SALIDA_IMAGEN = (
    set(FORMATOS_PILLOW.keys())
    | FORMATOS_SALIDA_IMAGEMAGICK
)


# ================================================================
# PREPARAR IMAGEN PARA JPG
# ================================================================
def preparar_imagen_jpg(imagen):

    # Comprobar transparencia normal
    if imagen.mode in ("RGBA", "LA"):

        fondo = Image.new(
            "RGB",
            imagen.size,
            (255, 255, 255)
        )

        canal_alpha = imagen.getchannel("A")

        fondo.paste(
            imagen,
            mask=canal_alpha
        )

        return fondo


    # ----------------------------------- #
    # Transparencia en imágenes indexadas #
    # ----------------------------------- #

    if (
        imagen.mode == "P"
        and "transparency" in imagen.info
    ):

        imagen_rgba = imagen.convert(
            "RGBA"
        )

        fondo = Image.new(
            "RGB",
            imagen.size,
            (255, 255, 255)
        )

        fondo.paste(
            imagen_rgba,
            mask=imagen_rgba.getchannel("A")
        )

        return fondo


    # ----------------------------------- #
    #      Convertir modos especiales     #
    # ----------------------------------- #

    if imagen.mode not in ("RGB", "L"):
        return imagen.convert("RGB")

    return imagen


# ================================================================
# CONVERTIR CON PILLOW
# ================================================================
def convertir_con_pillow(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    formato_destino = formato_destino.upper()

    # Obtener nombre interno de Pillow
    formato_pillow = FORMATOS_PILLOW[
        formato_destino
    ]

    # Abrir imagen
    with Image.open(ruta_origen) as imagen:

        # Por ahora utilizar el primer fotograma
        try:
            imagen.seek(0)

        except EOFError:
            pass

        # Crear una copia independiente
        imagen_convertida = imagen.copy()

        # Preparar JPG
        if formato_destino == "JPG":

            imagen_convertida = preparar_imagen_jpg(
                imagen_convertida
            )

        # Guardar resultado
        imagen_convertida.save(
            ruta_destino,
            format=formato_pillow
        )

    return ruta_destino


# ================================================================
# COMPROBAR CONVERSIÓN IMPLEMENTADA
# ================================================================
def conversion_imagen_implementada(
    ruta_origen,
    formato_destino
):

    # Comprobar que realmente sea una imagen
    if obtener_categoria_archivo(ruta_origen) != "imagen":
        return False

    formato_destino = formato_destino.upper()

    return formato_destino in FORMATOS_SALIDA_IMAGEN


# ================================================================
# OBTENER MOTOR DE IMAGEN
# ================================================================
def obtener_motor_imagen(
    ruta_origen,
    formato_destino
):

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()


    # ----------------------------------- #
    #          Preferir Pillow            #
    # ----------------------------------- #

    if (
        formato_origen in FORMATOS_ENTRADA_PILLOW
        and formato_destino in FORMATOS_PILLOW
    ):
        return "pillow"


    # ----------------------------------- #
    #       Utilizar ImageMagick          #
    # ----------------------------------- #

    if (
        formato_destino in FORMATOS_SALIDA_IMAGEMAGICK
        and detectar_imagemagick()
    ):
        return "imagemagick"


    return None


# ================================================================
# COMPROBAR CONVERSIÓN DISPONIBLE
# ================================================================
def comprobar_imagen_disponible(
    ruta_origen,
    formato_destino
):

    # Comprobar implementación
    if not conversion_imagen_implementada(
        ruta_origen,
        formato_destino
    ):

        return (
            False,
            f"La conversión a {formato_destino} todavía "
            f"no está implementada para imágenes."
        )


    # ----------------------------------- #
    #             Pillow                  #
    # ----------------------------------- #

    motor = obtener_motor_imagen(
        ruta_origen,
        formato_destino
    )

    if motor == "pillow":
        return True, None


    # ----------------------------------- #
    #          ImageMagick                #
    # ----------------------------------- #

    if formato_destino.upper() in FORMATOS_SALIDA_IMAGEMAGICK:

        return comprobar_conversion_imagemagick(
            ruta_origen,
            formato_destino
        )


    return (
        False,
        "No existe un motor disponible para realizar esta conversión."
    )


# ================================================================
# CONVERTIR IMAGEN
# ================================================================
def convertir_imagen(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    # Elegir motor
    motor = obtener_motor_imagen(
        ruta_origen,
        formato_destino
    )


    # ----------------------------------- #
    #             Pillow                  #
    # ----------------------------------- #

    if motor == "pillow":

        return convertir_con_pillow(
            ruta_origen,
            ruta_destino,
            formato_destino
        )


    # ----------------------------------- #
    #          ImageMagick                #
    # ----------------------------------- #

    if motor == "imagemagick":

        return convertir_con_imagemagick(
            ruta_origen,
            ruta_destino,
            formato_destino
        )


    raise RuntimeError(
        "No existe un motor disponible para realizar esta conversión."
    )