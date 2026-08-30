import os
import stat
import shutil
import zipfile
import tarfile
import gzip
import bz2
import lzma
import tempfile

from funciones.archivos import obtener_nombre_sin_extension

from funciones.formatos import (
    obtener_categoria_archivo,
    obtener_formato_archivo
)

from funciones.capacidades import (
    detectar_7zip,
    detectar_winrar
)

from conversiones.siete_zip import (
    comprobar_lectura_7zip,
    extraer_con_7zip,
    crear_con_7zip
)

from conversiones.winrar import (
    comprobar_lectura_winrar,
    extraer_con_winrar,
    crear_rar_con_winrar
)


# ----------------------------------- #
#      Formatos ZIP especiales        #
# ----------------------------------- #

FORMATOS_ZIP_ESPECIALES = {
    "MCPACK",
    "MCADDON",
    "MCWORLD",
    "MCTEMPLATE"
}


# ----------------------------------- #
#      Entradas internas Python       #
# ----------------------------------- #

FORMATOS_ENTRADA_INTERNOS = {
    "ZIP",
    "TAR",
    "TAR.GZ",
    "TAR.BZ2",
    "TAR.XZ",
    "GZ",
    "BZ2",
    "XZ",
    "LZMA"
}


# ----------------------------------- #
#       Salidas internas Python       #
# ----------------------------------- #

FORMATOS_SALIDA_INTERNOS = {
    "ZIP",
    "TAR",
    "TAR.GZ",
    "TAR.BZ2",
    "TAR.XZ",
    "GZ",
    "BZ2",
    "XZ",
    "LZMA"
}


# ----------------------------------- #
#         Salidas de 7-Zip            #
# ----------------------------------- #

FORMATOS_SALIDA_7ZIP = {
    "7Z",
    "WIM"
}


# ----------------------------------- #
#         Salidas de WinRAR           #
# ----------------------------------- #

FORMATOS_SALIDA_WINRAR = {
    "RAR"
}


# ----------------------------------- #
#       Todas las salidas actuales    #
# ----------------------------------- #

FORMATOS_SALIDA_IMPLEMENTADOS = (
    FORMATOS_SALIDA_INTERNOS
    | FORMATOS_SALIDA_7ZIP
    | FORMATOS_SALIDA_WINRAR
)


# ================================================================
# COMPROBAR RUTA SEGURA
# ================================================================
def obtener_ruta_extraccion_segura(
    carpeta_destino,
    nombre_archivo
):

    # Normalizar carpeta base
    carpeta_base = os.path.abspath(
        carpeta_destino
    )

    # Crear ruta final
    ruta_destino = os.path.abspath(
        os.path.join(
            carpeta_base,
            nombre_archivo
        )
    )

    try:

        ruta_comun = os.path.commonpath(
            [
                carpeta_base,
                ruta_destino
            ]
        )

    except ValueError:

        raise RuntimeError(
            "El archivo comprimido contiene una ruta no válida."
        )

    # Evitar que un archivo salga de la carpeta temporal
    if ruta_comun != carpeta_base:

        raise RuntimeError(
            "El archivo comprimido contiene rutas potencialmente inseguras."
        )

    return ruta_destino


# ================================================================
# COMPROBAR CONTENEDOR ZIP
# ================================================================
def comprobar_contenedor_zip(ruta_archivo):

    return zipfile.is_zipfile(
        ruta_archivo
    )


# ================================================================
# CONVERTIR CONTENEDOR ZIP
# ================================================================
def convertir_contenedor_zip(
    ruta_origen,
    ruta_destino
):

    # Comprobar estructura real
    if not comprobar_contenedor_zip(
        ruta_origen
    ):

        raise ValueError(
            "El archivo seleccionado no contiene "
            "una estructura ZIP válida."
        )

    # Copiar exactamente los mismos bytes
    shutil.copy2(
        ruta_origen,
        ruta_destino
    )

    return ruta_destino


