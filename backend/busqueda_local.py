import fitz  # PyMuPDF
import os
import ollama

def traducir_a_ingles_tecnico(termino):
    """
    Obliga a la IA a devolver UNICAMENTE el término técnico.
    """
    try:
        # Usamos una estructura de mensaje más rígida
        response = ollama.chat(model='phi3', messages=[
            {
                'role': 'system', 
                'content': 'You are a technical translator. Translate the math term to English. Respond ONLY with the translated term, no explanations, no quotes.'
            },
            {'role': 'user', 'content': f"Translate: {termino}"}
        ])
        
        traduccion = response['message']['content'].strip()
        
        # Limpieza de emergencia: si la IA devolvió muchas líneas, nos quedamos con la primera
        traduccion = traduccion.split('\n')[0].replace('"', '').replace('.', '').strip()
        
        print(f"   [TRADUCCIÓN] Realizada: '{traduccion}'", flush=True)
        return traduccion
    except Exception as e:
        print(f"   [ERROR TRADUCCION] {e}")
        return termino
    
def buscar_en_pdf(query, nombre_archivo="calculus-volume-1.pdf"):
    # 1. Traducimos (usando la función de arriba)
    query_en = traducir_a_ingles_tecnico(query)
    
    # 2. Creamos una lista de palabras clave (ej: ['intermediate', 'value', 'theorem'])
    # Filtramos palabras cortas como 'the', 'and', 'of'
    palabras_clave = [p for p in query_en.lower().split() if len(p) > 3]
    
    ruta_pdf = os.path.join(os.path.dirname(__file__), "books", nombre_archivo)
    
    try:
        doc = fitz.open(ruta_pdf)
        for pagina in doc:
            texto_pagina = pagina.get_text().lower()
            
            # Verificamos si TODAS las palabras clave están en esta página
            if all(palabra in texto_pagina for palabra in palabras_clave):
                print(f"   [EXITO] Coincidencia en página {pagina.number + 1}", flush=True)
                return texto_pagina[:2500] 
        doc.close()
    except Exception as e:
        print(f"   [ERROR PDF] {e}")
    
    return None