import hashlib
import shutil

from pathlib import Path

import pikepdf

from pikepdf import PdfImage


# ================================================================
# UTILIDADES GENERALES
# ================================================================
def normalizar_nombre_recurso(
    nombre
):

    nombre = str(
        nombre
        or ""
    ).strip()


    if nombre.startswith(
        "/"
    ):

        return nombre[
            1:
        ]


    return nombre


# ================================================================
# CREAR NOMBRE SEGURO
# ================================================================
def crear_nombre_seguro(
    nombre
):

    nombre = normalizar_nombre_recurso(
        nombre
    )


    resultado = "".join(
        caracter
        if (
            caracter.isalnum()
            or caracter in (
                "-",
                "_"
            )
        )
        else "_"

        for caracter
        in nombre
    )


    return (
        resultado
        or "imagen"
    )


# ================================================================
# OBTENER VALOR DE OBJETO PDF
# ================================================================
def obtener_valor(
    objeto,
    clave,
    predeterminado=None
):

    if objeto is None:

        return predeterminado


    try:

        valor = objeto.get(
            clave
        )


        if valor is not None:

            return valor


    except Exception:

        pass


    try:

        valor = objeto.get(
            pikepdf.Name(
                clave
            )
        )


        if valor is not None:

            return valor


    except Exception:

        pass


    return predeterminado


# ================================================================
# OBTENER OBJGEN
# ================================================================
def obtener_objgen(
    objeto
):

    try:

        objgen = objeto.objgen


        return (
            int(
                objgen[
                    0
                ]
            ),
            int(
                objgen[
                    1
                ]
            )
        )


    except Exception:

        return None


# ================================================================
# CALCULAR SHA256 RAW
# ================================================================
def calcular_sha256_raw(
    objeto
):

    try:

        datos = (
            objeto.read_raw_bytes()
        )


    except Exception:

        return None


    return hashlib.sha256(
        datos
    ).hexdigest()


# ================================================================
# RECORRER XOBJECTS
# ================================================================
def recorrer_xobjects(
    recursos,
    encontrados=None,
    visitados=None
):

    if encontrados is None:

        encontrados = {}


    if visitados is None:

        visitados = set()


    if recursos is None:

        return encontrados


    xobjects = obtener_valor(
        recursos,
        "/XObject"
    )


    if xobjects is None:

        return encontrados


    try:

        elementos = list(
            xobjects.items()
        )


    except Exception:

        return encontrados


    for nombre, objeto in elementos:

        identificador = (
            obtener_objgen(
                objeto
            )
        )


        if (
            identificador is not None
            and identificador in visitados
        ):

            continue


        if identificador is not None:

            visitados.add(
                identificador
            )


        nombre_limpio = (
            normalizar_nombre_recurso(
                nombre
            )
        )


        subtipo = str(
            obtener_valor(
                objeto,
                "/Subtype",
                ""
            )
        )


        if subtipo == "/Image":

            encontrados.setdefault(
                nombre_limpio,
                []
            ).append(
                objeto
            )


        recursos_hijos = (
            obtener_valor(
                objeto,
                "/Resources"
            )
        )


        if recursos_hijos is not None:

            recorrer_xobjects(
                recursos_hijos,
                encontrados,
                visitados
            )


    return encontrados


# ================================================================
# BUSCAR IMAGEN POR DIMENSIONES
# ================================================================
def buscar_por_dimensiones(
    candidatos,
    ancho,
    alto
):

    if (
        ancho is None
        or alto is None
    ):

        return None


    try:

        ancho = int(
            ancho
        )


        alto = int(
            alto
        )


    except (
        TypeError,
        ValueError
    ):

        return None


    coincidencias = []


    for lista_objetos in (
        candidatos.values()
    ):

        for objeto in lista_objetos:

            try:

                ancho_objeto = int(
                    obtener_valor(
                        objeto,
                        "/Width",
                        0
                    )
                )


                alto_objeto = int(
                    obtener_valor(
                        objeto,
                        "/Height",
                        0
                    )
                )


            except (
                TypeError,
                ValueError
            ):

                continue


            if (
                ancho_objeto == ancho
                and alto_objeto == alto
            ):

                coincidencias.append(
                    objeto
                )


    if len(
        coincidencias
    ) == 1:

        return coincidencias[
            0
        ]


    return None


