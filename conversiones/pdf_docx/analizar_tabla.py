import json
import statistics

from collections import Counter
from pathlib import Path

import pypdfium2 as pdfium

from PIL import ImageDraw


# ================================================================
# RUTAS
# ================================================================

CARPETA_BASE = Path(__file__).resolve().parent
CARPETA_SALIDA = CARPETA_BASE / "salida"

RUTA_DISTRIBUCION = CARPETA_SALIDA / "distribucion_pdf.json"
RUTA_TABLA = CARPETA_SALIDA / "tabla_reconstruida.json"
RUTA_RESUMEN = CARPETA_SALIDA / "resumen_tabla.txt"
RUTA_DIAGNOSTICO = CARPETA_SALIDA / "diagnostico_tabla.png"


# ================================================================
# CONSTANTES
# ================================================================

TOLERANCIA_AGRUPACION = 1.2
TOLERANCIA_LINEA_TEXTO = 3.5

ANCHO_MAXIMO_LINEA_VERTICAL = 1.4
ALTO_MAXIMO_LINEA_HORIZONTAL = 1.4

ALTO_MINIMO_LINEA_VERTICAL = 12.0
ANCHO_MINIMO_LINEA_HORIZONTAL = 45.0

MARGEN_REGION_TABLA = 8.0

COBERTURA_MINIMA_RELLENO = 0.58


# ================================================================
# UTILIDADES BÁSICAS
# ================================================================

def cargar_json(ruta):

    if not ruta.is_file():

        raise FileNotFoundError(
            f"No existe el archivo requerido: {ruta}"
        )


    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )


def redondear(
    valor,
    decimales=3
):

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


def normalizar_texto(
    texto
):

    return " ".join(
        str(
            texto
            or ""
        ).split()
    )


def obtener_caja(
    elemento
):

    return elemento.get(
        "caja",
        {}
    )


def obtener_x0(
    elemento
):

    return redondear(
        obtener_caja(
            elemento
        ).get(
            "x0"
        )
    )


def obtener_x1(
    elemento
):

    return redondear(
        obtener_caja(
            elemento
        ).get(
            "x1"
        )
    )


def obtener_top(
    elemento
):

    return redondear(
        obtener_caja(
            elemento
        ).get(
            "top"
        )
    )


def obtener_bottom(
    elemento
):

    return redondear(
        obtener_caja(
            elemento
        ).get(
            "bottom"
        )
    )


def obtener_ancho(
    elemento
):

    return max(
        0.0,
        obtener_x1(
            elemento
        )
        - obtener_x0(
            elemento
        )
    )


def obtener_alto(
    elemento
):

    return max(
        0.0,
        obtener_bottom(
            elemento
        )
        - obtener_top(
            elemento
        )
    )


def obtener_centro(
    elemento
):

    return (
        (
            obtener_x0(
                elemento
            )
            + obtener_x1(
                elemento
            )
        )
        / 2,

        (
            obtener_top(
                elemento
            )
            + obtener_bottom(
                elemento
            )
        )
        / 2
    )


def combinar_cajas(
    elementos
):

    if not elementos:

        return {
            "x0": 0.0,
            "top": 0.0,
            "x1": 0.0,
            "bottom": 0.0
        }


    return {
        "x0": redondear(
            min(
                obtener_x0(
                    elemento
                )
                for elemento
                in elementos
            )
        ),

        "top": redondear(
            min(
                obtener_top(
                    elemento
                )
                for elemento
                in elementos
            )
        ),

        "x1": redondear(
            max(
                obtener_x1(
                    elemento
                )
                for elemento
                in elementos
            )
        ),

        "bottom": redondear(
            max(
                obtener_bottom(
                    elemento
                )
                for elemento
                in elementos
            )
        )
    }


def expandir_caja(
    caja,
    margen
):

    return {
        "x0": caja[
            "x0"
        ] - margen,

        "top": caja[
            "top"
        ] - margen,

        "x1": caja[
            "x1"
        ] + margen,

        "bottom": caja[
            "bottom"
        ] + margen
    }


def cajas_se_solapan(
    caja_a,
    caja_b
):

    return not (
        caja_a[
            "x1"
        ]
        < caja_b[
            "x0"
        ]

        or caja_a[
            "x0"
        ]
        > caja_b[
            "x1"
        ]

        or caja_a[
            "bottom"
        ]
        < caja_b[
            "top"
        ]

        or caja_a[
            "top"
        ]
        > caja_b[
            "bottom"
        ]
    )


