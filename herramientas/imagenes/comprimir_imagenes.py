import os
import shutil
import subprocess
import tempfile
import time

from pathlib import Path

from PIL import (
    Image,
    ImageOps,
    ImageSequence
)

from funciones.capacidades import (
    detectar_imagemagick
)

from funciones.formatos import (
    obtener_formato_archivo
)

from conversiones.imagenes import (
    FORMATOS_ENTRADA_PILLOW,
    FORMATOS_PILLOW
)

from conversiones.imagemagick import (
    CODERS_SALIDA_IMAGEMAGICK,
    comprobar_archivo_imagemagick,
    comprobar_formato_salida_imagemagick,
    crear_opciones_subproceso
)


# ----------------------------------- #
#      Formatos de compresion         #
# ----------------------------------- #

FORMATOS_COMPRESION = {
    "JPG",
    "PNG",
    "WEBP",
    "BMP",
    "TIFF",
    "GIF",
    "ICO",
    "APNG",
    "AVIF",
    "HEIC",
    "HEIF",
    "JXL",
    "JP2",
    "J2K",
    "JXR",
    "QOI",
    "TGA",
    "PCX",
    "PNM",
    "PBM",
    "PGM",
    "PPM",
    "PAM",
    "HDR",
    "EXR",
    "DPX",
    "DDS"
}


# ----------------------------------- #
#    Formatos con calidad ajustable   #
# ----------------------------------- #

FORMATOS_CALIDAD = {
    "JPG",
    "WEBP",
    "AVIF",
    "HEIC",
    "HEIF",
    "JXL",
    "JP2",
    "J2K",
    "JXR"
}


# ----------------------------------- #
#      Formatos preferidos Pillow     #
# ----------------------------------- #

FORMATOS_PILLOW_COMPRESION = {
    "JPG",
    "PNG",
    "WEBP",
    "BMP",
    "TIFF",
    "GIF"
}


# ================================================================
# INFORMAR PROGRESO
# ================================================================
def informar_progreso(
    callback,
    porcentaje,
    estado
):

    if callback is None:
        return

    porcentaje = max(
        0,
        min(
            100,
            int(
                round(
                    porcentaje
                )
            )
        )
    )

    callback(
        porcentaje,
        estado
    )


# ================================================================
# COMPROBAR CANCELACION
# ================================================================
def comprobar_cancelacion(
    callback
):

    if (
        callback is not None
        and callback()
    ):

        raise RuntimeError(
            "Operación cancelada por el usuario."
        )


# ================================================================
# NORMALIZAR RUTA
# ================================================================
def normalizar_ruta(
    ruta
):

    return Path(
        ruta
    ).expanduser().resolve()


# ================================================================
# VALIDAR CALIDAD
# ================================================================
def validar_calidad(
    calidad
):

    try:

        calidad = int(
            calidad
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "La calidad debe ser un número entero."
        )

    if not 1 <= calidad <= 100:

        raise ValueError(
            "La calidad debe estar entre 1 y 100."
        )

    return calidad


# ================================================================
# COMPROBAR ARCHIVO
# ================================================================
def comprobar_archivo_imagen(
    ruta
):

    ruta = normalizar_ruta(
        ruta
    )

    if not ruta.is_file():

        raise FileNotFoundError(
            f"No existe la imagen:\n{ruta}"
        )

    formato = obtener_formato_archivo(
        str(
            ruta
        )
    )

    if formato not in FORMATOS_COMPRESION:

        raise ValueError(
            "Este formato todavía no está habilitado "
            "para la herramienta de compresión."
        )

    return ruta


# ================================================================
# OBTENER DIMENSIONES CON PILLOW
# ================================================================
def obtener_dimensiones_pillow(
    ruta
):

    try:

        with Image.open(
            ruta
        ) as imagen:

            ancho, alto = imagen.size

            return (
                int(
                    ancho
                ),
                int(
                    alto
                )
            )

    except Exception:

        return None


# ================================================================
# OBTENER DIMENSIONES CON IMAGEMAGICK
# ================================================================
def obtener_dimensiones_imagemagick(
    ruta
):

    ruta_imagemagick = detectar_imagemagick()

    if not ruta_imagemagick:

        return None

    resultado = subprocess.run(
        [
            ruta_imagemagick,
            "identify",
            "-ping",
            "-format",
            "%w %h",
            str(
                ruta
            ) + "[0]"
        ],
        **crear_opciones_subproceso()
    )

    if resultado.returncode != 0:

        return None

    partes = (
        resultado.stdout
        .strip()
        .split()
    )

    if len(
        partes
    ) < 2:

        return None

    try:

        ancho = int(
            partes[0]
        )

        alto = int(
            partes[1]
        )

    except ValueError:

        return None

    if (
        ancho <= 0
        or alto <= 0
    ):

        return None

    return (
        ancho,
        alto
    )


