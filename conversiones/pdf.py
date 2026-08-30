import html
import os
import tempfile
import zipfile

from funciones.archivos import obtener_nombre_sin_extension

from funciones.capacidades import (
    detectar_pdfium,
    detectar_microsoft_word,
    detectar_pandoc,
    detectar_aspose_pdf
)

from conversiones.microsoft_office import convertir_con_word

from conversiones.pandoc import (
    ESCRITORES_PANDOC,
    obtener_formatos_pandoc,
    convertir_con_pandoc
)

from conversiones.aspose_pdf import (
    convertir_pdf_a_docx_aspose
)


# ----------------------------------- #
#       Formatos de imagen PDF        #
# ----------------------------------- #

FORMATOS_IMAGEN_PDF = {
    "JPG",
    "PNG",
    "TIFF"
}


# ----------------------------------- #
#      Formatos editables PDF         #
# ----------------------------------- #

FORMATOS_DOCUMENTO_PDF = {
    "DOCX",
    "ODT",
    "RTF"
}


# ----------------------------------- #
#          Otras salidas PDF          #
# ----------------------------------- #

FORMATOS_TEXTO_PDF = {
    "TXT",
    "HTML"
}


# ----------------------------------- #
#         Resolución de imagen        #
# ----------------------------------- #

RESOLUCION_PDF_DPI = 200


# ================================================================
# INFORMAR PROGRESO
# ================================================================
def informar_progreso(
    callback_progreso,
    progreso,
    estado
):

    if callback_progreso:

        callback_progreso(
            progreso,
            estado
        )


# ================================================================
# ABRIR PDF
# ================================================================
def abrir_pdf(
    ruta_archivo
):

    if not detectar_pdfium():

        raise RuntimeError(
            "No se encontró el motor PDFium."
        )


    try:

        import pypdfium2 as pdfium


        return pdfium.PdfDocument(
            os.path.abspath(
                ruta_archivo
            )
        )


    except Exception as error:

        raise RuntimeError(
            "No fue posible abrir el archivo PDF.\n\n"
            "Puede estar dañado o protegido con contraseña.\n\n"
            f"{error}"
        ) from error


# ================================================================
# OBTENER CANTIDAD DE PÁGINAS
# ================================================================
def obtener_cantidad_paginas_pdf(
    ruta_archivo
):

    documento = abrir_pdf(
        ruta_archivo
    )


    try:

        cantidad_paginas = len(
            documento
        )


    finally:

        documento.close()


    if cantidad_paginas <= 0:

        raise RuntimeError(
            "El archivo PDF no contiene páginas."
        )


    return cantidad_paginas


# ================================================================
# COMPROBAR SI EL RESULTADO SERÁ ZIP
# ================================================================
def resultado_pdf_requiere_zip(
    ruta_archivo,
    formato_destino
):

    formato_destino = formato_destino.upper()


    if formato_destino not in FORMATOS_IMAGEN_PDF:

        return False


    return (
        obtener_cantidad_paginas_pdf(
            ruta_archivo
        )
        > 1
    )


# ================================================================
# PREPARAR IMAGEN DE PÁGINA
# ================================================================
def preparar_imagen_pagina(
    pagina
):

    escala = (
        RESOLUCION_PDF_DPI
        / 72
    )


    bitmap = pagina.render(
        scale=escala,
        rev_byteorder=True,
        prefer_bgrx=True
    )


    try:

        imagen = bitmap.to_pil()

        imagen = imagen.convert(
            "RGB"
        )


    finally:

        bitmap.close()


    return imagen


