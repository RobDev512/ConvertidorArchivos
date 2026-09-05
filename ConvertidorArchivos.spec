# -*- mode: python ; coding: utf-8 -*-

import glob
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

CARPETA_PDF_DOCX = os.path.join(
    CARPETA_PROYECTO,
    "conversiones",
    "pdf_docx"
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


if not os.path.isfile(
    RUTA_ICONO
):

    RUTA_ICONO = None


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
# AGREGAR PAQUETE COMPLETO
# ================================================================
def agregar_paquete(
    nombre_modulo,
    nombre_distribucion=None
):

    datos_paquete, binarios_paquete, imports_paquete = collect_all(
        nombre_modulo
    )

    datos.extend(
        datos_paquete
    )

    binarios.extend(
        binarios_paquete
    )

    imports_ocultos.extend(
        imports_paquete
    )

    if nombre_distribucion:

        try:

            datos.extend(
                copy_metadata(
                    nombre_distribucion
                )
            )

        except Exception:

            pass


# ================================================================
# RECURSOS DE LA APLICACION
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
# FUENTES DEL MOTOR PDF A DOCX
# ================================================================

if os.path.isdir(
    CARPETA_PDF_DOCX
):

    for ruta_modulo in glob.glob(
        os.path.join(
            CARPETA_PDF_DOCX,
            "*.py"
        )
    ):

        datos.append(
            (
                ruta_modulo,
                os.path.join(
                    "conversiones",
                    "pdf_docx"
                )
            )
        )


# ================================================================
# DEPENDENCIAS PRINCIPALES
# ================================================================

agregar_paquete(
    "pypdfium2",
    "pypdfium2"
)

agregar_paquete(
    "pypdf",
    "pypdf"
)

agregar_paquete(
    "PIL",
    "Pillow"
)

agregar_paquete(
    "openpyxl",
    "openpyxl"
)


# ================================================================
# MOTOR PDF A DOCX
# ================================================================

agregar_paquete(
    "pdfplumber",
    "pdfplumber"
)

agregar_paquete(
    "pdfminer",
    "pdfminer.six"
)

agregar_paquete(
    "pikepdf",
    "pikepdf"
)

agregar_paquete(
    "docx",
    "python-docx"
)

agregar_paquete(
    "lxml",
    "lxml"
)


# ================================================================
# QUITAR FONDO / IA LOCAL
# ================================================================

agregar_paquete(
    "rembg",
    "rembg"
)

agregar_paquete(
    "onnxruntime",
    "onnxruntime"
)

agregar_paquete(
    "pymatting",
    "PyMatting"
)

agregar_paquete(
    "skimage",
    "scikit-image"
)


# ================================================================
# IMPORTS ADICIONALES
# ================================================================

imports_ocultos += [
    # Motor PDF a DOCX propio
    "conversiones.pdf_docx",
    "conversiones.pdf_docx.motor_pdf_docx",
    "conversiones.pdf_docx.extraer_fondos_pdf",

    # PDFium
    "pypdfium2",
    "pypdfium2.raw",

    # pypdf
    "pypdf",

    # Pillow
    "PIL",
    "PIL.Image",
    "PIL.ImageQt",

    # PDF a DOCX
    "pdfplumber",
    "pdfminer",
    "pdfminer.high_level",
    "pikepdf",
    "docx",
    "lxml",
    "lxml.etree",

    # Excel
    "openpyxl",

    # Quitar fondo / ONNX
    "numpy",
    "onnxruntime",
    "onnxruntime.capi._pybind_state",
    "onnxruntime.capi.onnxruntime_pybind11_state",
    "rembg",
    "rembg.bg",
    "rembg.session_factory",
    "rembg.sessions",
    "rembg.sessions.u2netp",
    "rembg.sessions.dis_general_use",
    "rembg.sessions.birefnet_general",
    "pymatting",
    "skimage",

    # Microsoft Office / COM
    "win32com",
    "win32com.client",
    "win32com.client.gencache",
    "pythoncom",
    "pywintypes"
]


imports_ocultos = list(
    dict.fromkeys(
        imports_ocultos
    )
)


# ================================================================
# ANALISIS
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
        "aspose",
        "aspose.pdf",
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