import argparse
import colorsys
import json
import math
import re
import shutil

from pathlib import Path
from statistics import median

import pypdfium2 as pdfium
from PIL import Image


# ================================================================
# RUTAS
# ================================================================

CARPETA_BASE = Path(__file__).resolve().parent
CARPETA_ENTRADA = CARPETA_BASE / "entrada"
CARPETA_SALIDA = CARPETA_BASE / "salida"
CARPETA_DIAGNOSTICO = CARPETA_BASE / "diagnostico" / "efectos_pdf"

RUTA_DISTRIBUCION_PREDETERMINADA = CARPETA_SALIDA / "distribucion_pdf.json"
RUTA_JSON_SALIDA = CARPETA_SALIDA / "analisis_efectos_pdf.json"
RUTA_RESUMEN_SALIDA = CARPETA_SALIDA / "resumen_efectos_pdf.txt"


# ================================================================
# CONFIGURACIÓN
# ================================================================

ESCALA_RENDER_PREDETERMINADA = 4.0
RELLENO_RECORTE_PT = 10.0
TAMANO_MINIMO_FUENTE = 16.0

DIFERENCIA_MINIMA_FOREGROUND = 24.0
SATURACION_MINIMA_COLOR = 42.0
DIFERENCIA_MINIMA_DEGRADADO = 24.0

SOLAPE_HORIZONTAL_MINIMO_EFECTO = 0.45
DISTANCIA_VERTICAL_MAXIMA_EFECTO_PT = 48.0


# ================================================================
# UTILIDADES GENERALES
# ================================================================

def limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def a_float(valor, predeterminado=0.0):
    try:
        return float(valor)

    except (TypeError, ValueError):
        return float(predeterminado)


def a_entero(valor, predeterminado=0):
    try:
        return int(valor)

    except (TypeError, ValueError):
        return int(predeterminado)


def slug_texto(texto, limite=48):
    texto = str(texto or "sin_texto")

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "Ü": "U",
        "Ñ": "N"
    }

    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)

    texto = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        texto
    ).strip("_")

    return (texto or "sin_texto")[:limite]


def percentil(valores, proporcion):
    if not valores:
        return 0.0

    ordenados = sorted(valores)

    proporcion = limitar(
        proporcion,
        0.0,
        1.0
    )

    indice = int(
        round(
            (len(ordenados) - 1)
            * proporcion
        )
    )

    return float(
        ordenados[indice]
    )


def mediana_rgb(pixeles):
    if not pixeles:
        return None

    return (
        int(
            round(
                median(
                    pixel[0]
                    for pixel in pixeles
                )
            )
        ),
        int(
            round(
                median(
                    pixel[1]
                    for pixel in pixeles
                )
            )
        ),
        int(
            round(
                median(
                    pixel[2]
                    for pixel in pixeles
                )
            )
        )
    )


def rgb_a_hex(rgb):
    if rgb is None:
        return None

    return "#{:02X}{:02X}{:02X}".format(
        int(
            limitar(
                rgb[0],
                0,
                255
            )
        ),
        int(
            limitar(
                rgb[1],
                0,
                255
            )
        ),
        int(
            limitar(
                rgb[2],
                0,
                255
            )
        )
    )


def distancia_rgb(a, b):
    if a is None or b is None:
        return 0.0

    return math.sqrt(
        (a[0] - b[0]) ** 2
        + (a[1] - b[1]) ** 2
        + (a[2] - b[2]) ** 2
    )


def luminancia(rgb):
    if rgb is None:
        return 0.0

    return (
        0.2126 * rgb[0]
        + 0.7152 * rgb[1]
        + 0.0722 * rgb[2]
    )


def saturacion(rgb):
    if rgb is None:
        return 0.0

    _, s, _ = colorsys.rgb_to_hsv(
        rgb[0] / 255.0,
        rgb[1] / 255.0,
        rgb[2] / 255.0
    )

    return s * 255.0


# ================================================================
# CAJAS Y GEOMETRÍA
# ================================================================

def normalizar_caja(caja):
    if not isinstance(caja, dict):
        return None

    x0 = a_float(
        caja.get("x0")
    )

    y0 = a_float(
        caja.get(
            "top",
            caja.get("y0")
        )
    )

    x1 = a_float(
        caja.get("x1")
    )

    y1 = a_float(
        caja.get(
            "bottom",
            caja.get("y1")
        )
    )

    if x1 <= x0 or y1 <= y0:
        return None

    return {
        "x0": x0,
        "top": y0,
        "x1": x1,
        "bottom": y1,
        "ancho": x1 - x0,
        "alto": y1 - y0
    }


