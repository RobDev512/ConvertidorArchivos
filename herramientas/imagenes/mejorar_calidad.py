import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import warnings

from collections import deque
from contextlib import contextmanager
from pathlib import Path

from PIL import (
    Image,
    ImageFilter,
    ImageOps
)


# ================================================================
# MODOS DE MEJORA
# ================================================================

MODO_IA = "ia"

MODO_CLASICO = "clasico"


# ================================================================
# TIPOS DE IMAGEN
# ================================================================

TIPO_AUTOMATICO = "automatico"

TIPO_FOTOGRAFIA = "fotografia"

TIPO_ILUSTRACION = "ilustracion"


# ================================================================
# MODELOS DE REAL-ESRGAN
# ================================================================

MODELO_GENERAL = "realesrgan-x4plus"

MODELO_ILUSTRACION = "realesrgan-x4plus-anime"


# ================================================================
# ESCALAS
# ================================================================

ESCALAS_VALIDAS = {
    2,
    3,
    4
}


# ================================================================
# LIMITES DE SEGURIDAD
# ================================================================

LIMITE_PIXELES_SALIDA_CLASICA = 220_000_000

LIMITE_PIXELES_SALIDA_IA = 220_000_000

LIMITE_PIXELES_TEMPORAL_IA = 256_000_000

LIMITE_LADO_SALIDA = 20_000

LIMITE_LADO_TEMPORAL_IA = 20_000


# ================================================================
# FORMATOS DE SALIDA
# ================================================================

FORMATOS_SALIDA = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".bmp": "BMP",
    ".tif": "TIFF",
    ".tiff": "TIFF"
}


# ================================================================
# PROGRESO DE REAL-ESRGAN
# ================================================================

PATRON_PROGRESO_REALESRGAN = re.compile(
    r"(?<!\d)(\d{1,3}(?:\.\d+)?)%"
)

MAXIMO_LINEAS_REGISTRO_REALESRGAN = 160