# ================================================================
# GUARDAR IMAGEN DE PÁGINA
# ================================================================
def guardar_imagen_pagina(
    imagen,
    ruta_destino,
    formato_destino
):

    formato_destino = formato_destino.upper()


    # ----------------------------------- #
    #               JPG                   #
    # ----------------------------------- #

    if formato_destino == "JPG":

        imagen.save(
            ruta_destino,
            format="JPEG",
            quality=92,
            optimize=True
        )

        return


    # ----------------------------------- #
    #               PNG                   #
    # ----------------------------------- #

    if formato_destino == "PNG":

        imagen.save(
            ruta_destino,
            format="PNG",
            optimize=True
        )

        return


    # ----------------------------------- #
    #               TIFF                  #
    # ----------------------------------- #

    if formato_destino == "TIFF":

        imagen.save(
            ruta_destino,
            format="TIFF",
            compression="tiff_lzw"
        )

        return


    raise ValueError(
        f"No existe una configuración de imagen "
        f"para {formato_destino}."
    )


# ================================================================
# OBTENER EXTENSIÓN DE IMAGEN
# ================================================================
def obtener_extension_imagen_pdf(
    formato_destino
):

    extensiones = {
        "JPG": ".jpg",
        "PNG": ".png",
        "TIFF": ".tiff"
    }


    extension = extensiones.get(
        formato_destino.upper()
    )


    if not extension:

        raise ValueError(
            f"No se conoce la extensión de "
            f"{formato_destino}."
        )


    return extension


# ================================================================
# CONVERTIR PDF A IMAGEN
# ================================================================
def convertir_pdf_a_imagen(
    ruta_origen,
    ruta_destino,
    formato_destino,
    callback_progreso=None
):

    formato_destino = formato_destino.upper()

    documento = abrir_pdf(
        ruta_origen
    )


    try:

        cantidad_paginas = len(
            documento
        )


        if cantidad_paginas <= 0:

            raise RuntimeError(
                "El PDF no contiene páginas."
            )


        # ========================================================
        # UNA SOLA PÁGINA
        # ========================================================

        if cantidad_paginas == 1:

            informar_progreso(
                callback_progreso,
                10,
                "Renderizando página 1 de 1..."
            )


            pagina = documento[
                0
            ]


            try:

                imagen = preparar_imagen_pagina(
                    pagina
                )


            finally:

                pagina.close()


            informar_progreso(
                callback_progreso,
                80,
                "Guardando imagen..."
            )


            guardar_imagen_pagina(
                imagen,
                ruta_destino,
                formato_destino
            )


            informar_progreso(
                callback_progreso,
                100,
                "Imagen generada correctamente."
            )


            return ruta_destino


        # ========================================================
        # VARIAS PÁGINAS
        # ========================================================

        with tempfile.TemporaryDirectory() as carpeta_temporal:

            nombre_base = obtener_nombre_sin_extension(
                ruta_origen
            )

            extension = obtener_extension_imagen_pdf(
                formato_destino
            )

            cantidad_digitos = max(
                3,
                len(
                    str(
                        cantidad_paginas
                    )
                )
            )

            archivos_generados = []


            # ----------------------------------- #
            #       Renderizar cada página        #
            # ----------------------------------- #

            for indice in range(
                cantidad_paginas
            ):

                numero_pagina = (
                    indice
                    + 1
                )


                progreso = round(
                    numero_pagina
                    / cantidad_paginas
                    * 90
                )


                informar_progreso(
                    callback_progreso,
                    progreso,
                    (
                        f"Renderizando página "
                        f"{numero_pagina} de "
                        f"{cantidad_paginas}..."
                    )
                )


                pagina = documento[
                    indice
                ]


                try:

                    imagen = preparar_imagen_pagina(
                        pagina
                    )


                finally:

                    pagina.close()


                nombre_imagen = (
                    f"{nombre_base}_pagina_"
                    f"{numero_pagina:0{cantidad_digitos}d}"
                    f"{extension}"
                )


                ruta_imagen = os.path.join(
                    carpeta_temporal,
                    nombre_imagen
                )


                guardar_imagen_pagina(
                    imagen,
                    ruta_imagen,
                    formato_destino
                )


                archivos_generados.append(
                    ruta_imagen
                )


            # ----------------------------------- #
            #          Crear archivo ZIP          #
            # ----------------------------------- #

            informar_progreso(
                callback_progreso,
                95,
                "Empaquetando imágenes..."
            )


            with zipfile.ZipFile(
                ruta_destino,
                "w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9
            ) as archivo_zip:


                for ruta_imagen in archivos_generados:

                    archivo_zip.write(
                        ruta_imagen,
                        os.path.basename(
                            ruta_imagen
                        )
                    )


        informar_progreso(
            callback_progreso,
            100,
            (
                f"{cantidad_paginas} páginas "
                f"convertidas correctamente."
            )
        )


        return ruta_destino


    finally:

        documento.close()


