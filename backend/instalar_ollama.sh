cat << 'EOF' > instalar_ollama.sh
#!/bin/bash

echo "========================================================="
echo "🚀 INICIANDO INSTALACIÓN AUTOMÁTICA DE OLLAMA Y DEPENDENCIAS"
echo "========================================================="

# 1. Actualizar paquetes e instalar zstd
echo "📦 1/4 Actualizando repositorios e instalando zstd..."
apt-get update && apt-get install -y zstd

# 2. Descargar e instalar Ollama de forma global
echo "📥 2/4 Descargando e instalando Ollama de forma oficial..."
curl -fsSL https://ollama.com/install.sh | sh

# 3. Levantar el servicio de Ollama en segundo plano
echo "⚙️ 3/4 Iniciando el servicio de Ollama en segundo plano (Background)..."
ollama serve > ollama.log 2>&1 &

# Esperar unos segundos para asegurarse de que el servicio de Ollama levantó correctamente
sleep 5

# 4. Descargar el modelo phi3:mini
echo "🤖 4/4 Descargando el modelo phi3:mini (esto puede demorar)..."
ollama pull phi3:mini

echo "========================================================="
echo "✅ ¡PROCESO TERMINADO CON ÉXITO!"
echo "Ollama está corriendo y el modelo phi3:mini está listo."
echo "Ya podés levantar tu Uvicorn normalmente."
echo "========================================================="
EOF