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

```

---

# 🟩 PARTE 1: Configuración y Despliegue del Backend (RunPod)

Para optimizar el almacenamiento y el uso de red en el Pod, se utiliza la característica `sparse-checkout` de Git para descargar de forma selectiva exclusivamente la carpeta del backend.

Ejecutá esta secuencia de comandos en la terminal de tu RunPod (dentro de `/workspace`):

En esta instancia todos los comandos ejecutados se realizarán sobre la terminal de JupyterLab de RunPod

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
echo "backend/" > .git/info/sparse-checkout 

# 5. Realizar el Pull descargando únicamente la carpeta especificada
git pull origin main

# 6. Actualizar dependencias y descargarlas 
cd backend/
pip install --upgrade pip
pip install -r requirements.txt

# 7. Otorgar permisos de ejecución al script de instalación
chmod +x instalar_ollama.sh

# 8. Ejecutar el instalador automático; Si este comando no se ejecuta, probar de nuevo en la misma u otra terminal
./instalar_ollama.sh

# 9. Levantar el backend 
uvicorn main:app --host 0.0.0.0 --port 8000

```

# 🟦 PARTE 2: Configuración y Despliegue del Frontend (Local)

El frontend se deberá desplegar en el entorno local de la máquina del usuario.

A partir de esta instancia todos los comandos a realizar se deberán ejectuar dentro de la terminal de VSCode o Git Bash (Windows)

## Requisitos previos para levantar el frontend local 

Antes de ejecutar estos comandos, verificar que la computadora tenga instalado:

- Git 
- Node.js 
- npm  
- VSCode 

```bash
# 1. Crear una carpeta de trabajo 
mkdir faro 
cd faro 

# 2. Generar un repositorio vacio de Git 
git init asistente-frontend
cd asistente-frontend

# 3. Vincular con el respositorio
git remote add -f origin https://github.com/LocuraExtrema/ChatBot.git
git config core.sparseCheckout true

# 4. Indicar la carpeta del cliente y realizar el Pull
echo "frontend/" > .git/info/sparse-checkout 
git pull origin main
cd frontend/

# 5. Configurar la URL del backend 
# Dentro de la carpeta frontend/, crear un archivo llamado .env.local con el siguiente contenido: 
VITE_API_URL=https://<TU_POD_ID>-8000.proxy.runpod.net 
# Reemplazar <TU_POD_ID> por el identificador real del pod de RunPod. 

# Instalar dependencias del proyecto
# Dentro de la terminal 
npm install

# Levantar el entorno de desarrollo local (Vite)
npm run dev

```