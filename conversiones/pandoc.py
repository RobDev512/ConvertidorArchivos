import os
import subprocess

from functools import lru_cache

from funciones.capacidades import detectar_pandoc
from funciones.formatos import obtener_formato_archivo


# ----------------------------------- #
#       Lectores de Pandoc            #
# ----------------------------------- #

LECTORES_PANDOC = {
    "DOCX": "docx",
    "ODT": "odt",
    "RTF": "rtf",
    "HTML": "html",
    "XHTML": "html",
    "MD": "markdown",

    "EPUB": "epub",
    "FB2": "fb2",
    "RST": "rst",
    "LATEX": "latex",
    "ASCIIDOC": "asciidoc",
    "OPML": "opml",
    "ORG": "org",
    "JUPYTER": "ipynb"
}


# ----------------------------------- #
#       Escritores de Pandoc          #
# ----------------------------------- #

ESCRITORES_PANDOC = {
    "DOCX": "docx",
    "ODT": "odt",
    "RTF": "rtf",
    "TXT": "plain",
    "HTML": "html5",
    "XHTML": "html5",
    "MD": "markdown",

    "EPUB": "epub3",
    "FB2": "fb2",
    "RST": "rst",
    "LATEX": "latex",
    "ASCIIDOC": "asciidoc",
    "OPML": "opml",
    "ORG": "org",
    "JUPYTER": "ipynb"
}


# ================================================================
# CREAR OPCIONES DE SUBPROCESO
# ================================================================
def crear_opciones_subproceso():

    opciones = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace"
    }

    # Evitar consola adicional en Windows
    if os.name == "nt":
        opciones["creationflags"] = subprocess.CREATE_NO_WINDOW

    return opciones


# ================================================================
# CONSULTAR FORMATOS DE PANDOC
# ================================================================
@lru_cache(maxsize=4)
def consultar_formatos_pandoc(ruta_pandoc):

    # ----------------------------------- #
    #        Consultar entradas           #
    # ----------------------------------- #

    resultado_entradas = subprocess.run(
        [
            ruta_pandoc,
            "--list-input-formats"
        ],
        **crear_opciones_subproceso()
    )

    if resultado_entradas.returncode != 0:

        detalle = (
            resultado_entradas.stderr.strip()
            or resultado_entradas.stdout.strip()
            or "Pandoc no pudo informar sus formatos de entrada."
        )

        raise RuntimeError(
            f"No fue posible consultar los formatos "
            f"de entrada de Pandoc.\n\n{detalle}"
        )


    # ----------------------------------- #
    #         Consultar salidas           #
    # ----------------------------------- #

    resultado_salidas = subprocess.run(
        [
            ruta_pandoc,
            "--list-output-formats"
        ],
        **crear_opciones_subproceso()
    )

    if resultado_salidas.returncode != 0:

        detalle = (
            resultado_salidas.stderr.strip()
            or resultado_salidas.stdout.strip()
            or "Pandoc no pudo informar sus formatos de salida."
        )

        raise RuntimeError(
            f"No fue posible consultar los formatos "
            f"de salida de Pandoc.\n\n{detalle}"
        )


    # ----------------------------------- #
    #          Preparar resultado         #
    # ----------------------------------- #

    entradas = {
        formato.strip().lower()
        for formato in resultado_entradas.stdout.splitlines()
        if formato.strip()
    }

    salidas = {
        formato.strip().lower()
        for formato in resultado_salidas.stdout.splitlines()
        if formato.strip()
    }

    return {
        "entrada": entradas,
        "salida": salidas
    }


# ================================================================
# OBTENER FORMATOS DE PANDOC
# ================================================================
def obtener_formatos_pandoc():

    ruta_pandoc = detectar_pandoc()

    if not ruta_pandoc:
        return {
            "entrada": set(),
            "salida": set()
        }

    return consultar_formatos_pandoc(
        ruta_pandoc
    )


