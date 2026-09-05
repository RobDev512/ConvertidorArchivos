import argparse
import json
import math
import re
import statistics

from collections import Counter
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium

from PIL import ImageDraw

from modelo_documento import (
    BordePaginaPDF,
    Caja,
    DistanciasEncabezadoPiePDF,
    DocumentoPDF,
    FondoPaginaPDF,
    FragmentoTextoPDF,
    ImagenPDF,
    LadoBordePDF,
    LineaTextoPDF,
    LineaVectorialPDF,
    MargenesPaginaPDF,
    PaginaPDF,
    PalabraPDF,
    RectanguloPDF,
    convertir_a_diccionario
)


# ================================================================
# RUTAS
# ================================================================

CARPETA_BASE = Path(
    __file__
).resolve().parent

CARPETA_ENTRADA = (
    CARPETA_BASE
    / "entrada"
)

CARPETA_SALIDA = (
    CARPETA_BASE
    / "salida"
)

CARPETA_DIAGNOSTICO = (
    CARPETA_SALIDA
    / "diagnostico"
)


# ================================================================
# UTILIDADES GENERALES
# ================================================================
def redondear(
    valor,
    decimales=3
):

    if valor is None:

        return 0.0


    try:

        return round(
            float(
                valor
            ),
            decimales
        )


    except (
        TypeError,
        ValueError
    ):

        return 0.0


# ================================================================
# NORMALIZAR VALOR
# ================================================================
def normalizar_valor(
    valor
):

    if (
        valor is None
        or isinstance(
            valor,
            (
                str,
                int,
                float,
                bool
            )
        )
    ):

        return valor


    if isinstance(
        valor,
        (
            list,
            tuple
        )
    ):

        return [
            normalizar_valor(
                item
            )
            for item in valor
        ]


    if isinstance(
        valor,
        dict
    ):

        return {
            str(
                clave
            ): normalizar_valor(
                contenido
            )
            for clave, contenido
            in valor.items()
        }


    return str(
        valor
    )


# ================================================================
# LIMPIAR NOMBRE DE FUENTE
# ================================================================
def limpiar_nombre_fuente(
    nombre
):

    if not nombre:

        return ""


    nombre = str(
        nombre
    ).strip()


    return re.sub(
        r"^[A-Z]{6}\+",
        "",
        nombre
    )


# ================================================================
# DETECTAR NEGRITA
# ================================================================
def es_negrita(
    nombre_fuente
):

    nombre = limpiar_nombre_fuente(
        nombre_fuente
    ).lower()


    indicadores = (
        "bold",
        "black",
        "heavy",
        "semibold",
        "semi-bold",
        "demibold",
        "demi-bold"
    )


    return any(
        indicador in nombre
        for indicador in indicadores
    )


# ================================================================
# DETECTAR CURSIVA
# ================================================================
def es_cursiva(
    nombre_fuente
):

    nombre = limpiar_nombre_fuente(
        nombre_fuente
    ).lower()


    indicadores = (
        "italic",
        "oblique"
    )


    return any(
        indicador in nombre
        for indicador in indicadores
    )


# ================================================================
# CREAR CLAVE COMPARABLE
# ================================================================
def crear_clave_valor(
    valor
):

    try:

        return json.dumps(
            normalizar_valor(
                valor
            ),
            ensure_ascii=False,
            sort_keys=True
        )


    except Exception:

        return repr(
            valor
        )


# ================================================================
# VALOR MÁS FRECUENTE
# ================================================================
def valor_mas_frecuente(
    valores,
    predeterminado=None
):

    contador = Counter()

    originales = {}


    for valor in valores:

        if valor is None:

            continue


        clave = crear_clave_valor(
            valor
        )


        contador[
            clave
        ] += 1


        if clave not in originales:

            originales[
                clave
            ] = valor


    if not contador:

        return predeterminado


    clave = contador.most_common(
        1
    )[0][0]


    return originales[
        clave
    ]


# ================================================================
# NORMALIZAR TEXTO REPETIDO
# ================================================================
def normalizar_texto_repetido(
    texto
):

    texto = str(
        texto
    ).lower().strip()


    texto = re.sub(
        r"\d+",
        "#",
        texto
    )


    texto = re.sub(
        r"\s+",
        " ",
        texto
    )


    return texto.strip()


# ================================================================
# FORMATEAR VALOR
# ================================================================
def formatear_valor(
    valor
):

    if valor is None:

        return "—"


    if isinstance(
        valor,
        float
    ):

        return (
            f"{valor:.2f}"
        )


    return str(
        valor
    )


# ================================================================
# RESOLVER PDF DE ENTRADA
# ================================================================
def resolver_pdf_entrada(
    ruta_argumento=None
):

    # ----------------------------------- #
    #        Ruta proporcionada           #
    # ----------------------------------- #

    if ruta_argumento:

        ruta = (
            Path(
                ruta_argumento
            )
            .expanduser()
            .resolve()
        )


        if not ruta.is_file():

            raise FileNotFoundError(
                (
                    "No existe el PDF indicado: "
                    f"{ruta}"
                )
            )


        if ruta.suffix.lower() != ".pdf":

            raise ValueError(
                "El archivo indicado no es un PDF."
            )


        return ruta


    # ----------------------------------- #
    #       Buscar dentro de entrada      #
    # ----------------------------------- #

    CARPETA_ENTRADA.mkdir(
        parents=True,
        exist_ok=True
    )


    archivos_pdf = sorted(
        CARPETA_ENTRADA.glob(
            "*.pdf"
        )
    )


    if not archivos_pdf:

        raise FileNotFoundError(
            (
                "No encontré ningún PDF dentro "
                "de la carpeta 'entrada'."
            )
        )


    if len(
        archivos_pdf
    ) > 1:

        print(
            (
                "Hay varios PDFs en 'entrada'. "
                "Se analizará: "
                f"{archivos_pdf[0].name}"
            )
        )


    return archivos_pdf[
        0
    ]


# ================================================================
# OBTENER CARACTERES DE UNA PALABRA
# ================================================================
def obtener_caracteres_palabra(
    palabra,
    caracteres
):

    x0 = float(
        palabra.get(
            "x0",
            0.0
        )
    )

    x1 = float(
        palabra.get(
            "x1",
            0.0
        )
    )

    top = float(
        palabra.get(
            "top",
            0.0
        )
    )

    bottom = float(
        palabra.get(
            "bottom",
            0.0
        )
    )


    resultado = []


    for caracter in caracteres:

        try:

            caracter_x0 = float(
                caracter.get(
                    "x0",
                    0.0
                )
            )

            caracter_x1 = float(
                caracter.get(
                    "x1",
                    0.0
                )
            )

            caracter_top = float(
                caracter.get(
                    "top",
                    0.0
                )
            )

            caracter_bottom = float(
                caracter.get(
                    "bottom",
                    0.0
                )
            )


        except (
            TypeError,
            ValueError
        ):

            continue


        centro_x = (
            caracter_x0
            + caracter_x1
        ) / 2


        centro_y = (
            caracter_top
            + caracter_bottom
        ) / 2


        if (
            x0 - 0.8
            <= centro_x
            <= x1 + 0.8

            and top - 1.5
            <= centro_y
            <= bottom + 1.5
        ):

            resultado.append(
                caracter
            )


    return sorted(
        resultado,
        key=lambda caracter: float(
            caracter.get(
                "x0",
                0.0
            )
        )
    )


# ================================================================
# CLAVE DE ESTILO DE CARÁCTER
# ================================================================
def crear_clave_estilo_caracter(
    caracter
):

    fuente = limpiar_nombre_fuente(
        caracter.get(
            "fontname"
        )
    )


    tamano = redondear(
        caracter.get(
            "size"
        ),
        2
    )


    color = normalizar_valor(
        caracter.get(
            "non_stroking_color"
        )
    )


    return (
        fuente,
        tamano,
        crear_clave_valor(
            color
        ),
        es_negrita(
            fuente
        ),
        es_cursiva(
            fuente
        )
    )


