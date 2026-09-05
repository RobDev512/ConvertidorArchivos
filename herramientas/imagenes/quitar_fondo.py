import gc
import importlib.util
import os
import tempfile
import threading

from pathlib import Path

from PIL import (
    Image,
    ImageChops,
    ImageFilter,
    ImageOps
)

from funciones.capacidades import (
    obtener_carpeta_motores
)


# ================================================================
# METODOS
# ================================================================

METODO_AUTOMATICO = "automatico"

METODO_RAPIDO = "rapido"

METODO_EQUILIBRADO = "equilibrado"

METODO_PRECISO = "preciso"


# ================================================================
# MODELOS
# ================================================================

MODELO_U2NETP = "u2netp"

MODELO_ISNET = "isnet-general-use"

MODELO_BIREFNET = "birefnet-general"


MODELOS_POR_METODO = {
    METODO_AUTOMATICO: MODELO_ISNET,
    METODO_RAPIDO: MODELO_U2NETP,
    METODO_EQUILIBRADO: MODELO_ISNET,
    METODO_PRECISO: MODELO_BIREFNET
}


NOMBRES_MODELOS = {
    MODELO_U2NETP: "U²-NetP",
    MODELO_ISNET: "IS-Net General Use",
    MODELO_BIREFNET: "BiRefNet General"
}


# ================================================================
# RECORTE DE TRANSPARENCIA
# ================================================================

RECORTE_SUAVE = "suave"

RECORTE_NORMAL = "normal"

RECORTE_FIRME = "firme"


RECORTES_VALIDOS = {
    RECORTE_SUAVE,
    RECORTE_NORMAL,
    RECORTE_FIRME
}


# ================================================================
# LIMITES DE SEGURIDAD
# ================================================================

LIMITE_LADO_ENTRADA = 12_000

LIMITE_PIXELES_ENTRADA = 60_000_000


# ================================================================
# SESION ACTUAL
# ================================================================

_sesion_actual = None

_modelo_sesion_actual = None

_bloqueo_sesion = threading.Lock()


