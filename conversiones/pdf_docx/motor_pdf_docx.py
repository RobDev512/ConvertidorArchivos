import importlib.util
import json
import os
import sys
import tempfile
import threading
from pathlib import Path


# ================================================================
# CONSTANTES
# ================================================================
CARPETA_MOTOR = Path(
    __file__
).resolve().parent

MODULOS_PROTOTIPO = (
    "modelo_documento",
    "analizar_tabla",
    "extraer_recursos_pdf",
    "analizar_pdf",
    "analizar_distribucion",
    "analizar_efectos_pdf",
    "refinar_efectos_pdf",
    "generar_docx"
)

DEPENDENCIAS_IMPORTACION = {
    "pdfplumber": "pdfplumber",
    "pypdfium2": "pypdfium2",
    "Pillow": "PIL",
    "pikepdf": "pikepdf",
    "python-docx": "docx",
    "lxml": "lxml"
}

_MODULOS_CARGADOS = None

_BLOQUEO_CARGA = threading.Lock()

_BLOQUEO_CONVERSION = threading.Lock()


# ================================================================
# EXCEPCIÓN DE CANCELACIÓN
# ================================================================
class ConversionPDFDOCXCancelada(
    RuntimeError
):
    pass


# ================================================================
# INFORMAR PROGRESO
# ================================================================
def informar_progreso(
    callback,
    porcentaje,
    estado
):
    if not callback:
        return

    porcentaje = max(
        0,
        min(
            100,
            int(
                round(
                    porcentaje
                )
            )
        )
    )

    callback(
        porcentaje,
        estado
    )


# ================================================================
# COMPROBAR CANCELACIÓN
# ================================================================
def comprobar_cancelacion(
    callback
):
    if (
        callback
        and callback()
    ):
        raise ConversionPDFDOCXCancelada(
            "Conversión cancelada por el usuario."
        )


# ================================================================
# OBTENER DEPENDENCIAS FALTANTES
# ================================================================
def dependencias_pdf_docx_faltantes():
    faltantes = []

    for paquete, modulo in (
        DEPENDENCIAS_IMPORTACION.items()
    ):
        try:
            disponible = (
                importlib.util.find_spec(
                    modulo
                )
                is not None
            )

        except Exception:
            disponible = False

        if not disponible:
            faltantes.append(
                paquete
            )

    for nombre in MODULOS_PROTOTIPO:
        ruta = (
            CARPETA_MOTOR
            / f"{nombre}.py"
        )

        if not ruta.is_file():
            faltantes.append(
                f"archivo:{nombre}.py"
            )

    return faltantes


# ================================================================
# COMPROBAR MOTOR DISPONIBLE
# ================================================================
def motor_pdf_docx_disponible():
    return not (
        dependencias_pdf_docx_faltantes()
    )


# ================================================================
# CARGAR MÓDULO DEL PROTOTIPO
# ================================================================
def cargar_modulo_prototipo(
    nombre,
    alias_temporales
):
    ruta = (
        CARPETA_MOTOR
        / f"{nombre}.py"
    )

    nombre_interno = (
        f"_convertidor_pdf_docx_{nombre}"
    )

    especificacion = (
        importlib.util.spec_from_file_location(
            nombre_interno,
            ruta
        )
    )

    if (
        especificacion is None
        or especificacion.loader is None
    ):
        raise ImportError(
            f"No fue posible cargar {ruta.name}."
        )

    modulo = (
        importlib.util.module_from_spec(
            especificacion
        )
    )

    sys.modules[
        nombre_interno
    ] = modulo

    alias_temporales[
        nombre
    ] = sys.modules.get(
        nombre
    )

    sys.modules[
        nombre
    ] = modulo

    especificacion.loader.exec_module(
        modulo
    )

    return modulo


# ================================================================
# CARGAR MÓDULOS DEL MOTOR
# ================================================================
def cargar_modulos_motor():
    global _MODULOS_CARGADOS

    if _MODULOS_CARGADOS is not None:
        return _MODULOS_CARGADOS

    with _BLOQUEO_CARGA:
        if _MODULOS_CARGADOS is not None:
            return _MODULOS_CARGADOS

        faltantes = (
            dependencias_pdf_docx_faltantes()
        )

        if faltantes:
            raise RuntimeError(
                "Faltan componentes necesarios para el motor "
                "PDF → DOCX:\n\n"
                + "\n".join(
                    f"- {nombre}"
                    for nombre in faltantes
                )
            )

        alias_temporales = {}

        modulos = {}

        try:
            for nombre in MODULOS_PROTOTIPO:
                modulos[
                    nombre
                ] = cargar_modulo_prototipo(
                    nombre,
                    alias_temporales
                )

        finally:
            for nombre, anterior in (
                alias_temporales.items()
            ):
                if anterior is None:
                    sys.modules.pop(
                        nombre,
                        None
                    )

                else:
                    sys.modules[
                        nombre
                    ] = anterior

        _MODULOS_CARGADOS = modulos

    return _MODULOS_CARGADOS