# ================================================================
# CREAR FRAGMENTO DE TEXTO
# ================================================================
def crear_fragmento(
    caracteres
):

    texto = "".join(
        str(
            caracter.get(
                "text",
                ""
            )
        )
        for caracter in caracteres
    )


    fuente = limpiar_nombre_fuente(
        caracteres[
            0
        ].get(
            "fontname"
        )
    )


    tamanos = []


    for caracter in caracteres:

        try:

            tamano = float(
                caracter.get(
                    "size",
                    0.0
                )
            )


            if tamano > 0:

                tamanos.append(
                    tamano
                )


        except (
            TypeError,
            ValueError
        ):

            pass


    if tamanos:

        tamano_promedio = (
            statistics.mean(
                tamanos
            )
        )


    else:

        tamano_promedio = 0.0


    return FragmentoTextoPDF(
        texto=texto,

        caja=Caja(
            x0=min(
                redondear(
                    caracter.get(
                        "x0"
                    )
                )
                for caracter
                in caracteres
            ),

            top=min(
                redondear(
                    caracter.get(
                        "top"
                    )
                )
                for caracter
                in caracteres
            ),

            x1=max(
                redondear(
                    caracter.get(
                        "x1"
                    )
                )
                for caracter
                in caracteres
            ),

            bottom=max(
                redondear(
                    caracter.get(
                        "bottom"
                    )
                )
                for caracter
                in caracteres
            )
        ),

        fuente=fuente,

        tamano=redondear(
            tamano_promedio
        ),

        color=normalizar_valor(
            caracteres[
                0
            ].get(
                "non_stroking_color"
            )
        ),

        negrita=es_negrita(
            fuente
        ),

        cursiva=es_cursiva(
            fuente
        )
    )


# ================================================================
# CREAR FRAGMENTOS DE PALABRA
# ================================================================
def crear_fragmentos_palabra(
    caracteres
):

    if not caracteres:

        return []


    grupos = []

    grupo_actual = [
        caracteres[
            0
        ]
    ]


    clave_actual = (
        crear_clave_estilo_caracter(
            caracteres[
                0
            ]
        )
    )


    for caracter in caracteres[
        1:
    ]:

        clave = (
            crear_clave_estilo_caracter(
                caracter
            )
        )


        if clave == clave_actual:

            grupo_actual.append(
                caracter
            )


        else:

            grupos.append(
                grupo_actual
            )


            grupo_actual = [
                caracter
            ]


            clave_actual = clave


    grupos.append(
        grupo_actual
    )


    return [
        crear_fragmento(
            grupo
        )
        for grupo
        in grupos
    ]


# ================================================================
# OBTENER ESTILO DE FRAGMENTOS
# ================================================================
def obtener_estilo_fragmentos(
    fragmentos
):

    if not fragmentos:

        return {
            "fuente": "",
            "tamano": 0.0,
            "color": None,
            "negrita": False,
            "cursiva": False
        }


    pesos = [
        max(
            1,
            len(
                fragmento.texto
            )
        )
        for fragmento
        in fragmentos
    ]


    total_peso = sum(
        pesos
    )


    if total_peso:

        tamano = (
            sum(
                fragmento.tamano
                * peso
                for fragmento, peso
                in zip(
                    fragmentos,
                    pesos
                )
            )
            / total_peso
        )


    else:

        tamano = 0.0


    caracteres_negrita = sum(
        peso
        for fragmento, peso
        in zip(
            fragmentos,
            pesos
        )
        if fragmento.negrita
    )


    caracteres_cursiva = sum(
        peso
        for fragmento, peso
        in zip(
            fragmentos,
            pesos
        )
        if fragmento.cursiva
    )


    return {
        "fuente": valor_mas_frecuente(
            [
                fragmento.fuente
                for fragmento
                in fragmentos
            ],
            ""
        ),

        "tamano": tamano,

        "color": valor_mas_frecuente(
            [
                fragmento.color
                for fragmento
                in fragmentos
            ],
            None
        ),

        "negrita": (
            caracteres_negrita
            >= max(
                1,
                total_peso * 0.5
            )
        ),

        "cursiva": (
            caracteres_cursiva
            >= max(
                1,
                total_peso * 0.5
            )
        )
    }


# ================================================================
# EXTRAER PALABRAS
# ================================================================
def extraer_palabras(
    pagina
):

    datos = pagina.extract_words(
        x_tolerance=2,
        y_tolerance=2,
        keep_blank_chars=False,
        use_text_flow=False
    )


    caracteres = list(
        pagina.chars
    )


    palabras = []


    for dato in datos:

        texto = str(
            dato.get(
                "text",
                ""
            )
        ).strip()


        if not texto:

            continue


        caracteres_palabra = (
            obtener_caracteres_palabra(
                dato,
                caracteres
            )
        )


        fragmentos = (
            crear_fragmentos_palabra(
                caracteres_palabra
            )
        )


        estilo = (
            obtener_estilo_fragmentos(
                fragmentos
            )
        )


        palabras.append(
            PalabraPDF(
                texto=texto,

                caja=Caja(
                    x0=redondear(
                        dato.get(
                            "x0"
                        )
                    ),

                    top=redondear(
                        dato.get(
                            "top"
                        )
                    ),

                    x1=redondear(
                        dato.get(
                            "x1"
                        )
                    ),

                    bottom=redondear(
                        dato.get(
                            "bottom"
                        )
                    )
                ),

                fuente=estilo[
                    "fuente"
                ],

                tamano=redondear(
                    estilo[
                        "tamano"
                    ]
                ),

                color=estilo[
                    "color"
                ],

                negrita=estilo[
                    "negrita"
                ],

                cursiva=estilo[
                    "cursiva"
                ],

                fragmentos=fragmentos
            )
        )


    return palabras


# ================================================================
# COMPROBAR SI DOS PALABRAS DEBEN UNIRSE
# ================================================================
def deben_unirse_palabras(
    izquierda,
    derecha
):

    espacio = (
        derecha.caja.x0
        - izquierda.caja.x1
    )


    centro_izquierda = (
        izquierda.caja.top
        + izquierda.caja.bottom
    ) / 2


    centro_derecha = (
        derecha.caja.top
        + derecha.caja.bottom
    ) / 2


    diferencia_vertical = abs(
        centro_izquierda
        - centro_derecha
    )


    tamano_referencia = max(
        izquierda.tamano,
        derecha.tamano,
        izquierda.caja.alto,
        derecha.caja.alto,
        8.0
    )


    tolerancia_vertical = max(
        3.0,
        tamano_referencia * 0.22
    )


    if (
        diferencia_vertical
        > tolerancia_vertical
    ):

        return False


    # ----------------------------------- #
    #          No unir viñetas            #
    # ----------------------------------- #

    if izquierda.texto in (
        "•",
        "▪",
        "◦",
        "●",
        "○"
    ):

        return False


    # ----------------------------------- #
    #        Sin espacio gráfico          #
    # ----------------------------------- #

    umbral_general = max(
        0.85,
        min(
            1.8,
            tamano_referencia * 0.075
        )
    )


    if (
        -2.5
        <= espacio
        <= umbral_general
    ):

        return True


    # ----------------------------------- #
    #       Signos de puntuación          #
    # ----------------------------------- #

    signos_derecha = (
        ".",
        ",",
        ";",
        ":",
        "!",
        "?",
        "%",
        ")",
        "]",
        "}",
        "»"
    )


    if (
        derecha.texto.startswith(
            signos_derecha
        )
        and espacio <= 2.5
    ):

        return True


    signos_izquierda = (
        "(",
        "[",
        "{",
        "¿",
        "¡",
        "«"
    )


    if (
        izquierda.texto.endswith(
            signos_izquierda
        )
        and espacio <= 2.5
    ):

        return True


    return False


# ================================================================
# CREAR FRAGMENTO DESDE PALABRA
# ================================================================
def crear_fragmento_desde_palabra(
    palabra
):

    return FragmentoTextoPDF(
        texto=palabra.texto,

        caja=Caja(
            x0=palabra.caja.x0,
            top=palabra.caja.top,
            x1=palabra.caja.x1,
            bottom=palabra.caja.bottom
        ),

        fuente=palabra.fuente,

        tamano=palabra.tamano,

        color=palabra.color,

        negrita=palabra.negrita,

        cursiva=palabra.cursiva
    )


