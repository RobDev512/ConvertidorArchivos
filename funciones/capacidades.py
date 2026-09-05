import glob
import importlib.metadata
import importlib.util
import os
import shutil
import sys


# ================================================================
# OBTENER CARPETA DE LA APLICACIÓN
# ================================================================
def obtener_carpeta_aplicacion():

    if getattr(
        sys,
        "frozen",
        False
    ):
        return os.path.dirname(
            sys.executable
        )

    return os.path.dirname(
        os.path.dirname(
            os.path.abspath(
                __file__
            )
        )
    )


# ================================================================
# OBTENER CARPETA DE MOTORES
# ================================================================
def obtener_carpeta_motores():

    return os.path.join(
        obtener_carpeta_aplicacion(),
        "motores"
    )


# ================================================================
# BUSCAR EJECUTABLE
# ================================================================
def buscar_ejecutable(
    nombres,
    rutas_comunes=None
):

    for nombre in nombres:
        ruta = shutil.which(
            nombre
        )

        if ruta:
            return ruta

    if rutas_comunes:
        for ruta in rutas_comunes:
            if os.path.isfile(
                ruta
            ):
                return ruta

    return None


# ================================================================
# COMPROBAR LIBRERÍA DE PYTHON
# ================================================================
def biblioteca_instalada(
    nombre
):

    try:
        return (
            importlib.util.find_spec(
                nombre
            )
            is not None
        )

    except (
        ImportError,
        ModuleNotFoundError
    ):
        return False


# ================================================================
# COMPROBAR PAQUETE DE PYTHON
# ================================================================
def paquete_instalado(
    nombre
):

    try:
        importlib.metadata.version(
            nombre
        )
        return True

    except importlib.metadata.PackageNotFoundError:
        return False


# ================================================================
# OBTENER VERSIÓN DE PAQUETE
# ================================================================
def obtener_version_paquete(
    nombre
):

    try:
        return importlib.metadata.version(
            nombre
        )

    except importlib.metadata.PackageNotFoundError:
        return None


# ================================================================
# DETECTAR PDFIUM
# ================================================================
def detectar_pdfium():

    return biblioteca_instalada(
        "pypdfium2"
    )


# ================================================================
# DETECTAR OPENPYXL
# ================================================================
def detectar_openpyxl():

    return biblioteca_instalada(
        "openpyxl"
    )


# ================================================================
# DETECTAR PDFPLUMBER
# ================================================================
def detectar_pdfplumber():

    return biblioteca_instalada(
        "pdfplumber"
    )


# ================================================================
# DETECTAR PIKEPDF
# ================================================================
def detectar_pikepdf():

    return biblioteca_instalada(
        "pikepdf"
    )


# ================================================================
# DETECTAR PYTHON-DOCX
# ================================================================
def detectar_python_docx():

    return biblioteca_instalada(
        "docx"
    )


# ================================================================
# DETECTAR LXML
# ================================================================
def detectar_lxml():

    return biblioteca_instalada(
        "lxml"
    )


# ================================================================
# COMPROBAR COMPONENTE COM
# ================================================================
def componente_com_registrado(
    nombre
):

    if os.name != "nt":
        return False

    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CLASSES_ROOT,
            rf"{nombre}\CLSID"
        ):
            return True

    except OSError:
        return False


# ================================================================
# DETECTAR PYWIN32
# ================================================================
def detectar_pywin32():

    return biblioteca_instalada(
        "win32com.client"
    )


# ================================================================
# DETECTAR MICROSOFT WORD INSTALADO
# ================================================================
def detectar_microsoft_word_instalado():

    return componente_com_registrado(
        "Word.Application"
    )


# ================================================================
# DETECTAR MICROSOFT EXCEL INSTALADO
# ================================================================
def detectar_microsoft_excel_instalado():

    return componente_com_registrado(
        "Excel.Application"
    )


# ================================================================
# DETECTAR MICROSOFT POWERPOINT INSTALADO
# ================================================================
def detectar_microsoft_powerpoint_instalado():

    return componente_com_registrado(
        "PowerPoint.Application"
    )


# ================================================================
# DETECTAR MICROSOFT WORD
# ================================================================
def detectar_microsoft_word():

    return (
        detectar_pywin32()
        and detectar_microsoft_word_instalado()
    )


# ================================================================
# DETECTAR MICROSOFT EXCEL
# ================================================================
def detectar_microsoft_excel():

    return (
        detectar_pywin32()
        and detectar_microsoft_excel_instalado()
    )


# ================================================================
# DETECTAR MICROSOFT POWERPOINT
# ================================================================
def detectar_microsoft_powerpoint():

    return (
        detectar_pywin32()
        and detectar_microsoft_powerpoint_instalado()
    )


