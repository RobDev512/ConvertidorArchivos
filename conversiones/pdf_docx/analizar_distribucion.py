import json
import math
import re
import statistics

from collections import Counter
from pathlib import Path

from analizar_tabla import reconstruir_tabla
from extraer_recursos_pdf import extraer_imagenes_documento


# ================================================================
# RUTAS
# ================================================================

CARPETA_BASE = Path(
    __file__
).resolve().parent

CARPETA_SALIDA = (
    CARPETA_BASE
    / "salida"
)

RUTA_ANALISIS = (
    CARPETA_SALIDA
    / "analisis_pdf.json"
)

RUTA_PATRONES = (
    CARPETA_SALIDA
    / "recursos_fondo"
    / "patrones_fondo.json"
)

RUTA_DISTRIBUCION = (
    CARPETA_SALIDA
    / "distribucion_pdf.json"
)

RUTA_RESUMEN = (
    CARPETA_SALIDA
    / "resumen_distribucion.txt"
)

CARPETA_RECURSOS_PAGINAS = (
    CARPETA_SALIDA
    / "recursos_paginas"
)


# ================================================================
# CONSTANTES
# ================================================================

MARGENES_COMUNES = (
    18.0,
    36.0,
    54.0,
    72.0,
    90.0,
    108.0,
    126.0,
    144.0
)


# ================================================================
# JSON
# ================================================================
def cargar_json(
    ruta
):

    if not ruta.is_file():

        raise FileNotFoundError(
            (
                "No existe el archivo requerido: "
                f"{ruta}"
            )
        )


    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )


# ================================================================
# UTILIDADES NUMÉRICAS
# ================================================================
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


# ================================================================
# MEDIANA
# ================================================================
def mediana(
    valores,
    predeterminado=0.0
):

    validos = []


    for valor in valores:

        try:

            validos.append(
                float(
                    valor
                )
            )


        except (
            TypeError,
            ValueError
        ):

            pass


    if not validos:

        return predeterminado


    return statistics.median(
        validos
    )


# ================================================================
# AJUSTAR A MARGEN COMÚN
# ================================================================
def ajustar_a_margen_comun(
    valor,
    tolerancia=7.0
):

    valor = redondear(
        valor
    )


    candidato = min(
        MARGENES_COMUNES,
        key=lambda margen: abs(
            margen
            - valor
        )
    )


    if abs(
        candidato
        - valor
    ) <= tolerancia:

        return float(
            candidato
        )


    return valor


# ================================================================
# NORMALIZAR TEXTO
# ================================================================
def normalizar_texto(
    texto
):

    return re.sub(
        r"\s+",
        " ",
        str(
            texto
            or ""
        )
    ).strip()


# ================================================================
# NORMALIZAR PARA COMPARAR
# ================================================================
def normalizar_comparacion(
    texto
):

    texto = normalizar_texto(
        texto
    ).lower()


    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u"
    }


    for origen, destino in (
        reemplazos.items()
    ):

        texto = texto.replace(
            origen,
            destino
        )


    return texto


# ================================================================
# GEOMETRÍA
# ================================================================
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


# ================================================================
# COMBINAR CAJAS
# ================================================================
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