def punto_en_caja(
    x,
    y,
    caja,
    tolerancia=0.8
):

    return (
        caja[
            "x0"
        ] - tolerancia
        <= x
        <= caja[
            "x1"
        ] + tolerancia

        and caja[
            "top"
        ] - tolerancia
        <= y
        <= caja[
            "bottom"
        ] + tolerancia
    )


def calcular_area_caja(
    caja
):

    return max(
        0.0,
        caja[
            "x1"
        ]
        - caja[
            "x0"
        ]
    ) * max(
        0.0,
        caja[
            "bottom"
        ]
        - caja[
            "top"
        ]
    )


def calcular_interseccion(
    caja_a,
    caja_b
):

    x0 = max(
        caja_a[
            "x0"
        ],
        caja_b[
            "x0"
        ]
    )


    top = max(
        caja_a[
            "top"
        ],
        caja_b[
            "top"
        ]
    )


    x1 = min(
        caja_a[
            "x1"
        ],
        caja_b[
            "x1"
        ]
    )


    bottom = min(
        caja_a[
            "bottom"
        ],
        caja_b[
            "bottom"
        ]
    )


    if (
        x1 <= x0
        or bottom <= top
    ):

        return 0.0


    return (
        x1
        - x0
    ) * (
        bottom
        - top
    )


# ================================================================
# DETECCIÓN DE TABLAS
# ================================================================

def obtener_paginas_con_tabla(
    distribucion
):

    paginas = []


    for pagina in distribucion.get(
        "paginas",
        []
    ):

        tablas = [
            elemento
            for elemento
            in pagina.get(
                "elementos",
                []
            )
            if elemento.get(
                "tipo"
            ) == "tabla_detectada"
        ]


        if tablas:

            paginas.append(
                (
                    pagina,
                    tablas
                )
            )


    return paginas


def obtener_region_tabla(
    tabla
):

    lineas = tabla.get(
        "lineas_origen",
        []
    )


    if lineas:

        return expandir_caja(
            combinar_cajas(
                lineas
            ),
            MARGEN_REGION_TABLA
        )


    return tabla.get(
        "caja",
        {
            "x0": 0.0,
            "top": 0.0,
            "x1": 0.0,
            "bottom": 0.0
        }
    )


def filtrar_rectangulos_region(
    rectangulos,
    region
):

    return [
        rectangulo
        for rectangulo
        in rectangulos
        if cajas_se_solapan(
            obtener_caja(
                rectangulo
            ),
            region
        )
    ]


# ================================================================
# AGRUPACIÓN DE LÍMITES
# ================================================================

def agrupar_valores(
    valores,
    tolerancia=TOLERANCIA_AGRUPACION
):

    if not valores:

        return []


    valores = sorted(
        float(
            valor
        )
        for valor
        in valores
    )


    grupos = [
        [
            valores[
                0
            ]
        ]
    ]


    for valor in valores[
        1:
    ]:

        grupo = grupos[
            -1
        ]


        promedio = statistics.mean(
            grupo
        )


        if abs(
            valor
            - promedio
        ) <= tolerancia:

            grupo.append(
                valor
            )


        else:

            grupos.append(
                [
                    valor
                ]
            )


    resultado = []


    for grupo in grupos:

        resultado.append(
            {
                "valor": redondear(
                    statistics.mean(
                        grupo
                    )
                ),

                "cantidad": len(
                    grupo
                ),

                "minimo": redondear(
                    min(
                        grupo
                    )
                ),

                "maximo": redondear(
                    max(
                        grupo
                    )
                )
            }
        )


    return resultado


def limpiar_limites(
    valores,
    distancia_minima=3.0
):

    if not valores:

        return []


    valores = sorted(
        valores
    )


    resultado = [
        valores[
            0
        ]
    ]


    for valor in valores[
        1:
    ]:

        if (
            valor
            - resultado[
                -1
            ]
            >= distancia_minima
        ):

            resultado.append(
                valor
            )


    return resultado


def detectar_lineas_verticales(
    rectangulos
):

    valores = []


    for rectangulo in rectangulos:

        ancho = obtener_ancho(
            rectangulo
        )


        alto = obtener_alto(
            rectangulo
        )


        if (
            ancho
            <= ANCHO_MAXIMO_LINEA_VERTICAL

            and alto
            >= ALTO_MINIMO_LINEA_VERTICAL
        ):

            valores.append(
                (
                    obtener_x0(
                        rectangulo
                    )
                    + obtener_x1(
                        rectangulo
                    )
                )
                / 2
            )


    return [
        grupo
        for grupo
        in agrupar_valores(
            valores
        )
        if grupo[
            "cantidad"
        ] >= 3
    ]