def solape_horizontal(caja_a, caja_b):
    if caja_a is None or caja_b is None:
        return 0.0

    interseccion = max(
        0.0,
        min(
            caja_a["x1"],
            caja_b["x1"]
        )
        - max(
            caja_a["x0"],
            caja_b["x0"]
        )
    )

    base = min(
        caja_a["ancho"],
        caja_b["ancho"]
    )

    if base <= 0:
        return 0.0

    return interseccion / base


def solape_vertical(caja_a, caja_b):
    if caja_a is None or caja_b is None:
        return 0.0

    interseccion = max(
        0.0,
        min(
            caja_a["bottom"],
            caja_b["bottom"]
        )
        - max(
            caja_a["top"],
            caja_b["top"]
        )
    )

    base = min(
        caja_a["alto"],
        caja_b["alto"]
    )

    if base <= 0:
        return 0.0

    return interseccion / base


def distancia_vertical(caja_a, caja_b):
    if caja_a is None or caja_b is None:
        return float("inf")

    if caja_a["bottom"] < caja_b["top"]:
        return (
            caja_b["top"]
            - caja_a["bottom"]
        )

    if caja_b["bottom"] < caja_a["top"]:
        return (
            caja_a["top"]
            - caja_b["bottom"]
        )

    return 0.0


# ================================================================
# RESOLUCIÓN DE ARCHIVOS
# ================================================================

def resolver_pdf(ruta_argumento=None):
    if ruta_argumento:
        ruta = (
            Path(ruta_argumento)
            .expanduser()
            .resolve()
        )

        if not ruta.is_file():
            raise FileNotFoundError(
                f"No existe el PDF indicado: {ruta}"
            )

        if ruta.suffix.lower() != ".pdf":
            raise ValueError(
                "El archivo indicado no es un PDF."
            )

        return ruta

    CARPETA_ENTRADA.mkdir(
        parents=True,
        exist_ok=True
    )

    candidatos = sorted(
        CARPETA_ENTRADA.glob("*.pdf")
    )

    if not candidatos:
        candidatos = sorted(
            CARPETA_BASE.glob("*.pdf")
        )

    if not candidatos:
        raise FileNotFoundError(
            (
                "No encontré ningún PDF en 'entrada' "
                "ni en la carpeta del prototipo."
            )
        )

    return candidatos[0]


def resolver_distribucion(ruta_argumento=None):
    ruta = (
        Path(ruta_argumento)
        .expanduser()
        .resolve()
        if ruta_argumento
        else RUTA_DISTRIBUCION_PREDETERMINADA
    )

    if not ruta.is_file():
        raise FileNotFoundError(
            (
                "No existe distribucion_pdf.json: "
                f"{ruta}"
            )
        )

    return ruta


def obtener_paginas(datos):
    if isinstance(datos, list):
        return datos

    if not isinstance(datos, dict):
        return []

    for clave in (
        "paginas",
        "pages"
    ):
        valor = datos.get(clave)

        if isinstance(valor, list):
            return valor

    return []


# ================================================================
# SELECCIÓN DE TEXTO DECORATIVO
# ================================================================

def obtener_tamano_fuente(elemento):
    estilo = elemento.get(
        "estilo",
        {}
    )

    if (
        isinstance(estilo, dict)
        and estilo.get("tamano") is not None
    ):
        return a_float(
            estilo.get("tamano")
        )

    return 0.0


def es_candidato_decorativo(
    elemento,
    numero_pagina
):
    if not isinstance(elemento, dict):
        return False

    texto = str(
        elemento.get(
            "texto",
            ""
        )
    ).strip()

    caja = normalizar_caja(
        elemento.get("caja")
    )

    if not texto or caja is None:
        return False

    tipo = str(
        elemento.get(
            "tipo",
            ""
        )
    ).lower()

    tamano = obtener_tamano_fuente(
        elemento
    )

    if (
        "titulo" in tipo
        or "encabezado" in tipo
    ):
        return True

    if (
        numero_pagina == 1
        and tamano >= TAMANO_MINIMO_FUENTE
    ):
        return True

    return False


def recolectar_candidatos(pagina):
    numero_pagina = a_entero(
        pagina.get("numero"),
        1
    )

    candidatos = []

    encabezado = pagina.get(
        "encabezado"
    )

    if es_candidato_decorativo(
        encabezado,
        numero_pagina
    ):
        candidatos.append(
            (
                "encabezado",
                encabezado
            )
        )

    for indice, elemento in enumerate(
        pagina.get(
            "elementos",
            []
        ),
        start=1
    ):
        if es_candidato_decorativo(
            elemento,
            numero_pagina
        ):
            candidatos.append(
                (
                    f"elemento_{indice:03d}",
                    elemento
                )
            )

    return candidatos