# ================================================================
# EXTRAER UNA IMAGEN
# ================================================================
def extraer_imagen(
    objeto,
    carpeta,
    nombre
):

    carpeta.mkdir(
        parents=True,
        exist_ok=True
    )


    prefijo = (
        carpeta
        / crear_nombre_seguro(
            nombre
        )
    )


    try:

        ruta = (
            PdfImage(
                objeto
            ).extract_to(
                fileprefix=str(
                    prefijo
                )
            )
        )


    except Exception:

        return None


    if not ruta:

        return None


    return str(
        Path(
            ruta
        ).resolve()
    )


# ================================================================
# EXTRAER IMÁGENES DEL DOCUMENTO
# ================================================================
def extraer_imagenes_documento(
    ruta_pdf,
    paginas_analisis,
    carpeta_salida,
    limpiar=True
):

    ruta_pdf = Path(
        ruta_pdf
    ).resolve()


    carpeta_salida = Path(
        carpeta_salida
    ).resolve()


    if not ruta_pdf.is_file():

        raise FileNotFoundError(
            (
                "No existe el PDF: "
                f"{ruta_pdf}"
            )
        )


    if (
        limpiar
        and carpeta_salida.exists()
    ):

        shutil.rmtree(
            carpeta_salida
        )


    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True
    )


    resultado = {}


    with pikepdf.Pdf.open(
        str(
            ruta_pdf
        )
    ) as pdf:

        for datos_pagina in (
            paginas_analisis
        ):

            numero = int(
                datos_pagina.get(
                    "numero",
                    0
                )
            )


            if (
                numero <= 0
                or numero > len(
                    pdf.pages
                )
            ):

                continue


            imagenes = datos_pagina.get(
                "imagenes",
                []
            )


            if not imagenes:

                resultado[
                    numero
                ] = {}


                continue


            pagina_pdf = pdf.pages[
                numero - 1
            ]


            recursos = obtener_valor(
                pagina_pdf.obj,
                "/Resources"
            )


            candidatos = recorrer_xobjects(
                recursos
            )


            carpeta_pagina = (
                carpeta_salida
                / (
                    f"pagina_"
                    f"{numero:03d}"
                )
            )


            pagina_resultado = {}


            for indice, imagen in enumerate(
                imagenes,
                start=1
            ):

                nombre = normalizar_nombre_recurso(
                    imagen.get(
                        "nombre"
                    )
                    or (
                        f"imagen_"
                        f"{indice}"
                    )
                )


                objetos = candidatos.get(
                    nombre,
                    []
                )


                if objetos:

                    objeto = objetos[
                        0
                    ]


                else:

                    objeto = None


                if objeto is None:

                    objeto = buscar_por_dimensiones(
                        candidatos,
                        imagen.get(
                            "ancho_pixeles"
                        ),
                        imagen.get(
                            "alto_pixeles"
                        )
                    )


                if objeto is None:

                    pagina_resultado[
                        nombre
                    ] = {
                        "extraida": False,
                        "archivo": None,
                        "sha256_raw": None,
                        "objgen": None
                    }


                    continue


                ruta_extraida = (
                    extraer_imagen(
                        objeto,
                        carpeta_pagina,
                        nombre
                    )
                )


                identificador = (
                    obtener_objgen(
                        objeto
                    )
                )


                pagina_resultado[
                    nombre
                ] = {
                    "extraida": (
                        ruta_extraida
                        is not None
                    ),

                    "archivo": (
                        ruta_extraida
                    ),

                    "sha256_raw": (
                        calcular_sha256_raw(
                            objeto
                        )
                    ),

                    "objgen": (
                        list(
                            identificador
                        )
                        if identificador
                        else None
                    )
                }


            resultado[
                numero
            ] = pagina_resultado


    return resultado