# ================================================================
# CENTRO DE CAJA
# ================================================================
def centro_caja(
    caja
):

    return (
        (
            redondear(
                caja.get(
                    "x0"
                )
            )
            + redondear(
                caja.get(
                    "x1"
                )
            )
        )
        / 2,

        (
            redondear(
                caja.get(
                    "top"
                )
            )
            + redondear(
                caja.get(
                    "bottom"
                )
            )
        )
        / 2
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


        clave = json.dumps(
            valor,
            ensure_ascii=False,
            sort_keys=True
        )


        contador[
            clave
        ] += 1


        originales.setdefault(
            clave,
            valor
        )


    if not contador:

        return predeterminado


    clave = contador.most_common(
        1
    )[0][0]


    return originales[
        clave
    ]


# ================================================================
# FONDO
# ================================================================
def obtener_imagenes_patron(
    xobjects
):

    resultado = []


    for xobject in (
        xobjects
        or []
    ):

        if (
            xobject.get(
                "subtipo"
            )
            == "/Image"
        ):

            resultado.append(
                xobject
            )


        resultado.extend(
            obtener_imagenes_patron(
                xobject.get(
                    "xobjects_hijos",
                    []
                )
            )
        )


    return resultado


# ================================================================
# DETECTAR FONDO SEMÁNTICO
# ================================================================
def detectar_fondo_semantico(
    datos_patrones,
    total_paginas
):

    patrones = datos_patrones.get(
        "patrones",
        []
    )


    grupos = {}


    for patron in patrones:

        imagenes = obtener_imagenes_patron(
            patron.get(
                "xobjects",
                []
            )
        )


        hashes = sorted(
            {
                imagen.get(
                    "hash_stream_raw"
                )
                for imagen
                in imagenes
                if imagen.get(
                    "hash_stream_raw"
                )
            }
        )


        geometria = patron.get(
            "geometria",
            {}
        )


        firma = {
            "bbox": geometria.get(
                "/BBox"
            ),

            "xstep": geometria.get(
                "/XStep"
            ),

            "ystep": geometria.get(
                "/YStep"
            ),

            "imagenes": hashes
        }


        clave = json.dumps(
            firma,
            ensure_ascii=False,
            sort_keys=True
        )


        if clave not in grupos:

            grupos[
                clave
            ] = {
                "firma": firma,
                "paginas": [],
                "recursos": [],
                "archivos_extraidos": []
            }


        grupo = grupos[
            clave
        ]


        grupo[
            "paginas"
        ].append(
            patron.get(
                "pagina"
            )
        )


        grupo[
            "recursos"
        ].append(
            patron.get(
                "recurso"
            )
        )


        for imagen in imagenes:

            archivo = imagen.get(
                "archivo_extraido"
            )


            if (
                archivo
                and archivo not in grupo[
                    "archivos_extraidos"
                ]
            ):

                grupo[
                    "archivos_extraidos"
                ].append(
                    archivo
                )


    lista = list(
        grupos.values()
    )


    lista.sort(
        key=lambda grupo: len(
            grupo[
                "paginas"
            ]
        ),
        reverse=True
    )


    if not lista:

        return {
            "detectado": False,
            "repetido": False,
            "paginas": [],
            "tipo": "desconocido"
        }


    principal = lista[
        0
    ]


    cantidad = len(
        principal[
            "paginas"
        ]
    )


    return {
        "detectado": True,

        "repetido": (
            cantidad
            >= max(
                2,
                math.ceil(
                    total_paginas
                    * 0.5
                )
            )
        ),

        "tipo": "textura_mosaico",

        "paginas": principal[
            "paginas"
        ],

        "cantidad_paginas": (
            cantidad
        ),

        "bbox_mosaico": principal[
            "firma"
        ].get(
            "bbox"
        ),

        "xstep": principal[
            "firma"
        ].get(
            "xstep"
        ),

        "ystep": principal[
            "firma"
        ].get(
            "ystep"
        ),

        "hashes_imagen": principal[
            "firma"
        ].get(
            "imagenes"
        ),

        "recursos_pdf": principal[
            "recursos"
        ],

        "archivos_extraidos": principal[
            "archivos_extraidos"
        ],

        "grupos_semanticos": len(
            lista
        )
    }


# ================================================================
# MÁRGENES
# ================================================================
def inferir_margenes_documento(
    analisis
):

    globales = analisis.get(
        "margenes_globales",
        {}
    )


    izquierdo = ajustar_a_margen_comun(
        globales.get(
            "izquierdo",
            72.0
        )
    )


    derecho = ajustar_a_margen_comun(
        globales.get(
            "derecho",
            72.0
        )
    )


    superior_original = redondear(
        globales.get(
            "superior",
            72.0
        )
    )


    inferior_original = redondear(
        globales.get(
            "inferior",
            72.0
        )
    )


    superior = ajustar_a_margen_comun(
        superior_original
    )


    distancias_pie = []


    for pagina in analisis.get(
        "paginas",
        []
    ):

        distancia = (
            pagina
            .get(
                "distancias_encabezado_pie",
                {}
            )
            .get(
                "pie_desde_borde_inferior"
            )
        )


        if distancia is not None:

            distancias_pie.append(
                distancia
            )


    pie_medio = mediana(
        distancias_pie,
        36.0
    )


    if inferior_original > 120.0:

        if (
            25.0
            <= pie_medio
            <= 50.0
        ):

            inferior = 72.0


        else:

            inferior = superior


    else:

        inferior = ajustar_a_margen_comun(
            inferior_original
        )


    return {
        "izquierdo": redondear(
            izquierdo
        ),

        "derecho": redondear(
            derecho
        ),

        "superior": redondear(
            superior
        ),

        "inferior": redondear(
            inferior
        ),

        "origen_estimado": {
            "izquierdo": redondear(
                globales.get(
                    "izquierdo"
                )
            ),

            "derecho": redondear(
                globales.get(
                    "derecho"
                )
            ),

            "superior": superior_original,

            "inferior": inferior_original
        },

        "confianza": (
            "alta_lateral_media_vertical"
        ),

        "nota": (
            "El margen inferior se corrige para no "
            "confundir el espacio vacío de la página "
            "con un margen real de Word."
        )
    }


# ================================================================
# TIPO DE PÁGINA
# ================================================================
def detectar_tipo_pagina(
    pagina
):

    numero = int(
        pagina.get(
            "numero",
            0
        )
    )


    lineas = pagina.get(
        "lineas_texto",
        []
    )


    rectangulos = pagina.get(
        "rectangulos",
        []
    )


    imagenes = pagina.get(
        "imagenes",
        []
    )


    textos = [
        normalizar_comparacion(
            linea.get(
                "texto"
            )
        )
        for linea
        in lineas
    ]


    tamanos = [
        redondear(
            linea.get(
                "tamano_promedio"
            )
        )
        for linea
        in lineas
    ]


    tiene_encabezado = any(
        linea.get(
            "zona"
        ) == "encabezado"
        for linea
        in lineas
    )


    tiene_pie = any(
        linea.get(
            "zona"
        ) == "pie"
        for linea
        in lineas
    )


    if (
        numero == 1
        and not tiene_encabezado
        and not tiene_pie
        and len(
            imagenes
        ) >= 3
        and max(
            tamanos
            or [
                0.0
            ]
        ) >= 30.0
    ):

        return "portada"


    lineas_indice = sum(
        1
        for linea
        in lineas
        if str(
            linea.get(
                "texto",
                ""
            )
        ).count(
            "_"
        ) >= 5
    )


    if (
        any(
            texto == "indice"
            for texto
            in textos
        )
        and lineas_indice >= 3
    ):

        return "indice"


    if len(
        rectangulos
    ) >= 100:

        return "tabla"


    if any(
        (
            texto == "referencias"
            or re.match(
                r"^\d+\.\s*referencias\b",
                texto
            )
        )
        for texto
        in textos
    ):

        return "referencias"


    return "contenido"


# ================================================================
# DETECTAR NIVEL DE TÍTULO
# ================================================================
def detectar_nivel_titulo(
    linea
):

    if linea.get(
        "zona"
    ) != "cuerpo":

        return None


    texto = normalizar_texto(
        linea.get(
            "texto"
        )
    )


    tamano = redondear(
        linea.get(
            "tamano_promedio"
        )
    )


    negrita = bool(
        linea.get(
            "negrita_predominante"
        )
    )


    cursiva = bool(
        linea.get(
            "cursiva_predominante"
        )
    )


    fuente = str(
        linea.get(
            "fuente_predominante",
            ""
        )
    ).lower()


    if tamano >= 28.0:

        return 0


    if (
        tamano >= 18.0
        and (
            negrita
            or "bold" in fuente
        )
        and len(
            texto
        ) <= 120
    ):

        return 1


    if (
        tamano >= 15.5
        and (
            negrita
            or "bold" in fuente
        )
        and (
            cursiva
            or "italic" in fuente
            or re.match(
                r"^\d+\.\d+\.",
                texto
            )
        )
        and len(
            texto
        ) <= 140
    ):

        return 2


    return None


# ================================================================
# DETECTAR VIÑETA
# ================================================================
def es_vineta(
    texto
):

    return normalizar_texto(
        texto
    ).startswith(
        (
            "•",
            "▪",
            "◦",
            "●",
            "○"
        )
    )


# ================================================================
# ELEMENTO NUMERADO
# ================================================================
def es_elemento_numerado(
    linea
):

    texto = normalizar_texto(
        linea.get(
            "texto"
        )
    )


    tamano = redondear(
        linea.get(
            "tamano_promedio"
        )
    )


    if tamano > 15.0:

        return False


    return bool(
        re.match(
            r"^\d+\.\s+\S",
            texto
        )
    )


# ================================================================
# ETIQUETA NUMERADA
# ================================================================
def es_etiqueta_numerada(
    linea
):

    texto = normalizar_texto(
        linea.get(
            "texto"
        )
    )


    tamano = redondear(
        linea.get(
            "tamano_promedio"
        )
    )


    negrita = bool(
        linea.get(
            "negrita_predominante"
        )
    )


    fuente = str(
        linea.get(
            "fuente_predominante",
            ""
        )
    ).lower()


    return (
        12.5
        <= tamano
        <= 15.0

        and (
            negrita
            or "bold" in fuente
        )

        and bool(
            re.match(
                r"^\d+\.\s+.+:\s*$",
                texto
            )
        )
    )


# ================================================================
# ENTRADA DE ÍNDICE
# ================================================================
def es_entrada_indice(
    linea
):

    return str(
        linea.get(
            "texto",
            ""
        )
    ).count(
        "_"
    ) >= 5


# ================================================================
# LIMPIAR ENTRADA DE ÍNDICE
# ================================================================
def limpiar_entrada_indice(
    texto
):

    texto = normalizar_texto(
        texto
    )


    coincidencia = re.match(
        r"^(.*?)_+\s*(\d+)\s*$",
        texto
    )


    if not coincidencia:

        return {
            "texto": texto,
            "pagina_destino": None
        }


    return {
        "texto": normalizar_texto(
            coincidencia.group(
                1
            )
        ),

        "pagina_destino": int(
            coincidencia.group(
                2
            )
        )
    }


# ================================================================
# PÁRRAFOS
# ================================================================
def calcular_separacion_vertical(
    anterior,
    actual
):

    return (
        obtener_top(
            actual
        )
        - obtener_bottom(
            anterior
        )
    )


# ================================================================
# DEBEN UNIRSE LÍNEAS
# ================================================================
def deben_unirse_lineas(
    anterior,
    actual
):

    tamano_anterior = redondear(
        anterior.get(
            "tamano_promedio"
        )
    )


    tamano_actual = redondear(
        actual.get(
            "tamano_promedio"
        )
    )


    if abs(
        tamano_anterior
        - tamano_actual
    ) > 2.2:

        return False


    espacio = calcular_separacion_vertical(
        anterior,
        actual
    )


    limite = max(
        6.5,
        min(
            9.0,
            max(
                tamano_anterior,
                tamano_actual,
                10.0
            )
            * 0.58
        )
    )


    if (
        espacio > limite
        or espacio < -2.0
    ):

        return False


    diferencia_x = abs(
        obtener_x0(
            anterior
        )
        - obtener_x0(
            actual
        )
    )


    if diferencia_x > 48.0:

        return False


    return True


# ================================================================
# UNIR TEXTO DE LÍNEAS
# ================================================================
def unir_texto_lineas(
    lineas
):

    resultado = ""


    for indice, linea in enumerate(
        lineas
    ):

        texto = normalizar_texto(
            linea.get(
                "texto"
            )
        )


        if not texto:

            continue


        if not resultado:

            resultado = texto

            continue


        anterior = normalizar_texto(
            lineas[
                indice - 1
            ].get(
                "texto"
            )
        )


        contiene_url = (
            "http://"
            in resultado
            or "https://"
            in resultado
            or anterior.startswith(
                (
                    "http://",
                    "https://"
                )
            )
        )


        if contiene_url:

            if (
                anterior.startswith(
                    (
                        "http://",
                        "https://"
                    )
                )

                or re.match(
                    r"^[A-Za-z0-9%/?=&._-]+$",
                    texto
                )
            ):

                resultado += texto

                continue


        if (
            resultado.endswith(
                "-"
            )
            and texto
            and texto[
                0
            ].islower()
        ):

            resultado = (
                resultado[
                    :-1
                ]
                + texto
            )


            continue


        resultado += (
            " "
            + texto
        )


    return resultado


# ================================================================
# ALINEACIÓN DE BLOQUE
# ================================================================
def obtener_alineacion_bloque(
    lineas
):

    valores = [
        linea.get(
            "alineacion_estimada",
            "izquierda"
        )
        for linea
        in lineas
    ]


    if not valores:

        return "izquierda"


    contador = Counter(
        valores
    )


    if contador.get(
        "justificada",
        0
    ) >= max(
        1,
        len(
            valores
        )
        // 2
    ):

        return "justificada"


    return contador.most_common(
        1
    )[0][0]


# ================================================================
# ESTILO DE BLOQUE
# ================================================================
def obtener_estilo_bloque(
    lineas
):

    if not lineas:

        return {}


    fuentes = [
        linea.get(
            "fuente_predominante",
            ""
        )
        for linea
        in lineas
    ]


    tamanos = [
        redondear(
            linea.get(
                "tamano_promedio"
            )
        )
        for linea
        in lineas
    ]


    return {
        "fuente": Counter(
            fuentes
        ).most_common(
            1
        )[0][0],

        "tamano": redondear(
            mediana(
                tamanos
            )
        ),

        "negrita": (
            sum(
                1
                for linea
                in lineas
                if linea.get(
                    "negrita_predominante"
                )
            )
            >= max(
                1,
                len(
                    lineas
                )
                / 2
            )
        ),

        "cursiva": (
            sum(
                1
                for linea
                in lineas
                if linea.get(
                    "cursiva_predominante"
                )
            )
            >= max(
                1,
                len(
                    lineas
                )
                / 2
            )
        ),

        "color": valor_mas_frecuente(
            [
                linea.get(
                    "color_predominante"
                )
                for linea
                in lineas
            ]
        )
    }


# ================================================================
# ALINEACIÓN GEOMÉTRICA
# ================================================================
def detectar_alineacion_geometrica(
    lineas,
    pagina,
    margenes
):

    if not lineas:

        return "izquierda"


    caja = combinar_cajas(
        lineas
    )


    ancho_pagina = redondear(
        pagina.get(
            "ancho"
        )
    )


    centro_texto = (
        caja[
            "x0"
        ]
        + caja[
            "x1"
        ]
    ) / 2


    centro_pagina = (
        ancho_pagina
        / 2
    )


    limite_izquierdo = (
        margenes[
            "izquierdo"
        ]
    )


    limite_derecho = (
        ancho_pagina
        - margenes[
            "derecho"
        ]
    )


    centro_util = (
        limite_izquierdo
        + limite_derecho
    ) / 2


    if (
        abs(
            centro_texto
            - centro_pagina
        )
        <= 14.0

        or abs(
            centro_texto
            - centro_util
        )
        <= 14.0
    ):

        return "centro"


    if abs(
        caja[
            "x1"
        ]
        - limite_derecho
    ) <= 12.0:

        return "derecha"


    return "izquierda"


# ================================================================
# CALCULAR SANGRÍAS
# ================================================================
def calcular_sangrias(
    lineas,
    margen_izquierdo,
    margen_derecho,
    ancho_pagina
):

    if not lineas:

        return {
            "izquierda": 0.0,
            "derecha": 0.0,
            "primera_linea": 0.0,
            "francesa": 0.0
        }


    primer_x = obtener_x0(
        lineas[
            0
        ]
    )


    if len(
        lineas
    ) >= 2:

        x_continuacion = mediana(
            [
                obtener_x0(
                    linea
                )
                for linea
                in lineas[
                    1:
                ]
            ],
            primer_x
        )


    else:

        x_continuacion = primer_x


    sangria_izquierda = max(
        0.0,
        x_continuacion
        - margen_izquierdo
    )


    primera_linea = (
        primer_x
        - x_continuacion
    )


    limite_derecho = (
        ancho_pagina
        - margen_derecho
    )


    x1_medio = mediana(
        [
            obtener_x1(
                linea
            )
            for linea
            in lineas
        ],
        limite_derecho
    )


    sangria_derecha = max(
        0.0,
        limite_derecho
        - x1_medio
    )


    if primera_linea < -10.0:

        francesa = abs(
            primera_linea
        )


    else:

        francesa = 0.0


    return {
        "izquierda": redondear(
            sangria_izquierda
        ),

        "derecha": redondear(
            sangria_derecha
        ),

        "primera_linea": redondear(
            primera_linea
        ),

        "francesa": redondear(
            francesa
        )
    }


# ================================================================
# CREAR ELEMENTO
# ================================================================
def crear_elemento(
    tipo,
    lineas,
    pagina,
    margenes,
    datos_extra=None,
    alineacion_forzada=None
):

    if not lineas:

        return None


    ancho_pagina = redondear(
        pagina.get(
            "ancho"
        )
    )


    elemento = {
        "tipo": tipo,

        "texto": unir_texto_lineas(
            lineas
        ),

        "caja": combinar_cajas(
            lineas
        ),

        "alineacion": (
            alineacion_forzada
            if alineacion_forzada
            is not None
            else obtener_alineacion_bloque(
                lineas
            )
        ),

        "estilo": obtener_estilo_bloque(
            lineas
        ),

        "sangrias": calcular_sangrias(
            lineas,
            margenes[
                "izquierdo"
            ],
            margenes[
                "derecho"
            ],
            ancho_pagina
        ),

        "cantidad_lineas": len(
            lineas
        ),

        "lineas_origen": lineas
    }


    if datos_extra:

        elemento.update(
            datos_extra
        )


    return elemento


# ================================================================
# PORTADA
# ================================================================
def analizar_portada(
    pagina,
    margenes
):

    elementos = []


    lineas = [
        linea
        for linea
        in pagina.get(
            "lineas_texto",
            []
        )
        if linea.get(
            "zona"
        ) == "cuerpo"
    ]


    for linea in lineas:

        nivel = detectar_nivel_titulo(
            linea
        )


        if nivel == 0:

            tipo = (
                "titulo_portada_principal"
            )


        elif nivel == 1:

            tipo = "titulo_portada"


        elif es_vineta(
            linea.get(
                "texto"
            )
        ):

            tipo = "vineta_portada"


        else:

            tipo = "texto_portada"


        alineacion = (
            detectar_alineacion_geometrica(
                [
                    linea
                ],
                pagina,
                margenes
            )
        )


        elemento = crear_elemento(
            tipo,
            [
                linea
            ],
            pagina,
            margenes,
            alineacion_forzada=(
                alineacion
            )
        )


        if elemento:

            elementos.append(
                elemento
            )


    return elementos


# ================================================================
# ÍNDICE
# ================================================================
def analizar_indice(
    pagina,
    margenes
):

    elementos = []


    for linea in pagina.get(
        "lineas_texto",
        []
    ):

        if linea.get(
            "zona"
        ) != "cuerpo":

            continue


        texto = normalizar_texto(
            linea.get(
                "texto"
            )
        )


        if es_entrada_indice(
            linea
        ):

            datos_indice = (
                limpiar_entrada_indice(
                    texto
                )
            )


            elemento = crear_elemento(
                "entrada_indice",
                [
                    linea
                ],
                pagina,
                margenes,
                datos_indice
            )


        else:

            nivel = detectar_nivel_titulo(
                linea
            )


            if (
                normalizar_comparacion(
                    texto
                )
                == "indice"
            ):

                tipo = "titulo_indice"


            elif nivel is not None:

                tipo = "titulo"


            else:

                tipo = "texto_indice"


            elemento = crear_elemento(
                tipo,
                [
                    linea
                ],
                pagina,
                margenes
            )


        if elemento:

            elementos.append(
                elemento
            )


    return elementos


# ================================================================
# REFERENCIAS
# ================================================================
def analizar_referencias(
    pagina,
    margenes
):

    elementos = []


    lineas = [
        linea
        for linea
        in pagina.get(
            "lineas_texto",
            []
        )
        if linea.get(
            "zona"
        ) == "cuerpo"
    ]


    if not lineas:

        return elementos


    indice_inicio = 0


    for indice, linea in enumerate(
        lineas
    ):

        texto = normalizar_comparacion(
            linea.get(
                "texto"
            )
        )


        if (
            texto == "referencias"

            or re.match(
                r"^\d+\.\s*referencias\b",
                texto
            )
        ):

            elemento = crear_elemento(
                "titulo",
                [
                    linea
                ],
                pagina,
                margenes,
                {
                    "nivel": 1
                }
            )


            if elemento:

                elementos.append(
                    elemento
                )


            indice_inicio = (
                indice
                + 1
            )


            break


    restantes = lineas[
        indice_inicio:
    ]


    margen_base = (
        margenes[
            "izquierdo"
        ]
    )


    grupo_actual = []


    for linea in restantes:

        x0 = obtener_x0(
            linea
        )


        comienza_en_margen = (
            x0
            <= margen_base
            + 10.0
        )


        if (
            grupo_actual
            and comienza_en_margen
        ):

            elemento = crear_elemento(
                "referencia",
                grupo_actual,
                pagina,
                margenes
            )


            if elemento:

                elementos.append(
                    elemento
                )


            grupo_actual = []


        grupo_actual.append(
            linea
        )


    if grupo_actual:

        elemento = crear_elemento(
            "referencia",
            grupo_actual,
            pagina,
            margenes
        )


        if elemento:

            elementos.append(
                elemento
            )


    return elementos


# ================================================================
# PÁGINA CON TABLA
# ================================================================
def analizar_pagina_tabla(
    pagina,
    margenes
):

    elementos = []


    lineas_cuerpo = [
        linea
        for linea
        in pagina.get(
            "lineas_texto",
            []
        )
        if linea.get(
            "zona"
        ) == "cuerpo"
    ]


    if not lineas_cuerpo:

        return elementos


    titulo = None


    for linea in lineas_cuerpo:

        if (
            detectar_nivel_titulo(
                linea
            )
            is not None
        ):

            titulo = linea

            break


    if titulo is not None:

        elemento_titulo = (
            crear_elemento(
                "titulo",
                [
                    titulo
                ],
                pagina,
                margenes,
                {
                    "nivel": 1
                }
            )
        )


        if elemento_titulo:

            elementos.append(
                elemento_titulo
            )


    lineas_tabla = [
        linea
        for linea
        in lineas_cuerpo
        if (
            titulo is None

            or obtener_top(
                linea
            )
            > obtener_bottom(
                titulo
            )
            + 2.0
        )
    ]


    if lineas_tabla:

        elementos.append(
            {
                "tipo": (
                    "tabla_detectada"
                ),

                "texto": "",

                "caja": combinar_cajas(
                    lineas_tabla
                ),

                "cantidad_lineas_texto": (
                    len(
                        lineas_tabla
                    )
                ),

                "cantidad_rectangulos": (
                    len(
                        pagina.get(
                            "rectangulos",
                            []
                        )
                    )
                ),

                "lineas_origen": (
                    lineas_tabla
                ),

                "rectangulos_origen": (
                    pagina.get(
                        "rectangulos",
                        []
                    )
                ),

                "estado": (
                    "pendiente_reconstruccion_celdas"
                )
            }
        )


    return elementos


# ================================================================
# CORREGIR ALINEACIÓN DE CELDA
# ================================================================
def corregir_alineacion_celda(
    celda
):

    lineas = celda.get(
        "lineas_visuales",
        []
    )


    caja = celda.get(
        "caja",
        {}
    )


    if not lineas:

        return celda.get(
            "alineacion",
            "izquierda"
        )


    margenes_izquierdos = []

    margenes_derechos = []


    for linea in lineas:

        caja_linea = linea.get(
            "caja",
            {}
        )


        margenes_izquierdos.append(
            redondear(
                caja_linea.get(
                    "x0"
                )
            )
            - redondear(
                caja.get(
                    "x0"
                )
            )
        )


        margenes_derechos.append(
            redondear(
                caja.get(
                    "x1"
                )
            )
            - redondear(
                caja_linea.get(
                    "x1"
                )
            )
        )


    cantidad = len(
        lineas
    )


    pegadas_izquierda = sum(
        1
        for margen
        in margenes_izquierdos
        if margen <= 4.5
    )


    pegadas_derecha = sum(
        1
        for margen
        in margenes_derechos
        if margen <= 4.5
    )


    if (
        pegadas_izquierda
        / cantidad
        >= 0.60
    ):

        return "izquierda"


    if (
        pegadas_derecha
        / cantidad
        >= 0.60
    ):

        return "derecha"


    diferencias = [
        abs(
            izquierdo
            - derecho
        )
        for izquierdo, derecho
        in zip(
            margenes_izquierdos,
            margenes_derechos
        )
    ]


    if mediana(
        diferencias,
        999.0
    ) <= 10.0:

        return "centro"


    return "izquierda"


# ================================================================
# CORREGIR ALINEACIONES DE TABLA
# ================================================================
def corregir_alineaciones_tabla(
    datos_tabla
):

    for fila in datos_tabla.get(
        "filas_reconstruidas",
        []
    ):

        for celda in fila.get(
            "celdas",
            []
        ):

            celda[
                "alineacion"
            ] = corregir_alineacion_celda(
                celda
            )


    return datos_tabla


# ================================================================
# INTEGRAR TABLAS
# ================================================================
def integrar_tablas(
    elementos,
    pagina
):

    resultado = []

    indice_tabla = 0


    for elemento in elementos:

        if elemento.get(
            "tipo"
        ) != "tabla_detectada":

            resultado.append(
                elemento
            )


            continue


        indice_tabla += 1


        datos = reconstruir_tabla(
            pagina,
            elemento,
            indice_tabla
        )


        datos = corregir_alineaciones_tabla(
            datos
        )


        resultado.append(
            {
                "tipo": "tabla",

                "texto": "",

                "caja": elemento.get(
                    "caja"
                ),

                "estado": (
                    "reconstruida"
                ),

                "datos_tabla": datos
            }
        )


    return resultado


# ================================================================
# CONTENIDO NORMAL
# ================================================================
def analizar_contenido(
    pagina,
    margenes
):

    elementos = []


    lineas = [
        linea
        for linea
        in pagina.get(
            "lineas_texto",
            []
        )
        if linea.get(
            "zona"
        ) == "cuerpo"
    ]


    grupo_parrafo = []


    def vaciar_parrafo():

        nonlocal grupo_parrafo


        if not grupo_parrafo:

            return


        elemento = crear_elemento(
            "parrafo",
            grupo_parrafo,
            pagina,
            margenes
        )


        if elemento:

            elementos.append(
                elemento
            )


        grupo_parrafo = []


    for linea in lineas:

        nivel_titulo = (
            detectar_nivel_titulo(
                linea
            )
        )


        if nivel_titulo is not None:

            vaciar_parrafo()


            elemento = crear_elemento(
                "titulo",
                [
                    linea
                ],
                pagina,
                margenes,
                {
                    "nivel": (
                        nivel_titulo
                    )
                }
            )


            if elemento:

                elementos.append(
                    elemento
                )


            continue


        if es_vineta(
            linea.get(
                "texto"
            )
        ):

            vaciar_parrafo()


            elemento = crear_elemento(
                "elemento_lista_vineta",
                [
                    linea
                ],
                pagina,
                margenes
            )


            if elemento:

                elementos.append(
                    elemento
                )


            continue


        if es_etiqueta_numerada(
            linea
        ):

            vaciar_parrafo()


            elemento = crear_elemento(
                "elemento_lista_titulo",
                [
                    linea
                ],
                pagina,
                margenes
            )


            if elemento:

                elementos.append(
                    elemento
                )


            continue


        if es_elemento_numerado(
            linea
        ):

            vaciar_parrafo()


            elemento = crear_elemento(
                "elemento_lista_numerada",
                [
                    linea
                ],
                pagina,
                margenes
            )


            if elemento:

                elementos.append(
                    elemento
                )


            continue


        if not grupo_parrafo:

            grupo_parrafo = [
                linea
            ]


            continue


        if deben_unirse_lineas(
            grupo_parrafo[
                -1
            ],
            linea
        ):

            grupo_parrafo.append(
                linea
            )


        else:

            vaciar_parrafo()


            grupo_parrafo = [
                linea
            ]


    vaciar_parrafo()


    return elementos


# ================================================================
# ENCABEZADO
# ================================================================
def extraer_encabezado(
    pagina,
    margenes
):

    lineas = [
        linea
        for linea
        in pagina.get(
            "lineas_texto",
            []
        )
        if linea.get(
            "zona"
        ) == "encabezado"
    ]


    if not lineas:

        return None


    alineacion = (
        detectar_alineacion_geometrica(
            lineas,
            pagina,
            margenes
        )
    )


    elemento = crear_elemento(
        "encabezado",
        lineas,
        pagina,
        margenes,
        alineacion_forzada=(
            alineacion
        )
    )


    elemento[
        "distancia_desde_borde_superior"
    ] = (
        pagina
        .get(
            "distancias_encabezado_pie",
            {}
        )
        .get(
            "encabezado_desde_borde_superior"
        )
    )


    return elemento


# ================================================================
# CREAR LÍNEA SINTÉTICA DESDE PALABRAS
# ================================================================
def crear_linea_sintetica_desde_palabras(
    palabras,
    linea_base
):

    palabras = sorted(
        palabras,
        key=lambda palabra: obtener_x0(
            palabra
        )
    )


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
        "texto": " ".join(
            normalizar_texto(
                palabra.get(
                    "texto"
                )
            )
            for palabra
            in palabras
            if normalizar_texto(
                palabra.get(
                    "texto"
                )
            )
        ),

        "caja": combinar_cajas(
            palabras
        ),

        "fuente_predominante": (
            valor_mas_frecuente(
                [
                    palabra.get(
                        "fuente"
                    )
                    for palabra
                    in palabras
                ],
                linea_base.get(
                    "fuente_predominante",
                    ""
                )
            )
        ),

        "tamano_promedio": redondear(
            mediana(
                tamanos,
                linea_base.get(
                    "tamano_promedio",
                    0.0
                )
            )
        ),

        "color_predominante": (
            valor_mas_frecuente(
                [
                    palabra.get(
                        "color"
                    )
                    for palabra
                    in palabras
                ],
                linea_base.get(
                    "color_predominante"
                )
            )
        ),

        "negrita_predominante": (
            sum(
                1
                for palabra
                in palabras
                if palabra.get(
                    "negrita"
                )
            )
            >= max(
                1,
                total
                / 2
            )
        ),

        "cursiva_predominante": (
            sum(
                1
                for palabra
                in palabras
                if palabra.get(
                    "cursiva"
                )
            )
            >= max(
                1,
                total
                / 2
            )
        ),

        "alineacion_estimada": (
            "sin_analizar"
        ),

        "zona": "pie",

        "palabras": palabras
    }