# ================================================================
# DETECTAR LIBREOFFICE ADMINISTRADO
# ================================================================
def detectar_libreoffice_administrado():

    carpeta_libreoffice = os.path.join(
        obtener_carpeta_motores(),
        "libreoffice",
        "program"
    )

    rutas = [
        os.path.join(
            carpeta_libreoffice,
            "soffice.com"
        ),
        os.path.join(
            carpeta_libreoffice,
            "soffice.exe"
        )
    ]

    for ruta in rutas:
        if os.path.isfile(
            ruta
        ):
            return ruta

    return None


# ================================================================
# DETECTAR LIBREOFFICE DEL SISTEMA
# ================================================================
def detectar_libreoffice_sistema():

    rutas_comunes = [
        r"C:\Program Files\LibreOffice\program\soffice.com",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.com",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    ]

    return buscar_ejecutable(
        [
            "soffice.com",
            "soffice.exe",
            "soffice"
        ],
        rutas_comunes
    )


# ================================================================
# DETECTAR LIBREOFFICE
# ================================================================
def detectar_libreoffice():

    ruta_administrada = detectar_libreoffice_administrado()

    if ruta_administrada:
        return ruta_administrada

    return detectar_libreoffice_sistema()


# ================================================================
# OBTENER ORIGEN DE LIBREOFFICE
# ================================================================
def obtener_origen_libreoffice():

    if detectar_libreoffice_administrado():
        return "administrado"

    if detectar_libreoffice_sistema():
        return "sistema"

    return None


# ================================================================
# DETECTAR IMAGEMAGICK ADMINISTRADO
# ================================================================
def detectar_imagemagick_administrado():

    ruta = os.path.join(
        obtener_carpeta_motores(),
        "imagemagick",
        "magick.exe"
    )

    if os.path.isfile(
        ruta
    ):
        return ruta

    return None


# ================================================================
# DETECTAR IMAGEMAGICK DEL SISTEMA
# ================================================================
def detectar_imagemagick_sistema():

    rutas_comunes = []

    carpetas_programas = [
        os.environ.get(
            "ProgramFiles"
        ),
        os.environ.get(
            "ProgramFiles(x86)"
        )
    ]

    for carpeta_programas in carpetas_programas:
        if not carpeta_programas:
            continue

        rutas_comunes.append(
            os.path.join(
                carpeta_programas,
                "ImageMagick",
                "magick.exe"
            )
        )

        rutas_versionadas = glob.glob(
            os.path.join(
                carpeta_programas,
                "ImageMagick-*",
                "magick.exe"
            )
        )

        rutas_versionadas.sort(
            reverse=True
        )

        rutas_comunes.extend(
            rutas_versionadas
        )

    return buscar_ejecutable(
        [
            "magick.exe",
            "magick"
        ],
        rutas_comunes
    )


# ================================================================
# DETECTAR IMAGEMAGICK
# ================================================================
def detectar_imagemagick():

    ruta_administrada = detectar_imagemagick_administrado()

    if ruta_administrada:
        return ruta_administrada

    return detectar_imagemagick_sistema()


# ================================================================
# OBTENER ORIGEN DE IMAGEMAGICK
# ================================================================
def obtener_origen_imagemagick():

    if detectar_imagemagick_administrado():
        return "administrado"

    if detectar_imagemagick_sistema():
        return "sistema"

    return None


# ================================================================
# DETECTAR PANDOC ADMINISTRADO
# ================================================================
def detectar_pandoc_administrado():

    ruta = os.path.join(
        obtener_carpeta_motores(),
        "pandoc",
        "pandoc.exe"
    )

    if os.path.isfile(
        ruta
    ):
        return ruta

    return None


# ================================================================
# DETECTAR PANDOC DEL SISTEMA
# ================================================================
def detectar_pandoc_sistema():

    rutas_comunes = []

    local_appdata = os.environ.get(
        "LOCALAPPDATA"
    )

    if local_appdata:
        rutas_comunes.append(
            os.path.join(
                local_appdata,
                "Pandoc",
                "pandoc.exe"
            )
        )

    program_files = os.environ.get(
        "ProgramFiles"
    )

    if program_files:
        rutas_comunes.append(
            os.path.join(
                program_files,
                "Pandoc",
                "pandoc.exe"
            )
        )

    program_files_x86 = os.environ.get(
        "ProgramFiles(x86)"
    )

    if program_files_x86:
        rutas_comunes.append(
            os.path.join(
                program_files_x86,
                "Pandoc",
                "pandoc.exe"
            )
        )

    appdata = os.environ.get(
        "APPDATA"
    )

    if appdata:
        rutas_comunes.append(
            os.path.join(
                appdata,
                "cabal",
                "bin",
                "pandoc.exe"
            )
        )

    return buscar_ejecutable(
        [
            "pandoc.exe",
            "pandoc"
        ],
        rutas_comunes
    )


# ================================================================
# DETECTAR PANDOC
# ================================================================
def detectar_pandoc():

    ruta_administrada = detectar_pandoc_administrado()

    if ruta_administrada:
        return ruta_administrada

    return detectar_pandoc_sistema()


# ================================================================
# OBTENER ORIGEN DE PANDOC
# ================================================================
def obtener_origen_pandoc():

    if detectar_pandoc_administrado():
        return "administrado"

    if detectar_pandoc_sistema():
        return "sistema"

    return None


# ================================================================
# DETECTAR 7-ZIP ADMINISTRADO
# ================================================================
def detectar_7zip_administrado():

    carpeta_7zip = os.path.join(
        obtener_carpeta_motores(),
        "7zip"
    )

    rutas = [
        os.path.join(
            carpeta_7zip,
            "7z.exe"
        ),
        os.path.join(
            carpeta_7zip,
            "7za.exe"
        ),
        os.path.join(
            carpeta_7zip,
            "7zz.exe"
        )
    ]

    for ruta in rutas:
        if os.path.isfile(
            ruta
        ):
            return ruta

    return None


# ================================================================
# DETECTAR 7-ZIP DEL SISTEMA
# ================================================================
def detectar_7zip_sistema():

    rutas_comunes = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe"
    ]

    return buscar_ejecutable(
        [
            "7z.exe",
            "7z",
            "7za.exe",
            "7za",
            "7zz.exe",
            "7zz"
        ],
        rutas_comunes
    )


