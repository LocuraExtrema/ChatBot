import fitz  # PyMuPDF
import os

# =========================================================
# CONFIGURACIÓN DE LIBROS
# =========================================================

BIBLIOTECA = {
    "calculo1": "calculus-volume-1.pdf",
    "calculo2": "calculus-volume-2.pdf",
    "calculo3": "calculus-volume-3.pdf"
}

# =========================================================
# DICCIONARIO DE TRADUCCIONES
# (MUCHO MÁS RÁPIDO QUE USAR IA)
# =========================================================

TRADUCCIONES = {
    "derivadas": "derivatives",
    "integrales": "integrals",
    "integrales triples": "triple integrals",
    "limites": "limits",
    "funciones": "functions",
    "series": "series",
    "sucesiones": "sequences",
    "vectores": "vectors",
    "gradiente": "gradient",
    "stokes": "stokes",
    "ecuaciones diferenciales": "differential equations"
}

# =========================================================
# SELECCIÓN DEL LIBRO
# =========================================================

def seleccionar_libro(tema_limpio):

    tema = str(tema_limpio).lower().strip()

    tema = "".join(
        c for c in tema
        if c.isalnum() or c in ["_", " "]
    ).strip()

    print(f"[DEBUG] Tema procesado: '{tema}'")

    # -------------------------------------------------
    # CÁLCULO 3
    # -------------------------------------------------

    if any(w in tema for w in [
        "integracion multiple",
        "multiple",
        "triple",
        "multivariable",
        "parcial",
        "calculo vectorial",
        "vectores",
        "superficie",
        "gradiente",
        "stokes"
    ]):
        print("[MATCH] Cálculo 3")
        return BIBLIOTECA["calculo3"]

    # -------------------------------------------------
    # CÁLCULO 2
    # -------------------------------------------------

    elif any(w in tema for w in [
        "serie",
        "sucesion",
        "converg",
        "diverg",
        "potencias",
        "ecuacion diferencial",
        "tecnicas de integracion",
        "fracciones parciales",
        "por partes"
    ]):
        print("[MATCH] Cálculo 2")
        return BIBLIOTECA["calculo2"]

    # -------------------------------------------------
    # CÁLCULO 1
    # -------------------------------------------------

    elif any(w in tema for w in [
        "funciones",
        "limites",
        "derivadas",
        "recta tangente",
        "lhopital",
        "optimizacion",
        "integracion simple"
    ]):
        print("[MATCH] Cálculo 1")
        return BIBLIOTECA["calculo1"]

    # -------------------------------------------------
    # DEFAULT
    # -------------------------------------------------

    else:
        print("[MATCH] Default -> Cálculo 1")
        return BIBLIOTECA["calculo1"]

# =========================================================
# BÚSQUEDA EN PDF
# =========================================================

def buscar_en_pdf(tema_detectado):

    # ---------------------------------------------
    # SELECCIÓN DEL LIBRO
    # ---------------------------------------------

    libro_archivo = seleccionar_libro(tema_detectado)

    # ---------------------------------------------
    # TRADUCCIÓN RÁPIDA SIN OLLAMA
    # ---------------------------------------------

    query_en = TRADUCCIONES.get(
        tema_detectado.lower().strip(),
        tema_detectado.lower().strip()
    )

    print(f"[RAG] Libro: {libro_archivo}")
    print(f"[RAG] Query: {query_en}")

    # ---------------------------------------------
    # LIMPIEZA DE PALABRAS
    # ---------------------------------------------

    stop_words = [
        "the",
        "with",
        "from",
        "that",
        "this"
    ]

    palabras = [
        p for p in query_en.split()
        if len(p) > 3 and p not in stop_words
    ]

    if not palabras:
        print("[AVISO] No hay palabras clave.")
        return None

    # ---------------------------------------------
    # RUTA DEL PDF
    # ---------------------------------------------

    ruta_pdf = os.path.join(
        os.path.dirname(__file__),
        "books",
        libro_archivo
    )

    if not os.path.exists(ruta_pdf):
        print(f"[ERROR] No existe: {ruta_pdf}")
        return None

    # ---------------------------------------------
    # BÚSQUEDA
    # ---------------------------------------------

    try:

        doc = fitz.open(ruta_pdf)

        for pagina in doc:

            texto_pagina = pagina.get_text().lower()

            if all(p in texto_pagina for p in palabras):

                print(
                    f"[EXITO] Encontrado en "
                    f"{libro_archivo} "
                    f"página {pagina.number + 1}"
                )

                contenido = texto_pagina[:3000]

                doc.close()

                return contenido

        doc.close()

        print("[AVISO] No hubo coincidencias.")

    except Exception as e:
        print(f"[ERROR PDF] {e}")

    return None
