from interfaz.previsualizadores.visor_documento import VisorDocumento


# ================================================================
# VISOR DE PRESENTACIÓN
# ================================================================
class VisorPresentacion(VisorDocumento):

    # ============================================================
    # INICIALIZACIÓN
    # ============================================================
    def __init__(self):
        super().__init__(
            nombre_unidad="Diapositiva"
        )