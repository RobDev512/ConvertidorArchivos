import os
import tempfile

from pathlib import Path

from PIL import (
    Image,
    ImageOps
)

from pypdf import (
    PdfReader,
    PdfWriter
)

from conversiones.imagemagick import (
    comprobar_archivo_imagemagick,
    convertir_con_imagemagick
)


# ================================================================
# TAMANOS DE PAGINA
# ================================================================

TAMANO_AUTOMATICO = "automatico"

TAMANO_A0 = "a0"
TAMANO_A1 = "a1"
TAMANO_A2 = "a2"
TAMANO_A3 = "a3"
TAMANO_A4 = "a4"
TAMANO_A5 = "a5"
TAMANO_A6 = "a6"

TAMANO_B0 = "b0"
TAMANO_B1 = "b1"
TAMANO_B2 = "b2"
TAMANO_B3 = "b3"
TAMANO_B4 = "b4"
TAMANO_B5 = "b5"
TAMANO_B6 = "b6"

TAMANO_CARTA = "carta"
TAMANO_LEGAL = "legal"
TAMANO_SOBRE_10 = "sobre_10"
TAMANO_TABLOIDE = "tabloide"
TAMANO_EJECUTIVO = "ejecutivo"


TAMANOS_PAGINA_MM = {
    TAMANO_A0: (
        841.0,
        1189.0
    ),
    TAMANO_A1: (
        594.0,
        841.0
    ),
    TAMANO_A2: (
        420.0,
        594.0
    ),
    TAMANO_A3: (
        297.0,
        420.0
    ),
    TAMANO_A4: (
        210.0,
        297.0
    ),
    TAMANO_A5: (
        148.0,
        210.0
    ),
    TAMANO_A6: (
        105.0,
        148.0
    ),

    TAMANO_B0: (
        1000.0,
        1414.0
    ),
    TAMANO_B1: (
        707.0,
        1000.0
    ),
    TAMANO_B2: (
        500.0,
        707.0
    ),
    TAMANO_B3: (
        353.0,
        500.0
    ),
    TAMANO_B4: (
        250.0,
        353.0
    ),
    TAMANO_B5: (
        176.0,
        250.0
    ),
    TAMANO_B6: (
        125.0,
        176.0
    ),

    TAMANO_CARTA: (
        215.9,
        279.4
    ),
    TAMANO_LEGAL: (
        215.9,
        355.6
    ),
    TAMANO_SOBRE_10: (
        104.8,
        241.3
    ),
    TAMANO_TABLOIDE: (
        279.4,
        431.8
    ),
    TAMANO_EJECUTIVO: (
        184.15,
        266.7
    )
}


# ================================================================
# ORIENTACIONES
# ================================================================

ORIENTACION_AUTOMATICA = "automatica"

ORIENTACION_VERTICAL = "vertical"

ORIENTACION_HORIZONTAL = "horizontal"


# ================================================================
# MODOS DE AJUSTE
# ================================================================

AJUSTE_ENCAJAR = "encajar"

AJUSTE_LLENAR = "llenar"


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
# NORMALIZAR ORIENTACION
# ================================================================
def normalizar_orientacion(
    orientacion
):

    orientaciones_validas = {
        ORIENTACION_AUTOMATICA,
        ORIENTACION_VERTICAL,
        ORIENTACION_HORIZONTAL
    }

    if orientacion not in orientaciones_validas:

        raise ValueError(
            "La orientación indicada no es válida."
        )

    return orientacion


# ================================================================
# NORMALIZAR AJUSTE
# ================================================================
def normalizar_ajuste(
    ajuste
):

    ajustes_validos = {
        AJUSTE_ENCAJAR,
        AJUSTE_LLENAR
    }

    if ajuste not in ajustes_validos:

        raise ValueError(
            "El modo de ajuste indicado no es válido."
        )

    return ajuste


# ================================================================
# VALIDAR TAMANO DE PAGINA
# ================================================================
def validar_tamano_pagina(
    tamano_pagina
):

    if tamano_pagina == TAMANO_AUTOMATICO:

        return tamano_pagina

    if tamano_pagina not in TAMANOS_PAGINA_MM:

        raise ValueError(
            "El tamaño de página indicado no es válido."
        )

    return tamano_pagina