def recolectar_imagenes(pagina):
    recursos = pagina.get(
        "recursos_graficos",
        {}
    )

    if not isinstance(recursos, dict):
        return []

    imagenes = recursos.get(
        "imagenes",
        []
    )

    if not isinstance(imagenes, list):
        return []

    return imagenes


# ================================================================
# RENDER Y RECORTES
# ================================================================

def renderizar_pagina(
    documento,
    indice_pagina,
    escala
):
    pagina = documento[
        indice_pagina
    ]

    bitmap = pagina.render(
        scale=escala
    )

    imagen = (
        bitmap
        .to_pil()
        .convert("RGB")
    )

    return imagen


def caja_pdf_a_pixeles(
    caja,
    escala,
    ancho_imagen,
    alto_imagen,
    relleno_pt=0.0
):
    x0 = math.floor(
        (
            caja["x0"]
            - relleno_pt
        )
        * escala
    )

    y0 = math.floor(
        (
            caja["top"]
            - relleno_pt
        )
        * escala
    )

    x1 = math.ceil(
        (
            caja["x1"]
            + relleno_pt
        )
        * escala
    )

    y1 = math.ceil(
        (
            caja["bottom"]
            + relleno_pt
        )
        * escala
    )

    return (
        int(
            limitar(
                x0,
                0,
                ancho_imagen
            )
        ),
        int(
            limitar(
                y0,
                0,
                alto_imagen
            )
        ),
        int(
            limitar(
                x1,
                0,
                ancho_imagen
            )
        ),
        int(
            limitar(
                y1,
                0,
                alto_imagen
            )
        )
    )


def extraer_recorte(
    imagen_pagina,
    caja,
    escala
):
    ancho_imagen, alto_imagen = (
        imagen_pagina.size
    )

    x0, y0, x1, y1 = caja_pdf_a_pixeles(
        caja,
        escala,
        ancho_imagen,
        alto_imagen,
        RELLENO_RECORTE_PT
    )

    recorte = imagen_pagina.crop(
        (
            x0,
            y0,
            x1,
            y1
        )
    )

    objetivo_local = {
        "x0": int(
            round(
                caja["x0"]
                * escala
                - x0
            )
        ),
        "top": int(
            round(
                caja["top"]
                * escala
                - y0
            )
        ),
        "x1": int(
            round(
                caja["x1"]
                * escala
                - x0
            )
        ),
        "bottom": int(
            round(
                caja["bottom"]
                * escala
                - y0
            )
        )
    }

    return (
        recorte,
        objetivo_local
    )


# ================================================================
# ESTIMACIÓN DEL FONDO
# ================================================================

def obtener_pixeles_fondo(
    recorte,
    objetivo_local
):
    ancho, alto = recorte.size

    paso = max(
        1,
        int(
            round(
                min(
                    ancho,
                    alto
                )
                / 180.0
            )
        )
    )

    margen = max(
        3,
        int(
            round(
                min(
                    ancho,
                    alto
                )
                * 0.06
            )
        )
    )

    x0 = objetivo_local["x0"]
    y0 = objetivo_local["top"]
    x1 = objetivo_local["x1"]
    y1 = objetivo_local["bottom"]

    pixeles = []

    for y in range(
        0,
        alto,
        paso
    ):
        for x in range(
            0,
            ancho,
            paso
        ):
            fuera_objetivo = (
                x < x0
                or x >= x1
                or y < y0
                or y >= y1
            )

            cerca_borde = (
                x < margen
                or x >= ancho - margen
                or y < margen
                or y >= alto - margen
            )

            if (
                fuera_objetivo
                and cerca_borde
            ):
                pixeles.append(
                    recorte.getpixel(
                        (
                            x,
                            y
                        )
                    )[:3]
                )

    if not pixeles:
        for x in range(
            0,
            ancho,
            paso
        ):
            pixeles.append(
                recorte.getpixel(
                    (
                        x,
                        0
                    )
                )[:3]
            )

            pixeles.append(
                recorte.getpixel(
                    (
                        x,
                        alto - 1
                    )
                )[:3]
            )

    return pixeles


# ================================================================
# ANÁLISIS VISUAL DE TEXTO
# ================================================================

