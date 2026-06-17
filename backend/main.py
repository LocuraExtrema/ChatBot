from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import hashlib
from pydantic import BaseModel, Field
from typing import Optional
import os
import time
import ollama
from ollama import AsyncClient
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Los únicos componentes reales de la raíz que necesitamos
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.request import Request as LTIRequest
from pylti1p3.message_launch import MessageLaunch
from pylti1p3.oidc_login import OIDCLogin

# Importaciones de tus módulos locales
from database import init_db, registrar_log, inicializar_tabla_profesores, registrar_feedback_profesor, es_profesor_autorizado, get_connection
from subtemas import SUBTEMAS_VALIDOS
from models import ChatResponse # Mantenemos ChatResponse de models
from busqueda_local import buscar_en_pdf

class CustomFastAPIOIDCLogin(OIDCLogin):
    def __init__(self, request: Request, tool_config):
        self._request = request
        lti_request = LTIRequest({
            'get': dict(request.query_params),
            'post': {}
        })
        super().__init__(lti_request, tool_config)

    def redirect(self, url):
        return RedirectResponse(url=url, status_code=302)


class CustomFastAPIMessageLaunch(MessageLaunch):
    def __init__(self, request: Request, tool_config, form_data: dict):
        self._request = request
        lti_request = LTIRequest({
            'get': {},
            'post': form_data
        })
        super().__init__(lti_request, tool_config)

app = FastAPI(title="Faro Chatbot UNRaf")

# Permitimos que Lovable se conecte (podés dejar "*" para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En desarrollo, el asterisco te salva la vida con las urls de Lovable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURACIÓN DE CONCURRENCIA ---
executor = ThreadPoolExecutor(max_workers=3)

# --- MODELOS DE DATOS ---
# Definimos ChatRequest aquí mismo para evitar confusiones de importación
class ChatRequest(BaseModel):
    user_id: str
    course_id: str
    role: str
    pregunta: str
    confidence: int = Field(..., ge=1, le=3)

class FeedbackProfesorRequest(BaseModel):
    email: str = Field(..., example="elias.profesor@unraf.edu.ar", description="Email del profesor autenticado")
    pregunta_original: str = Field(..., example="¿Qué es una dirección IP?", description="La pregunta que se le hizo al bot")
    respuesta_bot: str = Field(..., example="Es un número único...", description="La respuesta que arrojó el bot")
    calificacion: str = Field(..., example="negativo", description="Debe ser 'positivo' o 'negativo'")
    correccion_sugerida: Optional[str] = Field(None, example="Faltó explicar IPv4 e IPv6", description="Comentario o respuesta corregida por el docente (opcional)")

def hashear_usuario(username: str):
    return hashlib.sha256(username.encode()).hexdigest()

@app.on_event("startup")
def startup_event():
    init_db()
    inicializar_tabla_profesores()
    os.makedirs("uploads", exist_ok=True)