# ================================================================
# FUSIONAR PALABRAS
# ================================================================
def fusionar_palabras(
    izquierda,
    derecha
):

    if izquierda.fragmentos:

        fragmentos_izquierda = (
            izquierda.fragmentos
        )


    else:

        fragmentos_izquierda = [
            crear_fragmento_desde_palabra(
                izquierda
            )
        ]


    if derecha.fragmentos:

        fragmentos_derecha = (
            derecha.fragmentos
        )


    else:

        fragmentos_derecha = [
            crear_fragmento_desde_palabra(
                derecha
            )
        ]


    fragmentos = (
        fragmentos_izquierda
        + fragmentos_derecha
    )


    estilo = obtener_estilo_fragmentos(
        fragmentos
    )


    return PalabraPDF(
        texto=(
            izquierda.texto
            + derecha.texto
        ),

        caja=Caja(
            x0=min(
                izquierda.caja.x0,
                derecha.caja.x0
            ),

            top=min(
                izquierda.caja.top,
                derecha.caja.top
            ),

            x1=max(
                izquierda.caja.x1,
                derecha.caja.x1
            ),

            bottom=max(
                izquierda.caja.bottom,
                derecha.caja.bottom
            )
        ),

        fuente=estilo[
            "fuente"
        ],

        tamano=redondear(
            estilo[
                "tamano"
            ]
        ),

        color=estilo[
            "color"
        ],

        negrita=estilo[
            "negrita"
        ],

        cursiva=estilo[
            "cursiva"
        ],

        fragmentos=fragmentos
    )


# ================================================================
# FUSIONAR PALABRAS DE UNA LÍNEA
# ================================================================
def fusionar_palabras_linea(
    palabras
):

    if not palabras:

        return []


    palabras = sorted(
        palabras,
        key=lambda palabra: (
            palabra.caja.x0
        )
    )


    resultado = [
        palabras[
            0
        ]
    ]


    for palabra in palabras[
        1:
    ]:

        ultima = resultado[
            -1
        ]


        if deben_unirse_palabras(
            ultima,
            palabra
        ):

            resultado[
                -1
            ] = fusionar_palabras(
                ultima,
                palabra
            )


        else:

            resultado.append(
                palabra
            )


    return resultado


# ================================================================
# AGRUPAR PALABRAS EN LÍNEAS
# ================================================================
def agrupar_palabras_en_lineas(
    palabras
):

    if not palabras:

        return []


    palabras_ordenadas = sorted(
        palabras,
        key=lambda palabra: (
            palabra.caja.top,
            palabra.caja.x0
        )
    )


    grupos = []


    for palabra in palabras_ordenadas:

        centro_y = (
            palabra.caja.top
            + palabra.caja.bottom
        ) / 2


        alto_palabra = max(
            palabra.caja.alto,
            palabra.tamano,
            1.0
        )


        grupo_elegido = None

        mejor_distancia = None


        for grupo in reversed(
            grupos[
                -8:
            ]
        ):

            tolerancia = max(
                2.2,
                min(
                    5.0,
                    grupo[
                        "alto_medio"
                    ] * 0.32
                )
            )


            distancia = abs(
                centro_y
                - grupo[
                    "centro_y"
                ]
            )


            if distancia <= tolerancia:

                if (
                    mejor_distancia is None
                    or distancia
                    < mejor_distancia
                ):

                    grupo_elegido = grupo

                    mejor_distancia = distancia


        if grupo_elegido is None:

            grupos.append(
                {
                    "palabras": [
                        palabra
                    ],

                    "centro_y": centro_y,

                    "alto_medio": (
                        alto_palabra
                    )
                }
            )


            continue


        grupo_elegido[
            "palabras"
        ].append(
            palabra
        )


        grupo_elegido[
            "centro_y"
        ] = statistics.mean(
            [
                (
                    item.caja.top
                    + item.caja.bottom
                ) / 2
                for item
                in grupo_elegido[
                    "palabras"
                ]
            ]
        )


        grupo_elegido[
            "alto_medio"
        ] = statistics.mean(
            [
                max(
                    item.caja.alto,
                    item.tamano,
                    1.0
                )
                for item
                in grupo_elegido[
                    "palabras"
                ]
            ]
        )


    lineas = []


    for grupo in sorted(
        grupos,
        key=lambda item: item[
            "centro_y"
        ]
    ):

        palabras_linea = (
            fusionar_palabras_linea(
                grupo[
                    "palabras"
                ]
            )
        )


        texto = " ".join(
            palabra.texto
            for palabra
            in palabras_linea
        ).strip()


        x0 = min(
            palabra.caja.x0
            for palabra
            in palabras_linea
        )


        x1 = max(
            palabra.caja.x1
            for palabra
            in palabras_linea
        )


        top = min(
            palabra.caja.top
            for palabra
            in palabras_linea
        )


        bottom = max(
            palabra.caja.bottom
            for palabra
            in palabras_linea
        )


        pesos = [
            max(
                1,
                len(
                    palabra.texto
                )
            )
            for palabra
            in palabras_linea
        ]


        total_peso = sum(
            pesos
        )


        if total_peso:

            tamano_promedio = (
                sum(
                    palabra.tamano
                    * peso
                    for palabra, peso
                    in zip(
                        palabras_linea,
                        pesos
                    )
                )
                / total_peso
            )


        else:

            tamano_promedio = 0.0


        fuente = valor_mas_frecuente(
            [
                palabra.fuente
                for palabra
                in palabras_linea
            ],
            ""
        )


        color = valor_mas_frecuente(
            [
                palabra.color
                for palabra
                in palabras_linea
            ],
            None
        )


        cantidad_caracteres = sum(
            len(
                palabra.texto
            )
            for palabra
            in palabras_linea
        )


        caracteres_negrita = sum(
            len(
                palabra.texto
            )
            for palabra
            in palabras_linea
            if palabra.negrita
        )


        caracteres_cursiva = sum(
            len(
                palabra.texto
            )
            for palabra
            in palabras_linea
            if palabra.cursiva
        )


        lineas.append(
            LineaTextoPDF(
                texto=texto,

                caja=Caja(
                    x0=redondear(
                        x0
                    ),

                    top=redondear(
                        top
                    ),

                    x1=redondear(
                        x1
                    ),

                    bottom=redondear(
                        bottom
                    )
                ),

                fuente_predominante=(
                    fuente
                ),

                tamano_promedio=redondear(
                    tamano_promedio
                ),

                color_predominante=(
                    color
                ),

                negrita_predominante=(
                    caracteres_negrita
                    >= max(
                        1,
                        cantidad_caracteres
                        * 0.5
                    )
                ),

                cursiva_predominante=(
                    caracteres_cursiva
                    >= max(
                        1,
                        cantidad_caracteres
                        * 0.5
                    )
                ),

                alineacion_estimada=(
                    "sin_analizar"
                ),

                zona="cuerpo",

                palabras=palabras_linea
            )
        )


    return lineas


# ================================================================
# EXTRAER IMÁGENES
# ================================================================
def extraer_imagenes(
    pagina
):

    imagenes = []


    for indice, dato in enumerate(
        pagina.images,
        start=1
    ):

        srcsize = dato.get(
            "srcsize"
        )


        ancho_pixeles = None

        alto_pixeles = None


        if (
            isinstance(
                srcsize,
                (
                    list,
                    tuple
                )
            )
            and len(
                srcsize
            ) >= 2
        ):

            try:

                ancho_pixeles = int(
                    srcsize[
                        0
                    ]
                )


                alto_pixeles = int(
                    srcsize[
                        1
                    ]
                )


            except (
                TypeError,
                ValueError
            ):

                pass


        imagenes.append(
            ImagenPDF(
                caja=Caja(
                    x0=redondear(
                        dato.get(
                            "x0"
                        )
                    ),

                    top=redondear(
                        dato.get(
                            "top"
                        )
                    ),

                    x1=redondear(
                        dato.get(
                            "x1"
                        )
                    ),

                    bottom=redondear(
                        dato.get(
                            "bottom"
                        )
                    )
                ),

                nombre=str(
                    dato.get(
                        "name",
                        (
                            f"imagen_"
                            f"{indice}"
                        )
                    )
                ),

                ancho_pixeles=(
                    ancho_pixeles
                ),

                alto_pixeles=(
                    alto_pixeles
                ),

                bits=(
                    int(
                        dato[
                            "bits"
                        ]
                    )
                    if isinstance(
                        dato.get(
                            "bits"
                        ),
                        (
                            int,
                            float
                        )
                    )
                    else None
                ),

                espacio_color=(
                    normalizar_valor(
                        dato.get(
                            "colorspace"
                        )
                    )
                )
            )
        )


    return imagenes


