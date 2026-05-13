import requests

def buscar_en_openstax(query):
    """
    Busca contenido académico en la API de OpenStax.
    """
    # Buscamos específicamente en libros de ciencias/matemáticas
    query_limpia = query.replace("_", " ")
    
    print(f"\n--- Buscando en OpenStax: {query_limpia} ---", flush=True)
    url = f"https://openstax.org/api/v2/pages/?search={query_limpia}&type=book.Chapter"
    
    try:
        response = requests.get(url, timeout=3)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data['items']:
                # Retornamos la descripción y el título del capítulo más relevante
                resultado = data['items'][0]
                titulo = resultado['title']
                contenido = resultado['search_description']
                print(f"RESULTADO ENCONTRADO: {titulo}")
                return f"Información de OpenStax ({titulo}): {contenido}"
        print("AVISO: No hubo coincidencias en los items de OpenStax.")
        return "No se encontró información específica en los libros de texto."
    except Exception:
        print(f"ERROR DE CONEXIÓN: {e}")
        return "Error de conexión con la biblioteca externa."