def generar_system_prompt(confidence: int) -> str:
    base_prompt = r"""Eres un profesor universitario argentino de matemáticas, riguroso, paciente y preciso.
Tu tarea es ayudar al estudiante usando EXCLUSIVAMENTE el contexto provisto.

### REGLAS CRÍTICAS DE OPERACIÓN:
1. No uses conocimiento externo ni inventes pasos/resultados.
2. Si no puedes deducir la respuesta, di exactamente: "No puedo responder a esto basándome en el material proporcionado." y termina ahí.
3. Si requiere cálculo, resume la estrategia en exactamente 5 palabras antes de operar.
4. LÍMITE ESTRICTO: Sé extremadamente conciso. Si la respuesta es larga, sintetiza. Queda totalmente prohibido dejar oraciones a medias o cortar el texto; debes concluir la idea de forma lógica y cerrada antes del límite de espacio.
5. IMPORTANTE: No uses delimitadores de estilo '\( ... \)' o '\[ ... \]' para las fórmulas. Escribe las expresiones matemáticas en texto plano legible o formato Markdown estándar (ej: usar f(x) o Delta_y en lugar de símbolos codificados)."""

    # Estructuramos las directivas usando viñetas claras para que Phi-3 entienda el formato sin repetir las órdenes
    niveles = {
        1: """
### DIRECTIVA PEDAGÓGICA - MODO PRINCIPIANTE (NIVEL 1):
- Objetivo: Explicar con empatía a un alumno que está trabado o ve el tema por primera vez.
- Tono: Cálido, empático, descontracturado y paciente (estilo profesor argentino amigable). Usa expresiones sutiles como "Mirá, es más simple de lo que parece", "Vamos paso a paso", "Imaginate que...".
- Estructura obligatoria de respuesta:
  1. Un mensaje inicial empático, breve y alentador.
  2. Una analogía de la vida cotidiana muy simple (evita tecnicismos como "tasa de cambio" o "diferenciación" en la introducción).
  3. Una explicación de entrecasa de cómo se hace el cálculo (tratar a las otras variables como si fueran un número fijo, un "3" o un "5").
  4. Cierra OBLIGATORIAMENTE con una sola pregunta corta de control que sea fácil de responder para el alumno, introducida de forma amigable (ej: "A ver si quedó claro: si...").""",
        
        2: """
### DIRECTIVA PEDAGÓGICA - MODO INTERMEDIO (NIVEL 2):
- Objetivo: Explicar a un estudiante que ya conoce los conceptos básicos y necesita comprender la mecánica analítica o la aplicación técnica del tema.
- Tono: Profesional, académico, riguroso y preciso (estilo docente universitario técnico). Evita la informalidad del nivel 1, pero sé directo: habla como un maestro que guía los pasos de manera ejecutiva.
- Estructura obligatoria de respuesta:
  1. Ve directo al grano: prohibido empezar con introducciones largas o frases redundantes como "La derivada parcial es un concepto matemático...".
  2. Enuncia inmediatamente la regla, propiedad formal o criterio matemático del texto que se debe aplicar para resolver la duda.
  3. Explica el procedimiento analítico de forma lógica y secuencial, detallando cómo se comporta el sistema matemático (por ejemplo, qué se considera constante y qué se opera), omitiendo pasos aritméticos elementales que el alumno ya debería saber.
  4. Concluye la idea de forma cerrada y sintética en un máximo de dos párrafos.""",
        
        3: """
### DIRECTIVA PEDAGÓGICA - MODO EXPERTO (NIVEL 3):
- Objetivo: Responder con el máximo rigor académico y formalismo matemático a un estudiante avanzado de ingeniería.
- Tono: Estrictamente formal, analítico, académico, denso y minimalista. Queda totalmente prohibido el uso de analogías comunes, ejemplos cotidianos o lenguaje informal.
- Estructura obligatoria de respuesta:
  1. Prohibido iniciar con introducciones enciclopédicas o redundantes (evita frases como "La derivada parcial es...").
  2. Comienza directamente con la definición formal del límite, la estructura algebraica abstracta o el planteo operativo del problema según el contexto provisto.
  3. Utiliza de manera obligatoria la notación matemática formal estándar expresada en texto plano legible o Markdown (ej: usar f_x(x,y), del_f/del_x, lim_{h -> 0}, la definición formal por cociente incremental, etc.).
  4. Sé extremadamente conciso y sintético: ve directo a la médula de la estructura matemática utilizando la menor cantidad de palabras posible."""
    }

    instruccion_nivel = niveles.get(confidence, niveles[1])
    
    # El remate final actúa como un "metaprompt" para evitar que imprima tus nombres de variables en el chat
    meta_instruccion = """
### NOTA DE FORMATO FINAL:
Actúa directamente en el rol del docente. Está estrictamente prohibido incluir en tu respuesta final títulos o textos del prompt como "Nivel", "Directiva Pedagógica" o "Reglas Críticas". Comienza directamente con la explicación matemática formal orientada al estudiante."""

    return f"{base_prompt}{instruccion_nivel}{meta_instruccion}"