# ================================================================
# EXTRAER LÍNEAS VECTORIALES
# ================================================================
def extraer_lineas_vectoriales(
    pagina
):

    resultado = []


    for dato in pagina.lines:

        resultado.append(
            LineaVectorialPDF(
                caja=Caja(
                    x0=redondear(
                        dato.get(
                            "x0"
                        )
                    ),

                    top=redondear(
                        dato.get(
                            "top"
                        )
                    ),

                    x1=redondear(
                        dato.get(
                            "x1"
                        )
                    ),

                    bottom=redondear(
                        dato.get(
                            "bottom"
                        )
                    )
                ),

                grosor=redondear(
                    dato.get(
                        "linewidth"
                    )
                ),

                color=normalizar_valor(
                    dato.get(
                        "stroking_color"
                    )
                ),

                patron_trazo=(
                    normalizar_valor(
                        dato.get(
                            "dash"
                        )
                    )
                )
            )
        )


    return resultado


# ================================================================
# EXTRAER RECTÁNGULOS
# ================================================================
def extraer_rectangulos(
    pagina
):

    resultado = []


    for dato in pagina.rects:

        resultado.append(
            RectanguloPDF(
                caja=Caja(
                    x0=redondear(
                        dato.get(
                            "x0"
                        )
                    ),

                    top=redondear(
                        dato.get(
                            "top"
                        )
                    ),

                    x1=redondear(
                        dato.get(
                            "x1"
                        )
                    ),

                    bottom=redondear(
                        dato.get(
                            "bottom"
                        )
                    )
                ),

                color_trazo=(
                    normalizar_valor(
                        dato.get(
                            "stroking_color"
                        )
                    )
                ),

                color_relleno=(
                    normalizar_valor(
                        dato.get(
                            "non_stroking_color"
                        )
                    )
                ),

                relleno=bool(
                    dato.get(
                        "fill",
                        False
                    )
                )
            )
        )


    return resultado


# ================================================================
# DETECTAR REPETICIONES
# ================================================================
def detectar_repeticiones(
    documento
):

    contador_encabezados = Counter()

    contador_pies = Counter()


    for pagina in documento.paginas:

        candidatos_encabezado = set()

        candidatos_pie = set()


        for linea in pagina.lineas_texto:

            texto = (
                normalizar_texto_repetido(
                    linea.texto
                )
            )


            if len(
                texto
            ) < 3:

                continue


            if (
                linea.caja.top
                <= pagina.alto
                * 0.15
            ):

                candidatos_encabezado.add(
                    texto
                )


            if (
                linea.caja.bottom
                >= pagina.alto
                * 0.85
            ):

                candidatos_pie.add(
                    texto
                )


        contador_encabezados.update(
            candidatos_encabezado
        )


        contador_pies.update(
            candidatos_pie
        )


    minimo = max(
        2,
        math.ceil(
            len(
                documento.paginas
            )
            * 0.5
        )
    )


    documento.encabezados_probables = [
        {
            "texto_normalizado": texto,
            "paginas": cantidad
        }
        for texto, cantidad
        in contador_encabezados.most_common()
        if cantidad >= minimo
    ]


    documento.pies_probables = [
        {
            "texto_normalizado": texto,
            "paginas": cantidad
        }
        for texto, cantidad
        in contador_pies.most_common()
        if cantidad >= minimo
    ]


# ================================================================
# APLICAR ZONAS REALES
# ================================================================
def aplicar_zonas_reales(
    documento
):

    encabezados = {
        elemento[
            "texto_normalizado"
        ]
        for elemento
        in documento.encabezados_probables
    }


    pies = {
        elemento[
            "texto_normalizado"
        ]
        for elemento
        in documento.pies_probables
    }


    for pagina in documento.paginas:

        for linea in pagina.lineas_texto:

            texto = (
                normalizar_texto_repetido(
                    linea.texto
                )
            )


            if texto in encabezados:

                linea.zona = (
                    "encabezado"
                )


            elif texto in pies:

                linea.zona = "pie"


            else:

                linea.zona = (
                    "cuerpo"
                )


# ================================================================
# VALOR NUMÉRICO FRECUENTE
# ================================================================
def valor_numerico_frecuente(
    valores,
    predeterminado,
    paso=4.0
):

    valores_validos = []


    for valor in valores:

        try:

            valores_validos.append(
                float(
                    valor
                )
            )


        except (
            TypeError,
            ValueError
        ):

            continue


    if not valores_validos:

        return predeterminado


    contador = Counter()


    for valor in valores_validos:

        grupo = (
            round(
                valor
                / paso
            )
            * paso
        )


        contador[
            grupo
        ] += 1


    grupo_principal = (
        contador.most_common(
            1
        )[0][0]
    )


    cercanos = [
        valor
        for valor
        in valores_validos
        if abs(
            valor
            - grupo_principal
        ) <= paso
    ]


    if not cercanos:

        return grupo_principal


    return statistics.median(
        cercanos
    )


# ================================================================
# OBTENER CANDIDATOS PARA MÁRGENES
# ================================================================
def obtener_candidatos_margenes(
    pagina
):

    # ----------------------------------- #
    #     Evitar tablas muy complejas     #
    # ----------------------------------- #

    if len(
        pagina.rectangulos
    ) > 100:

        return []


    resultado = []


    for linea in pagina.lineas_texto:

        if linea.zona != "cuerpo":

            continue


        texto = linea.texto.strip()


        if len(
            texto
        ) < 25:

            continue


        if texto.count(
            "_"
        ) >= 5:

            continue


        if not (
            10.0
            <= linea.tamano_promedio
            <= 16.5
        ):

            continue


        if (
            linea.caja.ancho
            < pagina.ancho
            * 0.30
        ):

            continue


        resultado.append(
            linea
        )


    return resultado


# ================================================================
# ESTIMAR MÁRGENES GLOBALES
# ================================================================
def estimar_margenes_globales(
    documento
):

    candidatos = []


    for pagina in documento.paginas:

        candidatos.extend(
            obtener_candidatos_margenes(
                pagina
            )
        )


    if documento.paginas:

        ancho_referencia = (
            documento.paginas[
                0
            ].ancho
        )


    else:

        ancho_referencia = 612.0


    if candidatos:

        izquierdo = (
            valor_numerico_frecuente(
                [
                    linea.caja.x0
                    for linea
                    in candidatos
                ],
                72.0
            )
        )


        derecho_limite = (
            valor_numerico_frecuente(
                [
                    linea.caja.x1
                    for linea
                    in candidatos
                ],
                ancho_referencia
                - 72.0
            )
        )


        derecho = (
            ancho_referencia
            - derecho_limite
        )


        if len(
            candidatos
        ) >= 20:

            confianza_lateral = (
                "alta"
            )


        else:

            confianza_lateral = (
                "media"
            )


    else:

        izquierdo = 72.0

        derecho = 72.0

        confianza_lateral = "baja"


    primeros_bloques = []

    ultimos_bloques = []


    for pagina in documento.paginas[
        1:
    ]:

        lineas_cuerpo = [
            linea
            for linea
            in pagina.lineas_texto
            if linea.zona == "cuerpo"
        ]


        if not lineas_cuerpo:

            continue


        primeros_bloques.append(
            min(
                linea.caja.top
                for linea
                in lineas_cuerpo
            )
        )


        ultimos_bloques.append(
            pagina.alto
            - max(
                linea.caja.bottom
                for linea
                in lineas_cuerpo
            )
        )


    if primeros_bloques:

        superior = (
            valor_numerico_frecuente(
                primeros_bloques,
                72.0,
                paso=6.0
            )
        )


    else:

        superior = 72.0


    if ultimos_bloques:

        inferior = (
            valor_numerico_frecuente(
                ultimos_bloques,
                72.0,
                paso=8.0
            )
        )


    else:

        inferior = 72.0


    documento.margenes_globales = (
        MargenesPaginaPDF(
            izquierdo=redondear(
                izquierdo
            ),

            derecho=redondear(
                derecho
            ),

            superior=redondear(
                superior
            ),

            inferior=redondear(
                inferior
            ),

            confianza_lateral=(
                confianza_lateral
            ),

            confianza_vertical="media"
        )
    )


# ================================================================
# APLICAR MÁRGENES A PÁGINAS
# ================================================================
def aplicar_margenes_paginas(
    documento
):

    globales = (
        documento.margenes_globales
    )


    for pagina in documento.paginas:

        candidatos = (
            obtener_candidatos_margenes(
                pagina
            )
        )


        if len(
            candidatos
        ) >= 4:

            izquierdo = (
                valor_numerico_frecuente(
                    [
                        linea.caja.x0
                        for linea
                        in candidatos
                    ],
                    globales.izquierdo
                )
            )


            limite_derecho = (
                valor_numerico_frecuente(
                    [
                        linea.caja.x1
                        for linea
                        in candidatos
                    ],
                    pagina.ancho
                    - globales.derecho
                )
            )


            derecho = (
                pagina.ancho
                - limite_derecho
            )


            confianza_lateral = (
                "media"
            )


        else:

            izquierdo = (
                globales.izquierdo
            )


            derecho = (
                globales.derecho
            )


            confianza_lateral = (
                "heredada"
            )


        pagina.margenes = (
            MargenesPaginaPDF(
                izquierdo=redondear(
                    izquierdo
                ),

                derecho=redondear(
                    derecho
                ),

                superior=redondear(
                    globales.superior
                ),

                inferior=redondear(
                    globales.inferior
                ),

                confianza_lateral=(
                    confianza_lateral
                ),

                confianza_vertical=(
                    "heredada"
                )
            )
        )