# ================================================================
# AGRUPAR PALABRAS DEL PIE
# ================================================================
def agrupar_palabras_pie(
    lineas
):

    grupos_lineas = []


    for linea in lineas:

        palabras = sorted(
            linea.get(
                "palabras",
                []
            ),
            key=lambda palabra: obtener_x0(
                palabra
            )
        )


        if len(
            palabras
        ) < 2:

            if palabras:

                grupos_lineas.append(
                    (
                        palabras,
                        linea
                    )
                )


            else:

                grupos_lineas.append(
                    (
                        [],
                        linea
                    )
                )


            continue


        gaps = []


        for anterior, actual in zip(
            palabras,
            palabras[
                1:
            ]
        ):

            gaps.append(
                max(
                    0.0,
                    obtener_x0(
                        actual
                    )
                    - obtener_x1(
                        anterior
                    )
                )
            )


        positivos = [
            gap
            for gap
            in gaps
            if gap > 0.0
        ]


        base = mediana(
            positivos,
            4.0
        )


        umbral = max(
            45.0,
            base
            * 6.0
        )


        grupos = [
            [
                palabras[
                    0
                ]
            ]
        ]


        for indice, palabra in enumerate(
            palabras[
                1:
            ]
        ):

            gap = gaps[
                indice
            ]


            if gap >= umbral:

                grupos.append(
                    [
                        palabra
                    ]
                )


            else:

                grupos[
                    -1
                ].append(
                    palabra
                )


        for grupo in grupos:

            grupos_lineas.append(
                (
                    grupo,
                    linea
                )
            )


    return grupos_lineas