# ================================================================
# GUARDAR JSON TEMPORAL
# ================================================================
def guardar_json(
    datos,
    ruta
):
    ruta = Path(
        ruta
    )

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2
        )


# ================================================================
# OBTENER CANTIDAD DE PÁGINAS
# ================================================================
def obtener_cantidad_paginas(
    ruta_pdf
):
    import pypdfium2 as pdfium

    documento = pdfium.PdfDocument(
        str(
            Path(
                ruta_pdf
            ).resolve()
        )
    )

    try:
        return len(
            documento
        )

    finally:
        documento.close()


# ================================================================
# ANALIZAR PDF BASE
# ================================================================
def ejecutar_analisis_pdf(
    modulos,
    ruta_pdf,
    total_paginas,
    callback_progreso,
    callback_cancelacion
):
    modulo = modulos[
        "analizar_pdf"
    ]

    modelo = modulos[
        "modelo_documento"
    ]

    contador = 0

    funcion_original = (
        modulo.extraer_palabras
    )

    def extraer_palabras_controlado(
        *args,
        **kwargs
    ):
        nonlocal contador

        comprobar_cancelacion(
            callback_cancelacion
        )

        contador += 1

        informar_progreso(
            callback_progreso,
            (
                3
                + contador
                / max(
                    1,
                    total_paginas
                )
                * 24
            ),
            (
                "Analizando estructura de la página "
                f"{contador} de {total_paginas}..."
            )
        )

        return funcion_original(
            *args,
            **kwargs
        )

    modulo.extraer_palabras = (
        extraer_palabras_controlado
    )

    try:
        documento = modulo.analizar_pdf(
            Path(
                ruta_pdf
            ).resolve()
        )

    finally:
        modulo.extraer_palabras = (
            funcion_original
        )

    comprobar_cancelacion(
        callback_cancelacion
    )

    return modelo.convertir_a_diccionario(
        documento
    )


# ================================================================
# EXTRAER FONDOS Y PATRONES
# ================================================================
def ejecutar_extraccion_fondos(
    ruta_pdf,
    carpeta_fondos,
    callback_progreso,
    callback_cancelacion
):
    from .extraer_fondos_pdf import (
        extraer_patrones_fondo
    )

    def progreso_pagina(
        actual,
        total
    ):
        informar_progreso(
            callback_progreso,
            (
                27
                + actual
                / max(
                    1,
                    total
                )
                * 5
            ),
            (
                f"Analizando fondos de la página "
                f"{actual} de {total}..."
            )
        )

    def comprobar_cancelacion_fondo():
        comprobar_cancelacion(
            callback_cancelacion
        )

        return False

    return extraer_patrones_fondo(
        ruta_pdf,
        carpeta_fondos,
        comprobar_cancelacion=(
            comprobar_cancelacion_fondo
        ),
        progreso=progreso_pagina
    )


