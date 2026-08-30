# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import (
    collect_all,
    copy_metadata
)


# ================================================================
# RUTAS GENERALES
# ================================================================

CARPETA_PROYECTO = os.path.abspath(
    SPECPATH
)

RUTA_PRINCIPAL = os.path.join(
    CARPETA_PROYECTO,
    "ConvertidorArchivos.py"
)

CARPETA_RECURSOS = os.path.join(
    CARPETA_PROYECTO,
    "recursos"
)

RUTA_ICONO = os.path.join(
    CARPETA_RECURSOS,
    "iconos",
    "FileConverter.ico"
)

RUTA_VERSION = os.path.join(
    CARPETA_PROYECTO,
    "version_info.txt"
)


# ----------------------------------- #
#      Icono opcional de la app       #
# ----------------------------------- #

if not os.path.isfile(
    RUTA_ICONO
):

    RUTA_ICONO = None


# ----------------------------------- #
#      Información de versión         #
# ----------------------------------- #

if not os.path.isfile(
    RUTA_VERSION
):

    RUTA_VERSION = None


# ================================================================
# ARCHIVOS Y DEPENDENCIAS ADICIONALES
# ================================================================

datos = []
binarios = []
imports_ocultos = []


# ================================================================
# RECURSOS DE LA APLICACIÓN
# ================================================================

if os.path.isdir(
    CARPETA_RECURSOS
):

    datos.append(
        (
            CARPETA_RECURSOS,
            "recursos"
        )
    )


# ================================================================
# ASPOSE.PDF
# ================================================================

datos_aspose, binarios_aspose, imports_aspose = collect_all(
    "aspose.pdf"
)

datos += datos_aspose
binarios += binarios_aspose
imports_ocultos += imports_aspose


# ----------------------------------- #
#       Metadatos de Aspose.PDF       #
# ----------------------------------- #

datos += copy_metadata(
    "aspose-pdf"
)


# ================================================================
# PDFIUM
# ================================================================

datos_pdfium, binarios_pdfium, imports_pdfium = collect_all(
    "pypdfium2"
)

datos += datos_pdfium
binarios += binarios_pdfium
imports_ocultos += imports_pdfium


# ================================================================
# PILLOW
# ================================================================

datos_pillow, binarios_pillow, imports_pillow = collect_all(
    "PIL"
)

datos += datos_pillow
binarios += binarios_pillow
imports_ocultos += imports_pillow


# ================================================================
# OPENPYXL
# ================================================================

datos_openpyxl, binarios_openpyxl, imports_openpyxl = collect_all(
    "openpyxl"
)

datos += datos_openpyxl
binarios += binarios_openpyxl
imports_ocultos += imports_openpyxl


# ================================================================
# IMPORTS ADICIONALES
# ================================================================

imports_ocultos += [
    # Aspose
    "aspose",
    "aspose.pdf",

    # PDFium
    "pypdfium2",
    "pypdfium2.raw",

    # Pillow
    "PIL",
    "PIL.Image",
    "PIL.ImageQt",

    # Excel
    "openpyxl",

    # Microsoft Office / COM
    "win32com",
    "win32com.client",
    "win32com.client.gencache",
    "pythoncom",
    "pywintypes"
]


# ----------------------------------- #
#        Eliminar duplicados          #
# ----------------------------------- #

imports_ocultos = list(
    dict.fromkeys(
        imports_ocultos
    )
)


# ================================================================
# ANÁLISIS
# ================================================================

analisis = Analysis(
    [
        RUTA_PRINCIPAL
    ],
    pathex=[
        CARPETA_PROYECTO
    ],
    binaries=binarios,
    datas=datos,
    hiddenimports=imports_ocultos,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "aspose.words",
        "pdf2docx",
        "fitz",
        "pymupdf"
    ],
    noarchive=False,
    optimize=0
)


# ================================================================
# ARCHIVO PYZ
# ================================================================

pyz = PYZ(
    analisis.pure
)


# ================================================================
# EJECUTABLE
# ================================================================

exe = EXE(
    pyz,
    analisis.scripts,
    [],
    exclude_binaries=True,
    name="ConvertidorArchivos",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=RUTA_ICONO,
    version=RUTA_VERSION,
    contents_directory="_internal"
)


# ================================================================
# CARPETA FINAL
# ================================================================

coleccion = COLLECT(
    exe,
    analisis.binaries,
    analisis.datas,
    strip=False,
    upx=False,
    name="ConvertidorArchivos"
)