# ================================================================
# CANCELACION
# ================================================================
class MejoraCalidadCancelada(
    RuntimeError
):
    pass


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

        raise MejoraCalidadCancelada(
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
# OBTENER CARPETA DE LA APLICACION
# ================================================================
def obtener_carpeta_aplicacion():

    if getattr(
        sys,
        "frozen",
        False
    ):

        return Path(
            sys.executable
        ).resolve().parent

    return Path(
        __file__
    ).resolve().parents[2]


# ================================================================
# OBTENER CARPETA DE REAL-ESRGAN
# ================================================================
def obtener_carpeta_realesrgan():

    return (
        obtener_carpeta_aplicacion()
        / "motores"
        / "realesrgan"
    )


# ================================================================
# OBTENER CARPETA DE MODELOS
# ================================================================
def obtener_carpeta_modelos_realesrgan():

    return (
        obtener_carpeta_realesrgan()
        / "models"
    )


# ================================================================
# DETECTAR REAL-ESRGAN
# ================================================================
def detectar_realesrgan():

    carpeta = obtener_carpeta_realesrgan()

    candidatos = [
        carpeta
        / "realesrgan-ncnn-vulkan.exe",

        carpeta
        / "realesrgan-ncnn-vulkan"
    ]

    for ruta in candidatos:

        if ruta.is_file():

            return str(
                ruta
            )

    for nombre in (
        "realesrgan-ncnn-vulkan.exe",
        "realesrgan-ncnn-vulkan"
    ):

        ruta = shutil.which(
            nombre
        )

        if ruta:

            return ruta

    return None


# ================================================================
# SELECCIONAR MODELO
# ================================================================
def seleccionar_modelo(
    tipo_imagen
):

    if tipo_imagen == TIPO_ILUSTRACION:

        return MODELO_ILUSTRACION

    return MODELO_GENERAL


# ================================================================
# COMPROBAR MODELO
# ================================================================
def comprobar_modelo_realesrgan(
    modelo
):

    carpeta = (
        obtener_carpeta_modelos_realesrgan()
    )

    ruta_param = (
        carpeta
        / f"{modelo}.param"
    )

    ruta_bin = (
        carpeta
        / f"{modelo}.bin"
    )

    return (
        ruta_param.is_file()
        and ruta_bin.is_file()
    )


# ================================================================
# COMPROBAR MOTOR DE IA
# ================================================================
def comprobar_motor_ia(
    tipo_imagen=TIPO_AUTOMATICO
):

    ejecutable = detectar_realesrgan()

    if not ejecutable:

        return {
            "disponible": False,
            "ejecutable": None,
            "modelo": None,
            "mensaje": (
                "No se encontró Real-ESRGAN."
            )
        }

    modelo = seleccionar_modelo(
        tipo_imagen
    )

    if not comprobar_modelo_realesrgan(
        modelo
    ):

        return {
            "disponible": False,
            "ejecutable": ejecutable,
            "modelo": modelo,
            "mensaje": (
                f"Faltan los archivos del modelo "
                f"{modelo}."
            )
        }

    return {
        "disponible": True,
        "ejecutable": ejecutable,
        "modelo": modelo,
        "mensaje": (
            "Real-ESRGAN disponible."
        )
    }


# ================================================================
# VALIDAR PARAMETROS
# ================================================================
def validar_parametros(
    modo,
    tipo_imagen,
    escala
):

    if modo not in {
        MODO_IA,
        MODO_CLASICO
    }:

        raise ValueError(
            "El método de mejora no es válido."
        )

    if tipo_imagen not in {
        TIPO_AUTOMATICO,
        TIPO_FOTOGRAFIA,
        TIPO_ILUSTRACION
    }:

        raise ValueError(
            "El tipo de imagen no es válido."
        )

    try:

        escala = int(
            escala
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "La escala debe ser un número entero."
        )

    if escala not in ESCALAS_VALIDAS:

        raise ValueError(
            "La escala debe ser 2×, 3× o 4×."
        )

    return escala


# ================================================================
# CALCULAR DIMENSIONES DE SALIDA
# ================================================================
def calcular_dimensiones_salida(
    ancho,
    alto,
    escala
):

    escala = int(
        escala
    )

    return (
        max(
            1,
            int(
                ancho
            )
            * escala
        ),
        max(
            1,
            int(
                alto
            )
            * escala
        )
    )


# ================================================================
# CALCULAR MEGAPIXELES
# ================================================================
def calcular_megapixeles(
    ancho,
    alto
):

    return (
        max(
            1,
            int(
                ancho
            )
        )
        * max(
            1,
            int(
                alto
            )
        )
        / 1_000_000.0
    )



# ================================================================
# FORMATEAR ENTERO
# ================================================================
def formatear_entero(
    valor
):

    return (
        f"{int(valor):,}"
        .replace(",", ".")
    )


# ================================================================
# FORMATEAR MEGAPIXELES
# ================================================================
def formatear_megapixeles(
    pixeles
):

    return (
        f"{pixeles / 1_000_000.0:.1f} MP"
    )


# ================================================================
# OBTENER ESCALA INTERNA DE IA
# ================================================================
def obtener_escala_interna_ia(
    escala
):

    _ = int(
        escala
    )

    return 4


# ================================================================
# VALIDAR LIMITES DE MEJORA
# ================================================================
def validar_limites_mejora(
    ancho,
    alto,
    escala,
    modo
):

    ancho = max(
        1,
        int(
            ancho
        )
    )

    alto = max(
        1,
        int(
            alto
        )
    )

    escala = int(
        escala
    )

    ancho_salida, alto_salida = (
        calcular_dimensiones_salida(
            ancho,
            alto,
            escala
        )
    )

    pixeles_salida = (
        ancho_salida
        * alto_salida
    )

    if max(
        ancho_salida,
        alto_salida
    ) > LIMITE_LADO_SALIDA:

        raise RuntimeError(
            "La imagen resultante sería demasiado grande. "
            f"El límite configurado es de {formatear_entero(LIMITE_LADO_SALIDA)} px "
            "por lado. "
            f"Con {escala}×, esta imagen generaría "
            f"{formatear_entero(ancho_salida)} × {formatear_entero(alto_salida)} px."
        )

    if modo == MODO_CLASICO:

        if pixeles_salida > LIMITE_PIXELES_SALIDA_CLASICA:

            raise RuntimeError(
                "La imagen es demasiado grande para la mejora clásica con la escala elegida. "
                f"Se generarían {formatear_entero(ancho_salida)} × {formatear_entero(alto_salida)} px "
                f"({formatear_megapixeles(pixeles_salida)}), y el límite configurado es "
                f"{formatear_megapixeles(LIMITE_PIXELES_SALIDA_CLASICA)}."
            )

        return

    if pixeles_salida > LIMITE_PIXELES_SALIDA_IA:

        raise RuntimeError(
            "La imagen final sería demasiado grande para la mejora con IA usando la escala elegida. "
            f"Se generarían {formatear_entero(ancho_salida)} × {formatear_entero(alto_salida)} px "
            f"({formatear_megapixeles(pixeles_salida)}), y el límite configurado es "
            f"{formatear_megapixeles(LIMITE_PIXELES_SALIDA_IA)}."
        )

    escala_interna = obtener_escala_interna_ia(
        escala
    )

    ancho_temporal, alto_temporal = (
        calcular_dimensiones_salida(
            ancho,
            alto,
            escala_interna
        )
    )

    pixeles_temporales = (
        ancho_temporal
        * alto_temporal
    )

    if max(
        ancho_temporal,
        alto_temporal
    ) > LIMITE_LADO_TEMPORAL_IA:

        raise RuntimeError(
            "La mejora con IA no puede continuar porque la imagen temporal interna sería demasiado grande. "
            f"Esta herramienta usa 4× interno para procesar 2×, 3× y 4×, y en este caso produciría "
            f"{formatear_entero(ancho_temporal)} × {formatear_entero(alto_temporal)} px. "
            f"El límite configurado es de {formatear_entero(LIMITE_LADO_TEMPORAL_IA)} px por lado."
        )

    if pixeles_temporales > LIMITE_PIXELES_TEMPORAL_IA:

        raise RuntimeError(
            "La mejora con IA no puede continuar porque la imagen temporal interna sería demasiado grande. "
            f"Esta herramienta usa 4× interno para procesar 2×, 3× y 4×. "
            f"En este caso se producirían {formatear_entero(ancho_temporal)} × {formatear_entero(alto_temporal)} px "
            f"({formatear_megapixeles(pixeles_temporales)}), y el límite configurado es "
            f"{formatear_megapixeles(LIMITE_PIXELES_TEMPORAL_IA)}."
        )


# ================================================================
# SELECCIONAR TAMANO DE MOSAICO
# ================================================================
def seleccionar_tamano_tile(
    ancho,
    alto,
    escala
):

    # Real-ESRGAN NCNN/Vulkan ya incluye selección automática
    # del tamaño de mosaico según la memoria disponible de la GPU.
    #
    # Forzar mosaicos pequeños puede provocar diferencias visibles
    # entre bloques y, en algunos equipos, resultados con fragmentos
    # ampliados o desplazados. Por calidad y compatibilidad dejamos
    # siempre que el propio motor elija el valor adecuado (-t 0).
    #
    # Conservamos los parámetros en la función porque forman parte
    # de la API interna y pueden ser útiles para futuras estrategias
    # de compatibilidad.

    _ = (
        ancho,
        alto,
        escala
    )

    return 0


# ================================================================
# OBTENER INFORMACION DE IMAGEN
# ================================================================
def obtener_informacion_imagen(
    ruta
):

    ruta = normalizar_ruta(
        ruta
    )

    if not ruta.is_file():

        raise FileNotFoundError(
            f"No existe la imagen:\n{ruta}"
        )

    try:

        with Image.open(
            ruta
        ) as imagen:

            try:

                imagen.seek(
                    0
                )

            except EOFError:

                pass

            formato = (
                imagen.format
                or ruta.suffix.lstrip(
                    "."
                ).upper()
            )

            imagen = ImageOps.exif_transpose(
                imagen
            )

            ancho, alto = imagen.size

            tiene_alpha = (
                "A" in imagen.getbands()
                or (
                    imagen.mode == "P"
                    and "transparency"
                    in imagen.info
                )
            )

    except Image.DecompressionBombError as error:

        raise ValueError(
            "La imagen de entrada es demasiado grande para abrirla "
            "de forma segura. Reduce sus dimensiones antes de usar "
            "esta herramienta."
        ) from error

    except Exception as error:

        raise ValueError(
            "No fue posible abrir la imagen."
        ) from error

    return {
        "ruta": str(
            ruta
        ),
        "ancho": int(
            ancho
        ),
        "alto": int(
            alto
        ),
        "tamano": ruta.stat().st_size,
        "formato": formato,
        "tiene_alpha": bool(
            tiene_alpha
        )
    }


# ================================================================
# EXTRAER METADATOS
# ================================================================
def extraer_metadatos(
    imagen
):

    metadatos = {}

    icc_profile = imagen.info.get(
        "icc_profile"
    )

    if icc_profile:

        metadatos[
            "icc_profile"
        ] = icc_profile

    try:

        exif = imagen.getexif()

        if exif:

            # La imagen se rota físicamente con exif_transpose.
            # No debemos volver a guardar la orientación antigua.
            if 274 in exif:

                del exif[
                    274
                ]

            exif_bytes = exif.tobytes()

            if exif_bytes:

                metadatos[
                    "exif"
                ] = exif_bytes

    except Exception:

        pass

    return metadatos


# ================================================================
# ABRIR IMAGEN NORMALIZADA
# ================================================================
def abrir_imagen_normalizada(
    ruta
):

    try:

        imagen_origen = Image.open(
            ruta
        )

    except Image.DecompressionBombError as error:

        raise ValueError(
            "La imagen de entrada es demasiado grande para abrirla "
            "de forma segura. Reduce sus dimensiones antes de usar "
            "esta herramienta."
        ) from error

    except Exception as error:

        raise ValueError(
            "No fue posible abrir la imagen de entrada."
        ) from error

    try:

        try:

            imagen_origen.seek(
                0
            )

        except EOFError:

            pass

        metadatos = extraer_metadatos(
            imagen_origen
        )

        imagen = ImageOps.exif_transpose(
            imagen_origen
        ).convert(
            "RGBA"
        )

    except Exception as error:

        imagen_origen.close()

        raise ValueError(
            "No fue posible preparar la imagen de entrada."
        ) from error

    imagen_origen.close()

    return (
        imagen,
        metadatos
    )


# ================================================================
# PREPARAR RGB
# ================================================================
def preparar_rgb(
    imagen
):

    if imagen.mode == "RGB":

        return imagen.copy()

    if imagen.mode != "RGBA":

        imagen_rgba = imagen.convert(
            "RGBA"
        )

    else:

        imagen_rgba = imagen

    fondo = Image.new(
        "RGB",
        imagen_rgba.size,
        "white"
    )

    fondo.paste(
        imagen_rgba,
        (
            0,
            0
        ),
        imagen_rgba
    )

    if imagen_rgba is not imagen:

        imagen_rgba.close()

    return fondo


# ================================================================
# MEJORA CLASICA
# ================================================================
def mejorar_clasico(
    imagen,
    escala,
    conservar_transparencia=True
):

    alpha = None

    if (
        conservar_transparencia
        and "A" in imagen.getbands()
    ):

        alpha = imagen.getchannel(
            "A"
        )

    rgb = preparar_rgb(
        imagen
    )

    ancho_destino = max(
        1,
        imagen.width
        * escala
    )

    alto_destino = max(
        1,
        imagen.height
        * escala
    )

    try:

        rgb_redimensionado = rgb.resize(
            (
                ancho_destino,
                alto_destino
            ),
            Image.Resampling.LANCZOS
        )

    except MemoryError as error:

        rgb.close()

        raise RuntimeError(
            "No hay memoria suficiente para crear la imagen con "
            "esas dimensiones. Prueba una escala menor."
        ) from error

    rgb.close()

    resultado = rgb_redimensionado.filter(
        ImageFilter.UnsharpMask(
            radius=1.2,
            percent=115,
            threshold=3
        )
    )

    rgb_redimensionado.close()

    if alpha is None:

        return resultado

    try:

        alpha_redimensionada = alpha.resize(
            (
                ancho_destino,
                alto_destino
            ),
            Image.Resampling.LANCZOS
        )

    except MemoryError as error:

        resultado.close()

        alpha.close()

        raise RuntimeError(
            "No hay memoria suficiente para conservar la transparencia "
            "a esas dimensiones. Prueba una escala menor."
        ) from error

    resultado_rgba = resultado.convert(
        "RGBA"
    )

    resultado_rgba.putalpha(
        alpha_redimensionada
    )

    resultado.close()

    alpha.close()

    alpha_redimensionada.close()

    return resultado_rgba


# ================================================================
# CREAR OPCIONES DE SUBPROCESO
# ================================================================
def crear_opciones_subproceso():

    opciones = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "bufsize": 1
    }

    if os.name == "nt":

        opciones[
            "creationflags"
        ] = getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0
        )

    return opciones