# ================================================================
# OBTENER INFORMACION DE IMAGEN
# ================================================================
def obtener_informacion_imagen(
    ruta
):

    ruta = comprobar_archivo_imagen(
        ruta
    )

    formato = obtener_formato_archivo(
        str(
            ruta
        )
    )

    dimensiones = obtener_dimensiones_pillow(
        ruta
    )

    if dimensiones is None:

        dimensiones = obtener_dimensiones_imagemagick(
            ruta
        )

    if dimensiones is None:

        raise RuntimeError(
            "No fue posible obtener las dimensiones "
            "de la imagen."
        )

    return {
        "ruta": str(
            ruta
        ),
        "formato": formato,
        "ancho": dimensiones[0],
        "alto": dimensiones[1],
        "tamano": ruta.stat().st_size,
        "calidad_ajustable": (
            formato
            in FORMATOS_CALIDAD
        )
    }


# ================================================================
# OBTENER MOTOR DE COMPRESION
# ================================================================
def obtener_motor_compresion(
    ruta
):

    ruta = comprobar_archivo_imagen(
        ruta
    )

    formato = obtener_formato_archivo(
        str(
            ruta
        )
    )


    # ----------------------------------- #
    #          Preferir Pillow            #
    # ----------------------------------- #

    if (
        formato
        in FORMATOS_PILLOW_COMPRESION
        and formato
        in FORMATOS_ENTRADA_PILLOW
    ):

        try:

            with Image.open(
                ruta
            ):
                pass

            return "pillow"

        except Exception:

            pass


    # ----------------------------------- #
    #       Utilizar ImageMagick          #
    # ----------------------------------- #

    ruta_imagemagick = detectar_imagemagick()

    coder = CODERS_SALIDA_IMAGEMAGICK.get(
        formato
    )

    if (
        ruta_imagemagick
        and coder
        and comprobar_formato_salida_imagemagick(
            formato
        )
    ):

        legible, _ = comprobar_archivo_imagemagick(
            str(
                ruta
            )
        )

        if legible:

            return "imagemagick"


    # ----------------------------------- #
    #          Respaldo Pillow            #
    # ----------------------------------- #

    if (
        formato
        in FORMATOS_PILLOW
        and formato
        in FORMATOS_ENTRADA_PILLOW
    ):

        try:

            with Image.open(
                ruta
            ):
                pass

            return "pillow"

        except Exception:

            pass

    return None


# ================================================================
# CREAR ARCHIVO TEMPORAL
# ================================================================
def crear_archivo_temporal(
    ruta_destino
):

    ruta_destino = normalizar_ruta(
        ruta_destino
    )

    ruta_destino.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    descriptor, ruta_temporal = tempfile.mkstemp(
        prefix=".compresion_imagen_",
        suffix=ruta_destino.suffix,
        dir=str(
            ruta_destino.parent
        )
    )

    os.close(
        descriptor
    )

    os.remove(
        ruta_temporal
    )

    return Path(
        ruta_temporal
    )


# ================================================================
# RECOLECTAR METADATOS PILLOW
# ================================================================
def recolectar_metadatos_pillow(
    imagen,
    eliminar_metadatos
):

    if eliminar_metadatos:

        return {}

    opciones = {}

    perfil_icc = imagen.info.get(
        "icc_profile"
    )

    if perfil_icc:

        opciones[
            "icc_profile"
        ] = perfil_icc

    datos_exif = imagen.info.get(
        "exif"
    )

    if datos_exif:

        opciones[
            "exif"
        ] = datos_exif

    return opciones


