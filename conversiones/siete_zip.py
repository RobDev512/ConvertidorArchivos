import os
import subprocess

from funciones.capacidades import detectar_7zip


# ----------------------------------- #
#        Tipos de creación 7-Zip      #
# ----------------------------------- #

TIPOS_CREACION_7ZIP = {
    "7Z": "7z",
    "WIM": "wim"
}


# ================================================================
# CREAR OPCIONES DE SUBPROCESO
# ================================================================
def crear_opciones_subproceso():

    opciones = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "errors": "replace"
    }

    # Evitar consola adicional en Windows
    if os.name == "nt":
        opciones["creationflags"] = subprocess.CREATE_NO_WINDOW

    return opciones


# ================================================================
# EJECUTAR 7-ZIP
# ================================================================
def ejecutar_7zip(argumentos, carpeta_trabajo=None):

    # Buscar ejecutable
    ruta_7zip = detectar_7zip()

    if not ruta_7zip:
        raise RuntimeError(
            "7-Zip no está disponible."
        )

    # Crear comando
    comando = [
        ruta_7zip,
        *argumentos
    ]

    # Ejecutar
    resultado = subprocess.run(
        comando,
        cwd=carpeta_trabajo,
        **crear_opciones_subproceso()
    )

    # Comprobar resultado
    if resultado.returncode != 0:

        detalle = (
            resultado.stderr.strip()
            or resultado.stdout.strip()
            or f"7-Zip terminó con el código {resultado.returncode}."
        )

        raise RuntimeError(
            f"7-Zip no pudo completar la operación.\n\n"
            f"{detalle}"
        )

    return resultado


# ================================================================
# COMPROBAR LECTURA CON 7-ZIP
# ================================================================
def comprobar_lectura_7zip(ruta_archivo):

    if not detectar_7zip():
        return False, "7-Zip no está disponible."

    try:

        # Listar contenido sin extraerlo
        ejecutar_7zip(
            [
                "l",
                "-slt",
                os.path.abspath(ruta_archivo)
            ]
        )

        return True, None

    except Exception as error:

        return False, str(error)


# ================================================================
# EXTRAER CON 7-ZIP
# ================================================================
def extraer_con_7zip(ruta_origen, carpeta_destino):

    # Asegurar carpeta
    os.makedirs(
        carpeta_destino,
        exist_ok=True
    )

    # Extraer conservando estructura
    ejecutar_7zip(
        [
            "x",
            "-y",
            f"-o{os.path.abspath(carpeta_destino)}",
            os.path.abspath(ruta_origen)
        ]
    )

    return carpeta_destino


# ================================================================
# CREAR CON 7-ZIP
# ================================================================
def crear_con_7zip(
    carpeta_origen,
    ruta_destino,
    formato_destino
):

    formato_destino = formato_destino.upper()

    # Obtener tipo interno de 7-Zip
    tipo_7zip = TIPOS_CREACION_7ZIP.get(
        formato_destino
    )

    if not tipo_7zip:

        raise ValueError(
            f"7-Zip no tiene configurada la creación "
            f"de {formato_destino} en la aplicación."
        )

    # Trabajar desde la carpeta de contenido para
    # no incluir el nombre de la carpeta temporal
    ejecutar_7zip(
        [
            "a",
            "-y",
            f"-t{tipo_7zip}",
            os.path.abspath(ruta_destino),
            "*"
        ],
        carpeta_trabajo=carpeta_origen
    )

    return ruta_destino