# ================================================================
# EXTRAER ZIP INTERNAMENTE
# ================================================================
def extraer_zip_interno(
    ruta_origen,
    carpeta_destino
):

    # Comprobar ZIP real
    if not zipfile.is_zipfile(
        ruta_origen
    ):

        raise RuntimeError(
            "El archivo no contiene una estructura ZIP válida."
        )

    # Abrir ZIP
    with zipfile.ZipFile(
        ruta_origen,
        "r"
    ) as archivo_zip:

        # Extraer cada elemento de forma controlada
        for informacion in archivo_zip.infolist():

            # Detectar enlaces simbólicos de sistemas Unix
            modo = (
                informacion.external_attr
                >> 16
            )

            if stat.S_ISLNK(modo):

                raise RuntimeError(
                    "El archivo contiene enlaces simbólicos. "
                    "Por seguridad no se extraerán automáticamente."
                )

            ruta_salida = obtener_ruta_extraccion_segura(
                carpeta_destino,
                informacion.filename
            )

            # Directorio
            if informacion.is_dir():

                os.makedirs(
                    ruta_salida,
                    exist_ok=True
                )

                continue

            # Crear carpeta contenedora
            os.makedirs(
                os.path.dirname(ruta_salida),
                exist_ok=True
            )

            # Copiar contenido
            with archivo_zip.open(
                informacion,
                "r"
            ) as archivo_origen:

                with open(
                    ruta_salida,
                    "wb"
                ) as archivo_destino:

                    shutil.copyfileobj(
                        archivo_origen,
                        archivo_destino
                    )

    return carpeta_destino


# ================================================================
# EXTRAER TAR INTERNAMENTE
# ================================================================
def extraer_tar_interno(
    ruta_origen,
    carpeta_destino
):

    # Abrir TAR y detectar compresión
    with tarfile.open(
        ruta_origen,
        "r:*"
    ) as archivo_tar:

        # Recorrer contenido manualmente
        for miembro in archivo_tar.getmembers():

            # No extraer enlaces ni dispositivos
            if miembro.issym() or miembro.islnk():
                raise RuntimeError(
                    "El archivo TAR contiene enlaces simbólicos. "
                    "Por seguridad no se extraerán automáticamente."
                )

            # Ignorar elementos especiales
            if not miembro.isdir() and not miembro.isfile():
                continue

            ruta_salida = obtener_ruta_extraccion_segura(
                carpeta_destino,
                miembro.name
            )

            # Directorio
            if miembro.isdir():

                os.makedirs(
                    ruta_salida,
                    exist_ok=True
                )

                continue

            # Archivo normal
            archivo_origen = archivo_tar.extractfile(
                miembro
            )

            if archivo_origen is None:
                continue

            os.makedirs(
                os.path.dirname(ruta_salida),
                exist_ok=True
            )

            with archivo_origen:

                with open(
                    ruta_salida,
                    "wb"
                ) as archivo_destino:

                    shutil.copyfileobj(
                        archivo_origen,
                        archivo_destino
                    )

    return carpeta_destino


# ================================================================
# EXTRAER FLUJO COMPRIMIDO
# ================================================================
def extraer_flujo_interno(
    ruta_origen,
    carpeta_destino,
    formato_origen
):

    formato_origen = formato_origen.upper()

    # Obtener nombre original aproximado
    nombre_salida = obtener_nombre_sin_extension(
        ruta_origen
    )

    if not nombre_salida:
        nombre_salida = "contenido"

    ruta_salida = os.path.join(
        carpeta_destino,
        nombre_salida
    )


    # ----------------------------------- #
    #              GZIP                   #
    # ----------------------------------- #

    if formato_origen == "GZ":

        archivo_comprimido = gzip.open(
            ruta_origen,
            "rb"
        )


    # ----------------------------------- #
    #              BZIP2                  #
    # ----------------------------------- #

    elif formato_origen == "BZ2":

        archivo_comprimido = bz2.open(
            ruta_origen,
            "rb"
        )


    # ----------------------------------- #
    #               XZ                    #
    # ----------------------------------- #

    elif formato_origen == "XZ":

        archivo_comprimido = lzma.open(
            ruta_origen,
            "rb",
            format=lzma.FORMAT_XZ
        )


    # ----------------------------------- #
    #              LZMA                   #
    # ----------------------------------- #

    elif formato_origen == "LZMA":

        archivo_comprimido = lzma.open(
            ruta_origen,
            "rb",
            format=lzma.FORMAT_ALONE
        )


    # ----------------------------------- #
    #          Formato desconocido        #
    # ----------------------------------- #

    else:

        raise ValueError(
            f"No existe un extractor interno para {formato_origen}."
        )


    # ----------------------------------- #
    #          Descomprimir               #
    # ----------------------------------- #

    with archivo_comprimido:

        with open(
            ruta_salida,
            "wb"
        ) as archivo_destino:

            shutil.copyfileobj(
                archivo_comprimido,
                archivo_destino
            )


    return carpeta_destino


