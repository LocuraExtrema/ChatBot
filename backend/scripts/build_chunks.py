import os
import json
import re

# --- CONFIGURACIÓN ---
INPUT_DIR = "../secciones_output/calculus_volume_1"
OUTPUT_FILE = "base_chunks.json"

CHUNK_SIZE = 1200       # Tamaño aproximado en caracteres de cada bloque
CHUNK_OVERLAP = 170     # Solapamiento entre chunks para no perder contexto

def generar_chunks_por_ventana(texto, size, overlap):
    """
    Trocea el texto usando una ventana deslizante con solapamiento.
    Intenta cortar en espacios para no romper palabras a la mitad.
    """
    chunks = []
    if not texto or len(texto.strip()) == 0:
        return chunks
        
    inicio = 0
    texto_len = len(texto)
    
    while inicio < texto_len:
        # El final teórico de nuestra ventana
        fin = inicio + size
        
        # Si el fin supera el largo del texto, llegamos al último bloque
        if fin >= texto_len:
            fin = texto_len
            chunk_texto = texto[inicio:fin].strip()
            if len(chunk_texto) > 10: # Evitamos fragmentos residuales ínfimos
                chunks.append(chunk_texto)
            break
            
        # Para no cortar una palabra a la mitad, buscamos el último espacio en blanco cercano al final teórico
        posicion_espacio = texto.rfind(" ", inicio + size - 50, inicio + size + 20)
        if posicion_espacio != -1:
            fin = posicion_espacio
            
        chunk_texto = texto[inicio:fin].strip()
        if len(chunk_texto) > 10:
            chunks.append(chunk_texto)
            
        # Avanzamos el inicio de la ventana restándole el overlap
        inicio = fin - overlap
        
        # Guardas de seguridad para evitar bucles infinitos en textos raros
        if inicio >= fin:
            inicio = fin
            
    return chunks

def procesar_pipeline_chunks():
    print(f"1. Leyendo archivos de secciones desde '{INPUT_DIR}'...")
    
    # Listamos y ordenamos los JSON numéricamente por su capítulo y sección
    archivos = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json') and f[0].isdigit()]
    archivos.sort(key=lambda x: [int(num) for num in x.split('_')[0].split('.')])
    
    chunks_maestros = []
    total_secciones_procesadas = 0
    
    for archivo in archivos:
        ruta_archivo = os.path.join(INPUT_DIR, archivo)
        
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        seccion_id = data["seccion"] # Ej: "3.1"
        paginas = data["paginas_abarca"] # Ej: [16, 38]
        texto_completo = data["texto_completo"]
        
        # Limpiamos saltos de línea excesivos del PDF para que el texto sea más homogéneo
        texto_limpio = re.sub(r'\n{3,}', '\n\n', texto_completo).strip()
        
        # Modulamos el texto de la sección
        lista_fragmentos = generar_chunks_por_ventana(texto_limpio, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # Construimos la estructura de datos para cada chunk herederando metadatos
        for i, fragmento in enumerate(lista_fragmentos):
            # Formateamos un ID único incremental por sección, ej: chunk_3_1_002
            chunk_id = f"chunk_{seccion_id.replace('.', '_')}_{i+1:03d}"
            
            chunks_maestros.append({
                "chunk_id": chunk_id,
                "seccion": seccion_id,
                "paginas_abarca": paginas,
                "contenido": fragmento
            })
            
        print(f"   -> Sección {seccion_id}: Fragmentada en {len(lista_fragmentos)} chunks.")
        total_secciones_procesadas += 1

    # --- PASO FINAL: Guardar el archivo maestro ---
    print(f"\n2. Consolidando {len(chunks_maestros)} chunks en el archivo maestro...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks_maestros, f, ensure_ascii=False, indent=2)
        
    print(f"¡Completado! Archivo unificado generado con éxito: '{OUTPUT_FILE}'")

if __name__ == "__main__":
    procesar_pipeline_chunks()