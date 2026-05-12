import sqlite3
from datetime import datetime

DB_NAME = "logs_pedagogicos.db"

def get_connection():
    """Retorna una conexión a la base de datos."""
    return sqlite3.connect(DB_NAME)

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