# ================================================================
# VALIDAR CONTENIDO EXTRAÍDO
# ================================================================
def validar_contenido_extraido(
    carpeta_contenido
):

    encontrado = False

    # Recorrer contenido
    for carpeta_actual, carpetas, archivos in os.walk(
        carpeta_contenido,
        followlinks=False
    ):

        # Revisar directorios
        for nombre in carpetas:

            ruta = os.path.join(
                carpeta_actual,
                nombre
            )

            if os.path.islink(ruta):

                raise RuntimeError(
                    "El archivo comprimido contiene enlaces "
                    "simbólicos que no se procesarán automáticamente."
                )

            encontrado = True

        # Revisar archivos
        for nombre in archivos:

            ruta = os.path.join(
                carpeta_actual,
                nombre
            )

            if os.path.islink(ruta):

                raise RuntimeError(
                    "El archivo comprimido contiene enlaces "
                    "simbólicos que no se procesarán automáticamente."
                )

            encontrado = True

    if not encontrado:

        raise RuntimeError(
            "El archivo comprimido no contiene elementos para convertir."
        )


# ================================================================
# EXTRAER ARCHIVO COMPRIMIDO
# ================================================================
def extraer_archivo_comprimido(
    ruta_origen,
    carpeta_destino
):

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )


    # ----------------------------------- #
    #               ZIP                   #
    # ----------------------------------- #

    if formato_origen == "ZIP":

        extraer_zip_interno(
            ruta_origen,
            carpeta_destino
        )


    # ----------------------------------- #
    #            TAR y variantes          #
    # ----------------------------------- #

    elif formato_origen in {
        "TAR",
        "TAR.GZ",
        "TAR.BZ2",
        "TAR.XZ"
    }:

        extraer_tar_interno(
            ruta_origen,
            carpeta_destino
        )


    # ----------------------------------- #
    #       Compresores de un archivo     #
    # ----------------------------------- #

    elif formato_origen in {
        "GZ",
        "BZ2",
        "XZ",
        "LZMA"
    }:

        extraer_flujo_interno(
            ruta_origen,
            carpeta_destino,
            formato_origen
        )


    # ----------------------------------- #
    #              7-Zip                  #
    # ----------------------------------- #

    elif detectar_7zip():

        extraer_con_7zip(
            ruta_origen,
            carpeta_destino
        )


    # ----------------------------------- #
    #              WinRAR                 #
    # ----------------------------------- #

    elif detectar_winrar():

        extraer_con_winrar(
            ruta_origen,
            carpeta_destino
        )


    # ----------------------------------- #
    #           Sin extractor             #
    # ----------------------------------- #

    else:

        raise RuntimeError(
            f"No existe un motor disponible para extraer "
            f"archivos {formato_origen}."
        )


    # Comprobar resultado
    validar_contenido_extraido(
        carpeta_destino
    )

    return carpeta_destino