def detectar_lineas_horizontales(
    rectangulos
):

    valores = []


    for rectangulo in rectangulos:

        ancho = obtener_ancho(
            rectangulo
        )


        alto = obtener_alto(
            rectangulo
        )


        if (
            alto
            <= ALTO_MAXIMO_LINEA_HORIZONTAL

            and ancho
            >= ANCHO_MINIMO_LINEA_HORIZONTAL
        ):

            valores.append(
                (
                    obtener_top(
                        rectangulo
                    )
                    + obtener_bottom(
                        rectangulo
                    )
                )
                / 2
            )


    return [
        grupo
        for grupo
        in agrupar_valores(
            valores
        )
        if grupo[
            "cantidad"
        ] >= 3
    ]


def obtener_limites_columnas(
    rectangulos
):

    return limpiar_limites(
        [
            grupo[
                "valor"
            ]
            for grupo
            in detectar_lineas_verticales(
                rectangulos
            )
        ]
    )


def obtener_limites_filas(
    rectangulos
):

    return limpiar_limites(
        [
            grupo[
                "valor"
            ]
            for grupo
            in detectar_lineas_horizontales(
                rectangulos
            )
        ]
    )


# ================================================================
# PALABRAS DE LA TABLA
# ================================================================

def extraer_palabras_tabla(
    lineas
):

    palabras = []


    for indice_linea, linea in enumerate(
        lineas
    ):

        for indice_palabra, palabra in enumerate(
            linea.get(
                "palabras",
                []
            )
        ):

            texto = normalizar_texto(
                palabra.get(
                    "texto"
                )
            )


            if not texto:

                continue


            copia = {
                "texto": texto,

                "caja": dict(
                    palabra.get(
                        "caja",
                        {}
                    )
                ),

                "fuente": palabra.get(
                    "fuente"
                ),

                "tamano": palabra.get(
                    "tamano"
                ),

                "color": palabra.get(
                    "color"
                ),

                "negrita": bool(
                    palabra.get(
                        "negrita",
                        False
                    )
                ),

                "cursiva": bool(
                    palabra.get(
                        "cursiva",
                        False
                    )
                ),

                "fragmentos": palabra.get(
                    "fragmentos",
                    []
                ),

                "indice_linea_origen": (
                    indice_linea
                ),

                "indice_palabra_origen": (
                    indice_palabra
                )
            }


            palabras.append(
                copia
            )


    palabras.sort(
        key=lambda palabra: (
            obtener_top(
                palabra
            ),
            obtener_x0(
                palabra
            )
        )
    )


    return palabras


def obtener_palabras_celda(
    palabras,
    caja_celda
):

    resultado = []


    for palabra in palabras:

        centro_x, centro_y = obtener_centro(
            palabra
        )


        if punto_en_caja(
            centro_x,
            centro_y,
            caja_celda
        ):

            resultado.append(
                palabra
            )


    resultado.sort(
        key=lambda palabra: (
            obtener_top(
                palabra
            ),
            obtener_x0(
                palabra
            )
        )
    )


    return resultado


# ================================================================
# LÍNEAS VISUALES DENTRO DE UNA CELDA
# ================================================================

def agrupar_palabras_por_linea(
    palabras
):

    if not palabras:

        return []


    ordenadas = sorted(
        palabras,
        key=lambda palabra: (
            obtener_centro(
                palabra
            )[
                1
            ],
            obtener_x0(
                palabra
            )
        )
    )


    grupos = []


    for palabra in ordenadas:

        centro_y = obtener_centro(
            palabra
        )[
            1
        ]


        grupo_elegido = None
        mejor_distancia = None


        for grupo in grupos:

            distancia = abs(
                centro_y
                - grupo[
                    "centro_y"
                ]
            )


            if distancia <= TOLERANCIA_LINEA_TEXTO:

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
                    "centro_y": centro_y,

                    "palabras": [
                        palabra
                    ]
                }
            )


        else:

            grupo_elegido[
                "palabras"
            ].append(
                palabra
            )


            grupo_elegido[
                "centro_y"
            ] = statistics.mean(
                obtener_centro(
                    elemento
                )[
                    1
                ]
                for elemento
                in grupo_elegido[
                    "palabras"
                ]
            )


    grupos.sort(
        key=lambda grupo: grupo[
            "centro_y"
        ]
    )


    resultado = []


    for grupo in grupos:

        grupo[
            "palabras"
        ].sort(
            key=obtener_x0
        )


        texto = " ".join(
            palabra[
                "texto"
            ]
            for palabra
            in grupo[
                "palabras"
            ]
        )


        resultado.append(
            {
                "texto": texto,

                "caja": combinar_cajas(
                    grupo[
                        "palabras"
                    ]
                ),

                "palabras": grupo[
                    "palabras"
                ]
            }
        )


    return resultado