# ================================================================
# ANALIZAR DISTRIBUCIÓN
# ================================================================
def ejecutar_analisis_distribucion(
    modulo,
    analisis,
    datos_patrones,
    carpeta_recursos,
    callback_progreso,
    callback_cancelacion
):
    paginas_originales = (
        analisis.get(
            "paginas",
            []
        )
    )

    total_paginas = len(
        paginas_originales
    )

    margenes = (
        modulo.inferir_margenes_documento(
            analisis
        )
    )

    fondo = (
        modulo.detectar_fondo_semantico(
            datos_patrones,
            total_paginas
        )
    )

    ruta_origen = Path(
        analisis.get(
            "ruta_origen",
            ""
        )
    )

    recursos_extraidos = {}

    comprobar_cancelacion(
        callback_cancelacion
    )

    informar_progreso(
        callback_progreso,
        33,
        (
            "Extrayendo imágenes y recursos "
            "gráficos del PDF..."
        )
    )

    if ruta_origen.is_file():
        try:
            recursos_extraidos = (
                modulo.extraer_imagenes_documento(
                    ruta_origen,
                    paginas_originales,
                    carpeta_recursos,
                    limpiar=True
                )
            )

        except ConversionPDFDOCXCancelada:
            raise

        except Exception:
            recursos_extraidos = {}

    paginas = []

    for indice, pagina in enumerate(
        paginas_originales,
        start=1
    ):
        comprobar_cancelacion(
            callback_cancelacion
        )

        informar_progreso(
            callback_progreso,
            (
                36
                + indice
                / max(
                    1,
                    total_paginas
                )
                * 14
            ),
            (
                "Reconstruyendo distribución de la página "
                f"{indice} de {total_paginas}..."
            )
        )

        paginas.append(
            modulo.analizar_pagina(
                pagina,
                margenes,
                recursos_extraidos
            )
        )

    return {
        "ruta_origen": analisis.get(
            "ruta_origen"
        ),
        "cantidad_paginas": len(
            paginas
        ),
        "margenes_documento": margenes,
        "fondo_documento": fondo,
        "encabezados_probables": (
            analisis.get(
                "encabezados_probables",
                []
            )
        ),
        "pies_probables": (
            analisis.get(
                "pies_probables",
                []
            )
        ),
        "carpeta_recursos_extraidos": str(
            Path(
                carpeta_recursos
            ).resolve()
        ),
        "paginas": paginas
    }


# ================================================================
# ANALIZAR EFECTOS VISUALES
# ================================================================
def ejecutar_analisis_efectos(
    modulo,
    ruta_pdf,
    distribucion,
    carpeta_diagnostico,
    callback_progreso,
    callback_cancelacion
):
    carpeta_diagnostico = Path(
        carpeta_diagnostico
    )

    carpeta_diagnostico.mkdir(
        parents=True,
        exist_ok=True
    )

    modulo.CARPETA_DIAGNOSTICO = (
        carpeta_diagnostico
    )

    paginas = modulo.obtener_paginas(
        distribucion
    )

    candidatos_por_pagina = []

    total_candidatos = 0

    for pagina in paginas:
        candidatos = (
            modulo.recolectar_candidatos(
                pagina
            )
        )

        candidatos_por_pagina.append(
            (
                pagina,
                candidatos
            )
        )

        total_candidatos += len(
            candidatos
        )

    documento = (
        modulo.pdfium.PdfDocument(
            str(
                Path(
                    ruta_pdf
                ).resolve()
            )
        )
    )

    resultados = []

    procesados = 0

    escala = (
        modulo.ESCALA_RENDER_PREDETERMINADA
    )

    try:
        for pagina, candidatos in (
            candidatos_por_pagina
        ):
            comprobar_cancelacion(
                callback_cancelacion
            )

            if not candidatos:
                continue

            numero_pagina = modulo.a_entero(
                pagina.get(
                    "numero"
                ),
                1
            )

            indice_pagina = (
                numero_pagina
                - 1
            )

            if (
                indice_pagina < 0
                or indice_pagina >= len(
                    documento
                )
            ):
                continue

            imagen_pagina = (
                modulo.renderizar_pagina(
                    documento,
                    indice_pagina,
                    escala
                )
            )

            try:
                for identificador, elemento in (
                    candidatos
                ):
                    comprobar_cancelacion(
                        callback_cancelacion
                    )

                    procesados += 1

                    informar_progreso(
                        callback_progreso,
                        (
                            50
                            + procesados
                            / max(
                                1,
                                total_candidatos
                            )
                            * 24
                        ),
                        (
                            "Analizando efectos visuales "
                            f"({procesados} de "
                            f"{total_candidatos})..."
                        )
                    )

                    try:
                        resultados.append(
                            modulo.analizar_candidato(
                                imagen_pagina,
                                escala,
                                pagina,
                                identificador,
                                elemento
                            )
                        )

                    except Exception as error:
                        resultados.append(
                            {
                                "id": identificador,
                                "pagina": numero_pagina,
                                "tipo": elemento.get(
                                    "tipo"
                                ),
                                "texto": elemento.get(
                                    "texto"
                                ),
                                "error": (
                                    f"{type(error).__name__}: "
                                    f"{error}"
                                )
                            }
                        )

            finally:
                try:
                    imagen_pagina.close()

                except Exception:
                    pass

    finally:
        documento.close()

    return {
        "pdf": str(
            Path(
                ruta_pdf
            ).resolve()
        ),
        "distribucion": "memoria",
        "escala_render": escala,
        "candidatos": resultados
    }