# ================================================================
# CREAR ZIP INTERNAMENTE
# ================================================================
def crear_zip_interno(
    carpeta_origen,
    ruta_destino
):

    with zipfile.ZipFile(
        ruta_destino,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9
    ) as archivo_zip:

        for carpeta_actual, carpetas, archivos in os.walk(
            carpeta_origen
        ):

            # Ruta relativa
            ruta_relativa_carpeta = os.path.relpath(
                carpeta_actual,
                carpeta_origen
            )


            # -------------------------------- #
            #       Directorios vacíos         #
            # -------------------------------- #

            if not carpetas and not archivos:

                if ruta_relativa_carpeta != ".":

                    nombre_zip = (
                        ruta_relativa_carpeta.replace(
                            os.sep,
                            "/"
                        )
                        + "/"
                    )

                    archivo_zip.writestr(
                        nombre_zip,
                        b""
                    )


            # -------------------------------- #
            #             Archivos             #
            # -------------------------------- #

            for nombre_archivo in archivos:

                ruta_archivo = os.path.join(
                    carpeta_actual,
                    nombre_archivo
                )

                ruta_relativa = os.path.relpath(
                    ruta_archivo,
                    carpeta_origen
                )

                archivo_zip.write(
                    ruta_archivo,
                    ruta_relativa
                )

    return ruta_destino


# ================================================================
# CREAR TAR INTERNAMENTE
# ================================================================
def crear_tar_interno(
    carpeta_origen,
    ruta_destino,
    formato_destino
):

    formato_destino = formato_destino.upper()

    modos = {
        "TAR": "w",
        "TAR.GZ": "w:gz",
        "TAR.BZ2": "w:bz2",
        "TAR.XZ": "w:xz"
    }

    modo = modos.get(
        formato_destino
    )

    if not modo:

        raise ValueError(
            f"No existe configuración TAR para {formato_destino}."
        )

    # Crear TAR
    with tarfile.open(
        ruta_destino,
        modo
    ) as archivo_tar:

        # Añadir únicamente los elementos raíz
        for nombre in os.listdir(
            carpeta_origen
        ):

            ruta = os.path.join(
                carpeta_origen,
                nombre
            )

            archivo_tar.add(
                ruta,
                arcname=nombre,
                recursive=True
            )

    return ruta_destino


# ================================================================
# OBTENER ÚNICO ARCHIVO
# ================================================================
def obtener_archivo_unico(
    carpeta_origen
):

    archivos_encontrados = []

    # Buscar todos los archivos reales
    for carpeta_actual, _, archivos in os.walk(
        carpeta_origen
    ):

        for nombre in archivos:

            ruta = os.path.join(
                carpeta_actual,
                nombre
            )

            if os.path.isfile(ruta):
                archivos_encontrados.append(
                    ruta
                )


    # Estos formatos no pueden almacenar
    # varios archivos ni directorios
    if len(archivos_encontrados) != 1:

        raise RuntimeError(
            "El formato de destino seleccionado solamente puede "
            "comprimir un archivo individual.\n\n"
            "El contenido actual contiene más de un archivo. "
            "Utiliza TAR.GZ, TAR.BZ2, TAR.XZ, ZIP o 7Z."
        )

    return archivos_encontrados[0]