def unir_texto_celda(
    lineas_visuales
):

    return " ".join(
        normalizar_texto(
            linea.get(
                "texto"
            )
        )
        for linea
        in lineas_visuales
        if normalizar_texto(
            linea.get(
                "texto"
            )
        )
    )


# ================================================================
# ESTILO
# ================================================================

def valor_mas_frecuente(
    valores,
    predeterminado=None
):

    valores = [
        valor
        for valor
        in valores
        if valor is not None
    ]


    if not valores:

        return predeterminado


    claves = []
    mapa = {}


    for valor in valores:

        clave = json.dumps(
            valor,
            ensure_ascii=False,
            sort_keys=True
        )


        claves.append(
            clave
        )


        mapa[
            clave
        ] = valor


    clave = Counter(
        claves
    ).most_common(
        1
    )[
        0
    ][
        0
    ]


    return mapa[
        clave
    ]


def obtener_estilo_celda(
    palabras
):

    if not palabras:

        return {
            "fuente": None,
            "tamano": None,
            "negrita": False,
            "cursiva": False,
            "color": None
        }


    tamanos = [
        redondear(
            palabra.get(
                "tamano"
            )
        )
        for palabra
        in palabras
        if palabra.get(
            "tamano"
        ) is not None
    ]


    total = len(
        palabras
    )


    return {
        "fuente": valor_mas_frecuente(
            [
                palabra.get(
                    "fuente"
                )
                for palabra
                in palabras
            ]
        ),

        "tamano": (
            redondear(
                statistics.median(
                    tamanos
                )
            )
            if tamanos
            else None
        ),

        "negrita": (
            sum(
                1
                for palabra
                in palabras
                if palabra.get(
                    "negrita"
                )
            )
            >= total
            / 2
        ),

        "cursiva": (
            sum(
                1
                for palabra
                in palabras
                if palabra.get(
                    "cursiva"
                )
            )
            >= total
            / 2
        ),

        "color": valor_mas_frecuente(
            [
                palabra.get(
                    "color"
                )
                for palabra
                in palabras
            ]
        )
    }


# ================================================================
# ALINEACIÓN
# ================================================================

def detectar_alineacion_celda(
    lineas_visuales,
    caja_celda
):

    if not lineas_visuales:

        return "izquierda"


    ancho_celda = (
        caja_celda[
            "x1"
        ]
        - caja_celda[
            "x0"
        ]
    )


    tolerancia_centro = max(
        5.0,
        ancho_celda
        * 0.06
    )


    tolerancia_margen = max(
        5.0,
        ancho_celda
        * 0.08
    )


    votos_centro = 0
    votos_derecha = 0
    votos_izquierda = 0


    for linea in lineas_visuales:

        caja = linea[
            "caja"
        ]


        margen_izquierdo = (
            caja[
                "x0"
            ]
            - caja_celda[
                "x0"
            ]
        )


        margen_derecho = (
            caja_celda[
                "x1"
            ]
            - caja[
                "x1"
            ]
        )


        centro_texto = (
            caja[
                "x0"
            ]
            + caja[
                "x1"
            ]
        ) / 2


        centro_celda = (
            caja_celda[
                "x0"
            ]
            + caja_celda[
                "x1"
            ]
        ) / 2


        if (
            abs(
                centro_texto
                - centro_celda
            )
            <= tolerancia_centro

            and abs(
                margen_izquierdo
                - margen_derecho
            )
            <= tolerancia_margen
        ):

            votos_centro += 1


        elif (
            margen_derecho
            <= tolerancia_margen

            and margen_izquierdo
            > tolerancia_margen
        ):

            votos_derecha += 1


        else:

            votos_izquierda += 1


    votos = {
        "centro": votos_centro,
        "derecha": votos_derecha,
        "izquierda": votos_izquierda
    }


    return max(
        votos,
        key=votos.get
    )


