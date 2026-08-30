import os


# ----------------------------------- #
#      Formatos de Microsoft Word     #
# ----------------------------------- #

FORMATOS_WORD = {
    "DOC": 0,
    "RTF": 6,
    "TXT": 7,
    "HTML": 8,
    "DOCX": 16,
    "ODT": 23
}


# ----------------------------------- #
#     Formatos de Microsoft Excel     #
# ----------------------------------- #

FORMATOS_EXCEL = {
    "HTML": 44,
    "XLSB": 50,
    "XLSX": 51,
    "XLSM": 52,
    "XLS": 56,
    "ODS": 60
}


# ----------------------------------- #
#   Formatos de Microsoft PowerPoint  #
# ----------------------------------- #

FORMATOS_POWERPOINT = {
    "PPT": 1,
    "PPTX": 24,
    "PPTM": 25,
    "PPSX": 28,
    "PPSM": 29,
    "PDF": 32,
    "ODP": 35
}


# ================================================================
# CARGAR PYWIN32
# ================================================================
def cargar_pywin32():

    try:
        import pythoncom
        from win32com.client import DispatchEx

        return pythoncom, DispatchEx

    except ImportError as error:
        raise RuntimeError(
            "No se encontró pywin32.\n\n"
            "Instálalo con:\n"
            "python -m pip install pywin32"
        ) from error


# ================================================================
# CONVERTIR CON MICROSOFT WORD
# ================================================================
def convertir_con_word(ruta_origen, ruta_destino, formato_destino):

    # Cargar componentes COM
    pythoncom, DispatchEx = cargar_pywin32()

    formato_destino = formato_destino.upper()

    # Comprobar formato
    if formato_destino != "PDF" and formato_destino not in FORMATOS_WORD:
        raise ValueError(
            f"Microsoft Word no tiene configurada la salida {formato_destino}."
        )

    # Normalizar rutas
    ruta_origen = os.path.abspath(ruta_origen)
    ruta_destino = os.path.abspath(ruta_destino)

    aplicacion = None
    documento = None

    # Cada hilo debe inicializar COM
    pythoncom.CoInitialize()

    try:

        # Crear una instancia independiente de Word
        aplicacion = DispatchEx("Word.Application")
        aplicacion.Visible = False
        aplicacion.DisplayAlerts = 0

        # Evitar ejecución automática de macros cuando sea posible
        try:
            aplicacion.AutomationSecurity = 3
        except Exception:
            pass

        # Abrir documento como solo lectura
        documento = aplicacion.Documents.Open(
            ruta_origen,
            False,
            True,
            False
        )

        # Exportar a PDF
        if formato_destino == "PDF":
            documento.ExportAsFixedFormat(ruta_destino, 17)

        # Guardar en otro formato
        else:
            documento.SaveAs2(
                ruta_destino,
                FORMATOS_WORD[formato_destino]
            )

    except Exception as error:
        raise RuntimeError(
            f"Microsoft Word no pudo realizar la conversión.\n\n{error}"
        ) from error

    finally:

        # Cerrar documento
        if documento is not None:
            try:
                documento.Close(False)
            except Exception:
                pass

        # Cerrar Word
        if aplicacion is not None:
            try:
                aplicacion.Quit()
            except Exception:
                pass

        # Liberar COM
        pythoncom.CoUninitialize()

    return ruta_destino


# ================================================================
# CONVERTIR CON MICROSOFT EXCEL
# ================================================================
def convertir_con_excel(ruta_origen, ruta_destino, formato_destino):

    # Cargar componentes COM
    pythoncom, DispatchEx = cargar_pywin32()

    formato_destino = formato_destino.upper()

    # Comprobar formato
    if formato_destino != "PDF" and formato_destino not in FORMATOS_EXCEL:
        raise ValueError(
            f"Microsoft Excel no tiene configurada la salida {formato_destino}."
        )

    # Normalizar rutas
    ruta_origen = os.path.abspath(ruta_origen)
    ruta_destino = os.path.abspath(ruta_destino)

    aplicacion = None
    libro = None

    # Cada hilo debe inicializar COM
    pythoncom.CoInitialize()

    try:

        # Crear una instancia independiente de Excel
        aplicacion = DispatchEx("Excel.Application")
        aplicacion.Visible = False
        aplicacion.DisplayAlerts = False

        # Evitar ejecución automática de macros cuando sea posible
        try:
            aplicacion.AutomationSecurity = 3
        except Exception:
            pass

        # Abrir libro como solo lectura
        libro = aplicacion.Workbooks.Open(
            ruta_origen,
            0,
            True
        )

        # Exportar libro completo a PDF
        if formato_destino == "PDF":
            libro.ExportAsFixedFormat(0, ruta_destino)

        # Guardar en otro formato
        else:
            libro.SaveAs(
                ruta_destino,
                FORMATOS_EXCEL[formato_destino]
            )

    except Exception as error:
        raise RuntimeError(
            f"Microsoft Excel no pudo realizar la conversión.\n\n{error}"
        ) from error

    finally:

        # Cerrar libro
        if libro is not None:
            try:
                libro.Close(False)
            except Exception:
                pass

        # Cerrar Excel
        if aplicacion is not None:
            try:
                aplicacion.Quit()
            except Exception:
                pass

        # Liberar COM
        pythoncom.CoUninitialize()

    return ruta_destino


# ================================================================
# CONVERTIR CON MICROSOFT POWERPOINT
# ================================================================
def convertir_con_powerpoint(ruta_origen, ruta_destino, formato_destino):

    # Cargar componentes COM
    pythoncom, DispatchEx = cargar_pywin32()

    formato_destino = formato_destino.upper()

    # Comprobar formato
    if formato_destino not in FORMATOS_POWERPOINT:
        raise ValueError(
            f"Microsoft PowerPoint no tiene configurada la salida {formato_destino}."
        )

    # Normalizar rutas
    ruta_origen = os.path.abspath(ruta_origen)
    ruta_destino = os.path.abspath(ruta_destino)

    aplicacion = None
    presentacion = None

    # Cada hilo debe inicializar COM
    pythoncom.CoInitialize()

    try:

        # Crear una instancia independiente de PowerPoint
        aplicacion = DispatchEx("PowerPoint.Application")
        aplicacion.DisplayAlerts = 1

        # Evitar ejecución automática de macros cuando sea posible
        try:
            aplicacion.AutomationSecurity = 3
        except Exception:
            pass

        # Abrir presentación sin mostrar ventana
        presentacion = aplicacion.Presentations.Open(
            ruta_origen,
            True,
            False,
            False
        )

        # Guardar en el formato solicitado
        presentacion.SaveAs(
            ruta_destino,
            FORMATOS_POWERPOINT[formato_destino]
        )

    except Exception as error:
        raise RuntimeError(
            f"Microsoft PowerPoint no pudo realizar la conversión.\n\n{error}"
        ) from error

    finally:

        # Cerrar presentación
        if presentacion is not None:
            try:
                presentacion.Close()
            except Exception:
                pass

        # Cerrar PowerPoint
        if aplicacion is not None:
            try:
                aplicacion.Quit()
            except Exception:
                pass

        # Liberar COM
        pythoncom.CoUninitialize()

    return ruta_destino