# ================================================================
# CLASIFICAR ZONA HORIZONTAL
# ================================================================
def clasificar_zona_horizontal(
    caja,
    ancho_pagina
):

    centro_x, _ = centro_caja(
        caja
    )


    if centro_x < (
        ancho_pagina
        / 3
    ):

        return "izquierda"


    if centro_x > (
        ancho_pagina
        * 2
        / 3
    ):

        return "derecha"


    return "centro"


# ================================================================
# PIE DE PÁGINA
# ================================================================
def extraer_pie(
    pagina,
    margenes
):

    lineas = [
        linea
        for linea
        in pagina.get(
            "lineas_texto",
            []
        )
        if linea.get(
            "zona"
        ) == "pie"
    ]


    if not lineas:

        return None


    ancho_pagina = redondear(
        pagina.get(
            "ancho"
        )
    )


    zonas = []


    for palabras, linea_base in (
        agrupar_palabras_pie(
            lineas
        )
    ):

        if palabras:

            linea = (
                crear_linea_sintetica_desde_palabras(
                    palabras,
                    linea_base
                )
            )


        else:

            linea = linea_base


        caja = combinar_cajas(
            [
                linea
            ]
        )


        posicion = (
            clasificar_zona_horizontal(
                caja,
                ancho_pagina
            )
        )


        alineacion = {
            "izquierda": "izquierda",
            "centro": "centro",
            "derecha": "derecha"
        }[
            posicion
        ]


        elemento = crear_elemento(
            (
                f"pie_"
                f"{posicion}"
            ),
            [
                linea
            ],
            pagina,
            margenes,
            alineacion_forzada=(
                alineacion
            )
        )


        elemento[
            "posicion_horizontal"
        ] = posicion


        zonas.append(
            elemento
        )


    zonas.sort(
        key=lambda zona: (
            zona.get(
                "caja",
                {}
            ).get(
                "x0",
                0.0
            )
        )
    )


    return {
        "tipo": "pie",

        "texto": " | ".join(
            zona.get(
                "texto",
                ""
            )
            for zona
            in zonas
        ),

        "zonas": zonas,

        "distancia_desde_borde_inferior": (
            pagina
            .get(
                "distancias_encabezado_pie",
                {}
            )
            .get(
                "pie_desde_borde_inferior"
            )
        )
    }


