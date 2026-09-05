import json
import math

from pathlib import Path


# ================================================================
# RUTAS
# ================================================================

CARPETA_BASE = Path(
    __file__
).resolve().parent

CARPETA_SALIDA = (
    CARPETA_BASE
    / "salida"
)

RUTA_ANALISIS = (
    CARPETA_SALIDA
    / "analisis_efectos_pdf.json"
)

RUTA_REFINADO = (
    CARPETA_SALIDA
    / "analisis_efectos_pdf_refinado.json"
)

RUTA_RESUMEN = (
    CARPETA_SALIDA
    / "resumen_efectos_pdf_refinado.txt"
)


# ================================================================
# CONFIGURACIÓN
# ================================================================

PIXELES_VISUALES_MINIMOS = 80

SATURACION_VISUAL_MINIMA = 55.0

DISTANCIA_COLOR_MINIMA = 55.0

VARIACION_MINIMA_DEGRADADO = 35.0

SOLAPE_HORIZONTAL_REFLEJO_MINIMO = 0.75

RELACION_ANCHO_REFLEJO_MINIMA = 0.72

RELACION_ANCHO_REFLEJO_MAXIMA = 1.30

ALPHA_REFLEJO_MAXIMO = 220

DISTANCIA_REFLEJO_MAXIMA_ABSOLUTA = 8.0


# ================================================================
# UTILIDADES
# ================================================================

def numero(
    valor,
    predeterminado=0.0
):
    try:
        return float(
            valor
        )

    except (
        TypeError,
        ValueError
    ):
        return float(
            predeterminado
        )


# ================================================================
# LIMITAR
# ================================================================

def limitar(
    valor,
    minimo,
    maximo
):
    return max(
        minimo,
        min(
            maximo,
            valor
        )
    )


# ================================================================
# RGB A HEX
# ================================================================

def rgb_a_hex(
    rgb
):
    if rgb is None:
        return None

    if len(
        rgb
    ) < 3:
        return None

    return "#{:02X}{:02X}{:02X}".format(
        int(
            limitar(
                round(
                    rgb[0]
                ),
                0,
                255
            )
        ),
        int(
            limitar(
                round(
                    rgb[1]
                ),
                0,
                255
            )
        ),
        int(
            limitar(
                round(
                    rgb[2]
                ),
                0,
                255
            )
        )
    )


# ================================================================
# DISTANCIA RGB
# ================================================================

def distancia_rgb(
    color_a,
    color_b
):
    if (
        color_a is None
        or color_b is None
    ):
        return 0.0

    return math.sqrt(
        (
            color_a[0]
            - color_b[0]
        ) ** 2
        + (
            color_a[1]
            - color_b[1]
        ) ** 2
        + (
            color_a[2]
            - color_b[2]
        ) ** 2
    )


# ================================================================
# SATURACIÓN APROXIMADA
# ================================================================

def saturacion_rgb(
    rgb
):
    if rgb is None:
        return 0.0

    mayor = max(
        rgb
    )

    menor = min(
        rgb
    )

    if mayor <= 0:
        return 0.0

    return (
        (
            mayor
            - menor
        )
        / mayor
    ) * 255.0


# ================================================================
# LUMINANCIA
# ================================================================

def luminancia_rgb(
    rgb
):
    if rgb is None:
        return 0.0

    return (
        0.2126
        * rgb[0]
        + 0.7152
        * rgb[1]
        + 0.0722
        * rgb[2]
    )


# ================================================================
# NORMALIZAR COLOR NATIVO DEL PDF
# ================================================================

