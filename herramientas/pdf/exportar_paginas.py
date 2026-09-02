import io
import os
import tempfile

from PIL import Image

from pypdf import PdfReader

from conversiones.previsualizacion import (
    renderizar_pagina_pdf
)


# ================================================================
# VALIDACIONES
# ================================================================
def _validar_pdf(
    ruta_pdf
):

    ruta_pdf = os.path.abspath(
        os.path.normpath(
            ruta_pdf
        )
    )


    if not os.path.isfile(
        ruta_pdf
    ):

        raise FileNotFoundError(
            f"No se encontró el archivo PDF:\n{ruta_pdf}"
        )


    if os.path.splitext(
        ruta_pdf
    )[1].lower() != ".pdf":

        raise ValueError(
            "El archivo seleccionado no es un PDF."
        )


    return ruta_pdf


# ================================================================
# ABRIR LECTOR PDF
# ================================================================
def _abrir_lector_pdf(
    ruta_pdf
):

    lector = PdfReader(
        ruta_pdf
    )


    if lector.is_encrypted:

        resultado = lector.decrypt(
            ""
        )


        if resultado == 0:

            raise ValueError(
                "El PDF está protegido con contraseña."
            )


    return lector


# ================================================================
# NORMALIZAR PÁGINAS
# ================================================================
def _normalizar_paginas(
    paginas,
    cantidad_paginas
):

    if not paginas:

        raise ValueError(
            "No se seleccionó ninguna página."
        )


    paginas_normalizadas = []


    for pagina in paginas:

        try:

            numero_pagina = int(
                pagina
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                f"La página '{pagina}' no es válida."
            )


        if (
            numero_pagina < 1
            or numero_pagina > cantidad_paginas
        ):

            raise ValueError(
                (
                    f"La página {numero_pagina} está fuera "
                    f"del rango 1-{cantidad_paginas}."
                )
            )


        if numero_pagina not in paginas_normalizadas:

            paginas_normalizadas.append(
                numero_pagina
            )


    paginas_normalizadas.sort()


    return paginas_normalizadas


# ================================================================
# COMPROBAR CANCELACIÓN
# ================================================================
def _comprobar_cancelacion(
    comprobar_cancelacion
):

    if (
        comprobar_cancelacion is not None
        and comprobar_cancelacion()
    ):

        return True


    return False


# ================================================================
# INFORMAR PROGRESO
# ================================================================
def _informar_progreso(
    progreso,
    actual,
    total
):

    if progreso is not None:

        progreso(
            actual,
            total
        )


# ================================================================
# RUTA DISPONIBLE
# ================================================================
def _obtener_ruta_disponible(
    ruta
):

    if not os.path.exists(
        ruta
    ):

        return ruta


    carpeta = os.path.dirname(
        ruta
    )

    nombre = os.path.basename(
        ruta
    )

    base, extension = os.path.splitext(
        nombre
    )


    contador = 2


    while True:

        alternativa = os.path.join(
            carpeta,
            f"{base}_{contador}{extension}"
        )


        if not os.path.exists(
            alternativa
        ):

            return alternativa


        contador += 1


# ================================================================
# CREAR ARCHIVO TEMPORAL
# ================================================================
def _crear_ruta_temporal(
    carpeta,
    sufijo
):

    descriptor, ruta_temporal = tempfile.mkstemp(
        prefix=".extraer_paginas_",
        suffix=sufijo,
        dir=carpeta
    )

    os.close(
        descriptor
    )


    return ruta_temporal


# ================================================================
# PREPARAR IMAGEN PARA JPEG
# ================================================================
def _convertir_a_rgb(
    imagen
):

    if imagen.mode == "RGB":

        return imagen.copy()


    if imagen.mode in (
        "RGBA",
        "LA"
    ):

        fondo = Image.new(
            "RGB",
            imagen.size,
            "white"
        )


        if imagen.mode != "RGBA":

            imagen = imagen.convert(
                "RGBA"
            )


        fondo.paste(
            imagen,
            mask=imagen.getchannel(
                "A"
            )
        )


        return fondo


    return imagen.convert(
        "RGB"
    )


