import os
import subprocess
import tempfile
from pathlib import Path

from PIL import (
    Image,
    ImageOps
)

from funciones.capacidades import (
    detectar_imagemagick
)

from conversiones.imagenes import (
    FORMATOS_ENTRADA_PILLOW,
    FORMATOS_PILLOW
)

from conversiones.imagemagick import (
    crear_opciones_subproceso,
    comprobar_archivo_imagemagick
)

from funciones.formatos import (
    obtener_formato_archivo
)


# ----------------------------------- #
#          Modos disponibles          #
# ----------------------------------- #

MODO_PORCENTAJE = "porcentaje"
MODO_ANCHO = "ancho"
MODO_ALTO = "alto"
MODO_ENCAJAR = "encajar"
MODO_EXACTO = "exacto"


MODOS_REDIMENSION = {
    MODO_PORCENTAJE,
    MODO_ANCHO,
    MODO_ALTO,
    MODO_ENCAJAR,
    MODO_EXACTO
}


# ----------------------------------- #
#        Filtros de redimension       #
# ----------------------------------- #

FILTROS_PILLOW = {
    "alta": Image.Resampling.LANCZOS,
    "media": Image.Resampling.BICUBIC,
    "rapida": Image.Resampling.BILINEAR
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
# COMPROBAR CANCELACIÓN
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

    texto = resultado.stdout.strip()

    partes = texto.split()

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
# OBTENER DIMENSIONES DE IMAGEN
# ================================================================
def obtener_dimensiones_imagen(
    ruta
):

    ruta = comprobar_archivo_imagen(
        ruta
    )

    dimensiones = obtener_dimensiones_pillow(
        ruta
    )

    if dimensiones is not None:
        return dimensiones

    dimensiones = obtener_dimensiones_imagemagick(
        ruta
    )

    if dimensiones is not None:
        return dimensiones

    raise RuntimeError(
        "No fue posible obtener las dimensiones "
        "de la imagen."
    )


# ================================================================
# VALIDAR ENTERO POSITIVO
# ================================================================
def validar_entero_positivo(
    valor,
    nombre
):

    try:
        valor = int(
            valor
        )

    except (
        TypeError,
        ValueError
    ):
        raise ValueError(
            f"{nombre} debe ser un número entero."
        )

    if valor <= 0:
        raise ValueError(
            f"{nombre} debe ser mayor que 0."
        )

    return valor


# ================================================================
# VALIDAR PORCENTAJE
# ================================================================
def validar_porcentaje(
    porcentaje
):

    try:
        porcentaje = float(
            porcentaje
        )

    except (
        TypeError,
        ValueError
    ):
        raise ValueError(
            "El porcentaje debe ser un número."
        )

    if porcentaje <= 0:
        raise ValueError(
            "El porcentaje debe ser mayor que 0."
        )

    return porcentaje


# ================================================================
# CALCULAR DIMENSIONES POR PORCENTAJE
# ================================================================
def calcular_porcentaje(
    ancho_original,
    alto_original,
    porcentaje
):

    porcentaje = validar_porcentaje(
        porcentaje
    )

    escala = porcentaje / 100.0

    ancho = max(
        1,
        round(
            ancho_original
            * escala
        )
    )

    alto = max(
        1,
        round(
            alto_original
            * escala
        )
    )

    return (
        ancho,
        alto
    )


# ================================================================
# CALCULAR DIMENSIONES POR ANCHO
# ================================================================
def calcular_por_ancho(
    ancho_original,
    alto_original,
    ancho
):

    ancho = validar_entero_positivo(
        ancho,
        "El ancho"
    )

    escala = (
        ancho
        / ancho_original
    )

    alto = max(
        1,
        round(
            alto_original
            * escala
        )
    )

    return (
        ancho,
        alto
    )


# ================================================================
# CALCULAR DIMENSIONES POR ALTO
# ================================================================
def calcular_por_alto(
    ancho_original,
    alto_original,
    alto
):

    alto = validar_entero_positivo(
        alto,
        "El alto"
    )

    escala = (
        alto
        / alto_original
    )

    ancho = max(
        1,
        round(
            ancho_original
            * escala
        )
    )

    return (
        ancho,
        alto
    )


# ================================================================
# CALCULAR DIMENSIONES PARA ENCAJAR
# ================================================================
def calcular_para_encajar(
    ancho_original,
    alto_original,
    ancho_maximo,
    alto_maximo
):

    ancho_maximo = validar_entero_positivo(
        ancho_maximo,
        "El ancho máximo"
    )

    alto_maximo = validar_entero_positivo(
        alto_maximo,
        "El alto máximo"
    )

    escala_ancho = (
        ancho_maximo
        / ancho_original
    )

    escala_alto = (
        alto_maximo
        / alto_original
    )

    escala = min(
        escala_ancho,
        escala_alto
    )

    ancho = max(
        1,
        round(
            ancho_original
            * escala
        )
    )

    alto = max(
        1,
        round(
            alto_original
            * escala
        )
    )

    return (
        ancho,
        alto
    )


# ================================================================
# CALCULAR DIMENSIONES EXACTAS
# ================================================================
def calcular_exacto(
    ancho,
    alto
):

    ancho = validar_entero_positivo(
        ancho,
        "El ancho"
    )

    alto = validar_entero_positivo(
        alto,
        "El alto"
    )

    return (
        ancho,
        alto
    )


# ================================================================
# CALCULAR DIMENSIONES DE DESTINO
# ================================================================
def calcular_dimensiones_destino(
    ancho_original,
    alto_original,
    modo,
    ancho=None,
    alto=None,
    porcentaje=None,
    evitar_ampliar=False
):

    modo = str(
        modo
    ).strip().lower()

    if modo not in MODOS_REDIMENSION:
        raise ValueError(
            f"Modo de redimensionado desconocido: {modo}"
        )

    if modo == MODO_PORCENTAJE:
        dimensiones = calcular_porcentaje(
            ancho_original,
            alto_original,
            porcentaje
        )

    elif modo == MODO_ANCHO:
        dimensiones = calcular_por_ancho(
            ancho_original,
            alto_original,
            ancho
        )

    elif modo == MODO_ALTO:
        dimensiones = calcular_por_alto(
            ancho_original,
            alto_original,
            alto
        )

    elif modo == MODO_ENCAJAR:
        dimensiones = calcular_para_encajar(
            ancho_original,
            alto_original,
            ancho,
            alto
        )

    else:
        dimensiones = calcular_exacto(
            ancho,
            alto
        )

    ancho_destino, alto_destino = dimensiones

    if evitar_ampliar:
        if modo == MODO_EXACTO:

            ancho_destino = min(
                ancho_destino,
                ancho_original
            )

            alto_destino = min(
                alto_destino,
                alto_original
            )

        elif (
            ancho_destino > ancho_original
            or alto_destino > alto_original
        ):
            ancho_destino = ancho_original
            alto_destino = alto_original

    return (
        max(
            1,
            ancho_destino
        ),
        max(
            1,
            alto_destino
        )
    )


# ================================================================
# OBTENER MOTOR PARA REDIMENSIONAR
# ================================================================
def obtener_motor_redimension(
    ruta
):

    formato = obtener_formato_archivo(
        str(
            ruta
        )
    )

    if formato in FORMATOS_ENTRADA_PILLOW:
        return "pillow"

    ruta_imagemagick = detectar_imagemagick()

    if ruta_imagemagick:
        legible, _ = comprobar_archivo_imagemagick(
            str(
                ruta
            )
        )

        if legible:
            return "imagemagick"

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
        prefix=".redimension_",
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
# PREPARAR IMAGEN PARA JPG
# ================================================================
def preparar_para_jpg(
    imagen
):

    if imagen.mode in {
        "RGBA",
        "LA"
    }:

        fondo = Image.new(
            "RGB",
            imagen.size,
            (
                255,
                255,
                255
            )
        )

        canal_alpha = imagen.getchannel(
            "A"
        )

        fondo.paste(
            imagen,
            mask=canal_alpha
        )

        return fondo

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
            (
                255,
                255,
                255
            )
        )

        fondo.paste(
            imagen_rgba,
            mask=imagen_rgba.getchannel(
                "A"
            )
        )

        return fondo

    if imagen.mode not in {
        "RGB",
        "L"
    }:
        return imagen.convert(
            "RGB"
        )

    return imagen