def color_pdf_a_rgb(
    color
):
    if not isinstance(
        color,
        (
            list,
            tuple
        )
    ):
        return None

    if not color:
        return None

    try:
        if len(
            color
        ) == 1:
            gris = int(
                limitar(
                    round(
                        float(
                            color[0]
                        )
                        * 255.0
                    ),
                    0,
                    255
                )
            )

            return [
                gris,
                gris,
                gris
            ]

        if len(
            color
        ) >= 3:
            return [
                int(
                    limitar(
                        round(
                            float(
                                color[indice]
                            )
                            * 255.0
                        ),
                        0,
                        255
                    )
                )
                for indice
                in range(
                    3
                )
            ]

    except (
        TypeError,
        ValueError
    ):
        return None

    return None


# ================================================================
# NORMALIZAR CAJA
# ================================================================

def normalizar_caja(
    caja
):
    if not isinstance(
        caja,
        dict
    ):
        return None

    x0 = numero(
        caja.get(
            "x0"
        )
    )

    top = numero(
        caja.get(
            "top",
            caja.get(
                "y0"
            )
        )
    )

    x1 = numero(
        caja.get(
            "x1"
        )
    )

    bottom = numero(
        caja.get(
            "bottom",
            caja.get(
                "y1"
            )
        )
    )

    if (
        x1 <= x0
        or bottom <= top
    ):
        return None

    return {
        "x0": x0,
        "top": top,
        "x1": x1,
        "bottom": bottom,
        "ancho": (
            x1
            - x0
        ),
        "alto": (
            bottom
            - top
        ),
        "centro_x": (
            x0
            + x1
        ) / 2.0,
        "centro_y": (
            top
            + bottom
        ) / 2.0
    }


# ================================================================
# COLOR VISUAL VÁLIDO
# ================================================================

def color_visual_valido(
    candidato
):
    visual = candidato.get(
        "analisis_visual",
        {}
    )

    color = visual.get(
        "color_principal_rgb"
    )

    cantidad = int(
        numero(
            visual.get(
                "cantidad_pixeles_foreground"
            )
        )
    )

    if (
        not isinstance(
            color,
            list
        )
        or len(
            color
        ) < 3
    ):
        return False

    if (
        cantidad
        < PIXELES_VISUALES_MINIMOS
    ):
        return False

    return True


# ================================================================
# COLOR NATIVO SOSPECHOSO
# ================================================================

def color_nativo_sospechoso(
    color_nativo,
    color_visual
):
    if (
        color_nativo is None
        or color_visual is None
    ):
        return False

    saturacion_nativa = (
        saturacion_rgb(
            color_nativo
        )
    )

    luminancia_nativa = (
        luminancia_rgb(
            color_nativo
        )
    )

    saturacion_visual = (
        saturacion_rgb(
            color_visual
        )
    )

    diferencia = distancia_rgb(
        color_nativo,
        color_visual
    )

    nativo_negro_o_gris = (
        saturacion_nativa
        <= 18.0
        and luminancia_nativa
        <= 90.0
    )

    visual_coloreado = (
        saturacion_visual
        >= SATURACION_VISUAL_MINIMA
    )

    cambio_importante = (
        diferencia
        >= DISTANCIA_COLOR_MINIMA
    )

    return (
        nativo_negro_o_gris
        and visual_coloreado
        and cambio_importante
    )


# ================================================================
# ELEGIR COLOR FINAL
# ================================================================

def elegir_color_final(
    candidato
):
    estilo = candidato.get(
        "estilo_pdf_extraido",
        {}
    )

    color_nativo = color_pdf_a_rgb(
        estilo.get(
            "color"
        )
    )

    visual = candidato.get(
        "analisis_visual",
        {}
    )

    color_visual = (
        visual.get(
            "color_principal_rgb"
        )
        if color_visual_valido(
            candidato
        )
        else None
    )

    if color_nativo is None:
        if color_visual is not None:
            return {
                "origen": (
                    "analisis_visual"
                ),
                "rgb": color_visual,
                "hex": rgb_a_hex(
                    color_visual
                ),
                "motivo": (
                    "El PDF no proporcionó "
                    "un color nativo utilizable."
                )
            }

        return {
            "origen": (
                "desconocido"
            ),
            "rgb": None,
            "hex": None,
            "motivo": (
                "No se obtuvo un color "
                "nativo ni visual fiable."
            )
        }

    if (
        color_visual is not None
        and color_nativo_sospechoso(
            color_nativo,
            color_visual
        )
    ):
        return {
            "origen": (
                "analisis_visual"
            ),
            "rgb": color_visual,
            "hex": rgb_a_hex(
                color_visual
            ),
            "motivo": (
                "El PDF declaró negro/gris, "
                "pero el render muestra un "
                "color saturado claramente distinto."
            )
        }

    return {
        "origen": (
            "pdf_nativo"
        ),
        "rgb": color_nativo,
        "hex": rgb_a_hex(
            color_nativo
        ),
        "motivo": (
            "El color nativo del PDF "
            "se considera fiable."
        )
    }