# ================================================================
# CREAR FLUJO COMPRIMIDO
# ================================================================
def crear_flujo_interno(
    carpeta_origen,
    ruta_destino,
    formato_destino
):

    formato_destino = formato_destino.upper()

    # Obtener único archivo
    ruta_archivo = obtener_archivo_unico(
        carpeta_origen
    )


    # ----------------------------------- #
    #              GZIP                   #
    # ----------------------------------- #

    if formato_destino == "GZ":

        with open(
            ruta_destino,
            "wb"
        ) as archivo_salida:

            with gzip.GzipFile(
                filename=os.path.basename(ruta_archivo),
                mode="wb",
                fileobj=archivo_salida,
                compresslevel=9
            ) as archivo_comprimido:

                with open(
                    ruta_archivo,
                    "rb"
                ) as archivo_origen:

                    shutil.copyfileobj(
                        archivo_origen,
                        archivo_comprimido
                    )


    # ----------------------------------- #
    #              BZIP2                  #
    # ----------------------------------- #

    elif formato_destino == "BZ2":

        with open(
            ruta_archivo,
            "rb"
        ) as archivo_origen:

            with bz2.open(
                ruta_destino,
                "wb",
                compresslevel=9
            ) as archivo_comprimido:

                shutil.copyfileobj(
                    archivo_origen,
                    archivo_comprimido
                )


    # ----------------------------------- #
    #               XZ                    #
    # ----------------------------------- #

    elif formato_destino == "XZ":

        with open(
            ruta_archivo,
            "rb"
        ) as archivo_origen:

            with lzma.open(
                ruta_destino,
                "wb",
                format=lzma.FORMAT_XZ,
                preset=9
            ) as archivo_comprimido:

                shutil.copyfileobj(
                    archivo_origen,
                    archivo_comprimido
                )


    # ----------------------------------- #
    #              LZMA                   #
    # ----------------------------------- #

    elif formato_destino == "LZMA":

        with open(
            ruta_archivo,
            "rb"
        ) as archivo_origen:

            with lzma.open(
                ruta_destino,
                "wb",
                format=lzma.FORMAT_ALONE,
                preset=9
            ) as archivo_comprimido:

                shutil.copyfileobj(
                    archivo_origen,
                    archivo_comprimido
                )


    # ----------------------------------- #
    #         Formato desconocido         #
    # ----------------------------------- #

    else:

        raise ValueError(
            f"No existe un compresor interno para {formato_destino}."
        )


    return ruta_destino


# ================================================================
# CREAR ARCHIVO COMPRIMIDO
# ================================================================
def crear_archivo_comprimido(
    carpeta_origen,
    ruta_destino,
    formato_destino
):

    formato_destino = formato_destino.upper()


    # ----------------------------------- #
    #               ZIP                   #
    # ----------------------------------- #

    if formato_destino == "ZIP":

        return crear_zip_interno(
            carpeta_origen,
            ruta_destino
        )


    # ----------------------------------- #
    #          TAR y variantes            #
    # ----------------------------------- #

    if formato_destino in {
        "TAR",
        "TAR.GZ",
        "TAR.BZ2",
        "TAR.XZ"
    }:

        return crear_tar_interno(
            carpeta_origen,
            ruta_destino,
            formato_destino
        )


    # ----------------------------------- #
    #     Compresión de archivo único     #
    # ----------------------------------- #

    if formato_destino in {
        "GZ",
        "BZ2",
        "XZ",
        "LZMA"
    }:

        return crear_flujo_interno(
            carpeta_origen,
            ruta_destino,
            formato_destino
        )


    # ----------------------------------- #
    #              7-Zip                  #
    # ----------------------------------- #

    if formato_destino in FORMATOS_SALIDA_7ZIP:

        return crear_con_7zip(
            carpeta_origen,
            ruta_destino,
            formato_destino
        )


    # ----------------------------------- #
    #               RAR                   #
    # ----------------------------------- #

    if formato_destino == "RAR":

        return crear_rar_con_winrar(
            carpeta_origen,
            ruta_destino
        )


    raise NotImplementedError(
        f"La creación de {formato_destino} "
        f"todavía no está implementada."
    )


# ================================================================
# COMPROBAR CONVERSIÓN IMPLEMENTADA
# ================================================================
def conversion_comprimido_implementada(
    ruta_origen,
    formato_destino
):

    # Debe ser archivo comprimido
    if obtener_categoria_archivo(
        ruta_origen
    ) != "comprimido":

        return False

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()


    # ----------------------------------- #
    #      Casos tratados por separado    #
    # ----------------------------------- #

    # Minecraft solamente se manejará mediante
    # las conversiones ZIP especiales acordadas
    if formato_origen in FORMATOS_ZIP_ESPECIALES:
        return False

    # JAR tendrá lógica propia posteriormente
    if formato_origen == "JAR":
        return False


    # ----------------------------------- #
    #      Comprobar salida disponible    #
    # ----------------------------------- #

    return (
        formato_origen != formato_destino
        and formato_destino in FORMATOS_SALIDA_IMPLEMENTADOS
    )


