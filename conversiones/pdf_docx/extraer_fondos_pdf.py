import hashlib
import json
from pathlib import Path

import pikepdf
from pikepdf import PdfImage


# ================================================================
# NORMALIZAR VALOR PDF
# ================================================================
def normalizar_valor_pdf(valor):
    if valor is None:
        return None

    if isinstance(
        valor,
        (bool, int, float, str)
    ):
        return valor

    if isinstance(
        valor,
        (list, tuple)
    ):
        return [
            normalizar_valor_pdf(
                elemento
            )
            for elemento in valor
        ]

    try:
        return [
            normalizar_valor_pdf(
                elemento
            )
            for elemento in valor
        ]

    except TypeError:
        return str(
            valor
        )


# ================================================================
# OBTENER OBJGEN
# ================================================================
def obtener_objgen(
    objeto
):
    try:
        objgen = objeto.objgen

    except Exception:
        return None

    if not objgen:
        return None

    try:
        return [
            int(
                objgen[0]
            ),
            int(
                objgen[1]
            )
        ]

    except Exception:
        return None


# ================================================================
# OBTENER CLAVE
# ================================================================
def obtener_clave(
    objeto,
    clave,
    predeterminado=None
):
    if objeto is None:
        return predeterminado

    try:
        return objeto.get(
            clave,
            predeterminado
        )

    except Exception:
        return predeterminado


# ================================================================
# LEER STREAM DECODIFICADO
# ================================================================
def leer_stream_decodificado(
    objeto
):
    try:
        return objeto.read_bytes()

    except Exception:
        return None


# ================================================================
# LEER STREAM RAW
# ================================================================
def leer_stream_raw(
    objeto
):
    try:
        return objeto.read_raw_bytes()

    except Exception:
        return None


# ================================================================
# CALCULAR HASH
# ================================================================
def calcular_hash(
    datos
):
    if datos is None:
        return None

    return hashlib.sha256(
        datos
    ).hexdigest()


# ================================================================
# CREAR HASH DE ESTRUCTURA
# ================================================================
def crear_hash_estructura(
    datos
):
    texto = json.dumps(
        datos,
        ensure_ascii=False,
        sort_keys=True,
        separators=(
            ",",
            ":"
        )
    )

    return calcular_hash(
        texto.encode(
            "utf-8"
        )
    )


# ================================================================
# EXTRAER IMAGEN XOBJECT
# ================================================================
def extraer_imagen_xobject(
    objeto,
    nombre,
    carpeta_salida
):
    carpeta_salida = Path(
        carpeta_salida
    )

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True
    )

    nombre_seguro = (
        str(
            nombre
        )
        .lstrip(
            "/"
        )
        .replace(
            "\\",
            "_"
        )
        .replace(
            "/",
            "_"
        )
    )

    prefijo = (
        carpeta_salida
        / nombre_seguro
    )

    try:
        imagen = PdfImage(
            objeto
        )

        ruta = imagen.extract_to(
            fileprefix=str(
                prefijo
            )
        )

        if ruta:
            return str(
                Path(
                    ruta
                ).resolve()
            )

    except Exception:
        return None

    return None