def detectar_alineacion_vertical(
    palabras,
    caja_celda
):

    if not palabras:

        return "centro"


    caja_texto = combinar_cajas(
        palabras
    )


    margen_superior = (
        caja_texto[
            "top"
        ]
        - caja_celda[
            "top"
        ]
    )


    margen_inferior = (
        caja_celda[
            "bottom"
        ]
        - caja_texto[
            "bottom"
        ]
    )


    alto_celda = (
        caja_celda[
            "bottom"
        ]
        - caja_celda[
            "top"
        ]
    )


    tolerancia = max(
        3.0,
        alto_celda
        * 0.12
    )


    if abs(
        margen_superior
        - margen_inferior
    ) <= tolerancia:

        return "centro"


    if margen_superior < margen_inferior:

        return "arriba"


    return "abajo"


# ================================================================
# RELLENOS
# ================================================================

def es_color_relleno_util(
    color
):

    if isinstance(
        color,
        (
            int,
            float
        )
    ):

        return True


    if (
        isinstance(
            color,
            (
                list,
                tuple
            )
        )
        and color
    ):

        return all(
            isinstance(
                valor,
                (
                    int,
                    float
                )
            )
            for valor
            in color
        )


    return False


def convertir_color_rgb(
    color
):

    if isinstance(
        color,
        (
            int,
            float
        )
    ):

        valor = max(
            0,
            min(
                255,
                round(
                    float(
                        color
                    )
                    * 255
                )
            )
        )


        return [
            valor,
            valor,
            valor
        ]


    if (
        isinstance(
            color,
            (
                list,
                tuple
            )
        )
        and color
    ):

        valores = list(
            color[
                :3
            ]
        )


        if len(
            valores
        ) == 1:

            valores *= 3


        while len(
            valores
        ) < 3:

            valores.append(
                valores[
                    -1
                ]
            )


        return [
            max(
                0,
                min(
                    255,
                    round(
                        float(
                            valor
                        )
                        * 255
                    )
                )
            )
            for valor
            in valores
        ]


    return None


def detectar_relleno_celda(
    rectangulos,
    caja_celda
):

    area_celda = calcular_area_caja(
        caja_celda
    )


    if area_celda <= 0:

        return None, None


    candidatos = []


    for rectangulo in rectangulos:

        if not rectangulo.get(
            "relleno",
            False
        ):

            continue


        color = rectangulo.get(
            "color_relleno"
        )


        # ----------------------------------- #
        # Los fondos tipo P267, P190, etc.    #
        # son patrones del fondo de página.   #
        # ----------------------------------- #

        if not es_color_relleno_util(
            color
        ):

            continue


        ancho = obtener_ancho(
            rectangulo
        )


        alto = obtener_alto(
            rectangulo
        )


        # ----------------------------------- #
        #        Descartar líneas finas       #
        # ----------------------------------- #

        if (
            ancho <= 2.0
            or alto <= 2.0
        ):

            continue


        caja_rectangulo = obtener_caja(
            rectangulo
        )


        interseccion = calcular_interseccion(
            caja_rectangulo,
            caja_celda
        )


        cobertura = (
            interseccion
            / area_celda
        )


        if cobertura < COBERTURA_MINIMA_RELLENO:

            continue


        area_rectangulo = calcular_area_caja(
            caja_rectangulo
        )


        diferencia_area = abs(
            area_rectangulo
            - area_celda
        ) / area_celda


        candidatos.append(
            {
                "cobertura": cobertura,

                "diferencia_area": (
                    diferencia_area
                ),

                "area": area_rectangulo,

                "color": color
            }
        )


    if not candidatos:

        return None, None


    candidatos.sort(
        key=lambda candidato: (
            candidato[
                "cobertura"
            ],

            -candidato[
                "diferencia_area"
            ],

            candidato[
                "area"
            ]
        ),
        reverse=True
    )


    color = candidatos[
        0
    ][
        "color"
    ]


    return (
        color,
        convertir_color_rgb(
            color
        )
    )


# ================================================================
# CELDAS
# ================================================================

def crear_caja_celda(
    x0,
    top,
    x1,
    bottom
):

    return {
        "x0": redondear(
            x0
        ),

        "top": redondear(
            top
        ),

        "x1": redondear(
            x1
        ),

        "bottom": redondear(
            bottom
        )
    }