# ================================================================
# CANCELACION
# ================================================================
class QuitarFondoCancelado(
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

        raise QuitarFondoCancelado(
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
# OBTENER CARPETA DE MODELOS
# ================================================================
def obtener_carpeta_modelos_quitar_fondo():

    return Path(
        obtener_carpeta_motores()
    ) / "quitar_fondo"


# ================================================================
# OBTENER RUTA DE MODELO
# ================================================================
def obtener_ruta_modelo(
    modelo
):

    return (
        obtener_carpeta_modelos_quitar_fondo()
        / f"{modelo}.onnx"
    )


# ================================================================
# SELECCIONAR MODELO
# ================================================================
def seleccionar_modelo(
    metodo
):

    if metodo not in MODELOS_POR_METODO:

        raise ValueError(
            "El método de eliminación de fondo no es válido."
        )

    return MODELOS_POR_METODO[
        metodo
    ]


# ================================================================
# OBTENER NOMBRE DEL MODELO
# ================================================================
def obtener_nombre_modelo(
    modelo
):

    return NOMBRES_MODELOS.get(
        modelo,
        modelo
    )


# ================================================================
# COMPROBAR DEPENDENCIAS
# ================================================================
def comprobar_dependencias():

    if (
        importlib.util.find_spec(
            "rembg"
        )
        is None
    ):

        return (
            False,
            (
                "No está instalada la biblioteca rembg. "
                'Instálala con: pip install "rembg[cpu]"'
            )
        )

    if (
        importlib.util.find_spec(
            "onnxruntime"
        )
        is None
    ):

        return (
            False,
            (
                "No está instalado ONNX Runtime."
            )
        )

    return (
        True,
        None
    )


# ================================================================
# COMPROBAR MOTOR
# ================================================================
def comprobar_motor_quitar_fondo(
    metodo=METODO_AUTOMATICO
):

    disponible, mensaje = (
        comprobar_dependencias()
    )

    if not disponible:

        return {
            "disponible": False,
            "modelo": None,
            "ruta_modelo": None,
            "mensaje": mensaje
        }

    try:

        modelo = seleccionar_modelo(
            metodo
        )

    except Exception as error:

        return {
            "disponible": False,
            "modelo": None,
            "ruta_modelo": None,
            "mensaje": str(
                error
            )
        }

    ruta_modelo = obtener_ruta_modelo(
        modelo
    )

    if not ruta_modelo.is_file():

        return {
            "disponible": False,
            "modelo": modelo,
            "ruta_modelo": str(
                ruta_modelo
            ),
            "mensaje": (
                "No se encontró el modelo "
                f"{obtener_nombre_modelo(modelo)}."
            )
        }

    return {
        "disponible": True,
        "modelo": modelo,
        "ruta_modelo": str(
            ruta_modelo
        ),
        "mensaje": (
            f"{obtener_nombre_modelo(modelo)} disponible."
        )
    }


# ================================================================
# VALIDAR DIMENSIONES
# ================================================================
def validar_dimensiones(
    ancho,
    alto
):

    ancho = int(
        ancho
    )

    alto = int(
        alto
    )

    if (
        ancho <= 0
        or alto <= 0
    ):

        raise ValueError(
            "Las dimensiones de la imagen no son válidas."
        )

    if max(
        ancho,
        alto
    ) > LIMITE_LADO_ENTRADA:

        raise RuntimeError(
            "La imagen es demasiado grande para quitarle "
            "el fondo de forma segura.\n\n"
            f"Resolución: {ancho} × {alto} px\n"
            f"Límite por lado: {LIMITE_LADO_ENTRADA} px"
        )

    pixeles = (
        ancho
        * alto
    )

    if pixeles > LIMITE_PIXELES_ENTRADA:

        megapixeles = (
            pixeles
            / 1_000_000
        )

        limite_megapixeles = (
            LIMITE_PIXELES_ENTRADA
            / 1_000_000
        )

        raise RuntimeError(
            "La imagen contiene demasiados píxeles para "
            "quitarle el fondo de forma segura.\n\n"
            f"Imagen: {megapixeles:.1f} MP\n"
            f"Límite: {limite_megapixeles:.0f} MP"
        )


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

            imagen = ImageOps.exif_transpose(
                imagen
            )

            ancho, alto = imagen.size

            validar_dimensiones(
                ancho,
                alto
            )

            formato = (
                imagen.format
                or ruta.suffix.lstrip(
                    "."
                ).upper()
            )

            tiene_alpha = (
                "A" in imagen.getbands()
                or (
                    imagen.mode == "P"
                    and "transparency"
                    in imagen.info
                )
            )

    except Image.DecompressionBombError as error:

        raise RuntimeError(
            "La imagen es demasiado grande para abrirse "
            "de forma segura."
        ) from error

    except (
        RuntimeError,
        FileNotFoundError
    ):

        raise

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

            # La orientación ya se aplicará físicamente.
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
# ABRIR IMAGEN
# ================================================================
def abrir_imagen(
    ruta
):

    ruta = normalizar_ruta(
        ruta
    )

    try:

        imagen_origen = Image.open(
            ruta
        )

    except Image.DecompressionBombError as error:

        raise RuntimeError(
            "La imagen es demasiado grande para abrirse "
            "de forma segura."
        ) from error

    except Exception as error:

        raise ValueError(
            "No fue posible abrir la imagen."
        ) from error

    try:

        metadatos = extraer_metadatos(
            imagen_origen
        )

        imagen = ImageOps.exif_transpose(
            imagen_origen
        ).convert(
            "RGBA"
        )

        validar_dimensiones(
            imagen.width,
            imagen.height
        )

    except Exception:

        imagen_origen.close()

        raise

    imagen_origen.close()

    return (
        imagen,
        metadatos
    )


# ================================================================
# CONFIGURAR CARPETA DE MODELOS PARA REMBG
# ================================================================
def configurar_carpeta_modelos():

    carpeta = (
        obtener_carpeta_modelos_quitar_fondo()
    )

    carpeta.mkdir(
        parents=True,
        exist_ok=True
    )

    # rembg reconoce U2NET_HOME.
    # Al apuntarlo a motores/quitar_fondo puede encontrar
    # nuestras copias locales sin descargar nada.
    os.environ[
        "U2NET_HOME"
    ] = str(
        carpeta
    )

    return carpeta


# ================================================================
# OBTENER SESION DE IA
# ================================================================
def obtener_sesion(
    modelo
):

    global _sesion_actual
    global _modelo_sesion_actual

    ruta_modelo = obtener_ruta_modelo(
        modelo
    )

    if not ruta_modelo.is_file():

        raise RuntimeError(
            "No se encontró el modelo necesario:\n"
            f"{ruta_modelo}"
        )

    disponible, mensaje = (
        comprobar_dependencias()
    )

    if not disponible:

        raise RuntimeError(
            mensaje
        )

    configurar_carpeta_modelos()

    with _bloqueo_sesion:

        if (
            _sesion_actual is not None
            and _modelo_sesion_actual == modelo
        ):

            return _sesion_actual

        _sesion_actual = None
        _modelo_sesion_actual = None

        gc.collect()

        try:

            from rembg import new_session

            sesion = new_session(
                modelo
            )

        except Exception as error:

            raise RuntimeError(
                "No fue posible iniciar "
                f"{obtener_nombre_modelo(modelo)}."
            ) from error

        _sesion_actual = sesion
        _modelo_sesion_actual = modelo

        return _sesion_actual


# ================================================================
# LIBERAR SESION
# ================================================================
def liberar_sesion():

    global _sesion_actual
    global _modelo_sesion_actual

    with _bloqueo_sesion:

        _sesion_actual = None
        _modelo_sesion_actual = None

    gc.collect()


# ================================================================
# AJUSTAR MASCARA
# ================================================================
def ajustar_mascara(
    mascara,
    suavizado_bordes=1,
    recorte=RECORTE_NORMAL
):

    if recorte not in RECORTES_VALIDOS:

        raise ValueError(
            "El tipo de recorte de transparencia no es válido."
        )

    mascara = mascara.convert(
        "L"
    )

    if recorte == RECORTE_SUAVE:

        minimo = 6
        maximo = 249

    elif recorte == RECORTE_FIRME:

        minimo = 40
        maximo = 215

    else:

        minimo = 18
        maximo = 238

    tabla = []

    diferencia = max(
        1,
        maximo - minimo
    )

    for valor in range(
        256
    ):

        if valor <= minimo:

            nuevo = 0

        elif valor >= maximo:

            nuevo = 255

        else:

            nuevo = int(
                (
                    valor - minimo
                )
                / diferencia
                * 255
            )

        tabla.append(
            nuevo
        )

    mascara = mascara.point(
        tabla
    )

    suavizado_bordes = max(
        0,
        min(
            5,
            int(
                suavizado_bordes
            )
        )
    )

    if suavizado_bordes > 0:

        mascara = mascara.filter(
            ImageFilter.GaussianBlur(
                radius=(
                    suavizado_bordes
                    * 0.55
                )
            )
        )

    return mascara


# ================================================================
# CREAR RESULTADO CON TRANSPARENCIA
# ================================================================
def aplicar_mascara(
    imagen,
    mascara,
    conservar_transparencia_original=True
):

    resultado = imagen.convert(
        "RGBA"
    )

    mascara = mascara.resize(
        resultado.size,
        Image.Resampling.LANCZOS
    )

    if (
        conservar_transparencia_original
        and "A" in imagen.getbands()
    ):

        alpha_original = imagen.getchannel(
            "A"
        )

        mascara_final = ImageChops.multiply(
            alpha_original,
            mascara
        )

        alpha_original.close()

        mascara.close()

        mascara = mascara_final

    resultado.putalpha(
        mascara
    )

    mascara.close()

    return resultado


# ================================================================
# GUARDAR PNG
# ================================================================
def guardar_png(
    imagen,
    ruta_destino,
    metadatos=None,
    conservar_metadatos=True
):

    ruta_destino = normalizar_ruta(
        ruta_destino
    )

    ruta_destino.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    opciones = {
        "optimize": True
    }

    metadatos = (
        metadatos
        or {}
    )

    if conservar_metadatos:

        if "icc_profile" in metadatos:

            opciones[
                "icc_profile"
            ] = metadatos[
                "icc_profile"
            ]

        if "exif" in metadatos:

            opciones[
                "exif"
            ] = metadatos[
                "exif"
            ]

    descriptor, ruta_temporal = (
        tempfile.mkstemp(
            prefix=".quitar_fondo_",
            suffix=".png",
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

        imagen.save(
            ruta_temporal,
            format="PNG",
            **opciones
        )

        os.replace(
            ruta_temporal,
            ruta_destino
        )

    except PermissionError as error:

        raise RuntimeError(
            "No hay permiso para guardar el archivo "
            "en la carpeta seleccionada."
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
                "No hay suficiente espacio libre en el disco."
            ) from error

        raise RuntimeError(
            "No fue posible guardar la imagen sin fondo."
        ) from error

    finally:

        if ruta_temporal.exists():

            try:

                ruta_temporal.unlink()

            except OSError:

                pass


# ================================================================
# GENERAR RUTA DE SALIDA
# ================================================================
def generar_ruta_salida(
    ruta_origen,
    carpeta_salida,
    sufijo="_sin_fondo",
    sobrescribir=False
):

    ruta_origen = normalizar_ruta(
        ruta_origen
    )

    carpeta_salida = normalizar_ruta(
        carpeta_salida
    )

    nombre_base = (
        ruta_origen.stem
        + sufijo
    )

    ruta_salida = (
        carpeta_salida
        / f"{nombre_base}.png"
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
                f"{nombre_base}_{contador}.png"
            )
        )

        if not candidata.exists():

            return candidata

        contador += 1


# ================================================================
# QUITAR FONDO
# ================================================================
def quitar_fondo_imagen(
    ruta_origen,
    ruta_destino,
    metodo=METODO_AUTOMATICO,
    suavizado_bordes=1,
    recorte=RECORTE_NORMAL,
    conservar_transparencia_original=True,
    conservar_metadatos=True,
    progreso=None,
    comprobar_cancelacion_callback=None
):

    comprobar_cancelacion(
        comprobar_cancelacion_callback
    )

    informacion = obtener_informacion_imagen(
        ruta_origen
    )

    modelo = seleccionar_modelo(
        metodo
    )

    estado_motor = comprobar_motor_quitar_fondo(
        metodo
    )

    if not estado_motor[
        "disponible"
    ]:

        raise RuntimeError(
            estado_motor[
                "mensaje"
            ]
        )

    ruta_destino = normalizar_ruta(
        ruta_destino
    )

    # La herramienta siempre necesita PNG para conservar alfa.
    if ruta_destino.suffix.lower() != ".png":

        ruta_destino = ruta_destino.with_suffix(
            ".png"
        )

    informar_progreso(
        progreso,
        5,
        "Abriendo imagen..."
    )

    imagen, metadatos = abrir_imagen(
        ruta_origen
    )

    resultado = None
    mascara = None

    try:

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        informar_progreso(
            progreso,
            18,
            (
                "Cargando "
                f"{obtener_nombre_modelo(modelo)}..."
            )
        )

        sesion = obtener_sesion(
            modelo
        )

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        informar_progreso(
            progreso,
            35,
            "Analizando la imagen con IA..."
        )

        try:

            from rembg import remove

            mascara = remove(
                imagen.convert(
                    "RGB"
                ),
                session=sesion,
                only_mask=True
            )

        except MemoryError as error:

            raise RuntimeError(
                "No hay suficiente memoria para procesar "
                "esta imagen con el modelo seleccionado."
            ) from error

        except Exception as error:

            raise RuntimeError(
                "El modelo de IA no pudo analizar la imagen."
            ) from error

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        if not isinstance(
            mascara,
            Image.Image
        ):

            raise RuntimeError(
                "El modelo no devolvió una máscara válida."
            )

        informar_progreso(
            progreso,
            78,
            "Refinando el recorte..."
        )

        mascara_ajustada = ajustar_mascara(
            mascara,
            suavizado_bordes,
            recorte
        )

        mascara.close()

        mascara = None

        resultado = aplicar_mascara(
            imagen,
            mascara_ajustada,
            conservar_transparencia_original
        )

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        informar_progreso(
            progreso,
            92,
            "Guardando PNG con transparencia..."
        )

        guardar_png(
            resultado,
            ruta_destino,
            metadatos,
            conservar_metadatos
        )

    finally:

        if mascara is not None:

            mascara.close()

        if resultado is not None:

            resultado.close()

        imagen.close()

    informar_progreso(
        progreso,
        100,
        "Fondo eliminado correctamente."
    )

    return {
        "ruta_origen": informacion[
            "ruta"
        ],
        "ruta": str(
            ruta_destino
        ),
        "ancho": informacion[
            "ancho"
        ],
        "alto": informacion[
            "alto"
        ],
        "metodo": metodo,
        "modelo": modelo,
        "nombre_modelo": obtener_nombre_modelo(
            modelo
        ),
        "tamano_original": informacion[
            "tamano"
        ],
        "tamano_final": (
            ruta_destino.stat().st_size
        )
    }