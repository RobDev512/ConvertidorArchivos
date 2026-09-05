from dataclasses import (
    asdict,
    dataclass,
    field
)

from typing import (
    Any
)


# ================================================================
# CAJA DE POSICIÓN
# ================================================================
@dataclass
class Caja:

    x0: float
    top: float
    x1: float
    bottom: float


    # ============================================================
    # ANCHO
    # ============================================================
    @property
    def ancho(
        self
    ):

        return max(
            0.0,
            self.x1
            - self.x0
        )


    # ============================================================
    # ALTO
    # ============================================================
    @property
    def alto(
        self
    ):

        return max(
            0.0,
            self.bottom
            - self.top
        )


# ================================================================
# FRAGMENTO DE TEXTO PDF
# ================================================================
@dataclass
class FragmentoTextoPDF:

    texto: str

    caja: Caja

    fuente: str = ""

    tamano: float = 0.0

    color: Any = None

    negrita: bool = False

    cursiva: bool = False


# ================================================================
# PALABRA PDF
# ================================================================
@dataclass
class PalabraPDF:

    texto: str

    caja: Caja

    fuente: str = ""

    tamano: float = 0.0

    color: Any = None

    negrita: bool = False

    cursiva: bool = False

    fragmentos: list[
        FragmentoTextoPDF
    ] = field(
        default_factory=list
    )


# ================================================================
# LÍNEA DE TEXTO PDF
# ================================================================
@dataclass
class LineaTextoPDF:

    texto: str

    caja: Caja

    fuente_predominante: str = ""

    tamano_promedio: float = 0.0

    color_predominante: Any = None

    negrita_predominante: bool = False

    cursiva_predominante: bool = False

    alineacion_estimada: str = "izquierda"

    zona: str = "cuerpo"

    palabras: list[
        PalabraPDF
    ] = field(
        default_factory=list
    )


# ================================================================
# IMAGEN PDF
# ================================================================
@dataclass
class ImagenPDF:

    caja: Caja

    nombre: str = ""

    ancho_pixeles: int | None = None

    alto_pixeles: int | None = None

    bits: int | None = None

    espacio_color: Any = None


# ================================================================
# LÍNEA VECTORIAL PDF
# ================================================================
@dataclass
class LineaVectorialPDF:

    caja: Caja

    grosor: float = 0.0

    color: Any = None

    patron_trazo: Any = None


# ================================================================
# RECTÁNGULO PDF
# ================================================================
@dataclass
class RectanguloPDF:

    caja: Caja

    color_trazo: Any = None

    color_relleno: Any = None

    relleno: bool = False


# ================================================================
# MÁRGENES DE PÁGINA
# ================================================================
@dataclass
class MargenesPaginaPDF:

    izquierdo: float = 0.0

    derecho: float = 0.0

    superior: float = 0.0

    inferior: float = 0.0

    confianza_lateral: str = "baja"

    confianza_vertical: str = "baja"


# ================================================================
# DISTANCIAS DE ENCABEZADO Y PIE
# ================================================================
@dataclass
class DistanciasEncabezadoPiePDF:

    encabezado_desde_borde_superior: float | None = None

    pie_desde_borde_inferior: float | None = None


# ================================================================
# LADO DE BORDE DE PÁGINA
# ================================================================
@dataclass
class LadoBordePDF:

    presente: bool = False

    posicion: float | None = None

    separacion_borde: float | None = None

    grosor: float | None = None

    color: Any = None

    estilo: str = "desconocido"

    patron_trazo: Any = None

    longitud: float | None = None


# ================================================================
# BORDE DE PÁGINA
# ================================================================
@dataclass
class BordePaginaPDF:

    superior: LadoBordePDF = field(
        default_factory=LadoBordePDF
    )

    derecho: LadoBordePDF = field(
        default_factory=LadoBordePDF
    )

    inferior: LadoBordePDF = field(
        default_factory=LadoBordePDF
    )

    izquierdo: LadoBordePDF = field(
        default_factory=LadoBordePDF
    )


# ================================================================
# FONDO DE PÁGINA
# ================================================================
@dataclass
class FondoPaginaPDF:

    detectado: bool = False

    tipo: str = "ninguno"

    recurso_pdf: Any = None

    color: Any = None

    caja: Caja | None = None

    cubre_pagina: bool = False

    cobertura: float = 0.0


# ================================================================
# PÁGINA PDF
# ================================================================
@dataclass
class PaginaPDF:

    numero: int

    ancho: float

    alto: float

    rotacion: int = 0

    palabras: list[
        PalabraPDF
    ] = field(
        default_factory=list
    )

    lineas_texto: list[
        LineaTextoPDF
    ] = field(
        default_factory=list
    )

    imagenes: list[
        ImagenPDF
    ] = field(
        default_factory=list
    )

    lineas_vectoriales: list[
        LineaVectorialPDF
    ] = field(
        default_factory=list
    )

    rectangulos: list[
        RectanguloPDF
    ] = field(
        default_factory=list
    )

    margenes: MargenesPaginaPDF = field(
        default_factory=MargenesPaginaPDF
    )

    distancias_encabezado_pie: (
        DistanciasEncabezadoPiePDF
    ) = field(
        default_factory=DistanciasEncabezadoPiePDF
    )

    borde_pagina: BordePaginaPDF = field(
        default_factory=BordePaginaPDF
    )

    fondo_pagina: FondoPaginaPDF = field(
        default_factory=FondoPaginaPDF
    )


# ================================================================
# DOCUMENTO PDF
# ================================================================
@dataclass
class DocumentoPDF:

    ruta_origen: str

    paginas: list[
        PaginaPDF
    ] = field(
        default_factory=list
    )

    encabezados_probables: list[
        dict
    ] = field(
        default_factory=list
    )

    pies_probables: list[
        dict
    ] = field(
        default_factory=list
    )

    margenes_globales: MargenesPaginaPDF = field(
        default_factory=MargenesPaginaPDF
    )

    fondo_repetido: dict = field(
        default_factory=dict
    )


# ================================================================
# CONVERTIR A DICCIONARIO
# ================================================================
def convertir_a_diccionario(
    objeto
):

    return asdict(
        objeto
    )