# ================================================================
# VALIDAR CONFIGURACION DE PAGINA
# ================================================================
def validar_configuracion_pagina(
    configuracion,
    configuracion_predeterminada
):

    configuracion = dict(
        configuracion
        or {}
    )

    tamano_pagina = configuracion.get(
        "tamano_pagina",
        configuracion_predeterminada[
            "tamano_pagina"
        ]
    )

    orientacion = configuracion.get(
        "orientacion",
        configuracion_predeterminada[
            "orientacion"
        ]
    )

    ajuste = configuracion.get(
        "ajuste",
        configuracion_predeterminada[
            "ajuste"
        ]
    )

    margen_mm = configuracion.get(
        "margen_mm",
        configuracion_predeterminada[
            "margen_mm"
        ]
    )

    no_ampliar = configuracion.get(
        "no_ampliar",
        configuracion_predeterminada[
            "no_ampliar"
        ]
    )

    validar_tamano_pagina(
        tamano_pagina
    )

    normalizar_orientacion(
        orientacion
    )

    normalizar_ajuste(
        ajuste
    )

    try:

        margen_mm = float(
            margen_mm
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "El margen debe ser un número."
        )

    if margen_mm < 0:

        raise ValueError(
            "El margen no puede ser negativo."
        )

    return {
        "tamano_pagina": tamano_pagina,
        "orientacion": orientacion,
        "ajuste": ajuste,
        "margen_mm": margen_mm,
        "no_ampliar": bool(
            no_ampliar
        )
    }


# ================================================================
# VALIDAR PARAMETROS GENERALES
# ================================================================
def validar_parametros_generales(
    resolucion_ppp,
    calidad
):

    try:

        resolucion_ppp = int(
            resolucion_ppp
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "La resolución debe ser un número entero."
        )

    if not 72 <= resolucion_ppp <= 600:

        raise ValueError(
            "La resolución debe estar entre 72 y 600 ppp."
        )

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

    return (
        resolucion_ppp,
        calidad
    )


# ================================================================
# OBTENER INFORMACION CON PILLOW
# ================================================================
def obtener_informacion_pillow(
    ruta
):

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

            imagen = ImageOps.exif_transpose(
                imagen
            )

            ancho, alto = imagen.size

            dpi = imagen.info.get(
                "dpi"
            )

            dpi_promedio = None

            if isinstance(
                dpi,
                (
                    tuple,
                    list
                )
            ):

                valores = []

                for valor in dpi[:2]:

                    try:

                        numero = float(
                            valor
                        )

                    except (
                        TypeError,
                        ValueError
                    ):

                        continue

                    if numero > 0:

                        valores.append(
                            numero
                        )

                if valores:

                    dpi_promedio = (
                        sum(
                            valores
                        )
                        / len(
                            valores
                        )
                    )

            elif isinstance(
                dpi,
                (
                    int,
                    float
                )
            ):

                if dpi > 0:

                    dpi_promedio = float(
                        dpi
                    )

            return {
                "ancho": int(
                    ancho
                ),
                "alto": int(
                    alto
                ),
                "dpi": dpi_promedio,
                "motor": "pillow"
            }

    except Exception:

        return None


# ================================================================
# OBTENER INFORMACION CON IMAGEMAGICK
# ================================================================
def obtener_informacion_imagemagick(
    ruta
):

    legible, _ = comprobar_archivo_imagemagick(
        str(
            ruta
        )
    )

    if not legible:

        return None

    return {
        "ancho": None,
        "alto": None,
        "dpi": None,
        "motor": "imagemagick"
    }


# ================================================================
# COMPROBAR IMAGEN
# ================================================================
def comprobar_imagen(
    ruta
):

    ruta = normalizar_ruta(
        ruta
    )

    if not ruta.is_file():

        raise FileNotFoundError(
            f"No existe la imagen:\n{ruta}"
        )

    informacion = obtener_informacion_pillow(
        ruta
    )

    if informacion is not None:

        informacion[
            "ruta"
        ] = str(
            ruta
        )

        informacion[
            "tamano"
        ] = ruta.stat().st_size

        return informacion

    informacion = obtener_informacion_imagemagick(
        ruta
    )

    if informacion is not None:

        informacion[
            "ruta"
        ] = str(
            ruta
        )

        informacion[
            "tamano"
        ] = ruta.stat().st_size

        return informacion

    raise ValueError(
        "El archivo no pudo reconocerse "
        "como una imagen compatible."
    )