# ================================================================
# ACTUALIZAR ALINEACIONES
# ================================================================
def actualizar_alineaciones(
    documento
):

    for pagina in documento.paginas:

        margen_izquierdo = (
            pagina.margenes.izquierdo
        )


        limite_derecho = (
            pagina.ancho
            - pagina.margenes.derecho
        )


        ancho_util = max(
            1.0,
            limite_derecho
            - margen_izquierdo
        )


        centro_util = (
            margen_izquierdo
            + limite_derecho
        ) / 2


        tolerancia_margen = max(
            10.0,
            pagina.ancho
            * 0.022
        )


        tolerancia_centro = max(
            10.0,
            pagina.ancho
            * 0.025
        )


        for linea in pagina.lineas_texto:

            x0 = linea.caja.x0

            x1 = linea.caja.x1

            ancho = linea.caja.ancho


            centro = (
                x0
                + x1
            ) / 2


            cerca_izquierda = (
                abs(
                    x0
                    - margen_izquierdo
                )
                <= tolerancia_margen
            )


            cerca_derecha = (
                abs(
                    x1
                    - limite_derecho
                )
                <= tolerancia_margen
            )


            cerca_centro = (
                abs(
                    centro
                    - centro_util
                )
                <= tolerancia_centro
            )


            # ----------------------------------- #
            #        Encabezado y pie             #
            # ----------------------------------- #

            if linea.zona in (
                "encabezado",
                "pie"
            ):

                if cerca_centro:

                    linea.alineacion_estimada = (
                        "centro"
                    )


                elif cerca_derecha:

                    linea.alineacion_estimada = (
                        "derecha"
                    )


                else:

                    linea.alineacion_estimada = (
                        "izquierda"
                    )


                continue


            # ----------------------------------- #
            #              Índice                 #
            # ----------------------------------- #

            if linea.texto.count(
                "_"
            ) >= 5:

                linea.alineacion_estimada = (
                    "izquierda"
                )


                continue


            # ----------------------------------- #
            #       Texto grande / título         #
            # ----------------------------------- #

            if (
                linea.tamano_promedio
                >= 17.0

                or (
                    linea.negrita_predominante

                    and len(
                        linea.texto
                    ) <= 90
                )
            ):

                if (
                    cerca_centro

                    or abs(
                        centro
                        - pagina.ancho
                        / 2
                    )
                    <= pagina.ancho
                    * 0.045
                ):

                    linea.alineacion_estimada = (
                        "centro"
                    )


                    continue


            # ----------------------------------- #
            #           Justificado               #
            # ----------------------------------- #

            if (
                cerca_izquierda

                and cerca_derecha

                and ancho
                >= ancho_util
                * 0.68

                and linea.tamano_promedio
                <= 16.5
            ):

                linea.alineacion_estimada = (
                    "justificada"
                )


                continue


            if cerca_izquierda:

                linea.alineacion_estimada = (
                    "izquierda"
                )


                continue


            if (
                cerca_derecha

                and ancho
                <= ancho_util
                * 0.70
            ):

                linea.alineacion_estimada = (
                    "derecha"
                )


                continue


            if (
                cerca_centro

                and ancho
                <= ancho_util
                * 0.90
            ):

                linea.alineacion_estimada = (
                    "centro"
                )


                continue


            linea.alineacion_estimada = (
                "izquierda"
            )


# ================================================================
# DETECTAR DISTANCIA DE ENCABEZADO Y PIE
# ================================================================
def detectar_distancias_encabezado_pie(
    pagina
):

    encabezados = [
        linea
        for linea
        in pagina.lineas_texto
        if linea.zona == "encabezado"
    ]


    pies = [
        linea
        for linea
        in pagina.lineas_texto
        if linea.zona == "pie"
    ]


    distancia_encabezado = None

    distancia_pie = None


    if encabezados:

        distancia_encabezado = min(
            linea.caja.top
            for linea
            in encabezados
        )


    if pies:

        distancia_pie = (
            pagina.alto
            - max(
                linea.caja.bottom
                for linea
                in pies
            )
        )


    pagina.distancias_encabezado_pie = (
        DistanciasEncabezadoPiePDF(
            encabezado_desde_borde_superior=(
                redondear(
                    distancia_encabezado
                )
                if distancia_encabezado
                is not None
                else None
            ),

            pie_desde_borde_inferior=(
                redondear(
                    distancia_pie
                )
                if distancia_pie
                is not None
                else None
            )
        )
    )


# ================================================================
# CLASIFICAR ESTILO DE TRAZO
# ================================================================
def clasificar_estilo_trazo(
    patron
):

    if patron in (
        None,
        [],
        (),
        ""
    ):

        return "continua"


    texto = str(
        patron
    ).lower()


    if "dash" in texto:

        return "discontinua"


    return "personalizada"


# ================================================================
# CREAR LADO DE BORDE
# ================================================================
def crear_lado_borde(
    linea,
    posicion,
    separacion,
    longitud
):

    if linea is None:

        return LadoBordePDF()


    return LadoBordePDF(
        presente=True,

        posicion=redondear(
            posicion
        ),

        separacion_borde=redondear(
            separacion
        ),

        grosor=redondear(
            linea.grosor
        ),

        color=linea.color,

        estilo=clasificar_estilo_trazo(
            linea.patron_trazo
        ),

        patron_trazo=(
            linea.patron_trazo
        ),

        longitud=redondear(
            longitud
        )
    )


# ================================================================
# DETECTAR BORDE DE PÁGINA
# ================================================================
def detectar_borde_pagina(
    pagina
):

    horizontales = []

    verticales = []


    for linea in pagina.lineas_vectoriales:

        ancho = linea.caja.ancho

        alto = linea.caja.alto


        if (
            alto <= 1.0

            and ancho
            >= pagina.ancho
            * 0.70
        ):

            horizontales.append(
                linea
            )


        if (
            ancho <= 1.0

            and alto
            >= pagina.alto
            * 0.70
        ):

            verticales.append(
                linea
            )


    superior = None

    inferior = None

    izquierdo = None

    derecho = None


    if horizontales:

        superior = min(
            horizontales,
            key=lambda linea: (
                (
                    linea.caja.top
                    + linea.caja.bottom
                ) / 2
            )
        )


        inferior = max(
            horizontales,
            key=lambda linea: (
                (
                    linea.caja.top
                    + linea.caja.bottom
                ) / 2
            )
        )


    if verticales:

        izquierdo = min(
            verticales,
            key=lambda linea: (
                (
                    linea.caja.x0
                    + linea.caja.x1
                ) / 2
            )
        )


        derecho = max(
            verticales,
            key=lambda linea: (
                (
                    linea.caja.x0
                    + linea.caja.x1
                ) / 2
            )
        )


    if superior:

        posicion_superior = (
            superior.caja.top
            + superior.caja.bottom
        ) / 2


    else:

        posicion_superior = 0.0


    if inferior:

        posicion_inferior = (
            inferior.caja.top
            + inferior.caja.bottom
        ) / 2


    else:

        posicion_inferior = (
            pagina.alto
        )


    if izquierdo:

        posicion_izquierdo = (
            izquierdo.caja.x0
            + izquierdo.caja.x1
        ) / 2


    else:

        posicion_izquierdo = 0.0


    if derecho:

        posicion_derecho = (
            derecho.caja.x0
            + derecho.caja.x1
        ) / 2


    else:

        posicion_derecho = (
            pagina.ancho
        )


    pagina.borde_pagina = (
        BordePaginaPDF(
            superior=crear_lado_borde(
                superior,

                posicion_superior,

                posicion_superior,

                (
                    superior.caja.ancho
                    if superior
                    else 0.0
                )
            ),

            derecho=crear_lado_borde(
                derecho,

                posicion_derecho,

                (
                    pagina.ancho
                    - posicion_derecho
                ),

                (
                    derecho.caja.alto
                    if derecho
                    else 0.0
                )
            ),

            inferior=crear_lado_borde(
                inferior,

                posicion_inferior,

                (
                    pagina.alto
                    - posicion_inferior
                ),

                (
                    inferior.caja.ancho
                    if inferior
                    else 0.0
                )
            ),

            izquierdo=crear_lado_borde(
                izquierdo,

                posicion_izquierdo,

                posicion_izquierdo,

                (
                    izquierdo.caja.alto
                    if izquierdo
                    else 0.0
                )
            )
        )
    )