def analizar_pixeles_texto(
    recorte,
    objetivo_local
):
    pixeles_fondo = obtener_pixeles_fondo(
        recorte,
        objetivo_local
    )

    color_fondo = (
        mediana_rgb(
            pixeles_fondo
        )
        or (
            255,
            255,
            255
        )
    )

    ruido_fondo = [
        distancia_rgb(
            pixel,
            color_fondo
        )
        for pixel in pixeles_fondo
    ]

    umbral_foreground = max(
        DIFERENCIA_MINIMA_FOREGROUND,
        percentil(
            ruido_fondo,
            0.95
        )
        + 10.0
    )

    x0 = int(
        limitar(
            objetivo_local["x0"],
            0,
            recorte.width
        )
    )

    y0 = int(
        limitar(
            objetivo_local["top"],
            0,
            recorte.height
        )
    )

    x1 = int(
        limitar(
            objetivo_local["x1"],
            0,
            recorte.width
        )
    )

    y1 = int(
        limitar(
            objetivo_local["bottom"],
            0,
            recorte.height
        )
    )

    ancho_objetivo = max(
        1,
        x1 - x0
    )

    alto_objetivo = max(
        1,
        y1 - y0
    )

    paso = max(
        1,
        int(
            round(
                max(
                    ancho_objetivo,
                    alto_objetivo
                )
                / 800.0
            )
        )
    )

    foreground = []
    foreground_saturado = []

    por_banda = {
        "superior": [],
        "centro": [],
        "inferior": []
    }

    por_banda_saturado = {
        "superior": [],
        "centro": [],
        "inferior": []
    }

    mascara = Image.new(
        "RGBA",
        recorte.size,
        (
            255,
            255,
            255,
            255
        )
    )

    pixeles_mascara = (
        mascara.load()
    )

    for y in range(
        y0,
        y1,
        paso
    ):
        proporcion_y = (
            (
                y
                - y0
            )
            / max(
                1,
                alto_objetivo - 1
            )
        )

        if proporcion_y < 0.34:
            banda = "superior"

        elif proporcion_y < 0.67:
            banda = "centro"

        else:
            banda = "inferior"

        for x in range(
            x0,
            x1,
            paso
        ):
            pixel = recorte.getpixel(
                (
                    x,
                    y
                )
            )[:3]

            if (
                distancia_rgb(
                    pixel,
                    color_fondo
                )
                < umbral_foreground
            ):
                continue

            registro = (
                pixel[0],
                pixel[1],
                pixel[2]
            )

            foreground.append(
                registro
            )

            por_banda[
                banda
            ].append(
                registro
            )

            if (
                saturacion(
                    registro
                )
                >= SATURACION_MINIMA_COLOR
            ):
                foreground_saturado.append(
                    registro
                )

                por_banda_saturado[
                    banda
                ].append(
                    registro
                )

            for dy in range(paso):
                for dx in range(paso):
                    xx = x + dx
                    yy = y + dy

                    if (
                        xx < mascara.width
                        and yy < mascara.height
                    ):
                        pixeles_mascara[
                            xx,
                            yy
                        ] = (
                            registro[0],
                            registro[1],
                            registro[2],
                            255
                        )

    usar_saturados = (
        len(
            foreground_saturado
        )
        >= 80
        and len(
            foreground_saturado
        )
        >= len(
            foreground
        )
        * 0.04
    )

    base_color = (
        foreground_saturado
        if usar_saturados
        else foreground
    )

    color_principal = mediana_rgb(
        base_color
    )

    colores_banda = {}
    cantidades_banda = {}

    for banda in (
        "superior",
        "centro",
        "inferior"
    ):
        if (
            usar_saturados
            and len(
                por_banda_saturado[
                    banda
                ]
            )
            >= 12
        ):
            base_banda = (
                por_banda_saturado[
                    banda
                ]
            )

        else:
            base_banda = (
                por_banda[
                    banda
                ]
            )

        colores_banda[
            banda
        ] = mediana_rgb(
            base_banda
        )

        cantidades_banda[
            banda
        ] = len(
            base_banda
        )

    colores_validos = [
        color
        for color in colores_banda.values()
        if color is not None
    ]

    variacion_maxima = 0.0

    for indice, color_a in enumerate(
        colores_validos
    ):
        for color_b in colores_validos[
            indice + 1:
        ]:
            variacion_maxima = max(
                variacion_maxima,
                distancia_rgb(
                    color_a,
                    color_b
                )
            )

    degradado_probable = (
        len(
            colores_validos
        )
        >= 2
        and variacion_maxima
        >= DIFERENCIA_MINIMA_DEGRADADO
        and len(
            foreground
        )
        >= 100
    )

    if degradado_probable:
        tipo_relleno = (
            "degradado_vertical_probable"
        )

    elif color_principal is not None:
        tipo_relleno = (
            "color_solido_probable"
        )

    else:
        tipo_relleno = (
            "no_concluyente"
        )

    stops = []

    for posicion, banda in (
        (
            0,
            "superior"
        ),
        (
            50000,
            "centro"
        ),
        (
            100000,
            "inferior"
        )
    ):
        color = (
            colores_banda.get(
                banda
            )
            or color_principal
        )

        stops.append(
            {
                "pos": posicion,
                "rgb": (
                    list(color)
                    if color is not None
                    else None
                ),
                "hex": rgb_a_hex(
                    color
                )
            }
        )

    return {
        "color_fondo_rgb": (
            list(
                color_fondo
            )
        ),
        "color_fondo_hex": (
            rgb_a_hex(
                color_fondo
            )
        ),
        "umbral_foreground": (
            round(
                umbral_foreground,
                3
            )
        ),
        "cantidad_pixeles_foreground": (
            len(
                foreground
            )
        ),
        "cantidad_pixeles_saturados": (
            len(
                foreground_saturado
            )
        ),
        "se_priorizaron_pixeles_saturados": (
            usar_saturados
        ),
        "color_principal_rgb": (
            list(
                color_principal
            )
            if color_principal is not None
            else None
        ),
        "color_principal_hex": (
            rgb_a_hex(
                color_principal
            )
        ),
        "luminancia_principal": (
            round(
                luminancia(
                    color_principal
                ),
                3
            )
            if color_principal is not None
            else None
        ),
        "saturacion_principal": (
            round(
                saturacion(
                    color_principal
                ),
                3
            )
            if color_principal is not None
            else None
        ),
        "colores_bandas": {
            banda: {
                "rgb": (
                    list(
                        colores_banda[
                            banda
                        ]
                    )
                    if colores_banda[
                        banda
                    ]
                    is not None
                    else None
                ),
                "hex": (
                    rgb_a_hex(
                        colores_banda[
                            banda
                        ]
                    )
                ),
                "cantidad": (
                    cantidades_banda[
                        banda
                    ]
                )
            }
            for banda in (
                "superior",
                "centro",
                "inferior"
            )
        },
        "variacion_rgb_maxima": (
            round(
                variacion_maxima,
                3
            )
        ),
        "tipo_relleno": (
            tipo_relleno
        ),
        "degradado_probable": (
            degradado_probable
        ),
        "direccion_degradado": (
            "vertical"
            if degradado_probable
            else None
        ),
        "stops_sugeridos": (
            stops
        ),
        "mascara": (
            mascara
        )
    }


