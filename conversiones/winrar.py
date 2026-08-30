import os
import subprocess

from funciones.capacidades import detectar_winrar


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

    # Evitar consola adicional
    if os.name == "nt":
        opciones["creationflags"] = subprocess.CREATE_NO_WINDOW

    return opciones


# ================================================================
# EJECUTAR WINRAR
# ================================================================
def ejecutar_winrar(argumentos, carpeta_trabajo=None):

    # Buscar WinRAR o RAR
    ruta_winrar = detectar_winrar()

    if not ruta_winrar:
        raise RuntimeError(
            "WinRAR no está disponible."
        )

    # Crear comando
    comando = [
        ruta_winrar,
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
            or f"WinRAR terminó con el código {resultado.returncode}."
        )

        raise RuntimeError(
            f"WinRAR no pudo completar la operación.\n\n"
            f"{detalle}"
        )

    return resultado


# ================================================================
# COMPROBAR LECTURA CON WINRAR
# ================================================================
def comprobar_lectura_winrar(ruta_archivo):

    if not detectar_winrar():
        return False, "WinRAR no está disponible."

    try:

        # Probar integridad del archivo
        ejecutar_winrar(
            [
                "t",
                "-ibck",
                "-y",
                os.path.abspath(ruta_archivo)
            ]
        )

        return True, None

    except Exception as error:

        return False, str(error)


# ================================================================
# EXTRAER CON WINRAR
# ================================================================
def extraer_con_winrar(ruta_origen, carpeta_destino):

    # Crear carpeta
    os.makedirs(
        carpeta_destino,
        exist_ok=True
    )

    # WinRAR espera una barra final en el destino
    carpeta_salida = (
        os.path.abspath(carpeta_destino)
        + os.sep
    )

    # Extraer conservando rutas
    ejecutar_winrar(
        [
            "x",
            "-ibck",
            "-y",
            os.path.abspath(ruta_origen),
            carpeta_salida
        ]
    )

    return carpeta_destino


# ================================================================
# CREAR RAR CON WINRAR
# ================================================================
def crear_rar_con_winrar(
    carpeta_origen,
    ruta_destino
):

    # Crear archivo RAR.
    # RAR.exe ya crea formato RAR de forma predeterminada,
    # así que no se utiliza el parámetro -afrar.
    ejecutar_winrar(
        [
            "a",
            "-r",
            "-ep1",
            "-ibck",
            "-y",
            os.path.abspath(ruta_destino),
            "*"
        ],
        carpeta_trabajo=carpeta_origen
    )

    return ruta_destino