# ================================================================
# CALCULAR COBERTURA
# ================================================================
def calcular_cobertura(
    caja,
    ancho_pagina,
    alto_pagina
):

    area_pagina = (
        ancho_pagina
        * alto_pagina
    )


    if area_pagina <= 0:

        return 0.0


    area = (
        caja.ancho
        * caja.alto
    )


    return max(
        0.0,
        min(
            1.0,
            area
            / area_pagina
        )
    )


# ================================================================
# DETECTAR FONDO DE PÁGINA
# ================================================================
def detectar_fondo_pagina(
    pagina
):

    candidatos_rectangulo = []


    for rectangulo in pagina.rectangulos:

        if not rectangulo.relleno:

            continue


        cobertura = (
            calcular_cobertura(
                rectangulo.caja,
                pagina.ancho,
                pagina.alto
            )
        )


        if cobertura >= 0.90:

            candidatos_rectangulo.append(
                (
                    cobertura,
                    rectangulo
                )
            )


    if candidatos_rectangulo:

        candidatos_rectangulo.sort(
            key=lambda elemento: (
                elemento[
                    0
                ]
            ),
            reverse=True
        )


        cobertura, rectangulo = (
            candidatos_rectangulo[
                0
            ]
        )


        relleno = (
            rectangulo.color_relleno
        )


        if (
            isinstance(
                relleno,
                str
            )

            and re.fullmatch(
                r"P\d+",
                relleno,
                flags=re.IGNORECASE
            )
        ):

            tipo = "patron_pdf"

            recurso = relleno

            color = None


        else:

            tipo = (
                "color_o_relleno_pdf"
            )

            recurso = None

            color = relleno


        pagina.fondo_pagina = (
            FondoPaginaPDF(
                detectado=True,

                tipo=tipo,

                recurso_pdf=(
                    recurso
                ),

                color=color,

                caja=rectangulo.caja,

                cubre_pagina=(
                    cobertura
                    >= 0.97
                ),

                cobertura=redondear(
                    cobertura,
                    4
                )
            )
        )


        return


    candidatos_imagen = []


    for imagen in pagina.imagenes:

        cobertura = (
            calcular_cobertura(
                imagen.caja,
                pagina.ancho,
                pagina.alto
            )
        )


        if cobertura >= 0.90:

            candidatos_imagen.append(
                (
                    cobertura,
                    imagen
                )
            )


    if candidatos_imagen:

        candidatos_imagen.sort(
            key=lambda elemento: (
                elemento[
                    0
                ]
            ),
            reverse=True
        )


        cobertura, imagen = (
            candidatos_imagen[
                0
            ]
        )


        pagina.fondo_pagina = (
            FondoPaginaPDF(
                detectado=True,

                tipo="imagen",

                recurso_pdf=(
                    imagen.nombre
                ),

                color=None,

                caja=imagen.caja,

                cubre_pagina=(
                    cobertura
                    >= 0.97
                ),

                cobertura=redondear(
                    cobertura,
                    4
                )
            )
        )


        return


    pagina.fondo_pagina = (
        FondoPaginaPDF()
    )


# ================================================================
# DETECTAR FONDO REPETIDO
# ================================================================
def detectar_fondo_repetido(
    documento
):

    contador = Counter()

    datos = {}


    for pagina in documento.paginas:

        fondo = pagina.fondo_pagina


        if not fondo.detectado:

            continue


        clave = (
            fondo.tipo,

            crear_clave_valor(
                fondo.recurso_pdf
            ),

            crear_clave_valor(
                fondo.color
            )
        )


        contador[
            clave
        ] += 1


        if clave not in datos:

            datos[
                clave
            ] = {
                "tipo": fondo.tipo,

                "recurso_pdf": (
                    fondo.recurso_pdf
                ),

                "color": fondo.color
            }


    if not contador:

        documento.fondo_repetido = {}

        return


    clave, cantidad = (
        contador.most_common(
            1
        )[0]
    )


    minimo = max(
        2,
        math.ceil(
            len(
                documento.paginas
            )
            * 0.5
        )
    )


    if cantidad < minimo:

        documento.fondo_repetido = {}

        return


    documento.fondo_repetido = {
        **datos[
            clave
        ],

        "paginas": cantidad
    }


# ================================================================
# ANALIZAR PDF
# ================================================================
def analizar_pdf(
    ruta_pdf
):

    documento_resultado = DocumentoPDF(
        ruta_origen=str(
            ruta_pdf
        )
    )


    with pdfplumber.open(
        str(
            ruta_pdf
        )
    ) as documento:

        total_paginas = len(
            documento.pages
        )


        for numero, pagina in enumerate(
            documento.pages,
            start=1
        ):

            ancho = float(
                pagina.width
            )


            alto = float(
                pagina.height
            )


            print(
                (
                    f"Analizando página "
                    f"{numero} de "
                    f"{total_paginas}..."
                )
            )


            palabras_iniciales = (
                extraer_palabras(
                    pagina
                )
            )


            lineas_texto = (
                agrupar_palabras_en_lineas(
                    palabras_iniciales
                )
            )


            palabras_finales = [
                palabra
                for linea
                in lineas_texto
                for palabra
                in linea.palabras
            ]


            pagina_resultado = PaginaPDF(
                numero=numero,

                ancho=redondear(
                    ancho
                ),

                alto=redondear(
                    alto
                ),

                rotacion=int(
                    getattr(
                        pagina,
                        "rotation",
                        0
                    )
                    or 0
                ),

                palabras=palabras_finales,

                lineas_texto=(
                    lineas_texto
                ),

                imagenes=extraer_imagenes(
                    pagina
                ),

                lineas_vectoriales=(
                    extraer_lineas_vectoriales(
                        pagina
                    )
                ),

                rectangulos=(
                    extraer_rectangulos(
                        pagina
                    )
                )
            )


            detectar_borde_pagina(
                pagina_resultado
            )


            detectar_fondo_pagina(
                pagina_resultado
            )


            documento_resultado.paginas.append(
                pagina_resultado
            )


    # ============================================================
    # ANÁLISIS GLOBAL
    # ============================================================

    detectar_repeticiones(
        documento_resultado
    )


    aplicar_zonas_reales(
        documento_resultado
    )


    estimar_margenes_globales(
        documento_resultado
    )


    aplicar_margenes_paginas(
        documento_resultado
    )


    actualizar_alineaciones(
        documento_resultado
    )


    for pagina in (
        documento_resultado.paginas
    ):

        detectar_distancias_encabezado_pie(
            pagina
        )


    detectar_fondo_repetido(
        documento_resultado
    )


    return documento_resultado


# ================================================================
# GUARDAR JSON
# ================================================================
def guardar_json(
    documento,
    ruta_salida
):

    with open(
        ruta_salida,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            convertir_a_diccionario(
                documento
            ),
            archivo,
            ensure_ascii=False,
            indent=2
        )