# ================================================================
# COMPRIMIR GIF CON PILLOW
# ================================================================
def comprimir_gif_con_pillow(
    imagen,
    ruta_destino
):

    fotogramas = [
        fotograma.copy()
        for fotograma
        in ImageSequence.Iterator(
            imagen
        )
    ]

    if not fotogramas:

        raise RuntimeError(
            "El GIF no contiene fotogramas válidos."
        )

    opciones = {
        "save_all": True,
        "append_images": fotogramas[1:],
        "optimize": True,
        "loop": imagen.info.get(
            "loop",
            0
        )
    }

    duracion = imagen.info.get(
        "duration"
    )

    if duracion is not None:

        opciones[
            "duration"
        ] = duracion

    transparencia = imagen.info.get(
        "transparency"
    )

    if transparencia is not None:

        opciones[
            "transparency"
        ] = transparencia

    fotogramas[0].save(
        ruta_destino,
        format="GIF",
        **opciones
    )


# ================================================================
# COMPRIMIR CON PILLOW
# ================================================================
def comprimir_con_pillow(
    ruta_origen,
    ruta_destino,
    calidad,
    eliminar_metadatos
):

    formato = obtener_formato_archivo(
        str(
            ruta_origen
        )
    )

    formato_pillow = FORMATOS_PILLOW.get(
        formato
    )

    if not formato_pillow:

        raise RuntimeError(
            "Pillow no tiene configurado este formato."
        )

    with Image.open(
        ruta_origen
    ) as imagen:

        if formato == "GIF":

            comprimir_gif_con_pillow(
                imagen,
                ruta_destino
            )

            return

        try:

            imagen.seek(
                0
            )

        except EOFError:

            pass


        # ----------------------------------- #
        #    Orientacion al quitar EXIF       #
        # ----------------------------------- #

        if eliminar_metadatos:

            imagen_base = ImageOps.exif_transpose(
                imagen
            )

        else:

            imagen_base = imagen

        imagen_salida = imagen_base.copy()

        opciones = recolectar_metadatos_pillow(
            imagen,
            eliminar_metadatos
        )


        # ----------------------------------- #
        #               JPG                   #
        # ----------------------------------- #

        if formato == "JPG":

            if imagen_salida.mode not in {
                "RGB",
                "L"
            }:

                imagen_salida = imagen_salida.convert(
                    "RGB"
                )

            opciones.update(
                {
                    "quality": calidad,
                    "optimize": True,
                    "progressive": True
                }
            )


        # ----------------------------------- #
        #               PNG                   #
        # ----------------------------------- #

        elif formato == "PNG":

            opciones.update(
                {
                    "optimize": True,
                    "compress_level": 9
                }
            )


        # ----------------------------------- #
        #              WEBP                   #
        # ----------------------------------- #

        elif formato == "WEBP":

            opciones.update(
                {
                    "quality": calidad,
                    "method": 6
                }
            )


        # ----------------------------------- #
        #              TIFF                   #
        # ----------------------------------- #

        elif formato == "TIFF":

            opciones[
                "compression"
            ] = "tiff_adobe_deflate"

        imagen_salida.save(
            ruta_destino,
            format=formato_pillow,
            **opciones
        )


# ================================================================
# EJECUTAR IMAGEMAGICK CANCELABLE
# ================================================================
def ejecutar_imagemagick_cancelable(
    comando,
    comprobar_cancelacion_callback=None
):

    opciones = crear_opciones_subproceso()

    proceso = subprocess.Popen(
        comando,
        **opciones
    )

    try:

        while proceso.poll() is None:

            if (
                comprobar_cancelacion_callback
                is not None
                and comprobar_cancelacion_callback()
            ):

                proceso.terminate()

                try:

                    proceso.wait(
                        timeout=2
                    )

                except subprocess.TimeoutExpired:

                    proceso.kill()

                    proceso.wait()

                raise RuntimeError(
                    "Operación cancelada por el usuario."
                )

            time.sleep(
                0.08
            )

        stdout, stderr = proceso.communicate()

    except Exception:

        if proceso.poll() is None:

            proceso.kill()

            proceso.wait()

        raise

    return (
        proceso.returncode,
        stdout,
        stderr
    )


