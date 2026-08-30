import os
import shutil
import subprocess
import tempfile

from pathlib import Path

from funciones.capacidades import detectar_libreoffice


# ----------------------------------- #
#         Filtros para PDF            #
# ----------------------------------- #

FILTROS_PDF = {
    "writer": "pdf:writer_pdf_Export",
    "calc": "pdf:calc_pdf_Export",
    "impress": "pdf:impress_pdf_Export"
}


# ================================================================
# OBTENER ARGUMENTO DE CONVERSIÓN
# ================================================================
def obtener_argumento_conversion(formato_destino, tipo_documento):

    # Normalizar formato
    formato_destino = formato_destino.upper()

    # PDF utiliza un filtro diferente según el tipo de documento
    if formato_destino == "PDF":

        filtro_pdf = FILTROS_PDF.get(tipo_documento)

        if not filtro_pdf:
            raise ValueError(
                "No se encontró un filtro PDF para este tipo de documento."
            )

        return filtro_pdf

    # Para los demás formatos LibreOffice puede
    # seleccionar el filtro mediante la extensión
    return formato_destino.lower()


# ================================================================
# BUSCAR ARCHIVO CONVERTIDO
# ================================================================
def buscar_archivo_convertido(carpeta_salida, formato_destino):

    # Obtener extensión esperada
    extension = "." + formato_destino.lower()

    # Buscar archivos con la extensión correspondiente
    candidatos = [
        os.path.join(carpeta_salida, archivo)
        for archivo in os.listdir(carpeta_salida)
        if archivo.lower().endswith(extension)
    ]

    # No se generó ningún resultado
    if not candidatos:
        return None

    # LibreOffice debería generar únicamente uno
    return candidatos[0]


# ================================================================
# EJECUTAR LIBREOFFICE
# ================================================================
def ejecutar_libreoffice(
    ruta_origen,
    formato_destino,
    tipo_documento
):

    # Buscar LibreOffice
    ruta_libreoffice = detectar_libreoffice()

    if not ruta_libreoffice:
        raise RuntimeError(
            "LibreOffice no está instalado o no pudo encontrarse."
        )


    # Crear carpetas temporales independientes
    with tempfile.TemporaryDirectory() as carpeta_temporal:

        carpeta_salida = os.path.join(
            carpeta_temporal,
            "salida"
        )

        carpeta_perfil = os.path.join(
            carpeta_temporal,
            "perfil"
        )

        os.makedirs(
            carpeta_salida,
            exist_ok=True
        )

        os.makedirs(
            carpeta_perfil,
            exist_ok=True
        )


        # ----------------------------------- #
        #      Preparar perfil temporal       #
        # ----------------------------------- #

        ruta_perfil = Path(
            carpeta_perfil
        ).resolve().as_uri()


        # ----------------------------------- #
        #     Preparar tipo de conversión     #
        # ----------------------------------- #

        argumento_conversion = obtener_argumento_conversion(
            formato_destino,
            tipo_documento
        )


        # ----------------------------------- #
        #          Crear comando              #
        # ----------------------------------- #

        comando = [
            ruta_libreoffice,
            "--headless",
            "--nologo",
            "--nodefault",
            "--norestore",
            f"-env:UserInstallation={ruta_perfil}",
            "--convert-to",
            argumento_conversion,
            "--outdir",
            carpeta_salida,
            ruta_origen
        ]


        # ----------------------------------- #
        #         Ejecutar conversión          #
        # ----------------------------------- #

        opciones_subproceso = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace"
        }

        # Evitar que aparezca una consola en Windows
        if os.name == "nt":
            opciones_subproceso["creationflags"] = (
                subprocess.CREATE_NO_WINDOW
            )

        resultado = subprocess.run(
            comando,
            **opciones_subproceso
        )


        # ----------------------------------- #
        #          Buscar resultado           #
        # ----------------------------------- #

        ruta_generada = buscar_archivo_convertido(
            carpeta_salida,
            formato_destino
        )

        # Comprobar que LibreOffice realmente
        # haya generado el archivo
        if not ruta_generada:

            mensaje_error = (
                resultado.stderr.strip()
                or resultado.stdout.strip()
                or "LibreOffice no generó ningún archivo."
            )

            raise RuntimeError(
                f"No fue posible realizar la conversión.\n\n"
                f"{mensaje_error}"
            )


        # Leer el resultado antes de eliminar
        # la carpeta temporal
        with open(ruta_generada, "rb") as archivo:
            datos_resultado = archivo.read()


    return datos_resultado


# ================================================================
# CONVERTIR CON LIBREOFFICE
# ================================================================
def convertir_con_libreoffice(
    ruta_origen,
    ruta_destino,
    formato_destino,
    tipo_documento
):

    # Realizar conversión en carpeta temporal
    datos_resultado = ejecutar_libreoffice(
        ruta_origen,
        formato_destino,
        tipo_documento
    )

    # Guardar resultado en la ruta indicada
    with open(ruta_destino, "wb") as archivo:
        archivo.write(
            datos_resultado
        )

    return ruta_destino