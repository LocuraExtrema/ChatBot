import fitz  # PyMuPDF
import os
import ollamaz

# 1. Configuración de la Biblioteca
# Asegurate de que los nombres coincidan EXACTAMENTE con tus archivos en /books
BIBLIOTECA = {
    "calculo1": "calculus-volume-1.pdf", 
    "calculo2": "calculus-volume-2.pdf", 
    "calculo3": "calculus-volume-3.pdf"
}

def seleccionar_libro(tema_limpio):
    """
    Analiza el tema y devuelve el nombre del archivo PDF correspondiente.
    """
    # 1. Limpieza absoluta antes de comparar
    tema = str(tema_limpio).lower().strip()
    tema = "".join(c for c in tema if c.isalnum() or c in ["_", " "]).strip()
    
    # !!! PRINT CLAVE DE CONTROL:
    print(f"   --> [DEBUG INTERNO] El string final procesado es: '{tema}'")

    # Prioridad Cálculo 3
    if any(w in tema for w in ["integracion multiple", "multiple", "triple", "multivariable", "parcial", "calculo vectorial", "vectores", "superficie", "gradiente", "stokes"]):
        print("   --> [DEBUG MATCH] Clasificado en Cálculo 3")
        return BIBLIOTECA["calculo3"]
    
    # Prioridad Cálculo 2
    elif any(w in tema for w in ["serie", "sucesion", "converg", "diverg", "potencias", "ecuacion diferencial", "tecnicas de integracion", "fracciones parciales", "por partes"]):
        print("   --> [DEBUG MATCH] Clasificado en Cálculo 2")
        return BIBLIOTECA["calculo2"]
    
    # Prioridad Cálculo 1
    elif any(w in tema for w in ["funciones", "limites", "derivadas", "recta tangente", "lhopital", "optimizacion", "integracion simple"]):
        print("   --> [DEBUG MATCH] Clasificado en Cálculo 1")
        return BIBLIOTECA["calculo1"]
    
    else:
        print(f"   --> [DEBUG MATCH] Cayó en el ELSE. Asignando Cálculo 1 por defecto.")
        return BIBLIOTECA["calculo1"]

def traducir_a_ingles_tecnico(termino):
    try:
        # Prompt con ejemplos (Few-shot) para que la IA entienda el formato exacto
        response = ollama.chat(model='phi3', messages=[
            {
                'role': 'system', 
                'content': (
                    "You are a technical math dictionary. Translate to English. "
                    "Example 1: 'Derivadas' -> 'Derivatives'. "
                    "Example 2: 'Integrales triples' -> 'Triple integrals'. "
                    "Respond ONLY with the term. No explanations."
                )
            },
            {'role': 'user', 'content': f"Translate: {termino}"}
        ])
        
        traduccion = response['message']['content'].strip()
        
        # Limpieza de seguridad: nos quedamos con lo último que parezca un término
        # Por si la IA dice: "The translation is: Limit"
        if ":" in traduccion:
            traduccion = traduccion.split(":")[-1]
            
        traduccion = traduccion.split('\n')[0].replace('"', '').replace('.', '').strip()
        
        print(f"   [TRADUCCIÓN] '{termino}' -> '{traduccion}'")
        return traduccion
    except Exception as e:
        print(f"   [ERROR TRADUCCION] {e}")
        return termino

def buscar_en_pdf(tema_detectado):
    # 1. Selección del Libro
    libro_archivo = seleccionar_libro(tema_detectado)
    
    # 2. Traducción técnica (usando el prompt de "diccionario" que armamos)
    query_en = traducir_a_ingles_tecnico(tema_detectado).lower().strip()
    if not query_en:
        print("   [AVISO] La traducción quedó vacía. Usando fallback del término original.")
        query_en = "".join(c for c in str(tema_detectado) if c.isalnum() or c in [" ", "_"]).lower()

    print(f"   [RAG] Libro: {libro_archivo} | Buscando: '{query_en}'")

    # 3. Limpieza de palabras clave
    # Eliminamos términos comunes que pueden "ensuciar" la búsqueda
    stop_words = ["the", "with", "from", "that", "this"]
    palabras = [p for p in query_en.split() if len(p) > 3 and p not in stop_words]
    
    # Si aun así no quedan palabras clave, evitamos recorrer el documento en vano
    if not palabras:
        print("   [AVISO] No hay palabras clave suficientes para buscar. Saltando RAG.")
        return None
    
    # Ajuste de ruta (verificá si es "docs" o "books" según tu carpeta)
    ruta_pdf = os.path.join(os.path.dirname(_file_), "books", libro_archivo)
    
    if not os.path.exists(ruta_pdf):
        print(f"   [ERROR] No existe el archivo: {ruta_pdf}")
        return None

    try:
        doc = fitz.open(ruta_pdf)
        for pagina in doc:
            texto_pagina = pagina.get_text().lower()
            
            # --- MEJORA DE COINCIDENCIA ---
            # Si el concepto tiene varias palabras, permitimos que falte una (opcional)
            # o simplemente buscamos la coincidencia exacta de la frase clave.
            if all(p in texto_pagina for p in palabras):
                print(f"   [EXITO] Se encontró contenido en {libro_archivo}, Pág {pagina.number + 1}")
                
                # Extraemos un bloque de texto un poco más grande para dar contexto
                contenido = texto_pagina[:3000] 
                doc.close()
                return contenido
                
        doc.close()
        print(f"   [AVISO] No se hallaron coincidencias para '{query_en}' en el PDF.")
    except Exception as e:
        print(f"   [ERROR CRÍTICO PDF] {e}")
    return None