# ================================================================
# DETECTAR 7-ZIP
# ================================================================
def detectar_7zip():

    ruta_administrada = detectar_7zip_administrado()

    if ruta_administrada:
        return ruta_administrada

    return detectar_7zip_sistema()


# ================================================================
# OBTENER ORIGEN DE 7-ZIP
# ================================================================
def obtener_origen_7zip():

    if detectar_7zip_administrado():
        return "administrado"

    if detectar_7zip_sistema():
        return "sistema"

    return None


# ================================================================
# DETECTAR WINRAR
# ================================================================
def detectar_winrar():

    rutas_comunes = [
        r"C:\Program Files\WinRAR\RAR.exe",
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files (x86)\WinRAR\RAR.exe",
        r"C:\Program Files (x86)\WinRAR\WinRAR.exe"
    ]

    return buscar_ejecutable(
        [
            "RAR.exe",
            "WinRAR.exe",
            "rar"
        ],
        rutas_comunes
    )


# ================================================================
# DETECTAR FFMPEG
# ================================================================
def detectar_ffmpeg():

    rutas_comunes = [
        os.path.join(
            obtener_carpeta_motores(),
            "ffmpeg",
            "ffmpeg.exe"
        )
    ]

    return buscar_ejecutable(
        [
            "ffmpeg.exe",
            "ffmpeg"
        ],
        rutas_comunes
    )


# ================================================================
# DETECTAR CAPACIDADES
# ================================================================
def detectar_capacidades():

    return {
        # Librerías Python
        "pillow": biblioteca_instalada(
            "PIL"
        ),
        "pypdfium2": detectar_pdfium(),
        "openpyxl": detectar_openpyxl(),
        "pywin32": detectar_pywin32(),
        "pdfplumber": detectar_pdfplumber(),
        "pikepdf": detectar_pikepdf(),
        "python_docx": detectar_python_docx(),
        "lxml": detectar_lxml(),

        # Microsoft Office
        "microsoft_word": detectar_microsoft_word(),
        "microsoft_excel": detectar_microsoft_excel(),
        "microsoft_powerpoint": detectar_microsoft_powerpoint(),

        # LibreOffice
        "libreoffice": detectar_libreoffice(),
        "libreoffice_administrado": detectar_libreoffice_administrado(),
        "libreoffice_sistema": detectar_libreoffice_sistema(),

        # ImageMagick
        "imagemagick": detectar_imagemagick(),
        "imagemagick_administrado": detectar_imagemagick_administrado(),
        "imagemagick_sistema": detectar_imagemagick_sistema(),

        # Pandoc
        "pandoc": detectar_pandoc(),
        "pandoc_administrado": detectar_pandoc_administrado(),
        "pandoc_sistema": detectar_pandoc_sistema(),

        # 7-Zip
        "7zip": detectar_7zip(),
        "7zip_administrado": detectar_7zip_administrado(),
        "7zip_sistema": detectar_7zip_sistema(),

        # Motores opcionales
        "winrar": detectar_winrar(),
        "ffmpeg": detectar_ffmpeg()
    }