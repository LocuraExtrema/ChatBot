import json

def auditar_chunks():
    try:
        with open("base_chunks.json", "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'base_chunks.json'.")
        return

    total_chunks = len(chunks)
    secciones = set()
    
    tamanos = []
    chunks_muy_cortos = 0
    chunks_muy_largos = 0

    for ch in chunks:
        secciones.add(ch["seccion"])
        largo = len(ch["contenido"])
        tamanos.append(largo)
        
        if largo < 300: # Alerta si hay bloques casi vacíos
            chunks_muy_cortos += 1
        if largo > 1500: # Alerta si la ventana se descontroló
            chunks_muy_largos += 1

    promedio = sum(tamanos) / total_chunks if total_chunks > 0 else 0

    print("=== AUDITORÍA DE MODULACIÓN POR CHUNKS ===")
    print(f"Total de chunks generados : {total_chunks}")
    print(f"Total de secciones cubiertas: {len(secciones)}")
    print(f"Tamaño promedio de chunk  : {promedio:.1f} caracteres")
    print(f"Chunks sospechosos cortos : {chunks_muy_cortos} (menores a 300 caracteres)")
    print(f"Chunks sospechosos largos : {chunks_muy_largos} (mayores a 1500 caracteres)")
    print("==========================================")
    
    # Mostramos una muestra del primer chunk para verificar estructura
    if total_chunks > 0:
        print("\nMuestra de estructura del primer chunk:")
        print(json.dumps(chunks[0], indent=2, ensure_ascii=False)[:300] + "...\n")

if __name__ == "__main__":
    auditar_chunks()