# ================================================================
# ANÁLISIS DE XOBJECTS EXTRAÍDOS
# ================================================================

def analizar_archivo_imagen(ruta):
    if not ruta:
        return None

    ruta = Path(
        ruta
    )

    if not ruta.is_file():
        return None

    try:
        with Image.open(
            ruta
        ) as imagen:
            imagen_original = (
                imagen.copy()
            )

    except Exception:
        return None

    tiene_alpha = (
        "A"
        in imagen_original.getbands()
    )

    rgba = imagen_original.convert(
        "RGBA"
    )

    pixeles = []
    pixeles_saturados = []
    alpha_valores = []

    bandas = {
        "superior": [],
        "centro": [],
        "inferior": []
    }

    paso = max(
        1,
        int(
            round(
                max(
                    rgba.width,
                    rgba.height
                )
                / 500.0
            )
        )
    )

    for y in range(
        0,
        rgba.height,
        paso
    ):
        proporcion_y = (
            y
            / max(
                1,
                rgba.height - 1
            )
        )

        if proporcion_y < 0.34:
            banda = "superior"

        elif proporcion_y < 0.67:
            banda = "centro"

        else:
            banda = "inferior"

        for x in range(
            0,
            rgba.width,
            paso
        ):
            r, g, b, a = rgba.getpixel(
                (
                    x,
                    y
                )
            )

            alpha_valores.append(
                a
            )

            if a < 20:
                continue

            rgb = (
                r,
                g,
                b
            )

            if (
                luminancia(
                    rgb
                )
                > 248
                and saturacion(
                    rgb
                )
                < 12
            ):
                continue

            pixeles.append(
                rgb
            )

            bandas[
                banda
            ].append(
                rgb
            )

            if (
                saturacion(
                    rgb
                )
                >= SATURACION_MINIMA_COLOR
            ):
                pixeles_saturados.append(
                    rgb
                )

    usar_saturados = (
        len(
            pixeles_saturados
        )
        >= 40
        and len(
            pixeles_saturados
        )
        >= len(
            pixeles
        )
        * 0.03
    )

    color = mediana_rgb(
        pixeles_saturados
        if usar_saturados
        else pixeles
    )

    colores_banda = {
        nombre: mediana_rgb(
            valores
        )
        for nombre, valores in bandas.items()
    }

    return {
        "ruta": str(
            ruta
        ),
        "ancho_px": (
            rgba.width
        ),
        "alto_px": (
            rgba.height
        ),
        "modo_original": (
            imagen_original.mode
        ),
        "tiene_alpha": (
            tiene_alpha
        ),
        "alpha_min": (
            min(
                alpha_valores
            )
            if alpha_valores
            else None
        ),
        "alpha_max": (
            max(
                alpha_valores
            )
            if alpha_valores
            else None
        ),
        "color_principal_rgb": (
            list(
                color
            )
            if color
            else None
        ),
        "color_principal_hex": (
            rgb_a_hex(
                color
            )
        ),
        "se_priorizaron_pixeles_saturados": (
            usar_saturados
        ),
        "colores_bandas": {
            nombre: {
                "rgb": (
                    list(
                        valor
                    )
                    if valor
                    else None
                ),
                "hex": (
                    rgb_a_hex(
                        valor
                    )
                )
            }
            for nombre, valor in colores_banda.items()
        }
    }