# ================================================================
# EXPORTAR PÁGINAS COMO IMÁGENES
# ================================================================
def exportar_paginas_como_imagenes(
    ruta_pdf,
    paginas,
    carpeta_salida,
    formato="JPG",
    calidad=90,
    progreso=None,
    comprobar_cancelacion=None
):

    ruta_pdf = _validar_pdf(
        ruta_pdf
    )


    carpeta_salida = os.path.abspath(
        os.path.normpath(
            carpeta_salida
        )
    )

    os.makedirs(
        carpeta_salida,
        exist_ok=True
    )


    lector = _abrir_lector_pdf(
        ruta_pdf
    )

    cantidad_paginas = len(
        lector.pages
    )


    paginas = _normalizar_paginas(
        paginas,
        cantidad_paginas
    )


    formato = str(
        formato
    ).strip().upper()


    formatos_validos = {
        "JPG",
        "JPEG",
        "PNG",
        "WEBP"
    }


    if formato not in formatos_validos:

        raise ValueError(
            (
                "El formato de imagen debe ser "
                "JPG, PNG o WebP."
            )
        )


    calidad = int(
        calidad
    )

    calidad = max(
        1,
        min(
            100,
            calidad
        )
    )


    nombre_base = os.path.splitext(
        os.path.basename(
            ruta_pdf
        )
    )[0]


    total = len(
        paginas
    )

    resultados = []


    for posicion, numero_pagina in enumerate(
        paginas,
        start=1
    ):

        if _comprobar_cancelacion(
            comprobar_cancelacion
        ):

            break


        datos_png = renderizar_pagina_pdf(
            ruta_pdf,
            numero_pagina - 1
        )


        with Image.open(
            io.BytesIO(
                datos_png
            )
        ) as imagen:

            imagen.load()


            if formato in (
                "JPG",
                "JPEG"
            ):

                extension = ".jpg"

                formato_pillow = "JPEG"

                imagen_guardar = _convertir_a_rgb(
                    imagen
                )


            elif formato == "PNG":

                extension = ".png"

                formato_pillow = "PNG"

                imagen_guardar = imagen.copy()


            else:

                extension = ".webp"

                formato_pillow = "WEBP"

                imagen_guardar = imagen.copy()


            nombre_salida = (
                f"{nombre_base}_pagina_"
                f"{numero_pagina:03d}"
                f"{extension}"
            )


            ruta_salida = _obtener_ruta_disponible(
                os.path.join(
                    carpeta_salida,
                    nombre_salida
                )
            )


            ruta_temporal = _crear_ruta_temporal(
                carpeta_salida,
                extension
            )


            try:

                if formato_pillow == "JPEG":

                    imagen_guardar.save(
                        ruta_temporal,
                        formato_pillow,
                        quality=calidad,
                        optimize=True
                    )


                elif formato_pillow == "WEBP":

                    imagen_guardar.save(
                        ruta_temporal,
                        formato_pillow,
                        quality=calidad,
                        method=6
                    )


                else:

                    imagen_guardar.save(
                        ruta_temporal,
                        formato_pillow,
                        optimize=True
                    )


                os.replace(
                    ruta_temporal,
                    ruta_salida
                )


            finally:

                imagen_guardar.close()


                if os.path.exists(
                    ruta_temporal
                ):

                    try:

                        os.remove(
                            ruta_temporal
                        )

                    except OSError:

                        pass


        resultados.append(
            ruta_salida
        )


        _informar_progreso(
            progreso,
            posicion,
            total
        )


    return resultados


# ================================================================
# EXTRAER TEXTO DE PÁGINA
# ================================================================
def _extraer_texto_pagina(
    pagina
):

    texto = pagina.extract_text()


    if texto is None:

        return ""


    return texto.strip()


# ================================================================
# EXPORTAR PÁGINAS COMO TEXTO
# ================================================================
def exportar_paginas_como_texto(
    ruta_pdf,
    paginas,
    carpeta_salida,
    un_solo_archivo=True,
    progreso=None,
    comprobar_cancelacion=None
):

    ruta_pdf = _validar_pdf(
        ruta_pdf
    )


    carpeta_salida = os.path.abspath(
        os.path.normpath(
            carpeta_salida
        )
    )

    os.makedirs(
        carpeta_salida,
        exist_ok=True
    )


    lector = _abrir_lector_pdf(
        ruta_pdf
    )

    cantidad_paginas = len(
        lector.pages
    )


    paginas = _normalizar_paginas(
        paginas,
        cantidad_paginas
    )


    nombre_base = os.path.splitext(
        os.path.basename(
            ruta_pdf
        )
    )[0]


    total = len(
        paginas
    )

    resultados = []


    # ============================================================
    # UN SOLO ARCHIVO TXT
    # ============================================================

    if un_solo_archivo:

        partes = []


        for posicion, numero_pagina in enumerate(
            paginas,
            start=1
        ):

            if _comprobar_cancelacion(
                comprobar_cancelacion
            ):

                return resultados


            texto = _extraer_texto_pagina(
                lector.pages[
                    numero_pagina - 1
                ]
            )


            partes.append(
                (
                    f"===== Página {numero_pagina} =====\n\n"
                    f"{texto}"
                )
            )


            _informar_progreso(
                progreso,
                posicion,
                total
            )


        nombre_salida = (
            f"{nombre_base}_paginas_extraidas.txt"
        )


        ruta_salida = _obtener_ruta_disponible(
            os.path.join(
                carpeta_salida,
                nombre_salida
            )
        )


        ruta_temporal = _crear_ruta_temporal(
            carpeta_salida,
            ".txt"
        )


        try:

            with open(
                ruta_temporal,
                "w",
                encoding="utf-8",
                newline="\n"
            ) as archivo:

                archivo.write(
                    "\n\n\n".join(
                        partes
                    )
                )


            os.replace(
                ruta_temporal,
                ruta_salida
            )


        finally:

            if os.path.exists(
                ruta_temporal
            ):

                try:

                    os.remove(
                        ruta_temporal
                    )

                except OSError:

                    pass


        resultados.append(
            ruta_salida
        )


        return resultados


    # ============================================================
    # UN TXT POR PÁGINA
    # ============================================================

    for posicion, numero_pagina in enumerate(
        paginas,
        start=1
    ):

        if _comprobar_cancelacion(
            comprobar_cancelacion
        ):

            break


        texto = _extraer_texto_pagina(
            lector.pages[
                numero_pagina - 1
            ]
        )


        nombre_salida = (
            f"{nombre_base}_pagina_"
            f"{numero_pagina:03d}.txt"
        )


        ruta_salida = _obtener_ruta_disponible(
            os.path.join(
                carpeta_salida,
                nombre_salida
            )
        )


        ruta_temporal = _crear_ruta_temporal(
            carpeta_salida,
            ".txt"
        )


        try:

            with open(
                ruta_temporal,
                "w",
                encoding="utf-8",
                newline="\n"
            ) as archivo:

                archivo.write(
                    texto
                )


            os.replace(
                ruta_temporal,
                ruta_salida
            )


        finally:

            if os.path.exists(
                ruta_temporal
            ):

                try:

                    os.remove(
                        ruta_temporal
                    )

                except OSError:

                    pass


        resultados.append(
            ruta_salida
        )


        _informar_progreso(
            progreso,
            posicion,
            total
        )


    return resultados