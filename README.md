# 🚀 Asistente Didáctico de Matemáticas - Backend (FastAPI + Ollama RAG)

Este repositorio contiene el backend asincrónico desarrollado en FastAPI para el asistente pedagógico virtual. El sistema implementa una arquitectura RAG local corriendo en **RunPod** utilizando **Ollama** con el modelo `phi3:mini`, permitiendo adaptar las respuestas en tiempo real según tres niveles de confianza pedagógica: Principiante, Intermedio y Avanzado.

---

## 🛠️ Arquitectura General del Sistema

El flujo de datos e inferencia está optimizado para ejecutarse al 100% dentro del hardware dedicado de la GPU de RunPod:

```text
[Cliente Frontend (Lovable)] 
           │ (Streaming de Tokens)
           ▼
   [FastAPI (Puerto 8000)] 
           │
           ├──► [Búsqueda RAG Local] ──► Consulta la base de conocimiento del PDF
           │
           └──► [Ollama Local (Puerto 11434)] ──► Inferencia de texto con 'phi3:mini'


Este componente contiene el backend asincrónico desarrollado en FastAPI para el asistente pedagógico virtual (Faro). Implementa una arquitectura RAG local corriendo en **RunPod** utilizando **Ollama** con el modelo `phi3:mini`, permitiendo adaptar las respuestas en tiempo real según tres niveles de confianza pedagógica (Principiante, Intermedio y Avanzado).

---

# 🟩 PARTE 1: Configuración y Despliegue del Backend (RunPod)

Para optimizar el almacenamiento y el uso de red en el Pod, se utiliza la característica `sparse-checkout` de Git para descargar de forma selectiva exclusivamente la carpeta del backend.

Ejecutá esta secuencia de comandos en la terminal de tu RunPod (dentro de `/workspace`):

```bash
cd /workspace

# 1. Inicializar un repositorio vacío de Git
git init asistente-backend
cd asistente-backend

# 2. Vincular tu repositorio remoto de GitHub
git remote add -f origin https://github.com/LocuraExtrema/ChatBot.git

# 3. Habilitar la característica de clonado disperso (Sparse Checkout)
git config core.sparseCheckout true

# 4. Indicar a Git la carpeta exacta que querés descargar (Reemplazar con tu ruta real si difiere)
echo "backend/" >> .git/info/sparse-checkout

# 5. Realizar el Pull descargando únicamente la carpeta especificada
git pull origin main

# 6. Actualizar dependencias y descargarlas 
cd backend/
pip install --upgrade pip
pip install -r requirements.txt

# 7. Otorgar permisos de ejecución al script de instalación
chmod +x instalar_ollama.sh

# 8. Ejecutar el instalador automático
./instalar_ollama.sh

# 9. Levantar el backend 
uvicorn main:app --host 0.0.0.0 --port 8000

# 🟦 PARTE 2: Configuración y Despliegue del Frontend (Local)

# 1. Generar un repositorio vacio de Git 
git init asistente-frontend
cd asistente-frontend

# 2. Vincular con el respositorio
git remote add -f origin https://github.com/LocuraExtrema/ChatBot.git
git config core.sparseCheckout true

# 3. Indicar la carpeta del cliente y realizar el Pull
echo "frontend/" >> .git/info/sparse-checkout
git pull origin main
cd frontend/

# 4. Configurar la URL del archivo .env 
VITE_API_BASE_URL=https://<TU_POD_ID>-8000.proxy.runpod.net

# Instalar dependencias del proyecto
npm install

# Levantar el entorno de desarrollo local (Vite)
npm run dev