# ================================================================
# ASOCIACIÓN TEXTO - IMAGEN
# ================================================================

def calcular_asociacion(
    caja_texto,
    imagen
):
    caja_imagen = normalizar_caja(
        imagen.get("caja")
    )

    if caja_imagen is None:
        return None

    solape_h = solape_horizontal(
        caja_texto,
        caja_imagen
    )

    solape_v = solape_vertical(
        caja_texto,
        caja_imagen
    )

    distancia_v = distancia_vertical(
        caja_texto,
        caja_imagen
    )

    rol = str(
        imagen.get(
            "rol_estimado",
            ""
        )
    ).lower()

    es_imagen_efecto = (
        "efecto"
        in rol
    )

    limite_distancia = max(
        DISTANCIA_VERTICAL_MAXIMA_EFECTO_PT,
        caja_texto["alto"]
        * 0.8
    )

    asociada = (
        solape_h
        >= SOLAPE_HORIZONTAL_MINIMO_EFECTO
        and (
            distancia_v
            <= limite_distancia
            or solape_v
            > 0.0
        )
        and (
            es_imagen_efecto
            or caja_imagen["ancho"]
            >= caja_texto["ancho"]
            * 0.65
        )
    )

    centro_texto_y = (
        caja_texto["top"]
        + caja_texto["bottom"]
    ) / 2.0

    centro_imagen_y = (
        caja_imagen["top"]
        + caja_imagen["bottom"]
    ) / 2.0

    reflejo_probable = (
        asociada
        and solape_h >= 0.6
        and centro_imagen_y
        > centro_texto_y
        and caja_imagen["bottom"]
        > caja_texto["bottom"]
    )

    puntuacion = (
        solape_h * 0.55
        + min(
            1.0,
            solape_v
        ) * 0.20
        + (
            0.15
            if es_imagen_efecto
            else 0.0
        )
        + (
            0.10
            if reflejo_probable
            else 0.0
        )
    )

    return {
        "asociada": (
            asociada
        ),
        "reflejo_probable": (
            reflejo_probable
        ),
        "puntuacion": (
            round(
                puntuacion,
                4
            )
        ),
        "solape_horizontal": (
            round(
                solape_h,
                4
            )
        ),
        "solape_vertical": (
            round(
                solape_v,
                4
            )
        ),
        "distancia_vertical_pt": (
            round(
                distancia_v,
                3
            )
        ),
        "caja_imagen": {
            "x0": (
                caja_imagen["x0"]
            ),
            "top": (
                caja_imagen["top"]
            ),
            "x1": (
                caja_imagen["x1"]
            ),
            "bottom": (
                caja_imagen["bottom"]
            )
        }
    }


# ================================================================
# ANÁLISIS DE UN CANDIDATO
# ================================================================

