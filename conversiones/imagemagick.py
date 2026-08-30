import os
import subprocess

from functools import lru_cache

from funciones.capacidades import detectar_imagemagick


# ----------------------------------- #
#      Formatos de ImageMagick        #
# ----------------------------------- #

CODERS_SALIDA_IMAGEMAGICK = {
    "JPG": "JPEG",
    "PNG": "PNG",
    "APNG": "APNG",
    "WEBP": "WEBP",
    "AVIF": "AVIF",
    "HEIC": "HEIC",
    "HEIF": "HEIC",
    "JXL": "JXL",
    "GIF": "GIF",
    "BMP": "BMP",
    "TIFF": "TIFF",
    "ICO": "ICO",
    "JP2": "JP2",
    "J2K": "J2K",
    "JXR": "JXR",
    "QOI": "QOI",
    "TGA": "TGA",
    "PCX": "PCX",
    "PNM": "PNM",
    "PBM": "PBM",
    "PGM": "PGM",
    "PPM": "PPM",
    "PAM": "PAM",
    "HDR": "HDR",
    "EXR": "EXR",
    "DPX": "DPX",
    "DDS": "DDS",
    "PSD": "PSD",
    "EPS": "EPS",
    "PDF": "PDF"
}


# ================================================================
# CREAR OPCIONES DE SUBPROCESO
# ================================================================
def crear_opciones_subproceso():

    opciones = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace"
    }

    # Evitar que aparezca una consola adicional en Windows
    if os.name == "nt":
        opciones["creationflags"] = subprocess.CREATE_NO_WINDOW

    return opciones


# ================================================================
# CONSULTAR FORMATOS DE IMAGEMAGICK
# ================================================================
@lru_cache(maxsize=4)
def consultar_formatos_imagemagick(ruta_imagemagick):

    # Ejecutar consulta oficial de formatos
    resultado = subprocess.run(
        [
            ruta_imagemagick,
            "identify",
            "-list",
            "format"
        ],
        **crear_opciones_subproceso()
    )

    if resultado.returncode != 0:

        detalle = (
            resultado.stderr.strip()
            or resultado.stdout.strip()
            or "ImageMagick no pudo informar sus formatos."
        )

        raise RuntimeError(
            f"No fue posible consultar los formatos "
            f"de ImageMagick.\n\n{detalle}"
        )


    # ----------------------------------- #
    #          Analizar resultado          #
    # ----------------------------------- #

    formatos = {}

    for linea in resultado.stdout.splitlines():

        partes = linea.split()

        # Las líneas de formato normalmente contienen:
        # formato, módulo, modo y descripción
        if len(partes) < 3:
            continue

        formato = partes[0].rstrip("*").upper()
        modo = partes[2].lower()

        # Ignorar encabezados y líneas que no sean formatos
        if "r" not in modo and "w" not in modo:
            continue

        formatos[formato] = {
            "lectura": "r" in modo,
            "escritura": "w" in modo
        }

    return formatos


# ================================================================
# OBTENER FORMATOS DE IMAGEMAGICK
# ================================================================
def obtener_formatos_imagemagick():

    ruta_imagemagick = detectar_imagemagick()

    if not ruta_imagemagick:
        return {}

    return consultar_formatos_imagemagick(
        ruta_imagemagick
    )


# ================================================================
# COMPROBAR FORMATO DE SALIDA
# ================================================================
def comprobar_formato_salida_imagemagick(formato_destino):

    formato_destino = formato_destino.upper()

    # Obtener coder correspondiente
    coder = CODERS_SALIDA_IMAGEMAGICK.get(
        formato_destino
    )

    if not coder:
        return False

    # Consultar formatos reales de esta instalación
    formatos = obtener_formatos_imagemagick()

    informacion = formatos.get(
        coder
    )

    if not informacion:
        return False

    return informacion["escritura"]


