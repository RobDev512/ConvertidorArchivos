import os
import tempfile

from pypdf import PdfReader, PdfWriter


# ================================================================
# VALIDAR PDF
# ================================================================
def _validar_pdf(
    ruta_pdf
):

    if not ruta_pdf:

        raise ValueError(
            "No se indicó ningún archivo PDF."
        )

    ruta_pdf = os.path.abspath(
        ruta_pdf
    )

    if not os.path.isfile(
        ruta_pdf
    ):

        raise FileNotFoundError(
            "El archivo PDF no existe."
        )

    if (
        os.path.splitext(
            ruta_pdf
        )[1].lower()
        != ".pdf"
    ):

        raise ValueError(
            "El archivo seleccionado no es un PDF."
        )

    return ruta_pdf


# ================================================================
# ABRIR LECTOR PDF
# ================================================================
def _abrir_lector_pdf(
    ruta_pdf
):

    lector = PdfReader(
        ruta_pdf
    )

    if lector.is_encrypted:

        try:

            resultado = lector.decrypt(
                ""
            )

        except Exception:

            resultado = 0

        if not resultado:

            raise RuntimeError(
                "El PDF está protegido con contraseña."
            )

    return lector


# ================================================================
# COMPROBAR CANCELACIÓN
# ================================================================
def _comprobar_cancelacion(
    comprobar_cancelacion
):

    if (
        comprobar_cancelacion is not None
        and comprobar_cancelacion()
    ):

        return True

    return False


# ================================================================
# INFORMAR PROGRESO
# ================================================================
def _informar_progreso(
    progreso,
    valor
):

    if progreso is None:
        return

    progreso(
        max(
            0,
            min(
                100,
                int(valor)
            )
        )
    )


# ================================================================
# VALIDAR ORDEN DE PÁGINAS
# ================================================================
def _validar_orden_paginas(
    orden_paginas,
    cantidad_paginas
):

    if not isinstance(
        orden_paginas,
        (
            list,
            tuple
        )
    ):

        raise ValueError(
            "El orden de páginas no es válido."
        )

    if len(
        orden_paginas
    ) != cantidad_paginas:

        raise ValueError(
            "El orden debe contener todas las páginas del PDF."
        )

    orden_normalizado = []

    for indice_pagina in orden_paginas:

        try:

            indice_pagina = int(
                indice_pagina
            )

        except Exception:

            raise ValueError(
                "El orden contiene una página no válida."
            )

        if (
            indice_pagina < 0
            or indice_pagina >= cantidad_paginas
        ):

            raise ValueError(
                "El orden contiene una página fuera del documento."
            )

        orden_normalizado.append(
            indice_pagina
        )

    if len(
        set(
            orden_normalizado
        )
    ) != cantidad_paginas:

        raise ValueError(
            "El orden contiene páginas repetidas."
        )

    if set(
        orden_normalizado
    ) != set(
        range(
            cantidad_paginas
        )
    ):

        raise ValueError(
            "El orden debe contener exactamente todas las páginas."
        )

    return orden_normalizado


# ================================================================
# CREAR RUTA TEMPORAL
# ================================================================
def _crear_ruta_temporal(
    ruta_salida
):

    carpeta_salida = os.path.dirname(
        os.path.abspath(
            ruta_salida
        )
    )

    os.makedirs(
        carpeta_salida,
        exist_ok=True
    )

    descriptor, ruta_temporal = tempfile.mkstemp(
        prefix=".reordenar_pdf_",
        suffix=".pdf",
        dir=carpeta_salida
    )

    os.close(
        descriptor
    )

    return ruta_temporal


# ================================================================
# REORDENAR PÁGINAS PDF
# ================================================================
def reordenar_paginas_pdf(
    ruta_pdf,
    orden_paginas,
    ruta_salida,
    progreso=None,
    comprobar_cancelacion=None
):

    ruta_pdf = _validar_pdf(
        ruta_pdf
    )

    if not ruta_salida:

        raise ValueError(
            "No se indicó una ruta de salida."
        )

    ruta_salida = os.path.abspath(
        ruta_salida
    )

    if (
        os.path.splitext(
            ruta_salida
        )[1].lower()
        != ".pdf"
    ):

        ruta_salida += ".pdf"

    lector = _abrir_lector_pdf(
        ruta_pdf
    )

    cantidad_paginas = len(
        lector.pages
    )

    if cantidad_paginas <= 0:

        raise RuntimeError(
            "El PDF no contiene páginas."
        )

    orden_paginas = _validar_orden_paginas(
        orden_paginas,
        cantidad_paginas
    )

    if _comprobar_cancelacion(
        comprobar_cancelacion
    ):

        return None

    _informar_progreso(
        progreso,
        0
    )

    escritor = PdfWriter()

    for posicion, indice_pagina in enumerate(
        orden_paginas,
        start=1
    ):

        if _comprobar_cancelacion(
            comprobar_cancelacion
        ):

            return None

        escritor.add_page(
            lector.pages[
                indice_pagina
            ]
        )

        _informar_progreso(
            progreso,
            (
                posicion
                / cantidad_paginas
            )
            * 90
        )

    ruta_temporal = _crear_ruta_temporal(
        ruta_salida
    )

    try:

        if _comprobar_cancelacion(
            comprobar_cancelacion
        ):

            return None

        with open(
            ruta_temporal,
            "wb"
        ) as archivo_salida:

            escritor.write(
                archivo_salida
            )

        if _comprobar_cancelacion(
            comprobar_cancelacion
        ):

            return None

        _informar_progreso(
            progreso,
            95
        )

        os.replace(
            ruta_temporal,
            ruta_salida
        )

        ruta_temporal = None

        _informar_progreso(
            progreso,
            100
        )

        return ruta_salida

    finally:

        if (
            ruta_temporal
            and os.path.isfile(
                ruta_temporal
            )
        ):

            try:

                os.remove(
                    ruta_temporal
                )

            except OSError:
                pass