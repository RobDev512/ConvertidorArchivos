import os
import shutil
import tempfile

from pypdf import (
    PdfReader,
    PdfWriter
)


# ================================================================
# SEPARAR PDF POR CORTES
# ================================================================
def separar_pdf_por_cortes(
    ruta_pdf,
    cortes,
    carpeta_salida,
    prefijo=None,
    progreso=None,
    comprobar_cancelacion=None,
    sobrescribir=False
):

    # ----------------------------------- #
    #          Preparar PDF               #
    # ----------------------------------- #

    ruta_pdf = validar_ruta_pdf(
        ruta_pdf
    )

    carpeta_salida = preparar_carpeta_salida(
        carpeta_salida
    )


    # ----------------------------------- #
    #            Abrir PDF                #
    # ----------------------------------- #

    with open(
        ruta_pdf,
        "rb"
    ) as archivo_pdf:

        lector = crear_lector_pdf(
            archivo_pdf,
            ruta_pdf
        )

        cantidad_paginas = len(
            lector.pages
        )


        # ----------------------------------- #
        #          Validar cortes             #
        # ----------------------------------- #

        cortes = validar_cortes(
            cortes,
            cantidad_paginas
        )


        # ----------------------------------- #
        #       Convertir cortes a grupos     #
        # ----------------------------------- #

        grupos = crear_grupos_desde_cortes(
            cantidad_paginas,
            cortes
        )


        return separar_pdf_en_grupos(
            ruta_pdf,
            grupos,
            carpeta_salida,
            prefijo=prefijo,
            progreso=progreso,
            comprobar_cancelacion=comprobar_cancelacion,
            sobrescribir=sobrescribir,
            lector=lector
        )


# ================================================================
# SEPARAR CADA PÁGINA
# ================================================================
def separar_pdf_por_paginas(
    ruta_pdf,
    carpeta_salida,
    prefijo=None,
    progreso=None,
    comprobar_cancelacion=None,
    sobrescribir=False
):

    # ----------------------------------- #
    #          Preparar PDF               #
    # ----------------------------------- #

    ruta_pdf = validar_ruta_pdf(
        ruta_pdf
    )

    carpeta_salida = preparar_carpeta_salida(
        carpeta_salida
    )


    # ----------------------------------- #
    #            Abrir PDF                #
    # ----------------------------------- #

    with open(
        ruta_pdf,
        "rb"
    ) as archivo_pdf:

        lector = crear_lector_pdf(
            archivo_pdf,
            ruta_pdf
        )

        cantidad_paginas = len(
            lector.pages
        )


        # ----------------------------------- #
        #        Grupo por cada página        #
        # ----------------------------------- #

        grupos = [
            [
                indice
            ]
            for indice in range(
                cantidad_paginas
            )
        ]


        return separar_pdf_en_grupos(
            ruta_pdf,
            grupos,
            carpeta_salida,
            prefijo=prefijo,
            progreso=progreso,
            comprobar_cancelacion=comprobar_cancelacion,
            sobrescribir=sobrescribir,
            lector=lector
        )


# ================================================================
# SEPARAR PDF POR BLOQUES
# ================================================================
def separar_pdf_por_bloques(
    ruta_pdf,
    paginas_por_archivo,
    carpeta_salida,
    prefijo=None,
    progreso=None,
    comprobar_cancelacion=None,
    sobrescribir=False
):

    # ----------------------------------- #
    #       Validar tamaño de bloque      #
    # ----------------------------------- #

    if (
        not isinstance(
            paginas_por_archivo,
            int
        )
        or paginas_por_archivo <= 0
    ):

        raise ValueError(
            "La cantidad de páginas por archivo "
            "debe ser mayor que cero."
        )


    # ----------------------------------- #
    #          Preparar PDF               #
    # ----------------------------------- #

    ruta_pdf = validar_ruta_pdf(
        ruta_pdf
    )

    carpeta_salida = preparar_carpeta_salida(
        carpeta_salida
    )


    # ----------------------------------- #
    #            Abrir PDF                #
    # ----------------------------------- #

    with open(
        ruta_pdf,
        "rb"
    ) as archivo_pdf:

        lector = crear_lector_pdf(
            archivo_pdf,
            ruta_pdf
        )

        cantidad_paginas = len(
            lector.pages
        )


        # ----------------------------------- #
        #           Crear grupos              #
        # ----------------------------------- #

        grupos = []


        for inicio in range(
            0,
            cantidad_paginas,
            paginas_por_archivo
        ):

            fin = min(
                inicio + paginas_por_archivo,
                cantidad_paginas
            )

            grupo = list(
                range(
                    inicio,
                    fin
                )
            )

            grupos.append(
                grupo
            )


        return separar_pdf_en_grupos(
            ruta_pdf,
            grupos,
            carpeta_salida,
            prefijo=prefijo,
            progreso=progreso,
            comprobar_cancelacion=comprobar_cancelacion,
            sobrescribir=sobrescribir,
            lector=lector
        )


