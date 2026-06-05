import fitz

doc = fitz.open("books/calculus-volume-1.pdf")

# Analizamos las páginas 16, 17 y 18 para espiar los tamaños de los títulos
for p in [16, 17, 18]:
    print(f"\n--- INSPECCIONANDO PÁGINA FÍSICA {p} ---")
    pag_dict = doc[p-1].get_text("dict")
    
    for bloque in pag_dict["blocks"]:
        if "lines" in bloque:
            for linea in bloque["lines"]:
                for span in linea["spans"]:
                    texto = span["text"].strip()
                    # Si la línea tiene cara de sección, imprimimos su tamaño real de tipografía
                    if any(char.isdigit() for char in texto) and len(texto) > 2:
                        print(f"Texto: '{texto}' | Tamaño Fuente: {span['size']:.2f}pt | Font: {span['font']}")