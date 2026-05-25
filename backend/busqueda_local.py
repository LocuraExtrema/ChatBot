import fitz  # PyMuPDF
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

def seleccionar_libro(texto_consulta):
    """Analiza el texto de la consulta y asigna el tomo correcto de OpenStax."""
    tema = str(texto_consulta).lower().strip()

    # Prioridad Cálculo 3
    if any(w in tema for w in ["integracion multiple", "multiple", "triple", "multivariable", "parcial", "calculo vectorial", "vectores", "superficie", "gradiente", "stokes"]):
        print("   --> [DEBUG MATCH] Clasificado en Cálculo 3")
        return BIBLIOTECA["calculo3"]
    
    # Prioridad Cálculo 2
    elif any(w in tema for w in ["serie", "sucesion", "converg", "diverg", "potencias", "ecuacion diferencial", "tecnicas de integracion", "fracciones parciales", "por partes"]):
        print("   --> [DEBUG MATCH] Clasificado en Cálculo 2")
        return BIBLIOTECA["calculo2"]
    
    # Prioridad Cálculo 1
    elif any(w in tema for w in ["funciones", "limites", "derivada", "derivadas", "recta tangente", "lhopital", "optimizacion", "integracion simple"]):
        print("   --> [DEBUG MATCH] Clasificado en Cálculo 1")
        return BIBLIOTECA["calculo1"]
    
    return BIBLIOTECA["calculo1"]

def buscar_en_pdf(pregunta_alumno):
    # 1. Selección del Libro basándonos en el texto
    libro_archivo = seleccionar_libro(pregunta_alumno)
    
    # 2. Tokenizar y limpiar la pregunta del alumno en español
    pregunta_limpia = "".join(c for c in pregunta_alumno.lower() if c.isalnum() or c in [" "]).strip()
    palabras_alumno = [p for p in pregunta_limpia.split() if len(p) > 3]

    # 3. Traducir palabras clave usando el diccionario estático
    palabras_ingles = []
    for p in palabras_alumno:
        # Si la palabra exacta está en nuestro diccionario, añadimos su traducción
        if p in DICCIONARIO_TECNICO:
            palabras_ingles.append(DICCIONARIO_TECNICO[p])
        else:
            # Si no está, probamos si alguna palabra clave está contenida (ej: "derivadas" -> "derivative")
            for clave, traduccion in DICCIONARIO_TECNICO.items():
                if clave in p or p in clave:
                    palabras_ingles.append(traduccion)

    # Si no se pudo mapear nada, dejamos las palabras originales como fallback
    if not palabras_ingles:
        palabras_ingles = palabras_alumno[:3]

    print(f"   [RAG] Libro: {libro_archivo} | Palabras clave en inglés: {palabras_ingles}")
    
    if not palabras_ingles:
        return None
    
    ruta_pdf = os.path.join(os.path.dirname(__file__), "books", libro_archivo)
    if not os.path.exists(ruta_pdf):
        print(f"   [ERROR] No existe el archivo: {ruta_pdf}")
        return None

    try:
        doc = fitz.open(ruta_pdf)
        
        # Estrategia de búsqueda híbrida:
        # Intentamos buscar páginas que contengan AL MENOS las 2 primeras palabras clave importantes
        palabras_filtro = palabras_ingles[:2]
        
        for pagina in doc:
            texto_pagina = pagina.get_text().lower()
            
            # Si todas las palabras principales están en la página, la damos por válida
            if all(p in texto_pagina for p in palabras_filtro):
                print(f"   [EXITO] Coincidencia RAG en {libro_archivo}, Pág {pagina.number + 1}")
                contenido = texto_pagina[:3500] 
                doc.close()
                return contenido
                
        doc.close()
        print(f"   [AVISO] No se hallaron páginas con las palabras clave {palabras_filtro}")
    except Exception as e:
        print(f"   [ERROR CRÍTICO PDF] {e}")
    
    return None