# ================================================================
# OBTENER INFORMACION DE IMAGEN
# ================================================================
def obtener_informacion_imagen(
    ruta
):

    informacion = comprobar_imagen(
        ruta
    )

    if (
        informacion[
            "ancho"
        ] is not None
        and informacion[
            "alto"
        ] is not None
    ):

        return informacion

    with tempfile.TemporaryDirectory(
        prefix="convertidor_info_imagen_"
    ) as carpeta_temporal:

        ruta_png = Path(
            carpeta_temporal
        ) / "imagen.png"

        convertir_con_imagemagick(
            informacion[
                "ruta"
            ],
            str(
                ruta_png
            ),
            "PNG"
        )

        informacion_png = obtener_informacion_pillow(
            ruta_png
        )

        if informacion_png is None:

            raise RuntimeError(
                "No fue posible obtener las dimensiones "
                "de la imagen."
            )

        informacion[
            "ancho"
        ] = informacion_png[
            "ancho"
        ]

        informacion[
            "alto"
        ] = informacion_png[
            "alto"
        ]

        informacion[
            "dpi"
        ] = informacion_png[
            "dpi"
        ]

    return informacion


# ================================================================
# CARGAR IMAGEN PARA PDF
# ================================================================
def cargar_imagen_para_pdf(
    ruta,
    carpeta_temporal,
    indice
):

    ruta = normalizar_ruta(
        ruta
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

            imagen = ImageOps.exif_transpose(
                imagen
            )

            return imagen.convert(
                "RGBA"
            )

    except Exception:

        ruta_png = Path(
            carpeta_temporal
        ) / (
            f"normalizada_"
            f"{indice:05d}.png"
        )

        convertir_con_imagemagick(
            str(
                ruta
            ),
            str(
                ruta_png
            ),
            "PNG"
        )

        with Image.open(
            ruta_png
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

            return imagen.convert(
                "RGBA"
            )


# ================================================================
# CONVERTIR MILIMETROS A PIXELES
# ================================================================
def mm_a_pixels(
    milimetros,
    resolucion_ppp
):

    return max(
        0,
        int(
            round(
                float(
                    milimetros
                )
                / 25.4
                * resolucion_ppp
            )
        )
    )


# ================================================================
# OBTENER DIMENSIONES DE PAGINA
# ================================================================
def obtener_dimensiones_pagina(
    ancho_imagen,
    alto_imagen,
    tamano_pagina,
    orientacion,
    margen_mm,
    resolucion_ppp
):

    margen_px = mm_a_pixels(
        margen_mm,
        resolucion_ppp
    )

    if tamano_pagina == TAMANO_AUTOMATICO:

        ancho_pagina = (
            int(
                ancho_imagen
            )
            + margen_px
            * 2
        )

        alto_pagina = (
            int(
                alto_imagen
            )
            + margen_px
            * 2
        )

    else:

        ancho_mm, alto_mm = (
            TAMANOS_PAGINA_MM[
                tamano_pagina
            ]
        )

        ancho_pagina = mm_a_pixels(
            ancho_mm,
            resolucion_ppp
        )

        alto_pagina = mm_a_pixels(
            alto_mm,
            resolucion_ppp
        )

    ancho_pagina = max(
        1,
        ancho_pagina
    )

    alto_pagina = max(
        1,
        alto_pagina
    )

    if orientacion == ORIENTACION_VERTICAL:

        if ancho_pagina > alto_pagina:

            ancho_pagina, alto_pagina = (
                alto_pagina,
                ancho_pagina
            )

    elif orientacion == ORIENTACION_HORIZONTAL:

        if alto_pagina > ancho_pagina:

            ancho_pagina, alto_pagina = (
                alto_pagina,
                ancho_pagina
            )

    elif orientacion == ORIENTACION_AUTOMATICA:

        imagen_horizontal = (
            ancho_imagen
            > alto_imagen
        )

        pagina_horizontal = (
            ancho_pagina
            > alto_pagina
        )

        if imagen_horizontal != pagina_horizontal:

            ancho_pagina, alto_pagina = (
                alto_pagina,
                ancho_pagina
            )

    return (
        ancho_pagina,
        alto_pagina,
        margen_px
    )


# ================================================================
# PREPARAR IMAGEN RGB
# ================================================================
def preparar_imagen_rgb(
    imagen
):

    if imagen.mode != "RGBA":

        imagen = imagen.convert(
            "RGBA"
        )

    fondo = Image.new(
        "RGB",
        imagen.size,
        "white"
    )

    fondo.paste(
        imagen,
        (
            0,
            0
        ),
        imagen
    )

    return fondo


# ================================================================
# COLOCAR IMAGEN EN PAGINA
# ================================================================
def crear_pagina(
    imagen,
    tamano_pagina,
    orientacion,
    ajuste,
    margen_mm,
    resolucion_ppp,
    no_ampliar
):

    imagen_rgb = preparar_imagen_rgb(
        imagen
    )

    ancho_imagen, alto_imagen = (
        imagen_rgb.size
    )

    (
        ancho_pagina,
        alto_pagina,
        margen_px
    ) = obtener_dimensiones_pagina(
        ancho_imagen,
        alto_imagen,
        tamano_pagina,
        orientacion,
        margen_mm,
        resolucion_ppp
    )

    ancho_disponible = (
        ancho_pagina
        - margen_px
        * 2
    )

    alto_disponible = (
        alto_pagina
        - margen_px
        * 2
    )

    if (
        ancho_disponible <= 0
        or alto_disponible <= 0
    ):

        imagen_rgb.close()

        raise ValueError(
            "El margen es demasiado grande para "
            "el tamaño de página seleccionado."
        )

    if ajuste == AJUSTE_LLENAR:

        escala = max(
            ancho_disponible
            / max(
                1,
                ancho_imagen
            ),
            alto_disponible
            / max(
                1,
                alto_imagen
            )
        )

    else:

        escala = min(
            ancho_disponible
            / max(
                1,
                ancho_imagen
            ),
            alto_disponible
            / max(
                1,
                alto_imagen
            )
        )

    if no_ampliar:

        escala = min(
            escala,
            1.0
        )

    nuevo_ancho = max(
        1,
        int(
            round(
                ancho_imagen
                * escala
            )
        )
    )

    nuevo_alto = max(
        1,
        int(
            round(
                alto_imagen
                * escala
            )
        )
    )

    if (
        nuevo_ancho != ancho_imagen
        or nuevo_alto != alto_imagen
    ):

        imagen_redimensionada = imagen_rgb.resize(
            (
                nuevo_ancho,
                nuevo_alto
            ),
            Image.Resampling.LANCZOS
        )

        imagen_rgb.close()

        imagen_rgb = imagen_redimensionada

    if ajuste == AJUSTE_LLENAR:

        if (
            imagen_rgb.width
            > ancho_disponible
            or imagen_rgb.height
            > alto_disponible
        ):

            izquierda = max(
                0,
                int(
                    round(
                        (
                            imagen_rgb.width
                            - ancho_disponible
                        )
                        / 2
                    )
                )
            )

            arriba = max(
                0,
                int(
                    round(
                        (
                            imagen_rgb.height
                            - alto_disponible
                        )
                        / 2
                    )
                )
            )

            derecha = min(
                imagen_rgb.width,
                izquierda
                + ancho_disponible
            )

            abajo = min(
                imagen_rgb.height,
                arriba
                + alto_disponible
            )

            imagen_recortada = imagen_rgb.crop(
                (
                    izquierda,
                    arriba,
                    derecha,
                    abajo
                )
            )

            imagen_rgb.close()

            imagen_rgb = imagen_recortada

    pagina = Image.new(
        "RGB",
        (
            ancho_pagina,
            alto_pagina
        ),
        "white"
    )

    x = int(
        round(
            (
                ancho_pagina
                - imagen_rgb.width
            )
            / 2
        )
    )

    y = int(
        round(
            (
                alto_pagina
                - imagen_rgb.height
            )
            / 2
        )
    )

    pagina.paste(
        imagen_rgb,
        (
            x,
            y
        )
    )

    imagen_rgb.close()

    return pagina


# ================================================================
# PREPARAR CONFIGURACIONES DE PAGINA
# ================================================================
def preparar_configuraciones_paginas(
    total,
    configuraciones_paginas,
    configuracion_predeterminada
):

    if configuraciones_paginas is None:

        configuraciones_paginas = [
            None
        ] * total

    if len(
        configuraciones_paginas
    ) != total:

        raise ValueError(
            "La cantidad de configuraciones de página "
            "no coincide con la cantidad de imágenes."
        )

    configuraciones = []

    for configuracion in configuraciones_paginas:

        configuraciones.append(
            validar_configuracion_pagina(
                configuracion,
                configuracion_predeterminada
            )
        )

    return configuraciones


# ================================================================
# CREAR PDF DESDE IMAGENES
# ================================================================
def crear_pdf_desde_imagenes(
    rutas_imagenes,
    ruta_destino,
    tamano_pagina=TAMANO_A4,
    orientacion=ORIENTACION_AUTOMATICA,
    ajuste=AJUSTE_ENCAJAR,
    margen_mm=8.0,
    resolucion_ppp=200,
    calidad=92,
    no_ampliar=False,
    configuraciones_paginas=None,
    progreso=None,
    comprobar_cancelacion_callback=None
):

    if not rutas_imagenes:

        raise ValueError(
            "No se recibieron imágenes para crear el PDF."
        )

    (
        resolucion_ppp,
        calidad
    ) = validar_parametros_generales(
        resolucion_ppp,
        calidad
    )

    configuracion_predeterminada = (
        validar_configuracion_pagina(
            {
                "tamano_pagina": tamano_pagina,
                "orientacion": orientacion,
                "ajuste": ajuste,
                "margen_mm": margen_mm,
                "no_ampliar": no_ampliar
            },
            {
                "tamano_pagina": TAMANO_A4,
                "orientacion": ORIENTACION_AUTOMATICA,
                "ajuste": AJUSTE_ENCAJAR,
                "margen_mm": 8.0,
                "no_ampliar": False
            }
        )
    )

    rutas = []

    for ruta in rutas_imagenes:

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        informacion = comprobar_imagen(
            ruta
        )

        rutas.append(
            informacion[
                "ruta"
            ]
        )

    total = len(
        rutas
    )

    configuraciones = (
        preparar_configuraciones_paginas(
            total,
            configuraciones_paginas,
            configuracion_predeterminada
        )
    )

    ruta_destino = normalizar_ruta(
        ruta_destino
    )

    if ruta_destino.suffix.lower() != ".pdf":

        ruta_destino = ruta_destino.with_suffix(
            ".pdf"
        )

    ruta_destino.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    (
        descriptor,
        ruta_temporal_final
    ) = tempfile.mkstemp(
        prefix=".imagenes_pdf_",
        suffix=".pdf",
        dir=str(
            ruta_destino.parent
        )
    )

    os.close(
        descriptor
    )

    os.remove(
        ruta_temporal_final
    )

    ruta_temporal_final = Path(
        ruta_temporal_final
    )

    escritor = PdfWriter()

    try:

        with tempfile.TemporaryDirectory(
            prefix="convertidor_imagenes_pdf_"
        ) as carpeta_temporal:

            for indice, (
                ruta,
                configuracion
            ) in enumerate(
                zip(
                    rutas,
                    configuraciones
                ),
                start=1
            ):

                comprobar_cancelacion(
                    comprobar_cancelacion_callback
                )

                porcentaje_inicio = (
                    (
                        indice - 1
                    )
                    / total
                    * 90
                )

                informar_progreso(
                    progreso,
                    porcentaje_inicio,
                    (
                        f"Preparando imagen "
                        f"{indice} de {total}..."
                    )
                )

                imagen = cargar_imagen_para_pdf(
                    ruta,
                    carpeta_temporal,
                    indice
                )

                comprobar_cancelacion(
                    comprobar_cancelacion_callback
                )

                pagina = crear_pagina(
                    imagen,
                    configuracion[
                        "tamano_pagina"
                    ],
                    configuracion[
                        "orientacion"
                    ],
                    configuracion[
                        "ajuste"
                    ],
                    configuracion[
                        "margen_mm"
                    ],
                    resolucion_ppp,
                    configuracion[
                        "no_ampliar"
                    ]
                )

                imagen.close()

                ruta_pagina = Path(
                    carpeta_temporal
                ) / (
                    f"pagina_"
                    f"{indice:05d}.pdf"
                )

                pagina.save(
                    ruta_pagina,
                    format="PDF",
                    resolution=resolucion_ppp,
                    quality=calidad,
                    optimize=True
                )

                pagina.close()

                lector = PdfReader(
                    str(
                        ruta_pagina
                    )
                )

                if not lector.pages:

                    raise RuntimeError(
                        "No fue posible crear "
                        f"la página {indice}."
                    )

                escritor.add_page(
                    lector.pages[0]
                )

                informar_progreso(
                    progreso,
                    (
                        indice
                        / total
                        * 90
                    ),
                    (
                        f"Página {indice} de "
                        f"{total} preparada."
                    )
                )

            comprobar_cancelacion(
                comprobar_cancelacion_callback
            )

            informar_progreso(
                progreso,
                94,
                "Escribiendo PDF..."
            )

            with open(
                ruta_temporal_final,
                "wb"
            ) as archivo_pdf:

                escritor.write(
                    archivo_pdf
                )

        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        if not ruta_temporal_final.is_file():

            raise RuntimeError(
                "La operación terminó sin generar el PDF."
            )

        if ruta_temporal_final.stat().st_size <= 0:

            raise RuntimeError(
                "La operación generó un PDF vacío."
            )

        os.replace(
            ruta_temporal_final,
            ruta_destino
        )

    except Exception:

        if ruta_temporal_final.exists():

            try:

                ruta_temporal_final.unlink()

            except OSError:

                pass

        raise

    informar_progreso(
        progreso,
        100,
        "PDF creado correctamente."
    )

    return {
        "ruta": str(
            ruta_destino
        ),
        "paginas": total,
        "tamano": ruta_destino.stat().st_size,
        "resolucion_ppp": resolucion_ppp,
        "calidad": calidad
    }