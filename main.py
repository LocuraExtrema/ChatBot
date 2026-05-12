from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import ollama
import asyncio
from concurrent.futures import ThreadPoolExecutor
# Importamos las funciones desde tus otros archivos
from database import init_db, registrar_log
from subtemas import SUBTEMAS_VALIDOS
from models import ChatRequest, ChatResponse

app = FastAPI(title="Chatbot Pedagógico UNRaf")
# Inicializamos la DB al arrancar
@app.on_event("startup")
def startup_event():
    init_db()

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

# Usamos el ejecutor para no bloquear el bucle de eventos de FastAPI
executor = ThreadPoolExecutor(max_workers=3)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    loop = asyncio.get_event_loop()
    
    # 1. Clasificación asíncrona
    # Usamos args en run_in_executor para pasar parámetros de forma limpia
    tema_detectado = await loop.run_in_executor(executor, clasificar_pregunta, request.pregunta)
    
    # 2. Validación de seguridad
    if "FUERA_DE_ESTRUCTURA" in tema_detectado:
        return {"respuesta": "No puedo responder a esto basándome en el material proporcionado."}

    # 3. Preparación del Prompt
    system_content = generar_system_prompt(request.confidence)
    contexto_prueba = "Material de cátedra: La derivada de una constante es cero..."
    full_prompt = f"CONTEXTO:\n{contexto_prueba}\n\nPREGUNTA: {request.pregunta}"

    # 4. Ejecución de la IA
    try:
        # Definimos una función interna para la llamada a Ollama
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
        
        # 5. Registro en DB usando tu archivo database.py
        # No hace falta await aquí si no es una función asíncrona, 
        # pero lo mandamos al executor para no bloquear el retorno al usuario
        loop.run_in_executor(executor, registrar_log, request, tema_detectado, respuesta_final)
        
        return ChatResponse(
            tema = tema_detectado,
            respuesta = respuesta_final
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de IA: {str(e)}")

def clasificar_pregunta(pregunta):
    prompt = f"Clasifica: {pregunta} en {SUBTEMAS_VALIDOS} o FUERA_DE_ESTRUCTURA. Solo el nombre."
    response = ollama.generate(model='phi3', prompt=prompt)
    return response['response'].strip().split('\n')[0]