# ================================================================
# COMPRIMIR CON IMAGEMAGICK
# ================================================================
def comprimir_con_imagemagick(
    ruta_origen,
    ruta_destino,
    calidad,
    eliminar_metadatos,
    comprobar_cancelacion_callback=None
):

    ruta_imagemagick = detectar_imagemagick()

    if not ruta_imagemagick:

        raise RuntimeError(
            "ImageMagick no está disponible."
        )

    formato = obtener_formato_archivo(
        str(
            ruta_origen
        )
    )

    coder = CODERS_SALIDA_IMAGEMAGICK.get(
        formato
    )

    if not coder:

        raise RuntimeError(
            "ImageMagick no tiene configurado "
            "este formato de salida."
        )

    comando = [
        ruta_imagemagick,
        str(
            ruta_origen
        )
    ]


    # ----------------------------------- #
    #          Eliminar metadatos         #
    # ----------------------------------- #

    if eliminar_metadatos:

        comando.extend(
            [
                "-auto-orient",
                "-strip"
            ]
        )


    # ----------------------------------- #
    #          Calidad ajustable          #
    # ----------------------------------- #

    if formato in FORMATOS_CALIDAD:

        comando.extend(
            [
                "-quality",
                str(
                    calidad
                )
            ]
        )


    # ----------------------------------- #
    #          Opciones por formato       #
    # ----------------------------------- #

    if formato == "JPG":

        comando.extend(
            [
                "-interlace",
                "Plane"
            ]
        )

    elif formato == "PNG":

        comando.extend(
            [
                "-define",
                "png:compression-level=9",
                "-define",
                "png:compression-strategy=1"
            ]
        )

    elif formato == "WEBP":

        comando.extend(
            [
                "-define",
                "webp:method=6"
            ]
        )

    elif formato == "GIF":

        comando.extend(
            [
                "-layers",
                "Optimize"
            ]
        )

    elif formato == "TIFF":

        comando.extend(
            [
                "-compress",
                "Zip"
            ]
        )

    comando.append(
        f"{coder}:{ruta_destino}"
    )

    (
        codigo,
        stdout,
        stderr
    ) = ejecutar_imagemagick_cancelable(
        comando,
        comprobar_cancelacion_callback
    )

    if codigo != 0:

        detalle = (
            stderr.strip()
            or stdout.strip()
            or "ImageMagick no pudo comprimir la imagen."
        )

        raise RuntimeError(
            "ImageMagick no pudo comprimir "
            f"la imagen.\n\n{detalle}"
        )

    if not ruta_destino.is_file():

        raise RuntimeError(
            "ImageMagick terminó sin generar "
            "el archivo esperado."
        )


# ================================================================
# GENERAR RUTA DE SALIDA
# ================================================================
def generar_ruta_salida(
    ruta_origen,
    carpeta_salida,
    sufijo="_comprimida",
    sobrescribir=False
):

    ruta_origen = normalizar_ruta(
        ruta_origen
    )

    carpeta_salida = normalizar_ruta(
        carpeta_salida
    )

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_destino = (
        carpeta_salida
        / (
            ruta_origen.stem
            + sufijo
            + ruta_origen.suffix
        )
    )

    if (
        sobrescribir
        or not ruta_destino.exists()
    ):

        return ruta_destino

    contador = 2

    while True:

        ruta_destino = (
            carpeta_salida
            / (
                ruta_origen.stem
                + sufijo
                + f"_{contador}"
                + ruta_origen.suffix
            )
        )

        if not ruta_destino.exists():

            return ruta_destino

        contador += 1