def analizar_candidato(
    imagen_pagina,
    escala,
    pagina,
    identificador,
    elemento
):
    numero_pagina = a_entero(
        pagina.get("numero"),
        1
    )

    caja = normalizar_caja(
        elemento.get("caja")
    )

    texto = str(
        elemento.get(
            "texto",
            ""
        )
    ).strip()

    recorte, objetivo_local = (
        extraer_recorte(
            imagen_pagina,
            caja,
            escala
        )
    )

    analisis_visual = (
        analizar_pixeles_texto(
            recorte,
            objetivo_local
        )
    )

    nombre_base = (
        f"p{numero_pagina:03d}_"
        f"{identificador}_"
        f"{slug_texto(texto)}"
    )

    ruta_recorte = (
        CARPETA_DIAGNOSTICO
        / f"{nombre_base}_recorte.png"
    )

    ruta_mascara = (
        CARPETA_DIAGNOSTICO
        / f"{nombre_base}_mascara.png"
    )

    recorte.save(
        ruta_recorte
    )

    mascara = analisis_visual.pop(
        "mascara"
    )

    mascara.save(
        ruta_mascara
    )

    asociaciones = []

    for imagen in recolectar_imagenes(
        pagina
    ):
        asociacion = calcular_asociacion(
            caja,
            imagen
        )

        if (
            asociacion is None
            or not asociacion["asociada"]
        ):
            continue

        ruta_imagen = imagen.get(
            "archivo_extraido"
        )

        asociaciones.append(
            {
                "nombre": (
                    imagen.get("nombre")
                ),
                "rol_estimado": (
                    imagen.get(
                        "rol_estimado"
                    )
                ),
                "archivo_extraido": (
                    ruta_imagen
                ),
                "ancho_pixeles": (
                    imagen.get(
                        "ancho_pixeles"
                    )
                ),
                "alto_pixeles": (
                    imagen.get(
                        "alto_pixeles"
                    )
                ),
                **asociacion,
                "analisis_imagen": (
                    analizar_archivo_imagen(
                        ruta_imagen
                    )
                )
            }
        )

    asociaciones.sort(
        key=lambda item: (
            item.get(
                "puntuacion",
                0.0
            )
        ),
        reverse=True
    )

    return {
        "id": (
            identificador
        ),
        "pagina": (
            numero_pagina
        ),
        "tipo": (
            elemento.get("tipo")
        ),
        "texto": (
            texto
        ),
        "caja": {
            "x0": caja["x0"],
            "top": caja["top"],
            "x1": caja["x1"],
            "bottom": caja["bottom"]
        },
        "estilo_pdf_extraido": (
            elemento.get("estilo")
        ),
        "analisis_visual": (
            analisis_visual
        ),
        "efecto_grafico_probable": (
            bool(
                asociaciones
            )
        ),
        "reflejo_probable": (
            any(
                item.get(
                    "reflejo_probable"
                )
                for item in asociaciones
            )
        ),
        "imagenes_asociadas": (
            asociaciones
        ),
        "diagnostico": {
            "recorte": (
                str(
                    ruta_recorte
                )
            ),
            "mascara": (
                str(
                    ruta_mascara
                )
            )
        }
    }


# ================================================================
# PREPARAR SALIDA
# ================================================================

def preparar_salida():
    if CARPETA_DIAGNOSTICO.exists():
        shutil.rmtree(
            CARPETA_DIAGNOSTICO
        )

    CARPETA_DIAGNOSTICO.mkdir(
        parents=True,
        exist_ok=True
    )

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True
    )


# ================================================================
# RESUMEN DE TEXTO
# ================================================================

def guardar_resumen(datos):
    lineas = [
        "PROTOTIPO PDF → DOCX",
        "ANÁLISIS VISUAL DE EFECTOS DE TEXTO DEL PDF",
        "=" * 84,
        "",
        f"PDF: {datos['pdf']}",
        f"Distribución: {datos['distribucion']}",
        f"Escala de render: {datos['escala_render']}",
        (
            "Candidatos analizados: "
            f"{len(datos['candidatos'])}"
        ),
        ""
    ]

    for candidato in datos[
        "candidatos"
    ]:
        lineas.extend(
            [
                "-" * 84,
                (
                    f"Página "
                    f"{candidato.get('pagina')} | "
                    f"{candidato.get('id')}"
                ),
                (
                    "Tipo: "
                    f"{candidato.get('tipo')}"
                ),
                (
                    "Texto: "
                    f"{candidato.get('texto')}"
                )
            ]
        )

        if candidato.get("error"):
            lineas.extend(
                [
                    (
                        "ERROR: "
                        f"{candidato['error']}"
                    ),
                    ""
                ]
            )

            continue

        visual = candidato.get(
            "analisis_visual",
            {}
        )

        lineas.extend(
            [
                (
                    "Caja: "
                    f"{candidato.get('caja')}"
                ),
                (
                    "Estilo PDF extraído: "
                    f"{candidato.get('estilo_pdf_extraido')}"
                ),
                (
                    "Color visual principal: "
                    f"{visual.get('color_principal_hex')} "
                    f"{visual.get('color_principal_rgb')}"
                ),
                (
                    "Relleno visual: "
                    f"{visual.get('tipo_relleno')}"
                ),
                (
                    "Variación RGB: "
                    f"{visual.get('variacion_rgb_maxima')}"
                ),
                (
                    "Stops sugeridos: "
                    f"{visual.get('stops_sugeridos')}"
                ),
                (
                    "Efecto gráfico asociado: "
                    f"{candidato.get('efecto_grafico_probable')}"
                ),
                (
                    "Reflejo probable: "
                    f"{candidato.get('reflejo_probable')}"
                )
            ]
        )

        for asociacion in candidato.get(
            "imagenes_asociadas",
            []
        ):
            lineas.append(
                (
                    "  Imagen asociada: "
                    f"{asociacion.get('nombre')} | "
                    f"rol={asociacion.get('rol_estimado')} | "
                    "solape_h="
                    f"{asociacion.get('solape_horizontal')} | "
                    "solape_v="
                    f"{asociacion.get('solape_vertical')} | "
                    "dist_v="
                    f"{asociacion.get('distancia_vertical_pt')} pt | "
                    "reflejo="
                    f"{asociacion.get('reflejo_probable')}"
                )
            )

            analisis_imagen = (
                asociacion.get(
                    "analisis_imagen"
                )
            )

            if analisis_imagen:
                lineas.append(
                    (
                        "    Color imagen: "
                        f"{analisis_imagen.get('color_principal_hex')} | "
                        "bandas="
                        f"{analisis_imagen.get('colores_bandas')}"
                    )
                )

        lineas.extend(
            [
                (
                    "Recorte: "
                    f"{candidato['diagnostico']['recorte']}"
                ),
                (
                    "Máscara: "
                    f"{candidato['diagnostico']['mascara']}"
                ),
                ""
            ]
        )

    RUTA_RESUMEN_SALIDA.write_text(
        "\n".join(
            lineas
        ),
        encoding="utf-8"
    )


