import fitz  # PyMuPDF
import pickle
import os

BIBLIOTECA = {
    "calculo1": "calculus-volume-1.pdf", 
    "calculo2": "calculus-volume-2.pdf", 
    "calculo3": "calculus-volume-3.pdf"
}

# 🌟 DICCIONARIO MATEMÁTICO ESTÁTICO (Reemplaza a Ollama para traducir en 0ms)
DICCIONARIO_TECNICO = {
    "derivada": "derivative",
    "derivadas": "derivatives",
    "recta tangente": "tangent line",
    "limite": "limit",
    "limites": "limits",
    "integrales": "integrals",
    "integral": "integral",
    "serie": "series",
    "sucesion": "sequence",
    "sucesiones": "sequences",
    "convergencia": "convergence",
    "divergencia": "divergence",
    "potencias": "power series",
    "vector": "vector",
    "vectores": "vectors",
    "parcial": "partial",
    "superficie": "surface",
    "gradiente": "gradient",
    "stokes": "stokes",
    "optimizacion": "optimization",
    "lhopital": "l'hopital"
}

INDICES_CARGADOS = {}

def cargar_indice_en_memoria(nombre_libro_clave):
    """Carga el diccionario .pkl desde el disco si no se cargó antes."""
    if nombre_libro_clave in INDICES_CARGADOS:
        return INDICES_CARGADOS[nombre_libro_clave]
        
    ruta_pkl = os.path.join(os.path.dirname(__file__), "books", f"{nombre_libro_clave}_index.pkl")
    if os.path.exists(ruta_pkl):
        with open(ruta_pkl, "rb") as f:
            INDICES_CARGADOS[nombre_libro_clave] = pickle.load(f)
        return INDICES_CARGADOS[nombre_libro_clave]
    return None

def seleccionar_libro(texto_consulta):
    """Analiza el texto de la consulta y asigna el tomo correcto de OpenStax y su clave."""
    tema = str(texto_consulta).lower().strip()

    if any(w in tema for w in ["integracion multiple", "multiple", "triple", "multivariable", "parcial", "calculo vectorial", "vectores", "superficie", "gradiente", "stokes"]):
        return BIBLIOTECA["calculo3"], "calculo3"
    elif any(w in tema for w in ["serie", "sucesion", "converg", "diverg", "potencias", "ecuacion diferencial", "tecnicas de integracion", "fracciones parciales", "por partes"]):
        return BIBLIOTECA["calculo2"], "calculo2"
    
    return BIBLIOTECA["calculo1"], "calculo1"


def buscar_en_pdf(pregunta_alumno):
    # 1. Selección del Libro (Ahora nos devuelve el archivo y la clave interna)
    libro_archivo, libro_clave = seleccionar_libro(pregunta_alumno)
    
    # 2. Tokenizar y limpiar la pregunta del alumno
    pregunta_limpia = "".join(c for c in pregunta_alumno.lower() if c.isalnum() or c in [" "]).strip()
    palabras_alumno = [p for p in pregunta_limpia.split() if len(p) > 3]

    # 3. Traducir palabras clave usando el diccionario estático
    palabras_ingles = []
    for p in palabras_alumno:
        if p in DICCIONARIO_TECNICO:
            palabras_ingles.append(DICCIONARIO_TECNICO[p])
        else:
            for clave, traduccion in DICCIONARIO_TECNICO.items():
                if clave in p or p in clave:
                    palabras_ingles.append(traduccion)

    if not palabras_ingles:
        palabras_ingles = palabras_alumno[:3]

    print(f"   [RAG] Libro: {libro_archivo} | Palabras clave en inglés: {palabras_ingles}")
    
    if not palabras_ingles:
        return None
        
    # 🌟 4. INTRODUCCIÓN DEL ÍNDICE INVERTIDO
    indice = cargar_indice_en_memoria(libro_clave)
    if not indice:
        print(f"   [AVISO] No se encontró el índice precalculado para {libro_clave}. Fallback a búsqueda lenta.")
        return None # O podés meter tu bucle viejo acá como plan B

    # Tomamos las dos palabras clave principales en inglés
    palabras_filtro = palabras_ingles[:2]
    
    # Buscamos qué páginas contienen la primera palabra
    paginas_candidatas = set(indice.get(palabras_filtro[0], []))
    
    # Si pusiste una segunda palabra clave, hacemos la intersección de conjuntos (matemática pura de conjuntos)
    if len(palabras_filtro) > 1:
        paginas_segunda_palabra = set(indice.get(palabras_filtro[1], []))
        # El operador '&' nos da solo las páginas donde aparecen AMBAS palabras al mismo tiempo
        paginas_candidatas = paginas_candidatas & paginas_segunda_palabra

    if not paginas_candidatas:
        print(f"   [AVISO] El índice no arrojó páginas con el filtro {palabras_filtro}")
        return None

    # Ordenamos las páginas para leer la primera que aparezca en el libro
    pagina_elegida = sorted(list(paginas_candidatas))[0]

    # 5. Ir directo a la página exacta (Sin hacer bucles pesados)
    ruta_pdf = os.path.join(os.path.dirname(__file__), "books", libro_archivo)
    try:
        doc = fitz.open(ruta_pdf)
        pagina = doc[pagina_elegida] # 🧠 Acceso directo O(1) por índice de array
        texto_pagina = pagina.get_text().lower()
        
        print(f"   [EXITO - ÍNDICE INVERTIDO] Coincidencia RAG directa en {libro_archivo}, Pág {pagina_elegida + 1}")
        contenido = texto_pagina[:3500] 
        doc.close()
        return contenido
    except Exception as e:
        print(f"   [ERROR CRÍTICO PDF] {e}")
    
    return None