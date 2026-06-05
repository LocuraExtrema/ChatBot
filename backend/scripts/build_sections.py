import fitz  # PyMuPDF
import re
import json
import os

# --- CONFIGURACIÓN ---
PDF_PATH = "books/calculus-volume-3.pdf"
OUTPUT_DIR = "secciones_output/calculus_volume_3"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Regex para detectar títulos de sección (admite hasta dos dígitos, ej: 4.10)
SECTION_PATTERN = re.compile(r"^([1-7]\.(?:[1-9][0-9]?))\s+(.*)$")

def limpiar_texto_openstax(texto_crudo):
    """
    Normaliza el texto extraído del PDF eliminando roturas provocadas 
    por fórmulas en línea, fuentes especiales o espaciados rotos.
    """
    # 1. Reemplazamos múltiples espacios o tabulaciones por un solo espacio
    texto = re.sub(r'[ \t]+', ' ', texto_crudo)
    
    # 2. Corregimos palabras cortadas por variables matemáticas (ej: "t  imes" -> "times")
    # Si hay una letra sola rodeada de muchos espacios, juntamos el texto de forma natural
    texto = re.sub(r'(?<=\b\w)\s{2,}(?=\w\b)', '', texto)
    
    # 3. Unimos saltos de línea huérfanos que cortan una oración a la mitad dentro de un párrafo
    # Solo dejamos los saltos de línea dobles que marcan puntos y aparte reales
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)
    
    # 4. Reconstruimos el bloque línea por línea limpiando los extremos
    lineas_limpias = []
    for linea in texto.split("\n"):
        linea_strip = linea.strip()
        if linea_strip:
            # Eliminamos pequeños caracteres extraños residuales aislados (ruido de fórmulas)
            if len(linea_strip) == 1 and not linea_strip.isalnum():
                continue
            lineas_limpias.append(linea_strip)
            
    return "\n".join(lineas_limpias)

def extraer_secciones_quirurgico(pdf_path):
    print("1. Extrayendo secciones con limpieza y normalización de texto...")
    doc = fitz.open(pdf_path)
    
    secciones = {}
    seccion_actual = "0.0_introduccion"
    secciones[seccion_actual] = {"paginas": [], "texto_acumulado": ""}
    
    for num_pag in range(len(doc)):
        num_real = num_pag + 1
        pagina = doc[num_pag]
        
        # Saltamos preliminares lógicos
        if num_real < 16:
            texto_preliminar = limpiar_texto_openstax(pagina.get_text("text"))
            secciones[seccion_actual]["texto_acumulado"] += texto_preliminar + "\n"
            secciones[seccion_actual]["paginas"].append(num_real)
            continue
            
        pag_dict = pagina.get_text("dict")
        
        # Aplicamos la nueva limpieza estética a todo el bloque de texto de la página
        texto_pagina_completo = limpiar_texto_openstax(pagina.get_text("text"))
        nueva_seccion_en_pagina = None
        
        for bloque in pag_dict["blocks"]:
            if "lines" not in bloque:
                continue
            for linea in bloque["lines"]:
                if not linea["spans"]:
                    continue
                
                texto_linea = "".join([span["text"] for span in linea["spans"]]).strip()
                match = SECTION_PATTERN.match(texto_linea)
                
                if match:
                    first_span = linea["spans"][0]
                    tamano_letra = first_span["size"]
                    nombre_fuente = first_span["font"].lower()
                    
                    # Filtro exacto por RobotoSlab y tamaño real mapeado
                    if "robotoslab" in nombre_fuente and tamano_letra > 14.0:
                        num_sec = match.group(1)
                        titulo_sucio = match.group(2).strip().lower().replace(" ", "_")
                        titulo_limpio = re.sub(r'[^\w\-]', '', titulo_sucio)[:40]
                        
                        nueva_seccion_en_pagina = f"{num_sec}_{titulo_limpio}"
                        break
                        
        if nueva_seccion_en_pagina and nueva_seccion_en_pagina not in secciones:
            seccion_actual = nueva_seccion_en_pagina
            print(f"   -> [CORTE CONFIRMADO] {seccion_actual} en Página {num_real}")
            secciones[seccion_actual] = {"paginas": [], "texto_acumulado": ""}
            
        secciones[seccion_actual]["texto_acumulado"] += texto_pagina_completo + "\n"
        secciones[seccion_actual]["paginas"].append(num_real)
        
    return secciones

def guardar_secciones(secciones):
    print("2. Escribiendo archivos JSON limpios en el disco...")
    for id_seccion, datos in secciones.items():
        if len(datos["texto_acumulado"].strip()) < 100:
            continue
            
        filename = os.path.join(OUTPUT_DIR, f"{id_seccion}.json")
        estructura = {
            "seccion": id_seccion.split("_")[0],
            "paginas_abarca": [min(datos["paginas"]), max(datos["paginas"])],
            "texto_completo": datos["texto_acumulado"]
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(estructura, f, ensure_ascii=False, indent=2)
            
    print(f"\n¡Extracción limpia completada en '{OUTPUT_DIR}'!")

if __name__ == "__main__":
    mapa_secciones = extraer_secciones_quirurgico(PDF_PATH)
    guardar_secciones(mapa_secciones)