# ================================================================
# EJECUCIÓN PRINCIPAL
# ================================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Analiza títulos y encabezados del PDF "
            "para detectar colores visuales, degradados "
            "y posibles reflejos."
        )
    )

    parser.add_argument(
        "pdf",
        nargs="?",
        help=(
            "Ruta al PDF. Si se omite, usa el primer "
            "PDF de la carpeta 'entrada'."
        )
    )

    parser.add_argument(
        "--distribucion",
        help=(
            "Ruta a distribucion_pdf.json. Si se omite, "
            "usa salida/distribucion_pdf.json."
        )
    )

    parser.add_argument(
        "--escala",
        type=float,
        default=ESCALA_RENDER_PREDETERMINADA,
        help=(
            "Escala de render. "
            "Predeterminado: 4.0"
        )
    )

    argumentos = parser.parse_args()

    if argumentos.escala < 1.0:
        raise ValueError(
            "La escala debe ser al menos 1.0."
        )

    ruta_pdf = resolver_pdf(
        argumentos.pdf
    )

    ruta_distribucion = (
        resolver_distribucion(
            argumentos.distribucion
        )
    )

    with open(
        ruta_distribucion,
        "r",
        encoding="utf-8"
    ) as archivo:
        distribucion = json.load(
            archivo
        )

    paginas = obtener_paginas(
        distribucion
    )

    if not paginas:
        raise ValueError(
            (
                "No encontré la lista de páginas "
                "dentro de distribucion_pdf.json."
            )
        )

    preparar_salida()

    documento = pdfium.PdfDocument(
        str(
            ruta_pdf
        )
    )

    resultados = []

    try:
        for pagina in paginas:
            numero_pagina = a_entero(
                pagina.get("numero"),
                1
            )

            indice_pagina = (
                numero_pagina
                - 1
            )

            if (
                indice_pagina < 0
                or indice_pagina
                >= len(documento)
            ):
                continue

            candidatos = recolectar_candidatos(
                pagina
            )

            if not candidatos:
                continue

            print(
                (
                    "Analizando efectos visuales "
                    f"de la página {numero_pagina}..."
                )
            )

            imagen_pagina = renderizar_pagina(
                documento,
                indice_pagina,
                argumentos.escala
            )

            for identificador, elemento in candidatos:
                try:
                    resultados.append(
                        analizar_candidato(
                            imagen_pagina,
                            argumentos.escala,
                            pagina,
                            identificador,
                            elemento
                        )
                    )

                except Exception as error:
                    resultados.append(
                        {
                            "id": (
                                identificador
                            ),
                            "pagina": (
                                numero_pagina
                            ),
                            "tipo": (
                                elemento.get(
                                    "tipo"
                                )
                            ),
                            "texto": (
                                elemento.get(
                                    "texto"
                                )
                            ),
                            "error": (
                                f"{type(error).__name__}: "
                                f"{error}"
                            )
                        }
                    )

    finally:
        documento.close()

    datos_salida = {
        "pdf": str(
            ruta_pdf
        ),
        "distribucion": str(
            ruta_distribucion
        ),
        "escala_render": (
            argumentos.escala
        ),
        "candidatos": (
            resultados
        )
    }

    with open(
        RUTA_JSON_SALIDA,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            datos_salida,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    guardar_resumen(
        datos_salida
    )

    print()
    print(
        "Análisis de efectos terminado."
    )
    print(
        f"JSON: {RUTA_JSON_SALIDA}"
    )
    print(
        f"Resumen: {RUTA_RESUMEN_SALIDA}"
    )
    print(
        f"Diagnóstico visual: {CARPETA_DIAGNOSTICO}"
    )
    print()


if __name__ == "__main__":
    main()