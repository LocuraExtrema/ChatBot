from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import hashlib
from pydantic import BaseModel, Field
from typing import Optional
import os
import ollama
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

def generar_system_prompt(confidence):
    base_prompt = r"""Eres un profesor universitario argentino de matemáticas, riguroso, paciente y preciso.
Tu tarea es ayudar al estudiante utilizando exclusivamente la información contenida en el contexto proporcionado.
Reglas obligatorias:
1. No utilices conocimientos externos al contexto. 
2. No agregues resultados no justificados. 
3. Si la respuesta no puede deducirse del material dado, debes decir exactamente: "No puedo responder a esto basándome en el material proporcionado." 
4. No inventes pasos ni resultados. 
5. Si el problema requiere cálculo, explicita primero la estrategia antes de ejecutar el procedimiento.
6. IMPORTANTE: No uses delimitadores de estilo '\( ... \)' o '\[ ... \]' para las fórmulas. Escribe las expresiones matemáticas en texto plano legible o formato Markdown estándar (ej: usar f(x) o Delta_y en lugar de símbolos codificados)."""


    niveles = {
        1: "\nNivel 1 (básico): Explica definiciones, paso a paso detallado, justifica cada transformación y pregunta de control final.",
        2: "\nNivel 2 (intermedio): Enuncia idea clave y estrategia, resuelve sin detalles elementales, señala errores frecuentes.",
        3: "\nNivel 3 (avanzado): Directo a la estrategia, justificaciones sintéticas, incluye equivalencias formales."
    }
    return f"{base_prompt}{niveles[confidence]}\nRespuestas formales y sin motivaciones innecesarias."

def clasificar_pregunta(pregunta):
    # Normalizamos la pregunta eliminando signos para que Ollama trabaje parejo
    pregunta_limpia = pregunta.replace("¿", "").replace("?", "").strip()

    prompt = f"""Te voy a dar una pregunta de un alumno de matemática. Tu única tarea es clasificarla seleccionando EXCLUSIVAMENTE uno de los temas de la siguiente lista válida o devolver 'FUERA_DE_ESTRUCTURA' si no pertenece a la materia.

Lista de temas válidos: {SUBTEMAS_VALIDOS}

Ejemplos de respuesta obligatorios:
Pregunta: "Qué es una derivada" -> Respuesta: Derivadas
Pregunta: "Explicame el vector normal a la superficie" -> Respuesta: Plano Tangente
Pregunta: "Quiero cocinar un keke" -> Respuesta: FUERA_DE_ESTRUCTURA

Pregunta a clasificar: "{pregunta_limpia}"
Respuesta:"""
    
    try:
        response = ollama.generate(
            model='phi3', 
            prompt=prompt, 
            options={'temperature': 0, 'keep_alive': 0}
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
    
# --- ENDPOINT PRINCIPAL ---
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_data: ChatRequest, request: Request):
    loop = asyncio.get_event_loop()
    # ^^^ EXPLICACIÓN: 'chat_data' recibe el JSON, 'request' detecta la conexión de red.
    
    # 🔍 IMPRIMIMOS EL CONTENIDO EXACTO QUE MANDÓ EL FRONT:
    print("\n================ DATO RECIBIDO DEL FRONT ================")
    print(f"1. Petición recibida de: {chat_data.user_id}")
    print(chat_data.dict()) # Muestra todo el JSON convertido en diccionario de Python
    print("=========================================================\n")

    # --- PROCESO DE HASHING ---
    user_hash = hashear_usuario(chat_data.user_id)
    print(f"2. Guardando actividad bajo hash: {user_hash}")
    
# --- LÓGICA DE PROCESAMIENTO ---
    print(f"3. Clasificando tema...")
    tema_detectado = await loop.run_in_executor(executor, clasificar_pregunta, chat_data.pregunta)
    print(f"-> Tema final asignado: '{tema_detectado}'")

    # --- CORTO CIRCUITO DE SEGURIDAD ---
    contexto_pdf = None
    if tema_detectado == "FUERA_DE_ESTRUCTURA":
        print("-> La pregunta no encaja en los subtemas válidos. Saltando el buscador de PDF.")
        # Dejamos contexto_pdf en None para que Ollama responda con CONOCIMIENTO GENERAL directamente
        contexto_pdf = None
    else:
        # --- LIMPIEZA CRÍTICA PARA EL RAG ---
        tema_para_buscar = str(tema_detectado)
        if ":" in tema_para_buscar:
            tema_para_buscar = tema_para_buscar.split(":")[0].strip()
        
        tema_para_buscar = "".join(c for c in tema_para_buscar if c.isalnum() or c in [" ", "_"]).strip()
        palabras = tema_para_buscar.split()
        tema_para_buscar = " ".join(palabras[:4]).strip().strip("_").strip()

        # --- BÚSQUEDA LOCAL EN PDF (RAG) ---
        print(f"4. Consultando PDF local para: {tema_para_buscar}...")
        contexto_pdf = await loop.run_in_executor(executor, buscar_en_pdf, tema_para_buscar)

    system_content = generar_system_prompt(chat_data.confidence)
    
    if contexto_pdf:
        fuente_info = "PDF LOCAL (Inglés)"
        full_prompt = f"""
        TECHNICAL CONTEXT (From English Textbook):
        {contexto_pdf}
        
        INSTRUCCIÓN: Utiliza el contexto anterior en inglés para responder la duda del alumno en ESPAÑOL.
        PREGUNTA DEL ESTUDIANTE: {chat_data.pregunta}
        """
    else:
        fuente_info = "CONOCIMIENTO GENERAL"
        full_prompt = chat_data.pregunta
    
    print(f"5. Llamando a Ollama (Modo: {fuente_info})...")

    def call_ollama():
        # Usamos la API de chat pero con un identificador o simplemente 
        # confiamos en que al cerrar el socket local, Ollama debería notar la presión, 
        # pero para ser agresivos, usaremos un timeout.
        return ollama.chat(
            model='phi3', 
            messages=[
                {'role': 'system', 'content': system_content},
                {'role': 'user', 'content': full_prompt},
            ],
            options={'temperature': 0.1, 'num_predict': 1024, 'keep_alive': 0}
        )

    try:
        task = loop.run_in_executor(executor, call_ollama)

        while not task.done():
            if await request.is_disconnected():
                print("!!! CLIENTE DESCONECTADO: Forzando parada de Ollama...")
                
                # --- SOLUCIÓN RADICAL ---
                # Enviamos una petición vacía o intentamos matar el proceso 
                # En Ollama, la mejor forma es simplemente dejar de leer, 
                # pero si querés liberar la RAM YA:
                task.cancel()
                
                # Intentamos avisarle a la API local de Ollama que aborte
                try:
                    # Esto intenta "pisar" la tarea anterior generando algo vacío
                    await request.post("http://localhost:11434/api/generate", 
                                  json={"model": "phi3", "keep_alive": 0})
                except:
                    pass
                
                return None 
            await asyncio.sleep(0.5)

        response = await task
        respuesta_final = response['message']['content']
        
        # --- REGISTRO EN DB ---
        # Pasamos una copia de chat_data con el ID hasheado para el log
        chat_data_log = chat_data.copy(update={"user_id": user_hash})
        await loop.run_in_executor(
            executor, 
            registrar_log, 
            chat_data_log,
            tema_detectado, 
            respuesta_final
        )
        
        print(f"6. Respuesta enviada. Fuente: {fuente_info}")
        return ChatResponse(tema=tema_detectado, respuesta=respuesta_final)

    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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