## Descripción de los Componentes

### Fase 1: Extracción Quirúrgica por Secciones (`build_sections.py`)
Separa el PDF completo en archivos independientes por sección (ej. `3.1_tangent_lines.json`).
* **Lógica Avanzada:** Utiliza **PyMuPDF** para inspeccionar los bloques de texto a bajo nivel. Filtra los títulos reales exigiendo que la tipografía contenga la firma `robotoslab` (fuente exclusiva de títulos en OpenStax) y que su tamaño de fuente sea superior a `14.0pt`. Esto evita falsos positivos de los mini-índices de portadas o pies de página.
* **Limpieza Adaptativa:** Une de forma natural palabras rotas por variables matemáticas en línea (ej: `t  imes` -> `times`) y normaliza renglones huérfanos provocados por ecuaciones.

### Fase 2: Modulación por Chunks (`build_chunks.py`)
Levanta las secciones de la carpeta `secciones_output` y las trocea en bloques homogéneos.
* **Métricas:** Configurado para un tamaño objetivo de **1200 caracteres** (`CHUNK_SIZE`) y un solapamiento/overlap de **170 caracteres** (`CHUNK_OVERLAP`).
* **Corte Inteligente:** Utiliza búsquedas de espacio (`rfind(" ")`) para garantizar que ningún fragmento corte una palabra o teorema a la mitad. Cada chunk hereda un ID autoincremental, el ID de sección y el rango de páginas PDF que abarca.
* **Salida:** Consolida todo en el archivo maestro unificado `base_chunks.json`.

### Fase 3: Indexación Semántica TF-IDF (`build_index.py`)
Construye el motor matemático de búsqueda e indexación inversa en memoria pura.
* **Matemática Pura:** Tokeniza los textos, limpia caracteres especiales y remueve *Stop Words* comunes en inglés. Calcula el **TF** (frecuencia de término relativa en el chunk) y el **IDF** (frecuencia inversa en el libro para penalizar palabras genéricas y premiar conceptos técnicos como *derivative* o *optimization*).
* **Persistencia:** Exporta un paquete serializado único comprimido (`.pkl`) mediante `pickle`. Contiene el índice invertido ponderado, el diccionario de IDFs maestros y un diccionario rápido de referencias con los textos limpios para el RAG.

---

## Ejecución del Pipeline

Para procesar un libro desde cero o actualizar la base de datos tras modificar un parámetro, ejecutá los siguientes comandos de forma secuencial en tu terminal:

```bash
# 1. Extraer y limpiar las secciones del PDF
python build_sections.py

# 2. Modular el contenido en ventanas con overlap
python build_chunks.py

# 3. Generar la matriz matemática y el índice binario
python build_index.py

# Suite de Comprobación y Auditoría RAG

Este módulo contiene las herramientas offline diseñadas para auditar, controlar la calidad y testear el pipeline de datos de los libros de **Calculus de OpenStax** antes de pasar los índices a producción en el backend.

---

## ⚙️ ¿Cómo Funciona? (Breve Explicación)

Los scripts de comprobación operan como un "filtro de control de calidad" en tres frentes distintos:
1. **Validación de Estructura (`check_sections.py`)**: Analiza los archivos JSON individuales generados en la fase de extracción para verificar que no haya baches ni saltos extraños de páginas en el PDF.
2. **Auditoría Métrica (`check_chunks.py`)**: Evalúa el archivo maestro comprimido para asegurar que la ventana deslizante haya fragmentado el texto respetando los límites de caracteres (evitando bloques vacíos o masivos).
3. **Simulación del Motor (`check_index.py`)**: Ejecuta una consulta matemática fría sobre la matriz **TF-IDF** final (`.pkl`) levantada en RAM para validar la relevancia del ordenamiento y la legibilidad del texto limpio.

---

## 🚀 Cómo se Utiliza (Modo de Empleo)

Para auditar el estado de tu base de conocimientos en cualquier momento, ejecutá los scripts desde tu terminal según el control que necesites:

### 1. Control de Continuidad de Páginas
Para verificar que el extractor cubrió todo el libro de corrido y guardó bien los JSON:

```bash
python check_sections.py

python check_chunks.py

python check_index.py

El archivo ver_fuentes.py solo detecta las fuentes del libro para generar de forma correcta las secciones de los libros OpenStax