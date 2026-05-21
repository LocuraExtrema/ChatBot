import sqlite3
import os
from datetime import datetime

# 🌟 Forzamos la ruta absoluta apuntando a logs_pedagogicos.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs_pedagogicos.db")

def get_connection():
    # Establecemos el timeout para mitigar bloqueos en entorno web
    conn = sqlite3.connect(DB_PATH, timeout=30.0) 
    
    # Habilitamos el modo WAL para lecturas y escrituras simultáneas sin trabas
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    conn.commit()
    return conn


def init_db():
    """Crea la tabla de logs de alumnos si no existe."""
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

def registrar_log(user_id, course_id, role, subtema, pregunta, respuesta):
    """Guarda las consultas de los alumnos de manera segura de forma posicional."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO chat_logs (user_id, course_id, role, subtema, pregunta, respuesta, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(user_id),
            str(course_id),
            str(role),
            str(subtema),
            str(pregunta),
            str(respuesta),
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        print("--> [DB SUCCESS] Registro de consulta de alumno guardado en logs_pedagogicos.db.")
    except Exception as e:
        print(f"Error crítico al registrar log de alumno: {e}")
        conn.rollback()
    finally:
        conn.close()

def inicializar_tabla_profesores():
    """Crea las tablas del módulo docente si no existen y carga los accesos iniciales."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de Profesores Autorizados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profesores (
            email TEXT PRIMARY KEY,
            nombre TEXT,
            activo INTEGER DEFAULT 1
        )
    """)
    
    # Tabla de Auditoría / Feedback Pedagógico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profesores_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profesor_email TEXT,
            pregunta_original TEXT,
            respuesta_bot TEXT,
            calificacion TEXT,
            correccion_sugerida TEXT,
            timestamp TEXT,
            FOREIGN KEY (profesor_email) REFERENCES profesores(email)
        )
    """)
    conn.commit()

    # Insertamos los profesores autorizados
    profesores_test = [
    ('elias.profesor@unraf.edu.ar', 'Elías Farinoli'),
    ('test.docente@unraf.edu.ar', 'Profesor de Prueba'),
    ('profesor@unraf.edu.ar', 'Profesor Simulado LTI') # 👈 Agregamos este
]
    try:
        cursor.executemany("""
            INSERT OR IGNORE INTO profesores (email, nombre, activo) 
            VALUES (?, ?, ?)
        """, profesores_test)
        conn.commit()
    except Exception as e:
        print(f"Error al insertar profesores de prueba: {e}")
        conn.rollback()
    finally:
        conn.close()

def registrar_feedback_profesor(email, pregunta, respuesta, calificacion, correccion=None):
    """Guarda una auditoría realizada por un profesor en la tabla de feedback."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
        print("--> [DB SUCCESS] Feedback docente guardado en logs_pedagogicos.db.")
    except Exception as e:
        print(f"Error crítico al registrar feedback de profesor: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def es_profesor_autorizado(email: str) -> bool:
    """Verifica si el email pertenece a un profesor activo liberando siempre la conexión."""
    conn = get_connection()
    cursor = conn.cursor()
    autorizado = False
    try:
        cursor.execute("SELECT activo FROM profesores WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row and row[0] == 1:
            autorizado = True
    except Exception as e:
        print(f"Error al verificar profesor: {e}")
    finally:
        conn.close() # 🌟 Crucial para que no deje trabada la DB en las verificaciones del GET
    return autorizado