# ================================================================
# CLASIFICAR IMAGEN
# ================================================================
def clasificar_imagen(
    pagina,
    imagen
):

    caja = imagen.get(
        "caja",
        {}
    )


    x0 = redondear(
        caja.get(
            "x0"
        )
    )


    x1 = redondear(
        caja.get(
            "x1"
        )
    )


    top = redondear(
        caja.get(
            "top"
        )
    )


    bottom = redondear(
        caja.get(
            "bottom"
        )
    )


    ancho = max(
        0.0,
        x1
        - x0
    )


    alto = max(
        0.0,
        bottom
        - top
    )


    numero = int(
        pagina.get(
            "numero",
            0
        )
    )


    if numero == 1:

        if (
            top < 180.0
            and x0 < 260.0
            and alto > 50.0
        ):

            return (
                "logo_o_imagen_institucional_izquierda"
            )


        if (
            top < 180.0
            and x0 > 400.0
            and alto > 50.0
        ):

            return (
                "logo_o_imagen_institucional_derecha"
            )


        if (
            top < 50.0
            and ancho > 400.0
            and alto < 30.0
        ):

            return "franja_superior"


        if (
            alto < 65.0
            and ancho > 250.0
        ):

            return (
                "efecto_grafico_texto"
            )


    return "imagen_o_efecto"