# ================================================================
# REFINAR RELLENO
# ================================================================

def refinar_relleno(
    candidato,
    color_final
):
    visual = candidato.get(
        "analisis_visual",
        {}
    )

    variacion = numero(
        visual.get(
            "variacion_rgb_maxima"
        )
    )

    es_degradado_visual = bool(
        visual.get(
            "degradado_probable"
        )
    )

    color_visual = visual.get(
        "color_principal_rgb"
    )

    saturacion_visual = (
        saturacion_rgb(
            color_visual
        )
        if color_visual
        else 0.0
    )

    visual_fiable = (
        color_visual_valido(
            candidato
        )
    )

    if (
        visual_fiable
        and es_degradado_visual
        and variacion
        >= VARIACION_MINIMA_DEGRADADO
        and saturacion_visual
        >= SATURACION_VISUAL_MINIMA
    ):
        return {
            "tipo": (
                "degradado"
            ),
            "direccion": (
                visual.get(
                    "direccion_degradado"
                )
                or "vertical"
            ),
            "stops": (
                visual.get(
                    "stops_sugeridos",
                    []
                )
            ),
            "variacion_rgb": (
                round(
                    variacion,
                    3
                )
            ),
            "confianza": (
                "alta"
                if variacion
                >= 60.0
                else "media"
            )
        }

    return {
        "tipo": (
            "solido"
        ),
        "color": (
            color_final
        ),
        "variacion_rgb": (
            round(
                variacion,
                3
            )
        ),
        "confianza": (
            "alta"
            if color_final.get(
                "rgb"
            )
            is not None
            else "baja"
        )
    }


# ================================================================
# VALIDAR REFLEJO
# ================================================================

