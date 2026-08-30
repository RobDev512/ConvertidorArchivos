import importlib.metadata
import os

from funciones.capacidades import obtener_carpeta_motores


# ----------------------------------- #
#       Configuración de Aspose       #
# ----------------------------------- #

MODO_DOCX_PREDETERMINADO = "FLOW"

NOMBRES_LICENCIA = [
    "Aspose.PDF.lic",
    "Aspose.Total.lic"
]


# ================================================================
# DETECTAR ASPOSE.PDF
# ================================================================
def detectar_aspose_pdf():

    try:

        importlib.metadata.version(
            "aspose-pdf"
        )

        return True

    except importlib.metadata.PackageNotFoundError:

        return False


# ================================================================
# OBTENER VERSIÓN DE ASPOSE.PDF
# ================================================================
def obtener_version_aspose_pdf():

    try:

        return importlib.metadata.version(
            "aspose-pdf"
        )

    except importlib.metadata.PackageNotFoundError:

        return None


# ================================================================
# DETECTAR LICENCIA DE ASPOSE.PDF
# ================================================================
def detectar_licencia_aspose_pdf():

    carpeta_aspose = os.path.join(
        obtener_carpeta_motores(),
        "aspose"
    )


    # ----------------------------------- #
    #       Buscar licencia gestionada    #
    # ----------------------------------- #

    for nombre in NOMBRES_LICENCIA:

        ruta = os.path.join(
            carpeta_aspose,
            nombre
        )

        if os.path.isfile(
            ruta
        ):

            return ruta


    # ----------------------------------- #
    #        Variable de entorno          #
    # ----------------------------------- #

    ruta_entorno = os.environ.get(
        "ASPOSE_PDF_LICENSE"
    )

    if (
        ruta_entorno
        and os.path.isfile(
            ruta_entorno
        )
    ):

        return os.path.abspath(
            ruta_entorno
        )


    return None


# ================================================================
# IMPORTAR ASPOSE.PDF
# ================================================================
def importar_aspose_pdf():

    if not detectar_aspose_pdf():

        raise RuntimeError(
            "Aspose.PDF no está instalado."
        )


    try:

        import aspose.pdf as ap

        return ap


    except Exception as error:

        raise RuntimeError(
            "Aspose.PDF está instalado, pero su módulo "
            "no pudo cargarse correctamente.\n\n"
            f"{error}"
        ) from error


# ================================================================
# APLICAR LICENCIA
# ================================================================
def aplicar_licencia_aspose_pdf(
    ap
):

    ruta_licencia = detectar_licencia_aspose_pdf()

    if not ruta_licencia:

        return False


    try:

        licencia = ap.License()

        licencia.set_license(
            ruta_licencia
        )

        return True


    except Exception as error:

        raise RuntimeError(
            "Se encontró una licencia de Aspose.PDF, "
            "pero no fue posible aplicarla.\n\n"
            f"{error}"
        ) from error


# ================================================================
# OBTENER MODO DE RECONOCIMIENTO
# ================================================================
def obtener_modo_reconocimiento(
    ap,
    modo
):

    modo = modo.upper()


    if modo == "FLOW":

        return (
            ap.DocSaveOptions
            .RecognitionMode
            .FLOW
        )


    if modo == "TEXTBOX":

        return (
            ap.DocSaveOptions
            .RecognitionMode
            .TEXTBOX
        )


    if modo == "ENHANCED_FLOW":

        return (
            ap.DocSaveOptions
            .RecognitionMode
            .ENHANCED_FLOW
        )


    raise ValueError(
        f"Modo de reconocimiento de Aspose "
        f"desconocido: {modo}"
    )


# ================================================================
# CREAR OPCIONES DE DOCX
# ================================================================
def crear_opciones_docx(
    ap,
    modo
):

    opciones = ap.DocSaveOptions()


    # ----------------------------------- #
    #             DOCX                    #
    # ----------------------------------- #

    opciones.format = (
        ap.DocSaveOptions
        .DocFormat
        .DOC_X
    )


    # ----------------------------------- #
    #       Reconocimiento de diseño      #
    # ----------------------------------- #

    opciones.mode = obtener_modo_reconocimiento(
        ap,
        modo
    )


    # ----------------------------------- #
    #          Reconocer viñetas          #
    # ----------------------------------- #

    try:

        opciones.recognize_bullets = True

    except Exception:

        pass


    return opciones


# ================================================================
# CONVERTIR PDF A DOCX CON ASPOSE
# ================================================================
def convertir_pdf_a_docx_aspose(
    ruta_origen,
    ruta_destino,
    modo=MODO_DOCX_PREDETERMINADO
):

    # ----------------------------------- #
    #         Cargar biblioteca           #
    # ----------------------------------- #

    ap = importar_aspose_pdf()


    # ----------------------------------- #
    #          Aplicar licencia           #
    # ----------------------------------- #

    aplicar_licencia_aspose_pdf(
        ap
    )


    # ----------------------------------- #
    #           Normalizar rutas          #
    # ----------------------------------- #

    ruta_origen = os.path.abspath(
        ruta_origen
    )

    ruta_destino = os.path.abspath(
        ruta_destino
    )


    # ----------------------------------- #
    #             Abrir PDF               #
    # ----------------------------------- #

    try:

        documento = ap.Document(
            ruta_origen
        )

    except Exception as error:

        raise RuntimeError(
            "Aspose.PDF no pudo abrir el documento.\n\n"
            f"{error}"
        ) from error


    # ----------------------------------- #
    #          Crear opciones             #
    # ----------------------------------- #

    opciones = crear_opciones_docx(
        ap,
        modo
    )


    # ----------------------------------- #
    #             Convertir               #
    # ----------------------------------- #

    try:

        documento.save(
            ruta_destino,
            opciones
        )

    except Exception as error:

        raise RuntimeError(
            "Aspose.PDF no pudo convertir el PDF a DOCX.\n\n"
            f"{error}"
        ) from error


    # ----------------------------------- #
    #       Comprobar resultado           #
    # ----------------------------------- #

    if not os.path.isfile(
        ruta_destino
    ):

        raise RuntimeError(
            "Aspose.PDF terminó sin generar "
            "el archivo DOCX esperado."
        )


    if os.path.getsize(
        ruta_destino
    ) <= 0:

        raise RuntimeError(
            "Aspose.PDF generó un archivo DOCX vacío."
        )


    return ruta_destino