# ================================================================
# CREAR RECURSOS GRÁFICOS
# ================================================================
def crear_recursos_graficos(
    pagina,
    recursos_extraidos
):

    numero = int(
        pagina.get(
            "numero",
            0
        )
    )


    recursos_pagina = (
        recursos_extraidos.get(
            numero,
            {}
        )
    )


    imagenes = []


    for imagen in pagina.get(
        "imagenes",
        []
    ):

        nombre = str(
            imagen.get(
                "nombre",
                ""
            )
        )


        extraido = recursos_pagina.get(
            nombre,
            {}
        )


        imagenes.append(
            {
                **imagen,

                "rol_estimado": (
                    clasificar_imagen(
                        pagina,
                        imagen
                    )
                ),

                "archivo_extraido": (
                    extraido.get(
                        "archivo"
                    )
                ),

                "extraida": bool(
                    extraido.get(
                        "extraida"
                    )
                ),

                "sha256_raw": (
                    extraido.get(
                        "sha256_raw"
                    )
                ),

                "objgen": (
                    extraido.get(
                        "objgen"
                    )
                )
            }
        )


    resultado = {
        "imagenes": imagenes
    }


    if numero == 1:

        rectangulos = []


        for rectangulo in pagina.get(
            "rectangulos",
            []
        ):

            caja = rectangulo.get(
                "caja",
                {}
            )


            ancho = max(
                0.0,
                redondear(
                    caja.get(
                        "x1"
                    )
                )
                - redondear(
                    caja.get(
                        "x0"
                    )
                )
            )


            alto = max(
                0.0,
                redondear(
                    caja.get(
                        "bottom"
                    )
                )
                - redondear(
                    caja.get(
                        "top"
                    )
                )
            )


            cobertura = (
                ancho
                * alto
            ) / max(
                1.0,
                redondear(
                    pagina.get(
                        "ancho"
                    )
                )
                * redondear(
                    pagina.get(
                        "alto"
                    )
                )
            )


            if cobertura >= 0.90:

                continue


            if (
                ancho <= 1.0
                and alto <= 1.0
            ):

                continue


            rectangulos.append(
                rectangulo
            )


        resultado[
            "rectangulos_portada"
        ] = rectangulos


        resultado[
            "lineas_vectoriales_portada"
        ] = pagina.get(
            "lineas_vectoriales",
            []
        )


    return resultado