# ================================================================
# REDIMENSIONAR CON PILLOW
# ================================================================
def redimensionar_con_pillow(
    ruta_origen,
    ruta_destino,
    ancho,
    alto,
    calidad="alta"
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

    filtro = FILTROS_PILLOW.get(
        calidad,
        Image.Resampling.LANCZOS
    )

    with Image.open(
        ruta_origen
    ) as imagen:

        try:
            imagen.seek(
                0
            )

        except EOFError:
            pass

        imagen = ImageOps.exif_transpose(
            imagen
        )

        perfil_icc = imagen.info.get(
            "icc_profile"
        )

        datos_exif = imagen.info.get(
            "exif"
        )

        imagen_redimensionada = imagen.resize(
            (
                ancho,
                alto
            ),
            resample=filtro
        )

        if formato == "JPG":
            imagen_redimensionada = preparar_para_jpg(
                imagen_redimensionada
            )

        opciones = {}

        if perfil_icc:
            opciones[
                "icc_profile"
            ] = perfil_icc

        if datos_exif:
            opciones[
                "exif"
            ] = datos_exif

        if formato == "JPG":
            opciones.update(
                {
                    "quality": 95,
                    "optimize": True
                }
            )

        elif formato == "PNG":
            opciones.update(
                {
                    "optimize": True
                }
            )

        elif formato == "WEBP":
            opciones.update(
                {
                    "quality": 95,
                    "method": 6
                }
            )

        imagen_redimensionada.save(
            ruta_destino,
            format=formato_pillow,
            **opciones
        )


# ================================================================
# REDIMENSIONAR CON IMAGEMAGICK
# ================================================================
def redimensionar_con_imagemagick(
    ruta_origen,
    ruta_destino,
    ancho,
    alto
):

    ruta_imagemagick = detectar_imagemagick()

    if not ruta_imagemagick:
        raise RuntimeError(
            "ImageMagick no está disponible."
        )

    comando = [
        ruta_imagemagick,
        str(
            ruta_origen
        ),
        "-auto-orient",
        "-resize",
        f"{ancho}x{alto}!"
    ]

    formato = obtener_formato_archivo(
        str(
            ruta_destino
        )
    )

    if formato == "JPG":
        comando.extend(
            [
                "-background",
                "white",
                "-alpha",
                "remove",
                "-alpha",
                "off",
                "-quality",
                "95"
            ]
        )

    comando.append(
        str(
            ruta_destino
        )
    )

    resultado = subprocess.run(
        comando,
        **crear_opciones_subproceso()
    )

    if resultado.returncode != 0:
        detalle = (
            resultado.stderr.strip()
            or resultado.stdout.strip()
            or "ImageMagick no pudo redimensionar la imagen."
        )

        raise RuntimeError(
            "ImageMagick no pudo redimensionar "
            f"la imagen.\n\n{detalle}"
        )

    if not ruta_destino.is_file():
        raise RuntimeError(
            "ImageMagick terminó sin generar "
            "el archivo esperado."
        )


# ================================================================
# REDIMENSIONAR UNA IMAGEN
# ================================================================
def redimensionar_imagen(
    ruta_origen,
    ruta_destino,
    modo=MODO_PORCENTAJE,
    ancho=None,
    alto=None,
    porcentaje=100,
    evitar_ampliar=False,
    calidad="alta",
    progreso=None,
    comprobar_cancelacion_callback=None
):

    ruta_origen = comprobar_archivo_imagen(
        ruta_origen
    )

    ruta_destino = normalizar_ruta(
        ruta_destino
    )

    comprobar_cancelacion(
        comprobar_cancelacion_callback
    )

    informar_progreso(
        progreso,
        5,
        "Analizando imagen..."
    )

    ancho_original, alto_original = (
        obtener_dimensiones_imagen(
            ruta_origen
        )
    )

    ancho_destino, alto_destino = (
        calcular_dimensiones_destino(
            ancho_original,
            alto_original,
            modo,
            ancho=ancho,
            alto=alto,
            porcentaje=porcentaje,
            evitar_ampliar=evitar_ampliar
        )
    )

    comprobar_cancelacion(
        comprobar_cancelacion_callback
    )

    informar_progreso(
        progreso,
        20,
        (
            f"Redimensionando de "
            f"{ancho_original} × {alto_original} a "
            f"{ancho_destino} × {alto_destino}..."
        )
    )

    motor = obtener_motor_redimension(
        ruta_origen
    )

    if motor is None:
        raise RuntimeError(
            "No existe un motor disponible para "
            "redimensionar esta imagen."
        )

    ruta_temporal = crear_archivo_temporal(
        ruta_destino
    )

    try:
        if motor == "pillow":
            redimensionar_con_pillow(
                ruta_origen,
                ruta_temporal,
                ancho_destino,
                alto_destino,
                calidad=calidad
            )

        else:
            redimensionar_con_imagemagick(
                ruta_origen,
                ruta_temporal,
                ancho_destino,
                alto_destino
            )

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        informar_progreso(
            progreso,
            90,
            "Guardando imagen..."
        )

        if not ruta_temporal.is_file():
            raise RuntimeError(
                "La operación terminó sin generar "
                "una imagen."
            )

        if ruta_temporal.stat().st_size <= 0:
            raise RuntimeError(
                "La operación generó una imagen vacía."
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

    informar_progreso(
        progreso,
        100,
        "Imagen redimensionada correctamente."
    )

    return {
        "ruta": str(
            ruta_destino
        ),
        "ancho_original": ancho_original,
        "alto_original": alto_original,
        "ancho": ancho_destino,
        "alto": alto_destino,
        "motor": motor
    }


# ================================================================
# GENERAR RUTA DE SALIDA
# ================================================================
def generar_ruta_salida(
    ruta_origen,
    carpeta_salida,
    sufijo="_redimensionada",
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

    nombre = (
        ruta_origen.stem
        + sufijo
        + ruta_origen.suffix
    )

    ruta_destino = (
        carpeta_salida
        / nombre
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
# REDIMENSIONAR VARIAS IMÁGENES
# ================================================================
def redimensionar_imagenes(
    rutas_origen,
    carpeta_salida,
    modo=MODO_PORCENTAJE,
    ancho=None,
    alto=None,
    porcentaje=100,
    evitar_ampliar=False,
    calidad="alta",
    sobrescribir=False,
    sufijo="_redimensionada",
    progreso=None,
    comprobar_cancelacion_callback=None
):

    rutas = [
        comprobar_archivo_imagen(
            ruta
        )
        for ruta in rutas_origen
    ]

    if not rutas:
        raise ValueError(
            "No se recibieron imágenes para redimensionar."
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

        def progreso_imagen(
            porcentaje,
            estado
        ):

            informar_progreso(
                progreso,
                (
                    inicio
                    + porcentaje
                    / 100
                    * rango
                ),
                (
                    f"Imagen {indice} de {total}: "
                    f"{estado}"
                )
            )

        resultado = redimensionar_imagen(
            ruta_origen,
            ruta_destino,
            modo=modo,
            ancho=ancho,
            alto=alto,
            porcentaje=porcentaje,
            evitar_ampliar=evitar_ampliar,
            calidad=calidad,
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
            f"{total} imagen"
            + (
                " redimensionada correctamente."
                if total == 1
                else "es redimensionadas correctamente."
            )
        )
    )

    return resultados