# ================================================================
# EXTRAER TEXTO DE PDF
# ================================================================
def extraer_texto_pdf(
    ruta_origen,
    callback_progreso=None,
    progreso_maximo=100
):

    documento = abrir_pdf(
        ruta_origen
    )

    paginas_texto = []


    try:

        cantidad_paginas = len(
            documento
        )


        if cantidad_paginas <= 0:

            raise RuntimeError(
                "El PDF no contiene páginas."
            )


        # ----------------------------------- #
        #         Extraer cada página         #
        # ----------------------------------- #

        for indice in range(
            cantidad_paginas
        ):

            numero_pagina = (
                indice
                + 1
            )


            progreso = round(
                numero_pagina
                / cantidad_paginas
                * progreso_maximo
            )


            informar_progreso(
                callback_progreso,
                progreso,
                (
                    f"Extrayendo texto de la página "
                    f"{numero_pagina} de "
                    f"{cantidad_paginas}..."
                )
            )


            pagina = documento[
                indice
            ]


            try:

                pagina_texto = pagina.get_textpage()


                try:

                    texto = (
                        pagina_texto
                        .get_text_bounded()
                    )


                finally:

                    pagina_texto.close()


            finally:

                pagina.close()


            paginas_texto.append(
                texto.strip()
            )


    finally:

        documento.close()


    # ----------------------------------- #
    #      Comprobar texto encontrado     #
    # ----------------------------------- #

    if not any(
        pagina.strip()
        for pagina in paginas_texto
    ):

        raise RuntimeError(
            "El PDF no contiene texto extraíble.\n\n"
            "Es posible que sea un documento escaneado. "
            "La lectura mediante OCR se añadirá posteriormente."
        )


    return paginas_texto


# ================================================================
# CONVERTIR PDF A TXT
# ================================================================
def convertir_pdf_a_txt(
    ruta_origen,
    ruta_destino,
    callback_progreso=None
):

    paginas = extraer_texto_pdf(
        ruta_origen,
        callback_progreso,
        95
    )


    contenido = []


    for indice, texto in enumerate(
        paginas,
        start=1
    ):

        contenido.append(
            f"========== PÁGINA {indice} ==========\n\n"
            f"{texto}"
        )


    informar_progreso(
        callback_progreso,
        98,
        "Guardando documento de texto..."
    )


    with open(
        ruta_destino,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "\n\n".join(
                contenido
            )
        )


    informar_progreso(
        callback_progreso,
        100,
        "Texto extraído correctamente."
    )


    return ruta_destino


