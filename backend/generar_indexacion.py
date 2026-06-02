import fitz
import pickle
import os

BIBLIOTECA = {
    "calculo1": "calculus-volume-1.pdf", 
    "calculo2": "calculus-volume-2.pdf", 
    "calculo3": "calculus-volume-3.pdf"
}

def precalcular_todo():
    base_dir = os.path.dirname(__file__)
    books_dir = os.path.join(base_dir, "books")
    
    for clave, nombre_archivo in BIBLIOTECA.items():
        ruta_pdf = os.path.join(books_dir, nombre_archivo)
        if not os.path.exists(ruta_pdf):
            print(f"No se encontró {nombre_archivo}, salteando...")
            continue
            
        print(f"Indexando {nombre_archivo}...")
        doc = fitz.open(ruta_pdf)
        indice = {}
        
        for pag in doc:
            texto = pag.get_text().lower()
            # set() evita registrar la misma palabra varias veces en una sola página
            palabras_unicas = set(texto.split())
            
            for palabra in palabras_unicas:
                palabra_limpia = palabra.strip(".,;:()[]{}¿?¡!\"'")
                if len(palabra_limpia) > 4:
                    # Usamos setdefault para inicializar la lista si es palabra nueva
                    indice.setdefault(palabra_limpia, []).append(pag.number)
        
        doc.close()
        
        # Guardamos el índice invertido en un archivo .pkl
        ruta_pkl = os.path.join(base_dir, "books", f"{clave}_index.pkl")
        with open(ruta_pkl, "wb") as f:
            pickle.dump(indice, f)
        print(f"¡Índice guardado con éxito en {ruta_pkl}!")

if __name__ == "__main__":
    precalcular_todo()