# ================================================================
# ESPACIADOS
# ================================================================
def calcular_espaciados(
    elementos
):

    for indice, elemento in enumerate(
        elementos
    ):

        caja = elemento.get(
            "caja",
            {}
        )


        if indice == 0:

            elemento[
                "espacio_antes"
            ] = 0.0


        else:

            anterior = elementos[
                indice - 1
            ]


            caja_anterior = anterior.get(
                "caja",
                {}
            )


            espacio = (
                redondear(
                    caja.get(
                        "top"
                    )
                )
                - redondear(
                    caja_anterior.get(
                        "bottom"
                    )
                )
            )


            elemento[
                "espacio_antes"
            ] = redondear(
                max(
                    0.0,
                    espacio
                )
            )


        if (
            indice
            + 1
            < len(
                elementos
            )
        ):

            siguiente = elementos[
                indice + 1
            ]


            caja_siguiente = siguiente.get(
                "caja",
                {}
            )


            espacio = (
                redondear(
                    caja_siguiente.get(
                        "top"
                    )
                )
                - redondear(
                    caja.get(
                        "bottom"
                    )
                )
            )


            elemento[
                "espacio_despues"
            ] = redondear(
                max(
                    0.0,
                    espacio
                )
            )


        else:

            elemento[
                "espacio_despues"
            ] = 0.0


# ================================================================
# ANALIZAR PÁGINA
# ================================================================
def analizar_pagina(
    pagina,
    margenes,
    recursos_extraidos
):

    tipo_pagina = detectar_tipo_pagina(
        pagina
    )


    encabezado = extraer_encabezado(
        pagina,
        margenes
    )


    pie = extraer_pie(
        pagina,
        margenes
    )


    if tipo_pagina == "portada":

        elementos = analizar_portada(
            pagina,
            margenes
        )


    elif tipo_pagina == "indice":

        elementos = analizar_indice(
            pagina,
            margenes
        )


    elif tipo_pagina == "tabla":

        elementos = analizar_pagina_tabla(
            pagina,
            margenes
        )


        elementos = integrar_tablas(
            elementos,
            pagina
        )


    elif tipo_pagina == "referencias":

        elementos = analizar_referencias(
            pagina,
            margenes
        )


    else:

        elementos = analizar_contenido(
            pagina,
            margenes
        )


    calcular_espaciados(
        elementos
    )


    return {
        "numero": pagina.get(
            "numero"
        ),

        "tipo": tipo_pagina,

        "ancho": pagina.get(
            "ancho"
        ),

        "alto": pagina.get(
            "alto"
        ),

        "encabezado": encabezado,

        "pie": pie,

        "borde_pagina": pagina.get(
            "borde_pagina"
        ),

        "fondo_pagina_original": (
            pagina.get(
                "fondo_pagina"
            )
        ),

        "recursos_graficos": (
            crear_recursos_graficos(
                pagina,
                recursos_extraidos
            )
        ),

        "elementos": elementos
    }


