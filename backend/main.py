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

# Componentes LTI
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.request import Request as LTIRequest
from pylti1p3.message_launch import MessageLaunch
from pylti1p3.oidc_login import OIDCLogin

# Módulos locales
from database import (
    init_db,
    registrar_log,
    inicializar_tabla_profesores,
    registrar_feedback_profesor,
    es_profesor_autorizado,
    get_connection
)

from subtemas import SUBTEMAS_VALIDOS
from models import ChatResponse
from busqueda_local import buscar_en_pdf

# =========================================================
# CONFIG FASTAPI
# =========================================================

app = FastAPI(title="Faro Chatbot UNRaf")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# THREADS
# =========================================================

executor = ThreadPoolExecutor(max_workers=3)

# =========================================================
# MODELOS
# =========================================================

class ChatRequest(BaseModel):
    user_id: str
    course_id: str
    role: str
    pregunta: str
    confidence: int = Field(..., ge=1, le=3)

class FeedbackProfesorRequest(BaseModel):
    email: str
    pregunta: str
    respuesta: str
    calificacion: str
    correccion: Optional[str] = None

# =========================================================
# LTI CUSTOM
# =========================================================

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

# =========================================================
# HELPERS
# =========================================================

def hashear_usuario(username: str):

    return hashlib.sha256(username.encode()).hexdigest()

# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup_event():

    init_db()
    inicializar_tabla_profesores()

    os.makedirs("uploads", exist_ok=True)

# =========================================================
# PROMPT
# =========================================================

def generar_system_prompt(confidence):

    base_prompt = """
Eres un profesor universitario argentino de matemáticas.

Debes responder:
- con claridad,
- precisión,
- formalidad,
- y utilizando el contexto dado.

REGLAS:
1. No inventes información.
2. No uses conocimiento externo si existe contexto PDF.
3. Si no podés responder:
"No puedo responder a esto basándome en el material proporcionado."
4. Explicá estrategia antes del cálculo.
5. Usá texto matemático simple.
"""

    niveles = {
        1: "\nNivel básico: explicación detallada paso a paso.",
        2: "\nNivel intermedio: estrategia y resolución resumida.",
        3: "\nNivel avanzado: respuesta técnica y sintética."
    }

    return f"{base_prompt}\n{niveles[confidence]}"

# =========================================================
# CLASIFICACIÓN
# =========================================================

def clasificar_pregunta(pregunta):

    pregunta_limpia = (
        pregunta
        .replace("¿", "")
        .replace("?", "")
        .strip()
    )

    prompt = f"""
Clasificá la pregunta usando SOLO uno
de estos temas válidos:

{SUBTEMAS_VALIDOS}

Si no pertenece:
FUERA_DE_ESTRUCTURA

Pregunta:
{pregunta_limpia}

Respuesta:
"""

    try:

        response = ollama.generate(

            model='tinyllama',

            prompt=prompt,

            options={
                'temperature': 0,
                'keep_alive': -1,
                'num_predict': 20
            }

        )

        respuesta_bruta = (
            response['response']
            .strip()
            .replace("Respuesta:", "")
            .strip()
        )

        print(f"[CLASIFICACIÓN] {respuesta_bruta}")

        linea_limpia = (
            respuesta_bruta
            .split('\n')[0]
            .strip()
        )

        for subtema in SUBTEMAS_VALIDOS:

            subtema_limpio = str(subtema).strip()

            if (
                subtema_limpio.lower() == linea_limpia.lower()
                or subtema_limpio.lower() in respuesta_bruta.lower()
                or linea_limpia.lower() in subtema_limpio.lower()
            ):

                return subtema_limpio

        if (
            "fuera" in respuesta_bruta.lower()
            or "estructura" in respuesta_bruta.lower()
        ):
            return "FUERA_DE_ESTRUCTURA"

        return "FUERA_DE_ESTRUCTURA"

    except Exception as e:

        print(f"[ERROR CLASIFICACIÓN] {e}")

        return "FUERA_DE_ESTRUCTURA"