def clasificar_pregunta(pregunta):
    pregunta_limpia = pregunta.replace("¿", "").replace("?", "").strip()

    prompt = f"""Te voy a dar una pregunta de un alumno de matemática. Tu única tarea es clasificarla seleccionando EXCLUSIVamente uno de los temas de la lista o devolver 'FUERA_DE_ESTRUCTURA'.

Lista de temas válidos: {SUBTEMAS_VALIDOS}

Regla de oro: Responde ÚNICAMENTE con el nombre del tema, sin introducciones, sin puntos ni texto extra.

Ejemplos:
Pregunta: "Qué es una derivada" -> Derivadas
Pregunta: "Explicame el vector normal a la superficie" -> Plano Tangente
Pregunta: "Quiero cocinar un keke" -> FUERA_DE_ESTRUCTURA

Pregunta a clasificar: "{pregunta_limpia}"
Respuesta:"""
    
    try:
        response = ollama.generate(
            model='phi3:mini', 
            prompt=prompt, 
            options={'temperature': 0, 'keep_alive': -1, 'num_predict': 1024}
        )
        
        # Limpieza absoluta de la respuesta del modelo
        respuesta_bruta = response['response'].strip().replace("Respuesta:", "").strip()
        print(f"--> [DEBUG OLLAMA OUT] El modelo respondió textualmente: '{respuesta_bruta}'")
        
        linea_limpia = respuesta_bruta.split('\n')[0].strip()
        
        # --- COMPARACIÓN BLINDADA (Case-Insensitive y Strip Completo) ---
        for subtema in SUBTEMAS_VALIDOS:
            # Limpiamos espacios fantasmas o saltos de línea del archivo subtemas.py
            subtema_limpio = str(subtema).strip()
            
            # Comparamos ignorando mayúsculas/minúsculas de manera exacta o por inclusión parcial
            if (subtema_limpio.lower() == linea_limpia.lower() or 
                subtema_limpio.lower() in respuesta_bruta.lower() or 
                linea_limpia.lower() in subtema_limpio.lower()):
                print(f"--> [DEBUG MATCH] Éxito absoluto. Mapeado a: '{subtema_limpio}'")
                return subtema_limpio  
                
        if "fuera" in respuesta_bruta.lower() or "estructura" in respuesta_bruta.lower():
            return "FUERA_DE_ESTRUCTURA"
            
        return "FUERA_DE_ESTRUCTURA"
        
    except Exception as e:
        print(f"Error en clasificación: {e}")
        return "FUERA_DE_ESTRUCTURA"
    