# ================================================================
# TRADUCIR ERROR DE REAL-ESRGAN
# ================================================================
def traducir_error_realesrgan(
    registro,
    codigo_salida
):

    texto = (
        registro
        or ""
    ).lower()

    if (
        "out of memory" in texto
        or "vkallocatememory" in texto
        or "failed to allocate" in texto
        or "bad allocation" in texto
        or "std::bad_alloc" in texto
    ):

        return (
            "Real-ESRGAN se quedó sin memoria durante el procesamiento. "
            "Prueba una escala menor o cierra otras aplicaciones que "
            "estén usando la GPU."
        )

    if (
        "vulkan" in texto
        and (
            "failed" in texto
            or "not support" in texto
            or "no gpu" in texto
            or "no device" in texto
            or "unsupported" in texto
        )
    ):

        return (
            "Real-ESRGAN no pudo iniciar Vulkan. Comprueba que el "
            "controlador de tu tarjeta gráfica esté actualizado y que "
            "el equipo sea compatible con Vulkan."
        )

    if (
        "vkcreateinstance" in texto
        or "vkcreate" in texto
    ):

        return (
            "No fue posible iniciar el motor gráfico Vulkan necesario "
            "para Real-ESRGAN."
        )

    if (
        "decode image failed" in texto
        or "load image failed" in texto
        or "failed to load image" in texto
        or "image decode" in texto
    ):

        return (
            "Real-ESRGAN no pudo leer la imagen de entrada."
        )

    if (
        "encode image failed" in texto
        or "save image failed" in texto
        or "failed to save" in texto
        or "image encode" in texto
    ):

        return (
            "Real-ESRGAN no pudo guardar la imagen generada. Comprueba "
            "que haya espacio disponible y permisos de escritura."
        )

    if (
        "failed to load model" in texto
        or "load model failed" in texto
        or ".param" in texto
        or ".bin" in texto
    ):

        return (
            "Real-ESRGAN no pudo cargar el modelo de IA. Comprueba que "
            "los archivos del modelo estén completos dentro de la carpeta "
            "de Real-ESRGAN."
        )

    if (
        "permission denied" in texto
        or "access is denied" in texto
    ):

        return (
            "Real-ESRGAN no tiene permiso para leer o guardar alguno de "
            "los archivos necesarios."
        )

    if (
        "no space left" in texto
        or "disk full" in texto
    ):

        return (
            "No hay suficiente espacio libre en el disco para guardar "
            "la imagen mejorada."
        )

    if codigo_salida is None:

        return (
            "Real-ESRGAN se cerró de forma inesperada antes de terminar "
            "el procesamiento."
        )

    return (
        "Real-ESRGAN no pudo completar la mejora de la imagen. "
        f"Código de salida: {codigo_salida}."
    )