# ================================================================
# COMPROBAR FUENTE DISPONIBLE
# ================================================================
def comprobar_fuente_comprimida(
    ruta_origen
):

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )


    # ----------------------------------- #
    #         Lectura interna             #
    # ----------------------------------- #

    if formato_origen in FORMATOS_ENTRADA_INTERNOS:

        # ZIP puede verificarse inmediatamente
        if formato_origen == "ZIP":

            if not zipfile.is_zipfile(
                ruta_origen
            ):

                return (
                    False,
                    "El archivo no contiene una estructura ZIP válida."
                )

        # TAR y sus variantes
        if formato_origen in {
            "TAR",
            "TAR.GZ",
            "TAR.BZ2",
            "TAR.XZ"
        }:

            if not tarfile.is_tarfile(
                ruta_origen
            ):

                return (
                    False,
                    "El archivo no contiene una estructura TAR válida."
                )

        return True, None


    # ----------------------------------- #
    #              7-Zip                  #
    # ----------------------------------- #

    if detectar_7zip():

        return comprobar_lectura_7zip(
            ruta_origen
        )


    # ----------------------------------- #
    #              WinRAR                 #
    # ----------------------------------- #

    if detectar_winrar():

        return comprobar_lectura_winrar(
            ruta_origen
        )


    return (
        False,
        f"No existe un motor disponible para leer "
        f"archivos {formato_origen}."
    )


# ================================================================
# COMPROBAR SALIDA DISPONIBLE
# ================================================================
def comprobar_salida_comprimida(
    formato_destino
):

    formato_destino = formato_destino.upper()


    # ----------------------------------- #
    #           Salidas internas          #
    # ----------------------------------- #

    if formato_destino in FORMATOS_SALIDA_INTERNOS:
        return True, None


    # ----------------------------------- #
    #              7-Zip                  #
    # ----------------------------------- #

    if formato_destino in FORMATOS_SALIDA_7ZIP:

        if detectar_7zip():
            return True, None

        return (
            False,
            f"La creación de {formato_destino} necesita 7-Zip, "
            f"pero no se encontró disponible."
        )


    # ----------------------------------- #
    #               RAR                   #
    # ----------------------------------- #

    if formato_destino == "RAR":

        if detectar_winrar():
            return True, None

        return (
            False,
            "Para crear archivos RAR se necesita WinRAR, "
            "pero no se encontró instalado."
        )


    return (
        False,
        f"La creación de {formato_destino} "
        f"todavía no está implementada."
    )


# ================================================================
# COMPROBAR CONVERSIÓN DISPONIBLE
# ================================================================
def comprobar_comprimido_disponible(
    ruta_origen,
    formato_destino
):

    # Comprobar implementación
    if not conversion_comprimido_implementada(
        ruta_origen,
        formato_destino
    ):

        return (
            False,
            f"La conversión a {formato_destino} todavía "
            f"no está implementada para este archivo comprimido."
        )

    # Comprobar entrada
    disponible, mensaje = comprobar_fuente_comprimida(
        ruta_origen
    )

    if not disponible:
        return False, mensaje

    # Comprobar salida
    return comprobar_salida_comprimida(
        formato_destino
    )


# ================================================================
# CONVERTIR ARCHIVO COMPRIMIDO
# ================================================================
def convertir_comprimido(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    # Comprobar disponibilidad
    disponible, mensaje = comprobar_comprimido_disponible(
        ruta_origen,
        formato_destino
    )

    if not disponible:
        raise RuntimeError(
            mensaje
        )


    # ============================================================
    # CREAR ENTORNO TEMPORAL
    # ============================================================

    with tempfile.TemporaryDirectory() as carpeta_temporal:

        carpeta_contenido = os.path.join(
            carpeta_temporal,
            "contenido"
        )

        os.makedirs(
            carpeta_contenido,
            exist_ok=True
        )


        # ----------------------------------- #
        #             Extraer                 #
        # ----------------------------------- #

        extraer_archivo_comprimido(
            ruta_origen,
            carpeta_contenido
        )


        # ----------------------------------- #
        #        Crear nuevo contenedor       #
        # ----------------------------------- #

        crear_archivo_comprimido(
            carpeta_contenido,
            ruta_destino,
            formato_destino
        )


    return ruta_destino