def crear_celda(
    fila,
    columna,
    caja,
    palabras,
    rectangulos
):

    lineas_visuales = agrupar_palabras_por_linea(
        palabras
    )


    texto = unir_texto_celda(
        lineas_visuales
    )


    relleno, relleno_rgb = detectar_relleno_celda(
        rectangulos,
        caja
    )


    return {
        "fila": fila,

        "columna": columna,

        "caja": caja,

        "ancho": redondear(
            caja[
                "x1"
            ]
            - caja[
                "x0"
            ]
        ),

        "alto": redondear(
            caja[
                "bottom"
            ]
            - caja[
                "top"
            ]
        ),

        "texto": texto,

        "alineacion": detectar_alineacion_celda(
            lineas_visuales,
            caja
        ),

        "alineacion_vertical": (
            detectar_alineacion_vertical(
                palabras,
                caja
            )
        ),

        "estilo": obtener_estilo_celda(
            palabras
        ),

        "relleno": relleno,

        "relleno_rgb": relleno_rgb,

        "lineas_visuales": (
            lineas_visuales
        ),

        "palabras_origen": (
            palabras
        )
    }


def crear_celdas(
    limites_x,
    limites_y,
    palabras,
    rectangulos
):

    filas = []


    for indice_fila in range(
        len(
            limites_y
        )
        - 1
    ):

        top = limites_y[
            indice_fila
        ]


        bottom = limites_y[
            indice_fila
            + 1
        ]


        fila = {
            "indice": indice_fila,

            "top": redondear(
                top
            ),

            "bottom": redondear(
                bottom
            ),

            "alto": redondear(
                bottom
                - top
            ),

            "celdas": []
        }


        for indice_columna in range(
            len(
                limites_x
            )
            - 1
        ):

            x0 = limites_x[
                indice_columna
            ]


            x1 = limites_x[
                indice_columna
                + 1
            ]


            caja = crear_caja_celda(
                x0,
                top,
                x1,
                bottom
            )


            palabras_celda = obtener_palabras_celda(
                palabras,
                caja
            )


            fila[
                "celdas"
            ].append(
                crear_celda(
                    indice_fila,
                    indice_columna,
                    caja,
                    palabras_celda,
                    rectangulos
                )
            )


        filas.append(
            fila
        )


    return filas


# ================================================================
# BORDES
# ================================================================

def detectar_grosor_bordes(
    rectangulos
):

    grosores = []


    for rectangulo in rectangulos:

        ancho = obtener_ancho(
            rectangulo
        )


        alto = obtener_alto(
            rectangulo
        )


        if (
            ancho <= 1.4
            and alto >= 10.0
            and ancho > 0
        ):

            grosores.append(
                ancho
            )


        elif (
            alto <= 1.4
            and ancho >= 30.0
            and alto > 0
        ):

            grosores.append(
                alto
            )


    if not grosores:

        return None


    return redondear(
        statistics.median(
            grosores
        )
    )


# ================================================================
# RECONSTRUIR TABLA
# ================================================================

def reconstruir_tabla(
    pagina,
    tabla,
    indice_tabla
):

    rectangulos = tabla.get(
        "rectangulos_origen",
        []
    )


    lineas = tabla.get(
        "lineas_origen",
        []
    )


    region = obtener_region_tabla(
        tabla
    )


    rectangulos_region = filtrar_rectangulos_region(
        rectangulos,
        region
    )


    limites_x = obtener_limites_columnas(
        rectangulos_region
    )


    limites_y = obtener_limites_filas(
        rectangulos_region
    )


    if len(
        limites_x
    ) < 2:

        raise RuntimeError(
            "No fue posible detectar las columnas de la tabla."
        )


    if len(
        limites_y
    ) < 2:

        raise RuntimeError(
            "No fue posible detectar las filas de la tabla."
        )


    palabras = extraer_palabras_tabla(
        lineas
    )


    filas = crear_celdas(
        limites_x,
        limites_y,
        palabras,
        rectangulos_region
    )


    anchos_columnas = [
        redondear(
            limites_x[
                indice + 1
            ]
            - limites_x[
                indice
            ]
        )
        for indice
        in range(
            len(
                limites_x
            )
            - 1
        )
    ]


    altos_filas = [
        redondear(
            limites_y[
                indice + 1
            ]
            - limites_y[
                indice
            ]
        )
        for indice
        in range(
            len(
                limites_y
            )
            - 1
        )
    ]


    return {
        "pagina": pagina.get(
            "numero"
        ),

        "indice_tabla": indice_tabla,

        "caja_original": tabla.get(
            "caja"
        ),

        "region_analizada": region,

        "columnas": (
            len(
                limites_x
            )
            - 1
        ),

        "filas": (
            len(
                limites_y
            )
            - 1
        ),

        "limites_x": [
            redondear(
                valor
            )
            for valor
            in limites_x
        ],

        "limites_y": [
            redondear(
                valor
            )
            for valor
            in limites_y
        ],

        "anchos_columnas": (
            anchos_columnas
        ),

        "altos_filas": (
            altos_filas
        ),

        "grosor_borde_estimado": (
            detectar_grosor_bordes(
                rectangulos_region
            )
        ),

        "cantidad_rectangulos_originales": (
            len(
                rectangulos
            )
        ),

        "cantidad_rectangulos_region": (
            len(
                rectangulos_region
            )
        ),

        "cantidad_lineas_texto": (
            len(
                lineas
            )
        ),

        "cantidad_palabras": (
            len(
                palabras
            )
        ),

        "filas_reconstruidas": (
            filas
        )
    }