# ================================================================
# ANALIZAR XOBJECTS
# ================================================================
def analizar_xobjects(
    recursos,
    carpeta_salida,
    visitados=None
):
    if visitados is None:
        visitados = set()

    xobjects = obtener_clave(
        recursos,
        "/XObject"
    )

    if xobjects is None:
        return []

    try:
        elementos = list(
            xobjects.items()
        )

    except Exception:
        return []

    resultado = []

    for nombre_pdf, objeto in elementos:
        nombre = str(
            nombre_pdf
        )

        objgen = obtener_objgen(
            objeto
        )

        clave_visitado = (
            tuple(
                objgen
            )
            if objgen
            else id(
                objeto
            )
        )

        if clave_visitado in visitados:
            continue

        visitados.add(
            clave_visitado
        )

        subtipo = str(
            obtener_clave(
                objeto,
                "/Subtype",
                ""
            )
        )

        raw = leer_stream_raw(
            objeto
        )

        decodificado = (
            leer_stream_decodificado(
                objeto
            )
        )

        datos = {
            "nombre": nombre,
            "objgen": objgen,
            "subtipo": subtipo,
            "ancho": normalizar_valor_pdf(
                obtener_clave(
                    objeto,
                    "/Width"
                )
            ),
            "alto": normalizar_valor_pdf(
                obtener_clave(
                    objeto,
                    "/Height"
                )
            ),
            "bits": normalizar_valor_pdf(
                obtener_clave(
                    objeto,
                    "/BitsPerComponent"
                )
            ),
            "espacio_color": normalizar_valor_pdf(
                obtener_clave(
                    objeto,
                    "/ColorSpace"
                )
            ),
            "filtro": normalizar_valor_pdf(
                obtener_clave(
                    objeto,
                    "/Filter"
                )
            ),
            "hash_stream_decodificado": (
                calcular_hash(
                    decodificado
                )
            ),
            "hash_stream_raw": calcular_hash(
                raw
            ),
            "archivo_extraido": None,
            "xobjects_hijos": []
        }

        if subtipo == "/Image":
            datos[
                "archivo_extraido"
            ] = extraer_imagen_xobject(
                objeto,
                nombre,
                carpeta_salida
            )

        recursos_hijos = obtener_clave(
            objeto,
            "/Resources"
        )

        if recursos_hijos is not None:
            datos[
                "xobjects_hijos"
            ] = analizar_xobjects(
                recursos_hijos,
                carpeta_salida,
                visitados
            )

        resultado.append(
            datos
        )

    return resultado


# ================================================================
# RECOLECTAR IDENTIDAD VISUAL DE XOBJECTS
# ================================================================
def recolectar_identidad_visual(
    xobjects
):
    identidades = []

    for xobject in xobjects:
        if (
            xobject.get(
                "subtipo"
            )
            == "/Image"
        ):
            identidades.append(
                {
                    "ancho": xobject.get(
                        "ancho"
                    ),
                    "alto": xobject.get(
                        "alto"
                    ),
                    "bits": xobject.get(
                        "bits"
                    ),
                    "espacio_color": xobject.get(
                        "espacio_color"
                    ),
                    "hash_stream_raw": (
                        xobject.get(
                            "hash_stream_raw"
                        )
                    ),
                    "hash_stream_decodificado": (
                        xobject.get(
                            "hash_stream_decodificado"
                        )
                    )
                }
            )

        identidades.extend(
            recolectar_identidad_visual(
                xobject.get(
                    "xobjects_hijos",
                    []
                )
            )
        )

    return identidades