# =========================================================
# CHAT PRINCIPAL
# =========================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_data: ChatRequest, request: Request):

    loop = asyncio.get_event_loop()

    print("\n========== REQUEST ==========")
    print(chat_data.dict())
    print("=============================\n")

    user_hash = hashear_usuario(chat_data.user_id)

    # -----------------------------------------------------
    # CLASIFICACIÓN
    # -----------------------------------------------------

    tema_detectado = await loop.run_in_executor(
        executor,
        clasificar_pregunta,
        chat_data.pregunta
    )

    print(f"[TEMA] {tema_detectado}")

    # -----------------------------------------------------
    # RAG
    # -----------------------------------------------------

    contexto_pdf = None

    if tema_detectado != "FUERA_DE_ESTRUCTURA":

        tema_para_buscar = (
            str(tema_detectado)
            .replace(":", "")
            .strip()
        )

        contexto_pdf = await loop.run_in_executor(
            executor,
            buscar_en_pdf,
            tema_para_buscar
        )

    # -----------------------------------------------------
    # PROMPT FINAL
    # -----------------------------------------------------

    system_content = generar_system_prompt(
        chat_data.confidence
    )

    if contexto_pdf:

        full_prompt = f"""
CONTEXTO:

{contexto_pdf}

PREGUNTA:
{chat_data.pregunta}

Respondé en español.
"""

    else:

        full_prompt = chat_data.pregunta

    print("[OLLAMA] Generando respuesta...")

    # -----------------------------------------------------
    # OLLAMA
    # -----------------------------------------------------

    def call_ollama():

        return ollama.chat(

            model='tinyllama',

            messages=[
                {
                    'role': 'system',
                    'content': system_content
                },
                {
                    'role': 'user',
                    'content': full_prompt
                }
            ],

            options={
                'temperature': 0.1,
                'num_predict': 256,
                'keep_alive': -1
            }

        )

    try:

        task = loop.run_in_executor(
            executor,
            call_ollama
        )

        while not task.done():

            if await request.is_disconnected():

                print("[CLIENTE DESCONECTADO]")

                task.cancel()

                return None

            await asyncio.sleep(0.3)

        response = await task

        respuesta_final = (
            response['message']['content']
        )

        # -------------------------------------------------
        # LOG
        # -------------------------------------------------

        chat_data_log = chat_data.copy(
            update={"user_id": user_hash}
        )

        await loop.run_in_executor(
            executor,
            registrar_log,
            chat_data_log,
            tema_detectado,
            respuesta_final
        )

        return ChatResponse(
            tema=tema_detectado,
            respuesta=respuesta_final
        )

    except Exception as e:

        print(f"[ERROR CHAT] {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================================================
# SHUTDOWN
# =========================================================

@app.on_event("shutdown")
def shutdown_event():

    print("Cerrando servidor...")

    executor.shutdown(wait=False)

# =========================================================
# LTI CONFIG
# =========================================================

CONFIG_LTI_PATH = os.path.join(
    os.path.dirname(__file__),
    'lti_config.json'
)

tool_conf = ToolConfJsonFile(CONFIG_LTI_PATH)

# =========================================================
# LOGIN LTI
# =========================================================

@app.api_route("/lti/login", methods=["GET", "POST"])
async def lti_login(request: Request):

    try:

        oidc_login = CustomFastAPIOIDCLogin(
            request,
            tool_conf
        )

        target_link_uri = (
            "http://127.0.0.1:8000/lti/launch"
        )

        return oidc_login.redirect(
            target_link_uri
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Error OIDC: {str(e)}"
        )

# =========================================================
# LTI LAUNCH
# =========================================================

@app.post("/lti/launch")
async def lti_launch(
    request: Request,
    state: str = Form(...),
    id_token: str = Form(...)
):

    try:

        form_data = {
            "state": state,
            "id_token": id_token
        }

        message_launch = CustomFastAPIMessageLaunch(
            request,
            tool_conf,
            form_data
        )

        launch_data = (
            message_launch.get_launch_data()
        )

        user_name = launch_data.get(
            'name',
            'Usuario_LTI'
        )

        user_email = launch_data.get(
            'email',
            ''
        )

        if not es_profesor_autorizado(
            user_email
        ):

            raise HTTPException(
                status_code=403,
                detail="Profesor no autorizado."
            )

        context = launch_data.get(
            'https://purl.imsglobal.org/spec/lti/claim/context',
            {}
        )

        course_title = context.get(
            'title',
            'Curso_Test'
        )

        frontend_url = (
            f"http://localhost:5173/chat"
            f"?user={user_name}"
            f"&course={course_title}"
            f"&role=professor"
        )

        return RedirectResponse(
            url=frontend_url,
            status_code=303
        )

    except HTTPException as http_ex:

        raise http_ex

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# =========================================================
# JWKS
# =========================================================

@app.get("/lti/jwks")
async def lti_jwks():

    return tool_conf.get_jwks()

# =========================================================
# FEEDBACK
# =========================================================

@app.post("/api/feedback", status_code=201)
async def guardar_feedback_profesor(
    data: FeedbackProfesorRequest
):

    if data.calificacion not in [
        "positivo",
        "negativo"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Calificación inválida."
        )

    try:

        registrar_feedback_profesor(
            email=data.email,
            pregunta=data.pregunta,
            respuesta=data.respuesta,
            calificacion=data.calificacion,
            correccion=data.correccion
        )

        return {
            "status": "success"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================================================
# LOGS PROFESORES
# =========================================================

@app.get("/api/logs-maestros")
async def obtener_logs_para_profesores(
    email_profesor: str
):

    if not es_profesor_autorizado(
        email_profesor
    ):

        raise HTTPException(
            status_code=403,
            detail="No autorizado."
        )

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
SELECT
    id,
    user_id,
    course_id,
    role,
    subtema,
    pregunta,
    respuesta,
    timestamp
FROM chat_logs
ORDER BY id DESC
""")

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
                "pregunta_original": row[5],
                "respuesta_bot": row[6],
                "timestamp": row[7]
            })

        return logs

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
