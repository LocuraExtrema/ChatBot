import json
import math
import re
import pickle
import os

# --- CONFIGURACIÓN ---
INPUT_FILE = "base_chunks.json"
OUTPUT_INDEX_FILE = "calculo3_index.pkl"

# Lista básica de Stop Words en inglés (palabras ultra comunes que no aportan valor semántico)
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else', 'of', 'at', 'by', 
    'from', 'for', 'with', 'in', 'on', 'to', 'is', 'was', 'are', 'were', 'be', 'been',
    'this', 'that', 'these', 'those', 'it', 'its', 'we', 'you', 'they', 'he', 'she',
    'as', 'at', 'by', 'an', 'your', 'my', 'their', 'our', 'his', 'her', 'which', 'who'
}

def limpiar_y_tokenizar(texto):
    """
    Limpia el texto, elimina caracteres especiales y devuelve una lista de palabras válidas.
    """
    # Pasamos a minúsculas y reemplazamos caracteres que no sean letras, números o espacios por un espacio vacío
    texto_limpio = re.sub(r'[^a-z0-9\s\-]', ' ', texto.lower())
    # Separamos por espacios y filtramos palabras vacías o stop words cortas
    palabras = [p for p in texto_limpio.split() if p not in STOP_WORDS and len(p) > 1]
    return palabras

def construir_tfidf_index():
    print(f"1. Cargando los chunks desde '{INPUT_FILE}'...")
    if not os.path.exists(INPUT_FILE):
        print(f"Error: No se encontró '{INPUT_FILE}'. Ejecutá primero 'build_chunks.py'.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    total_chunks = len(chunks)
    print(f"   -> {total_chunks} chunks cargados correctamente.")

    # Estructuras para el cálculo
    # Vocabulario e índice invertido: { palabra: { chunk_id: tf_score } }
    indice_invertido = {}
    # Guarda en cuántos chunks aparece cada palabra (para el cálculo de IDF)
    document_frequency = {}

    print("\n2. Procesando texto y calculando Frecuencias de Término (TF)...")
    for ch in chunks:
        chunk_id = ch["chunk_id"]
        palabras = limpiar_y_tokenizar(ch["contenido"])
        
        if not palabras:
            continue
            
        # Contamos la frecuencia de cada palabra en ESTE chunk
        conteo_palabras = {}
        for p in palabras:
            conteo_palabras[p] = conteo_palabras.get(p, 0) + 1
            
        total_palabras_en_chunk = len(palabras)

        # Calculamos el TF de cada palabra y actualizamos el diccionario de DF
        for palabra, conteo in conteo_palabras.items():
            tf = conteo / total_palabras_en_chunk
            
            if palabra not in indice_invertido:
                indice_invertido[palabra] = {}
                document_frequency[palabra] = 0
                
            indice_invertido[palabra][chunk_id] = tf
            document_frequency[palabra] += 1

    print("3. Calculando Frecuencias Inversas de Documento (IDF) y ponderando matriz...")
    # Calculamos el IDF final para cada palabra y multiplicamos por su TF
    idf_maestro = {}
    for palabra, df in document_frequency.items():
        # Fórmula estándar de IDF suavizada para evitar divisiones por cero
        idf = math.log(total_chunks / (1 + df)) + 1
        idf_maestro[palabra] = idf
        
        # Multiplicamos el TF guardado previamente por el IDF calculado
        for chunk_id in indice_invertido[palabra]:
            indice_invertido[palabra][chunk_id] *= idf

    # --- PASO FINAL: Empaquetar y exportar con Pickle ---
    # Guardamos el índice invertido (matriz TF-IDF) junto con los metadatos de los chunks
    # para que FastAPI no tenga que mapear dos archivos separados.
    paquete_indexacion = {
        "index": indice_invertido,
        "idf": idf_maestro,
        "chunks_reference": {ch["chunk_id"]: {"seccion": ch["seccion"], "paginas": ch["paginas_abarca"], "contenido": ch["contenido"]} for ch in chunks}
    }

    print(f"\n4. Exportando índice binario comprimido a '{OUTPUT_INDEX_FILE}'...")
    with open(OUTPUT_INDEX_FILE, "wb") as f:
        pickle.dump(paquete_indexacion, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"¡Éxito absoluto! Índice invertido generado. Tamaño del vocabulario: {len(indice_invertido)} palabras únicas.")

if __name__ == "__main__":
    construir_tfidf_index()