# ================================================================
# GUARDAR RESUMEN
# ================================================================
def guardar_resumen(
    documento,
    ruta_salida
):

    paginas_con_encabezado = sum(
        1
        for pagina
        in documento.paginas
        if any(
            linea.zona
            == "encabezado"
            for linea
            in pagina.lineas_texto
        )
    )


    paginas_con_pie = sum(
        1
        for pagina
        in documento.paginas
        if any(
            linea.zona
            == "pie"
            for linea
            in pagina.lineas_texto
        )
    )


    with open(
        ruta_salida,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "PROTOTIPO PDF → DOCX\n"
        )


        archivo.write(
            "ANÁLISIS GEOMÉTRICO DEL PDF\n"
        )


        archivo.write(
            "=" * 72
            + "\n\n"
        )


        archivo.write(
            (
                f"PDF: "
                f"{documento.ruta_origen}\n"
            )
        )


        archivo.write(
            (
                "Páginas físicas: "
                f"{len(documento.paginas)}\n"
            )
        )


        archivo.write(
            (
                "Páginas con encabezado "
                "repetido detectado: "
                f"{paginas_con_encabezado}\n"
            )
        )


        archivo.write(
            (
                "Páginas con pie "
                "repetido detectado: "
                f"{paginas_con_pie}\n\n"
            )
        )


        # ========================================================
        # MÁRGENES GLOBALES
        # ========================================================

        margenes = (
            documento.margenes_globales
        )


        archivo.write(
            "MÁRGENES ESTIMADOS DEL DOCUMENTO\n"
        )


        archivo.write(
            "-" * 72
            + "\n"
        )


        archivo.write(
            (
                "Izquierdo: "
                f"{margenes.izquierdo:.2f} pt\n"
            )
        )


        archivo.write(
            (
                "Derecho: "
                f"{margenes.derecho:.2f} pt\n"
            )
        )


        archivo.write(
            (
                "Superior: "
                f"{margenes.superior:.2f} pt\n"
            )
        )


        archivo.write(
            (
                "Inferior: "
                f"{margenes.inferior:.2f} pt\n"
            )
        )


        archivo.write(
            (
                "Confianza lateral: "
                f"{margenes.confianza_lateral}\n"
            )
        )


        archivo.write(
            (
                "Confianza vertical: "
                f"{margenes.confianza_vertical}\n\n"
            )
        )


        # ========================================================
        # FONDO REPETIDO
        # ========================================================

        archivo.write(
            "FONDO REPETIDO\n"
        )


        archivo.write(
            "-" * 72
            + "\n"
        )


        if documento.fondo_repetido:

            archivo.write(
                (
                    "Tipo: "
                    f"{documento.fondo_repetido.get('tipo')}\n"
                )
            )


            archivo.write(
                (
                    "Recurso PDF: "
                    f"{documento.fondo_repetido.get('recurso_pdf')}\n"
                )
            )


            archivo.write(
                (
                    "Páginas: "
                    f"{documento.fondo_repetido.get('paginas')}\n"
                )
            )


        else:

            archivo.write(
                "No se detectó un fondo repetido.\n"
            )


        archivo.write(
            "\n"
        )


        # ========================================================
        # PÁGINAS
        # ========================================================

        for pagina in documento.paginas:

            archivo.write(
                "=" * 72
                + "\n"
            )


            archivo.write(
                (
                    f"Página "
                    f"{pagina.numero}\n"
                )
            )


            archivo.write(
                "-" * 72
                + "\n"
            )


            archivo.write(
                (
                    "Tamaño: "
                    f"{pagina.ancho:.2f} × "
                    f"{pagina.alto:.2f} pt\n"
                )
            )


            archivo.write(
                (
                    "Palabras: "
                    f"{len(pagina.palabras)}\n"
                )
            )


            archivo.write(
                (
                    "Líneas de texto: "
                    f"{len(pagina.lineas_texto)}\n"
                )
            )


            archivo.write(
                (
                    "Imágenes: "
                    f"{len(pagina.imagenes)}\n"
                )
            )


            archivo.write(
                (
                    "Líneas vectoriales: "
                    f"{len(pagina.lineas_vectoriales)}\n"
                )
            )


            archivo.write(
                (
                    "Rectángulos: "
                    f"{len(pagina.rectangulos)}\n"
                )
            )


            archivo.write(
                (
                    "Margen izquierdo: "
                    f"{pagina.margenes.izquierdo:.2f} pt\n"
                )
            )


            archivo.write(
                (
                    "Margen derecho: "
                    f"{pagina.margenes.derecho:.2f} pt\n"
                )
            )


            # ----------------------------------- #
            #   Evitar expresiones partidas      #
            #        dentro de f-string           #
            # ----------------------------------- #

            distancia_encabezado = (
                pagina
                .distancias_encabezado_pie
                .encabezado_desde_borde_superior
            )


            distancia_pie = (
                pagina
                .distancias_encabezado_pie
                .pie_desde_borde_inferior
            )


            texto_distancia_encabezado = (
                formatear_valor(
                    distancia_encabezado
                )
            )


            texto_distancia_pie = (
                formatear_valor(
                    distancia_pie
                )
            )


            archivo.write(
                (
                    "Distancia encabezado: "
                    f"{texto_distancia_encabezado} pt\n"
                )
            )


            archivo.write(
                (
                    "Distancia pie: "
                    f"{texto_distancia_pie} pt\n"
                )
            )


            # ----------------------------------- #
            #          Borde de página            #
            # ----------------------------------- #

            borde = (
                pagina.borde_pagina
            )


            superior_separacion = (
                formatear_valor(
                    borde
                    .superior
                    .separacion_borde
                )
            )


            superior_grosor = (
                formatear_valor(
                    borde
                    .superior
                    .grosor
                )
            )


            derecho_separacion = (
                formatear_valor(
                    borde
                    .derecho
                    .separacion_borde
                )
            )


            derecho_grosor = (
                formatear_valor(
                    borde
                    .derecho
                    .grosor
                )
            )


            inferior_separacion = (
                formatear_valor(
                    borde
                    .inferior
                    .separacion_borde
                )
            )


            inferior_grosor = (
                formatear_valor(
                    borde
                    .inferior
                    .grosor
                )
            )


            izquierdo_separacion = (
                formatear_valor(
                    borde
                    .izquierdo
                    .separacion_borde
                )
            )


            izquierdo_grosor = (
                formatear_valor(
                    borde
                    .izquierdo
                    .grosor
                )
            )


            archivo.write(
                (
                    "Borde superior: "
                    f"{borde.superior.presente} | "
                    "separación "
                    f"{superior_separacion} pt | "
                    "grosor "
                    f"{superior_grosor} pt\n"
                )
            )


            archivo.write(
                (
                    "Borde derecho: "
                    f"{borde.derecho.presente} | "
                    "separación "
                    f"{derecho_separacion} pt | "
                    "grosor "
                    f"{derecho_grosor} pt\n"
                )
            )


            archivo.write(
                (
                    "Borde inferior: "
                    f"{borde.inferior.presente} | "
                    "separación "
                    f"{inferior_separacion} pt | "
                    "grosor "
                    f"{inferior_grosor} pt\n"
                )
            )


            archivo.write(
                (
                    "Borde izquierdo: "
                    f"{borde.izquierdo.presente} | "
                    "separación "
                    f"{izquierdo_separacion} pt | "
                    "grosor "
                    f"{izquierdo_grosor} pt\n"
                )
            )


            # ----------------------------------- #
            #              Fondo                  #
            # ----------------------------------- #

            fondo = (
                pagina.fondo_pagina
            )


            archivo.write(
                (
                    "Fondo: "
                    f"{fondo.tipo} | "
                    "recurso "
                    f"{fondo.recurso_pdf} | "
                    "cobertura "
                    f"{fondo.cobertura:.4f}\n\n"
                )
            )


        # ========================================================
        # ENCABEZADOS
        # ========================================================

        archivo.write(
            "ENCABEZADOS REPETIDOS\n"
        )


        archivo.write(
            "-" * 72
            + "\n"
        )


        if documento.encabezados_probables:

            for elemento in (
                documento.encabezados_probables
            ):

                archivo.write(
                    (
                        f"{elemento['paginas']} "
                        "páginas | "
                        f"{elemento['texto_normalizado']}\n"
                    )
                )


        else:

            archivo.write(
                "No detectados.\n"
            )


        # ========================================================
        # PIES
        # ========================================================

        archivo.write(
            "\nPIES REPETIDOS\n"
        )


        archivo.write(
            "-" * 72
            + "\n"
        )


        if documento.pies_probables:

            for elemento in (
                documento.pies_probables
            ):

                archivo.write(
                    (
                        f"{elemento['paginas']} "
                        "páginas | "
                        f"{elemento['texto_normalizado']}\n"
                    )
                )


        else:

            archivo.write(
                "No detectados.\n"
            )