def validar_reflejo(
    candidato,
    asociacion
):
    caja_texto = normalizar_caja(
        candidato.get(
            "caja"
        )
    )

    caja_imagen = normalizar_caja(
        asociacion.get(
            "caja_imagen"
        )
    )

    if (
        caja_texto is None
        or caja_imagen is None
    ):
        return None

    solape_horizontal = numero(
        asociacion.get(
            "solape_horizontal"
        )
    )

    solape_vertical = numero(
        asociacion.get(
            "solape_vertical"
        )
    )

    distancia_vertical = numero(
        asociacion.get(
            "distancia_vertical_pt"
        ),
        9999.0
    )

    if (
        caja_texto["ancho"]
        <= 0.0
    ):
        return None

    relacion_ancho = (
        caja_imagen["ancho"]
        / caja_texto["ancho"]
    )

    imagen_debajo = (
        caja_imagen["centro_y"]
        > caja_texto["centro_y"]
        and caja_imagen["bottom"]
        > caja_texto["bottom"]
    )

    limite_distancia_relativo = min(
        DISTANCIA_REFLEJO_MAXIMA_ABSOLUTA,
        max(
            2.0,
            caja_texto["alto"]
            * 0.22
        )
    )

    contacto_vertical = (
        solape_vertical
        > 0.0
        or distancia_vertical
        <= limite_distancia_relativo
    )

    analisis_imagen = asociacion.get(
        "analisis_imagen",
        {}
    )

    tiene_alpha = bool(
        analisis_imagen.get(
            "tiene_alpha"
        )
    )

    alpha_min = analisis_imagen.get(
        "alpha_min"
    )

    alpha_max = analisis_imagen.get(
        "alpha_max"
    )

    transparencia_compatible = False

    if tiene_alpha:
        if (
            alpha_min is not None
            and alpha_max is not None
        ):
            transparencia_compatible = (
                numero(
                    alpha_min
                )
                <= 10.0
                and numero(
                    alpha_max
                )
                <= ALPHA_REFLEJO_MAXIMO
            )

    ancho_compatible = (
        RELACION_ANCHO_REFLEJO_MINIMA
        <= relacion_ancho
        <= RELACION_ANCHO_REFLEJO_MAXIMA
    )

    horizontal_compatible = (
        solape_horizontal
        >= SOLAPE_HORIZONTAL_REFLEJO_MINIMO
    )

    valido = all(
        (
            imagen_debajo,
            contacto_vertical,
            ancho_compatible,
            horizontal_compatible,
            transparencia_compatible
        )
    )

    if not valido:
        return None

    puntuacion = 0.0

    puntuacion += min(
        1.0,
        solape_horizontal
    ) * 0.30

    puntuacion += (
        1.0
        - min(
            1.0,
            abs(
                1.0
                - relacion_ancho
            )
        )
    ) * 0.25

    if solape_vertical > 0.0:
        puntuacion += 0.25

    else:
        puntuacion += (
            1.0
            - min(
                1.0,
                (
                    distancia_vertical
                    / max(
                        0.1,
                        limite_distancia_relativo
                    )
                )
            )
        ) * 0.25

    if transparencia_compatible:
        puntuacion += 0.20

    return {
        "nombre": (
            asociacion.get(
                "nombre"
            )
        ),
        "archivo_extraido": (
            asociacion.get(
                "archivo_extraido"
            )
        ),
        "rol_original": (
            asociacion.get(
                "rol_estimado"
            )
        ),
        "caja": (
            asociacion.get(
                "caja_imagen"
            )
        ),
        "solape_horizontal": (
            round(
                solape_horizontal,
                4
            )
        ),
        "solape_vertical": (
            round(
                solape_vertical,
                4
            )
        ),
        "distancia_vertical_pt": (
            round(
                distancia_vertical,
                3
            )
        ),
        "relacion_ancho": (
            round(
                relacion_ancho,
                4
            )
        ),
        "alpha_min": (
            alpha_min
        ),
        "alpha_max": (
            alpha_max
        ),
        "puntuacion": (
            round(
                puntuacion,
                4
            )
        ),
        "confianza": (
            "alta"
            if puntuacion >= 0.80
            else "media"
        )
    }


# ================================================================
# REFINAR REFLEJO
# ================================================================

def refinar_reflejo(
    candidato
):
    reflejos_validos = []

    for asociacion in candidato.get(
        "imagenes_asociadas",
        []
    ):
        resultado = validar_reflejo(
            candidato,
            asociacion
        )

        if resultado is not None:
            reflejos_validos.append(
                resultado
            )

    reflejos_validos.sort(
        key=lambda item: (
            item.get(
                "puntuacion",
                0.0
            )
        ),
        reverse=True
    )

    if not reflejos_validos:
        return {
            "presente": False,
            "confianza": (
                "alta"
            ),
            "imagen": None,
            "alternativas_validas": []
        }

    principal = reflejos_validos[
        0
    ]

    return {
        "presente": True,
        "confianza": (
            principal.get(
                "confianza",
                "media"
            )
        ),
        "imagen": principal,
        "alternativas_validas": (
            reflejos_validos[
                1:
            ]
        )
    }


# ================================================================
# REFINAR CANDIDATO
# ================================================================