# ================================================================
# SEPARAR PDF EN GRUPOS
# ================================================================
def separar_pdf_en_grupos(
    ruta_pdf,
    grupos,
    carpeta_salida,
    prefijo=None,
    progreso=None,
    comprobar_cancelacion=None,
    sobrescribir=False,
    lector=None
):

    ruta_pdf = validar_ruta_pdf(
        ruta_pdf
    )

    carpeta_salida = preparar_carpeta_salida(
        carpeta_salida
    )


    # ----------------------------------- #
    #       Abrir lector si hace falta    #
    # ----------------------------------- #

    archivo_pdf = None


    try:

        if lector is None:

            archivo_pdf = open(
                ruta_pdf,
                "rb"
            )

            lector = crear_lector_pdf(
                archivo_pdf,
                ruta_pdf
            )


        cantidad_paginas = len(
            lector.pages
        )


        # ----------------------------------- #
        #           Validar grupos            #
        # ----------------------------------- #

        grupos = validar_grupos(
            grupos,
            cantidad_paginas
        )


        # ----------------------------------- #
        #             Prefijo                 #
        # ----------------------------------- #

        if not prefijo:

            prefijo = os.path.splitext(
                os.path.basename(
                    ruta_pdf
                )
            )[
                0
            ]


        prefijo = limpiar_prefijo(
            prefijo
        )


        # ----------------------------------- #
        #        Preparar nombres             #
        # ----------------------------------- #

        salidas = crear_rutas_salida(
            grupos,
            carpeta_salida,
            prefijo
        )


        # ----------------------------------- #
        #       Comprobar conflictos          #
        # ----------------------------------- #

        if not sobrescribir:

            conflictos = [
                ruta
                for ruta in salidas
                if os.path.exists(
                    ruta
                )
            ]


            if conflictos:

                raise FileExistsError(
                    "Ya existe uno de los archivos "
                    "que se generaría:\n\n"
                    f"{conflictos[0]}"
                )


        # ----------------------------------- #
        #         Carpeta temporal            #
        # ----------------------------------- #

        carpeta_temporal = tempfile.mkdtemp(
            prefix=".separar_pdf_",
            dir=carpeta_salida
        )


        rutas_temporales = []


        try:

            cantidad_grupos = len(
                grupos
            )


            # ================================================ #
            # CREAR CADA PDF
            # ================================================ #

            for indice_grupo, grupo in enumerate(
                grupos,
                start=1
            ):

                # ----------------------------------- #
                #           Cancelación               #
                # ----------------------------------- #

                if (
                    comprobar_cancelacion is not None
                    and comprobar_cancelacion()
                ):

                    raise RuntimeError(
                        "La división del PDF fue cancelada."
                    )


                # ----------------------------------- #
                #            Escritor                 #
                # ----------------------------------- #

                escritor = PdfWriter()


                try:

                    for indice_pagina in grupo:

                        if (
                            comprobar_cancelacion is not None
                            and comprobar_cancelacion()
                        ):

                            raise RuntimeError(
                                "La división del PDF fue cancelada."
                            )


                        escritor.add_page(
                            lector.pages[
                                indice_pagina
                            ]
                        )


                    # ----------------------------------- #
                    #          Ruta temporal             #
                    # ----------------------------------- #

                    nombre_salida = os.path.basename(
                        salidas[
                            indice_grupo - 1
                        ]
                    )

                    ruta_temporal = os.path.join(
                        carpeta_temporal,
                        nombre_salida
                    )


                    # ----------------------------------- #
                    #            Guardar                  #
                    # ----------------------------------- #

                    with open(
                        ruta_temporal,
                        "wb"
                    ) as archivo_salida:

                        escritor.write(
                            archivo_salida
                        )


                    rutas_temporales.append(
                        ruta_temporal
                    )


                finally:

                    try:

                        escritor.close()

                    except Exception:

                        pass


                # ----------------------------------- #
                #             Progreso                #
                # ----------------------------------- #

                if progreso is not None:

                    progreso(
                        indice_grupo,
                        cantidad_grupos,
                        grupo[
                            0
                        ] + 1,
                        grupo[
                            -1
                        ] + 1
                    )


            # ================================================ #
            # MOVER RESULTADOS A DESTINO
            # ================================================ #

            for ruta_temporal, ruta_final in zip(
                rutas_temporales,
                salidas
            ):

                if (
                    os.path.exists(
                        ruta_final
                    )
                    and not sobrescribir
                ):

                    raise FileExistsError(
                        "El archivo ya existe:\n"
                        f"{ruta_final}"
                    )


                os.replace(
                    ruta_temporal,
                    ruta_final
                )


        finally:

            shutil.rmtree(
                carpeta_temporal,
                ignore_errors=True
            )


        return salidas


    finally:

        if archivo_pdf is not None:

            archivo_pdf.close()