# ================================================================
# COMPROBAR ARCHIVO DE ENTRADA
# ================================================================
def comprobar_archivo_imagemagick(ruta_origen):

    ruta_imagemagick = detectar_imagemagick()

    if not ruta_imagemagick:
        return False, "ImageMagick no está disponible."

    # Pedir únicamente información de la imagen
    resultado = subprocess.run(
        [
            ruta_imagemagick,
            "identify",
            "-ping",
            ruta_origen
        ],
        **crear_opciones_subproceso()
    )

    if resultado.returncode == 0:
        return True, None

    detalle = (
        resultado.stderr.strip()
        or resultado.stdout.strip()
        or "ImageMagick no pudo leer el archivo."
    )

    return False, detalle


# ================================================================
# COMPROBAR CONVERSIÓN DE IMAGEMAGICK
# ================================================================
def comprobar_conversion_imagemagick(
    ruta_origen,
    formato_destino
):

    # Comprobar instalación
    if not detectar_imagemagick():

        return (
            False,
            "Esta conversión necesita ImageMagick, "
            "pero no se encontró disponible."
        )

    # Comprobar formato de salida
    if not comprobar_formato_salida_imagemagick(
        formato_destino
    ):

        return (
            False,
            f"La instalación actual de ImageMagick no puede "
            f"escribir archivos {formato_destino}."
        )

    # Comprobar que realmente pueda leer el origen
    archivo_legible, detalle = comprobar_archivo_imagemagick(
        ruta_origen
    )

    if not archivo_legible:

        return (
            False,
            "ImageMagick está instalado, pero no pudo leer "
            f"este archivo.\n\n{detalle}"
        )

    return True, None


# ================================================================
# CONVERTIR CON IMAGEMAGICK
# ================================================================
def convertir_con_imagemagick(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    # Buscar motor
    ruta_imagemagick = detectar_imagemagick()

    if not ruta_imagemagick:

        raise RuntimeError(
            "ImageMagick no está disponible."
        )

    formato_destino = formato_destino.upper()

    # Obtener coder
    coder = CODERS_SALIDA_IMAGEMAGICK.get(
        formato_destino
    )

    if not coder:

        raise ValueError(
            f"ImageMagick todavía no tiene configurada "
            f"la salida {formato_destino} en la aplicación."
        )


    # ----------------------------------- #
    #          Preparar comando           #
    # ----------------------------------- #

    # Por ahora mantenemos el comportamiento actual
    # de utilizar el primer fotograma de imágenes animadas
    ruta_entrada = ruta_origen + "[0]"

    # Indicar explícitamente el formato de salida
    ruta_salida = f"{coder}:{ruta_destino}"

    comando = [
        ruta_imagemagick,
        ruta_entrada,
        "-auto-orient"
    ]


    # ----------------------------------- #
    #       Preparación especial JPG      #
    # ----------------------------------- #

    # JPG no admite transparencia
    if formato_destino == "JPG":

        comando.extend(
            [
                "-background",
                "white",
                "-alpha",
                "remove",
                "-alpha",
                "off"
            ]
        )


    # ----------------------------------- #
    #          Añadir destino             #
    # ----------------------------------- #

    comando.append(
        ruta_salida
    )


    # ----------------------------------- #
    #        Ejecutar conversión          #
    # ----------------------------------- #

    resultado = subprocess.run(
        comando,
        **crear_opciones_subproceso()
    )

    if resultado.returncode != 0:

        detalle = (
            resultado.stderr.strip()
            or resultado.stdout.strip()
            or "ImageMagick no pudo completar la conversión."
        )

        raise RuntimeError(
            f"ImageMagick no pudo convertir el archivo.\n\n"
            f"{detalle}"
        )


    # ----------------------------------- #
    #       Comprobar archivo final       #
    # ----------------------------------- #

    if not os.path.isfile(ruta_destino):

        raise RuntimeError(
            "ImageMagick terminó sin generar el archivo esperado."
        )

    return ruta_destino