# ================================================================
# CREAR RESUMEN
# ================================================================
def crear_resumen(
    distribucion
):

    lineas = []


    lineas.append(
        "PROTOTIPO PDF → DOCX"
    )


    lineas.append(
        "ANÁLISIS DE DISTRIBUCIÓN INTEGRADO"
    )


    lineas.append(
        "=" * 72
    )


    lineas.append(
        ""
    )


    margenes = distribucion[
        "margenes_documento"
    ]


    lineas.append(
        "MÁRGENES PROBABLES DE WORD"
    )


    lineas.append(
        "-" * 72
    )


    lineas.append(
        (
            "Izquierdo: "
            f"{margenes['izquierdo']:.2f} pt"
        )
    )


    lineas.append(
        (
            "Derecho: "
            f"{margenes['derecho']:.2f} pt"
        )
    )


    lineas.append(
        (
            "Superior: "
            f"{margenes['superior']:.2f} pt"
        )
    )


    lineas.append(
        (
            "Inferior: "
            f"{margenes['inferior']:.2f} pt"
        )
    )


    lineas.append(
        ""
    )


    fondo = distribucion[
        "fondo_documento"
    ]


    lineas.append(
        "FONDO"
    )


    lineas.append(
        "-" * 72
    )


    lineas.append(
        (
            "Detectado: "
            f"{fondo.get('detectado')}"
        )
    )


    lineas.append(
        (
            "Tipo: "
            f"{fondo.get('tipo')}"
        )
    )


    lineas.append(
        (
            "Repetido: "
            f"{fondo.get('repetido')}"
        )
    )


    lineas.append(
        (
            "Páginas: "
            f"{fondo.get('cantidad_paginas', 0)}"
        )
    )


    lineas.append(
        (
            "Mosaico: "
            f"{fondo.get('bbox_mosaico')}"
        )
    )


    lineas.append(
        (
            "Hashes de imagen: "
            f"{fondo.get('hashes_imagen')}"
        )
    )


    lineas.append(
        ""
    )


    lineas.append(
        "=" * 72
    )


    lineas.append(
        ""
    )


    for pagina in distribucion[
        "paginas"
    ]:

        lineas.append(
            (
                f"PÁGINA "
                f"{pagina['numero']}"
            )
        )


        lineas.append(
            "-" * 72
        )


        lineas.append(
            (
                "Tipo: "
                f"{pagina['tipo']}"
            )
        )


        lineas.append(
            (
                "Elementos: "
                f"{len(pagina['elementos'])}"
            )
        )


        encabezado = pagina.get(
            "encabezado"
        )


        if encabezado:

            lineas.append(
                (
                    "Encabezado: "
                    f"{encabezado.get('texto')} | "
                    "alineación="
                    f"{encabezado.get('alineacion')}"
                )
            )


        pie = pagina.get(
            "pie"
        )


        if pie:

            lineas.append(
                "Pie:"
            )


            for zona in pie.get(
                "zonas",
                []
            ):

                lineas.append(
                    (
                        "  - "
                        f"{zona.get('posicion_horizontal')}: "
                        f"{zona.get('texto')} | "
                        "alineación="
                        f"{zona.get('alineacion')}"
                    )
                )


        recursos = pagina.get(
            "recursos_graficos",
            {}
        )


        imagenes = recursos.get(
            "imagenes",
            []
        )


        extraidas = sum(
            1
            for imagen
            in imagenes
            if imagen.get(
                "extraida"
            )
        )


        lineas.append(
            (
                "Imágenes detectadas/extraídas: "
                f"{len(imagenes)} / "
                f"{extraidas}"
            )
        )


        if pagina[
            "tipo"
        ] == "portada":

            for imagen in imagenes:

                lineas.append(
                    (
                        "  - "
                        f"{imagen.get('nombre')}: "
                        f"{imagen.get('rol_estimado')} | "
                        f"{imagen.get('archivo_extraido')}"
                    )
                )


        lineas.append(
            ""
        )


        for indice, elemento in enumerate(
            pagina[
                "elementos"
            ],
            start=1
        ):

            tipo = elemento.get(
                "tipo"
            )


            lineas.append(
                (
                    f"{indice:02d}. "
                    f"{tipo}"
                )
            )


            if tipo == "tabla":

                datos = elemento.get(
                    "datos_tabla",
                    {}
                )


                lineas.append(
                    (
                        "    Tabla reconstruida: "
                        f"{datos.get('filas')} filas × "
                        f"{datos.get('columnas')} columnas"
                    )
                )


                lineas.append(
                    (
                        "    Borde estimado: "
                        f"{datos.get('grosor_borde_estimado')} pt"
                    )
                )


            else:

                texto = elemento.get(
                    "texto",
                    ""
                )


                if len(
                    texto
                ) > 140:

                    texto = (
                        texto[
                            :137
                        ]
                        + "..."
                    )


                lineas.append(
                    (
                        "    Texto: "
                        f"{texto}"
                    )
                )


                sangrias = elemento.get(
                    "sangrias",
                    {}
                )


                lineas.append(
                    (
                        "    Sangría izq.: "
                        f"{sangrias.get('izquierda', 0):.2f} pt | "
                        "Primera línea: "
                        f"{sangrias.get('primera_linea', 0):.2f} pt | "
                        "Francesa: "
                        f"{sangrias.get('francesa', 0):.2f} pt"
                    )
                )


                lineas.append(
                    (
                        "    Alineación: "
                        f"{elemento.get('alineacion')}"
                    )
                )


            lineas.append(
                (
                    "    Espacio antes/después: "
                    f"{elemento.get('espacio_antes', 0):.2f} / "
                    f"{elemento.get('espacio_despues', 0):.2f} pt"
                )
            )


        lineas.append(
            ""
        )


        lineas.append(
            "=" * 72
        )


        lineas.append(
            ""
        )


    return "\n".join(
        lineas
    )


# ================================================================
# EJECUCIÓN PRINCIPAL
# ================================================================
def main():

    # ============================================================
    # CARGAR ANÁLISIS
    # ============================================================

    analisis = cargar_json(
        RUTA_ANALISIS
    )


    datos_patrones = {}


    if RUTA_PATRONES.is_file():

        datos_patrones = cargar_json(
            RUTA_PATRONES
        )


    paginas_originales = analisis.get(
        "paginas",
        []
    )


    margenes = inferir_margenes_documento(
        analisis
    )


    fondo = detectar_fondo_semantico(
        datos_patrones,
        len(
            paginas_originales
        )
    )


    # ============================================================
    # EXTRAER RECURSOS GRÁFICOS
    # ============================================================

    ruta_origen = Path(
        analisis.get(
            "ruta_origen",
            ""
        )
    )


    recursos_extraidos = {}


    print()


    print(
        "Preparando recursos gráficos..."
    )


    if ruta_origen.is_file():

        try:

            recursos_extraidos = (
                extraer_imagenes_documento(
                    ruta_origen,
                    paginas_originales,
                    CARPETA_RECURSOS_PAGINAS,
                    limpiar=True
                )
            )


            print(
                (
                    "Recursos gráficos "
                    "extraídos correctamente."
                )
            )


        except Exception as error:

            print(
                (
                    "No fue posible extraer "
                    "todos los recursos gráficos: "
                    f"{error}"
                )
            )


    else:

        print(
            (
                "No se encontró el PDF original "
                "para extraer recursos gráficos."
            )
        )


    # ============================================================
    # ANALIZAR PÁGINAS
    # ============================================================

    paginas = []


    print()


    print(
        (
            "Analizando distribución "
            "integrada del documento..."
        )
    )


    print()


    for pagina in paginas_originales:

        numero = pagina.get(
            "numero"
        )


        print(
            (
                f"Página "
                f"{numero}..."
            )
        )


        resultado = analizar_pagina(
            pagina,
            margenes,
            recursos_extraidos
        )


        paginas.append(
            resultado
        )


    # ============================================================
    # DOCUMENTO FINAL DE DISTRIBUCIÓN
    # ============================================================

    distribucion = {
        "ruta_origen": analisis.get(
            "ruta_origen"
        ),

        "cantidad_paginas": len(
            paginas
        ),

        "margenes_documento": (
            margenes
        ),

        "fondo_documento": (
            fondo
        ),

        "encabezados_probables": (
            analisis.get(
                "encabezados_probables",
                []
            )
        ),

        "pies_probables": (
            analisis.get(
                "pies_probables",
                []
            )
        ),

        "carpeta_recursos_extraidos": str(
            CARPETA_RECURSOS_PAGINAS
        ),

        "paginas": paginas
    }


    # ============================================================
    # GUARDAR
    # ============================================================

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        RUTA_DISTRIBUCION,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            distribucion,
            archivo,
            ensure_ascii=False,
            indent=2
        )


    RUTA_RESUMEN.write_text(
        crear_resumen(
            distribucion
        ),
        encoding="utf-8"
    )


    # ============================================================
    # FINAL
    # ============================================================

    print()


    print(
        "Análisis integrado terminado."
    )


    print(
        (
            "JSON: "
            f"{RUTA_DISTRIBUCION}"
        )
    )


    print(
        (
            "Resumen: "
            f"{RUTA_RESUMEN}"
        )
    )


    print(
        (
            "Recursos: "
            f"{CARPETA_RECURSOS_PAGINAS}"
        )
    )


    print()


if __name__ == "__main__":

    main()