# ================================================================
# RESUMEN
# ================================================================

def formatear_relleno(
    celda
):

    relleno = celda.get(
        "relleno"
    )


    rgb = celda.get(
        "relleno_rgb"
    )


    if relleno is None:

        return "None"


    return (
        f"{relleno} | "
        f"RGB={rgb}"
    )


def generar_resumen(
    tablas
):

    lineas = [
        "PROTOTIPO PDF → DOCX",
        "RECONSTRUCCIÓN DE TABLAS",
        "=" * 72,
        ""
    ]


    for tabla in tablas:

        lineas.extend(
            [
                (
                    "Página: "
                    f"{tabla['pagina']}"
                ),

                (
                    "Tabla: "
                    f"{tabla['indice_tabla']}"
                ),

                (
                    "Columnas detectadas: "
                    f"{tabla['columnas']}"
                ),

                (
                    "Filas detectadas: "
                    f"{tabla['filas']}"
                ),

                (
                    "Límites X: "
                    f"{tabla['limites_x']}"
                ),

                (
                    "Límites Y: "
                    f"{tabla['limites_y']}"
                ),

                (
                    "Anchos de columnas: "
                    f"{tabla['anchos_columnas']}"
                ),

                (
                    "Altos de filas: "
                    f"{tabla['altos_filas']}"
                ),

                (
                    "Grosor de borde: "
                    f"{tabla['grosor_borde_estimado']} pt"
                ),

                (
                    "Palabras asignadas: "
                    f"{tabla['cantidad_palabras']}"
                ),

                "",

                "-" * 72,

                ""
            ]
        )


        for fila in tabla[
            "filas_reconstruidas"
        ]:

            lineas.append(
                (
                    "FILA "
                    f"{fila['indice'] + 1}"
                    " | alto "
                    f"{fila['alto']:.2f} pt"
                )
            )


            for celda in fila[
                "celdas"
            ]:

                texto = celda.get(
                    "texto",
                    ""
                )


                estilo = celda.get(
                    "estilo",
                    {}
                )


                lineas.append(
                    (
                        "  C"
                        f"{celda['columna'] + 1}: "
                        f"{texto}"
                    )
                )


                lineas.append(
                    (
                        "      "
                        "relleno="
                        f"{formatear_relleno(celda)} | "
                        "alineación="
                        f"{celda.get('alineacion')} | "
                        "vertical="
                        f"{celda.get('alineacion_vertical')} | "
                        "fuente="
                        f"{estilo.get('fuente')} | "
                        "tamaño="
                        f"{estilo.get('tamano')} | "
                        "negrita="
                        f"{estilo.get('negrita')}"
                    )
                )


            lineas.append(
                ""
            )


        lineas.extend(
            [
                "=" * 72,
                ""
            ]
        )


    return "\n".join(
        lineas
    )


# ================================================================
# DIAGNÓSTICO VISUAL
# ================================================================

