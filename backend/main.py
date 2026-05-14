from fastapi import FastAPI, HTTPException
import hashlib
from pydantic import BaseModel, Field
import shutil
import os
import ollama
import asyncio
from concurrent.futures import ThreadPoolExecutor
# Importamos las funciones desde tus otros archivos
from database import init_db, registrar_log
from subtemas import SUBTEMAS_VALIDOS
from models import ChatRequest, ChatResponse
from busqueda_local import buscar_en_pdf

# Usamos el ejecutor para no bloquear el bucle de eventos de FastAPI
executor = ThreadPoolExecutor(max_workers=3)

def hashear_usuario(username: str):
    # Convertimos el nombre a bytes, lo pasamos por SHA-256 y obtenemos el hex
    return hashlib.sha256(username.encode()).hexdigest()

app = FastAPI(title="Chatbot Pedagógico UNRaf")
# Inicializamos la DB al arrancar
@app.on_event("startup")
def startup_event():
    init_db()

# Creamos una carpeta para los videos si no existe
os.makedirs("uploads", exist_ok=True)

class ChatRequest(BaseModel):
    user_id: str
    course_id: str
    role: str
    pregunta: str
    confidence: int = Field(..., ge=1, le=3)

# Limitamos hilos para no saturar el CPU con la IA local
executor = ThreadPoolExecutor(max_workers=3)

def generar_system_prompt(confidence):
    base_prompt = """Eres un profesor universitario argentino de matemáticas, riguroso, paciente y preciso.
Tu tarea es ayudar al estudiante utilizando exclusivamente la información contenida en el contexto proporcionado.
Reglas obligatorias:
1. No utilices conocimientos externos al contexto. 
2. No agregues resultados no justificados. 
3. Si la respuesta no puede deducirse del material dado, debes decir exactamente: "No puedo responder a esto basándome en el material proporcionado." 
4. No inventes pasos ni resultados. 
5. Si el problema requiere cálculo, explicita primero la estrategia antes de ejecutar el procedimiento."""

    niveles = {
        1: "\nNivel 1 (básico): Explica definiciones, paso a paso detallado, justifica cada transformación y pregunta de control final.",
        2: "\nNivel 2 (intermedio): Enuncia idea clave y estrategia, resuelve sin detalles elementales, señala errores frecuentes.",
        3: "\nNivel 3 (avanzado): Directo a la estrategia, justificaciones sintéticas, incluye equivalencias formales."
    }

    return f"{base_prompt}{niveles[confidence]}\nRespuestas formales y sin motivaciones innecesarias."

def clasificar_pregunta(pregunta):
    prompt = f"Clasifica: {pregunta} en {SUBTEMAS_VALIDOS} o FUERA_DE_ESTRUCTURA. Solo el nombre."
    response = ollama.generate(model='phi3', prompt=prompt)
    return response['response'].strip().split('\n')[0]

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    loop = asyncio.get_event_loop()
    
    print(f"1. Petición recibida de: {request.user_id}")

    # --- PROCESO DE HASHING ---
    request.user_id = hashear_usuario(request.user_id)
    print(f"2. Guardando actividad bajo hash: {request.user_id}")
    
    # --- LÓGICA DE PROCESAMIENTO ---
    print(f"3. Clasificando tema...")
    tema_detectado = await loop.run_in_executor(executor, clasificar_pregunta, request.pregunta)
    
    # --- LIMPIEZA Y TRADUCCIÓN PARA BÚSQUEDA ---
    if isinstance(tema_detectado, set):
        tema_para_buscar = list(tema_detectado)[0]
    else:
        tema_para_buscar = tema_detectado

    # Limpiamos el tema de caracteres raros antes de traducir/buscar
    tema_para_buscar = str(tema_para_buscar).replace("{", "").replace("}", "").replace("'", "").strip()

    # --- BÚSQUEDA LOCAL EN PDF (RAG) ---
    # La función 'buscar_en_pdf' ahora recibirá el tema y ella misma 
    # se encargará de pedirle a Ollama la traducción rápida.
    print(f"4. Consultando PDF local (Traduciendo '{tema_para_buscar}' al inglés)...")
    contexto_pdf = await loop.run_in_executor(executor, buscar_en_pdf, tema_para_buscar)

    system_content = generar_system_prompt(request.confidence)
    
    # --- CONSTRUCCIÓN DEL PROMPT MULTILINGÜE ---
    if contexto_pdf:
        fuente_info = "PDF LOCAL (Inglés)"
        # Le indicamos explícitamente a Phi-3 que lea inglés pero responda en español
        full_prompt = f"""
        TECHNICAL CONTEXT (From English Textbook):
        {contexto_pdf}
        
        INSTRUCCIÓN: Utiliza el contexto anterior en inglés para responder la duda del alumno en ESPAÑOL.
        PREGUNTA DEL ESTUDIANTE: {request.pregunta}
        """
    else:
        fuente_info = "CONOCIMIENTO GENERAL"
        full_prompt = request.pregunta
    
    print(f"5. Llamando a Ollama (Modo: {fuente_info})...")
    
    try:
        def call_ollama():
            return ollama.chat(
                model='phi3', 
                messages=[
                    {'role': 'system', 'content': system_content},
                    {'role': 'user', 'content': full_prompt},
                ],
                options={'temperature': 0}
            )

        response = await loop.run_in_executor(executor, call_ollama)
        respuesta_final = response['message']['content']
        
        # --- REGISTRO EN DB ---
        await loop.run_in_executor(
            executor, 
            registrar_log, 
            request,
            tema_detectado, 
            respuesta_final
        )
        
        print(f"6. Respuesta enviada. Fuente: {fuente_info}")
        return ChatResponse(tema=tema_detectado, respuesta=respuesta_final)

    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))