# ================================================================
# COMPROBAR CONVERSIÓN DE PANDOC
# ================================================================
def comprobar_conversion_pandoc(
    ruta_origen,
    formato_destino
):

    # Buscar motor
    ruta_pandoc = detectar_pandoc()

    if not ruta_pandoc:

        return (
            False,
            "Esta conversión necesita Pandoc, "
            "pero no se encontró disponible."
        )

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()

    # Obtener lector
    lector = LECTORES_PANDOC.get(
        formato_origen
    )

    if not lector:

        return (
            False,
            f"No se ha configurado un lector de Pandoc "
            f"para archivos {formato_origen}."
        )

    # Obtener escritor
    escritor = ESCRITORES_PANDOC.get(
        formato_destino
    )

    if not escritor:

        return (
            False,
            f"No se ha configurado una salida de Pandoc "
            f"para archivos {formato_destino}."
        )


    # ----------------------------------- #
    #       Consultar esta instalación    #
    # ----------------------------------- #

    formatos = obtener_formatos_pandoc()

    if lector not in formatos["entrada"]:

        return (
            False,
            f"La instalación actual de Pandoc no puede "
            f"leer archivos {formato_origen}."
        )

    if escritor not in formatos["salida"]:

        return (
            False,
            f"La instalación actual de Pandoc no puede "
            f"escribir archivos {formato_destino}."
        )

    return True, None


# ================================================================
# CONVERTIR CON PANDOC
# ================================================================
def convertir_con_pandoc(
    ruta_origen,
    ruta_destino,
    formato_destino
):

    # Comprobar disponibilidad
    disponible, mensaje = comprobar_conversion_pandoc(
        ruta_origen,
        formato_destino
    )

    if not disponible:
        raise RuntimeError(
            mensaje
        )

    # Buscar Pandoc
    ruta_pandoc = detectar_pandoc()

    formato_origen = obtener_formato_archivo(
        ruta_origen
    )

    formato_destino = formato_destino.upper()

    # Obtener lector y escritor
    lector = LECTORES_PANDOC[
        formato_origen
    ]

    escritor = ESCRITORES_PANDOC[
        formato_destino
    ]

    # Normalizar rutas
    ruta_origen = os.path.abspath(
        ruta_origen
    )

    ruta_destino = os.path.abspath(
        ruta_destino
    )

    carpeta_origen = os.path.dirname(
        ruta_origen
    )


    # ----------------------------------- #
    #          Crear comando              #
    # ----------------------------------- #

    comando = [
        ruta_pandoc,
        "--from",
        lector,
        "--to",
        escritor,
        "--standalone"
    ]


    # ----------------------------------- #
    #        HTML autocontenido           #
    # ----------------------------------- #

    if formato_destino in {
        "HTML",
        "XHTML"
    }:

        comando.append(
            "--embed-resources"
        )


    # ----------------------------------- #
    #        Añadir salida y entrada      #
    # ----------------------------------- #

    comando.extend(
        [
            "--output",
            ruta_destino,
            ruta_origen
        ]
    )


    # ----------------------------------- #
    #          Ejecutar Pandoc            #
    # ----------------------------------- #

    resultado = subprocess.run(
        comando,
        cwd=carpeta_origen,
        **crear_opciones_subproceso()
    )

    if resultado.returncode != 0:

        detalle = (
            resultado.stderr.strip()
            or resultado.stdout.strip()
            or "Pandoc no pudo completar la conversión."
        )

        raise RuntimeError(
            f"Pandoc no pudo convertir el archivo.\n\n"
            f"{detalle}"
        )


    # ----------------------------------- #
    #       Comprobar resultado           #
    # ----------------------------------- #

    if not os.path.isfile(
        ruta_destino
    ):

        raise RuntimeError(
            "Pandoc terminó sin generar el archivo esperado."
        )

    return ruta_destino