# ================================================================
# FINALIZAR PROCESO CANCELADO
# ================================================================
def finalizar_proceso_cancelado(
    proceso
):

    if proceso.poll() is not None:

        return

    try:

        proceso.terminate()

        proceso.wait(
            timeout=2
        )

        return

    except Exception:

        pass

    try:

        proceso.kill()

    except Exception:

        pass


# ================================================================
# LEER SALIDA DE PROCESO
# ================================================================
def leer_salida_proceso(
    proceso,
    cola_salida
):

    try:

        if proceso.stdout is None:

            return

        for linea in iter(
            proceso.stdout.readline,
            ""
        ):

            cola_salida.put(
                linea
            )

    finally:

        cola_salida.put(
            None
        )


# ================================================================
# EJECUTAR REAL-ESRGAN
# ================================================================
def ejecutar_realesrgan(
    ruta_entrada,
    ruta_salida,
    modelo,
    escala,
    tamano_tile=0,
    progreso=None,
    comprobar_cancelacion_callback=None
):

    ejecutable = detectar_realesrgan()

    if not ejecutable:

        raise RuntimeError(
            "No se encontró Real-ESRGAN."
        )

    if not comprobar_modelo_realesrgan(
        modelo
    ):

        raise RuntimeError(
            f"No se encontró el modelo de IA {modelo}."
        )

    carpeta_modelos = (
        obtener_carpeta_modelos_realesrgan()
    )

    comando = [
        ejecutable,
        "-i",
        str(
            ruta_entrada
        ),
        "-o",
        str(
            ruta_salida
        ),
        "-n",
        modelo,
        "-s",
        str(
            escala
        ),
        "-m",
        str(
            carpeta_modelos
        ),
        "-t",
        str(
            int(
                tamano_tile
            )
        ),
        "-f",
        "png"
    ]

    opciones = crear_opciones_subproceso()

    opciones[
        "cwd"
    ] = str(
        Path(
            ejecutable
        ).resolve().parent
    )

    try:

        proceso = subprocess.Popen(
            comando,
            **opciones
        )

    except FileNotFoundError as error:

        raise RuntimeError(
            "No se pudo iniciar Real-ESRGAN porque falta su ejecutable."
        ) from error

    except OSError as error:

        raise RuntimeError(
            "No se pudo iniciar Real-ESRGAN. Comprueba que todos sus "
            "archivos estén completos."
        ) from error

    cola_salida = queue.Queue()

    lector = threading.Thread(
        target=leer_salida_proceso,
        args=(
            proceso,
            cola_salida
        ),
        daemon=True
    )

    lector.start()

    registro = deque(
        maxlen=MAXIMO_LINEAS_REGISTRO_REALESRGAN
    )

    salida_cerrada = False

    ultimo_progreso = -1.0

    informar_progreso(
        progreso,
        0,
        "Preparando Real-ESRGAN..."
    )

    try:

        while True:

            comprobar_cancelacion(
                comprobar_cancelacion_callback
            )

            try:

                linea = cola_salida.get(
                    timeout=0.05
                )

            except queue.Empty:

                if (
                    proceso.poll() is not None
                    and salida_cerrada
                ):

                    break

                continue

            if linea is None:

                salida_cerrada = True

                if proceso.poll() is not None:

                    break

                continue

            linea = linea.strip()

            if not linea:

                continue

            registro.append(
                linea
            )

            coincidencia = (
                PATRON_PROGRESO_REALESRGAN.search(
                    linea
                )
            )

            if coincidencia is None:

                continue

            try:

                progreso_actual = float(
                    coincidencia.group(
                        1
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            progreso_actual = max(
                0.0,
                min(
                    100.0,
                    progreso_actual
                )
            )

            if (
                progreso_actual
                >= ultimo_progreso + 0.25
                or progreso_actual >= 99.0
            ):

                ultimo_progreso = progreso_actual

                informar_progreso(
                    progreso,
                    progreso_actual,
                    (
                        "Mejorando imagen con IA... "
                        f"{progreso_actual:.0f}%"
                    )
                )

        codigo_salida = proceso.wait()

    except MejoraCalidadCancelada:

        finalizar_proceso_cancelado(
            proceso
        )

        raise

    except Exception:

        finalizar_proceso_cancelado(
            proceso
        )

        raise

    finally:

        try:

            if proceso.stdout is not None:

                proceso.stdout.close()

        except Exception:

            pass

    texto_registro = "\n".join(
        registro
    )

    if codigo_salida != 0:

        raise RuntimeError(
            traducir_error_realesrgan(
                texto_registro,
                codigo_salida
            )
        )

    ruta_salida = Path(
        ruta_salida
    )

    if (
        not ruta_salida.is_file()
        or ruta_salida.stat().st_size <= 0
    ):

        raise RuntimeError(
            "Real-ESRGAN terminó sin generar una imagen válida."
        )

    informar_progreso(
        progreso,
        100,
        "Superresolución terminada."
    )


# ================================================================
# PERMITIR IMAGEN LOCAL GENERADA MUY GRANDE
# ================================================================
@contextmanager
def permitir_imagen_local_generada(
    ancho_esperado,
    alto_esperado
):

    limite_anterior = Image.MAX_IMAGE_PIXELS

    pixels_esperados = max(
        1,
        int(
            ancho_esperado
        )
        * int(
            alto_esperado
        )
    )

    if limite_anterior is None:

        with warnings.catch_warnings():

            warnings.simplefilter(
                "ignore",
                Image.DecompressionBombWarning
            )

            yield

        return

    limite_temporal = max(
        int(
            limite_anterior
        ),
        int(
            pixels_esperados
            * 1.10
        )
    )

    Image.MAX_IMAGE_PIXELS = (
        limite_temporal
    )

    try:

        with warnings.catch_warnings():

            warnings.simplefilter(
                "ignore",
                Image.DecompressionBombWarning
            )

            yield

    finally:

        Image.MAX_IMAGE_PIXELS = (
            limite_anterior
        )


# ================================================================
# MEJORAR CON IA
# ================================================================
def mejorar_con_ia(
    imagen,
    escala,
    tipo_imagen,
    carpeta_temporal,
    conservar_transparencia=True,
    progreso=None,
    comprobar_cancelacion_callback=None
):

    modelo = seleccionar_modelo(
        tipo_imagen
    )

    escala = int(
        escala
    )

    escala_interna = obtener_escala_interna_ia(
        escala
    )

    alpha = None

    if (
        conservar_transparencia
        and "A" in imagen.getbands()
    ):

        alpha = imagen.getchannel(
            "A"
        )

    rgb = preparar_rgb(
        imagen
    )

    ruta_entrada = (
        Path(
            carpeta_temporal
        )
        / "entrada.png"
    )

    ruta_salida = (
        Path(
            carpeta_temporal
        )
        / "salida.png"
    )

    try:

        rgb.save(
            ruta_entrada,
            format="PNG"
        )

    except Exception as error:

        rgb.close()

        if alpha is not None:

            alpha.close()

        raise RuntimeError(
            "No fue posible preparar la imagen temporal para "
            "Real-ESRGAN."
        ) from error

    rgb.close()

    ancho_objetivo, alto_objetivo = (
        calcular_dimensiones_salida(
            imagen.width,
            imagen.height,
            escala
        )
    )

    ancho_temporal, alto_temporal = (
        calcular_dimensiones_salida(
            imagen.width,
            imagen.height,
            escala_interna
        )
    )

    tamano_tile = seleccionar_tamano_tile(
        imagen.width,
        imagen.height,
        escala_interna
    )

    if escala in {
        2,
        3
    }:

        informar_progreso(
            progreso,
            0,
            (
                f"Preparando superresolución {escala}× "
                "mediante 4× interno..."
            )
        )

    elif tamano_tile > 0:

        informar_progreso(
            progreso,
            0,
            (
                "Preparando procesamiento por mosaicos "
                f"de {tamano_tile} px..."
            )
        )

    ejecutar_realesrgan(
        ruta_entrada,
        ruta_salida,
        modelo,
        escala_interna,
        tamano_tile=tamano_tile,
        progreso=progreso,
        comprobar_cancelacion_callback=(
            comprobar_cancelacion_callback
        )
    )

    comprobar_cancelacion(
        comprobar_cancelacion_callback
    )

    try:

        with permitir_imagen_local_generada(
            ancho_temporal,
            alto_temporal
        ):

            with Image.open(
                ruta_salida
            ) as imagen_resultado:

                resultado = imagen_resultado.convert(
                    "RGB"
                )

    except MemoryError as error:

        if alpha is not None:

            alpha.close()

        raise RuntimeError(
            "La imagen generada es demasiado grande para cargarla en "
            "memoria. Prueba una escala menor."
        ) from error

    except Image.DecompressionBombError as error:

        if alpha is not None:

            alpha.close()

        raise RuntimeError(
            "La imagen generada es muy grande y no pudo abrirse de "
            "forma segura. Prueba una escala menor."
        ) from error

    except Exception as error:

        if alpha is not None:

            alpha.close()

        raise RuntimeError(
            "Real-ESRGAN terminó, pero no fue posible abrir la imagen "
            "generada."
        ) from error

    if resultado.size != (
        ancho_temporal,
        alto_temporal
    ):

        try:

            redimensionada = resultado.resize(
                (
                    ancho_temporal,
                    alto_temporal
                ),
                Image.Resampling.LANCZOS
            )

        except MemoryError as error:

            resultado.close()

            if alpha is not None:

                alpha.close()

            raise RuntimeError(
                "No hay memoria suficiente para ajustar el tamaño temporal "
                "de la imagen. Prueba una escala menor."
            ) from error

        resultado.close()

        resultado = redimensionada

    if (
        ancho_temporal,
        alto_temporal
    ) != (
        ancho_objetivo,
        alto_objetivo
    ):

        informar_progreso(
            progreso,
            100,
            f"Ajustando resultado final a {escala}×..."
        )

        try:

            redimensionada = resultado.resize(
                (
                    ancho_objetivo,
                    alto_objetivo
                ),
                Image.Resampling.LANCZOS
            )

        except MemoryError as error:

            resultado.close()

            if alpha is not None:

                alpha.close()

            raise RuntimeError(
                "No hay memoria suficiente para ajustar el tamaño final "
                "de la imagen. Prueba una escala menor."
            ) from error

        resultado.close()

        resultado = redimensionada

    if alpha is None:

        return resultado

    try:

        alpha_redimensionada = alpha.resize(
            (
                ancho_objetivo,
                alto_objetivo
            ),
            Image.Resampling.LANCZOS
        )

        resultado_rgba = resultado.convert(
            "RGBA"
        )

        resultado_rgba.putalpha(
            alpha_redimensionada
        )

    except MemoryError as error:

        resultado.close()

        alpha.close()

        raise RuntimeError(
            "No hay memoria suficiente para reconstruir la transparencia "
            "de la imagen mejorada. Prueba una escala menor."
        ) from error

    resultado.close()

    alpha.close()

    alpha_redimensionada.close()

    return resultado_rgba

# ================================================================
# GUARDAR IMAGEN
# ================================================================
def guardar_imagen(
    imagen,
    ruta_destino,
    metadatos=None,
    conservar_metadatos=True
):

    ruta_destino = normalizar_ruta(
        ruta_destino
    )

    extension = ruta_destino.suffix.lower()

    formato = FORMATOS_SALIDA.get(
        extension
    )

    if formato is None:

        raise ValueError(
            "El formato de salida no es compatible."
        )

    opciones = {}

    metadatos = (
        metadatos
        or {}
    )

    if conservar_metadatos:

        if (
            "icc_profile" in metadatos
            and formato in {
                "JPEG",
                "PNG",
                "WEBP",
                "TIFF"
            }
        ):

            opciones[
                "icc_profile"
            ] = metadatos[
                "icc_profile"
            ]

        if (
            "exif" in metadatos
            and formato in {
                "JPEG",
                "PNG",
                "WEBP",
                "TIFF"
            }
        ):

            opciones[
                "exif"
            ] = metadatos[
                "exif"
            ]

    imagen_guardado = imagen

    if formato == "JPEG":

        if imagen.mode != "RGB":

            imagen_guardado = preparar_rgb(
                imagen
            )

        opciones.update(
            {
                "quality": 95,
                "subsampling": 0,
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

    elif formato == "PNG":

        opciones[
            "optimize"
        ] = True

    try:

        imagen_guardado.save(
            ruta_destino,
            format=formato,
            **opciones
        )

    except MemoryError as error:

        raise RuntimeError(
            "No hay memoria suficiente para guardar la imagen mejorada. "
            "Prueba una escala menor."
        ) from error

    except PermissionError as error:

        raise RuntimeError(
            "No hay permiso para guardar la imagen en la carpeta de salida."
        ) from error

    except OSError as error:

        mensaje = str(
            error
        ).lower()

        if (
            "no space left" in mensaje
            or "disk full" in mensaje
        ):

            raise RuntimeError(
                "No hay suficiente espacio libre en el disco para guardar "
                "la imagen mejorada."
            ) from error

        raise RuntimeError(
            "No fue posible guardar la imagen mejorada."
        ) from error

    finally:

        if imagen_guardado is not imagen:

            imagen_guardado.close()


# ================================================================
# GENERAR RUTA DE SALIDA
# ================================================================
def generar_ruta_salida(
    ruta_origen,
    carpeta_salida,
    sufijo="_mejorada",
    sobrescribir=False
):

    ruta_origen = normalizar_ruta(
        ruta_origen
    )

    carpeta_salida = normalizar_ruta(
        carpeta_salida
    )

    extension = ruta_origen.suffix.lower()

    if extension not in FORMATOS_SALIDA:

        extension = ".png"

    nombre_base = (
        ruta_origen.stem
        + sufijo
    )

    ruta_salida = (
        carpeta_salida
        / (
            nombre_base
            + extension
        )
    )

    if (
        sobrescribir
        or not ruta_salida.exists()
    ):

        return ruta_salida

    contador = 2

    while True:

        candidata = (
            carpeta_salida
            / (
                f"{nombre_base}_{contador}"
                f"{extension}"
            )
        )

        if not candidata.exists():

            return candidata

        contador += 1


# ================================================================
# MEJORAR UNA IMAGEN
# ================================================================
def mejorar_imagen(
    ruta_origen,
    ruta_destino,
    modo=MODO_IA,
    tipo_imagen=TIPO_AUTOMATICO,
    escala=2,
    conservar_transparencia=True,
    conservar_metadatos=True,
    progreso=None,
    comprobar_cancelacion_callback=None
):

    escala = validar_parametros(
        modo,
        tipo_imagen,
        escala
    )

    comprobar_cancelacion(
        comprobar_cancelacion_callback
    )

    informacion = obtener_informacion_imagen(
        ruta_origen
    )

    ruta_origen = Path(
        informacion[
            "ruta"
        ]
    )

    validar_limites_mejora(
        informacion[
            "ancho"
        ],
        informacion[
            "alto"
        ],
        escala,
        modo
    )

    ruta_destino = normalizar_ruta(
        ruta_destino
    )

    ruta_destino.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    informar_progreso(
        progreso,
        5,
        "Abriendo imagen..."
    )

    imagen, metadatos = (
        abrir_imagen_normalizada(
            ruta_origen
        )
    )

    resultado = None

    try:

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        if modo == MODO_IA:

            informar_progreso(
                progreso,
                12,
                "Preparando superresolución IA..."
            )

            def progreso_ia(
                porcentaje,
                estado
            ):

                porcentaje_general = (
                    12
                    + (
                        74
                        * porcentaje
                        / 100.0
                    )
                )

                informar_progreso(
                    progreso,
                    porcentaje_general,
                    estado
                )

            with tempfile.TemporaryDirectory(
                prefix="convertidor_realesrgan_"
            ) as carpeta_temporal:

                resultado = mejorar_con_ia(
                    imagen,
                    escala,
                    tipo_imagen,
                    carpeta_temporal,
                    conservar_transparencia,
                    progreso_ia,
                    comprobar_cancelacion_callback
                )

            informar_progreso(
                progreso,
                88,
                "Procesando resultado..."
            )

        else:

            informar_progreso(
                progreso,
                35,
                "Aplicando mejora clásica..."
            )

            resultado = mejorar_clasico(
                imagen,
                escala,
                conservar_transparencia
            )

            informar_progreso(
                progreso,
                82,
                "Procesando resultado..."
            )

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        informar_progreso(
            progreso,
            92,
            "Guardando imagen..."
        )

        descriptor, ruta_temporal = (
            tempfile.mkstemp(
                prefix=".mejora_",
                suffix=ruta_destino.suffix,
                dir=str(
                    ruta_destino.parent
                )
            )
        )

        os.close(
            descriptor
        )

        ruta_temporal = Path(
            ruta_temporal
        )

        try:

            guardar_imagen(
                resultado,
                ruta_temporal,
                metadatos,
                conservar_metadatos
            )

            comprobar_cancelacion(
                comprobar_cancelacion_callback
            )

            os.replace(
                ruta_temporal,
                ruta_destino
            )

        finally:

            if ruta_temporal.exists():

                try:

                    ruta_temporal.unlink()

                except OSError:

                    pass

    except MemoryError as error:

        raise RuntimeError(
            "No hay memoria suficiente para completar la mejora. "
            "Prueba una escala menor."
        ) from error

    finally:

        if resultado is not None:

            resultado.close()

        imagen.close()

    informar_progreso(
        progreso,
        100,
        "Imagen mejorada correctamente."
    )

    ancho_salida, alto_salida = (
        calcular_dimensiones_salida(
            informacion[
                "ancho"
            ],
            informacion[
                "alto"
            ],
            escala
        )
    )

    return {
        "ruta_origen": str(
            ruta_origen
        ),
        "ruta": str(
            ruta_destino
        ),
        "ancho_original": informacion[
            "ancho"
        ],
        "alto_original": informacion[
            "alto"
        ],
        "ancho": ancho_salida,
        "alto": alto_salida,
        "escala": escala,
        "modo": modo,
        "modelo": (
            seleccionar_modelo(
                tipo_imagen
            )
            if modo == MODO_IA
            else None
        ),
        "tamano_original": informacion[
            "tamano"
        ],
        "tamano_final": (
            ruta_destino.stat().st_size
        )
    }


# ================================================================
# MEJORAR VARIAS IMAGENES
# ================================================================
def mejorar_imagenes(
    rutas_origen,
    carpeta_salida,
    modo=MODO_IA,
    tipo_imagen=TIPO_AUTOMATICO,
    escala=2,
    conservar_transparencia=True,
    conservar_metadatos=True,
    sobrescribir=False,
    sufijo="_mejorada",
    progreso=None,
    comprobar_cancelacion_callback=None
):

    if not rutas_origen:

        raise ValueError(
            "No se recibieron imágenes para mejorar."
        )

    escala = validar_parametros(
        modo,
        tipo_imagen,
        escala
    )

    carpeta_salida = normalizar_ruta(
        carpeta_salida
    )

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True
    )

    total = len(
        rutas_origen
    )

    resultados = []

    for indice, ruta_origen in enumerate(
        rutas_origen,
        start=1
    ):

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        ruta_destino = generar_ruta_salida(
            ruta_origen,
            carpeta_salida,
            sufijo,
            sobrescribir
        )

        inicio = (
            (
                indice - 1
            )
            / total
            * 100
        )

        fin = (
            indice
            / total
            * 100
        )

        def progreso_imagen(
            porcentaje,
            estado,
            inicio=inicio,
            fin=fin,
            indice=indice
        ):

            porcentaje_total = (
                inicio
                + (
                    fin - inicio
                )
                * porcentaje
                / 100
            )

            informar_progreso(
                progreso,
                porcentaje_total,
                (
                    f"{estado} "
                    f"({indice}/{total})"
                )
            )

        resultado = mejorar_imagen(
            ruta_origen,
            ruta_destino,
            modo=modo,
            tipo_imagen=tipo_imagen,
            escala=escala,
            conservar_transparencia=(
                conservar_transparencia
            ),
            conservar_metadatos=(
                conservar_metadatos
            ),
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
        "Mejora terminada correctamente."
    )

    return resultados