# ================================================================
# VALIDAR RUTA PDF
# ================================================================
def validar_ruta_pdf(
    ruta_pdf
):

    if not ruta_pdf:

        raise ValueError(
            "No se indicó un archivo PDF."
        )


    ruta_pdf = os.path.abspath(
        os.path.normpath(
            ruta_pdf
        )
    )


    if not os.path.isfile(
        ruta_pdf
    ):

        raise FileNotFoundError(
            f"No se encontró el archivo:\n{ruta_pdf}"
        )


    if not ruta_pdf.lower().endswith(
        ".pdf"
    ):

        raise ValueError(
            "El archivo seleccionado no es un PDF."
        )


    return ruta_pdf


# ================================================================
# PREPARAR CARPETA DE SALIDA
# ================================================================
def preparar_carpeta_salida(
    carpeta_salida
):

    if not carpeta_salida:

        raise ValueError(
            "No se indicó una carpeta de salida."
        )


    carpeta_salida = os.path.abspath(
        os.path.normpath(
            carpeta_salida
        )
    )


    os.makedirs(
        carpeta_salida,
        exist_ok=True
    )


    if not os.path.isdir(
        carpeta_salida
    ):

        raise ValueError(
            "La carpeta de salida no es válida."
        )


    return carpeta_salida


# ================================================================
# CREAR LECTOR PDF
# ================================================================
def crear_lector_pdf(
    archivo_pdf,
    ruta_pdf
):

    try:

        lector = PdfReader(
            archivo_pdf
        )


        # ----------------------------------- #
        #          PDF protegido              #
        # ----------------------------------- #

        if lector.is_encrypted:

            resultado = lector.decrypt(
                ""
            )


            if not resultado:

                raise ValueError(
                    "El PDF está protegido con contraseña:\n"
                    f"{ruta_pdf}"
                )


        # ----------------------------------- #
        #         Forzar lectura              #
        # ----------------------------------- #

        cantidad_paginas = len(
            lector.pages
        )


        if cantidad_paginas <= 0:

            raise ValueError(
                "El PDF no contiene páginas."
            )


        return lector


    except ValueError:

        raise


    except Exception as error:

        raise ValueError(
            "No se pudo leer el archivo PDF:\n"
            f"{ruta_pdf}\n\n"
            f"{error}"
        ) from error


