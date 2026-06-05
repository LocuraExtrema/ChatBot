import os
import json

OUTPUT_DIR = "secciones_output/calculus_volume_3"

# Levantamos todos los archivos .json que tengan la estructura X.X
archivos = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.json') and f[0].isdigit() and f[1] == '.']
# Los ordenamos numéricamente por su capítulo y sección (ej: 1.1, 1.2, 2.1...)
archivos.sort(key=lambda x: [int(num) for num in x.split('_')[0].split('.')])

print(f"{'Sección':<10} | {'Página Inicio':<14} | {'Página Fin':<10}")
print("-" * 45)

for archivo in archivos:
    with open(os.path.join(OUTPUT_DIR, archivo), "r", encoding="utf-8") as f:
        data = json.load(f)
        seccion = data["seccion"]
        inicio, fin = data["paginas_abarca"]
        print(f"{seccion:<10} | {inicio:<14} | {fin:<10}")