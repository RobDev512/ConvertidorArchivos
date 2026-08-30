import os
import shutil
import zipfile


# ----------------------------------- #
#       Datos del manifiesto          #
# ----------------------------------- #

RUTA_MANIFIESTO = "META-INF/MANIFEST.MF"

MANIFIESTO_MINIMO = (
    "Manifest-Version: 1.0\r\n"
    "Created-By: Convertidor de Archivos\r\n"
    "\r\n"
)


# ================================================================
# COMPROBAR ESTRUCTURA ZIP
# ================================================================
def comprobar_estructura_zip(ruta_archivo):

    return zipfile.is_zipfile(
        ruta_archivo
    )


# ================================================================
# NORMALIZAR NOMBRE INTERNO
# ================================================================
def normalizar_nombre_interno(nombre):

    # Normalizar barras y mayúsculas
    return (
        nombre
        .replace("\\", "/")
        .strip("/")
        .upper()
    )


# ================================================================
# COMPROBAR MANIFIESTO
# ================================================================
def comprobar_manifiesto(ruta_archivo):

    # Debe ser un ZIP válido
    if not comprobar_estructura_zip(
        ruta_archivo
    ):
        return False

    # Buscar manifiesto
    with zipfile.ZipFile(
        ruta_archivo,
        "r"
    ) as archivo_zip:

        for informacion in archivo_zip.infolist():

            nombre = normalizar_nombre_interno(
                informacion.filename
            )

            if nombre == RUTA_MANIFIESTO:
                return True

    return False


# ================================================================
# COMPROBAR CONVERSIÓN JAR IMPLEMENTADA
# ================================================================
def conversion_jar_implementada(
    ruta_origen,
    formato_destino
):

    formato_destino = formato_destino.upper()

    extension_origen = os.path.splitext(
        ruta_origen
    )[1].lower()

    # ZIP → JAR
    if (
        extension_origen == ".zip"
        and formato_destino == "JAR"
    ):
        return True

    # JAR → ZIP
    if (
        extension_origen == ".jar"
        and formato_destino == "ZIP"
    ):
        return True

    return False


# ================================================================
# COMPROBAR CONVERSIÓN JAR DISPONIBLE
# ================================================================
def comprobar_jar_disponible(
    ruta_origen,
    formato_destino
):

    # Comprobar implementación
    if not conversion_jar_implementada(
        ruta_origen,
        formato_destino
    ):

        return (
            False,
            "Esta conversión JAR todavía no está implementada."
        )

    # Tanto JAR como ZIP deben ser contenedores ZIP reales
    if not comprobar_estructura_zip(
        ruta_origen
    ):

        return (
            False,
            "El archivo seleccionado no contiene "
            "una estructura ZIP válida."
        )

    return True, None


# ================================================================
# CONVERTIR JAR A ZIP
# ================================================================
def convertir_jar_a_zip(
    ruta_origen,
    ruta_destino
):

    # Comprobar estructura
    if not comprobar_estructura_zip(
        ruta_origen
    ):

        raise RuntimeError(
            "El archivo JAR no contiene una estructura ZIP válida."
        )

    # JAR ya utiliza internamente el formato ZIP.
    # En esta dirección podemos conservar exactamente
    # el archivo sin extraerlo ni recomprimirlo.
    shutil.copy2(
        ruta_origen,
        ruta_destino
    )

    return ruta_destino


# ================================================================
# CONVERTIR ZIP A JAR
# ================================================================
def convertir_zip_a_jar(
    ruta_origen,
    ruta_destino
):

    # Comprobar estructura
    if not comprobar_estructura_zip(
        ruta_origen
    ):

        raise RuntimeError(
            "El archivo seleccionado no contiene "
            "una estructura ZIP válida."
        )


    # ----------------------------------- #
    #       Copiar contenedor original    #
    # ----------------------------------- #

    # Comenzamos conservando el ZIP original.
    # Si ya tiene manifiesto no necesitamos
    # modificar absolutamente nada.
    shutil.copy2(
        ruta_origen,
        ruta_destino
    )


    # ----------------------------------- #
    #      Comprobar manifiesto JAR       #
    # ----------------------------------- #

    if comprobar_manifiesto(
        ruta_destino
    ):

        return ruta_destino


    # ----------------------------------- #
    #       Añadir manifiesto mínimo      #
    # ----------------------------------- #

    with zipfile.ZipFile(
        ruta_destino,
        "a",
        compression=zipfile.ZIP_DEFLATED
    ) as archivo_jar:

        archivo_jar.writestr(
            RUTA_MANIFIESTO,
            MANIFIESTO_MINIMO
        )


    return ruta_destino


# ================================================================
# CONVERTIR JAR
# ================================================================
def convertir_jar(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    formato_destino = formato_destino.upper()

    extension_origen = os.path.splitext(
        ruta_origen
    )[1].lower()


    # ----------------------------------- #
    #             ZIP → JAR               #
    # ----------------------------------- #

    if (
        extension_origen == ".zip"
        and formato_destino == "JAR"
    ):

        return convertir_zip_a_jar(
            ruta_origen,
            ruta_destino
        )


    # ----------------------------------- #
    #             JAR → ZIP               #
    # ----------------------------------- #

    if (
        extension_origen == ".jar"
        and formato_destino == "ZIP"
    ):

        return convertir_jar_a_zip(
            ruta_origen,
            ruta_destino
        )


    raise NotImplementedError(
        "La conversión JAR solicitada todavía "
        "no está implementada."
    )