def generar_diagnostico_visual(
    ruta_pdf,
    tabla
):

    numero_pagina = int(
        tabla[
            "pagina"
        ]
    )


    documento = pdfium.PdfDocument(
        str(
            ruta_pdf
        )
    )


    pagina = documento[
        numero_pagina - 1
    ]


    escala = 2.0


    bitmap = pagina.render(
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


    # ============================================================
    # COLUMNAS
    # ============================================================

    for indice, x in enumerate(
        tabla[
            "limites_x"
        ]
    ):

        px = int(
            x
            * escala
        )


        dibujo.line(
            (
                px,
                0,
                px,
                imagen.height
            ),

            fill=(
                255,
                0,
                255
            ),

            width=2
        )


        dibujo.text(
            (
                px + 3,

                int(
                    tabla[
                        "limites_y"
                    ][
                        0
                    ]
                    * escala
                )
                - 18
            ),

            f"X{indice}",

            fill=(
                255,
                0,
                255
            )
        )


    # ============================================================
    # FILAS
    # ============================================================

    for indice, y in enumerate(
        tabla[
            "limites_y"
        ]
    ):

        py = int(
            y
            * escala
        )


        dibujo.line(
            (
                0,
                py,
                imagen.width,
                py
            ),

            fill=(
                0,
                190,
                255
            ),

            width=2
        )


        dibujo.text(
            (
                int(
                    tabla[
                        "limites_x"
                    ][
                        0
                    ]
                    * escala
                )
                - 35,

                py + 2
            ),

            f"Y{indice}",

            fill=(
                0,
                120,
                220
            )
        )


    # ============================================================
    # CENTROS DE PALABRAS
    # ============================================================

    for fila in tabla[
        "filas_reconstruidas"
    ]:

        for celda in fila[
            "celdas"
        ]:

            for palabra in celda.get(
                "palabras_origen",
                []
            ):

                centro_x, centro_y = obtener_centro(
                    palabra
                )


                px = int(
                    centro_x
                    * escala
                )


                py = int(
                    centro_y
                    * escala
                )


                dibujo.ellipse(
                    (
                        px - 2,
                        py - 2,
                        px + 2,
                        py + 2
                    ),

                    fill=(
                        255,
                        80,
                        0
                    )
                )


    imagen.save(
        RUTA_DIAGNOSTICO,
        "PNG"
    )


    try:

        bitmap.close()


    except Exception:

        pass


    try:

        pagina.close()


    except Exception:

        pass


    try:

        documento.close()


    except Exception:

        pass


# ================================================================
# EJECUCIÓN PRINCIPAL
# ================================================================

def main():

    distribucion = cargar_json(
        RUTA_DISTRIBUCION
    )


    paginas_tabla = obtener_paginas_con_tabla(
        distribucion
    )


    if not paginas_tabla:

        raise RuntimeError(
            (
                "No se encontraron tablas detectadas "
                "en distribucion_pdf.json."
            )
        )


    cantidad_tablas = sum(
        len(
            tablas
        )
        for _,
        tablas
        in paginas_tabla
    )


    print()


    print(
        (
            "Tablas detectadas: "
            f"{cantidad_tablas}"
        )
    )


    print()


    tablas_reconstruidas = []


    for pagina, tablas in paginas_tabla:

        for indice, tabla in enumerate(
            tablas,
            start=1
        ):

            print(
                (
                    "Reconstruyendo tabla "
                    f"{indice} "
                    "de la página "
                    f"{pagina.get('numero')}..."
                )
            )


            resultado = reconstruir_tabla(
                pagina,
                tabla,
                indice
            )


            tablas_reconstruidas.append(
                resultado
            )


            print(
                (
                    "  Columnas: "
                    f"{resultado['columnas']}"
                )
            )


            print(
                (
                    "  Filas: "
                    f"{resultado['filas']}"
                )
            )


            print(
                (
                    "  Palabras: "
                    f"{resultado['cantidad_palabras']}"
                )
            )


    datos_salida = {
        "ruta_origen": distribucion.get(
            "ruta_origen"
        ),

        "cantidad_tablas": len(
            tablas_reconstruidas
        ),

        "tablas": tablas_reconstruidas
    }


    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        RUTA_TABLA,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos_salida,
            archivo,
            ensure_ascii=False,
            indent=2
        )


    RUTA_RESUMEN.write_text(
        generar_resumen(
            tablas_reconstruidas
        ),
        encoding="utf-8"
    )


    ruta_pdf = Path(
        distribucion.get(
            "ruta_origen",
            ""
        )
    )


    if (
        ruta_pdf.is_file()

        and tablas_reconstruidas
    ):

        generar_diagnostico_visual(
            ruta_pdf,
            tablas_reconstruidas[
                0
            ]
        )


    print()


    print(
        "Reconstrucción terminada."
    )


    print(
        (
            "JSON: "
            f"{RUTA_TABLA}"
        )
    )


    print(
        (
            "Resumen: "
            f"{RUTA_RESUMEN}"
        )
    )


    if RUTA_DIAGNOSTICO.is_file():

        print(
            (
                "Diagnóstico visual: "
                f"{RUTA_DIAGNOSTICO}"
            )
        )


    print()


if __name__ == "__main__":

    main()