# ================================================================
# EXTRAER PATRONES DE FONDO
# ================================================================
def extraer_patrones_fondo(
    ruta_pdf,
    carpeta_salida,
    comprobar_cancelacion=None,
    progreso=None
):
    ruta_pdf = Path(
        ruta_pdf
    ).resolve()

    carpeta_salida = Path(
        carpeta_salida
    ).resolve()

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True
    )

    patrones = []

    with pikepdf.Pdf.open(
        str(
            ruta_pdf
        )
    ) as pdf:
        total_paginas = len(
            pdf.pages
        )

        for indice, pagina in enumerate(
            pdf.pages,
            start=1
        ):
            if (
                comprobar_cancelacion
                and comprobar_cancelacion()
            ):
                raise RuntimeError(
                    "Conversión cancelada por el usuario."
                )

            recursos = obtener_clave(
                pagina.obj,
                "/Resources"
            )

            patrones_pagina = (
                obtener_clave(
                    recursos,
                    "/Pattern"
                )
                if recursos is not None
                else None
            )

            if patrones_pagina is not None:
                try:
                    elementos = list(
                        patrones_pagina.items()
                    )

                except Exception:
                    elementos = []

                for nombre_pdf, patron in elementos:
                    tipo_patron = (
                        normalizar_valor_pdf(
                            obtener_clave(
                                patron,
                                "/PatternType"
                            )
                        )
                    )

                    if tipo_patron != 1:
                        continue

                    nombre = (
                        str(
                            nombre_pdf
                        )
                        .lstrip(
                            "/"
                        )
                    )

                    geometria = {
                        "/PatternType": tipo_patron,
                        "/PaintType": (
                            normalizar_valor_pdf(
                                obtener_clave(
                                    patron,
                                    "/PaintType"
                                )
                            )
                        ),
                        "/TilingType": (
                            normalizar_valor_pdf(
                                obtener_clave(
                                    patron,
                                    "/TilingType"
                                )
                            )
                        ),
                        "/BBox": (
                            normalizar_valor_pdf(
                                obtener_clave(
                                    patron,
                                    "/BBox"
                                )
                            )
                        ),
                        "/XStep": (
                            normalizar_valor_pdf(
                                obtener_clave(
                                    patron,
                                    "/XStep"
                                )
                            )
                        ),
                        "/YStep": (
                            normalizar_valor_pdf(
                                obtener_clave(
                                    patron,
                                    "/YStep"
                                )
                            )
                        ),
                        "/Matrix": (
                            normalizar_valor_pdf(
                                obtener_clave(
                                    patron,
                                    "/Matrix"
                                )
                            )
                        )
                    }

                    carpeta_pagina = (
                        carpeta_salida
                        / f"pagina_{indice:03d}"
                    )

                    recursos_patron = obtener_clave(
                        patron,
                        "/Resources"
                    )

                    xobjects = analizar_xobjects(
                        recursos_patron,
                        carpeta_pagina
                    )

                    raw = leer_stream_raw(
                        patron
                    )

                    decodificado = (
                        leer_stream_decodificado(
                            patron
                        )
                    )

                    identidad_visual = {
                        "geometria": {
                            "/PatternType": (
                                geometria[
                                    "/PatternType"
                                ]
                            ),
                            "/PaintType": (
                                geometria[
                                    "/PaintType"
                                ]
                            ),
                            "/TilingType": (
                                geometria[
                                    "/TilingType"
                                ]
                            ),
                            "/BBox": (
                                geometria[
                                    "/BBox"
                                ]
                            ),
                            "/XStep": (
                                geometria[
                                    "/XStep"
                                ]
                            ),
                            "/YStep": (
                                geometria[
                                    "/YStep"
                                ]
                            )
                        },
                        "xobjects": (
                            recolectar_identidad_visual(
                                xobjects
                            )
                        )
                    }

                    patrones.append(
                        {
                            "pagina": indice,
                            "recurso": nombre,
                            "objgen": obtener_objgen(
                                patron
                            ),
                            "geometria": geometria,
                            "hash_geometria": (
                                crear_hash_estructura(
                                    geometria
                                )
                            ),
                            "hash_stream_decodificado": (
                                calcular_hash(
                                    decodificado
                                )
                            ),
                            "hash_stream_raw": (
                                calcular_hash(
                                    raw
                                )
                            ),
                            "xobjects": xobjects,
                            "firma_visual": (
                                crear_hash_estructura(
                                    identidad_visual
                                )
                            )
                        }
                    )

            if progreso:
                progreso(
                    indice,
                    total_paginas
                )

    grupos = {}

    for patron in patrones:
        firma = patron.get(
            "firma_visual"
        )

        if not firma:
            continue

        grupo = grupos.setdefault(
            firma,
            {
                "firma_visual": firma,
                "cantidad_paginas": 0,
                "paginas": []
            }
        )

        grupo[
            "paginas"
        ].append(
            {
                "pagina": patron.get(
                    "pagina"
                ),
                "recurso": patron.get(
                    "recurso"
                )
            }
        )

        grupo[
            "cantidad_paginas"
        ] = len(
            grupo[
                "paginas"
            ]
        )

    grupos_ordenados = sorted(
        grupos.values(),
        key=lambda grupo: (
            -grupo.get(
                "cantidad_paginas",
                0
            ),
            grupo.get(
                "firma_visual",
                ""
            )
        )
    )

    resultado = {
        "pdf": str(
            ruta_pdf
        ),
        "patrones": patrones,
        "grupos_por_firma": (
            grupos_ordenados
        )
    }

    ruta_json = (
        carpeta_salida
        / "patrones_fondo.json"
    )

    with open(
        ruta_json,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            resultado,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    return resultado