# ================================================================
# GUARDAR TEXTO DE PÁGINAS
# ================================================================
def guardar_texto_paginas(
    documento,
    ruta_salida
):

    with open(
        ruta_salida,
        "w",
        encoding="utf-8"
    ) as archivo:

        for pagina in documento.paginas:

            archivo.write(
                "=" * 72
                + "\n"
            )


            archivo.write(
                (
                    f"PÁGINA "
                    f"{pagina.numero}\n"
                )
            )


            archivo.write(
                "=" * 72
                + "\n"
            )


            archivo.write(
                (
                    "Márgenes laterales: "
                    f"{pagina.margenes.izquierdo:.2f} pt / "
                    f"{pagina.margenes.derecho:.2f} pt\n"
                )
            )


            archivo.write(
                (
                    "Fondo: "
                    f"{pagina.fondo_pagina.tipo}"
                )
            )


            if (
                pagina.fondo_pagina.recurso_pdf
                is not None
            ):

                archivo.write(
                    (
                        " | recurso "
                        f"{pagina.fondo_pagina.recurso_pdf}"
                    )
                )


            archivo.write(
                "\n\n"
            )


            for linea in pagina.lineas_texto:

                archivo.write(
                    (
                        f"[{linea.zona:<10}] "
                        f"[{linea.alineacion_estimada:<11}] "
                        f"{linea.tamano_promedio:>6.2f} pt | "
                        f"{linea.fuente_predominante:<28} | "
                        f"{linea.texto}\n"
                    )
                )


            archivo.write(
                "\n\n"
            )


# ================================================================
# GENERAR DIAGNÓSTICOS VISUALES
# ================================================================
def generar_diagnosticos_visuales(
    ruta_pdf,
    documento_analizado
):

    CARPETA_DIAGNOSTICO.mkdir(
        parents=True,
        exist_ok=True
    )


    # ----------------------------------- #
    #       Limpiar resultados viejos     #
    # ----------------------------------- #

    for archivo in (
        CARPETA_DIAGNOSTICO.glob(
            "pagina_*.png"
        )
    ):

        archivo.unlink()


    documento_pdf = (
        pdfium.PdfDocument(
            str(
                ruta_pdf
            )
        )
    )


    escala = 1.8


    try:

        for indice in range(
            len(
                documento_pdf
            )
        ):

            pagina_pdf = (
                documento_pdf[
                    indice
                ]
            )


            bitmap = pagina_pdf.render(
                scale=escala
            )


            imagen = (
                bitmap
                .to_pil()
                .convert(
                    "RGB"
                )
            )


            dibujo = ImageDraw.Draw(
                imagen
            )


            pagina = (
                documento_analizado
                .paginas[
                    indice
                ]
            )


            # ----------------------------------- #
            #               Texto                 #
            # ----------------------------------- #

            for linea in pagina.lineas_texto:

                if linea.zona == "encabezado":

                    color = (
                        220,
                        60,
                        60
                    )


                elif linea.zona == "pie":

                    color = (
                        235,
                        145,
                        20
                    )


                elif (
                    linea.alineacion_estimada
                    == "justificada"
                ):

                    color = (
                        50,
                        110,
                        235
                    )


                else:

                    color = (
                        40,
                        170,
                        220
                    )


                dibujo.rectangle(
                    (
                        int(
                            linea.caja.x0
                            * escala
                        ),

                        int(
                            linea.caja.top
                            * escala
                        ),

                        int(
                            linea.caja.x1
                            * escala
                        ),

                        int(
                            linea.caja.bottom
                            * escala
                        )
                    ),

                    outline=color,

                    width=1
                )


            # ----------------------------------- #
            #              Imágenes               #
            # ----------------------------------- #

            for imagen_pdf in pagina.imagenes:

                dibujo.rectangle(
                    (
                        int(
                            imagen_pdf.caja.x0
                            * escala
                        ),

                        int(
                            imagen_pdf.caja.top
                            * escala
                        ),

                        int(
                            imagen_pdf.caja.x1
                            * escala
                        ),

                        int(
                            imagen_pdf.caja.bottom
                            * escala
                        )
                    ),

                    outline=(
                        30,
                        190,
                        80
                    ),

                    width=2
                )


            # ----------------------------------- #
            #              Márgenes               #
            # ----------------------------------- #

            x_izquierdo = int(
                pagina.margenes.izquierdo
                * escala
            )


            x_derecho = int(
                (
                    pagina.ancho
                    - pagina.margenes.derecho
                )
                * escala
            )


            dibujo.line(
                (
                    x_izquierdo,
                    0,
                    x_izquierdo,
                    imagen.height
                ),

                fill=(
                    180,
                    60,
                    220
                ),

                width=1
            )


            dibujo.line(
                (
                    x_derecho,
                    0,
                    x_derecho,
                    imagen.height
                ),

                fill=(
                    180,
                    60,
                    220
                ),

                width=1
            )


            # ----------------------------------- #
            #         Borde detectado             #
            # ----------------------------------- #

            borde = (
                pagina.borde_pagina
            )


            if borde.superior.presente:

                y = int(
                    borde.superior.posicion
                    * escala
                )


                dibujo.line(
                    (
                        0,
                        y,
                        imagen.width,
                        y
                    ),

                    fill=(
                        235,
                        210,
                        20
                    ),

                    width=2
                )


            if borde.inferior.presente:

                y = int(
                    borde.inferior.posicion
                    * escala
                )


                dibujo.line(
                    (
                        0,
                        y,
                        imagen.width,
                        y
                    ),

                    fill=(
                        235,
                        210,
                        20
                    ),

                    width=2
                )


            if borde.izquierdo.presente:

                x = int(
                    borde.izquierdo.posicion
                    * escala
                )


                dibujo.line(
                    (
                        x,
                        0,
                        x,
                        imagen.height
                    ),

                    fill=(
                        235,
                        210,
                        20
                    ),

                    width=2
                )


            if borde.derecho.presente:

                x = int(
                    borde.derecho.posicion
                    * escala
                )


                dibujo.line(
                    (
                        x,
                        0,
                        x,
                        imagen.height
                    ),

                    fill=(
                        235,
                        210,
                        20
                    ),

                    width=2
                )


            ruta_salida = (
                CARPETA_DIAGNOSTICO
                / (
                    f"pagina_"
                    f"{indice + 1:03d}.png"
                )
            )


            imagen.save(
                ruta_salida,
                "PNG"
            )


            try:

                bitmap.close()


            except Exception:

                pass


            try:

                pagina_pdf.close()


            except Exception:

                pass


    finally:

        try:

            documento_pdf.close()


        except Exception:

            pass


# ================================================================
# EJECUCIÓN PRINCIPAL
# ================================================================
def main():

    parser = argparse.ArgumentParser(
        description=(
            "Primera fase del motor propio PDF → DOCX: "
            "analiza contenido, formato y geometría del PDF."
        )
    )


    parser.add_argument(
        "pdf",
        nargs="?",
        help=(
            "PDF que se analizará. Si se omite, "
            "se usa el primer PDF de la carpeta 'entrada'."
        )
    )


    argumentos = parser.parse_args()


    # ============================================================
    # RESOLVER PDF
    # ============================================================

    ruta_pdf = resolver_pdf_entrada(
        argumentos.pdf
    )


    # ============================================================
    # CREAR CARPETAS
    # ============================================================

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True
    )


    print()


    print(
        (
            f"PDF de entrada: "
            f"{ruta_pdf}"
        )
    )


    print()


    # ============================================================
    # ANALIZAR
    # ============================================================

    documento = analizar_pdf(
        ruta_pdf
    )


    # ============================================================
    # RUTAS DE RESULTADO
    # ============================================================

    ruta_json = (
        CARPETA_SALIDA
        / "analisis_pdf.json"
    )


    ruta_resumen = (
        CARPETA_SALIDA
        / "resumen.txt"
    )


    ruta_texto = (
        CARPETA_SALIDA
        / "texto_paginas.txt"
    )


    # ============================================================
    # GUARDAR RESULTADOS
    # ============================================================

    guardar_json(
        documento,
        ruta_json
    )


    guardar_resumen(
        documento,
        ruta_resumen
    )


    guardar_texto_paginas(
        documento,
        ruta_texto
    )


    # ============================================================
    # DIAGNÓSTICO VISUAL
    # ============================================================

    print()


    print(
        "Generando imágenes de diagnóstico..."
    )


    generar_diagnosticos_visuales(
        ruta_pdf,
        documento
    )


    # ============================================================
    # FINALIZAR
    # ============================================================

    print()


    print(
        "Análisis terminado correctamente."
    )


    print(
        (
            "Páginas físicas: "
            f"{len(documento.paginas)}"
        )
    )


    print(
        (
            f"JSON: "
            f"{ruta_json}"
        )
    )


    print(
        (
            f"Resumen: "
            f"{ruta_resumen}"
        )
    )


    print(
        (
            f"Texto: "
            f"{ruta_texto}"
        )
    )


    print(
        (
            "Diagnóstico: "
            f"{CARPETA_DIAGNOSTICO}"
        )
    )


    print()


if __name__ == "__main__":

    main()