# ================================================================
# CREAR HTML DESDE PDF
# ================================================================
def crear_html_paginas(
    ruta_origen,
    paginas
):

    nombre_documento = obtener_nombre_sin_extension(
        ruta_origen
    )

    secciones = []


    for indice, texto in enumerate(
        paginas,
        start=1
    ):

        texto_seguro = html.escape(
            texto
        )


        secciones.append(
            f"""
<section class="pagina">
    <h2>Página {indice}</h2>
    <pre>{texto_seguro}</pre>
</section>
""".strip()
        )


    contenido = "\n\n".join(
        secciones
    )


    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>{html.escape(nombre_documento)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
        }}

        .pagina {{
            margin-bottom: 40px;
            page-break-after: always;
        }}

        .pagina:last-child {{
            page-break-after: auto;
        }}

        pre {{
            font-family: Arial, sans-serif;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
    </style>
</head>
<body>
{contenido}
</body>
</html>
"""


# ================================================================
# CONVERTIR PDF A HTML
# ================================================================
def convertir_pdf_a_html(
    ruta_origen,
    ruta_destino,
    callback_progreso=None,
    progreso_maximo=95
):

    paginas = extraer_texto_pdf(
        ruta_origen,
        callback_progreso,
        progreso_maximo
    )


    contenido_html = crear_html_paginas(
        ruta_origen,
        paginas
    )


    informar_progreso(
        callback_progreso,
        min(
            progreso_maximo + 3,
            99
        ),
        "Guardando documento HTML..."
    )


    with open(
        ruta_destino,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            contenido_html
        )


    return ruta_destino


# ================================================================
# COMPROBAR RESPALDO PANDOC
# ================================================================
def comprobar_respaldo_pandoc(
    formato_destino
):

    if not detectar_pdfium():

        return False


    if not detectar_pandoc():

        return False


    escritor = ESCRITORES_PANDOC.get(
        formato_destino.upper()
    )


    if not escritor:

        return False


    formatos = obtener_formatos_pandoc()


    return escritor in formatos[
        "salida"
    ]


# ================================================================
# CONVERTIR MEDIANTE PDFIUM Y PANDOC
# ================================================================
def convertir_pdf_con_pandoc(
    ruta_origen,
    ruta_destino,
    formato_destino,
    callback_progreso=None
):

    with tempfile.TemporaryDirectory() as carpeta_temporal:

        ruta_html = os.path.join(
            carpeta_temporal,
            "documento_intermedio.html"
        )


        convertir_pdf_a_html(
            ruta_origen,
            ruta_html,
            callback_progreso,
            70
        )


        informar_progreso(
            callback_progreso,
            80,
            (
                f"Creando archivo "
                f"{formato_destino}..."
            )
        )


        convertir_con_pandoc(
            ruta_html,
            ruta_destino,
            formato_destino
        )


        informar_progreso(
            callback_progreso,
            100,
            "Documento convertido correctamente."
        )


    return ruta_destino


# ================================================================
# CONVERTIR PDF A DOCX
# ================================================================
def convertir_pdf_a_docx(
    ruta_origen,
    ruta_destino,
    callback_progreso=None
):

    errores = []


    # ============================================================
    # ASPOSE.PDF
    # ============================================================

    if detectar_aspose_pdf():

        informar_progreso(
            callback_progreso,
            10,
            "Analizando estructura del PDF..."
        )


        try:

            resultado = convertir_pdf_a_docx_aspose(
                ruta_origen,
                ruta_destino,
                modo="FLOW"
            )


            informar_progreso(
                callback_progreso,
                100,
                "Documento DOCX convertido correctamente."
            )


            return resultado


        except Exception as error:

            errores.append(
                f"Aspose.PDF: {error}"
            )


            # Si Aspose creó un archivo defectuoso,
            # eliminarlo antes del siguiente motor
            if os.path.exists(
                ruta_destino
            ):

                try:

                    os.remove(
                        ruta_destino
                    )

                except OSError:

                    pass


    # ============================================================
    # MICROSOFT WORD
    # ============================================================

    if detectar_microsoft_word():

        informar_progreso(
            callback_progreso,
            35,
            "Intentando conversión con Microsoft Word..."
        )


        try:

            resultado = convertir_con_word(
                ruta_origen,
                ruta_destino,
                "DOCX"
            )


            informar_progreso(
                callback_progreso,
                100,
                "Documento DOCX convertido correctamente."
            )


            return resultado


        except Exception as error:

            errores.append(
                f"Microsoft Word: {error}"
            )


            if os.path.exists(
                ruta_destino
            ):

                try:

                    os.remove(
                        ruta_destino
                    )

                except OSError:

                    pass


    # ============================================================
    # PANDOC COMO ÚLTIMO RESPALDO
    # ============================================================

    if comprobar_respaldo_pandoc(
        "DOCX"
    ):

        try:

            return convertir_pdf_con_pandoc(
                ruta_origen,
                ruta_destino,
                "DOCX",
                callback_progreso
            )


        except Exception as error:

            errores.append(
                f"Pandoc: {error}"
            )


    # ============================================================
    # NINGÚN MOTOR FUNCIONÓ
    # ============================================================

    if errores:

        raise RuntimeError(
            "Ningún motor pudo convertir correctamente "
            "el PDF a DOCX.\n\n"
            + "\n\n".join(
                errores
            )
        )


    raise RuntimeError(
        "No existe un motor disponible para convertir "
        "el PDF a DOCX."
    )


# ================================================================
# CONVERTIR PDF A ODT O RTF
# ================================================================
def convertir_pdf_a_documento_editable(
    ruta_origen,
    ruta_destino,
    formato_destino,
    callback_progreso=None
):

    formato_destino = formato_destino.upper()

    error_word = None


    # ----------------------------------- #
    #       Intentar Microsoft Word       #
    # ----------------------------------- #

    if detectar_microsoft_word():

        informar_progreso(
            callback_progreso,
            10,
            "Abriendo PDF con Microsoft Word..."
        )


        try:

            resultado = convertir_con_word(
                ruta_origen,
                ruta_destino,
                formato_destino
            )


            informar_progreso(
                callback_progreso,
                100,
                "Documento convertido correctamente."
            )


            return resultado


        except Exception as error:

            error_word = error


    # ----------------------------------- #
    #        Respaldo PDFium + Pandoc     #
    # ----------------------------------- #

    if comprobar_respaldo_pandoc(
        formato_destino
    ):

        return convertir_pdf_con_pandoc(
            ruta_origen,
            ruta_destino,
            formato_destino,
            callback_progreso
        )


    # ----------------------------------- #
    #          Ningún motor funcionó      #
    # ----------------------------------- #

    if error_word:

        raise RuntimeError(
            "Microsoft Word no pudo convertir el PDF y "
            "no existe un motor de respaldo disponible.\n\n"
            f"{error_word}"
        )


    raise RuntimeError(
        "No existe un motor disponible para convertir "
        f"el PDF a {formato_destino}."
    )


# ================================================================
# CONVERTIR PDF A DOCUMENTO
# ================================================================
def convertir_pdf_a_documento(
    ruta_origen,
    ruta_destino,
    formato_destino,
    callback_progreso=None
):

    formato_destino = formato_destino.upper()


    # ----------------------------------- #
    #          DOCX especializado         #
    # ----------------------------------- #

    if formato_destino == "DOCX":

        return convertir_pdf_a_docx(
            ruta_origen,
            ruta_destino,
            callback_progreso
        )


    # ----------------------------------- #
    #           ODT / RTF                 #
    # ----------------------------------- #

    return convertir_pdf_a_documento_editable(
        ruta_origen,
        ruta_destino,
        formato_destino,
        callback_progreso
    )


# ================================================================
# COMPROBAR CONVERSIÓN PDF IMPLEMENTADA
# ================================================================
def conversion_pdf_implementada(
    ruta_origen,
    formato_destino
):

    if not ruta_origen.lower().endswith(
        ".pdf"
    ):

        return False


    formato_destino = formato_destino.upper()


    return formato_destino in (
        FORMATOS_IMAGEN_PDF
        | FORMATOS_TEXTO_PDF
        | FORMATOS_DOCUMENTO_PDF
    )


# ================================================================
# COMPROBAR CONVERSIÓN PDF DISPONIBLE
# ================================================================
def comprobar_pdf_disponible(
    ruta_origen,
    formato_destino
):

    formato_destino = formato_destino.upper()


    # ----------------------------------- #
    #       Comprobar implementación      #
    # ----------------------------------- #

    if not conversion_pdf_implementada(
        ruta_origen,
        formato_destino
    ):

        return (
            False,
            f"La conversión de PDF a {formato_destino} "
            f"todavía no está implementada."
        )


    # ----------------------------------- #
    #           Salidas de imagen         #
    # ----------------------------------- #

    if formato_destino in FORMATOS_IMAGEN_PDF:

        if not detectar_pdfium():

            return (
                False,
                "La conversión de PDF a imágenes necesita "
                "pypdfium2, pero no se encontró instalado."
            )


        try:

            obtener_cantidad_paginas_pdf(
                ruta_origen
            )


        except Exception as error:

            return (
                False,
                str(error)
            )


        return True, None


    # ----------------------------------- #
    #          TXT y HTML                 #
    # ----------------------------------- #

    if formato_destino in FORMATOS_TEXTO_PDF:

        if not detectar_pdfium():

            return (
                False,
                "La extracción de texto del PDF necesita "
                "pypdfium2, pero no se encontró instalado."
            )


        return True, None


    # ----------------------------------- #
    #              DOCX                   #
    # ----------------------------------- #

    if formato_destino == "DOCX":

        if detectar_aspose_pdf():

            return True, None


        if detectar_microsoft_word():

            return True, None


        if comprobar_respaldo_pandoc(
            "DOCX"
        ):

            return True, None


        return (
            False,
            "Para convertir PDF a DOCX se necesita "
            "Aspose.PDF, Microsoft Word o el respaldo "
            "formado por pypdfium2 y Pandoc."
        )


    # ----------------------------------- #
    #            ODT / RTF                #
    # ----------------------------------- #

    if formato_destino in {
        "ODT",
        "RTF"
    }:

        if detectar_microsoft_word():

            return True, None


        if comprobar_respaldo_pandoc(
            formato_destino
        ):

            return True, None


        return (
            False,
            "Para convertir PDF a este formato se necesita "
            "Microsoft Word o el respaldo formado por "
            "pypdfium2 y Pandoc."
        )


    return (
        False,
        "Conversión PDF no disponible."
    )


# ================================================================
# CONVERTIR PDF
# ================================================================
def convertir_pdf(
    ruta_origen,
    ruta_destino,
    formato_destino,
    callback_progreso=None
):

    formato_destino = formato_destino.upper()


    # ----------------------------------- #
    #             Imágenes                #
    # ----------------------------------- #

    if formato_destino in FORMATOS_IMAGEN_PDF:

        return convertir_pdf_a_imagen(
            ruta_origen,
            ruta_destino,
            formato_destino,
            callback_progreso
        )


    # ----------------------------------- #
    #               TXT                   #
    # ----------------------------------- #

    if formato_destino == "TXT":

        return convertir_pdf_a_txt(
            ruta_origen,
            ruta_destino,
            callback_progreso
        )


    # ----------------------------------- #
    #              HTML                   #
    # ----------------------------------- #

    if formato_destino == "HTML":

        resultado = convertir_pdf_a_html(
            ruta_origen,
            ruta_destino,
            callback_progreso,
            97
        )


        informar_progreso(
            callback_progreso,
            100,
            "Documento HTML creado correctamente."
        )


        return resultado


    # ----------------------------------- #
    #       Documentos editables          #
    # ----------------------------------- #

    if formato_destino in FORMATOS_DOCUMENTO_PDF:

        return convertir_pdf_a_documento(
            ruta_origen,
            ruta_destino,
            formato_destino,
            callback_progreso
        )


    raise NotImplementedError(
        f"La conversión de PDF a {formato_destino} "
        f"todavía no está implementada."
    )