# ================================================================
# COMPRIMIR UNA IMAGEN
# ================================================================
def comprimir_imagen(
    ruta_origen,
    ruta_destino,
    calidad=85,
    eliminar_metadatos=False,
    evitar_archivo_mayor=True,
    progreso=None,
    comprobar_cancelacion_callback=None
):

    ruta_origen = comprobar_archivo_imagen(
        ruta_origen
    )

    ruta_destino = normalizar_ruta(
        ruta_destino
    )

    calidad = validar_calidad(
        calidad
    )

    comprobar_cancelacion(
        comprobar_cancelacion_callback
    )

    informacion = obtener_informacion_imagen(
        ruta_origen
    )

    tamano_original = informacion[
        "tamano"
    ]

    informar_progreso(
        progreso,
        10,
        "Analizando imagen..."
    )

    motor = obtener_motor_compresion(
        ruta_origen
    )

    if motor is None:

        raise RuntimeError(
            "No existe un motor disponible para "
            "comprimir esta imagen."
        )

    ruta_temporal = crear_archivo_temporal(
        ruta_destino
    )

    recompresion_descartada = False

    try:

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        informar_progreso(
            progreso,
            30,
            "Comprimiendo imagen..."
        )

        if motor == "pillow":

            comprimir_con_pillow(
                ruta_origen,
                ruta_temporal,
                calidad,
                eliminar_metadatos
            )

        else:

            comprimir_con_imagemagick(
                ruta_origen,
                ruta_temporal,
                calidad,
                eliminar_metadatos,
                comprobar_cancelacion_callback
            )

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        informar_progreso(
            progreso,
            85,
            "Comprobando resultado..."
        )

        if not ruta_temporal.is_file():

            raise RuntimeError(
                "La operación terminó sin generar "
                "una imagen."
            )

        tamano_comprimido = (
            ruta_temporal.stat().st_size
        )

        if tamano_comprimido <= 0:

            raise RuntimeError(
                "La operación generó un archivo vacío."
            )


        # ----------------------------------- #
        #      Evitar un resultado mayor      #
        # ----------------------------------- #

        if (
            evitar_archivo_mayor
            and not eliminar_metadatos
            and tamano_comprimido
            >= tamano_original
        ):

            ruta_temporal.unlink()

            shutil.copy2(
                ruta_origen,
                ruta_temporal
            )

            tamano_comprimido = (
                ruta_temporal.stat().st_size
            )

            recompresion_descartada = True

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        ruta_destino.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        os.replace(
            ruta_temporal,
            ruta_destino
        )

    except Exception:

        if ruta_temporal.exists():

            try:

                ruta_temporal.unlink()

            except OSError:

                pass

        raise

    reduccion_bytes = max(
        0,
        tamano_original
        - tamano_comprimido
    )

    reduccion_porcentaje = (
        reduccion_bytes
        / tamano_original
        * 100
        if tamano_original > 0
        else 0.0
    )

    informar_progreso(
        progreso,
        100,
        "Imagen comprimida correctamente."
    )

    return {
        "ruta": str(
            ruta_destino
        ),
        "ruta_origen": str(
            ruta_origen
        ),
        "formato": informacion[
            "formato"
        ],
        "ancho": informacion[
            "ancho"
        ],
        "alto": informacion[
            "alto"
        ],
        "tamano_original": tamano_original,
        "tamano_final": tamano_comprimido,
        "reduccion_bytes": reduccion_bytes,
        "reduccion_porcentaje": reduccion_porcentaje,
        "motor": motor,
        "recompresion_descartada": (
            recompresion_descartada
        )
    }


# ================================================================
# COMPRIMIR VARIAS IMAGENES
# ================================================================
def comprimir_imagenes(
    rutas_origen,
    carpeta_salida,
    calidad=85,
    eliminar_metadatos=False,
    evitar_archivo_mayor=True,
    sobrescribir=False,
    sufijo="_comprimida",
    progreso=None,
    comprobar_cancelacion_callback=None
):

    rutas = [
        comprobar_archivo_imagen(
            ruta
        )
        for ruta
        in rutas_origen
    ]

    if not rutas:

        raise ValueError(
            "No se recibieron imágenes para comprimir."
        )

    calidad = validar_calidad(
        calidad
    )

    total = len(
        rutas
    )

    resultados = []

    for indice, ruta_origen in enumerate(
        rutas,
        start=1
    ):

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        ruta_destino = generar_ruta_salida(
            ruta_origen,
            carpeta_salida,
            sufijo=sufijo,
            sobrescribir=sobrescribir
        )

        inicio = (
            (indice - 1)
            / total
            * 100
        )

        fin = (
            indice
            / total
            * 100
        )

        rango = (
            fin
            - inicio
        )


        # ----------------------------------- #
        #        Progreso de esta imagen      #
        # ----------------------------------- #

        def progreso_imagen(
            porcentaje,
            estado,
            indice_actual=indice,
            inicio_actual=inicio,
            rango_actual=rango
        ):

            informar_progreso(
                progreso,
                (
                    inicio_actual
                    + porcentaje
                    / 100
                    * rango_actual
                ),
                (
                    f"Imagen {indice_actual} de "
                    f"{total}: {estado}"
                )
            )

        resultado = comprimir_imagen(
            ruta_origen,
            ruta_destino,
            calidad=calidad,
            eliminar_metadatos=eliminar_metadatos,
            evitar_archivo_mayor=evitar_archivo_mayor,
            progreso=progreso_imagen,
            comprobar_cancelacion_callback=(
                comprobar_cancelacion_callback
            )
        )

        resultados.append(
            resultado
        )

    informar_progreso(
        progreso,
        100,
        (
            f"{total} imagen comprimida correctamente."
            if total == 1
            else (
                f"{total} imágenes comprimidas "
                "correctamente."
            )
        )
    )

    return resultados