def refinar_candidato(
    candidato
):
    color_final = elegir_color_final(
        candidato
    )

    relleno = refinar_relleno(
        candidato,
        color_final
    )

    reflejo = refinar_reflejo(
        candidato
    )

    tiene_efecto = (
        relleno.get(
            "tipo"
        )
        == "degradado"
        or reflejo.get(
            "presente",
            False
        )
    )

    if (
        relleno.get(
            "tipo"
        )
        == "degradado"
        and reflejo.get(
            "presente"
        )
    ):
        confianza_general = (
            "alta"
        )

    elif (
        relleno.get(
            "tipo"
        )
        == "degradado"
        or reflejo.get(
            "presente"
        )
    ):
        confianza_general = (
            "media"
        )

    else:
        confianza_general = (
            "alta"
        )

    return {
        "pagina": (
            candidato.get(
                "pagina"
            )
        ),
        "id": (
            candidato.get(
                "id"
            )
        ),
        "tipo": (
            candidato.get(
                "tipo"
            )
        ),
        "texto": (
            candidato.get(
                "texto"
            )
        ),
        "caja": (
            candidato.get(
                "caja"
            )
        ),
        "estilo_pdf_extraido": (
            candidato.get(
                "estilo_pdf_extraido"
            )
        ),
        "color_final": (
            color_final
        ),
        "relleno_final": (
            relleno
        ),
        "reflejo_final": (
            reflejo
        ),
        "tiene_efecto_avanzado": (
            tiene_efecto
        ),
        "confianza_general": (
            confianza_general
        ),
        "diagnostico_original": (
            candidato.get(
                "diagnostico"
            )
        )
    }


# ================================================================
# GUARDAR RESUMEN
# ================================================================

def guardar_resumen(
    datos
):
    lineas = [
        "PROTOTIPO PDF → DOCX",
        "REFINAMIENTO DE EFECTOS DEL PDF",
        "=" * 88,
        "",
        (
            "Candidatos: "
            f"{len(datos['candidatos'])}"
        ),
        ""
    ]

    for candidato in datos[
        "candidatos"
    ]:
        lineas.append(
            "-" * 88
        )

        lineas.append(
            (
                "Página "
                f"{candidato.get('pagina')} | "
                f"{candidato.get('id')} | "
                f"{candidato.get('tipo')}"
            )
        )

        lineas.append(
            (
                "Texto: "
                f"{candidato.get('texto')}"
            )
        )

        color = candidato.get(
            "color_final",
            {}
        )

        lineas.append(
            (
                "Color final: "
                f"{color.get('hex')} "
                f"{color.get('rgb')} | "
                f"origen={color.get('origen')}"
            )
        )

        lineas.append(
            (
                "Motivo color: "
                f"{color.get('motivo')}"
            )
        )

        relleno = candidato.get(
            "relleno_final",
            {}
        )

        lineas.append(
            (
                "Relleno: "
                f"{relleno.get('tipo')} | "
                f"confianza="
                f"{relleno.get('confianza')}"
            )
        )

        if (
            relleno.get(
                "tipo"
            )
            == "degradado"
        ):
            lineas.append(
                (
                    "  Dirección: "
                    f"{relleno.get('direccion')}"
                )
            )

            lineas.append(
                (
                    "  Stops: "
                    f"{relleno.get('stops')}"
                )
            )

        reflejo = candidato.get(
            "reflejo_final",
            {}
        )

        lineas.append(
            (
                "Reflejo: "
                f"{reflejo.get('presente')} | "
                f"confianza="
                f"{reflejo.get('confianza')}"
            )
        )

        imagen = reflejo.get(
            "imagen"
        )

        if imagen:
            lineas.append(
                (
                    "  Imagen: "
                    f"{imagen.get('nombre')}"
                )
            )

            lineas.append(
                (
                    "  Relación ancho: "
                    f"{imagen.get('relacion_ancho')}"
                )
            )

            lineas.append(
                (
                    "  Solape H/V: "
                    f"{imagen.get('solape_horizontal')} / "
                    f"{imagen.get('solape_vertical')}"
                )
            )

            lineas.append(
                (
                    "  Distancia vertical: "
                    f"{imagen.get('distancia_vertical_pt')} pt"
                )
            )

            lineas.append(
                (
                    "  Alpha: "
                    f"{imagen.get('alpha_min')} - "
                    f"{imagen.get('alpha_max')}"
                )
            )

            lineas.append(
                (
                    "  Puntuación: "
                    f"{imagen.get('puntuacion')}"
                )
            )

        lineas.append(
            (
                "Efecto avanzado: "
                f"{candidato.get('tiene_efecto_avanzado')}"
            )
        )

        lineas.append(
            ""
        )

    RUTA_RESUMEN.write_text(
        "\n".join(
            lineas
        ),
        encoding="utf-8"
    )