# --- ENDPOINT PRINCIPAL MODIFICADO ---
@app.post("/api/chat")
async def chat_endpoint(chat_data: ChatRequest, request: Request):
    loop = asyncio.get_event_loop()
    user_hash = hashear_usuario(chat_data.user_id)
    
    print("\n================ DATO RECIBIDO DEL FRONT ================")
    print(f"Pregunta de: {chat_data.user_id} -> '{chat_data.pregunta}'")
    print("=========================================================\n")

    # --- BÚSQUEDA LOCAL DIRECTA EN PDF (RAG) ---
    print(f"3. Consultando biblioteca de PDFs con la pregunta directa...")
    inicio_rag = time.perf_counter()
    
    # Reducimos dinámicamente a un máximo de 2 chunks en busqueda_local para alivianar el Prefill
    contexto_pdf = await loop.run_in_executor(executor, lambda: buscar_en_pdf(chat_data.pregunta, limite_chunks=5))
    
    print(f"⏱️ [TIEMPO] Búsqueda local en PDF: {time.perf_counter() - inicio_rag:.4f} segundos")

    tema_log = "Consulta General / RAG"
    fuente_info = "PDF LOCAL (Inglés)" if contexto_pdf else "CONOCIMIENTO GENERAL"

    system_content = generar_system_prompt(chat_data.confidence)
    
    if contexto_pdf:
        full_prompt = f"""TECHNICAL CONTEXT (From English Textbook):
{contexto_pdf}

INSTRUCCIÓN: Utiliza el contexto anterior en inglés para responder la duda del alumno en ESPAÑOL de manera pedagógica y ultra-concisa.
PREGUNTA DEL ESTUDIANTE: {chat_data.pregunta}
Answer:"""
    else:
        full_prompt = chat_data.pregunta
    
    print(f"4. Iniciando flujo Ollama Nativo Asincrónico (Modo: {fuente_info})...")

    async def generador_de_respuesta():
        respuesta_completa = ""
        tokens_generados = 0
        inicio_gen = time.perf_counter()
        primer_token = False
        
        try:
            # 🚀 LLAMADA ASINCRÓNICA NATIVA: No bloquea el loop de FastAPI durante el prefill
            async_client = AsyncClient()
            response_stream = await async_client.chat(
                model='phi3:mini',
                messages=[
                    {'role': 'system', 'content': system_content},
                    {'role': 'user', 'content': full_prompt},
                ],
                options={'temperature': 0.1, 'num_predict': 1024, 'keep_alive': -1, 'num_thread': 6},
                stream=True
            )

            # 🌟 Iteramos usando 'async for' para liberar recursos mientras llega cada token
            async for chunk in response_stream:
                if await request.is_disconnected():
                    print("!!! CLIENTE DESCONECTADO: Cancelando Ollama en la GPU/CPU.")
                    return

                token = chunk['message']['content']
                respuesta_completa += token
                tokens_generados += 1
                
                if not primer_token:
                    print(f"⏱️ [TIEMPO] TTFT (Primer token real): {time.perf_counter() - inicio_gen:.4f} segundos")
                    primer_token = True

                yield token
                # Eliminamos el asyncio.sleep(0.01) artificial ya que el async for maneja el delay natural del hardware

            print(f"⏱️ [TIEMPO] Generación completa: {time.perf_counter() - inicio_gen:.4f} segundos ({tokens_generados} tokens)")

            # Registro en BD en segundo plano
            await loop.run_in_executor(
                executor, 
                registrar_log, 
                user_hash,               
                chat_data.course_id,     
                chat_data.role,          
                tema_log, 
                chat_data.pregunta,      
                respuesta_completa       
            )

        except Exception as e:
            print(f"ERROR EN STREAM: {e}")
            yield f"\n[Error en el servidor: {str(e)}]"

    return StreamingResponse(generador_de_respuesta(), media_type="text/plain")

@app.on_event("shutdown")
def shutdown_event():
    print("Cerrando servidor... Matando procesos colgados de Ollama.")
    executor.shutdown(wait=False)
    # OPCIONAL: Si estás en Windows y querés matar a Ollama al cerrar todo
    # os.system("taskkill /IM ollama_llama_server.exe /F")

# Inicializamos la lectura del archivo de configuración que creaste recién
CONFIG_LTI_PATH = os.path.join(os.path.dirname(__file__), 'lti_config.json')
tool_conf = ToolConfJsonFile(CONFIG_LTI_PATH)

# ENDPOINT 1: Inicio del flujo OIDC
@app.api_route("/lti/login", methods=["GET", "POST"])
async def lti_login(request: Request):
    try:
        oidc_login = CustomFastAPIOIDCLogin(request, tool_conf)
        target_link_uri = "http://127.0.0.1:8000/lti/launch"
        return oidc_login.redirect(target_link_uri)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en Login OIDC: {str(e)}")


