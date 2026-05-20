import sqlite3
from datetime import datetime

DB_NAME = "logs_pedagogicos.db"

def get_connection():
    """Retorna una conexión a la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Crea la tabla de logs si no existe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            course_id TEXT,
            role TEXT,
            subtema TEXT,
            pregunta TEXT,
            respuesta TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def registrar_log(req, tema, resp):
    """Guarda una interacción en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_logs (user_id, course_id, role, subtema, pregunta, respuesta, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        req.user_id, 
        req.course_id, 
        req.role, 
        tema, 
        req.pregunta, 
        resp, 
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

# --- SECCIÓN: CONTROL Y FEEDBACK DE PROFESORES ---

def inicializar_tabla_profesores():
    """Crea la estructura para profesores y sus feedbacks de forma independiente."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Tabla Maestra de Profesores (La que ya tenías)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profesores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            activo INTEGER DEFAULT 1
        )
    """)
    
    # 2. Nueva Tabla de Historial de Feedback (Vinculada a la anterior)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profesores_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profesor_email TEXT,
            pregunta_original TEXT,
            respuesta_bot TEXT,
            calificacion TEXT,         -- 'positivo' o 'negativo'
            correccion_sugerida TEXT,  -- Lo que el profesor edite
            timestamp TEXT,
            FOREIGN KEY(profesor_email) REFERENCES profesores(email)
        )
    """)
    
    # Insertar profesores de prueba (Tu lógica original)
    profesores_test = [
        ('elias.profesor@unraf.edu.ar', 'Elías Farinoli'),
        ('test.docente@unraf.edu.ar', 'Profesor de Prueba')
    ]
    try:
        cursor.executemany("""
            INSERT OR IGNORE INTO profesores (email, nombre) 
            VALUES (?, ?)
        """, profesores_test)
    except Exception as e:
        print(f"Error al insertar profesores de prueba: {e}")
        
    conn.commit()
    conn.close()

def registrar_feedback_profesor(email, pregunta, respuesta, calificacion, correccion=None):
    """Guarda una auditoría realizada por un profesor en la tabla de feedback."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO profesores_feedback (profesor_email, pregunta_original, respuesta_bot, calificacion, correccion_sugerida, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        email,
        pregunta,
        respuesta,
        calificacion,
        correccion,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def es_profesor_autorizado(email: str) -> bool:
    """Verifica en la BD si el email pertenece a un profesor activo."""
    conn = get_connection()  # Usa tu conexión con el PRAGMA configurado
    cursor = conn.cursor()
    
    cursor.execute("SELECT activo FROM profesores WHERE email = ?", (email,))
    resultado = cursor.fetchone()
    conn.close()
    
    # Retorna True si el profesor existe y está activo (1), sino False
    return resultado is not None and resultado[0] == 1