# ================================================================
# EJECUCIÓN PRINCIPAL
# ================================================================

def main():
    if not RUTA_ANALISIS.is_file():
        raise FileNotFoundError(
            (
                "No existe el análisis de efectos: "
                f"{RUTA_ANALISIS}"
            )
        )

    with open(
        RUTA_ANALISIS,
        "r",
        encoding="utf-8"
    ) as archivo:
        analisis = json.load(
            archivo
        )

    candidatos_originales = analisis.get(
        "candidatos",
        []
    )

    refinados = []

    for candidato in candidatos_originales:
        if candidato.get(
            "error"
        ):
            continue

        refinados.append(
            refinar_candidato(
                candidato
            )
        )

    salida = {
        "pdf": (
            analisis.get(
                "pdf"
            )
        ),
        "analisis_origen": (
            str(
                RUTA_ANALISIS
            )
        ),
        "reglas": {
            "prioridad_color": (
                "PDF nativo; análisis visual sólo "
                "cuando el color nativo parece haber "
                "perdido un efecto gráfico."
            ),
            "degradado_variacion_minima": (
                VARIACION_MINIMA_DEGRADADO
            ),
            "reflejo_solape_horizontal_minimo": (
                SOLAPE_HORIZONTAL_REFLEJO_MINIMO
            ),
            "reflejo_relacion_ancho": [
                RELACION_ANCHO_REFLEJO_MINIMA,
                RELACION_ANCHO_REFLEJO_MAXIMA
            ],
            "reflejo_distancia_maxima_pt": (
                DISTANCIA_REFLEJO_MAXIMA_ABSOLUTA
            )
        },
        "candidatos": refinados
    }

    with open(
        RUTA_REFINADO,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            salida,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    guardar_resumen(
        salida
    )

    print()

    print(
        "Refinamiento de efectos terminado."
    )

    print()

    print(
        (
            "JSON: "
            f"{RUTA_REFINADO}"
        )
    )

    print(
        (
            "Resumen: "
            f"{RUTA_RESUMEN}"
        )
    )

    print()

    especiales = [
        candidato
        for candidato
        in refinados
        if candidato.get(
            "tiene_efecto_avanzado"
        )
    ]

    print(
        (
            "Elementos con efecto avanzado "
            "confirmado/probable: "
            f"{len(especiales)}"
        )
    )

    print()

    for candidato in especiales:
        relleno = candidato.get(
            "relleno_final",
            {}
        )

        reflejo = candidato.get(
            "reflejo_final",
            {}
        )

        imagen = reflejo.get(
            "imagen"
        )

        print(
            (
                f"Página {candidato.get('pagina')}: "
                f"{candidato.get('texto')}"
            )
        )

        print(
            (
                "  Relleno: "
                f"{relleno.get('tipo')}"
            )
        )

        print(
            (
                "  Reflejo: "
                f"{reflejo.get('presente')}"
                + (
                    (
                        " | "
                        f"{imagen.get('nombre')}"
                    )
                    if imagen
                    else ""
                )
            )
        )

        print()


if __name__ == "__main__":
    main()