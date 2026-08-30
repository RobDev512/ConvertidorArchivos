import os


# ----------------------------------- #
#       Extensiones compuestas        #
# ----------------------------------- #

EXTENSIONES_COMPUESTAS = [
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
    ".tar.zst"
]


# ================================================================
# OBTENER NOMBRE DEL ARCHIVO
# ================================================================
def obtener_nombre_archivo(ruta_archivo):

    # Obtener únicamente el nombre final de la ruta
    nombre_archivo = os.path.basename(ruta_archivo)

    return nombre_archivo


# ================================================================
# OBTENER EXTENSIÓN DEL ARCHIVO
# ================================================================
def obtener_extension_archivo(ruta_archivo):

    # Convertir temporalmente la ruta a minúsculas
    ruta_minusculas = ruta_archivo.lower()

    # Comprobar primero extensiones compuestas
    for extension in EXTENSIONES_COMPUESTAS:
        if ruta_minusculas.endswith(extension):
            return extension

    # Obtener extensión normal
    _, extension = os.path.splitext(ruta_archivo)

    return extension.lower()


# ================================================================
# OBTENER NOMBRE SIN EXTENSIÓN
# ================================================================
def obtener_nombre_sin_extension(ruta_archivo):

    # Obtener nombre completo
    nombre_archivo = obtener_nombre_archivo(ruta_archivo)

    # Obtener extensión
    extension = obtener_extension_archivo(ruta_archivo)

    # Quitar extensión
    if extension:
        return nombre_archivo[:-len(extension)]

    return nombre_archivo


# ================================================================
# ASEGURAR EXTENSIÓN
# ================================================================
def asegurar_extension(ruta_archivo, extension):

    # Comprobar si ya termina con la extensión correcta
    if ruta_archivo.lower().endswith(extension.lower()):
        return ruta_archivo

    # Añadir extensión faltante
    return ruta_archivo + extension


# ================================================================
# NORMALIZAR RUTA
# ================================================================
def normalizar_ruta(ruta_archivo):

    # Obtener representación comparable de la ruta
    ruta_normalizada = os.path.abspath(
        ruta_archivo
    )

    ruta_normalizada = os.path.normcase(
        ruta_normalizada
    )

    return ruta_normalizada


# ================================================================
# CREAR RUTA ÚNICA
# ================================================================
def crear_ruta_unica(ruta_archivo, rutas_reservadas=None):

    # Preparar conjunto de rutas ya utilizadas
    if rutas_reservadas is None:
        rutas_reservadas = set()

    # Normalizar ruta original
    ruta_normalizada = normalizar_ruta(
        ruta_archivo
    )

    # Utilizar directamente si está disponible
    if (
        not os.path.exists(ruta_archivo)
        and ruta_normalizada not in rutas_reservadas
    ):
        return ruta_archivo

    # Obtener componentes
    carpeta = os.path.dirname(ruta_archivo)
    nombre_archivo = obtener_nombre_sin_extension(
        ruta_archivo
    )
    extension = obtener_extension_archivo(
        ruta_archivo
    )

    contador = 1

    # Buscar un nombre libre
    while True:

        nueva_ruta = os.path.join(
            carpeta,
            f"{nombre_archivo}_copia_{contador}{extension}"
        )

        ruta_normalizada = normalizar_ruta(
            nueva_ruta
        )

        if (
            not os.path.exists(nueva_ruta)
            and ruta_normalizada not in rutas_reservadas
        ):
            return nueva_ruta

        contador += 1