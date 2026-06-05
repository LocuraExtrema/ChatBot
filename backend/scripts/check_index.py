import pickle

with open("calculo3_index.pkl", "rb") as f:
    data = pickle.load(f)

indice = data["index"]
referencias = data["chunks_reference"]

# Probamos buscar una palabra clave fuerte del libro
palabra_a_buscar = "vectors"

if palabra_a_buscar in indice:
    # Ordenamos los chunks que contienen la palabra de mayor a menor score TF-IDF
    resultados = sorted(indice[palabra_a_buscar].items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"\n=== TOP 3 CHUNKS PARA '{palabra_a_buscar}' ===")
    for chunk_id, score in resultados:
        ref = referencias[chunk_id]
        print(f"\n[ID: {chunk_id}] | Score TF-IDF: {score:.4f} | Sección: {ref['seccion']} | Páginas: {ref['paginas']}")
        print(f"Texto: {ref['contenido'][:150]}...")
else:
    print(f"La palabra '{palabra_a_buscar}' no fue indexada.")