# ENDPOINT 2: Lanzamiento definitivo
@app.post("/lti/launch")
async def lti_launch(request: Request, state: str = Form(...), id_token: str = Form(...)):
    try:
        form_data = {"state": state, "id_token": id_token}
        message_launch = CustomFastAPIMessageLaunch(request, tool_conf, form_data)
        launch_data = message_launch.get_launch_data()
        
        user_name = launch_data.get('name', 'Usuario_LTI')
        user_email = launch_data.get('email', '')  # Email que manda Moodle
        
        # --- VALIDACIÓN CON TU DATABASE.PY ---
        if not user_email or not es_profesor_autorizado(user_email):
            print(f"\n[ACCESO DENEGADO] {user_name} ({user_email}) intentó entrar pero no es profesor autorizado.")
            raise HTTPException(
                status_code=403, 
                detail="Acceso denegado: Tu cuenta no está registrada como profesor autorizado."
            )
        # --------------------------------------

        context = launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context', {})
        course_title = context.get('title', 'Curso_Test')
        
        print(f"\n[LTI ACCESO PROFESOR] {user_name} ({user_email}) validado correctamente.")
        
        # Redirección al frontend pasándole el rol para que la interfaz sepa que es un profe
        frontend_url = f"http://localhost:5173/chat?user={user_name}&course={course_title}&role=professor"
        return RedirectResponse(url=frontend_url, status_code=303)
        
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fallo en validación de Token Moodle: {str(e)}")


# ENDPOINT 3: JWKS
@app.get("/lti/jwks")
async def lti_jwks():
    return tool_conf.get_jwks()

@app.post("/api/feedback", status_code=201)
async def guardar_feedback_profesor(data: FeedbackProfesorRequest):
    """
    Endpoint para que los profesores validen o corrijan las respuestas del bot.
    Almacena los datos de auditoría de forma relacional en la base de datos.
    """
    # Validación rápida de la calificación
    if data.calificacion not in ["positivo", "negativo"]:
        raise HTTPException(
            status_code=400, 
            detail="La calificación es inválida. Debe ser exactamente 'positivo' o 'negativo'."
        )
        
    try:
        # 🌟 EL MAPEO CLAVE:
        # Pasamos las variables del Front (pregunta_original) a los parámetros de la DB (pregunta)
        registrar_feedback_profesor(
            email=data.email,
            pregunta=data.pregunta_original,       # Mapeado a 'pregunta' que sí existe en la DB
            respuesta=data.respuesta_bot,          # Mapeado a 'respuesta' que sí existe en la DB
            calificacion=data.calificacion,
            correccion=data.correccion_sugerida    # Mapeado a 'correccion'
        )
        return {
            "status": "success", 
            "message": "Feedback de auditoría pedagógica registrado correctamente."
        }
        
    except Exception as e:
        print(f"--> [ERROR CRÍTICO DB]: {str(e)}")
        if "FOREIGN KEY" in str(e) or "constraint failed" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"Error de integridad: El email '{data.email}' no corresponde a un profesor autorizado."
            )
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al procesar el guardado en la base de datos: {str(e)}"
        )

@app.get("/api/logs-maestros")
async def obtener_logs_para_profesores(email_profesor: str):
    # Validamos primero con tu función local si es un profesor activo
    if not es_profesor_autorizado(email_profesor):
        raise HTTPException(status_code=403, detail="Acceso denegado: No eres un profesor autorizado.")
        
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Traemos el historial de lo que preguntaron los alumnos
        cursor.execute("SELECT id, user_id, course_id, role, subtema, pregunta, respuesta, timestamp FROM chat_logs ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append({
                "id": row[0],
                "user_id": row[1],
                "course_id": row[2],
                "role": row[3],
                "subtema": row[4],
                "pregunta_original": row[5], # Mapeado para que Lovable lo lea directo
                "respuesta_bot": row[6],      # Mapeado para que Lovable lo lea directo
                "timestamp": row[7]
            })
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer los logs: {str(e)}")