# ================================================================
# REFINAR EFECTOS
# ================================================================
def ejecutar_refinamiento_efectos(
    modulo,
    analisis_efectos,
    callback_progreso,
    callback_cancelacion
):
    candidatos = analisis_efectos.get(
        "candidatos",
        []
    )

    validos = [
        candidato
        for candidato in candidatos
        if not candidato.get(
            "error"
        )
    ]

    refinados = []

    total = len(
        validos
    )

    for indice, candidato in enumerate(
        validos,
        start=1
    ):
        comprobar_cancelacion(
            callback_cancelacion
        )

        informar_progreso(
            callback_progreso,
            (
                74
                + indice
                / max(
                    1,
                    total
                )
                * 7
            ),
            (
                "Refinando efectos detectados "
                f"({indice} de {total})..."
            )
        )

        try:
            refinados.append(
                modulo.refinar_candidato(
                    candidato
                )
            )

        except Exception:
            continue

    return {
        "pdf": analisis_efectos.get(
            "pdf"
        ),
        "analisis_origen": "memoria",
        "reglas": {
            "prioridad_color": (
                "PDF nativo; análisis visual sólo cuando "
                "el color nativo parece haber perdido "
                "un efecto gráfico."
            ),
            "degradado_variacion_minima": (
                modulo.VARIACION_MINIMA_DEGRADADO
            ),
            "reflejo_solape_horizontal_minimo": (
                modulo.SOLAPE_HORIZONTAL_REFLEJO_MINIMO
            ),
            "reflejo_relacion_ancho": [
                modulo.RELACION_ANCHO_REFLEJO_MINIMA,
                modulo.RELACION_ANCHO_REFLEJO_MAXIMA
            ],
            "reflejo_distancia_maxima_pt": (
                modulo.DISTANCIA_REFLEJO_MAXIMA_ABSOLUTA
            )
        },
        "candidatos": refinados
    }


# ================================================================
# GENERAR DOCX
# ================================================================
def ejecutar_generacion_docx(
    modulo,
    distribucion,
    efectos_refinados,
    ruta_salida,
    carpeta_trabajo,
    callback_progreso,
    callback_cancelacion
):
    paginas = distribucion.get(
        "paginas",
        []
    )

    if not paginas:
        raise RuntimeError(
            "No hay páginas para generar el DOCX."
        )

    modulo.CARPETA_SALIDA = Path(
        carpeta_trabajo
    )

    mapa_efectos = (
        modulo.construir_mapa_efectos(
            efectos_refinados
        )
    )

    mapa_espaciados = (
        modulo.construir_mapa_espaciados(
            {}
        )
    )

    margenes_word = (
        modulo.inferir_margenes_word(
            distribucion
        )
    )

    ruta_textura = (
        modulo.obtener_textura_fondo(
            distribucion
        )
    )

    estadisticas = {
        "efectos_aplicados": 0,
        "text_fill_aplicados": 0,
        "reflejos_aplicados": 0,
        "espaciados_refinados_aplicados": 0
    }

    documento = modulo.Document()

    modulo.configurar_documento(
        documento,
        distribucion,
        margenes_word
    )

    modulo.configurar_encabezado_pie(
        documento,
        distribucion,
        margenes_word,
        mapa_efectos,
        ruta_textura,
        estadisticas
    )

    ancho_pagina = modulo.numero(
        paginas[
            0
        ].get(
            "ancho"
        ),
        612.0
    )

    total_paginas = len(
        paginas
    )

    for indice, pagina in enumerate(
        paginas,
        start=1
    ):
        comprobar_cancelacion(
            callback_cancelacion
        )

        informar_progreso(
            callback_progreso,
            (
                82
                + indice
                / max(
                    1,
                    total_paginas
                )
                * 16
            ),
            (
                f"Construyendo página {indice} "
                f"de {total_paginas} en Word..."
            )
        )

        numero_pagina = int(
            modulo.numero(
                pagina.get(
                    "numero"
                ),
                indice
            )
        )

        modulo.agregar_pagina(
            documento,
            pagina,
            margenes_word,
            numero_pagina,
            mapa_efectos,
            mapa_espaciados,
            ancho_pagina,
            estadisticas
        )

    comprobar_cancelacion(
        callback_cancelacion
    )

    informar_progreso(
        callback_progreso,
        99,
        "Guardando documento DOCX..."
    )

    documento.save(
        str(
            ruta_salida
        )
    )

    return ruta_salida