# ================================================================
# VALIDAR CORTES
# ================================================================
def validar_cortes(
    cortes,
    cantidad_paginas
):

    if cortes is None:

        cortes = []


    cortes_validos = []


    for corte in cortes:

        if not isinstance(
            corte,
            int
        ):

            raise ValueError(
                "Los puntos de corte deben ser números enteros."
            )


        # ----------------------------------- #
        # Corte = después de esa página       #
        # ----------------------------------- #

        if (
            corte <= 0
            or corte >= cantidad_paginas
        ):

            raise ValueError(
                "Un punto de corte debe encontrarse "
                "entre la primera y la penúltima página."
            )


        cortes_validos.append(
            corte
        )


    return sorted(
        set(
            cortes_validos
        )
    )


# ================================================================
# CREAR GRUPOS DESDE CORTES
# ================================================================
def crear_grupos_desde_cortes(
    cantidad_paginas,
    cortes
):

    grupos = []

    inicio = 0


    for corte in cortes:

        fin = corte


        grupos.append(
            list(
                range(
                    inicio,
                    fin
                )
            )
        )


        inicio = fin


    # ----------------------------------- #
    #            Último grupo             #
    # ----------------------------------- #

    grupos.append(
        list(
            range(
                inicio,
                cantidad_paginas
            )
        )
    )


    return grupos


# ================================================================
# VALIDAR GRUPOS
# ================================================================
def validar_grupos(
    grupos,
    cantidad_paginas
):

    if not grupos:

        raise ValueError(
            "No hay grupos de páginas para separar."
        )


    grupos_validos = []


    for grupo in grupos:

        if not grupo:

            raise ValueError(
                "Un grupo de páginas no puede estar vacío."
            )


        grupo_valido = []


        for indice_pagina in grupo:

            if not isinstance(
                indice_pagina,
                int
            ):

                raise ValueError(
                    "El índice de página no es válido."
                )


            if (
                indice_pagina < 0
                or indice_pagina >= cantidad_paginas
            ):

                raise ValueError(
                    "Una de las páginas indicadas no existe."
                )


            grupo_valido.append(
                indice_pagina
            )


        grupos_validos.append(
            grupo_valido
        )


    return grupos_validos


# ================================================================
# CREAR RUTAS DE SALIDA
# ================================================================
def crear_rutas_salida(
    grupos,
    carpeta_salida,
    prefijo
):

    rutas = []

    cantidad_grupos = len(
        grupos
    )

    digitos = max(
        2,
        len(
            str(
                cantidad_grupos
            )
        )
    )


    for indice_grupo, grupo in enumerate(
        grupos,
        start=1
    ):

        primera_pagina = (
            grupo[
                0
            ]
            + 1
        )

        ultima_pagina = (
            grupo[
                -1
            ]
            + 1
        )


        # ----------------------------------- #
        #       Nombre según páginas          #
        # ----------------------------------- #

        if primera_pagina == ultima_pagina:

            paginas_texto = (
                f"pagina_{primera_pagina}"
            )


        else:

            paginas_texto = (
                f"paginas_"
                f"{primera_pagina}-"
                f"{ultima_pagina}"
            )


        nombre = (
            f"{prefijo}_"
            f"{indice_grupo:0{digitos}d}_"
            f"{paginas_texto}.pdf"
        )


        rutas.append(
            os.path.join(
                carpeta_salida,
                nombre
            )
        )


    return rutas


# ================================================================
# LIMPIAR PREFIJO
# ================================================================
def limpiar_prefijo(
    prefijo
):

    prefijo = str(
        prefijo
    ).strip()


    if not prefijo:

        return "PDF_dividido"


    caracteres_invalidos = (
        '<>:"/\\|?*'
    )


    for caracter in caracteres_invalidos:

        prefijo = prefijo.replace(
            caracter,
            "_"
        )


    prefijo = prefijo.rstrip(
        ". "
    )


    if not prefijo:

        return "PDF_dividido"


    return prefijo