# ================================================================
# CONVERTIR PDF A DOCX
# ================================================================
def convertir_pdf_a_docx(
    ruta_entrada,
    ruta_salida,
    progreso=None,
    comprobar_cancelacion_callback=None
):
    ruta_entrada = Path(
        ruta_entrada
    ).resolve()

    ruta_salida = Path(
        ruta_salida
    ).resolve()

    if not ruta_entrada.is_file():
        raise FileNotFoundError(
            (
                "No existe el PDF de entrada: "
                f"{ruta_entrada}"
            )
        )

    if ruta_entrada.suffix.lower() != ".pdf":
        raise ValueError(
            (
                "El motor PDF → DOCX sólo "
                "acepta archivos PDF."
            )
        )

    faltantes = (
        dependencias_pdf_docx_faltantes()
    )

    if faltantes:
        raise RuntimeError(
            "El motor PDF → DOCX no está disponible. "
            "Faltan los siguientes componentes:\n\n"
            + "\n".join(
                f"- {nombre}"
                for nombre in faltantes
            )
        )

    ruta_salida.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if ruta_salida.exists():
        os.remove(
            ruta_salida
        )

    with _BLOQUEO_CONVERSION:
        comprobar_cancelacion(
            comprobar_cancelacion_callback
        )

        modulos = cargar_modulos_motor()

        total_paginas = (
            obtener_cantidad_paginas(
                ruta_entrada
            )
        )

        if total_paginas <= 0:
            raise RuntimeError(
                "El PDF no contiene páginas."
            )

        informar_progreso(
            progreso,
            1,
            "Preparando análisis del PDF..."
        )

        with tempfile.TemporaryDirectory(
            prefix="convertidor_pdf_docx_"
        ) as carpeta_temporal:
            carpeta_temporal = Path(
                carpeta_temporal
            )

            ruta_analisis = (
                carpeta_temporal
                / "analisis_pdf.json"
            )

            ruta_distribucion = (
                carpeta_temporal
                / "distribucion_pdf.json"
            )

            ruta_efectos = (
                carpeta_temporal
                / "analisis_efectos_pdf.json"
            )

            ruta_efectos_refinados = (
                carpeta_temporal
                / "analisis_efectos_pdf_refinado.json"
            )

            carpeta_fondos = (
                carpeta_temporal
                / "recursos_fondo"
            )

            carpeta_recursos = (
                carpeta_temporal
                / "recursos_paginas"
            )

            carpeta_diagnostico = (
                carpeta_temporal
                / "diagnostico_efectos"
            )

            analisis = ejecutar_analisis_pdf(
                modulos,
                ruta_entrada,
                total_paginas,
                progreso,
                comprobar_cancelacion_callback
            )

            guardar_json(
                analisis,
                ruta_analisis
            )

            comprobar_cancelacion(
                comprobar_cancelacion_callback
            )

            datos_patrones = (
                ejecutar_extraccion_fondos(
                    ruta_entrada,
                    carpeta_fondos,
                    progreso,
                    comprobar_cancelacion_callback
                )
            )

            distribucion = (
                ejecutar_analisis_distribucion(
                    modulos[
                        "analizar_distribucion"
                    ],
                    analisis,
                    datos_patrones,
                    carpeta_recursos,
                    progreso,
                    comprobar_cancelacion_callback
                )
            )

            guardar_json(
                distribucion,
                ruta_distribucion
            )

            efectos = (
                ejecutar_analisis_efectos(
                    modulos[
                        "analizar_efectos_pdf"
                    ],
                    ruta_entrada,
                    distribucion,
                    carpeta_diagnostico,
                    progreso,
                    comprobar_cancelacion_callback
                )
            )

            guardar_json(
                efectos,
                ruta_efectos
            )

            efectos_refinados = (
                ejecutar_refinamiento_efectos(
                    modulos[
                        "refinar_efectos_pdf"
                    ],
                    efectos,
                    progreso,
                    comprobar_cancelacion_callback
                )
            )

            guardar_json(
                efectos_refinados,
                ruta_efectos_refinados
            )

            ejecutar_generacion_docx(
                modulos[
                    "generar_docx"
                ],
                distribucion,
                efectos_refinados,
                ruta_salida,
                carpeta_temporal,
                progreso,
                comprobar_cancelacion_callback
            )

        if not ruta_salida.is_file():
            raise RuntimeError(
                (
                    "El motor terminó sin generar "
                    "el archivo DOCX."
                )
            )

        if (
            ruta_salida.stat().st_size
            <= 0
        ):
            raise RuntimeError(
                (
                    "El motor generó un archivo "
                    "DOCX vacío."
                )
            )

        informar_progreso(
            progreso,
            100,
            (
                "Documento DOCX convertido "
                "correctamente."
            )
        )

        return str(
            ruta_salida
        )